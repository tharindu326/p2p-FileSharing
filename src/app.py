from flask import Flask, jsonify, request, send_from_directory
from flask_apscheduler import APScheduler
import json
import requests
import os
from threading import Thread
from peer import Peer
from file import SharedFile
from config import cfg

# Global variables for storing peers and shared files
peers = []
shared_files = []

# Configuration for the current node
self_host = None
self_port = None

app = Flask(__name__)
scheduler = APScheduler()


def load_config():
    """Load configuration from a JSON file."""
    global self_host, self_port
    with open(cfg.peer.config_file, 'r') as f:
        config = json.load(f)
        self_config = config["self"]
        self_host = self_config["host"]
        self_port = self_config["port"]
        for peer in config["peers"]:
            join_peer(peer["host"], peer["port"])


@scheduler.task('interval', id='update_shared_files', seconds=30)
def update_shared_files():
    """Update the list of shared files from the shared directory."""
    global shared_files
    shared_files = [SharedFile(file) for file in os.listdir(cfg.file.shared_directory)]
    print("Shared files list updated:", [file.filename for file in shared_files])


@scheduler.task('interval', id='send_heartbeat', seconds=30)
def send_heartbeat():
    """Send a heartbeat signal to all known peers."""
    for peer in peers:
        try:
            url = f"http://{peer.host}:{peer.port}/heartbeat"
            data = {"host": self_host, "port": self_port}
            response = requests.post(url, json=data)
            if response.status_code == 200:
                peer.update('active')
                print(f"Heartbeat successful to {peer.host}:{peer.port}. Marked as active.")
            else:
                # mark the peer as inactive
                peer.update('inactive')
                print(f"Heartbeat response from {peer.host}:{peer.port} was not successful. Marked as inactive.")

        except Exception as err:
            print(f"Failed sending heartbeat to {peer.host}-{peer.port}: {err}")


@app.route('/heartbeat', methods=["POST"])
def heartbeat():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)
    print(f"Received heartbeat request: {host}-{port} ")
    return jsonify({"status": True}, 201)


@app.route('/')
def hello_world():
    return 'Hello, World!'


def is_peer(host, port):
    """Check if a given host and port combination is already a known peer."""
    return any(peer.host == host and peer.port == port for peer in peers)


def join_peer(host, port):
    """Attempt to join a new peer by sending a ping and then a join request."""
    try:
        ping_response = requests.get(f"http://{host}:{port}/ping")
        if ping_response.status_code == 200:
            join_response = requests.post(f"http://{host}:{port}/join", json={"host": self_host, "port": self_port})
            if join_response.status_code == 200:
                peers.append(Peer(host, port))
    except Exception as err:
        print(f"Failed to join peer {host}:{port}: {err}")


@app.route('/join', methods=["POST"])
def join():
    """Endpoint for new peers to join the network."""
    data = request.get_json()
    host = data.get("host")
    port = data.get("port")
    if host and port and not is_peer(host, port):
        peers.append(Peer(host, port))
        print(f"New peer joined: {host}:{port}")
        return jsonify({"status": True})
    return jsonify({"status": False})


@app.route('/query', methods=["POST"])
def handle_query():
    """Handle incoming file query requests and either respond or forward."""
    data = request.get_json()
    thread = Thread(target=process_query, args=(data,))
    thread.start()
    return jsonify({"status": True})


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(cfg.file.shared_directory, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


@app.route('/query_hit', methods=['POST'])
def query_hit():
    data = request.get_json()
    filename = data.get('filename')
    filehash = data.get('filehash')
    host = data.get('host')
    port = data.get('port')

    print(f"File {filename} with hash {filehash} found at {host}:{port}")
    initiate_file_download(host, port, filename)
    return jsonify({"status": "success"})


def initiate_file_download(peer_host, peer_port, filename):
    download_url = f"http://{peer_host}:{peer_port}/download/{filename}"
    try:
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(f'{cfg.file.save_directory}{filename}', 'wb') as f:
                f.write(response.content)
            print(f"File {filename} downloaded successfully.")
        else:
            print(f"Failed to download file {filename}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as err:
        print(f"Error occurred while downloading file {filename}: {err}")


@app.route('/ping', methods=["GET"])
def ping():
    return jsonify({"status": True}, 201)


def is_local(filename):
    file_path = os.path.join(cfg.file.shared_directory, filename)
    return os.path.exists(file_path), file_path


def forward_query(sender_host, sender_port, filename, filehash, ttl):
    for peer in peers:
        # Not send the query back to the peer who sent it to us
        if peer.host == sender_host and peer.port == sender_port:
            continue
        # Decrease TTL by 1 to prevent infinite flooding
        if ttl > 0:
            peer.send_query(filename, filehash, ttl - 1)


def process_query(data):
    """Process a file query by checking local files or forwarding to peers."""
    filename = data.get("filename")
    filehash = data.get("filehash")
    sender_host = data.get("host")
    sender_port = data.get("port")
    ttl = data.get("ttl", 2)  # time to live

    found_locally, file_path = is_local(filename)
    if found_locally:
        print(f"File {filename} found locally at {file_path}. Sending query hit back to requester.")
        # Send a query hit back to the requester
        try:
            url = f"http://{sender_host}:{sender_port}/query_hit"
            data = {
                "filename": filename,
                "filehash": filehash,
                "host": self_host,
                "port": self_port
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Query hit successfully sent to {sender_host}:{sender_port}")
            else:
                print(f"Failed to send query hit to {sender_host}:{sender_port}, status code: {response.status_code}")
        except requests.exceptions.RequestException as err:
            print(f"Error sending query hit to {sender_host}:{sender_port}: {err}")
    else:
        print(f"File {filename} not found locally. Forwarding query to other peers.")
        forward_query(sender_host, sender_port, filename, filehash, ttl)


if __name__ == '__main__':
    load_config()
    update_shared_files()
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, host="0.0.0.0", port=self_port)

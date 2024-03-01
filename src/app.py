from flask import Flask, jsonify, request, send_from_directory
from flask_apscheduler import APScheduler
from threading import Thread
from peer import Peer
from config import cfg
from utils.query_manager import QueryManager
from utils.peer_manager import PeerManager
from utils.file_manager import FileManager

app = Flask(__name__)
scheduler = APScheduler()
peer_manager = PeerManager()
file_manager = FileManager()
query_manager = QueryManager(peer_manager, file_manager)


@scheduler.task('interval', id='update_shared_files', seconds=30)
def update_shared_files():
    file_manager.update_shared_files()


@scheduler.task('interval', id='send_heartbeat', seconds=30)
def send_heartbeat():
    peer_manager.send_heartbeat()


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/heartbeat', methods=["POST"])
def heartbeat():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)
    print(f"Received heartbeat request: {host}-{port} ")
    return jsonify({"status": True}, 201)


@app.route('/join', methods=["POST"])
def join():
    """Endpoint for new peers to join the network."""
    data = request.get_json()
    host = data.get("host")
    port = data.get("port")
    if host and port and not peer_manager.is_peer(host, port):
        peer_manager.peers.append(Peer(host, port))
        print(f"New peer joined: {host}:{port}")
        return jsonify({"status": True})
    return jsonify({"status": False})


@app.route('/query', methods=["POST"])
def handle_query():
    """Handle incoming file query requests and either respond or forward."""
    data = request.get_json()
    thread = Thread(target=query_manager.process_query, args=(data,))
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
    file_manager.initiate_file_download(host, port, filename)
    return jsonify({"status": "success"})


@app.route('/ping', methods=["GET"])
def ping():
    return jsonify({"status": True}, 201)


if __name__ == '__main__':
    update_shared_files()
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, host=cfg.peer.configuration['self']['host'],
            port=cfg.peer.configuration['self']['port'])

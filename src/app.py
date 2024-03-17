from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_apscheduler import APScheduler
from threading import Thread
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from peer import Peer
from utils.query_manager import QueryManager
from utils.peer_manager import PeerManager
from utils.file_manager import FileManager
import argparse
import importlib
from logger import get_debug_logger

app = Flask(__name__)
scheduler = APScheduler()


@scheduler.task('interval', id='update_shared_files', seconds=30)
def update_shared_files():
    file_manager.update_shared_files()


@scheduler.task('interval', id='send_heartbeat', seconds=30)
def send_heartbeat():
    peer_manager.send_heartbeat()


@scheduler.task('interval', id='check_peer_liveness', seconds=60)
def check_peer_liveness():
    peer_manager.peer_liveness_check()


@app.route('/heartbeat', methods=["POST"])
def heartbeat():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)
    peer_manager.update_heartbeat(host, port)
    logger.info(f"[APP] Received heartbeat request: {host}-{port} ")
    return jsonify({"status": True}, 200)


@app.route('/join', methods=["POST"])
def join():
    """Endpoint for new peers to join the network."""
    data = request.get_json()
    host = data.get("host")
    port = data.get("port")
    if host and port:
        new_peer = Peer(host, port)
        new_peer.status = 'active'
        peer_manager.addPeer(new_peer)
        logger.info(f"[APP] New peer joined: {host}:{port}")
        return jsonify({"status": True})
    return jsonify({"status": False})


@app.route('/get_peers', methods=["POST"])
def get_peers():
    """Endpoint for peers to request peer list from node."""
    data = request.get_json()
    host = data.get("host")
    port = data.get("port")
    if peer_manager.is_peer(host, port):
        peer_list = [{'host': peer.host, 'port': peer.port} for peer in peer_manager.peers]
        return jsonify({"status": True, 'peers': peer_list})
    return jsonify({"status": False, "Msg": "Unauthorized request."})


@app.route('/query', methods=["POST"])
def handle_query():
    """
    Handle incoming file query requests and either respond or forward.
    filename = data.get("filename")
    filehash = data.get("filehash")
    sender_host = data.get("host")
    sender_port = data.get("port")
    ttl = data.get("ttl", 2)  # time to live
    query_id = data.get("QID")
    """
    data = request.get_json()
    print(data)
    thread = Thread(target=query_manager.process_query, args=(data,))
    thread.start()
    return jsonify({"status": True}, 200)


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
    query_id = data.get('QID')
    logger.info(f"[APP] File {filename} with hash {filehash} found at {host}:{port}")
    query_manager.addQueryResponse(query_id, data)
    # file_manager.initiate_file_download(host, port, filename)
    return jsonify({"status": "success", })


@app.route('/ping', methods=["GET"])
def ping():
    return jsonify({"status": True}, 201)


# test endpoints to initiate queries
@app.route('/init_query', methods=["POST"])
def init_query():
    """
    Test function to trigger a /query
    data will include following
    filename = data.get("filename")
    filehash = data.get("filehash")
    sender_host = data.get("host")
    sender_port = data.get("port")
    ttl = data.get("ttl", 2)  # time to live
    query_id = data.get("QID")
    """
    data = request.get_json()
    query = query_manager.send_query(data)
    return jsonify({"status": True, "QID": query.id}, 201)


@app.route('/query_results/<qid>', methods=['GET'])
def get_query_results(qid):
    query = query_manager.getQuery(qid)
    if query:
        if len(query.responses)>0:
            return jsonify({"status": True, "QID": query.id, "msg": "Query results found.", "results":query.responses}, 200)
        else:
            return jsonify({"status": False, "QID": query.id, "msg": "No results found.", "results":[]}, 200)
    else:
        return jsonify({"status": False, "QID": None, "msg": "No query found."}, 404)
    

@app.route('/stats_all', methods=['GET'])
def get_stats_all():
    try:
        return jsonify({"status": True,"peers": peer_manager.toDict(), "queries": query_manager.toDict()[::-1]}, 200)
    except Exception:
        return jsonify({"status": False,"peers": [], "queries": []}, 201)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-cfg', required=True, type=str, help='Path to the configuration module')
    args = parser.parse_args()
    
    config_module = importlib.import_module(args.config)
    cfg = config_module.cfg
    
    logger = get_debug_logger('log', f'logs/log_{cfg.peer.configuration["self"]["port"]}.log')

    peer_manager = PeerManager(cfg=cfg, logger=logger)
    file_manager = FileManager(cfg=cfg, logger=logger)
    query_manager = QueryManager(peer_manager, file_manager, cfg=cfg, logger=logger)

    update_shared_files()
    scheduler.init_app(app)
    scheduler.start()

    app.run(debug=False, host=cfg.peer.configuration['self']['host'], port=cfg.peer.configuration['self']['port'])
    
    

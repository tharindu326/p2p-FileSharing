import time
from flask import Flask,jsonify,request,Response,send_file
from flask_apscheduler import APScheduler
import json
import requests
import os
import asyncio, aiohttp
from threading import Thread

from peer import Peer
from file import SharedFile

peers = []
shared_files = []

self_host = None
self_port = None

app = Flask(__name__)
scheduler = APScheduler()


@scheduler.task('interval', id='update_shared_files', seconds=30)
def update_shared_files():
    files = os.listdir('../shared')
    files_list = []

    for file in files:
        f = SharedFile(file)
        files_list.append(f)
    global shared_files
    shared_files = files_list
    print("Shared files list updated.")
    print([file.filename for file in shared_files])


@scheduler.task('interval', id='my_heartbeat', seconds=30)
def my_heartbeat():
    for peer in peers:
        send_heartbeat(peer.host, peer.port)


def send_heartbeat(host, port):
    try:
        url = "http://"+str(host)+":"+str(port)+"/heartbeat"
        data = {
        "host": self_host,
        "port": self_port,
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            pass
    except Exception as e:
        print("Failed sending heartbeat ", host,"-", port)
        print(e)


def is_peer(host, port):
    for peer in peers:
        if peer.host==host and peer.port==port:
            return True
    return False


def is_local(filename, hash):
    print("Searching for file : ", filename)
    print("Local files : ", [file.filename for file in shared_files])
    for file in shared_files:
        if file.filename == filename or file.hash == hash:
            return True,file
    return False, None


def register_peer(host, port):
    if not is_peer(host,port):
        p = Peer(host,port)
        peers.append(p)
        print(p.whois()," joined.")


def join_peer(host, port):
    #ping
    url = "http://"+str(host)+":"+str(port)+"/ping"
    response = requests.get(url)
    if response.status_code == 200:
        #join
        url = "http://"+str(host)+":"+str(port)+"/join"
        data = {
            "host": self_host,
            "port": self_port,
        }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            #register
            register_peer(host, port)
        else:
            print("Peer no response")
    else:
        print("Peer no response")


def peers_to_dict():
    peerdict = []
    for peer in peers:
        peerdict.append({'host':peer.host,'port':peer.port})
    return peerdict


@app.route('/')
def hello_world():
    return 'Hello, World!'


async def handle_query_message2(message):
    is_local_true, file_local = is_local(message['filename'], message['filehash'])
    if is_local_true:
        print("Query hit : Local file found.")
        data = {'filename':file_local.filename, 'filehash':file_local.hash, 'host':self_host, 'port':self_port}
        async with aiohttp.ClientSession() as session:
            response = await session.post(url="http://"+str(message['host'])+":"+str(message['port'])+"/query_hit",
                                            data=data,
                                            headers={"Content-Type": "application/json"})
            print(await response.json())
    else:
        print("Query : No local file found.")
        async with aiohttp.ClientSession() as session:
            for peer in peers:
                if not (peer.host==message["host"] and peer.port==message["port"]):
                    print("Forwarding query to ", peer.whois())
                    response = await session.post(url="http://"+str(peer.host)+":"+str(peer.port)+"/query",
                                                data=message,
                                                headers={"Content-Type": "application/json"})   
                    print(await response.json())   

def handle_query_message(host, port, filename, filehash, ttl):
    is_local_true, file_local = is_local(filename, filehash)
    if is_local_true:
        print("Query hit : Local file found.")
        url = "http://"+str(host)+":"+str(port)+"/query_hit"
        data = {'host':self_host,'port':self_port,'filename':file_local.filename,'filehash':file_local.hash}

        response = requests.post(url, json=data)
    else:
        print("Query : No local file found.")
        print(ttl)
        if ttl > 0:
            for peer in peers:
                if not (peer.host==host and peer.port==port):
                    print("Forwarding query to ", peer.whois())
                    url = "http://"+str(peer.host)+":"+str(peer.port)+"/query"
                    data = {'host':host,'port':port,'filename':filename,'filehash':filehash,'ttl':ttl-1}

                    response = requests.post(url, json=data)
        else:
            print("Exhausted TTL.")


@app.route('/query',methods=["POST"])
def query():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)
    filename = data.get("filename", None)
    filehash = data.get("filehash", None)
    ttl = data.get("ttl", 2)

    #asyncio.ensure_future(handle_query_message({'host':host,'port':port,'filename':filename,'filehash':filehash}))
    thread = Thread(target=handle_query_message, args=(host,port,filename,filehash,ttl))
    thread.start()

    return jsonify({
        "status": True
        })


@app.route('/query_hit',methods=["POST"])
def query_hit():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)
    filename = data.get("filename", None)
    filehash = data.get("filehash", None)

    print("Query hit message received.")

    return jsonify({
        "status": True
        })


@app.route('/peer_query',methods=["GET"])
def peer_query():
    peerlist = peers_to_dict()
    return jsonify({
        "status": True,
        "peers": peerlist
        })


@app.route('/join',methods=["POST"])
def join():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)

    if host and port:
        register_peer(host, port)
        print([peer.whois() for peer in peers])
        return jsonify({
        "status": True
        })

    return jsonify({
        "status": False
        })


@app.route('/ping',methods=["GET"])
def ping():
    return jsonify({
        "status": True
        })


@app.route('/heartbeat',methods=["POST"])
def heartbeat():
    data = request.get_json()
    host = data.get("host", None)
    port = data.get("port", None)

    print("Received heatbeat - ", host,"-",port)

    return jsonify({
        "status": True
        })


@app.route('/download',methods=["GET"])
def download_file():
    filename = request.args.get('filename')
    if filename:
        try:
            return send_file(f'..shared/{filename}', as_attachment=True)
        except FileNotFoundError:
            return "File not found", 404
    else:
        return "Please provide a filename parameter", 400


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)
        print(config)

        self_config = config["self"]

        self_host = config["self"]["host"]
        self_port = config["self"]["port"]

        peer_config = config["peers"]

        for peer in peer_config:
            try:
                join_peer(peer["host"], peer["port"])
            except Exception as e:
                print("Failed joining with peer ", peer)
                print(e)

    try:
        update_shared_files()
    except Exception as e:
        print(e)

    scheduler.init_app(app)
    scheduler.start()

    app.run(debug=True,host="0.0.0.0",port=self_port)


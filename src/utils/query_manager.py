import os
import requests
from datetime import datetime
import sys
sys.path.append('../src')
from src.config import cfg
from src.query import Query
from src.peer import logger


class QueryManager:
    def __init__(self, peer_manager, file_manager):
        self.peer_manager = peer_manager
        self.file_manager = file_manager
        self.self_host = cfg.peer.configuration['self']['host']
        self.self_port = cfg.peer.configuration['self']['port']
        self.queries = []

    def getQuery(self, query_id):
        for query in self.queries:
            if str(query.id) == query_id:
                return query
        return None

    def addQuery(self, query):
        self.queries.append(query)

    def addQueryResponse(self, query_id, data):
        """Add query hit response data to query response list."""
        query = self.getQuery(query_id)
        filename = data.get('filename')
        filehash = data.get('filehash')
        host = data.get('host')
        port = data.get('port')
        timestamp = datetime.now()
        if query:
            query.addResponse({'QID':query_id, 'timestamp':timestamp,'filename':filename, 'filehash':filehash,'host':host,'port':port})

    def is_local(self, filename, hash):
        """Check if the file is available in the local shared directory."""
        return self.file_manager.getSharedFile(filename, hash)

    def forward_query(self, sender_host, sender_port, filename, filehash, ttl, query_id):
        """Forward the query to other peers, excluding the sender."""
        for peer in self.peer_manager.peers:
            # Not send the query back to the peer who sent it to us
            if peer.host == sender_host and peer.port == sender_port:
                continue
            # Decrease TTL by 1 to prevent infinite flooding
            if ttl > 0:
                peer.send_query(sender_host, sender_port, filename, filehash, ttl - 1, query_id)

    def process_query(self, data):
        """Process a file query by checking local files or forwarding to peers."""
        filename = data.get("filename")
        filehash = data.get("filehash")
        sender_host = data.get("host")
        sender_port = data.get("port")
        ttl = data.get("ttl", 2)  # time to live
        query_id = data.get("QID")

        found_locally, file = self.is_local(filename, filehash)
        if found_locally:
            # Send a query hit back to the requester
            logger.info(f"[QUERY] File {filename} found locally at {file}. Sending query hit back to requester.")
            self.send_query_hit(sender_host, sender_port, file.filename, file.hash, query_id)
        else:
            # Forward the query to other peers
            logger.info(f"[QUERY] File {filename} not found locally. Forwarding query to other peers.")
            self.forward_query(sender_host, sender_port, filename, filehash, ttl - 1, query_id)

    def send_query_hit(self, requester_host, requester_port, filename, filehash, query_id):
        """Send a query hit back to the requester indicating the file was found."""
        url = f"http://{requester_host}:{requester_port}/query_hit"
        data = {
            "filename": filename,
            "filehash": filehash,
            "host": self.self_host,
            "port": self.self_port,
            "QID": query_id
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logger.info(f"[QUERY] Query hit successfully sent to {requester_host}:{requester_port}")
            else:
                logger.error(f"[QUERY] Failed to send query hit to {requester_host}:{requester_port}, status code: {response.status_code}")
        except requests.exceptions.RequestException as err:
            logger.error(f"[QUERY] Error sending query hit to {requester_host}:{requester_port}: {err}")

    def send_query(self, data):
        filename = data.get("filename")
        filehash = data.get("filehash")
        query = Query(filename, filehash)
        self.addQuery(query)
        peers = self.peer_manager.getActivePeers()
        for peer in peers:
            url = f"http://{peer.host}:{peer.port}/query"
            data = {
                "filename": filename,
                "filehash": filehash,
                "host": self.self_host,
                "port": self.self_port,
                "ttl": cfg.network.max_ttl,
                'QID': str(query.id)
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logger.info(f"[QUERY] Query sent successfully sent to {peer.host}:{peer.port}")
            else:
                logger.error(
                    f"[QUERY] Failed to send query to {peer.host}:{peer.port}, status code: {response.status_code}")
        return query
    
    def toDict(self):
        queries = [query.toDict() for query in self.queries]
        return queries

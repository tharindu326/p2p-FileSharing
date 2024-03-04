import os
import requests
import sys
sys.path.append('../src')
from src.config import cfg
from src.query import Query
from src.logger import get_debug_logger
query_logger = get_debug_logger('query', f'logs/query.log')


class QueryManager:
    def __init__(self, peer_manager, file_manager):
        self.peer_manager = peer_manager
        self.file_manager = file_manager
        self.self_host = cfg.peer.configuration['self']['host']
        self.self_port = cfg.peer.configuration['self']['port']
        self.queries = []

    def getQuery(self, query_id):
        for query in self.queries:
            if query.id == query_id:
                return query
        return None

    def addQuery(self, query):
        self.queries.append(query)

    def addQueryResponse(self, query_id, data):
        query = self.getQuery(query_id)
        if query:
            query.addResponse(data)

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
                peer.send_query(filename, filehash, ttl - 1, query_id)

    def process_query(self, data):
        """Process a file query by checking local files or forwarding to peers."""
        filename = data.get("filename")
        filehash = data.get("filehash")
        sender_host = data.get("host")
        sender_port = data.get("port")
        ttl = data.get("ttl", 2)  # time to live
        query_id = data.get("QID")

        found_locally, file_path = self.is_local(filename, filehash)
        if found_locally:
            # Send a query hit back to the requester
            query_logger.info(f"File {filename} found locally at {file_path}. Sending query hit back to requester.")
            self.send_query_hit(sender_host, sender_port, filename, filehash, query_id)
        else:
            # Forward the query to other peers
            query_logger.info(f"File {filename} not found locally. Forwarding query to other peers.")
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
                query_logger.info(f"Query hit successfully sent to {requester_host}:{requester_port}")
            else:
                query_logger.error(f"Failed to send query hit to {requester_host}:{requester_port}, status code: {response.status_code}")
        except requests.exceptions.RequestException as err:
            query_logger.error(f"Error sending query hit to {requester_host}:{requester_port}: {err}")

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
                'QID': query.id
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                query_logger.info(f"Query sent successfully sent to {peer.host}:{peer.port}")
            else:
                query_logger.error(
                    f"Failed to send query to {peer.host}:{peer.port}, status code: {response.status_code}")

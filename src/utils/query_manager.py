import os
import requests
from src.config import cfg


class QueryManager:
    def __init__(self, peer_manager, file_manager):
        self.peer_manager = peer_manager
        self.file_manager = file_manager
        self.self_host = cfg.peer.configuration['self']['host']
        self.self_port = cfg.peer.configuration['self']['port']

    def is_local(self, filename):
        """Check if the file is available in the local shared directory."""
        for shared_file in self.file_manager.shared_files:
            if shared_file.filename == filename:
                return True, os.path.join(self.file_manager.shared_directory, filename)
        return False, None

    def forward_query(self, sender_host, sender_port, filename, filehash, ttl):
        """Forward the query to other peers, excluding the sender."""
        for peer in self.peer_manager.peers:
            # Not send the query back to the peer who sent it to us
            if peer.host == sender_host and peer.port == sender_port:
                continue
            # Decrease TTL by 1 to prevent infinite flooding
            if ttl > 0:
                peer.send_query(filename, filehash, ttl - 1)

    def process_query(self, data):
        """Process a file query by checking local files or forwarding to peers."""
        filename = data.get("filename")
        filehash = data.get("filehash")
        sender_host = data.get("host")
        sender_port = data.get("port")
        ttl = data.get("ttl", 2)  # time to live

        found_locally, file_path = self.is_local(filename)
        if found_locally:
            # Send a query hit back to the requester
            print(f"File {filename} found locally at {file_path}. Sending query hit back to requester.")
            self.send_query_hit(sender_host, sender_port, filename, filehash)
        else:
            # Forward the query to other peers
            print(f"File {filename} not found locally. Forwarding query to other peers.")
            self.forward_query(sender_host, sender_port, filename, filehash, ttl - 1)

    def send_query_hit(self, requester_host, requester_port, filename, filehash):
        """Send a query hit back to the requester indicating the file was found."""
        url = f"http://{requester_host}:{requester_port}/query_hit"
        data = {
            "filename": filename,
            "filehash": filehash,
            "host": self.self_host,
            "port": self.self_port
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Query hit successfully sent to {requester_host}:{requester_port}")
            else:
                print(f"Failed to send query hit to {requester_host}:{requester_port}, status code: {response.status_code}")
        except requests.exceptions.RequestException as err:
            print(f"Error sending query hit to {requester_host}:{requester_port}: {err}")

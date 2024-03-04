import requests
import json
from src.config import cfg
from src.peer import Peer, peer_logger


class PeerManager:
    def __init__(self):
        self.peers = []
        self.self_host = cfg.peer.configuration['self']['host']
        self.self_port = cfg.peer.configuration['self']['port']
        for peer in cfg.peer.configuration["peers"]:
            self.join_peer(peer["host"], peer["port"])
        self.get_peer_lists()

    def is_peer(self, host, port):
        """Check if a given host and port combination is already a known peer."""
        if (self.self_host == host) and (self.self_port == port):
            return True
        return any(peer.host == host and peer.port == port for peer in self.peers)
    
    def add_peers_to_list(self, new_peers):
        """Add new peer details to peers."""
        for peer in new_peers:
            if (self.self_host == peer['host']) and (self.self_port == peer['port']):
                pass
            else:
                if not self.is_peer(peer['host'], peer['port']):
                    new_peer = Peer(peer['host'], peer['port'])
                    new_peer.status = 'inactive'
                    self.peers.append(new_peer)

    def peer_liveness_check(self):
        """Check peer liveness."""
        for peer in self.getActivePeers():
            time_since_last_update = peer.timeSinceLastUpdate()
            if time_since_last_update > 300:
                peer.disconnect()

        active_peers = self.getActivePeers()
        peer_logger.info("Peer liveness check...")
        peer_logger.info(f"Active peers ({len(active_peers)}):")
        peer_logger.info([peer.get_address() for peer in active_peers])

    def get_peer_lists(self):
        """Retrieve peer lists from neigbouring peers."""
        peer_list = []
        for peer in self.getActivePeers():
            try:
                url = f"http://{peer.host}:{peer.port}/get_peers"
                data = {"host": self.self_host, "port": self.self_port}
                response = requests.post(url, json=data)
                response_data = json.loads(response.text)
                if response_data['status']:
                    self.add_peers_to_list(response_data['peers'])
                    peer_logger.info([peer.get_address() for peer in self.peers])
            except Exception as err:
                peer_logger.error(f"Failed retrieving peer list from {peer.host}-{peer.port}: {err}")

    def join_peer(self, host, port):
        """Attempt to join a new peer by sending a ping and then a join request."""
        try:
            ping_response = requests.get(f"http://{host}:{port}/ping")
            if ping_response.status_code == 200:
                join_response = requests.post(f"http://{host}:{port}/join", json={"host": self.self_host, "port": self.self_port})
                if join_response.status_code == 200:
                    self.peers.append(Peer(host, port))
        except Exception as err:
            peer_logger.error(f"Failed to join peer {host}:{port}: {err}")

    def send_heartbeat(self):
        """Send a heartbeat signal to all known peers."""
        for peer in self.getActivePeers():
            try:
                url = f"http://{peer.host}:{peer.port}/heartbeat"
                data = {"host": self.self_host, "port": self.self_port}
                response = requests.post(url, json=data)
            except Exception as err:
                peer_logger.error(f"Failed sending heartbeat to {peer.host}-{peer.port}: {err}")

    def getPeer(self, host, port):
        for peer in self.peers:
            if peer.host == host and peer.port == port:
                return peer
        return None

    def addPeer(self, peer):
        self.peers.append(peer)

    def update_heartbeat(self, host, port):
        peer = self.getPeer(host, port)
        if peer:
            peer.update('active')

    def getActivePeers(self):
        peers = [peer for peer in self.peers if peer.isActive()]
        return peers
    
    def getInactivePeers(self):
        peers = [peer for peer in self.peers if not peer.isActive()]
        return peers


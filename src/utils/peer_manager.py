import requests
from src.config import cfg
from src.peer import Peer


class PeerManager:
    def __init__(self):
        self.peers = []
        self.self_host = cfg.peer.configuration['self']['host']
        self.self_port = cfg.peer.configuration['self']['port']
        for peer in cfg.peer.configuration["peers"]:
            self.join_peer(peer["host"], peer["port"])

    def is_peer(self, host, port):
        """Check if a given host and port combination is already a known peer."""
        return any(peer.host == host and peer.port == port for peer in self.peers)

    def join_peer(self, host, port):
        """Attempt to join a new peer by sending a ping and then a join request."""
        try:
            ping_response = requests.get(f"http://{host}:{port}/ping")
            if ping_response.status_code == 200:
                join_response = requests.post(f"http://{host}:{port}/join", json={"host": self.self_host, "port": self.self_port})
                if join_response.status_code == 200:
                    self.peers.append(Peer(host, port))
        except Exception as err:
            print(f"Failed to join peer {host}:{port}: {err}")

    def send_heartbeat(self):
        """Send a heartbeat signal to all known peers."""
        for peer in self.peers:
            try:
                url = f"http://{peer.host}:{peer.port}/heartbeat"
                data = {"host": self.self_host, "port": self.self_port}
                response = requests.post(url, json=data)
            except Exception as err:
                print(f"Failed sending heartbeat to {peer.host}-{peer.port}: {err}")

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


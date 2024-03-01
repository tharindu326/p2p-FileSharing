from datetime import datetime
import requests


class Peer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.status = 'active'
        self.last_seen = datetime.now()

    def get_address(self) -> str:
        """Return the address of the peer in the format 'host:port'."""
        return f"{self.host}:{self.port}"

    def update(self, status: str = 'active') -> None:
        """Update the peer's status and refresh the last seen timestamp."""
        self.status = status
        self.last_seen = datetime.now()
        print(f"Updated {self.get_address()} to status '{self.status}' at {self.last_seen}")

    def send_query(self, filename: str, filehash: str, ttl: int, query_id) -> None:
        """Send a file query to this peer."""
        url = f"http://{self.host}:{self.port}/query"
        data = {
            "filename": filename,
            "filehash": filehash,
            "ttl": ttl,
            "QID": query_id
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Query successfully sent to {self.host}:{self.port}")
            else:
                print(f"Failed to send query to {self.host}:{self.port}, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending query to {self.host}:{self.port}: {e}")

    def isActive(self):
        status = False
        if self.status == 'active':
            status = True
        return status




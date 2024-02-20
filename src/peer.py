class Peer:
    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port

    def whois(self):
        return str(self.host)+"-"+str(self.port)
    
    def update(self):
        return True
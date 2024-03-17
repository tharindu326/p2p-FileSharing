import requests
import json
from pyvis.network import Network


nodes = [{'host':'127.0.0.1','port':8081},{'host':'127.0.0.1','port':8082},{'host':'127.0.0.1','port':8083},{'host':'127.0.0.1','port':8084},{'host':'127.0.0.1','port':8085},{'host':'127.0.0.1','port':8086}]

peer_links = []

def add_peers(node, peers):
    for peer in peers:
        if peer['status']=='active':
            link = (node,f"{peer['host']}:{peer['port']}")
            peer_links.append(link)


def get_peer_lists(nodes):
    """Retrieve peer lists from neighbouring peers."""

    for node in nodes:
        url = f"http://{node['host']}:{node['port']}/stats_all"
        try:
            response = requests.get(url)
            #print(response.json())
            peers = json.loads(response.text)[0]['peers']
            print(peers)
            add_peers(f"{node['host']}:{node['port']}", peers)
        except Exception as e:
            print(f"Error fetching peers: {e}")

get_peer_lists(nodes)
network = Network()
nodeslist = [f"{node['host']}:{node['port']}" for node in nodes]

for node in nodeslist:
    network.add_node(node)

for link in peer_links:
    network.add_edge(link[0], link[1])

network.show('nodes.html',notebook=False)
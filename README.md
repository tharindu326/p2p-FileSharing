# Fully Distributed Peer-to-Peer File Sharing Network

## Introduction

![Intro](data/intro.png)

A fully distributed peer-to-peer file sharing network allowing peers to share and search for files within the network, and download files directly among peers. This system aims to implement functionalities similar to those found in Gnutella.

## Functionalities

- Peers share files with the network without the need for central servers; they store peer (neighbor) pointers and file directories themselves.
- The network facilitates periodic heartbeat signals among peers to update their availability.
- Peers can search for files in the network using a gossip protocol.
- The system enables peer-to-peer file retrieval.
- Caching/distributed file directory and structured query routing.

## Architecture

![Architecture](data/arch_updated.png)

## Communication Mechanism

Our peer-to-peer file sharing network, inspired by Gnutella's architecture, employs a fully distributed communication mechanism devoid of central coordination. Peers dynamically join the network, discovering others and maintaining a list of active connections. File searches are propagated through the network via a flood-based query system, where each peer forwards search queries to its neighbors, exponentially increasing the search's reach. Successful queries result in direct, decentralized file transfers between peers, leveraging the network's distributed nature to enhance scalability and fault tolerance. This mechanism ensures efficient resource discovery and sharing across the network, including the principles of robust, decentralized communication.


For Implementation details, see the [Documentation](docs/Documentation.md).

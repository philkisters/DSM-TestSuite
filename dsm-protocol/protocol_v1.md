# Protocoll for the P2P Network

## General Concept
- each peer sub process managed by the peer manager (../orchestrator/manager.py). 
- Communication over TCP with newline-delimited JSON in, with two Modes:
  - Debug: local with ip and port
  - Test: Over the course proxy with a fixed IP and Port. Identification of other peers by `NetworkId` and `PeerId`
- Request / Response system (open TCP connection, send request, wait for response, close connection)
- P2P Structure (similar to Chord, at the beginning without fingers) is symmetrical, when I am your predecessor you are my successor.
- Peers in the network are sorted by the SHA-256 hashed peerId.
- Images have an arbitrary name used as the image Id. That can be searched in the network. An image is stored on that peer, which has the next smaller or equal hash. To get the hash of the image the image id is hashed with the SHA256 algorithm. 

## Base Identity
```text
- NetworkId
- PeerId
```

## Base Image
```
- ImageId
```

## Ring Structure
Peers in a network are ordered by the SHA256 Hashed PeerID.

## Hashing
Hashes are computed as SHA-256 over the UTF-8 bytes of the ID string, with no normalization. Peers hash `peerId`, images hash `imageId` (e.g. `image-17.png`). Digests are compared as unsigned 256-bit big-endian integers (equivalently, byte-wise lexicographic order). Ties between equal hashes are broken by comparing the raw ID strings.

## Base Message Structure
```json
{
    "sender": {
      "networkId": "my-network",
      "peerId": "my-id"
    },
    "receiver": {
      "networkId": "my-network",
      "peerId": "target-id"
    },
    "message-code": 1,
    "content": {
      ...
    }
}
```

## Message Code
- Error: -1
- Ack: 0
- Join: 1
- Leave: 2
- GetNeighborsRequest: 3
- GetNeighborsResponse: 4

## Message Flow
- Join -> Ack (1 -> 0)
- Leave -> Ack (2 -> 0)
- GetNeighborsRequest -> GetNeighborsResponse (3 -> 4)

The response message reverses the sender and receiver and is send via the same TCP connection.

## Message Content

### Error: -1
```json
{
    ...
    "content": {
      "message": "..."
    }
}
```
### Ack: 0
```json
{
    ...
    "content": {
    }
}
```
### Join: 1
```json
{
    ...
    "content": {
    }
}
```
### Leave: 2
```json
{
    ...
    "content": {
      "predecessor":{
        "networkId": "my-network",
        "peerId": "predecessor-id"
      },
      "successor":{
        "networkId": "my-network",
        "peerId": "successor-id"
      },
    }
}
```
### GetNeighborsRequest: 3
```json
{
    ...
    "content": {
    }
}
```
### GetNeighborsResponse: 4
```json
{
    ...
    "content": {
      "predecessor":{
        "networkId": "my-network",
        "peerId": "predecessor-id"
      },
      "successor":{
        "networkId": "my-network",
        "peerId": "successor-id"
      },
    }
}
```
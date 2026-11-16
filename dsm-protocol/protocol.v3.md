# Protocoll for the P2P Network

## General Concept
- each peer sub process managed by the peer manager (../orchestrator/manager.py). 
- Communication over TCP with newline-delimited JSON in, with two Modes:
  - Debug: local with ip and port
  - Test: Over the course proxy with a fixed IP and Port. Identification of other peers by `NetworkId` and `PeerId`
- Request / Response system (open TCP connection, send request, wait for response, close connection)
- P2P Structure (similar to Chord) is symmetrical, when I am your predecessor you are my successor.
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

## Ring Repair
There are two cases to repair:
1. A known other peer is not responding (predecessor, successor, finger). Therefore I need to find a new matching peer in the network.
2. The peer realizes that the network split into multiple non-connected rings. Therefore we need to merge the rings again. Here nodes should rejoin the ring containing the peer with the smallest hash.


### Leave
To leave gracefully, send a leave message with your predecessor and successor to your two neighbors, so that they can fix the ring, without waiting for their heartbeat to detect the missing node. 

Additionally, when leaving the network the peer needs to calculate the reverse finger table and send leave messages to all peers having a finger pointing to them. 

Nonetheless, your peer should also support the option that it gets "crashed" by the manager, so that we can test non-gracefull leaves.

## Data Structure
The network allows to store images only. 
These are a fixed set of example images of 32x32 pixel images. 
They are named image-X.png where X is a number between 0 and 6079, both included. 

### Putting an image
To put an image the image Id is hashed and put onto any peer.
Peers acknowledge a valid image immediately, without waiting for forwarding or
storage by other peers. Forwarding happens independently; an acknowledgement
does not guarantee that the image has reached its responsible peer.
If the image's ring key is in the interval `(predecessor, this peer]`, this peer is responsible and stores the image.
Otherwise, it forwards the image to the predecessor or successor in the direction of the image's ring key.
This way images should be distributed evenly accross the network.

### Searching an Image
To search an image, the requester hashes the searched image ID and traverses the ring to the responsible peer. It can list the images available on that peer or request the image directly.
A peer answers a `RequestImage` only from its local storage: it returns the image in a `PutImage` response if present, or an `Error` response if the image is not stored locally.

## Base Message Structure
```json
{
    "sender": {
      "network_id": "my-network",
      "peer_id": "my-id"
    },
    "receiver": {
      "network_id": "my-network",
      "peer_id": "target-id"
    },
    "code": 1,
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
- GetFingersRequest: 5
- GetFingersResponse: 6
- PutImage: 7
- ListImageRequest: 8
- ListImageResponse: 9
- RequestImage: 10

## Message Flow
- Join -> Ack (1 -> 0)
- Leave -> Ack (2 -> 0)
- GetNeighborsRequest -> GetNeighborsResponse (3 -> 4)
- GetFingersRequest - GetFingersResponse (5 -> 6)
- PutImage -> ACK (7 -> 0)
- ListImageRequest -> ListImageResponse (8 -> 9)
- RequestImage -> PutImage (10 -> 7)

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
        "network_id": "my-network",
        "peer_id": "predecessor-id"
      },
      "successor":{
        "network_id": "my-network",
        "peer_id": "successor-id"
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
        "network_id": "my-network",
        "peer_id": "predecessor-id"
      },
      "successor":{
        "network_id": "my-network",
        "peer_id": "successor-id"
      },
    }
}
```

### GetFingersRequest: 5
```json
{
    ...
    "content": {
    }
}
```
### GetFingersResponse: 6
```json
{
    ...
    "content": {
      "fingers": [
        {
          "network_id": "my-network",
          "peer_id": "finger-0-id"
        },
        {
          "network_id": "my-network",
          "peer_id": "finger-1-id"
        },
        ...
      ]
    }
}
```

### PutImage: 7
```json
{
    ...
    "content": {
      "image_id": "image-id",
      "image": "base64 encoded image"
    }
}
```
### ListImageRequest: 8
```json
{
    ...
    "content": {
    }
}
```
### ListImageResponse: 9
```json
{
    ...
    "content": {
      "images": [
        "image-id",
        "image-id1",
        "image-id2",
        "image-id3",
        ...
      ]
    }
}
```
### RequestImage: 10
```json
{
    ...
    "content": {
      "image_id": "searched-image-id"
    }
}
```
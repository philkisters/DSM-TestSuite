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

## Ring Structure
Peers in a network are ordered by the SHA256 Hashed PeerID.

### Join
To join, the peer receives a seed peer from its orchestrator where it starts to join. If the seed is empty it initiates a new network.

#### Joining an existing network
From the seed peer it requests the neighbors and works itself to the position in the ring, where it fits. Here it sets its predecessor and successor and sends a join to them. These will compair their hashed Ids and their neighbor hashed Ids to see if this is a valid join. If so they send an acknowledgement and update their successor / predecessor. Otherwise send an error message.
If one direction sends an acknowledgement and the other sends an error, the peer starts to repair (see below). 

#### Initiating a network
If this is the first peer for a network. It should set itself as a neighbor. That way new peers know that they can directly join.

If you are the second peer to the network, you will add the only existing peer in both directions. The same is done by the existing peer. That whay you are a two peer ring. 

The third peer, needs to compare its hashed ID with the two peers and correctly set its predecessor and successor, then join both peers, which will do the same. 

After the third peer the join is always the same as described before. 


### Heartbeats
To detect network defects we send GetNeighborRequests (3) in defined intervals to see if we are still our neighbors neighbor.
If we are, everything is fine. If not we should try to repair. 

### Repair
If we see that we are not our neighbors neighbor, we need to repair. This has a similar logic like the join. Traverse the ring and find my own correct spot, join there.

### Leave
To leave gracefully, send a leave message with your predecessor and successor to your two neighbors, so that they can fix the ring, without waiting for their heartbeat to detect the missing node. 

Nonetheless, your peer should also support the option that it gets "crashed" by the manager, so that we can test non-gracefull leaves.

## Data Structure
The network allows to store images only. 
These are a fixed set of example images of 32x32 pixel images. 
They are named image-X.png where X is a number between 0 and 6079, both included. 

### Putting an image
To put an image the "putter" needs to find the correct peer, which hashed Id is smaller or equal to the hashed image id. 
If an image hash is smaller than the smallest hash in the ring the largest peer is responsible. 
This way images should be distributed evenly accross the network.

If a peer receives a `PutImage` message for an image ID it is not resposible for. It should respond with an error message. Otherwise store the image and send an acknowledge message. 

### Searching an Image
To search an image the searching should hash the searched image id and traverse the ring to the correct peer. It can then first list the images available on that peer, to see if that image exists. Otherwise it can also directly request the image. 
If the image exists, it should receive the image. Otherwise a peer will send an error response.

## Error Handling
The most likely error is, that a peer can not reach another peer in the network, since it went offline ungracefully and neighbors have not yet repaired. 
If that is the case, the peer should store the information of the last reachable peer and traverse the ring in the other direction to find its spot it that direction. 
If it finds its position just do a regular join. 
If again a peer is not answering, the peer should send a join to both ends of the ring and set them as their neighbor. 
Most likely they will reject the join until, they repair the ring. 
The peer should be resilient to keep the two correct neighbors and periodically with the heartbeat check if the prior neighbors are back online.

## Hashing
Hashes are computed as SHA-256 over the UTF-8 bytes of the ID string, with no normalization. Peers hash `peerId`, images hash `imageId` (e.g. `image-17.png`). Digests are compared as unsigned 256-bit big-endian integers (equivalently, byte-wise lexicographic order). Ties between equal hashes are broken by comparing the raw ID strings.

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
          "networkId": "my-network",
          "peerId": "finger-0-id"
        },
        {
          "networkId": "my-network",
          "peerId": "finger-1-id"
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
      "imageId": "image-id",
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
      "imageId": "searched-image-id"
    }
}
```
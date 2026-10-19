# Proxy Peer Registration Protocol

This document describes the proxy's peer registration endpoint. It is a small TCP
protocol used by peers to tell the proxy where they can receive peer-to-peer messages.
It is separate from the proxy's message-relay and HTTP administration endpoints.

## Connection and message format

- The default registration port is TCP `9002` (`REGISTER_PORT` can change it).
- Each request uses a new TCP connection.
- Send one JSON object followed by a newline (`\n`).
- Read one JSON response followed by a newline.
- Close the connection after the response.
- The proxy learns the peer's **host** from the IP address of the registration
  connection. Do not send a host in the JSON request.
- The `port` is the peer's P2P listener port, not the proxy's registration port.

All field names are case-sensitive and use `snake_case`.

## Register or update a peer

Send `action: "register"` with the peer identity and its listening port:

```json
{
  "action": "register",
  "network_id": "group-04",
  "peer_id": "42",
  "port": 5100
}
```

The `action` field may be omitted; registration is the default action. Both IDs must
be strings and `peer_id` must not be empty. `port` must be an integer from `1` to
`65535`.

Successful response:

```json
{"status": "ok"}
```

Registering a new identity adds it to the proxy's in-memory lookup table. Registering
an identity that already exists updates its host and port. The proxy publishes a
`peer_registered` event for a new peer and a `peer_updated` event for an existing peer.

## Unregister a peer

Send the peer identity with `action: "unregister"`; no port is required:

```json
{
  "action": "unregister",
  "network_id": "group-04",
  "peer_id": "42"
}
```

Successful responses include whether an entry was removed:

```json
{"status": "ok", "removed": true}
```

If the identity was not registered, the request still succeeds, with `"removed": false`.
Removing an existing peer publishes a `peer_unregistered` event. Unregistering a
non-existent peer does not publish that event.

## Errors

Rejected requests receive a JSON error response:

```json
{"status": "error", "message": "'port' must be an integer between 1 and 65535"}
```

For example, the proxy returns an error if the request is not a JSON object, the peer
identity is invalid, the port is outside the allowed range, or the action is unknown.
The connection is still closed after the response.

## Example using netcat

```sh
printf '%s\n' '{"action":"register","network_id":"group-04","peer_id":"42","port":5100}' \
  | nc localhost 9002
```

## Peer lifecycle

A peer should register after its P2P listener is ready to accept connections. It should
unregister when it gracefully leaves or shuts down. The proxy also checks registered
peers for liveness and can remove one that stops responding.

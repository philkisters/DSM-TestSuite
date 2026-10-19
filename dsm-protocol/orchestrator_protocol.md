# Student Orchestrator API

This guide explains the REST API described by [`orchestrator.v1.json`](./orchestrator.v1.json).
The API lets you start and control peer processes; it does not carry peer-to-peer messages.

## How to send a request

The orchestrator uses HTTP with JSON request and response bodies. Unless noted otherwise,
send a `Content-Type: application/json` header. The default local address is
`http://localhost:8000`; the bind address and port can be configured with
`ORCHESTRATOR_HOST` and `ORCHESTRATOR_PORT`.

Every peer is identified by a pair:

| Field | Meaning | Rules |
| --- | --- | --- |
| `network_id` | The logical network the peer belongs to | Required string, 1–128 characters |
| `peer_id` | The peer's ID within that network | Required string, 1–128 characters |

The same `peer_id` can be used in different networks. Include both fields whenever an
endpoint asks for a peer identity. Field names are case-sensitive and use `snake_case`.
Unknown JSON fields are rejected.

## Endpoints

### `GET /health` — check that the orchestrator is responding

No request body.

```json
{"status": "ok"}
```

### `POST /start` — start a peer process

Starts the peer process and waits for it to become ready. Starting a process does not
automatically make the peer join a network.

Request:

```json
{
  "network_id": "group-04",
  "peer_id": "42"
}
```

Success (`201 Created`):

```json
{
  "network_id": "group-04",
  "peer_id": "42",
  "status": "running"
}
```

### `POST /join` — ask a running peer to join

The optional `bootstrap_peer_id` identifies a peer the joining peer can contact to find
the network. Use `null` (or omit the field) to start a new network.

Request:

```json
{
  "network_id": "group-04",
  "peer_id": "42",
  "bootstrap_peer_id": "41"
}
```

Success (`200 OK`):

```json
{
  "network_id": "group-04",
  "peer_id": "42",
  "status": "joined"
}
```

### `POST /leave` — gracefully leave the network

The peer leaves the network but its process keeps running. It can be asked to join
again later.

Request:

```json
{
  "network_id": "group-04",
  "peer_id": "42"
}
```

Success (`200 OK`):

```json
{
  "network_id": "group-04",
  "peer_id": "42",
  "status": "left"
}
```

### `POST /kill` — stop a peer process

Terminates the running process. This is different from `/leave`: it is not a graceful
network departure.

Request:

```json
{
  "network_id": "group-04",
  "peer_id": "42"
}
```

Success (`200 OK`):

```json
{
  "network_id": "group-04",
  "peer_id": "42",
  "status": "killed"
}
```

## Example: start, then join

```sh
curl -i -X POST http://localhost:8000/start \
  -H 'Content-Type: application/json' \
  -d '{"network_id":"group-04","peer_id":"42"}'

curl -i -X POST http://localhost:8000/join \
  -H 'Content-Type: application/json' \
  -d '{"network_id":"group-04","peer_id":"42","bootstrap_peer_id":"41"}'
```

For the first peer in a network, start it in the same way and join with no bootstrap peer:

```sh
curl -i -X POST http://localhost:8000/join \
  -H 'Content-Type: application/json' \
  -d '{"network_id":"group-04","peer_id":"42","bootstrap_peer_id":null}'
```

## Errors

Errors use a JSON body with a human-readable `detail`:

```json
{"detail": "Peer '42' is not running in network 'group-04'"}
```

Common status codes:

| HTTP status | Meaning |
| --- | --- |
| `404 Not Found` | No running peer matches both IDs |
| `409 Conflict` | That peer is already running in the network |
| `422 Unprocessable Entity` | The JSON body is missing, malformed, or has invalid fields |
| `502 Bad Gateway` | The orchestrator could not communicate with the peer |
| `503 Service Unavailable` | The peer process could not be started or did not become ready |

## Peer-to-peer protocol

These HTTP endpoints are the control API. The messages peers exchange with each other
use a separate protocol described in [`protocol.md`](./protocol.md).

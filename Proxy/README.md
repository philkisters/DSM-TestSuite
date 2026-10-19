# DSM Proxy

Routes messages between peers of virtual networks, records all traffic to Postgres
(`proxy.events`) and streams it live. Network conditions (delay, drops, ...) are a TODO
(`apply_conditions` in `src/proxy/relay.py`).

## Endpoints

| Purpose | Protocol | Port | Env var |
|---|---|---|---|
| Message relay | TCP, newline-delimited JSON | 9000 | `PROXY_PORT` |
| Peer registration | TCP, newline-delimited JSON | 9002 | `REGISTER_PORT` |
| Status / peers / live feed | HTTP + WebSocket | 9001 | `ADMIN_PORT` |

- **Relay:** send one protocol message (see `protocol.md`), the receiver's reply is returned.
  The receiver is looked up by `networkId` + `peerId`. Unknown/unreachable receivers get no reply.
- **Register:** `{"action":"register","network_id":"n","peer_id":"p","port":5000}`. The peer host
  is taken from the registration connection's sender IP; `"action":"unregister"` removes it.
  Reply: `{"status":"ok"}` or `{"status":"error","message":"..."}`. The lookup table is in memory only.
- **REST:** `GET /health`, `/status`, `/peers?network_id=`, `/networks/{id}/peers`.
- **WebSocket:** `/ws/{network_id}` pushes JSON events: `type` is `message`, `peer_registered`,
  `peer_updated` or `peer_unregistered`.

## Run locally

Requires Python >= 3.12, [uv](https://docs.astral.sh/uv/) and a Postgres with the migrations applied.

```bash
# from the repository root: database + migrations
docker compose up -d postgres migrate

# start the proxy
cd Proxy
DATABASE_URL=postgresql://dsm:dsm@localhost:5432/dsm uv run python -m proxy
```

Postgres is published on `127.0.0.1:5432` for host-local connections (not exposed to other
machines on the network). Connect with `postgresql://dsm:dsm@localhost:5432/dsm`, or set
`POSTGRES_PASSWORD` to use a different password.

Or run the whole stack in Docker: `docker compose up --build proxy`.

## Quick check

```bash
curl localhost:9001/status
echo '{"network_id":"n","peer_id":"a","port":5000}' | nc localhost 9002
curl localhost:9001/peers
```

## Liveness check

Every `LIVENESS_INTERVAL` seconds (default 5) the proxy sends a `GET_NEIGHBORS_REQUEST` to each
registered peer. A peer that doesn't answer (timeout `LIVENESS_TIMEOUT`, default 2s) is retried
`LIVENESS_RETRIES` times (default 2); if still silent it is removed from the registry and a
`peer_unregistered` event with `"message":"unreachable"` is logged and published to the live feed.

## Registry history

Every register / update / unregister is stored in `proxy.registry_events` (migrations `0002`, `0003`):
`ts, network_id, peer_id, event, host, port, message`. `event` is `peer_registered`, `peer_updated`
or `peer_unregistered`; `message` is `requested` (peer asked to leave) or `unreachable` (liveness check).
Query via `GET /registry-events?network_id=&peer_id=&limit=` or SQL.

# DSM TestSuite

Scaffold. REST API (`/api`) plus a WebSocket for live run updates.

- `POST /api/runs` – body `{"group": "group-4", "challenge": "week-0/first-peer"}`; loads `Challenges/Week-0/first-peer.yml` (case-insensitive), returns 202 + run id (404 if unknown, 409 if the group already has a pending or running run). Each run gets a `net-{group-name}-{challenge-id}-{8-alphanumeric-characters}` network ID.
- `GET /api/runs`, `GET /api/runs/{id}` – status
- `WS /api/runs/{id}/ws` – live events; closes after a terminal status
- `GET /api/groups/{group_id}/uptime` – all-history uptime/downtime totals and percentages from recorded health samples. `ONLINE` and `NOT_RESPONDING` count as uptime; `OFFLINE` counts as downtime. The first sample starts the measurement period, and the latest sample's state is carried through `as_of`.
- OpenAPI schema at `/openapi.json`

Run: `uv run testsuite` · Tests: `uv run pytest`

## Copy Challenges to server
Run the following command from the TestSuite folder
```
rsync -avz --delete Challenges vmadmin@dos-mobs-controller:~/DSM-TestSuite/TestSuite
```
"""HTTP clients for a group's Orchestrator (always port 9090) and the shared Proxy."""
import httpx

from dsm_protocol import Message, Identity, MessageCode

ORCHESTRATOR_PORT = 9090


class ClientError(Exception):
    pass


async def _request(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    try:
        response = await client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        raise ClientError(f"{method} {url} failed: {exc!r}") from exc
    if response.is_error:
        raise ClientError(f"{method} {url} returned {response.status_code}: {response.text}")
    return response


class OrchestratorClient:
    """Only start / join / leave / kill; all P2P traffic goes through the proxy."""

    def __init__(self, vm_ip: str, network_id: str, http: httpx.AsyncClient) -> None:
        self.base_url = f"http://{vm_ip}:{ORCHESTRATOR_PORT}"
        self.network_id = network_id
        self.http = http

    async def _post(self, path: str, body: dict) -> None:
        await _request(
            self.http, "POST", f"{self.base_url}{path}", json={"network_id": self.network_id, **body}
        )
    
    async def _get(self, path: str) -> None:
        await _request(
            self.http, "GET", f"{self.base_url}{path}"
        )
    
    async def health(self) -> None:
        await self._get("/health")

    async def start(self, peer_id: str) -> None:
        await self._post("/start", {"peer_id": peer_id})

    async def join(self, peer_id: str, bootstrap_peer_id: str | None = None) -> None:
        await self._post("/join", {"peer_id": peer_id, "bootstrap_peer_id": bootstrap_peer_id})

    async def leave(self, peer_id: str) -> None:
        await self._post("/leave", {"peer_id": peer_id})

    async def kill(self, peer_id: str) -> None:
        await self._post("/kill", {"peer_id": peer_id})


class ProxyClient:
    def __init__(self, base_url: str, network_id: str, http: httpx.AsyncClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.network_id = network_id
        self.http = http
    
    async def _post(self, path: str, body: dict) -> httpx.Response:
        return await _request(
            self.http, "POST", f"{self.base_url}{path}", json={**body}
        )

    async def peers(self) -> list[dict]:
        response = await _request(self.http, "GET", f"{self.base_url}/api/networks/{self.network_id}/peers")
        return response.json()
    
    async def _send_message(self, message: Message) -> Message:
        response = await _request(
            self.http, "POST",
            f"{self.base_url}/api/message", 
            json=message.to_json(),
        )
        if response.is_error:
            raise ClientError(f"POST {self.base_url}/api/message returned {response.status_code}: {response.text}")
        
        return Message.from_json(response.json())

    
    async def send_get_neighborsmessage(self, peer_name: str) -> Message:
        message = Message(
            sender=Identity(
                network_id=self.network_id,
                peer_id='TestSuite',
            ),
            receiver=Identity(
                network_id=self.network_id,
                peer_id=peer_name,
            ),
            code=MessageCode.GET_NEIGHBORS_REQUEST,
            content={}
        )
        
        return await self._send_message(message)
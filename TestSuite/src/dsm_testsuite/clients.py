"""HTTP clients for a group's Orchestrator (always port 9090) and the shared Proxy."""
import base64
import httpx
from pathlib import Path

from dsm_protocol import Message, Identity, MessageCode

ORCHESTRATOR_PORT = 9090
CHALLENGES_IMAGES_DIR = Path(__file__).parent.parent.parent / "Challenges" / "images"


class HTTPError(Exception):
    """An HTTP request to Orchestrator or Proxy failed with an error status code."""

    def __init__(self, status_code: int | None, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _load_image_as_base64(image_id: str) -> str:
    """Load an image from Challenges/images and encode it as base64.
    
    Args:
        image_id: Image filename (e.g., "image-0.png")
    
    Returns:
        Base64 encoded image data
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
    """
    image_path = CHALLENGES_IMAGES_DIR / image_id
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    return base64.b64encode(image_data).decode("utf-8")


class ClientError(Exception):
    pass


async def _request(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    try:
        response = await client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        raise ClientError(f"{method} {url} failed: {exc!r}") from exc
    if response.is_error:
        raise HTTPError(response.status_code, f"{method} {url} returned {response.status_code}: {response.text}")
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
    
    async def _get(self, path: str, **kwargs) -> httpx.Response:
        return await _request(
            self.http, "GET", f"{self.base_url}{path}", **kwargs
        )

    async def peers(self) -> list[dict]:
        response = await _request(self.http, "GET", f"{self.base_url}/api/networks/{self.network_id}/peers")
        return response.json()
    
    async def message_count(self, exclude_sender: str = "TestSuite") -> int:
        """Count successfully forwarded peer-to-peer messages excluding a sender.
        
        Queries the proxy for the number of messages that were successfully relayed,
        excluding diagnostic/test messages from the specified sender. Useful for counting
        repair messages in recovery scenarios.
        
        Args:
            exclude_sender: Peer sender to exclude (default: TestSuite for diagnostic messages)
        
        Returns:
            Number of successfully forwarded messages (status='forwarded') excluding the sender
        
        Raises:
            ClientError: If the proxy query fails
        """
        try:
            response = await self._get(
                "/api/message-stats",
                params={
                    "network_id": self.network_id,
                    "exclude_sender": exclude_sender,
                    "status": "forwarded"
                }
            )
            return response.json().get("count", 0)
        except ClientError:
            raise
        except Exception as exc:
            raise ClientError(f"Failed to query message count: {exc!r}") from exc
    
    async def messages(self, src_peer: str | None = None, dst_peer: str | None = None,
                       code: int | None = None, limit: int = 1000) -> list[dict]:
        """Forwarded messages of this network (including events not yet persisted), newest first."""
        params = {"network_id": self.network_id, "limit": limit}
        for key, value in (("src_peer", src_peer), ("dst_peer", dst_peer), ("code", code)):
            if value is not None:
                params[key] = int(value) if key == "code" else value
        return (await self._get("/api/messages", params=params)).json()

    async def _send_message(self, message: Message) -> Message:
        response = await _request(
            self.http, "POST",
            f"{self.base_url}/api/message", 
            json=message.to_json(),
        )
        
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
    
    async def send_get_finger_message(self, peer_name: str) -> Message:
        message = Message(
            sender=Identity(
                network_id=self.network_id,
                peer_id='TestSuite',
            ),
            receiver=Identity(
                network_id=self.network_id,
                peer_id=peer_name,
            ),
            code=MessageCode.GET_FINGERS_REQUEST,
            content={}
        )
        
        return await self._send_message(message)
    
    async def send_list_images_message(self, peer_name: str) -> Message:
        message = Message(
            sender=Identity(
                network_id=self.network_id,
                peer_id='TestSuite',
            ),
            receiver=Identity(
                network_id=self.network_id,
                peer_id=peer_name,
            ),
            code=MessageCode.LIST_IMAGE_REQUEST,
            content={}
        )
    
        return await self._send_message(message)

    async def send_put_image_message(self, peer_name: str, image: str) -> Message:
        image_base64 = _load_image_as_base64(image)
        
        message = Message(
            sender=Identity(
                network_id=self.network_id,
                peer_id='TestSuite',
            ),
            receiver=Identity(
                network_id=self.network_id,
                peer_id=peer_name,
            ),
            code=MessageCode.PUT_IMAGE,
            content={"image": image_base64, "image_id": image}
        )

        return await self._send_message(message)

    async def put_images(self, peer_name: str, image_ids: list[str]) -> None:
        """Send multiple images to a peer, each as a base64 encoded string.
        
        Args:
            peer_name: Name of the peer to send images to
            image_ids: List of image filenames to send (e.g., ["image-0.png", "image-1.png"])
        
        Raises:
            ClientError: If any image fails to send
        """
        for image_id in image_ids:
            try:
                response = await self.send_put_image_message(peer_name, image_id)
                if response.code != MessageCode.ACK:
                    raise ClientError(f"Failed to send image {image_id!r} to {peer_name!r}: {response.content.get('message')}")
                
            except Exception as exc:
                raise ClientError(f"Failed to send image {image_id!r} to {peer_name!r}: {exc!r}") from exc
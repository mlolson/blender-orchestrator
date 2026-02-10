"""HTTP client for communicating with Blender add-on."""

import httpx
from typing import Any, Dict, Optional


class BlenderClient:
    """HTTP client for communicating with Blender add-on.

    Manages persistent httpx clients for connection reuse.
    Clients are lazy-initialized on first use.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    def _get_sync_client(self) -> httpx.Client:
        """Get or create the persistent sync HTTP client."""
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(timeout=30.0)
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the persistent async HTTP client."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=30.0)
        return self._async_client

    async def execute(
        self, action: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an action on Blender asynchronously."""
        client = self._get_async_client()
        response = await client.post(
            self.base_url,
            json={"action": action, "params": params or {}},
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error from Blender"))

        return result.get("result", {})

    def execute_sync(
        self, action: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an action on Blender synchronously."""
        client = self._get_sync_client()
        response = client.post(
            self.base_url,
            json={"action": action, "params": params or {}},
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error from Blender"))

        return result.get("result", {})

    async def health_check(self) -> bool:
        """Check if Blender server is running."""
        try:
            client = self._get_async_client()
            response = await client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def health_check_sync(self) -> bool:
        """Check if Blender server is running (synchronous)."""
        try:
            client = self._get_sync_client()
            response = client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        """Close the synchronous HTTP client."""
        if self._sync_client is not None and not self._sync_client.is_closed:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        """Close the asynchronous HTTP client."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> "BlenderClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> "BlenderClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()


# Global client instance
_client: Optional[BlenderClient] = None


def get_client() -> BlenderClient:
    """Get or create the global Blender client."""
    global _client
    if _client is None:
        _client = BlenderClient()
    return _client


def set_client(client: BlenderClient) -> None:
    """Set the global Blender client."""
    global _client
    _client = client

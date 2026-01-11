"""HTTP client for communicating with Blender add-on."""

import httpx
from typing import Any, Dict, Optional


class BlenderClient:
    """HTTP client for communicating with Blender add-on."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    async def execute(
        self, action: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an action on Blender asynchronously."""
        async with httpx.AsyncClient(timeout=30.0) as client:
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
        with httpx.Client(timeout=30.0) as client:
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
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    def health_check_sync(self) -> bool:
        """Check if Blender server is running (synchronous)."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


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

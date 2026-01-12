"""Meshy AI client for mesh generation.

Meshy provides text-to-3D and image-to-3D generation capabilities.
API Documentation: https://docs.meshy.ai/
"""

import asyncio
import base64
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx

from .base import (
    MeshGenerationProvider,
    MeshGenerationResult,
    GenerationStatus,
)
from .config import get_ai_config


class MeshyClient(MeshGenerationProvider):
    """Meshy AI client for 3D mesh generation.

    Supports both text-to-3D and image-to-3D generation.
    """

    BASE_URL = "https://api.meshy.ai/openapi/v2"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Meshy client.

        Args:
            api_key: Meshy API key. If not provided, reads from config.
        """
        config = get_ai_config().get_config("meshy")
        self.api_key = api_key or (config.api_key if config else None)

        if not self.api_key:
            raise ValueError(
                "Meshy API key not configured. "
                "Set MESHY_API_KEY environment variable."
            )

        self.timeout = config.timeout if config else 600
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "meshy"

    async def generate_from_text(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        output_format: str = "glb",
        art_style: str = "realistic",
        ai_model: str = "latest",
        refine: bool = True,
        enable_pbr: bool = True,
        **kwargs
    ) -> MeshGenerationResult:
        """Generate 3D mesh from text description.

        Args:
            prompt: Text description of the 3D object (max 600 chars)
            negative_prompt: Things to avoid in generation
            output_format: Output format (glb, fbx, obj, usdz)
            art_style: Style preset (realistic, cartoon, sculpture, pbr)
            ai_model: Model version ("latest" for Meshy-6)
            refine: Whether to run refinement pass for higher quality
            enable_pbr: Generate PBR textures during refinement
            **kwargs:
                topology: "triangle" or "quad"
                target_polycount: Target polygon count
                symmetry_mode: Enable symmetry ("auto", "on", "off")

        Returns:
            MeshGenerationResult with generated mesh
        """
        start_time = time.time()

        # Create preview task
        preview_payload = {
            "mode": "preview",
            "prompt": prompt[:600],  # Max 600 chars
            "art_style": art_style,
            "ai_model": ai_model,
        }

        if negative_prompt:
            preview_payload["negative_prompt"] = negative_prompt[:600]

        if kwargs.get("topology"):
            preview_payload["topology"] = kwargs["topology"]
        if kwargs.get("target_polycount"):
            preview_payload["target_polycount"] = kwargs["target_polycount"]
        if kwargs.get("symmetry_mode"):
            preview_payload["symmetry_mode"] = kwargs["symmetry_mode"]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Create preview task
            try:
                response = await client.post(
                    f"{self.BASE_URL}/text-to-3d",
                    headers=self.headers,
                    json=preview_payload,
                )

                if response.status_code != 200 and response.status_code != 202:
                    error_msg = self._parse_error(response)
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"API error ({response.status_code}): {error_msg}",
                        provider=self.provider_name,
                        model_id=ai_model,
                    )

                data = response.json()
                task_id = data.get("result")

                if not task_id:
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error="No task ID returned from API",
                        provider=self.provider_name,
                        model_id=ai_model,
                    )

            except httpx.RequestError as e:
                return MeshGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Request failed: {str(e)}",
                    provider=self.provider_name,
                    model_id=ai_model,
                )

            # Wait for preview to complete
            preview_result = await self._wait_for_task(
                client, "text-to-3d", task_id, ai_model
            )

            if preview_result.status != GenerationStatus.COMPLETED:
                return preview_result

            # Optionally refine the model
            if refine:
                refine_payload = {
                    "mode": "refine",
                    "preview_task_id": task_id,
                    "enable_pbr": enable_pbr,
                }

                try:
                    response = await client.post(
                        f"{self.BASE_URL}/text-to-3d",
                        headers=self.headers,
                        json=refine_payload,
                    )

                    if response.status_code in (200, 202):
                        refine_data = response.json()
                        refine_task_id = refine_data.get("result")

                        if refine_task_id:
                            refine_result = await self._wait_for_task(
                                client, "text-to-3d", refine_task_id, ai_model
                            )
                            if refine_result.status == GenerationStatus.COMPLETED:
                                refine_result.generation_time_seconds = time.time() - start_time
                                return refine_result
                except Exception:
                    pass  # Fall back to preview result

            preview_result.generation_time_seconds = time.time() - start_time
            return preview_result

    async def generate_from_image(
        self,
        image_path: str,
        output_format: str = "glb",
        ai_model: str = "latest",
        **kwargs
    ) -> MeshGenerationResult:
        """Generate 3D mesh from reference image.

        Args:
            image_path: Path to input image (PNG, JPG)
            output_format: Output format (glb, fbx, obj, usdz)
            ai_model: Model version ("latest" for Meshy-6)
            **kwargs:
                topology: "triangle" or "quad"
                target_polycount: Target polygon count

        Returns:
            MeshGenerationResult with generated mesh
        """
        start_time = time.time()

        # Check file exists
        if not Path(image_path).exists():
            return MeshGenerationResult(
                status=GenerationStatus.FAILED,
                error=f"Image file not found: {image_path}",
                provider=self.provider_name,
            )

        # Read and encode image as data URI
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        suffix = Path(image_path).suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        mime_type = mime_types.get(suffix, "image/png")
        image_url = f"data:{mime_type};base64,{image_data}"

        payload = {
            "image_url": image_url,
            "ai_model": ai_model,
        }

        if kwargs.get("topology"):
            payload["topology"] = kwargs["topology"]
        if kwargs.get("target_polycount"):
            payload["target_polycount"] = kwargs["target_polycount"]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/image-to-3d",
                    headers=self.headers,
                    json=payload,
                )

                if response.status_code != 200 and response.status_code != 202:
                    error_msg = self._parse_error(response)
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"API error ({response.status_code}): {error_msg}",
                        provider=self.provider_name,
                        model_id=ai_model,
                    )

                data = response.json()
                task_id = data.get("result")

                if not task_id:
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error="No task ID returned from API",
                        provider=self.provider_name,
                        model_id=ai_model,
                    )

            except httpx.RequestError as e:
                return MeshGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Request failed: {str(e)}",
                    provider=self.provider_name,
                    model_id=ai_model,
                )

            result = await self._wait_for_task(
                client, "image-to-3d", task_id, ai_model
            )
            result.generation_time_seconds = time.time() - start_time
            return result

    async def _wait_for_task(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        task_id: str,
        model_id: str,
        poll_interval: float = 3.0,
    ) -> MeshGenerationResult:
        """Poll task status until complete."""
        while True:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/{endpoint}/{task_id}",
                    headers=self.headers,
                )

                if response.status_code != 200:
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"Failed to check status: {response.status_code}",
                        provider=self.provider_name,
                        model_id=model_id,
                    )

                data = response.json()
                status = data.get("status", "").upper()

                if status == "SUCCEEDED":
                    model_urls = data.get("model_urls", {})
                    mesh_url = model_urls.get("glb") or model_urls.get("fbx") or model_urls.get("obj")

                    local_path = None
                    if mesh_url:
                        local_path = await self._download_file(mesh_url, client)

                    return MeshGenerationResult(
                        status=GenerationStatus.COMPLETED,
                        mesh_url=mesh_url,
                        local_path=local_path,
                        mesh_format=self._get_format_from_url(mesh_url) if mesh_url else "glb",
                        thumbnail_url=data.get("thumbnail_url"),
                        provider=self.provider_name,
                        model_id=model_id,
                        metadata={
                            "task_id": task_id,
                            "model_urls": model_urls,
                            "texture_urls": data.get("texture_urls"),
                        },
                    )

                elif status == "FAILED":
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=data.get("task_error", {}).get("message", "Generation failed"),
                        provider=self.provider_name,
                        model_id=model_id,
                    )

                elif status == "CANCELED":
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error="Task was canceled",
                        provider=self.provider_name,
                        model_id=model_id,
                    )

                # Still processing
                await asyncio.sleep(poll_interval)

            except httpx.RequestError as e:
                return MeshGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Status check failed: {str(e)}",
                    provider=self.provider_name,
                    model_id=model_id,
                )

    async def _download_file(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        """Download file to temporary location."""
        try:
            response = await client.get(url)
            response.raise_for_status()

            fmt = self._get_format_from_url(url)
            suffix = f".{fmt}"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(response.content)
                return f.name
        except httpx.HTTPError:
            return None

    def _get_format_from_url(self, url: str) -> str:
        """Determine mesh format from URL."""
        url_lower = url.lower()
        if ".glb" in url_lower or ".gltf" in url_lower:
            return "glb"
        elif ".fbx" in url_lower:
            return "fbx"
        elif ".obj" in url_lower:
            return "obj"
        elif ".usdz" in url_lower:
            return "usdz"
        return "glb"

    def _parse_error(self, response: httpx.Response) -> str:
        """Parse error message from response."""
        try:
            data = response.json()
            return data.get("message", response.text)
        except Exception:
            return response.text

    async def check_status(self, task_id: str) -> MeshGenerationResult:
        """Check status of a text-to-3D task.

        Args:
            task_id: The task ID to check

        Returns:
            MeshGenerationResult with current status
        """
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/text-to-3d/{task_id}",
                    headers=self.headers,
                )

                if response.status_code != 200:
                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"Failed to check status: {response.status_code}",
                        provider=self.provider_name,
                    )

                data = response.json()
                status_map = {
                    "PENDING": GenerationStatus.PENDING,
                    "IN_PROGRESS": GenerationStatus.PROCESSING,
                    "SUCCEEDED": GenerationStatus.COMPLETED,
                    "FAILED": GenerationStatus.FAILED,
                    "CANCELED": GenerationStatus.FAILED,
                }

                return MeshGenerationResult(
                    status=status_map.get(data.get("status", "").upper(), GenerationStatus.PENDING),
                    mesh_url=data.get("model_urls", {}).get("glb"),
                    provider=self.provider_name,
                    metadata={"progress": data.get("progress", 0)},
                )

            except httpx.RequestError as e:
                return MeshGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Request failed: {str(e)}",
                    provider=self.provider_name,
                )

    def get_supported_formats(self) -> List[str]:
        """Return supported output formats."""
        return ["glb", "fbx", "obj", "usdz"]

    def get_available_models(self) -> Dict[str, str]:
        """Return available models."""
        return {
            "latest": "Meshy-6 (latest model, best quality)",
            "meshy-6-preview": "Meshy-6 Preview",
            "meshy-5": "Meshy-5 (previous generation)",
        }

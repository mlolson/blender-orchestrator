"""Replicate AI client for texture generation.

Replicate provides access to many image generation models via a simple API.
API Documentation: https://replicate.com/docs
"""

import asyncio
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx

from .base import (
    TextureGenerationProvider,
    TextureGenerationResult,
    GenerationStatus,
)
from .config import get_ai_config


class ReplicateClient(TextureGenerationProvider):
    """Replicate AI client for texture generation.

    Uses Stable Diffusion XL and other models for generating textures.
    """

    BASE_URL = "https://api.replicate.com/v1"

    # Default model for texture generation (SDXL)
    DEFAULT_MODEL = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

    # Specialized texture model (generates seamless textures)
    SEAMLESS_MODEL = "tommoore515/material_stable_diffusion:3b5c0242f8925a4ab6c79b4c51e9b4ce6374e9b07b5e8461d89e692fd0faa449"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Replicate client.

        Args:
            api_key: Replicate API token. If not provided, reads from config.
        """
        config = get_ai_config().get_config("replicate")
        self.api_key = api_key or (config.api_key if config else None)

        if not self.api_key:
            raise ValueError(
                "Replicate API token not configured. "
                "Set REPLICATE_API_TOKEN environment variable."
            )

        self.timeout = config.timeout if config else 300
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "replicate"

    async def generate_texture(
        self,
        prompt: str,
        texture_type: str = "diffuse",
        resolution: tuple = (1024, 1024),
        seamless: bool = True,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate a texture from a text description.

        Args:
            prompt: Description of the desired texture
            texture_type: Type of map (diffuse, normal, roughness, metallic)
            resolution: Output resolution as (width, height)
            seamless: Whether to generate a tileable texture
            **kwargs:
                negative_prompt: Things to avoid
                model: Override the default model

        Returns:
            TextureGenerationResult with status and file path/URL
        """
        start_time = time.time()

        # Enhance prompt based on texture type
        enhanced_prompt = self._enhance_prompt(prompt, texture_type, seamless)
        negative_prompt = kwargs.get("negative_prompt", "blurry, low quality, distorted")

        # Choose model based on whether seamless is needed
        model = kwargs.get("model")
        if model is None:
            model = self.SEAMLESS_MODEL if seamless else self.DEFAULT_MODEL

        # Build input parameters
        if "material_stable_diffusion" in model:
            # Specialized texture model
            input_params = {
                "prompt": enhanced_prompt,
                "image_resolution": "1024x1024" if resolution[0] >= 1024 else "512x512",
            }
        else:
            # SDXL or other general models
            input_params = {
                "prompt": enhanced_prompt,
                "negative_prompt": negative_prompt,
                "width": min(resolution[0], 1024),
                "height": min(resolution[1], 1024),
                "num_outputs": 1,
                "scheduler": "K_EULER",
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
            }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Create prediction
                response = await client.post(
                    f"{self.BASE_URL}/predictions",
                    headers=self.headers,
                    json={
                        "version": model.split(":")[-1] if ":" in model else model,
                        "input": input_params,
                    },
                )

                if response.status_code not in (200, 201):
                    error_msg = self._parse_error(response)
                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"API error ({response.status_code}): {error_msg}",
                        provider=self.provider_name,
                        texture_type=texture_type,
                    )

                data = response.json()
                prediction_id = data.get("id")

                if not prediction_id:
                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error="No prediction ID returned from API",
                        provider=self.provider_name,
                        texture_type=texture_type,
                    )

                # Wait for completion
                result = await self._wait_for_prediction(
                    client, prediction_id, texture_type, resolution
                )
                result.metadata["generation_time_seconds"] = time.time() - start_time
                return result

            except httpx.RequestError as e:
                return TextureGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Request failed: {str(e)}",
                    provider=self.provider_name,
                    texture_type=texture_type,
                )

    async def generate_from_mesh(
        self,
        mesh_path: str,
        prompt: str,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate a texture for a mesh.

        Note: Replicate doesn't have direct mesh-to-texture support,
        so this generates a generic texture based on the prompt.

        Args:
            mesh_path: Path to the mesh file (not used directly)
            prompt: Description of the desired texture style
            **kwargs: Additional parameters

        Returns:
            TextureGenerationResult with status and file path/URL
        """
        # Fall back to regular texture generation
        return await self.generate_texture(
            prompt=prompt,
            texture_type=kwargs.get("texture_type", "diffuse"),
            resolution=kwargs.get("resolution", (1024, 1024)),
            seamless=kwargs.get("seamless", True),
            **kwargs
        )

    async def _wait_for_prediction(
        self,
        client: httpx.AsyncClient,
        prediction_id: str,
        texture_type: str,
        resolution: tuple,
        poll_interval: float = 1.0,
    ) -> TextureGenerationResult:
        """Poll prediction status until complete."""
        while True:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/predictions/{prediction_id}",
                    headers=self.headers,
                )

                if response.status_code != 200:
                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"Failed to check status: {response.status_code}",
                        provider=self.provider_name,
                        texture_type=texture_type,
                    )

                data = response.json()
                status = data.get("status", "")

                if status == "succeeded":
                    output = data.get("output")
                    # Output can be a list or a single URL
                    if isinstance(output, list):
                        texture_url = output[0] if output else None
                    else:
                        texture_url = output

                    local_path = None
                    if texture_url:
                        local_path = await self._download_file(texture_url, client)

                    return TextureGenerationResult(
                        status=GenerationStatus.COMPLETED,
                        texture_url=texture_url,
                        texture_type=texture_type,
                        local_path=local_path,
                        resolution=resolution,
                        provider=self.provider_name,
                        model_id=data.get("version", ""),
                        metadata={
                            "prediction_id": prediction_id,
                            "metrics": data.get("metrics", {}),
                        },
                    )

                elif status == "failed":
                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=data.get("error", "Generation failed"),
                        provider=self.provider_name,
                        texture_type=texture_type,
                    )

                elif status == "canceled":
                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error="Prediction was canceled",
                        provider=self.provider_name,
                        texture_type=texture_type,
                    )

                # Still processing
                await asyncio.sleep(poll_interval)

            except httpx.RequestError as e:
                return TextureGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Status check failed: {str(e)}",
                    provider=self.provider_name,
                    texture_type=texture_type,
                )

    async def _download_file(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        """Download file to temporary location."""
        try:
            response = await client.get(url)
            response.raise_for_status()

            # Determine extension from content type or URL
            content_type = response.headers.get("content-type", "")
            if "png" in content_type or url.endswith(".png"):
                suffix = ".png"
            elif "jpeg" in content_type or "jpg" in content_type or url.endswith((".jpg", ".jpeg")):
                suffix = ".jpg"
            else:
                suffix = ".png"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(response.content)
                return f.name
        except httpx.HTTPError:
            return None

    def _enhance_prompt(self, prompt: str, texture_type: str, seamless: bool) -> str:
        """Enhance the prompt based on texture type."""
        enhancements = []

        # Add texture type context
        type_modifiers = {
            "diffuse": "albedo color texture, base color",
            "normal": "normal map texture, bump map, blue-purple tones",
            "roughness": "roughness map, grayscale, smooth to rough variation",
            "metallic": "metallic map, grayscale, metal reflection areas",
            "ambient_occlusion": "ambient occlusion map, grayscale, shadows in crevices",
        }

        if texture_type in type_modifiers:
            enhancements.append(type_modifiers[texture_type])

        # Add seamless/tileable modifiers
        if seamless:
            enhancements.append("seamless tileable texture, repeating pattern")

        # Add quality modifiers
        enhancements.append("high quality, detailed, 4k texture")

        enhanced = f"{prompt}, {', '.join(enhancements)}"
        return enhanced

    def _parse_error(self, response: httpx.Response) -> str:
        """Parse error message from response."""
        try:
            data = response.json()
            if "detail" in data:
                return data["detail"]
            if "error" in data:
                return data["error"]
            return response.text
        except Exception:
            return response.text

    def get_supported_texture_types(self) -> List[str]:
        """Return supported texture map types."""
        return ["diffuse", "normal", "roughness", "metallic", "ambient_occlusion"]

    def get_supported_resolutions(self) -> List[tuple]:
        """Return supported output resolutions."""
        return [(512, 512), (768, 768), (1024, 1024)]

    def get_available_models(self) -> Dict[str, str]:
        """Return available models for texture generation."""
        return {
            "sdxl": "Stable Diffusion XL - High quality general image generation",
            "material": "Material Stable Diffusion - Specialized for seamless textures",
        }

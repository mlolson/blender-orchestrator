"""Stability AI client for texture generation.

Stability AI provides high-quality image generation suitable for textures.
API Documentation: https://platform.stability.ai/docs/api-reference
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


class StabilityClient(TextureGenerationProvider):
    """Stability AI client for texture generation.

    Uses Stability's image generation APIs to create texture maps.
    """

    BASE_URL = "https://api.stability.ai/v2beta"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Stability AI client.

        Args:
            api_key: Stability API key. If not provided, reads from config.
        """
        config = get_ai_config().get_config("stability")
        self.api_key = api_key or (config.api_key if config else None)

        if not self.api_key:
            raise ValueError(
                "Stability API key not configured. "
                "Set STABILITY_API_KEY environment variable."
            )

        self.timeout = config.timeout if config else 300
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*",
        }

    @property
    def provider_name(self) -> str:
        return "stability"

    async def generate_texture(
        self,
        prompt: str,
        texture_type: str = "diffuse",
        resolution: tuple = (1024, 1024),
        seamless: bool = True,
        negative_prompt: Optional[str] = None,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate a texture from a text description.

        Args:
            prompt: Description of the desired texture
            texture_type: Type of map (diffuse, normal, roughness, metallic, ao)
            resolution: Output resolution as (width, height)
            seamless: Whether to generate a tileable texture
            negative_prompt: Things to avoid in generation
            **kwargs:
                style_preset: Style preset (e.g., "photographic", "digital-art")
                seed: Random seed for reproducibility

        Returns:
            TextureGenerationResult with generated texture
        """
        # Build texture-optimized prompt
        full_prompt = self._build_texture_prompt(prompt, texture_type, seamless)

        # Build negative prompt
        full_negative = self._build_negative_prompt(negative_prompt, texture_type)

        # Stability uses specific aspect ratios, find closest match
        width, height = self._normalize_resolution(resolution)

        payload = {
            "prompt": full_prompt,
            "negative_prompt": full_negative,
            "output_format": "png",
            "width": width,
            "height": height,
        }

        if kwargs.get("style_preset"):
            payload["style_preset"] = kwargs["style_preset"]
        if kwargs.get("seed"):
            payload["seed"] = kwargs["seed"]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Use stable-image-core for texture generation
                response = await client.post(
                    f"{self.BASE_URL}/stable-image/generate/core",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "image/*",
                    },
                    files={"none": ""},  # Required for multipart
                    data=payload,
                )

                if response.status_code != 200:
                    error_msg = self._parse_error(response)
                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"API error ({response.status_code}): {error_msg}",
                        provider=self.provider_name,
                        texture_type=texture_type,
                    )

                # Save the image
                local_path = await self._save_image(response.content, texture_type)

                return TextureGenerationResult(
                    status=GenerationStatus.COMPLETED,
                    local_path=local_path,
                    texture_type=texture_type,
                    resolution=(width, height),
                    provider=self.provider_name,
                    metadata={
                        "prompt": full_prompt,
                        "seamless": seamless,
                    },
                )

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
        """Generate a texture for a specific mesh.

        Note: Stability AI doesn't directly support mesh-based texturing.
        Use generate_texture() for standalone texture generation.

        Args:
            mesh_path: Path to the mesh file (not used)
            prompt: Description of the desired texture style

        Returns:
            TextureGenerationResult indicating not supported
        """
        # Stability doesn't support mesh-based texturing directly
        # Fall back to regular texture generation
        return await self.generate_texture(
            prompt=prompt,
            **kwargs
        )

    def _build_texture_prompt(
        self, 
        prompt: str, 
        texture_type: str, 
        seamless: bool
    ) -> str:
        """Build an optimized prompt for texture generation.

        Args:
            prompt: User's texture description
            texture_type: Type of texture map
            seamless: Whether texture should tile

        Returns:
            Enhanced prompt for texture generation
        """
        # Base texture modifiers
        modifiers = ["texture", "material", "surface pattern"]

        if seamless:
            modifiers.extend(["seamless", "tileable", "repeating pattern"])

        # Type-specific modifiers
        type_modifiers = {
            "diffuse": ["albedo", "base color", "diffuse map"],
            "normal": ["normal map", "bump texture", "surface detail", "height variations"],
            "roughness": ["roughness map", "glossiness variation", "surface roughness"],
            "metallic": ["metallic map", "metalness texture", "metal surface"],
            "ao": ["ambient occlusion", "AO map", "shadow detail"],
            "ambient_occlusion": ["ambient occlusion", "AO map", "shadow detail"],
        }

        if texture_type in type_modifiers:
            modifiers.extend(type_modifiers[texture_type])

        # For normal maps, we want grayscale height-map style
        if texture_type == "normal":
            modifiers.extend(["grayscale", "height map", "displacement detail"])

        # Build final prompt
        modifier_str = ", ".join(modifiers[:5])  # Limit modifiers
        return f"{prompt}, {modifier_str}, high quality, detailed"

    def _build_negative_prompt(
        self,
        user_negative: Optional[str],
        texture_type: str
    ) -> str:
        """Build negative prompt for texture generation.

        Args:
            user_negative: User's negative prompt
            texture_type: Type of texture map

        Returns:
            Combined negative prompt
        """
        negatives = [
            "blurry",
            "low quality",
            "watermark",
            "text",
            "logo",
            "human",
            "face",
            "person",
            "animal",
        ]

        # For non-diffuse maps, avoid color
        if texture_type in ("normal", "roughness", "metallic", "ao", "ambient_occlusion"):
            negatives.extend(["colorful", "vibrant colors", "saturated"])

        if user_negative:
            negatives.append(user_negative)

        return ", ".join(negatives)

    def _normalize_resolution(self, resolution: tuple) -> tuple:
        """Normalize resolution to Stability's supported sizes.

        Args:
            resolution: Requested (width, height)

        Returns:
            Supported (width, height) closest to request
        """
        # Stability supports specific resolutions
        # For textures, we want square outputs ideally
        supported = [512, 768, 1024, 1536]

        width, height = resolution

        # Find closest supported size
        def closest(val):
            return min(supported, key=lambda x: abs(x - val))

        return (closest(width), closest(height))

    async def _save_image(self, content: bytes, texture_type: str) -> str:
        """Save image content to temporary file.

        Args:
            content: Image bytes
            texture_type: Type of texture (for filename)

        Returns:
            Path to saved file
        """
        suffix = f"_{texture_type}.png"
        with tempfile.NamedTemporaryFile(
            suffix=suffix, 
            prefix="stability_texture_",
            delete=False
        ) as f:
            f.write(content)
            return f.name

    def _parse_error(self, response: httpx.Response) -> str:
        """Parse error message from response.

        Args:
            response: HTTP response

        Returns:
            Error message string
        """
        try:
            # Stability returns JSON errors
            data = response.json()
            if "message" in data:
                return data["message"]
            if "errors" in data:
                return "; ".join(str(e) for e in data["errors"])
            return str(data)
        except Exception:
            return response.text[:200] if response.text else f"HTTP {response.status_code}"

    def get_supported_texture_types(self) -> List[str]:
        """Return supported texture map types."""
        return ["diffuse", "normal", "roughness", "metallic", "ao", "ambient_occlusion"]

    def get_supported_resolutions(self) -> List[tuple]:
        """Return supported output resolutions."""
        return [(512, 512), (768, 768), (1024, 1024), (1536, 1536)]

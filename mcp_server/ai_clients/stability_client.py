"""Stability AI client for mesh and texture generation."""

import base64
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

import httpx

from .base import (
    MeshGenerationProvider,
    TextureGenerationProvider,
    MeshGenerationResult,
    TextureGenerationResult,
    GenerationStatus,
)
from .config import get_ai_config


class StabilityMeshClient(MeshGenerationProvider):
    """Stability AI client for 3D mesh generation.

    Uses Stable Fast 3D for image-to-3D generation.
    Note: Stability AI does not currently offer text-to-3D directly.
    """

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

        self.base_url = "https://api.stability.ai"
        self.timeout = config.timeout if config else 300

    @property
    def provider_name(self) -> str:
        return "stability"

    async def generate_from_text(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        output_format: str = "glb",
        **kwargs
    ) -> MeshGenerationResult:
        """Text-to-3D is not directly supported by Stability AI.

        Stability's 3D API requires an image as input.
        For text-to-3D, first generate an image using SDXL, then use
        generate_from_image.
        """
        return MeshGenerationResult(
            status=GenerationStatus.FAILED,
            error=(
                "Stability AI does not support direct text-to-3D. "
                "Generate an image first with generate_image_from_text, "
                "then use generate_from_image. Or use provider='replicate' "
                "with model='shap-e' for text-to-3D."
            ),
            provider=self.provider_name,
            model_id="stable-fast-3d",
        )

    async def generate_from_image(
        self,
        image_path: str,
        output_format: str = "glb",
        **kwargs
    ) -> MeshGenerationResult:
        """Generate 3D mesh from image using Stable Fast 3D.

        Args:
            image_path: Path to input image
            output_format: Output format (only 'glb' supported)
            **kwargs:
                texture_resolution: Texture resolution (512, 1024, 2048)
                foreground_ratio: Ratio of foreground object (0.0-1.0)
                remesh: Remesh output ('none', 'quad', 'triangle')

        Returns:
            MeshGenerationResult with generated mesh
        """
        if not Path(image_path).exists():
            return MeshGenerationResult(
                status=GenerationStatus.FAILED,
                error=f"Image file not found: {image_path}",
                provider=self.provider_name,
            )

        # Read image data
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Build multipart form data
        files = {"image": ("image.png", image_data, "image/png")}

        data = {
            "texture_resolution": str(kwargs.get("texture_resolution", 1024)),
            "foreground_ratio": str(kwargs.get("foreground_ratio", 0.85)),
            "remesh": kwargs.get("remesh", "none"),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v2beta/3d/stable-fast-3d",
                    headers=headers,
                    files=files,
                    data=data,
                )

                if response.status_code == 200:
                    # Response body is the GLB file directly
                    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
                        f.write(response.content)
                        local_path = f.name

                    return MeshGenerationResult(
                        status=GenerationStatus.COMPLETED,
                        local_path=local_path,
                        mesh_format="glb",
                        provider=self.provider_name,
                        model_id="stable-fast-3d",
                    )
                else:
                    # Parse error response
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", response.text)
                    except Exception:
                        error_msg = response.text

                    return MeshGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"API error ({response.status_code}): {error_msg}",
                        provider=self.provider_name,
                        model_id="stable-fast-3d",
                    )

            except httpx.TimeoutException:
                return MeshGenerationResult(
                    status=GenerationStatus.FAILED,
                    error="Request timed out. Try again or use a smaller image.",
                    provider=self.provider_name,
                    model_id="stable-fast-3d",
                )
            except httpx.RequestError as e:
                return MeshGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Request failed: {str(e)}",
                    provider=self.provider_name,
                    model_id="stable-fast-3d",
                )

    async def check_status(self, prediction_id: str) -> MeshGenerationResult:
        """Stability's API is synchronous, so status checking is not applicable."""
        return MeshGenerationResult(
            status=GenerationStatus.FAILED,
            error="Stability AI uses synchronous generation. No status to check.",
            provider=self.provider_name,
        )

    def get_supported_formats(self) -> List[str]:
        """Return supported output formats."""
        return ["glb"]

    def get_available_models(self) -> Dict[str, str]:
        """Return available models."""
        return {
            "stable-fast-3d": "Fast image-to-3D generation with textures",
        }


class StabilityTextureClient(TextureGenerationProvider):
    """Stability AI client for texture generation using SDXL."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Stability AI texture client."""
        config = get_ai_config().get_config("stability")
        self.api_key = api_key or (config.api_key if config else None)

        if not self.api_key:
            raise ValueError(
                "Stability API key not configured. "
                "Set STABILITY_API_KEY environment variable."
            )

        self.base_url = "https://api.stability.ai"
        self.timeout = config.timeout if config else 120

    @property
    def provider_name(self) -> str:
        return "stability"

    async def generate_texture(
        self,
        prompt: str,
        texture_type: str = "diffuse",
        resolution: tuple = (1024, 1024),
        seamless: bool = True,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate texture using Stable Diffusion.

        Args:
            prompt: Description of the desired texture
            texture_type: Type of texture map
            resolution: Output resolution
            seamless: Generate tileable texture
            **kwargs:
                style_preset: Style preset (e.g., "photographic", "digital-art")
                cfg_scale: Classifier-free guidance scale (0-35)
                steps: Number of diffusion steps

        Returns:
            TextureGenerationResult with generated texture
        """
        # Enhance prompt for texture generation
        texture_prompt = prompt
        if seamless:
            texture_prompt = f"{prompt}, seamless texture, tileable, PBR material, high quality"

        if texture_type == "normal":
            texture_prompt = f"normal map of {prompt}, blue and purple tones, surface height detail, seamless"
        elif texture_type == "roughness":
            texture_prompt = f"roughness map of {prompt}, grayscale, surface roughness detail, seamless"
        elif texture_type == "metallic":
            texture_prompt = f"metallic map of {prompt}, grayscale, metallic regions in white, seamless"
        elif texture_type == "ambient_occlusion":
            texture_prompt = f"ambient occlusion map of {prompt}, grayscale, shadow detail, seamless"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "text_prompts": [
                {"text": texture_prompt, "weight": 1.0},
            ],
            "cfg_scale": kwargs.get("cfg_scale", 7),
            "height": resolution[1],
            "width": resolution[0],
            "samples": 1,
            "steps": kwargs.get("steps", 30),
        }

        if kwargs.get("style_preset"):
            payload["style_preset"] = kwargs["style_preset"]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    artifacts = data.get("artifacts", [])

                    if not artifacts:
                        return TextureGenerationResult(
                            status=GenerationStatus.FAILED,
                            error="No image generated",
                            provider=self.provider_name,
                        )

                    # Decode base64 image
                    image_b64 = artifacts[0].get("base64")
                    if not image_b64:
                        return TextureGenerationResult(
                            status=GenerationStatus.FAILED,
                            error="No image data in response",
                            provider=self.provider_name,
                        )

                    image_data = base64.b64decode(image_b64)

                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(image_data)
                        local_path = f.name

                    return TextureGenerationResult(
                        status=GenerationStatus.COMPLETED,
                        local_path=local_path,
                        texture_type=texture_type,
                        resolution=resolution,
                        provider=self.provider_name,
                        model_id="sdxl-1.0",
                    )

                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", response.text)
                    except Exception:
                        error_msg = response.text

                    return TextureGenerationResult(
                        status=GenerationStatus.FAILED,
                        error=f"API error ({response.status_code}): {error_msg}",
                        provider=self.provider_name,
                    )

            except httpx.TimeoutException:
                return TextureGenerationResult(
                    status=GenerationStatus.FAILED,
                    error="Request timed out",
                    provider=self.provider_name,
                )
            except httpx.RequestError as e:
                return TextureGenerationResult(
                    status=GenerationStatus.FAILED,
                    error=f"Request failed: {str(e)}",
                    provider=self.provider_name,
                )

    async def generate_from_mesh(
        self,
        mesh_path: str,
        prompt: str,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate texture for a mesh.

        Note: This is a simplified implementation that generates a standard
        texture. For proper mesh-aware texturing, additional rendering and
        projection steps would be needed.
        """
        return await self.generate_texture(prompt, **kwargs)

    def get_supported_texture_types(self) -> List[str]:
        """Return supported texture types."""
        return ["diffuse", "normal", "roughness", "metallic", "ambient_occlusion"]

    def get_supported_resolutions(self) -> List[tuple]:
        """Return supported resolutions."""
        return [
            (512, 512),
            (768, 768),
            (1024, 1024),
            (1152, 896),
            (896, 1152),
            (1216, 832),
            (832, 1216),
            (1344, 768),
            (768, 1344),
            (1536, 640),
            (640, 1536),
        ]


async def generate_image_for_3d(
    prompt: str,
    api_key: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Helper function to generate an image suitable for 3D conversion.

    Generates a clean, isolated object image that works well with
    image-to-3D models.

    Args:
        prompt: Description of the object to generate
        api_key: Stability API key
        **kwargs: Additional generation parameters

    Returns:
        Path to generated image, or None on failure
    """
    config = get_ai_config().get_config("stability")
    key = api_key or (config.api_key if config else None)

    if not key:
        return None

    # Optimize prompt for 3D conversion
    enhanced_prompt = (
        f"{prompt}, isolated object, white background, studio lighting, "
        "centered, full view, 3D asset reference, clean edges"
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "text_prompts": [
            {"text": enhanced_prompt, "weight": 1.0},
            {"text": "multiple objects, cluttered, busy background", "weight": -1.0},
        ],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 30,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            response = await client.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                artifacts = data.get("artifacts", [])

                if artifacts:
                    image_b64 = artifacts[0].get("base64")
                    if image_b64:
                        image_data = base64.b64decode(image_b64)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                            f.write(image_data)
                            return f.name
        except Exception:
            pass

    return None

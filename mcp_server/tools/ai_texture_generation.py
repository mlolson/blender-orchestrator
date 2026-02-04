"""MCP tools for AI-powered texture generation."""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from ..ai_clients import (
    get_registry,
    GenerationStatus,
)
from ..blender_client import get_client


def register_tools(mcp: FastMCP, client=None):
    """Register AI texture generation tools with the MCP server."""

    @mcp.tool()
    async def generate_texture(
        prompt: str,
        texture_type: str = "diffuse",
        resolution: int = 1024,
        seamless: bool = True,
        provider: Optional[str] = None,
        apply_to_object: Optional[str] = None,
    ) -> dict:
        """Generate a texture from a text description using AI.

        Args:
            prompt: Description of the desired texture (e.g., "weathered wood planks")
            texture_type: Type of texture map - diffuse, normal, roughness, metallic, ambient_occlusion
            resolution: Output resolution (512, 768, or 1024)
            seamless: Whether to generate a tileable/seamless texture
            provider: AI provider to use (default: replicate)
            apply_to_object: Optionally apply the texture to this Blender object

        Returns:
            Dict with texture file path and generation details
        """
        registry = get_registry()

        # Get provider
        provider_name = provider or registry.get_default_texture_provider()
        if not provider_name:
            return {
                "success": False,
                "error": "No texture generation provider configured. Set REPLICATE_API_TOKEN.",
            }

        try:
            texture_provider = registry.get_texture_provider(provider_name)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Generate texture
        result = await texture_provider.generate_texture(
            prompt=prompt,
            texture_type=texture_type,
            resolution=(resolution, resolution),
            seamless=seamless,
        )

        if result.status != GenerationStatus.COMPLETED:
            return {
                "success": False,
                "error": result.error or "Texture generation failed",
                "provider": provider_name,
            }

        response = {
            "success": True,
            "texture_path": result.local_path,
            "texture_url": result.texture_url,
            "texture_type": texture_type,
            "resolution": f"{resolution}x{resolution}",
            "seamless": seamless,
            "provider": provider_name,
        }

        # Optionally apply to object in Blender
        if apply_to_object and result.local_path:
            apply_result = get_client().execute_sync(
                "apply_texture",
                {
                    "object_name": apply_to_object,
                    "texture_path": result.local_path,
                    "texture_type": texture_type,
                },
            )
            response["applied_to"] = apply_to_object
            response["apply_result"] = apply_result

        return response

    @mcp.tool()
    async def generate_pbr_material_textures(
        prompt: str,
        include_normal: bool = True,
        include_roughness: bool = True,
        include_metallic: bool = False,
        include_ao: bool = False,
        resolution: int = 1024,
        provider: Optional[str] = None,
        apply_to_object: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> dict:
        """Generate a complete set of PBR material textures.

        Generates multiple texture maps for a physically-based rendering material.

        Args:
            prompt: Description of the material (e.g., "rusty corroded metal")
            include_normal: Generate normal map
            include_roughness: Generate roughness map
            include_metallic: Generate metallic map
            include_ao: Generate ambient occlusion map
            resolution: Output resolution (512, 768, or 1024)
            provider: AI provider to use (default: replicate)
            apply_to_object: Optionally apply textures to this Blender object
            material_name: Name for the created material (default: auto-generated)

        Returns:
            Dict with paths to all generated texture maps
        """
        registry = get_registry()

        provider_name = provider or registry.get_default_texture_provider()
        if not provider_name:
            return {
                "success": False,
                "error": "No texture generation provider configured. Set REPLICATE_API_TOKEN.",
            }

        try:
            texture_provider = registry.get_texture_provider(provider_name)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Build list of textures to generate
        texture_types = ["diffuse"]
        if include_normal:
            texture_types.append("normal")
        if include_roughness:
            texture_types.append("roughness")
        if include_metallic:
            texture_types.append("metallic")
        if include_ao:
            texture_types.append("ambient_occlusion")

        # Generate each texture
        textures = {}
        errors = []

        for tex_type in texture_types:
            result = await texture_provider.generate_texture(
                prompt=prompt,
                texture_type=tex_type,
                resolution=(resolution, resolution),
                seamless=True,
            )

            if result.status == GenerationStatus.COMPLETED:
                textures[tex_type] = {
                    "path": result.local_path,
                    "url": result.texture_url,
                }
            else:
                errors.append(f"{tex_type}: {result.error or 'failed'}")

        if not textures:
            return {
                "success": False,
                "error": f"All texture generations failed: {'; '.join(errors)}",
                "provider": provider_name,
            }

        response = {
            "success": True,
            "textures": textures,
            "resolution": f"{resolution}x{resolution}",
            "provider": provider_name,
        }

        if errors:
            response["warnings"] = errors

        # Optionally apply to object
        if apply_to_object and textures.get("diffuse"):
            mat_name = material_name or f"{prompt[:20].replace(' ', '_')}_material"

            # Create material with diffuse texture
            apply_result = get_client().execute_sync(
                "apply_texture",
                {
                    "object_name": apply_to_object,
                    "texture_path": textures["diffuse"]["path"],
                    "texture_type": "diffuse",
                    "material_name": mat_name,
                },
            )
            response["applied_to"] = apply_to_object
            response["material_name"] = mat_name

            # Apply additional maps if available
            for tex_type in ["normal", "roughness", "metallic"]:
                if tex_type in textures:
                    get_client().execute_sync(
                        "apply_texture",
                        {
                            "object_name": apply_to_object,
                            "texture_path": textures[tex_type]["path"],
                            "texture_type": tex_type,
                            "material_name": mat_name,
                        },
                    )

        return response

    @mcp.tool()
    async def list_texture_generation_providers() -> dict:
        """List available AI texture generation providers and their status.

        Returns:
            Dict with list of providers and their configuration status
        """
        registry = get_registry()
        providers = registry.list_texture_providers()

        return {
            "providers": [
                {
                    "name": p.name,
                    "description": p.description,
                    "capabilities": p.capabilities,
                    "configured": p.is_configured,
                }
                for p in providers
            ],
            "default": registry.get_default_texture_provider(),
        }

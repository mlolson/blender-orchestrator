"""MCP tools for AI-powered texture generation."""

from typing import Optional, List

from ..ai_clients import get_registry, TextureCapability


def register_tools(mcp, client):
    """Register AI texture generation tools."""

    @mcp.tool()
    async def generate_texture(
        prompt: str,
        texture_type: str = "diffuse",
        resolution: int = 1024,
        seamless: bool = True,
        provider: Optional[str] = None,
        apply_to_object: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> str:
        """Generate a texture from a text description using AI.

        Uses AI providers to generate texture maps from text prompts.

        Args:
            prompt: Description of the desired texture
                    (e.g., "weathered wood planks", "rusty metal", "mossy stone")
            texture_type: Type of texture map to generate:
                         - "diffuse": Base color/albedo map
                         - "normal": Normal/bump map for surface detail
                         - "roughness": Roughness map for surface smoothness
                         - "metallic": Metallic map for metal surfaces
                         - "ao": Ambient occlusion map
            resolution: Output resolution (512, 768, 1024, or 1536)
            seamless: Generate a tileable/seamless texture (recommended)
            provider: AI provider to use (default: first configured provider)
            apply_to_object: Optional object name to apply the texture to
            material_name: Optional name for the material (creates new if specified)

        Returns:
            Status message with generation result
        """
        registry = get_registry()

        # Get provider (use default if not specified)
        provider_name = provider or registry.get_default_texture_provider()

        if not provider_name:
            return (
                "Error: No texture generation provider configured. "
                "Set STABILITY_API_KEY environment variable."
            )

        try:
            texture_provider = registry.get_texture_provider(provider_name)
        except ValueError as e:
            return f"Error: {str(e)}"

        result = await texture_provider.generate_texture(
            prompt=prompt,
            texture_type=texture_type,
            resolution=(resolution, resolution),
            seamless=seamless,
        )

        # Check result
        if result.status.value == "failed":
            return f"Error: Generation failed - {result.error}"

        if not result.local_path:
            return "Error: Generation succeeded but no texture file was produced."

        output_msg = f"Generated {texture_type} texture from prompt: '{prompt}'\n"
        output_msg += f"Provider: {result.provider}\n"
        output_msg += f"Resolution: {result.resolution[0]}x{result.resolution[1]}\n"
        output_msg += f"Local file: {result.local_path}\n"

        # Apply to object if requested
        if apply_to_object:
            try:
                # Create or get material
                mat_name = material_name or f"{apply_to_object}_{texture_type}_material"

                if material_name:
                    # Create new material with texture
                    apply_result = await client.execute(
                        "create_material_with_texture",
                        {
                            "name": mat_name,
                            "texture_path": result.local_path,
                            "texture_type": texture_type,
                            "object_name": apply_to_object,
                        },
                    )
                else:
                    # Try to apply to existing material or create new one
                    apply_result = await client.execute(
                        "create_material_with_texture",
                        {
                            "name": mat_name,
                            "texture_path": result.local_path,
                            "texture_type": texture_type,
                            "object_name": apply_to_object,
                        },
                    )

                if "error" in apply_result:
                    output_msg += f"Apply failed: {apply_result['error']}\n"
                else:
                    output_msg += f"Applied to '{apply_to_object}' as material '{apply_result.get('name', mat_name)}'\n"

            except Exception as e:
                output_msg += f"Apply failed: {str(e)}\n"

        return output_msg

    @mcp.tool()
    async def generate_pbr_material_textures(
        prompt: str,
        include_normal: bool = True,
        include_roughness: bool = True,
        include_metallic: bool = False,
        include_ao: bool = False,
        resolution: int = 1024,
        seamless: bool = True,
        provider: Optional[str] = None,
        apply_to_object: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> str:
        """Generate a complete PBR material with multiple texture maps.

        Generates diffuse and optionally normal, roughness, metallic, and AO maps
        for a complete physically-based rendering material.

        Args:
            prompt: Description of the material
                    (e.g., "rusty corroded metal", "polished marble", "worn leather")
            include_normal: Generate normal map for surface detail
            include_roughness: Generate roughness map
            include_metallic: Generate metallic map (for metals)
            include_ao: Generate ambient occlusion map
            resolution: Output resolution for all maps
            seamless: Generate tileable textures
            provider: AI provider to use
            apply_to_object: Object name to apply the material to
            material_name: Name for the new material

        Returns:
            Status message with all generated textures
        """
        registry = get_registry()

        provider_name = provider or registry.get_default_texture_provider()

        if not provider_name:
            return (
                "Error: No texture generation provider configured. "
                "Set STABILITY_API_KEY environment variable."
            )

        try:
            texture_provider = registry.get_texture_provider(provider_name)
        except ValueError as e:
            return f"Error: {str(e)}"

        # Determine which maps to generate
        maps_to_generate = ["diffuse"]
        if include_normal:
            maps_to_generate.append("normal")
        if include_roughness:
            maps_to_generate.append("roughness")
        if include_metallic:
            maps_to_generate.append("metallic")
        if include_ao:
            maps_to_generate.append("ao")

        output_msg = f"Generating PBR material: '{prompt}'\n"
        output_msg += f"Maps: {', '.join(maps_to_generate)}\n"
        output_msg += f"Resolution: {resolution}x{resolution}\n\n"

        generated_paths = {}

        # Generate each texture map
        for texture_type in maps_to_generate:
            output_msg += f"Generating {texture_type} map... "

            result = await texture_provider.generate_texture(
                prompt=prompt,
                texture_type=texture_type,
                resolution=(resolution, resolution),
                seamless=seamless,
            )

            if result.status.value == "failed":
                output_msg += f"FAILED: {result.error}\n"
                continue

            if result.local_path:
                generated_paths[texture_type] = result.local_path
                output_msg += f"OK ({result.local_path})\n"
            else:
                output_msg += "FAILED: No file produced\n"

        # Apply to object if requested and we have at least diffuse
        if apply_to_object and "diffuse" in generated_paths:
            try:
                mat_name = material_name or f"{apply_to_object}_pbr_material"

                apply_params = {
                    "name": mat_name,
                    "diffuse_path": generated_paths.get("diffuse"),
                    "normal_path": generated_paths.get("normal"),
                    "roughness_path": generated_paths.get("roughness"),
                    "metallic_path": generated_paths.get("metallic"),
                    "ao_path": generated_paths.get("ao"),
                    "object_name": apply_to_object,
                }

                apply_result = await client.execute(
                    "create_pbr_material_from_textures",
                    apply_params,
                )

                if "error" in apply_result:
                    output_msg += f"\nApply failed: {apply_result['error']}"
                else:
                    output_msg += f"\nApplied PBR material '{mat_name}' to '{apply_to_object}'"
                    if "textures_applied" in apply_result:
                        output_msg += f" (maps: {', '.join(apply_result['textures_applied'])})"

            except Exception as e:
                output_msg += f"\nApply failed: {str(e)}"

        return output_msg

    @mcp.tool()
    async def apply_texture_to_object(
        texture_path: str,
        object_name: str,
        texture_type: str = "diffuse",
        material_name: Optional[str] = None,
        uv_scale: Optional[List[float]] = None,
    ) -> str:
        """Apply a texture file to an object in the scene.

        Args:
            texture_path: Path to the texture image file
            object_name: Name of the object to apply texture to
            texture_type: Type of texture map (diffuse, normal, roughness, metallic, ao)
            material_name: Optional name for new material (creates if not exists)
            uv_scale: Optional [x, y] UV scaling factors

        Returns:
            Status message
        """
        params = {
            "name": material_name or f"{object_name}_material",
            "texture_path": texture_path,
            "texture_type": texture_type,
            "object_name": object_name,
        }

        if uv_scale:
            params["uv_scale"] = uv_scale

        result = await client.execute("create_material_with_texture", params)

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"Applied {texture_type} texture to '{object_name}'\n"
        output += f"Material: {result.get('name', material_name)}\n"
        output += f"Texture: {texture_path}"

        return output

    @mcp.tool()
    async def list_texture_generation_providers() -> str:
        """List available AI texture generation providers and their status.

        Shows which providers are configured and available for use,
        along with their capabilities.

        Returns:
            Summary of available texture providers
        """
        registry = get_registry()
        providers = registry.list_texture_providers()

        output = "AI Texture Generation Providers:\n"
        output += "=" * 40 + "\n\n"

        if not providers:
            output += "No texture generation providers registered.\n"
            output += "\nTo enable texture generation, set STABILITY_API_KEY environment variable.\n"
            return output

        for provider in providers:
            status = "✓ Configured" if provider.is_configured else "✗ Not configured"
            output += f"{provider.name.upper()}: {status}\n"
            output += f"  {provider.description}\n"
            output += f"  Capabilities: {', '.join(provider.capabilities)}\n"

            if not provider.is_configured:
                output += f"  Setup: Set {provider.name.upper()}_API_KEY env var\n"

            output += "\n"

        output += "Usage Examples:\n"
        output += '  generate_texture("weathered wood planks")\n'
        output += '  generate_texture("rusty metal", texture_type="roughness")\n'
        output += '  generate_pbr_material_textures("mossy stone", apply_to_object="Cube")\n'

        return output

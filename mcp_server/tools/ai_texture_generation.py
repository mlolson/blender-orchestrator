"""MCP tools for AI-powered texture generation."""

from typing import Optional, List

from ..ai_clients.config import get_ai_config


def register_tools(mcp, client):
    """Register AI texture generation tools."""

    @mcp.tool()
    async def generate_texture(
        prompt: str,
        texture_type: str = "diffuse",
        resolution: int = 1024,
        seamless: bool = True,
        apply_to_object: Optional[str] = None,
    ) -> str:
        """Generate a texture image using AI.

        Creates texture maps using AI image generation, optimized for
        use in 3D materials. Can optionally apply directly to an object.

        Args:
            prompt: Description of the desired texture
                    (e.g., "weathered wood planks", "rusty metal")
            texture_type: Type of texture map to generate:
                         - "diffuse": Base color/albedo map
                         - "normal": Normal map for surface detail
                         - "roughness": Roughness map (grayscale)
                         - "metallic": Metallic map (grayscale)
                         - "ambient_occlusion": AO map
            resolution: Output resolution (512, 768, or 1024)
            seamless: Whether to generate a tileable texture
            apply_to_object: Optional object name to apply texture to

        Returns:
            Status message with texture file path
        """
        config = get_ai_config()

        if not config.has_provider("stability"):
            return "Error: STABILITY_API_KEY not configured. Set the environment variable."

        from ..ai_clients.stability_client import StabilityTextureClient

        try:
            texture_client = StabilityTextureClient()
        except ValueError as e:
            return f"Error: {str(e)}"

        # Generate texture
        result = await texture_client.generate_texture(
            prompt=prompt,
            texture_type=texture_type,
            resolution=(resolution, resolution),
            seamless=seamless,
        )

        if result.status.value == "failed":
            return f"Error: Texture generation failed - {result.error}"

        if not result.local_path:
            return "Error: Generation succeeded but no texture file was produced."

        output_msg = f"Generated {texture_type} texture from prompt: '{prompt}'\n"
        output_msg += f"Resolution: {resolution}x{resolution}\n"
        output_msg += f"Provider: {result.provider}\n"
        output_msg += f"Local file: {result.local_path}\n"

        # Apply to object if requested
        if apply_to_object:
            try:
                # First create or get material
                mat_result = await client.execute(
                    "create_material",
                    {"name": f"{apply_to_object}_AI_Material"},
                )
                material_name = mat_result["name"]

                # Assign to object
                await client.execute(
                    "assign_material",
                    {"object_name": apply_to_object, "material_name": material_name},
                )

                # Apply texture
                texture_result = await client.execute(
                    "apply_texture_to_material",
                    {
                        "material_name": material_name,
                        "texture_path": result.local_path,
                        "texture_type": texture_type,
                    },
                )

                if "error" in texture_result:
                    output_msg += f"\nFailed to apply texture: {texture_result['error']}"
                else:
                    output_msg += f"\nApplied to object '{apply_to_object}' via material '{material_name}'"

            except Exception as e:
                output_msg += f"\nFailed to apply texture: {str(e)}"

        return output_msg

    @mcp.tool()
    async def generate_pbr_material_textures(
        prompt: str,
        apply_to_object: Optional[str] = None,
        include_normal: bool = True,
        include_roughness: bool = True,
        include_metallic: bool = False,
        resolution: int = 1024,
    ) -> str:
        """Generate a complete PBR material with multiple texture maps.

        Creates diffuse, normal, and optionally roughness/metallic maps
        for a complete physically-based material.

        Args:
            prompt: Description of the material surface
                    (e.g., "cobblestone path", "brushed aluminum")
            apply_to_object: Optional object name to apply the material to
            include_normal: Generate normal map for surface detail
            include_roughness: Generate roughness map
            include_metallic: Generate metallic map (for metal surfaces)
            resolution: Texture resolution (512, 768, or 1024)

        Returns:
            Status message with generated texture paths
        """
        config = get_ai_config()

        if not config.has_provider("stability"):
            return "Error: STABILITY_API_KEY not configured."

        from ..ai_clients.stability_client import StabilityTextureClient

        try:
            texture_client = StabilityTextureClient()
        except ValueError as e:
            return f"Error: {str(e)}"

        output_msg = f"Generating PBR material for: '{prompt}'\n"
        output_msg += "=" * 40 + "\n\n"

        texture_paths = {}

        # Generate diffuse texture
        output_msg += "Generating diffuse texture...\n"
        diffuse_result = await texture_client.generate_texture(
            prompt=prompt,
            texture_type="diffuse",
            resolution=(resolution, resolution),
            seamless=True,
        )

        if diffuse_result.status.value == "failed":
            return f"Error: Failed to generate diffuse texture - {diffuse_result.error}"

        texture_paths["diffuse"] = diffuse_result.local_path
        output_msg += f"  Diffuse: {diffuse_result.local_path}\n"

        # Generate normal map
        if include_normal:
            output_msg += "Generating normal map...\n"
            normal_result = await texture_client.generate_texture(
                prompt=prompt,
                texture_type="normal",
                resolution=(resolution, resolution),
                seamless=True,
            )

            if normal_result.status.value == "completed" and normal_result.local_path:
                texture_paths["normal"] = normal_result.local_path
                output_msg += f"  Normal: {normal_result.local_path}\n"
            else:
                output_msg += f"  Normal: Failed - {normal_result.error}\n"

        # Generate roughness map
        if include_roughness:
            output_msg += "Generating roughness map...\n"
            roughness_result = await texture_client.generate_texture(
                prompt=prompt,
                texture_type="roughness",
                resolution=(resolution, resolution),
                seamless=True,
            )

            if roughness_result.status.value == "completed" and roughness_result.local_path:
                texture_paths["roughness"] = roughness_result.local_path
                output_msg += f"  Roughness: {roughness_result.local_path}\n"
            else:
                output_msg += f"  Roughness: Failed - {roughness_result.error}\n"

        # Generate metallic map
        if include_metallic:
            output_msg += "Generating metallic map...\n"
            metallic_result = await texture_client.generate_texture(
                prompt=prompt,
                texture_type="metallic",
                resolution=(resolution, resolution),
                seamless=True,
            )

            if metallic_result.status.value == "completed" and metallic_result.local_path:
                texture_paths["metallic"] = metallic_result.local_path
                output_msg += f"  Metallic: {metallic_result.local_path}\n"
            else:
                output_msg += f"  Metallic: Failed - {metallic_result.error}\n"

        output_msg += "\n"

        # Apply to object if requested
        if apply_to_object and texture_paths.get("diffuse"):
            try:
                pbr_params = {
                    "name": f"{apply_to_object}_PBR_Material",
                    "diffuse_path": texture_paths.get("diffuse"),
                    "normal_path": texture_paths.get("normal"),
                    "roughness_path": texture_paths.get("roughness"),
                    "metallic_path": texture_paths.get("metallic"),
                    "object_name": apply_to_object,
                }

                result = await client.execute("create_pbr_material_from_textures", pbr_params)

                if "error" in result:
                    output_msg += f"Failed to apply material: {result['error']}\n"
                else:
                    output_msg += f"Applied PBR material '{result['name']}' to '{apply_to_object}'\n"
                    output_msg += f"Textures applied: {', '.join(result.get('textures_applied', []))}"

            except Exception as e:
                output_msg += f"Failed to apply material: {str(e)}"
        elif texture_paths:
            output_msg += "Textures saved to disk. Use create_pbr_material_from_textures to apply."

        return output_msg

    @mcp.tool()
    async def list_texture_generation_providers() -> str:
        """List available AI texture generation providers and their status.

        Returns:
            Summary of available providers
        """
        config = get_ai_config()

        output = "AI Texture Generation Providers:\n"
        output += "=" * 40 + "\n\n"

        # Stability
        if config.has_provider("stability"):
            output += "STABILITY AI: Configured\n"
            output += "  Uses SDXL for texture generation\n"
            output += "  Supports: diffuse, normal, roughness, metallic, AO\n"
            output += "  Resolutions: 512, 768, 1024\n"
        else:
            output += "STABILITY AI: Not configured\n"
            output += "  Set STABILITY_API_KEY environment variable\n"

        output += "\n"
        output += "Texture types:\n"
        output += "  - diffuse: Base color/albedo\n"
        output += "  - normal: Surface detail bumps\n"
        output += "  - roughness: Surface smoothness\n"
        output += "  - metallic: Metal vs non-metal\n"
        output += "  - ambient_occlusion: Shadowed areas\n"

        return output

    @mcp.tool()
    async def apply_texture_to_object(
        object_name: str,
        texture_path: str,
        texture_type: str = "diffuse",
        material_name: Optional[str] = None,
    ) -> str:
        """Apply a texture file to an object's material.

        Args:
            object_name: Name of the object to apply texture to
            texture_path: Path to the texture image file
            texture_type: Type of texture (diffuse, normal, roughness, metallic)
            material_name: Optional specific material name to use

        Returns:
            Result message
        """
        # Create material if needed
        if not material_name:
            material_name = f"{object_name}_Material"

        try:
            # Check if material exists
            mat_result = await client.execute(
                "create_material",
                {"name": material_name},
            )
            actual_mat_name = mat_result["name"]

            # Assign to object
            await client.execute(
                "assign_material",
                {"object_name": object_name, "material_name": actual_mat_name},
            )

            # Apply texture
            result = await client.execute(
                "apply_texture_to_material",
                {
                    "material_name": actual_mat_name,
                    "texture_path": texture_path,
                    "texture_type": texture_type,
                },
            )

            if "error" in result:
                return f"Error applying texture: {result['error']}"

            return f"Applied {texture_type} texture to '{object_name}' via material '{actual_mat_name}'"

        except Exception as e:
            return f"Error: {str(e)}"

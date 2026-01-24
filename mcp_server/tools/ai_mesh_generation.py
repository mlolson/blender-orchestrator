"""MCP tools for AI-powered mesh generation."""

from typing import Optional, List

from ..ai_clients import get_registry, MeshCapability


def register_tools(mcp, client):
    """Register AI mesh generation tools."""

    @mcp.tool()
    async def generate_mesh_from_text(
        prompt: str,
        provider: str = "meshy",
        art_style: str = "realistic",
        refine: bool = True,
        import_to_scene: bool = True,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Generate a 3D mesh from a text description using AI.

        Uses AI providers to generate 3D models from text prompts.

        Args:
            prompt: Text description of the 3D object to generate
                    (e.g., "a wooden chair", "a red sports car")
            provider: AI provider to use (default: "meshy")
            art_style: Style for generation:
                      - "realistic": Photorealistic style
                      - "cartoon": Stylized cartoon look
                      - "sculpture": Sculpted appearance
                      - "pbr": PBR-optimized textures
            refine: Run refinement pass for higher quality (recommended)
            import_to_scene: Whether to import the generated mesh into Blender
            location: [x, y, z] position for imported mesh
            name: Optional name for the imported object

        Returns:
            Status message with generation result
        """
        registry = get_registry()

        try:
            mesh_provider = registry.get_mesh_provider(provider)
        except ValueError as e:
            return f"Error: {str(e)}"

        result = await mesh_provider.generate_from_text(
            prompt=prompt,
            art_style=art_style,
            refine=refine,
        )

        # Check result
        if result.status.value == "failed":
            return f"Error: Generation failed - {result.error}"

        if not result.local_path:
            return "Error: Generation succeeded but no mesh file was produced."

        output_msg = f"Generated 3D mesh from prompt: '{prompt}'\n"
        output_msg += f"Provider: {result.provider}\n"
        output_msg += f"Local file: {result.local_path}\n"

        if result.generation_time_seconds:
            output_msg += f"Generation time: {result.generation_time_seconds:.1f}s\n"

        # Import to scene if requested
        if import_to_scene:
            try:
                import_result = await client.execute(
                    "import_mesh_file",
                    {
                        "file_path": result.local_path,
                        "name": name,
                        "location": location or [0, 0, 0],
                    },
                )

                if "error" in import_result:
                    output_msg += f"Import failed: {import_result['error']}"
                else:
                    output_msg += f"Imported as '{import_result['name']}' at {import_result['location']}"

            except Exception as e:
                output_msg += f"Import failed: {str(e)}"

        return output_msg

    @mcp.tool()
    async def generate_mesh_from_image(
        image_path: str,
        provider: str = "meshy",
        import_to_scene: bool = True,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Generate a 3D mesh from a reference image using AI.

        Uses AI providers to generate 3D models from images.

        Args:
            image_path: Path to the input image (PNG, JPG)
            provider: AI provider to use (default: "meshy")
            import_to_scene: Whether to import the generated mesh into Blender
            location: [x, y, z] position for imported mesh
            name: Optional name for the imported object

        Returns:
            Status message with generation result

        Tips for best results:
            - Use images with a single object on a clean/white background
            - Ensure the object is well-lit and centered
            - Avoid cluttered backgrounds
        """
        registry = get_registry()

        # Check provider supports image-to-3D
        providers = registry.list_mesh_providers()
        provider_info = next((p for p in providers if p.name == provider), None)

        if provider_info and not provider_info.has_capability(MeshCapability.IMAGE_TO_3D):
            return f"Error: Provider '{provider}' does not support image-to-3D generation."

        try:
            mesh_provider = registry.get_mesh_provider(provider)
        except ValueError as e:
            return f"Error: {str(e)}"

        result = await mesh_provider.generate_from_image(image_path=image_path)

        # Check result
        if result.status.value == "failed":
            return f"Error: Generation failed - {result.error}"

        if not result.local_path:
            return "Error: Generation succeeded but no mesh file was produced."

        output_msg = f"Generated 3D mesh from image: '{image_path}'\n"
        output_msg += f"Provider: {result.provider}\n"
        output_msg += f"Local file: {result.local_path}\n"

        if result.generation_time_seconds:
            output_msg += f"Generation time: {result.generation_time_seconds:.1f}s\n"

        # Import to scene if requested
        if import_to_scene:
            try:
                import_result = await client.execute(
                    "import_mesh_file",
                    {
                        "file_path": result.local_path,
                        "name": name,
                        "location": location or [0, 0, 0],
                    },
                )

                if "error" in import_result:
                    output_msg += f"Import failed: {import_result['error']}"
                else:
                    output_msg += f"Imported as '{import_result['name']}' at {import_result['location']}"

            except Exception as e:
                output_msg += f"Import failed: {str(e)}"

        return output_msg

    @mcp.tool()
    async def list_mesh_generation_providers() -> str:
        """List available AI mesh generation providers and their status.

        Shows which providers are configured and available for use,
        along with their capabilities.

        Returns:
            Summary of available providers and their capabilities
        """
        registry = get_registry()
        providers = registry.list_mesh_providers()

        output = "AI Mesh Generation Providers:\n"
        output += "=" * 40 + "\n\n"

        if not providers:
            output += "No mesh generation providers registered.\n"
            return output

        for provider in providers:
            status = "Configured" if provider.is_configured else "Not configured"
            output += f"{provider.name.upper()}: {status}\n"
            output += f"  {provider.description}\n"
            output += f"  Capabilities: {', '.join(provider.capabilities)}\n"

            if not provider.is_configured:
                output += f"  Setup: Set {provider.name.upper()}_API_KEY env var or add to config.json\n"

            output += "\n"

        output += "Usage:\n"
        output += '  generate_mesh_from_text("a wooden chair")\n'
        output += '  generate_mesh_from_text("robot", provider="meshy", art_style="cartoon")\n'
        output += '  generate_mesh_from_image("/path/to/image.png")\n'

        return output

    @mcp.tool()
    async def import_mesh_file(
        file_path: str,
        location: Optional[List[float]] = None,
        scale: Optional[float] = None,
        name: Optional[str] = None,
    ) -> str:
        """Import a mesh file into the Blender scene.

        Supports GLB, GLTF, OBJ, FBX, PLY, and STL formats.

        Args:
            file_path: Path to the mesh file
            location: [x, y, z] position for the imported mesh
            scale: Uniform scale factor to apply
            name: Optional name for the imported object

        Returns:
            Import result message
        """
        params = {
            "file_path": file_path,
            "location": location or [0, 0, 0],
        }

        if scale is not None:
            params["scale"] = scale
        if name is not None:
            params["name"] = name

        result = await client.execute("import_mesh_file", params)

        if "error" in result:
            return f"Import failed: {result['error']}"

        output = f"Imported mesh '{result['name']}'\n"
        output += f"Location: {result['location']}\n"
        output += f"Source: {result.get('source_file', file_path)}\n"

        if "imported_objects" in result:
            output += f"Objects imported: {', '.join(result['imported_objects'])}"

        return output

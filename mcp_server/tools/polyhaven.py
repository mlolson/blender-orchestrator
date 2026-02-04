"""MCP tools for Poly Haven free asset library.

Poly Haven provides thousands of free CC0 licensed assets:
- HDRIs for lighting
- PBR Textures for materials
- 3D Models ready to use

All assets are public domain - free for any use.
"""

from typing import Optional, List

from ..asset_clients import PolyHavenClient, AssetType


def register_tools(mcp, client):
    """Register Poly Haven asset tools."""
    
    ph_client = PolyHavenClient()

    @mcp.tool()
    async def search_polyhaven(
        query: str,
        asset_type: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        """Search Poly Haven for free CC0 assets.

        Poly Haven has thousands of free HDRIs, textures, and 3D models.
        All assets are CC0 licensed (public domain, free for any use).

        Args:
            query: Search term (e.g., "forest", "brick", "chair")
            asset_type: Filter by type - 'hdri', 'texture', or 'model'
            limit: Max results to return (default: 10)

        Returns:
            List of matching assets with IDs for downloading
        """
        # Map type string to enum
        type_map = {
            "hdri": AssetType.HDRI,
            "hdris": AssetType.HDRI,
            "texture": AssetType.TEXTURE,
            "textures": AssetType.TEXTURE,
            "model": AssetType.MODEL,
            "models": AssetType.MODEL,
        }
        
        a_type = type_map.get(asset_type.lower()) if asset_type else None

        assets = await ph_client.list_assets(
            asset_type=a_type,
            search=query,
            limit=limit,
        )

        if not assets:
            return f"No assets found for '{query}'. Try a different search term."

        output = f"🎨 Poly Haven Results for '{query}'\n"
        output += "=" * 40 + "\n\n"

        for asset in assets:
            type_emoji = {"hdris": "🌅", "textures": "🧱", "models": "📦"}
            emoji = type_emoji.get(asset.asset_type.value, "📄")
            
            output += f"{emoji} **{asset.name}** (`{asset.id}`)\n"
            output += f"   Type: {asset.asset_type.value}\n"
            output += f"   Categories: {', '.join(asset.categories[:3])}\n"
            output += f"   Downloads: {asset.download_count:,}\n"
            output += f"   Max res: {asset.max_resolution[0]}px\n\n"

        output += "\nUse the asset ID to download:\n"
        output += "  `download_polyhaven_hdri(\"asset_id\")`\n"
        output += "  `download_polyhaven_texture(\"asset_id\")`\n"
        output += "  `download_polyhaven_model(\"asset_id\")`"

        return output

    @mcp.tool()
    async def list_polyhaven_categories(
        asset_type: str = "textures",
    ) -> str:
        """List available categories on Poly Haven.

        Use categories to filter searches.

        Args:
            asset_type: 'hdri', 'texture', or 'model'

        Returns:
            List of categories with asset counts
        """
        type_map = {
            "hdri": AssetType.HDRI,
            "hdris": AssetType.HDRI,
            "texture": AssetType.TEXTURE,
            "textures": AssetType.TEXTURE,
            "model": AssetType.MODEL,
            "models": AssetType.MODEL,
        }
        
        a_type = type_map.get(asset_type.lower(), AssetType.TEXTURE)
        categories = await ph_client.get_categories(a_type)

        output = f"📂 Poly Haven Categories ({a_type.value})\n"
        output += "=" * 40 + "\n\n"

        # Sort by count
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        for cat, count in sorted_cats[:30]:  # Top 30
            output += f"  {cat}: {count} assets\n"

        return output

    @mcp.tool()
    async def download_polyhaven_hdri(
        asset_id: str,
        resolution: str = "2k",
        apply_to_scene: bool = True,
    ) -> str:
        """Download an HDRI from Poly Haven and optionally apply as world lighting.

        HDRIs provide realistic lighting for your scene.

        Args:
            asset_id: The asset ID (from search results)
            resolution: Resolution - '1k', '2k', '4k', '8k' (default: 2k)
            apply_to_scene: Apply as world environment (default: True)

        Returns:
            Download result and application status
        """
        result = await ph_client.download_hdri(
            asset_id=asset_id,
            resolution=resolution,
        )

        output = f"🌅 Downloaded HDRI: {asset_id}\n"
        output += f"Resolution: {result.resolution}\n"
        output += f"File: {result.local_path}\n"

        if apply_to_scene:
            # Apply HDRI to world
            try:
                apply_result = await client.execute(
                    "set_world_hdri",
                    {"hdri_path": result.local_path},
                )
                if "error" not in apply_result:
                    output += "\n✅ Applied as world environment lighting"
                else:
                    output += f"\n⚠️ Apply failed: {apply_result.get('error')}"
                    output += "\nYou can manually apply the HDRI in Blender's World settings."
            except Exception as e:
                output += f"\n⚠️ Could not auto-apply: {str(e)}"
                output += "\nManually set as world environment in Blender."

        return output

    @mcp.tool()
    async def download_polyhaven_texture(
        asset_id: str,
        resolution: str = "2k",
        apply_to_object: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> str:
        """Download PBR textures from Poly Haven.

        Downloads diffuse, normal, roughness, and displacement maps.

        Args:
            asset_id: The asset ID (from search results)
            resolution: Resolution - '1k', '2k', '4k' (default: 2k)
            apply_to_object: Object name to apply material to
            material_name: Name for the new material

        Returns:
            Download result with texture paths
        """
        results = await ph_client.download_pbr_textures(
            asset_id=asset_id,
            resolution=resolution,
        )

        if not results:
            return f"Error: Could not download textures for '{asset_id}'"

        output = f"🧱 Downloaded Textures: {asset_id}\n"
        output += f"Resolution: {resolution}\n\n"
        output += "Downloaded maps:\n"
        
        paths = {}
        for tex_type, result in results.items():
            output += f"  • {tex_type}: {result.local_path}\n"
            paths[tex_type] = result.local_path

        # Apply to object if requested
        if apply_to_object and "diffuse" in paths:
            try:
                mat_name = material_name or f"{asset_id}_material"
                
                apply_params = {
                    "name": mat_name,
                    "diffuse_path": paths.get("diffuse"),
                    "normal_path": paths.get("normal"),
                    "roughness_path": paths.get("roughness"),
                    "object_name": apply_to_object,
                }
                
                apply_result = await client.execute(
                    "create_pbr_material_from_textures",
                    apply_params,
                )

                if "error" not in apply_result:
                    output += f"\n✅ Applied material '{mat_name}' to '{apply_to_object}'"
                else:
                    output += f"\n⚠️ Apply failed: {apply_result.get('error')}"
            except Exception as e:
                output += f"\n⚠️ Could not auto-apply: {str(e)}"

        return output

    @mcp.tool()
    async def download_polyhaven_model(
        asset_id: str,
        file_format: str = "gltf",
        import_to_scene: bool = True,
        location: Optional[List[float]] = None,
    ) -> str:
        """Download a 3D model from Poly Haven.

        Models come with PBR materials already applied.

        Args:
            asset_id: The asset ID (from search results)
            file_format: Format - 'gltf', 'fbx', 'blend' (default: gltf)
            import_to_scene: Import into Blender scene (default: True)
            location: [x, y, z] position for imported model

        Returns:
            Download and import result
        """
        result = await ph_client.download_model(
            asset_id=asset_id,
            file_format=file_format,
        )

        output = f"📦 Downloaded Model: {asset_id}\n"
        output += f"Format: {result.file_format}\n"
        output += f"File: {result.local_path}\n"

        if import_to_scene:
            try:
                import_result = await client.execute(
                    "import_mesh_file",
                    {
                        "file_path": result.local_path,
                        "name": asset_id,
                        "location": location or [0, 0, 0],
                    },
                )

                if "error" not in import_result:
                    output += f"\n✅ Imported as '{import_result.get('name', asset_id)}'"
                    if "location" in import_result:
                        output += f" at {import_result['location']}"
                else:
                    output += f"\n⚠️ Import failed: {import_result.get('error')}"
            except Exception as e:
                output += f"\n⚠️ Could not auto-import: {str(e)}"

        return output

"""MCP tools for VR/Meta Horizon Worlds optimization.

These tools help creators prepare 3D assets for mobile VR platforms.
Targets: Meta Horizon Worlds, Quest standalone apps, and other mobile VR.
"""

from typing import Optional, List


def register_tools(mcp, client):
    """Register VR optimization tools."""

    @mcp.tool()
    async def get_mesh_stats(
        name: Optional[str] = None,
    ) -> str:
        """Get detailed polygon and texture statistics for meshes.

        Essential for checking if models meet VR performance budgets.

        Args:
            name: Object name, or None for all scene objects

        Returns:
            Detailed stats: vertices, triangles, materials, textures, UVs
        """
        result = await client.execute(
            "get_mesh_stats",
            {"name": name, "include_modifiers": True},
        )

        if "error" in result:
            return f"Error: {result['error']}"

        output = "📊 Mesh Statistics\n"
        output += "=" * 40 + "\n\n"

        for obj in result["objects"]:
            output += f"**{obj['name']}**\n"
            output += f"  Vertices: {obj['vertices']:,}\n"
            output += f"  Triangles: {obj['triangles']:,}\n"
            output += f"  Materials: {len(obj['materials'])}\n"
            output += f"  Has UVs: {'Yes' if obj['has_uv'] else 'No ⚠️'}\n"
            if obj['textures']:
                output += f"  Textures:\n"
                for tex in obj['textures']:
                    output += f"    - {tex['name']} ({tex['size'][0]}x{tex['size'][1]})\n"
            output += "\n"

        output += f"**TOTALS**\n"
        output += f"  Objects: {result['object_count']}\n"
        output += f"  Total Triangles: {result['total_triangles']:,}\n"
        output += f"  Unique Materials: {len(result['total_materials'])}\n"
        output += f"  Unique Textures: {len(result['total_textures'])}\n"

        return output

    @mcp.tool()
    async def validate_for_vr(
        name: Optional[str] = None,
        platform: str = "horizon_worlds",
    ) -> str:
        """Validate scene against VR platform requirements.

        Checks polygon counts, texture sizes, materials, and UVs against
        platform-specific limits.

        Args:
            name: Object name, or None for entire scene
            platform: 'horizon_worlds' (default), 'quest', or 'generic_mobile_vr'

        Returns:
            Validation report with errors, warnings, and passed checks
        """
        result = await client.execute(
            "validate_for_vr",
            {"name": name, "platform": platform},
        )

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"🔍 VR Validation: {platform.replace('_', ' ').title()}\n"
        output += "=" * 40 + "\n\n"

        # Status
        if result["valid"]:
            output += "✅ **PASSED** - Ready for VR!\n\n"
        else:
            output += "❌ **FAILED** - Issues found\n\n"

        # Errors
        if result["errors"]:
            output += "**Errors (must fix):**\n"
            for err in result["errors"]:
                output += f"  ❌ {err}\n"
            output += "\n"

        # Warnings
        if result["warnings"]:
            output += "**Warnings (should fix):**\n"
            for warn in result["warnings"]:
                output += f"  ⚠️ {warn}\n"
            output += "\n"

        # Passed
        if result["passed"]:
            output += "**Passed:**\n"
            for p in result["passed"]:
                output += f"  ✅ {p}\n"
            output += "\n"

        # Stats summary
        output += f"**Scene Stats:**\n"
        output += f"  Total triangles: {result['stats']['total_triangles']:,}\n"
        output += f"  Objects: {result['stats']['total_objects']}\n"
        output += f"  Materials: {result['stats']['total_materials']}\n"

        # Platform limits reference
        output += f"\n**{platform.replace('_', ' ').title()} Limits:**\n"
        limits = result["limits"]
        output += f"  Max triangles/object: {limits['max_triangles_per_object']:,}\n"
        output += f"  Max triangles/scene: {limits['max_triangles_scene']:,}\n"
        output += f"  Max texture size: {limits['max_texture_size']}px\n"

        return output

    @mcp.tool()
    async def decimate_mesh(
        name: str,
        ratio: Optional[float] = None,
        target_triangles: Optional[int] = None,
        method: str = "COLLAPSE",
    ) -> str:
        """Reduce polygon count while preserving shape.

        Use this to optimize high-poly meshes for VR performance.

        Args:
            name: Object name to decimate
            ratio: Target ratio (0.0-1.0), e.g., 0.5 = keep 50%
            target_triangles: Alternative to ratio - specify exact triangle count
            method: 'COLLAPSE' (default, best quality), 'UNSUBDIV', or 'DISSOLVE'

        Returns:
            Before/after statistics and reduction percentage
        """
        params = {
            "name": name,
            "method": method,
            "apply": True,
        }
        if ratio is not None:
            params["ratio"] = ratio
        if target_triangles is not None:
            params["target_triangles"] = target_triangles

        result = await client.execute("decimate_mesh", params)

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"✂️ Decimated '{result['name']}'\n\n"
        output += f"**Before:** {result['before']['triangles']:,} triangles\n"
        output += f"**After:** {result['after']['triangles']:,} triangles\n"
        output += f"**Reduced:** {result['reduction']['percentage']}%\n"
        output += f"\nMethod: {result['method']}, Ratio: {result['ratio']:.2f}"

        return output

    @mcp.tool()
    async def generate_lod(
        name: str,
        levels: Optional[List[float]] = None,
    ) -> str:
        """Generate Level of Detail (LOD) variants of a mesh.

        Creates multiple decimated copies for distance-based rendering,
        improving VR performance.

        Args:
            name: Source object name
            levels: List of ratios (default: [1.0, 0.5, 0.25, 0.1])
                    - LOD0: 100% (original)
                    - LOD1: 50%
                    - LOD2: 25%
                    - LOD3: 10%

        Returns:
            List of generated LOD objects with triangle counts
        """
        params = {"name": name}
        if levels:
            params["levels"] = levels

        result = await client.execute("generate_lod", params)

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"📐 Generated LODs for '{result['source']}'\n"
        output += f"Collection: {result['collection']}\n\n"

        for lod in result["lods"]:
            output += f"**{lod['name']}** (LOD{lod['level']})\n"
            output += f"  Triangles: {lod['triangles']:,} ({100 - lod['reduction_percent']:.0f}% of original)\n"

        output += f"\nOriginal triangles: {result['original_triangles']:,}"

        return output

    @mcp.tool()
    async def export_glb(
        output_path: str,
        selected_only: bool = False,
        apply_modifiers: bool = True,
        use_draco: bool = False,
    ) -> str:
        """Export scene as GLB (binary glTF) for VR platforms.

        GLB is the standard format for Meta Horizon Worlds and most VR platforms.

        Args:
            output_path: Path for the .glb file
            selected_only: Export only selected objects (default: all visible)
            apply_modifiers: Apply modifiers before export (default: True)
            use_draco: Enable Draco mesh compression (smaller files)

        Returns:
            Export result with file path and size
        """
        result = await client.execute(
            "export_glb",
            {
                "output_path": output_path,
                "selected_only": selected_only,
                "apply_modifiers": apply_modifiers,
                "compress_textures": use_draco,
            },
        )

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"📦 Exported GLB\n\n"
        output += f"**File:** {result['output_path']}\n"
        output += f"**Size:** {result['file_size_mb']} MB ({result['file_size_bytes']:,} bytes)\n"
        output += f"**Draco compression:** {'Yes' if result['draco_compression'] else 'No'}\n"
        output += f"**Selected only:** {'Yes' if result['selected_only'] else 'No'}"

        return output

    @mcp.tool()
    async def optimize_for_vr(
        target_platform: str = "horizon_worlds",
        auto_decimate: bool = True,
    ) -> str:
        """One-click optimization for VR platforms.

        Automatically:
        1. Decimates meshes that exceed platform limits
        2. Reports optimization results
        3. Validates against platform requirements

        Args:
            target_platform: 'horizon_worlds' (default), 'quest', 'generic_mobile_vr'
            auto_decimate: Automatically reduce high-poly meshes (default: True)

        Returns:
            Optimization summary with before/after stats
        """
        result = await client.execute(
            "optimize_for_vr",
            {
                "target_platform": target_platform,
                "auto_decimate": auto_decimate,
                "validate": True,
            },
        )

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"🚀 VR Optimization Complete\n"
        output += f"Platform: {result['platform'].replace('_', ' ').title()}\n"
        output += "=" * 40 + "\n\n"

        output += f"**Before:** {result['before']['total_triangles']:,} triangles, {result['before']['object_count']} objects\n"
        output += f"**After:** {result['after']['total_triangles']:,} triangles, {result['after']['object_count']} objects\n\n"

        if result["optimizations"]:
            output += "**Optimizations applied:**\n"
            for opt in result["optimizations"]:
                output += f"  • {opt['object']}: {opt['before_tris']:,} → {opt['after_tris']:,} triangles\n"
            output += "\n"

        # Validation summary
        if "validation" in result:
            val = result["validation"]
            if val["valid"]:
                output += "✅ **Validation PASSED** - Ready for VR!\n"
            else:
                output += f"⚠️ **Validation:** {len(val['errors'])} errors, {len(val['warnings'])} warnings\n"
                output += "Run `validate_for_vr()` for details.\n"

        return output

    @mcp.tool()
    async def auto_uv_unwrap(
        name: str,
        method: str = "SMART_PROJECT",
    ) -> str:
        """Automatically UV unwrap a mesh.

        Essential for AI-generated meshes that often have no UVs.
        UVs are required for textures to work in VR.

        Args:
            name: Object name
            method: 'SMART_PROJECT' (default, best for organic),
                    'LIGHTMAP' (for architecture), 'CUBE' (for boxes)

        Returns:
            UV unwrap result
        """
        result = await client.execute(
            "auto_uv_unwrap",
            {"name": name, "method": method},
        )

        if "error" in result:
            return f"Error: {result['error']}"

        output = f"🗺️ UV Unwrapped '{result['name']}'\n\n"
        output += f"Method: {result['method']}\n"
        output += f"UV Layers: {', '.join(result['uv_layers'])}"

        return output

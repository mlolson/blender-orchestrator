"""MCP tools for importing external mesh and model files."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register mesh import tools."""

    @mcp.tool()
    async def import_mesh_file(
        file_path: str,
        name: Optional[str] = None,
        location: Optional[List[float]] = None,
        scale: Optional[float] = None,
        apply_transform: bool = True,
    ) -> str:
        """Import a 3D mesh/model from a local file into the Blender scene.

        Supported formats: GLB, GLTF, OBJ, FBX, PLY, STL.

        Args:
            file_path: Absolute path to the mesh file to import
            name: Optional name for the imported object
            location: [x, y, z] position to place the object (default: [0, 0, 0])
            scale: Uniform scale factor (default: 1.0)
            apply_transform: Apply rotation and scale transforms after import (default: True)
        """
        params = {
            "file_path": file_path,
            "location": location or [0, 0, 0],
            "apply_transform": apply_transform,
        }
        if name is not None:
            params["name"] = name
        if scale is not None:
            params["scale"] = scale

        result = await client.execute("import_mesh_file", params)

        if "error" in result:
            return f"Import failed: {result['error']}"

        imported = result.get("imported_objects", [])
        obj_name = result.get("name", "unknown")
        source = result.get("source_file", file_path)
        return (
            f"Imported '{obj_name}' from {source}\n"
            f"  Objects created: {', '.join(imported)}\n"
            f"  Location: {result.get('location', [0, 0, 0])}"
        )

    @mcp.tool()
    async def import_mesh_from_url(
        url: str,
        name: Optional[str] = None,
        location: Optional[List[float]] = None,
        scale: Optional[float] = None,
        format: Optional[str] = None,
        apply_transform: bool = True,
    ) -> str:
        """Download and import a 3D mesh/model from a URL into the Blender scene.

        The file is downloaded to a temp location, imported, then cleaned up.
        Supported formats: GLB, GLTF, OBJ, FBX, PLY, STL.

        Args:
            url: URL to download the mesh file from
            name: Optional name for the imported object
            location: [x, y, z] position to place the object (default: [0, 0, 0])
            scale: Uniform scale factor (default: 1.0)
            format: File format hint if URL doesn't have an extension (e.g. "glb", "obj")
            apply_transform: Apply rotation and scale transforms after import (default: True)
        """
        params = {
            "url": url,
            "location": location or [0, 0, 0],
            "apply_transform": apply_transform,
        }
        if name is not None:
            params["name"] = name
        if scale is not None:
            params["scale"] = scale
        if format is not None:
            params["format"] = format

        result = await client.execute("import_mesh_from_url", params)

        if "error" in result:
            return f"Import failed: {result['error']}"

        imported = result.get("imported_objects", [])
        obj_name = result.get("name", "unknown")
        source_url = result.get("source_url", url)
        return (
            f"Imported '{obj_name}' from URL\n"
            f"  Source: {source_url}\n"
            f"  Objects created: {', '.join(imported)}\n"
            f"  Location: {result.get('location', [0, 0, 0])}"
        )

    @mcp.tool()
    async def get_supported_import_formats() -> str:
        """Get a list of all supported 3D file formats for mesh importing.

        Returns format names and descriptions. Use this to check which
        file types can be imported before calling import_mesh_file or
        import_mesh_from_url.
        """
        result = await client.execute("get_supported_import_formats", {})

        if "error" in result:
            return f"Error: {result['error']}"

        formats = result.get("formats", {})
        lines = ["Supported import formats:"]
        for ext, desc in formats.items():
            lines.append(f"  .{ext} — {desc}")
        return "\n".join(lines)

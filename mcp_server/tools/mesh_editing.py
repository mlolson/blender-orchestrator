"""MCP tools for mesh editing operations."""

from typing import Optional


def register_tools(mcp, client):
    """Register mesh editing tools."""

    @mcp.tool()
    async def extrude_faces(
        name: str,
        offset: float = 1.0,
    ) -> str:
        """Extrude all faces of a mesh along their normals.

        Args:
            name: Name of the mesh object
            offset: Distance to extrude (positive = outward, negative = inward)
        """
        result = await client.execute(
            "extrude_faces",
            {"name": name, "offset": offset},
        )
        mesh = result.get("mesh", {})
        return f"Extruded '{result['name']}' by {offset}. Mesh now has {mesh.get('vertices', '?')} vertices, {mesh.get('faces', '?')} faces."

    @mcp.tool()
    async def bevel_edges(
        name: str,
        offset: float = 0.1,
        segments: int = 1,
        profile: float = 0.5,
    ) -> str:
        """Bevel the edges of a mesh object.

        Args:
            name: Name of the mesh object
            offset: Bevel width/offset (default: 0.1)
            segments: Number of bevel segments (default: 1)
            profile: Bevel profile shape, 0.0-1.0 where 0.5 is round (default: 0.5)
        """
        result = await client.execute(
            "bevel_edges",
            {
                "name": name,
                "offset": offset,
                "segments": segments,
                "profile": profile,
            },
        )
        mesh = result.get("mesh", {})
        return f"Beveled edges of '{result['name']}'. Mesh now has {mesh.get('vertices', '?')} vertices."

    @mcp.tool()
    async def boolean_operation(
        target: str,
        tool: str,
        operation: str = "DIFFERENCE",
        apply: bool = True,
        hide_tool: bool = True,
    ) -> str:
        """Apply a boolean operation between two mesh objects.

        Args:
            target: Name of the object to modify
            tool: Name of the object to use as the boolean tool
            operation: Type of operation - DIFFERENCE, UNION, or INTERSECT
            apply: Whether to apply the modifier immediately (default: True)
            hide_tool: Whether to hide the tool object after operation (default: True)
        """
        result = await client.execute(
            "boolean_operation",
            {
                "target": target,
                "tool": tool,
                "operation": operation,
                "apply": apply,
                "hide_tool": hide_tool,
            },
        )
        mesh = result.get("mesh", {})
        return f"Applied {operation} boolean to '{result['name']}'. Mesh now has {mesh.get('vertices', '?')} vertices, {mesh.get('faces', '?')} faces."

    @mcp.tool()
    async def subdivide_mesh(
        name: str,
        cuts: int = 1,
        smoothness: float = 0.0,
    ) -> str:
        """Subdivide a mesh by adding cuts.

        Args:
            name: Name of the mesh object
            cuts: Number of cuts to make (default: 1)
            smoothness: Smoothing factor, 0.0-1.0 (default: 0.0)
        """
        result = await client.execute(
            "subdivide_mesh",
            {
                "name": name,
                "cuts": cuts,
                "smoothness": smoothness,
            },
        )
        mesh = result.get("mesh", {})
        return f"Subdivided '{result['name']}' with {cuts} cuts. Mesh now has {mesh.get('vertices', '?')} vertices, {mesh.get('faces', '?')} faces."

    @mcp.tool()
    async def add_subdivision_surface(
        name: str,
        levels: int = 2,
        render_levels: int = 2,
        apply: bool = False,
    ) -> str:
        """Add a subdivision surface modifier to smooth the mesh.

        Args:
            name: Name of the mesh object
            levels: Subdivision levels for viewport (default: 2)
            render_levels: Subdivision levels for rendering (default: 2)
            apply: Whether to apply the modifier immediately (default: False)
        """
        result = await client.execute(
            "add_subdivision_surface",
            {
                "name": name,
                "levels": levels,
                "render_levels": render_levels,
                "apply": apply,
            },
        )
        status = "applied" if apply else "added as modifier"
        return f"Subdivision surface {status} to '{result['name']}' with {levels} levels."

    @mcp.tool()
    async def inset_faces(
        name: str,
        thickness: float = 0.1,
        depth: float = 0.0,
    ) -> str:
        """Inset all faces of a mesh (create smaller faces inside existing ones).

        Args:
            name: Name of the mesh object
            thickness: Inset thickness/distance (default: 0.1)
            depth: Depth to push inset faces (default: 0.0)
        """
        result = await client.execute(
            "inset_faces",
            {
                "name": name,
                "thickness": thickness,
                "depth": depth,
            },
        )
        mesh = result.get("mesh", {})
        return f"Inset faces of '{result['name']}'. Mesh now has {mesh.get('vertices', '?')} vertices, {mesh.get('faces', '?')} faces."

    @mcp.tool()
    async def smooth_mesh(
        name: str,
        iterations: int = 1,
        factor: float = 0.5,
    ) -> str:
        """Smooth a mesh by relaxing vertex positions.

        Args:
            name: Name of the mesh object
            iterations: Number of smoothing iterations (default: 1)
            factor: Smoothing strength, 0.0-1.0 (default: 0.5)
        """
        result = await client.execute(
            "smooth_mesh",
            {
                "name": name,
                "iterations": iterations,
                "factor": factor,
            },
        )
        return f"Smoothed '{result['name']}' with {iterations} iterations."

"""MCP tools for creating primitive objects."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register primitive creation tools."""

    @mcp.tool()
    async def create_cube(
        size: float = 2.0,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a cube primitive in Blender.

        Args:
            size: Size of the cube (default: 2.0)
            location: [x, y, z] position coordinates (default: [0, 0, 0])
            name: Optional name for the object
        """
        result = await client.execute(
            "create_cube",
            {
                "size": size,
                "location": location or [0, 0, 0],
                "name": name,
            },
        )
        return f"Created cube '{result['name']}' at {result['location']}"

    @mcp.tool()
    async def create_sphere(
        radius: float = 1.0,
        segments: int = 32,
        rings: int = 16,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a UV sphere primitive in Blender.

        Args:
            radius: Radius of the sphere (default: 1.0)
            segments: Number of horizontal segments (default: 32)
            rings: Number of vertical rings (default: 16)
            location: [x, y, z] position coordinates (default: [0, 0, 0])
            name: Optional name for the object
        """
        result = await client.execute(
            "create_sphere",
            {
                "radius": radius,
                "segments": segments,
                "rings": rings,
                "location": location or [0, 0, 0],
                "name": name,
            },
        )
        return f"Created sphere '{result['name']}' at {result['location']}"

    @mcp.tool()
    async def create_cylinder(
        radius: float = 1.0,
        depth: float = 2.0,
        vertices: int = 32,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a cylinder primitive in Blender.

        Args:
            radius: Radius of the cylinder (default: 1.0)
            depth: Height of the cylinder (default: 2.0)
            vertices: Number of vertices around the circumference (default: 32)
            location: [x, y, z] position coordinates (default: [0, 0, 0])
            name: Optional name for the object
        """
        result = await client.execute(
            "create_cylinder",
            {
                "radius": radius,
                "depth": depth,
                "vertices": vertices,
                "location": location or [0, 0, 0],
                "name": name,
            },
        )
        return f"Created cylinder '{result['name']}' at {result['location']}"

    @mcp.tool()
    async def create_cone(
        radius1: float = 1.0,
        radius2: float = 0.0,
        depth: float = 2.0,
        vertices: int = 32,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a cone primitive in Blender.

        Args:
            radius1: Bottom radius (default: 1.0)
            radius2: Top radius, 0 for pointed cone (default: 0.0)
            depth: Height of the cone (default: 2.0)
            vertices: Number of vertices around the base (default: 32)
            location: [x, y, z] position coordinates (default: [0, 0, 0])
            name: Optional name for the object
        """
        result = await client.execute(
            "create_cone",
            {
                "radius1": radius1,
                "radius2": radius2,
                "depth": depth,
                "vertices": vertices,
                "location": location or [0, 0, 0],
                "name": name,
            },
        )
        return f"Created cone '{result['name']}' at {result['location']}"

    @mcp.tool()
    async def create_torus(
        major_radius: float = 1.0,
        minor_radius: float = 0.25,
        major_segments: int = 48,
        minor_segments: int = 12,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a torus (donut shape) primitive in Blender.

        Args:
            major_radius: Radius from center to tube center (default: 1.0)
            minor_radius: Radius of the tube itself (default: 0.25)
            major_segments: Segments around the torus ring (default: 48)
            minor_segments: Segments around the tube (default: 12)
            location: [x, y, z] position coordinates (default: [0, 0, 0])
            name: Optional name for the object
        """
        result = await client.execute(
            "create_torus",
            {
                "major_radius": major_radius,
                "minor_radius": minor_radius,
                "major_segments": major_segments,
                "minor_segments": minor_segments,
                "location": location or [0, 0, 0],
                "name": name,
            },
        )
        return f"Created torus '{result['name']}' at {result['location']}"

    @mcp.tool()
    async def create_plane(
        size: float = 2.0,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a plane primitive in Blender.

        Args:
            size: Size of the plane (default: 2.0)
            location: [x, y, z] position coordinates (default: [0, 0, 0])
            name: Optional name for the object
        """
        result = await client.execute(
            "create_plane",
            {
                "size": size,
                "location": location or [0, 0, 0],
                "name": name,
            },
        )
        return f"Created plane '{result['name']}' at {result['location']}"

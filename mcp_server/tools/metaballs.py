"""MCP tools for metaball operations.

Metaballs create organic shapes that automatically blend where they overlap,
making them ideal for character bodies and smooth organic forms.
"""

from typing import Optional, List


def register_tools(mcp, client):
    """Register metaball tools."""

    @mcp.tool()
    async def create_metaball_object(
        name: str = "Metaball",
        resolution: float = 0.2,
        location: Optional[List[float]] = None,
    ) -> str:
        """Create a metaball object that can contain multiple blending elements.

        Metaballs automatically blend together where they overlap, creating
        smooth organic shapes perfect for character bodies.

        Args:
            name: Object name (default: "Metaball")
            resolution: Surface resolution, lower = smoother (default: 0.2)
            location: [x, y, z] position (default: [0, 0, 0])
        """
        result = await client.execute(
            "create_metaball_object",
            {
                "name": name,
                "resolution": resolution,
                "location": location or [0, 0, 0],
            },
        )
        return f"Created metaball object '{result['name']}'"

    @mcp.tool()
    async def add_metaball_element(
        name: str,
        element_type: str = "BALL",
        location: Optional[List[float]] = None,
        radius: float = 1.0,
        size_x: float = 1.0,
        size_y: float = 1.0,
        size_z: float = 1.0,
        stiffness: float = 2.0,
        negative: bool = False,
    ) -> str:
        """Add an element to a metaball object.

        Multiple elements blend together automatically to create the final surface.

        Args:
            name: Metaball object name
            element_type: Type - 'BALL', 'CAPSULE', 'ELLIPSOID', 'CUBE', 'PLANE'
            location: [x, y, z] position relative to object origin
            radius: Base radius (default: 1.0)
            size_x: X scale factor for ellipsoid shapes
            size_y: Y scale factor for ellipsoid shapes
            size_z: Z scale factor for ellipsoid shapes
            stiffness: How sharply it blends (higher = less blending, default: 2.0)
            negative: If True, subtracts from the surface instead of adding
        """
        result = await client.execute(
            "add_metaball_element",
            {
                "name": name,
                "type": element_type,
                "location": location or [0, 0, 0],
                "radius": radius,
                "size_x": size_x,
                "size_y": size_y,
                "size_z": size_z,
                "stiffness": stiffness,
                "negative": negative,
            },
        )
        return f"Added {result['element_type']} element to '{result['name']}' (total: {result['element_count']})"

    @mcp.tool()
    async def convert_metaball_to_mesh(
        name: str,
        keep_original: bool = False,
    ) -> str:
        """Convert a metaball to an editable mesh.

        This 'freezes' the metaball surface into a regular mesh that can be
        edited with standard mesh tools.

        Args:
            name: Metaball object name
            keep_original: Keep the metaball object (default: False)
        """
        result = await client.execute(
            "convert_metaball_to_mesh",
            {
                "name": name,
                "keep_original": keep_original,
            },
        )
        return f"Converted metaball to mesh '{result['name']}' ({result['vertex_count']} vertices)"

    @mcp.tool()
    async def create_metaball_body(
        name: str = "MetaballBody",
        style: str = "cartoon",
        scale: float = 1.0,
        resolution: float = 0.1,
    ) -> str:
        """Create a complete humanoid body shape using metaballs.

        This creates a full body with head, torso, arms, and legs that
        blend naturally together.

        Args:
            name: Object name (default: "MetaballBody")
            style: Body style - 'realistic', 'cartoon', 'chibi' (default: 'cartoon')
            scale: Overall scale factor (default: 1.0)
            resolution: Surface resolution (default: 0.1)
        """
        result = await client.execute(
            "create_metaball_body",
            {
                "name": name,
                "style": style,
                "scale": scale,
                "resolution": resolution,
            },
        )
        return f"Created {result['style']} metaball body '{result['name']}'. {result['message']}"

    @mcp.tool()
    async def get_metaball_elements(name: str) -> str:
        """Get information about all elements in a metaball object.

        Args:
            name: Metaball object name
        """
        result = await client.execute(
            "get_metaball_elements",
            {"name": name},
        )
        elements_info = "\n".join([
            f"  {e['index']}: {e['type']} at {e['location']}, radius={e['radius']}"
            for e in result['elements']
        ])
        return f"Metaball '{result['name']}' has {result['element_count']} elements:\n{elements_info}"

    @mcp.tool()
    async def modify_metaball_element(
        name: str,
        index: int,
        location: Optional[List[float]] = None,
        radius: Optional[float] = None,
        stiffness: Optional[float] = None,
    ) -> str:
        """Modify an existing metaball element.

        Args:
            name: Metaball object name
            index: Element index to modify
            location: New [x, y, z] position (optional)
            radius: New radius (optional)
            stiffness: New stiffness value (optional)
        """
        params = {"name": name, "index": index}
        if location is not None:
            params["location"] = location
        if radius is not None:
            params["radius"] = radius
        if stiffness is not None:
            params["stiffness"] = stiffness

        result = await client.execute("modify_metaball_element", params)
        return f"Modified element {result['modified_index']} of '{result['name']}'"

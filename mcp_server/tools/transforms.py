"""MCP tools for object transformations."""

from typing import Optional, List, Union


def register_tools(mcp, client):
    """Register transform tools."""

    @mcp.tool()
    async def move_object(
        name: str,
        location: Optional[List[float]] = None,
        offset: Optional[List[float]] = None,
    ) -> str:
        """Move an object to a new position or by an offset.

        Args:
            name: Name of the object to move
            location: Absolute [x, y, z] position to move to
            offset: Relative [x, y, z] offset to move by

        Note: Provide either location OR offset, not both.
        """
        params = {"name": name}
        if location is not None:
            params["location"] = location
        elif offset is not None:
            params["offset"] = offset

        result = await client.execute("move_object", params)
        return f"Moved '{result['name']}' to {result['location']}"

    @mcp.tool()
    async def rotate_object(
        name: str,
        rotation: Optional[List[float]] = None,
        rotation_offset: Optional[List[float]] = None,
    ) -> str:
        """Rotate an object (angles in degrees).

        Args:
            name: Name of the object to rotate
            rotation: Absolute [x, y, z] rotation in degrees
            rotation_offset: Relative [x, y, z] rotation offset in degrees

        Note: Provide either rotation OR rotation_offset, not both.
        """
        params = {"name": name}
        if rotation is not None:
            params["rotation"] = rotation
        elif rotation_offset is not None:
            params["rotation_offset"] = rotation_offset

        result = await client.execute("rotate_object", params)
        return f"Rotated '{result['name']}' to {result['rotation']} degrees"

    @mcp.tool()
    async def scale_object(
        name: str,
        scale: Optional[Union[float, List[float]]] = None,
        scale_factor: Optional[Union[float, List[float]]] = None,
    ) -> str:
        """Scale an object.

        Args:
            name: Name of the object to scale
            scale: Absolute scale - single number for uniform, or [x, y, z]
            scale_factor: Relative scale multiplier - single number or [x, y, z]

        Note: Provide either scale OR scale_factor, not both.
        """
        params = {"name": name}
        if scale is not None:
            params["scale"] = scale
        elif scale_factor is not None:
            params["scale_factor"] = scale_factor

        result = await client.execute("scale_object", params)
        return f"Scaled '{result['name']}' to {result['scale']}"

    @mcp.tool()
    async def duplicate_object(
        name: str,
        new_name: Optional[str] = None,
        offset: Optional[List[float]] = None,
        linked: bool = False,
    ) -> str:
        """Duplicate an object.

        Args:
            name: Name of the object to duplicate
            new_name: Optional name for the duplicate
            offset: Optional [x, y, z] offset for the duplicate's position
            linked: If True, create a linked duplicate (shares mesh data)
        """
        result = await client.execute(
            "duplicate_object",
            {
                "name": name,
                "new_name": new_name,
                "offset": offset,
                "linked": linked,
            },
        )
        return f"Duplicated '{name}' as '{result['name']}' at {result['location']}"

    @mcp.tool()
    async def delete_object(name: str) -> str:
        """Delete an object from the scene.

        Args:
            name: Name of the object to delete
        """
        result = await client.execute("delete_object", {"name": name})
        return f"Deleted object '{result['deleted']}'"

    @mcp.tool()
    async def set_origin(
        name: str,
        origin_type: str = "ORIGIN_CENTER_OF_MASS",
    ) -> str:
        """Set the origin point of an object.

        Args:
            name: Name of the object
            origin_type: Type of origin calculation:
                - ORIGIN_GEOMETRY: Origin to geometry center
                - ORIGIN_CENTER_OF_MASS: Origin to center of mass (default)
                - ORIGIN_CENTER_OF_VOLUME: Origin to center of volume
                - ORIGIN_CURSOR: Origin to 3D cursor
        """
        result = await client.execute(
            "set_origin",
            {"name": name, "type": origin_type},
        )
        return f"Set origin of '{result['name']}' to {origin_type}"

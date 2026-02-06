"""MCP tools for floor plan visualization and room creation."""

from typing import Optional


def register_tools(mcp, client):
    """Register floor plan tools."""

    @mcp.tool()
    async def show_floor_plan(
        cell_size: float = 0.5,
        include_labels: bool = True,
    ) -> str:
        """Show an ASCII top-down floor plan of the current scene.

        Projects all mesh objects onto a 2D grid viewed from above.
        Walls shown as W, doors as D, floor as #, other objects by
        their first letter or a short abbreviation. Empty cells are dots.

        This gives a quick spatial overview for reasoning about layout,
        placement, and room arrangement.

        Args:
            cell_size: Grid cell size in meters (smaller = more detail, default 0.5)
            include_labels: Include a legend mapping abbreviations to object names
        """
        result = await client.execute(
            "show_floor_plan",
            {"cell_size": cell_size, "include_labels": include_labels},
        )

        if not result.get("success"):
            return f"❌ Failed to generate floor plan: {result.get('error', 'Unknown error')}"

        lines = []
        lines.append("=" * 50)
        lines.append("FLOOR PLAN (Top-Down View)")
        lines.append("=" * 50)
        lines.append("")
        lines.append(result["floor_plan"])
        lines.append("")
        lines.append(f"Objects: {result['object_count']} | Grid: {result['grid_size'][0]}x{result['grid_size'][1]}")

        return "\n".join(lines)

    @mcp.tool()
    async def create_room_bounds(
        width: float,
        depth: float,
        height: float = 2.7,
        wall_thickness: float = 0.15,
    ) -> str:
        """Create basic room geometry with floor and four walls.

        Creates a rectangular room with properly dimensioned mesh objects.
        The room origin is at (0, 0, 0) with the floor on the XY plane.
        Use this as a starting point before furnishing a room.

        Args:
            width: Room width in meters (X axis)
            depth: Room depth in meters (Y axis)
            height: Wall height in meters (default 2.7)
            wall_thickness: Thickness of walls in meters (default 0.15)
        """
        result = await client.execute(
            "create_room_bounds",
            {
                "width": width,
                "depth": depth,
                "height": height,
                "wall_thickness": wall_thickness,
            },
        )

        if not result.get("success"):
            return f"❌ Failed to create room: {result.get('error', 'Unknown error')}"

        room = result["room"]
        lines = []
        lines.append(f"✅ {result['message']}")
        lines.append("")
        lines.append(f"Room dimensions: {room['width']}m × {room['depth']}m × {room['height']}m")
        lines.append(f"Wall thickness: {room['wall_thickness']}m")
        lines.append(f"Created objects: {', '.join(result['created_objects'])}")

        return "\n".join(lines)

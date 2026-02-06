"""MCP tools for floor plan visualization and room creation."""

from typing import Optional


def register_tools(mcp, client):
    """Register floor plan tools."""

    @mcp.tool()
    async def show_floor_plan(
        view: str = "top",
        cell_size: float = 0.25,
        max_grid: int = 120,
        include_labels: bool = True,
    ) -> str:
        """Show an ASCII view of the current scene from any angle.

        Projects all mesh objects onto a 2D grid from the chosen viewpoint.
        Walls shown as W, doors as D, floor as #, other objects by
        their first letter or a short abbreviation. Empty cells are dots.

        Use "all" to get views from all 6 sides at once for a complete
        spatial understanding of the scene.

        Args:
            view: Viewpoint - "top", "bottom", "front", "back", "left", "right", or "all"
            cell_size: Grid cell size in meters (smaller = higher resolution, default 0.25)
            max_grid: Maximum grid dimension in cells (default 120, increase for more detail)
            include_labels: Include a legend mapping abbreviations to object names
        """
        result = await client.execute(
            "show_floor_plan",
            {
                "view": view,
                "cell_size": cell_size,
                "max_grid": max_grid,
                "include_labels": include_labels,
            },
        )

        if not result.get("success"):
            return f"❌ Failed to generate view: {result.get('error', 'Unknown error')}"

        lines = []
        lines.append("=" * 60)
        views = result.get("views", ["top"])
        if len(views) == 1:
            lines.append(f"SCENE VIEW: {views[0].upper()}")
        else:
            lines.append(f"SCENE VIEWS: {', '.join(v.upper() for v in views)}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(result["floor_plan"])
        lines.append("")
        lines.append(f"Objects: {result['object_count']}")

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

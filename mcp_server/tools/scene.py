"""MCP tools for scene queries and management."""

from typing import Optional
import json


def register_tools(mcp, client):
    """Register scene query and management tools."""

    @mcp.tool()
    async def list_objects(
        type_filter: Optional[str] = None,
        name_contains: Optional[str] = None,
    ) -> str:
        """List all objects in the Blender scene.

        Args:
            type_filter: Filter by object type - MESH, CAMERA, LIGHT, EMPTY, etc.
            name_contains: Filter to objects whose names contain this string
        """
        result = await client.execute(
            "list_objects",
            {
                "type": type_filter,
                "name_contains": name_contains,
            },
        )
        objects = result.get("objects", [])

        if not objects:
            return "No objects found in the scene."

        lines = [f"Scene contains {result['count']} object(s):"]
        for obj in objects:
            loc = obj["location"]
            visible = "visible" if obj["visible"] else "hidden"
            lines.append(
                f"  - {obj['name']} ({obj['type']}) at ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f}) [{visible}]"
            )

        return "\n".join(lines)

    @mcp.tool()
    async def get_object_info(name: str) -> str:
        """Get detailed information about a specific object.

        Args:
            name: Name of the object to query
        """
        result = await client.execute("get_object_info", {"name": name})

        lines = [f"Object: {result['name']}"]
        lines.append(f"  Type: {result['type']}")
        lines.append(f"  Location: {result['location']}")
        lines.append(f"  Rotation: {result['rotation']} degrees")
        lines.append(f"  Scale: {result['scale']}")
        lines.append(f"  Visible: {result['visible']}")

        if "mesh" in result:
            mesh = result["mesh"]
            lines.append(f"  Mesh: {mesh['vertices']} vertices, {mesh['edges']} edges, {mesh['faces']} faces")

        if result.get("materials"):
            lines.append(f"  Materials: {', '.join(m for m in result['materials'] if m)}")

        if result.get("modifiers"):
            mod_names = [m["name"] for m in result["modifiers"]]
            lines.append(f"  Modifiers: {', '.join(mod_names)}")

        if result.get("parent"):
            lines.append(f"  Parent: {result['parent']}")

        if result.get("children"):
            lines.append(f"  Children: {', '.join(result['children'])}")

        return "\n".join(lines)

    @mcp.tool()
    async def get_scene_summary() -> str:
        """Get a comprehensive summary of the current Blender scene."""
        result = await client.execute("get_scene_summary", {})

        lines = [f"Scene: {result['scene_name']}"]
        lines.append(f"Total objects: {result['total_objects']}")

        if result["object_counts"]:
            lines.append("Objects by type:")
            for obj_type, count in result["object_counts"].items():
                lines.append(f"  - {obj_type}: {count}")

        if result.get("camera"):
            cam = result["camera"]
            lines.append(f"Active camera: {cam['name']} at {cam['location']}")
        else:
            lines.append("Active camera: None")

        render = result.get("render_settings", {})
        lines.append(f"Render engine: {render.get('engine', 'N/A')}")
        if render.get("resolution"):
            lines.append(f"Resolution: {render['resolution'][0]}x{render['resolution'][1]}")

        lines.append(f"Materials: {result.get('material_count', 0)}")
        lines.append(f"Frame: {result.get('frame_current', 1)} (range: {result.get('frame_range', [1, 250])})")

        return "\n".join(lines)

    @mcp.tool()
    async def get_selected_objects() -> str:
        """Get information about currently selected objects in Blender."""
        result = await client.execute("get_selected_objects", {})

        if result["count"] == 0:
            return "No objects selected."

        lines = [f"Selected objects ({result['count']}):"]
        for obj in result["selected"]:
            lines.append(f"  - {obj['name']} ({obj['type']}) at {obj['location']}")

        if result.get("active"):
            lines.append(f"Active object: {result['active']['name']}")

        return "\n".join(lines)

    @mcp.tool()
    async def select_object(
        name: str,
        add_to_selection: bool = False,
    ) -> str:
        """Select an object in Blender.

        Args:
            name: Name of the object to select
            add_to_selection: If True, add to current selection instead of replacing
        """
        result = await client.execute(
            "select_object",
            {"name": name, "add": add_to_selection},
        )
        return f"Selected '{result['name']}'"

    @mcp.tool()
    async def deselect_all() -> str:
        """Deselect all objects in the scene."""
        await client.execute("deselect_all", {})
        return "Deselected all objects"

    @mcp.tool()
    async def set_object_visibility(
        name: str,
        visible: bool = True,
        viewport: bool = True,
        render: bool = True,
    ) -> str:
        """Set the visibility of an object.

        Args:
            name: Name of the object
            visible: Whether the object should be visible
            viewport: Apply to viewport visibility
            render: Apply to render visibility
        """
        result = await client.execute(
            "set_object_visibility",
            {
                "name": name,
                "visible": visible,
                "viewport": viewport,
                "render": render,
            },
        )
        status = "visible" if not result.get("hide_viewport") else "hidden"
        return f"Set '{result['name']}' to {status}"

    @mcp.tool()
    async def set_parent(
        child: str,
        parent: Optional[str] = None,
    ) -> str:
        """Set or clear the parent of an object.

        Args:
            child: Name of the child object
            parent: Name of the parent object, or None to clear parent
        """
        result = await client.execute(
            "set_parent",
            {"child": child, "parent": parent},
        )
        if parent:
            return f"Set parent of '{result['name']}' to '{parent}'"
        else:
            return f"Cleared parent of '{result['name']}'"

    @mcp.tool()
    async def check_blender_connection() -> str:
        """Check if the Blender server is running and responsive."""
        try:
            is_healthy = await client.health_check()
            if is_healthy:
                return "Blender server is running and responsive."
            else:
                return "Blender server is not responding. Make sure the MCP Bridge addon is enabled and the server is started in Blender."
        except Exception as e:
            return f"Cannot connect to Blender server: {e}. Make sure Blender is running with the MCP Bridge addon."

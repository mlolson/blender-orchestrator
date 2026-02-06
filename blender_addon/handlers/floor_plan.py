"""Handlers for floor plan visualization and room creation."""

import bpy
import mathutils
from typing import Any, Dict, List, Tuple


def _get_object_world_bounds(obj) -> Tuple[mathutils.Vector, mathutils.Vector]:
    """Get world-space bounding box min/max for an object."""
    if obj.type == 'MESH' and obj.data:
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        min_corner = mathutils.Vector((
            min(c.x for c in bbox_corners),
            min(c.y for c in bbox_corners),
            min(c.z for c in bbox_corners)
        ))
        max_corner = mathutils.Vector((
            max(c.x for c in bbox_corners),
            max(c.y for c in bbox_corners),
            max(c.z for c in bbox_corners)
        ))
        return min_corner, max_corner
    else:
        loc = obj.matrix_world.translation
        offset = mathutils.Vector((0.1, 0.1, 0.1))
        return loc - offset, loc + offset


def _get_abbreviation(name: str, used: Dict[str, str]) -> str:
    """Get a short abbreviation for an object name, avoiding conflicts."""
    # Try first letter uppercase
    abbr = name[0].upper()
    if abbr not in used:
        return abbr
    # Try first two consonants or first + second letter
    clean = name.replace("_", "").replace(".", "").replace(" ", "")
    for i in range(1, len(clean)):
        candidate = clean[0].upper() + clean[i].lower()
        if candidate not in used:
            return candidate
    # Fallback: first letter + number
    count = 1
    while f"{abbr}{count}" in used:
        count += 1
    return f"{abbr}{count}"


def handle_show_floor_plan(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an ASCII top-down floor plan of the scene."""
    cell_size = params.get("cell_size", 0.5)
    include_labels = params.get("include_labels", True)

    # Gather all visible mesh objects
    objects_info = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or not obj.visible_get():
            continue
        min_b, max_b = _get_object_world_bounds(obj)
        objects_info.append({
            "name": obj.name,
            "min": min_b,
            "max": max_b,
        })

    if not objects_info:
        return {
            "success": True,
            "floor_plan": "No mesh objects in scene.",
            "object_count": 0,
        }

    # Compute scene bounds (X = right, Y = depth in Blender)
    scene_min_x = min(o["min"].x for o in objects_info)
    scene_max_x = max(o["max"].x for o in objects_info)
    scene_min_y = min(o["min"].y for o in objects_info)
    scene_max_y = max(o["max"].y for o in objects_info)

    # Add small padding
    pad = cell_size
    scene_min_x -= pad
    scene_min_y -= pad
    scene_max_x += pad
    scene_max_y += pad

    width = scene_max_x - scene_min_x
    depth = scene_max_y - scene_min_y

    cols = max(1, int(width / cell_size))
    rows = max(1, int(depth / cell_size))

    # Cap grid size to keep output readable
    max_grid = 60
    if cols > max_grid:
        cols = max_grid
        cell_size_x = width / cols
    else:
        cell_size_x = cell_size
    if rows > max_grid:
        rows = max_grid
        cell_size_y = depth / rows
    else:
        cell_size_y = cell_size

    # Build grid
    grid = [['.' for _ in range(cols)] for _ in range(rows)]

    # Assign abbreviations
    abbr_map = {}  # abbr -> name
    name_to_abbr = {}
    # Detect wall-like objects (name contains wall/floor)
    for obj_info in objects_info:
        name_lower = obj_info["name"].lower()
        is_wall = any(w in name_lower for w in ["wall", "boundary"])
        is_floor = "floor" in name_lower
        is_door = "door" in name_lower

        if is_wall:
            char = "W"
        elif is_floor:
            char = "#"
        elif is_door:
            char = "D"
        else:
            char = None

        if char and char not in abbr_map:
            abbr_map[char] = obj_info["name"]
            name_to_abbr[obj_info["name"]] = char
        elif char is None:
            abbr = _get_abbreviation(obj_info["name"], abbr_map)
            abbr_map[abbr] = obj_info["name"]
            name_to_abbr[obj_info["name"]] = abbr

    # If a wall char is already taken, still assign
    for obj_info in objects_info:
        if obj_info["name"] not in name_to_abbr:
            abbr = _get_abbreviation(obj_info["name"], abbr_map)
            abbr_map[abbr] = obj_info["name"]
            name_to_abbr[obj_info["name"]] = abbr

    # Fill grid cells
    for obj_info in objects_info:
        abbr = name_to_abbr[obj_info["name"]]
        # Map object bounds to grid cells
        col_start = int((obj_info["min"].x - scene_min_x) / cell_size_x)
        col_end = int((obj_info["max"].x - scene_min_x) / cell_size_x)
        row_start = int((obj_info["min"].y - scene_min_y) / cell_size_y)
        row_end = int((obj_info["max"].y - scene_min_y) / cell_size_y)

        col_start = max(0, min(col_start, cols - 1))
        col_end = max(0, min(col_end, cols - 1))
        row_start = max(0, min(row_start, rows - 1))
        row_end = max(0, min(row_end, rows - 1))

        # Use first char of abbreviation for grid display
        display_char = abbr[0]
        for r in range(row_start, row_end + 1):
            for c in range(col_start, col_end + 1):
                # Walls take priority
                if grid[r][c] == '.' or (display_char == 'W' and grid[r][c] != 'W'):
                    grid[r][c] = display_char

    # Build output string
    lines = []
    lines.append(f"Scene: {width:.1f}m x {depth:.1f}m (cell: {cell_size:.2f}m)")
    lines.append("")

    # Column headers
    col_width = 2
    header = "  "
    for c in range(cols):
        header += f"{c % 10:<{col_width}}"
    lines.append(header)

    for r in range(rows):
        row_str = f"{r % 10} "
        for c in range(cols):
            row_str += f"{grid[r][c]:<{col_width}}"
        lines.append(row_str)

    # Legend
    if include_labels:
        lines.append("")
        legend_items = []
        for abbr, name in sorted(abbr_map.items(), key=lambda x: x[1]):
            legend_items.append(f"{abbr}={name}")
        lines.append("Legend: " + ", ".join(legend_items))

    floor_plan_text = "\n".join(lines)

    return {
        "success": True,
        "floor_plan": floor_plan_text,
        "object_count": len(objects_info),
        "grid_size": [cols, rows],
        "scene_bounds": {
            "min": [scene_min_x + pad, scene_min_y + pad],
            "max": [scene_max_x - pad, scene_max_y - pad],
        },
    }


def handle_create_room_bounds(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create basic room geometry: floor + 4 walls."""
    width = params["width"]
    depth = params["depth"]
    height = params.get("height", 2.7)
    wall_thickness = params.get("wall_thickness", 0.15)

    created = []

    # Floor
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(width / 2, depth / 2, -wall_thickness / 2),
    )
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.scale = (width, depth, wall_thickness)
    bpy.ops.object.transform_apply(scale=True)
    created.append(floor.name)

    # Wall definitions: (name, location, scale)
    walls = [
        ("Wall_Back", (width / 2, 0, height / 2), (width, wall_thickness, height)),
        ("Wall_Front", (width / 2, depth, height / 2), (width, wall_thickness, height)),
        ("Wall_Left", (0, depth / 2, height / 2), (wall_thickness, depth, height)),
        ("Wall_Right", (width, depth / 2, height / 2), (wall_thickness, depth, height)),
    ]

    for name, loc, scale in walls:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        wall = bpy.context.active_object
        wall.name = name
        wall.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        created.append(wall.name)

    return {
        "success": True,
        "room": {
            "width": width,
            "depth": depth,
            "height": height,
            "wall_thickness": wall_thickness,
        },
        "created_objects": created,
        "message": f"Created room {width}m x {depth}m x {height}m with {wall_thickness}m thick walls.",
    }


FLOOR_PLAN_HANDLERS = {
    "show_floor_plan": handle_show_floor_plan,
    "create_room_bounds": handle_create_room_bounds,
}

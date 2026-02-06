"""Handlers for floor plan visualization and room creation."""

import bpy
import mathutils
from typing import Any, Dict, List, Tuple


# View definitions: (name, axis1, axis2, flip1, flip2)
# axis1 = horizontal axis index (0=X, 1=Y, 2=Z)
# axis2 = vertical axis index
# flip1/flip2 = whether to flip that axis
VIEW_DEFS = {
    "top":    {"h": 0, "v": 1, "fh": False, "fv": False, "label": "Top (looking down, +Z)"},
    "bottom": {"h": 0, "v": 1, "fh": False, "fv": True,  "label": "Bottom (looking up, -Z)"},
    "front":  {"h": 0, "v": 2, "fh": False, "fv": False, "label": "Front (looking from -Y)"},
    "back":   {"h": 0, "v": 2, "fh": True,  "fv": False, "label": "Back (looking from +Y)"},
    "left":   {"h": 1, "v": 2, "fh": False, "fv": False, "label": "Left (looking from -X)"},
    "right":  {"h": 1, "v": 2, "fh": True,  "fv": False, "label": "Right (looking from +X)"},
}

AXIS_NAMES = ["X", "Y", "Z"]


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
    abbr = name[0].upper()
    if abbr not in used:
        return abbr
    clean = name.replace("_", "").replace(".", "").replace(" ", "")
    for i in range(1, len(clean)):
        candidate = clean[0].upper() + clean[i].lower()
        if candidate not in used:
            return candidate
    count = 1
    while f"{abbr}{count}" in used:
        count += 1
    return f"{abbr}{count}"


def _classify_object(name: str) -> str | None:
    """Return a fixed char for known object types, or None."""
    name_lower = name.lower()
    if any(w in name_lower for w in ["wall", "boundary"]):
        return "W"
    if "floor" in name_lower:
        return "#"
    if "door" in name_lower:
        return "D"
    return None


def _render_view(
    view_name: str,
    objects_info: list,
    cell_size: float,
    include_labels: bool,
    max_grid: int,
) -> str:
    """Render a single ASCII view of the scene."""
    vdef = VIEW_DEFS[view_name]
    h_axis = vdef["h"]  # horizontal axis index
    v_axis = vdef["v"]  # vertical axis index
    flip_h = vdef["fh"]
    flip_v = vdef["fv"]

    # Compute bounds along the two projection axes
    scene_min_h = min(o["min"][h_axis] for o in objects_info)
    scene_max_h = max(o["max"][h_axis] for o in objects_info)
    scene_min_v = min(o["min"][v_axis] for o in objects_info)
    scene_max_v = max(o["max"][v_axis] for o in objects_info)

    pad = cell_size
    scene_min_h -= pad
    scene_min_v -= pad
    scene_max_h += pad
    scene_max_v += pad

    span_h = scene_max_h - scene_min_h
    span_v = scene_max_v - scene_min_v

    cols = max(1, int(span_h / cell_size))
    rows = max(1, int(span_v / cell_size))

    if cols > max_grid:
        cols = max_grid
    if rows > max_grid:
        rows = max_grid

    cell_size_h = span_h / cols
    cell_size_v = span_v / rows

    # Build grid
    grid = [['.' for _ in range(cols)] for _ in range(rows)]

    # Assign abbreviations
    abbr_map = {}
    name_to_abbr = {}
    for obj_info in objects_info:
        char = _classify_object(obj_info["name"])
        if char and char not in abbr_map:
            abbr_map[char] = obj_info["name"]
            name_to_abbr[obj_info["name"]] = char
        elif char is None:
            abbr = _get_abbreviation(obj_info["name"], abbr_map)
            abbr_map[abbr] = obj_info["name"]
            name_to_abbr[obj_info["name"]] = abbr

    for obj_info in objects_info:
        if obj_info["name"] not in name_to_abbr:
            abbr = _get_abbreviation(obj_info["name"], abbr_map)
            abbr_map[abbr] = obj_info["name"]
            name_to_abbr[obj_info["name"]] = abbr

    # Fill grid
    for obj_info in objects_info:
        abbr = name_to_abbr[obj_info["name"]]
        display_char = abbr[0]

        obj_min_h = obj_info["min"][h_axis]
        obj_max_h = obj_info["max"][h_axis]
        obj_min_v = obj_info["min"][v_axis]
        obj_max_v = obj_info["max"][v_axis]

        col_start = int((obj_min_h - scene_min_h) / cell_size_h)
        col_end = int((obj_max_h - scene_min_h) / cell_size_h)
        row_start = int((obj_min_v - scene_min_v) / cell_size_v)
        row_end = int((obj_max_v - scene_min_v) / cell_size_v)

        col_start = max(0, min(col_start, cols - 1))
        col_end = max(0, min(col_end, cols - 1))
        row_start = max(0, min(row_start, rows - 1))
        row_end = max(0, min(row_end, rows - 1))

        for r in range(row_start, row_end + 1):
            for c in range(col_start, col_end + 1):
                if grid[r][c] == '.' or (display_char == 'W' and grid[r][c] != 'W'):
                    grid[r][c] = display_char

    # Apply flips
    if flip_v:
        grid = grid[::-1]
    if flip_h:
        grid = [row[::-1] for row in grid]

    # Build output
    lines = []
    lines.append(f"--- {vdef['label']} ---")
    lines.append(f"Axes: horizontal={AXIS_NAMES[h_axis]}, vertical={AXIS_NAMES[v_axis]} | "
                 f"{span_h:.1f}m x {span_v:.1f}m (cell: {cell_size:.2f}m, grid: {cols}x{rows})")
    lines.append("")

    # Render grid — use single-char cells for compactness at high res
    for r in range(rows):
        row_str = ""
        for c in range(cols):
            row_str += grid[r][c]
        lines.append(row_str)

    if include_labels:
        lines.append("")
        legend_items = []
        for abbr, name in sorted(abbr_map.items(), key=lambda x: x[1]):
            legend_items.append(f"{abbr}={name}")
        lines.append("Legend: " + ", ".join(legend_items))

    return "\n".join(lines)


def handle_show_floor_plan(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate ASCII views of the scene from specified angles."""
    cell_size = params.get("cell_size", 0.25)
    include_labels = params.get("include_labels", True)
    view = params.get("view", "top")
    max_grid = params.get("max_grid", 120)

    valid_views = list(VIEW_DEFS.keys()) + ["all"]
    if view not in valid_views:
        return {"success": False, "error": f"Invalid view '{view}'. Choose from: {', '.join(valid_views)}"}

    # Gather all visible mesh objects
    objects_info = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or not obj.visible_get():
            continue
        min_b, max_b = _get_object_world_bounds(obj)
        objects_info.append({
            "name": obj.name,
            "min": (min_b.x, min_b.y, min_b.z),
            "max": (max_b.x, max_b.y, max_b.z),
        })

    if not objects_info:
        return {
            "success": True,
            "floor_plan": "No mesh objects in scene.",
            "object_count": 0,
            "grid_size": [0, 0],
        }

    views_to_render = list(VIEW_DEFS.keys()) if view == "all" else [view]
    sections = []
    grid_size = [0, 0]

    for v in views_to_render:
        section = _render_view(v, objects_info, cell_size, include_labels, max_grid)
        sections.append(section)

    floor_plan_text = "\n\n".join(sections)

    return {
        "success": True,
        "floor_plan": floor_plan_text,
        "object_count": len(objects_info),
        "grid_size": grid_size,
        "views": views_to_render,
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

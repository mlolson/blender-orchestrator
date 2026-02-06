"""Handlers for mesh editing operations."""

import bpy
import bmesh
import math
from mathutils import Vector
from typing import Any, Dict, List, Optional
from ..utils.serializers import serialize_object


def get_mesh_object(name: str) -> bpy.types.Object:
    """Get mesh object by name, raise if not found or not a mesh."""
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != "MESH":
        raise ValueError(f"Object '{name}' is not a mesh (type: {obj.type})")
    return obj


def ensure_object_mode() -> None:
    """Ensure we're in object mode."""
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def extrude_faces(params: Dict[str, Any]) -> Dict[str, Any]:
    """Extrude all faces of a mesh along their normals."""
    name = params["name"]
    offset = params.get("offset", 1.0)

    obj = get_mesh_object(name)
    ensure_object_mode()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Enter edit mode
    bpy.ops.object.mode_set(mode="EDIT")

    # Select all faces
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.select_mode(type="FACE")

    # Extrude along normals
    bpy.ops.mesh.extrude_region_shrink_fatten(
        TRANSFORM_OT_shrink_fatten={"value": offset}
    )

    bpy.ops.object.mode_set(mode="OBJECT")

    return serialize_object(obj, detailed=True)


def bevel_edges(params: Dict[str, Any]) -> Dict[str, Any]:
    """Bevel edges of an object."""
    name = params["name"]
    offset = params.get("offset", 0.1)
    segments = params.get("segments", 1)
    profile = params.get("profile", 0.5)

    obj = get_mesh_object(name)
    ensure_object_mode()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.select_mode(type="EDGE")

    bpy.ops.mesh.bevel(
        offset=offset,
        segments=segments,
        profile=profile,
        affect="EDGES",
    )

    bpy.ops.object.mode_set(mode="OBJECT")

    return serialize_object(obj, detailed=True)


def boolean_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply boolean operation between two objects."""
    target_name = params["target"]
    tool_name = params["tool"]
    operation = params.get("operation", "DIFFERENCE").upper()
    apply_modifier = params.get("apply", True)
    hide_tool = params.get("hide_tool", True)

    # Validate operation
    valid_ops = ["DIFFERENCE", "UNION", "INTERSECT"]
    if operation not in valid_ops:
        raise ValueError(f"Invalid operation '{operation}'. Must be one of: {valid_ops}")

    target = get_mesh_object(target_name)
    tool = get_mesh_object(tool_name)

    ensure_object_mode()

    # Add boolean modifier
    mod = target.modifiers.new(name="Boolean", type="BOOLEAN")
    mod.operation = operation
    mod.object = tool
    mod.solver = "EXACT"

    if apply_modifier:
        bpy.ops.object.select_all(action="DESELECT")
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=mod.name)

    if hide_tool:
        tool.hide_set(True)

    return serialize_object(target, detailed=True)


def subdivide_mesh(params: Dict[str, Any]) -> Dict[str, Any]:
    """Subdivide a mesh."""
    name = params["name"]
    cuts = params.get("cuts", 1)
    smoothness = params.get("smoothness", 0.0)

    obj = get_mesh_object(name)
    ensure_object_mode()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    bpy.ops.mesh.subdivide(
        number_cuts=cuts,
        smoothness=smoothness,
    )

    bpy.ops.object.mode_set(mode="OBJECT")

    return serialize_object(obj, detailed=True)


def add_subdivision_surface(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add subdivision surface modifier to an object."""
    name = params["name"]
    levels = params.get("levels", 2)
    render_levels = params.get("render_levels", 2)
    apply_modifier = params.get("apply", False)

    obj = get_mesh_object(name)
    ensure_object_mode()

    mod = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels

    if apply_modifier:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    return serialize_object(obj, detailed=True)


def inset_faces(params: Dict[str, Any]) -> Dict[str, Any]:
    """Inset faces of a mesh."""
    name = params["name"]
    thickness = params.get("thickness", 0.1)
    depth = params.get("depth", 0.0)

    obj = get_mesh_object(name)
    ensure_object_mode()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.select_mode(type="FACE")

    bpy.ops.mesh.inset(thickness=thickness, depth=depth)

    bpy.ops.object.mode_set(mode="OBJECT")

    return serialize_object(obj, detailed=True)


def smooth_mesh(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply smoothing to a mesh."""
    name = params["name"]
    iterations = params.get("iterations", 1)
    factor = params.get("factor", 0.5)

    obj = get_mesh_object(name)
    ensure_object_mode()

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    for _ in range(iterations):
        bpy.ops.mesh.vertices_smooth(factor=factor)

    bpy.ops.object.mode_set(mode="OBJECT")

    return serialize_object(obj, detailed=True)


def get_mesh_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get vertex, edge, and face data from a mesh."""
    name = params["name"]
    include_normals = params.get("include_normals", False)

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data

    # Get vertices
    vertices = []
    for v in mesh.vertices:
        vert_data = {
            "index": v.index,
            "co": list(v.co),
        }
        if include_normals:
            vert_data["normal"] = list(v.normal)
        vertices.append(vert_data)

    # Get edges
    edges = [{"index": e.index, "vertices": list(e.vertices)} for e in mesh.edges]

    # Get faces
    faces = [{"index": f.index, "vertices": list(f.vertices)} for f in mesh.polygons]

    return {
        "name": obj.name,
        "vertex_count": len(vertices),
        "edge_count": len(edges),
        "face_count": len(faces),
        "vertices": vertices,
        "edges": edges,
        "faces": faces,
    }


def set_vertex_positions(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set positions of specific vertices by index.

    params:
        name: object name
        vertices: list of {"index": int, "co": [x, y, z]} dicts
    """
    name = params["name"]
    vertex_data = params["vertices"]

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data
    modified_count = 0

    for v_data in vertex_data:
        idx = v_data["index"]
        if 0 <= idx < len(mesh.vertices):
            mesh.vertices[idx].co = Vector(v_data["co"])
            modified_count += 1

    mesh.update()

    return {
        "name": obj.name,
        "modified_vertices": modified_count,
        "total_vertices": len(mesh.vertices),
    }


def proportional_edit(params: Dict[str, Any]) -> Dict[str, Any]:
    """Move a vertex with proportional falloff affecting nearby vertices.

    This simulates sculpting by moving one point and having nearby
    vertices follow with a smooth falloff.

    params:
        name: object name
        vertex_index: index of the vertex to move (or use 'position' instead)
        position: [x, y, z] to find nearest vertex (alternative to vertex_index)
        offset: [x, y, z] movement offset
        radius: falloff radius (vertices within this distance are affected)
        falloff: falloff type - 'SMOOTH', 'SPHERE', 'LINEAR', 'SHARP', 'ROOT'
    """
    name = params["name"]
    offset = Vector(params["offset"])
    radius = params.get("radius", 1.0)
    falloff_type = params.get("falloff", "SMOOTH").upper()

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data

    # Find the center vertex
    if "vertex_index" in params:
        center_idx = params["vertex_index"]
        if center_idx < 0 or center_idx >= len(mesh.vertices):
            raise ValueError(f"Vertex index {center_idx} out of range")
        center_co = Vector(mesh.vertices[center_idx].co)
    elif "position" in params:
        # Find nearest vertex to position
        target = Vector(params["position"])
        min_dist = float('inf')
        center_idx = 0
        center_co = Vector(mesh.vertices[0].co)
        for v in mesh.vertices:
            dist = (Vector(v.co) - target).length
            if dist < min_dist:
                min_dist = dist
                center_idx = v.index
                center_co = Vector(v.co)
    else:
        raise ValueError("Must provide either 'vertex_index' or 'position'")

    # Apply world matrix to get world coordinates
    world_matrix = obj.matrix_world
    center_world = world_matrix @ center_co

    # Falloff functions
    def smooth_falloff(dist, radius):
        t = dist / radius
        return 1 - (3 * t * t - 2 * t * t * t)  # Smoothstep

    def sphere_falloff(dist, radius):
        t = dist / radius
        return math.sqrt(1 - t * t) if t < 1 else 0

    def linear_falloff(dist, radius):
        return 1 - (dist / radius)

    def sharp_falloff(dist, radius):
        t = dist / radius
        return (1 - t) ** 2

    def root_falloff(dist, radius):
        t = dist / radius
        return math.sqrt(1 - t) if t < 1 else 0

    falloff_funcs = {
        'SMOOTH': smooth_falloff,
        'SPHERE': sphere_falloff,
        'LINEAR': linear_falloff,
        'SHARP': sharp_falloff,
        'ROOT': root_falloff,
    }

    falloff_func = falloff_funcs.get(falloff_type, smooth_falloff)

    # Move vertices with falloff
    modified_count = 0
    for v in mesh.vertices:
        v_world = world_matrix @ Vector(v.co)
        dist = (v_world - center_world).length

        if dist <= radius:
            factor = falloff_func(dist, radius)
            # Apply offset scaled by falloff factor
            v.co = Vector(v.co) + (offset * factor)
            modified_count += 1

    mesh.update()

    return {
        "name": obj.name,
        "center_vertex": center_idx,
        "modified_vertices": modified_count,
        "radius": radius,
        "falloff": falloff_type,
    }


def get_vertices_in_radius(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get all vertices within a radius of a point.

    params:
        name: object name
        position: [x, y, z] center point (in local coordinates)
        radius: search radius
    """
    name = params["name"]
    position = Vector(params["position"])
    radius = params.get("radius", 1.0)

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data

    vertices = []
    for v in mesh.vertices:
        dist = (Vector(v.co) - position).length
        if dist <= radius:
            vertices.append({
                "index": v.index,
                "co": list(v.co),
                "distance": dist,
            })

    # Sort by distance
    vertices.sort(key=lambda x: x["distance"])

    return {
        "name": obj.name,
        "center": list(position),
        "radius": radius,
        "count": len(vertices),
        "vertices": vertices,
    }


def sculpt_grab(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate a sculpt grab brush - grab and move vertices.

    params:
        name: object name
        position: [x, y, z] grab center point (in local coordinates)
        offset: [x, y, z] movement direction and distance
        radius: brush radius
        strength: brush strength (0-1)
    """
    name = params["name"]
    position = Vector(params["position"])
    offset = Vector(params["offset"])
    radius = params.get("radius", 0.5)
    strength = params.get("strength", 1.0)

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data

    modified_count = 0
    for v in mesh.vertices:
        dist = (Vector(v.co) - position).length
        if dist <= radius:
            # Smooth falloff
            t = dist / radius
            factor = (1 - (3 * t * t - 2 * t * t * t)) * strength
            v.co = Vector(v.co) + (offset * factor)
            modified_count += 1

    mesh.update()

    return {
        "name": obj.name,
        "modified_vertices": modified_count,
    }


def sculpt_inflate(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate a sculpt inflate brush - push vertices along their normals.

    params:
        name: object name
        position: [x, y, z] brush center point (in local coordinates)
        radius: brush radius
        strength: how much to inflate (can be negative to deflate)
    """
    name = params["name"]
    position = Vector(params["position"])
    radius = params.get("radius", 0.5)
    strength = params.get("strength", 0.1)

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data

    # In Blender 4.0+, normals are calculated automatically when accessed
    # Force a mesh update to ensure normals are current
    mesh.update()

    modified_count = 0
    for v in mesh.vertices:
        dist = (Vector(v.co) - position).length
        if dist <= radius:
            # Smooth falloff
            t = dist / radius
            factor = (1 - (3 * t * t - 2 * t * t * t)) * strength
            # Move along vertex normal
            v.co = Vector(v.co) + (Vector(v.normal) * factor)
            modified_count += 1

    mesh.update()

    return {
        "name": obj.name,
        "modified_vertices": modified_count,
    }


def sculpt_smooth(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate a sculpt smooth brush - average vertex positions with neighbors.

    params:
        name: object name
        position: [x, y, z] brush center point (in local coordinates)
        radius: brush radius
        strength: smoothing strength (0-1)
        iterations: number of smoothing passes
    """
    name = params["name"]
    position = Vector(params["position"])
    radius = params.get("radius", 0.5)
    strength = params.get("strength", 0.5)
    iterations = params.get("iterations", 1)

    obj = get_mesh_object(name)
    ensure_object_mode()

    mesh = obj.data

    # Build adjacency map
    adjacency = {v.index: set() for v in mesh.vertices}
    for edge in mesh.edges:
        v1, v2 = edge.vertices
        adjacency[v1].add(v2)
        adjacency[v2].add(v1)

    # Find vertices in radius
    affected_verts = []
    for v in mesh.vertices:
        dist = (Vector(v.co) - position).length
        if dist <= radius:
            t = dist / radius
            factor = (1 - (3 * t * t - 2 * t * t * t)) * strength
            affected_verts.append((v.index, factor))

    # Perform smoothing iterations
    for _ in range(iterations):
        new_positions = {}
        for v_idx, factor in affected_verts:
            v = mesh.vertices[v_idx]
            neighbors = adjacency[v_idx]
            if neighbors:
                # Average of neighbor positions
                avg = Vector((0, 0, 0))
                for n_idx in neighbors:
                    avg += Vector(mesh.vertices[n_idx].co)
                avg /= len(neighbors)
                # Blend between current position and average
                new_positions[v_idx] = Vector(v.co).lerp(avg, factor)

        # Apply new positions
        for v_idx, new_co in new_positions.items():
            mesh.vertices[v_idx].co = new_co

    mesh.update()

    return {
        "name": obj.name,
        "modified_vertices": len(affected_verts),
    }


def join_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """Join multiple objects into one mesh.

    params:
        target: name of the target object (will contain the result)
        objects: list of object names to join into target
    """
    target_name = params["target"]
    object_names = params["objects"]

    target = get_mesh_object(target_name)
    ensure_object_mode()

    # Select all objects to join
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target

    for obj_name in object_names:
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.type == "MESH":
            obj.select_set(True)

    # Join
    bpy.ops.object.join()

    return serialize_object(target, detailed=True)


# =============================================================================
# Native Blender Sculpt Mode Operations
# =============================================================================

def enter_sculpt_mode(params: Dict[str, Any]) -> Dict[str, Any]:
    """Enter sculpt mode for an object.

    params:
        name: object name
        use_dyntopo: enable dynamic topology (default False)
        detail_size: dyntopo detail size (default 12)
    """
    name = params["name"]
    use_dyntopo = params.get("use_dyntopo", False)
    detail_size = params.get("detail_size", 12)

    obj = get_mesh_object(name)

    # Ensure object mode first
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Select and activate the object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Enter sculpt mode
    bpy.ops.object.mode_set(mode="SCULPT")

    # Enable dynamic topology if requested
    if use_dyntopo:
        if not bpy.context.sculpt_object.use_dynamic_topology_sculpting:
            bpy.ops.sculpt.dynamic_topology_toggle()
        bpy.context.scene.tool_settings.sculpt.detail_size = detail_size

    return {
        "name": obj.name,
        "mode": "SCULPT",
        "dyntopo_enabled": use_dyntopo,
    }


def exit_sculpt_mode(params: Dict[str, Any]) -> Dict[str, Any]:
    """Exit sculpt mode and return to object mode."""
    if bpy.context.mode == "SCULPT":
        # Disable dyntopo if enabled
        if (bpy.context.sculpt_object and
            bpy.context.sculpt_object.use_dynamic_topology_sculpting):
            bpy.ops.sculpt.dynamic_topology_toggle()
        bpy.ops.object.mode_set(mode="OBJECT")

    return {"mode": "OBJECT"}


def set_sculpt_brush(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set the active sculpt brush and its settings.

    params:
        brush: brush type - 'DRAW', 'CLAY', 'CLAY_STRIPS', 'INFLATE', 'BLOB',
               'GRAB', 'SNAKE_HOOK', 'THUMB', 'SMOOTH', 'PINCH', 'CREASE',
               'FLATTEN', 'FILL', 'SCRAPE', 'MASK'
        radius: brush radius in pixels (default 50)
        strength: brush strength 0-1 (default 0.5)
        direction: 'ADD' or 'SUBTRACT' (default 'ADD')
        use_smooth_stroke: smooth stroke (default False)
    """
    brush_type = params.get("brush", "DRAW").upper()
    radius = params.get("radius", 50)
    strength = params.get("strength", 0.5)
    direction = params.get("direction", "ADD").upper()
    use_smooth = params.get("use_smooth_stroke", False)

    # Ensure we're in sculpt mode
    if bpy.context.mode != "SCULPT":
        raise ValueError("Must be in sculpt mode. Call enter_sculpt_mode first.")

    tool_settings = bpy.context.scene.tool_settings.sculpt

    # Map brush types to Blender's brush names
    brush_map = {
        'DRAW': 'SculptDraw',
        'CLAY': 'Clay',
        'CLAY_STRIPS': 'Clay Strips',
        'INFLATE': 'Inflate/Deflate',
        'BLOB': 'Blob',
        'GRAB': 'Grab',
        'SNAKE_HOOK': 'Snake Hook',
        'THUMB': 'Thumb',
        'SMOOTH': 'Smooth',
        'PINCH': 'Pinch/Magnify',
        'CREASE': 'Crease',
        'FLATTEN': 'Flatten/Contrast',
        'FILL': 'Fill/Deepen',
        'SCRAPE': 'Scrape/Peaks',
        'MASK': 'Mask',
        'NUDGE': 'Nudge',
        'ROTATE': 'Rotate',
        'ELASTIC': 'Elastic Deform',
    }

    brush_name = brush_map.get(brush_type, 'SculptDraw')

    # Get or create the brush
    brush = bpy.data.brushes.get(brush_name)
    if brush:
        tool_settings.brush = brush
    else:
        # Try to set by sculpt tool
        try:
            bpy.ops.wm.tool_set_by_id(name=f"builtin_brush.{brush_type}")
        except:
            pass

    # Set brush properties
    if tool_settings.brush:
        tool_settings.brush.size = int(radius)
        tool_settings.brush.strength = strength
        tool_settings.brush.use_smooth_stroke = use_smooth

        if direction == "SUBTRACT":
            tool_settings.brush.direction = 'SUBTRACT'
        else:
            tool_settings.brush.direction = 'ADD'

    return {
        "brush": brush_type,
        "radius": radius,
        "strength": strength,
        "direction": direction,
    }


def sculpt_stroke(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a sculpt brush stroke along a path.

    params:
        name: object name
        stroke: list of points, each point is {"location": [x,y,z], "pressure": 0-1}
                or just [x, y, z] for simple strokes
        brush: brush type (optional, uses current if not specified)
        radius: brush radius (optional)
        strength: brush strength (optional)
    """
    name = params["name"]
    stroke_data = params["stroke"]

    obj = get_mesh_object(name)

    # Enter sculpt mode if not already
    if bpy.context.mode != "SCULPT":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="SCULPT")

    # Set brush if specified
    if "brush" in params:
        set_sculpt_brush({
            "brush": params["brush"],
            "radius": params.get("radius", 50),
            "strength": params.get("strength", 0.5),
        })

    # Build stroke data - Blender 4.x format
    stroke_points = []
    for i, point in enumerate(stroke_data):
        if isinstance(point, dict):
            loc = point.get("location", [0, 0, 0])
            pressure = point.get("pressure", 1.0)
        else:
            loc = point
            pressure = 1.0

        # Minimal stroke point format for Blender 4.x
        stroke_points.append({
            "name": f"stroke_{i}",
            "mouse": (0, 0),
            "mouse_event": (0, 0),
            "location": tuple(loc),
            "pressure": pressure,
            "is_start": i == 0,
        })

    # Apply the stroke
    try:
        bpy.ops.sculpt.brush_stroke(
            stroke=stroke_points,
            mode='NORMAL'
        )
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {
        "name": obj.name,
        "stroke_points": len(stroke_points),
        "success": True,
    }


def remesh_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply remesh modifier for better sculpting topology.

    params:
        name: object name
        mode: 'VOXEL', 'QUAD', or 'BLOCKS' (default 'VOXEL')
        voxel_size: size for voxel remesh (default 0.05)
        octree_depth: depth for other modes (default 6)
        apply: whether to apply the modifier (default True)
    """
    name = params["name"]
    mode = params.get("mode", "VOXEL").upper()
    voxel_size = params.get("voxel_size", 0.05)
    octree_depth = params.get("octree_depth", 6)
    apply = params.get("apply", True)

    obj = get_mesh_object(name)
    ensure_object_mode()

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # For voxel remesh in Blender 2.9+, use the built-in voxel remesh
    if mode == "VOXEL":
        obj.data.remesh_voxel_size = voxel_size
        bpy.ops.object.voxel_remesh()
    else:
        # Use remesh modifier
        mod = obj.modifiers.new(name="Remesh", type="REMESH")
        mod.mode = mode
        mod.octree_depth = octree_depth

        if apply:
            bpy.ops.object.modifier_apply(modifier=mod.name)

    return serialize_object(obj, detailed=True)


def apply_symmetry(params: Dict[str, Any]) -> Dict[str, Any]:
    """Enable symmetry for sculpting.

    params:
        x: enable X symmetry (default True)
        y: enable Y symmetry (default False)
        z: enable Z symmetry (default False)
    """
    x_sym = params.get("x", True)
    y_sym = params.get("y", False)
    z_sym = params.get("z", False)

    if bpy.context.mode != "SCULPT":
        raise ValueError("Must be in sculpt mode")

    sculpt = bpy.context.scene.tool_settings.sculpt

    sculpt.use_symmetry_x = x_sym
    sculpt.use_symmetry_y = y_sym
    sculpt.use_symmetry_z = z_sym

    return {
        "symmetry": {
            "x": x_sym,
            "y": y_sym,
            "z": z_sym,
        }
    }


def sculpt_mask(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply mask operations for sculpting.

    params:
        name: object name
        operation: 'INVERT', 'FILL', 'CLEAR', 'SMOOTH', 'SHARPEN', 'EXPAND'
    """
    name = params["name"]
    operation = params.get("operation", "CLEAR").upper()

    obj = get_mesh_object(name)

    if bpy.context.mode != "SCULPT":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="SCULPT")

    ops_map = {
        'INVERT': lambda: bpy.ops.paint.mask_flood_fill(mode='INVERT'),
        'FILL': lambda: bpy.ops.paint.mask_flood_fill(mode='VALUE', value=1.0),
        'CLEAR': lambda: bpy.ops.paint.mask_flood_fill(mode='VALUE', value=0.0),
        'SMOOTH': lambda: bpy.ops.sculpt.mask_filter(filter_type='SMOOTH'),
        'SHARPEN': lambda: bpy.ops.sculpt.mask_filter(filter_type='SHARPEN'),
    }

    if operation in ops_map:
        ops_map[operation]()

    return {
        "name": obj.name,
        "operation": operation,
    }


def mesh_filter(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a mesh filter to the entire sculpt mesh.

    These filters affect the whole mesh and are great for global adjustments.

    params:
        name: object name
        filter_type: 'SMOOTH', 'SCALE', 'INFLATE', 'SPHERE', 'RANDOM',
                     'RELAX', 'SURFACE_SMOOTH', 'SHARPEN', 'ENHANCE_DETAILS'
        strength: filter strength (default 1.0)
        iterations: number of iterations (default 1)
    """
    name = params["name"]
    filter_type = params.get("filter_type", "SMOOTH").upper()
    strength = params.get("strength", 1.0)
    iterations = params.get("iterations", 1)

    obj = get_mesh_object(name)

    # Enter sculpt mode if needed
    if bpy.context.mode != "SCULPT":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="SCULPT")

    # Apply filter multiple times for iterations
    for _ in range(iterations):
        try:
            bpy.ops.sculpt.mesh_filter(type=filter_type, strength=strength)
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {
        "name": obj.name,
        "filter_type": filter_type,
        "strength": strength,
        "iterations": iterations,
        "success": True,
    }


def cloth_filter(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply cloth simulation filter for organic deformation.

    params:
        name: object name
        filter_type: 'GRAVITY', 'INFLATE', 'EXPAND', 'PINCH'
        strength: filter strength (default 1.0)
        iterations: number of iterations (default 1)
    """
    name = params["name"]
    filter_type = params.get("filter_type", "GRAVITY").upper()
    strength = params.get("strength", 1.0)
    iterations = params.get("iterations", 1)

    obj = get_mesh_object(name)

    if bpy.context.mode != "SCULPT":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="SCULPT")

    for _ in range(iterations):
        try:
            bpy.ops.sculpt.cloth_filter(type=filter_type, strength=strength)
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {
        "name": obj.name,
        "filter_type": filter_type,
        "strength": strength,
        "iterations": iterations,
        "success": True,
    }


def color_filter(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply color adjustments (if vertex colors exist).

    params:
        name: object name
        filter_type: 'FILL', 'HUE', 'SATURATION', 'VALUE', 'BRIGHTNESS',
                     'CONTRAST', 'RED', 'GREEN', 'BLUE', 'SMOOTH'
        strength: filter strength (default 1.0)
    """
    name = params["name"]
    filter_type = params.get("filter_type", "SMOOTH").upper()
    strength = params.get("strength", 1.0)

    obj = get_mesh_object(name)

    if bpy.context.mode != "SCULPT":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="SCULPT")

    try:
        bpy.ops.sculpt.color_filter(type=filter_type, strength=strength)
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {
        "name": obj.name,
        "filter_type": filter_type,
        "success": True,
    }


def set_pivot_position(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set sculpt pivot position for transformations.

    params:
        name: object name
        position: [x, y, z] pivot position
    """
    name = params["name"]
    position = params.get("position", [0, 0, 0])

    obj = get_mesh_object(name)

    if bpy.context.mode != "SCULPT":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="SCULPT")

    try:
        bpy.ops.sculpt.set_pivot_position(mode='SURFACE', surface_co=tuple(position))
    except:
        pass

    return {
        "name": obj.name,
        "pivot": position,
    }


# =============================================================================
# Modifier Tools
# =============================================================================

def add_shrinkwrap_modifier(params: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap one mesh onto another surface.

    Great for conforming features (eyes, accessories) to body surface,
    or making objects follow terrain.

    params:
        target: object to shrinkwrap (the object that will be deformed)
        wrapper: surface to wrap onto (the target surface)
        mode: wrap method - 'NEAREST_SURFACEPOINT', 'PROJECT', 'NEAREST_VERTEX', 'TARGET_PROJECT'
        offset: distance from surface (default 0.0, positive = outside, negative = inside)
        apply: apply the modifier immediately (default False)
        subsurf_levels: subdivision levels to add before shrinkwrap (optional)
    """
    target_name = params["target"]
    wrapper_name = params["wrapper"]
    mode = params.get("mode", "NEAREST_SURFACEPOINT")
    offset = params.get("offset", 0.0)
    apply = params.get("apply", False)
    subsurf_levels = params.get("subsurf_levels")

    target = bpy.data.objects.get(target_name)
    wrapper = bpy.data.objects.get(wrapper_name)

    if not target:
        raise ValueError(f"Target object '{target_name}' not found")
    if not wrapper:
        raise ValueError(f"Wrapper object '{wrapper_name}' not found")

    ensure_object_mode()

    # Add subdivision first if requested (for better conforming)
    if subsurf_levels:
        subsurf = target.modifiers.new("Subdivision", 'SUBSURF')
        subsurf.levels = subsurf_levels

    # Add shrinkwrap modifier
    mod = target.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
    mod.wrap_method = mode
    mod.target = wrapper
    mod.offset = offset

    if apply:
        bpy.ops.object.select_all(action="DESELECT")
        target.select_set(True)
        bpy.context.view_layer.objects.active = target

        # Apply in order
        for m in list(target.modifiers):
            if m.type in ['SUBSURF', 'SHRINKWRAP']:
                bpy.ops.object.modifier_apply(modifier=m.name)

    return serialize_object(target, detailed=True)


def add_solidify_modifier(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add solidify modifier to give thickness to a mesh.

    Also useful for creating cartoon outlines when using flip normals.

    params:
        name: object name
        thickness: shell thickness
        offset: offset from original surface (-1 to 1, default -1)
        use_rim: create rim faces (default True)
        use_flip_normals: flip normals for outline effect (default False)
        material_offset: material slot offset for rim/shell (default 0)
        apply: apply the modifier (default False)
    """
    object_name = params["name"]
    thickness = params.get("thickness", 0.01)
    offset = params.get("offset", -1.0)
    use_rim = params.get("use_rim", True)
    use_flip = params.get("use_flip_normals", False)
    material_offset = params.get("material_offset", 0)
    apply = params.get("apply", False)

    obj = get_mesh_object(object_name)
    ensure_object_mode()

    mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = offset
    mod.use_rim = use_rim
    mod.use_flip_normals = use_flip
    mod.material_offset = material_offset

    if apply:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    return serialize_object(obj)


def add_mirror_modifier(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add mirror modifier for symmetrical modeling.

    params:
        name: object name
        axis: 'X', 'Y', 'Z' or combination like 'XY' (default 'X')
        merge: merge vertices at center (default True)
        merge_threshold: merge distance (default 0.001)
        apply: apply the modifier (default False)
    """
    object_name = params["name"]
    axis = params.get("axis", "X").upper()
    merge = params.get("merge", True)
    merge_threshold = params.get("merge_threshold", 0.001)
    apply = params.get("apply", False)

    obj = get_mesh_object(object_name)
    ensure_object_mode()

    mod = obj.modifiers.new("Mirror", 'MIRROR')
    mod.use_axis[0] = 'X' in axis
    mod.use_axis[1] = 'Y' in axis
    mod.use_axis[2] = 'Z' in axis
    mod.use_mirror_merge = merge
    mod.merge_threshold = merge_threshold

    if apply:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    return serialize_object(obj)


# =============================================================================
# Face Integration Tools
# =============================================================================

def create_eye_socket(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an eye socket depression in a head mesh.

    This properly integrates eye placement by:
    1. Creating a socket depression
    2. Adding edge loops around the socket
    3. Preparing for eyeball placement

    params:
        head: head mesh object name
        position: [x, y, z] eye center position
        radius: socket radius (default 0.03)
        depth: socket depth (default 0.015)
        edge_loops: number of edge loops around socket (default 2)
    """
    head_name = params["head"]
    position = Vector(params["position"])
    radius = params.get("radius", 0.03)
    depth = params.get("depth", 0.015)

    obj = get_mesh_object(head_name)
    ensure_object_mode()

    # Use proportional edit to create socket depression
    # Push vertices inward around eye position
    proportional_edit({
        "name": head_name,
        "position": list(position),
        "offset": [0, -depth, 0],  # Push inward (assuming Y is forward)
        "radius": radius,
        "falloff": "SMOOTH"
    })

    # Add a ring of vertices for better topology (via smooth)
    sculpt_smooth({
        "name": head_name,
        "position": list(position),
        "radius": radius * 1.2,
        "strength": 0.3,
        "iterations": 2
    })

    return {
        "head": head_name,
        "socket_position": list(position),
        "socket_radius": radius,
        "socket_depth": depth,
    }


def create_integrated_eye(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an eye that's properly integrated into a head mesh.

    This creates:
    1. Eye socket (depression in head mesh)
    2. Eyeball (properly positioned sphere)
    3. Optional eyelid geometry

    params:
        head: head mesh object name
        position: [x, y, z] eye center position
        radius: eye radius (default 0.025)
        socket_depth: how deep the socket is (default 0.01)
        iris_color: [r, g, b] iris color (default blue)
        create_socket: create socket depression (default True)
    """
    head_name = params["head"]
    position = Vector(params["position"])
    radius = params.get("radius", 0.025)
    socket_depth = params.get("socket_depth", 0.01)
    iris_color = params.get("iris_color", [0.2, 0.4, 0.7, 1.0])
    create_socket = params.get("create_socket", True)

    # Determine eye side (left or right)
    side = "R" if position.x > 0 else "L"
    eye_name = f"Eye_{side}"

    # Create socket depression in head
    if create_socket:
        create_eye_socket({
            "head": head_name,
            "position": list(position),
            "radius": radius * 1.3,
            "depth": socket_depth,
        })

    # Create eyeball sphere
    eye_pos = position.copy()
    eye_pos.y -= socket_depth * 0.3  # Slightly recessed

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=24,
        ring_count=16,
        location=eye_pos
    )
    eye_obj = bpy.context.active_object
    eye_obj.name = eye_name

    # Create and assign eye material
    from .materials import create_eye_shader, assign_material

    mat_name = f"EyeMat_{side}"
    create_eye_shader({
        "name": mat_name,
        "iris_color": iris_color,
        "pupil_size": 0.3,
        "wetness": 0.95,
    })

    assign_material({
        "object_name": eye_name,
        "material_name": mat_name,
    })

    return {
        "eye_name": eye_name,
        "head": head_name,
        "position": list(position),
        "radius": radius,
        "material": mat_name,
    }


def create_mouth_opening(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mouth opening/depression in a head mesh.

    params:
        head: head mesh object name
        position: [x, y, z] mouth center position
        width: mouth width (default 0.04)
        height: mouth height (default 0.01)
        depth: mouth depth (default 0.01)
    """
    head_name = params["head"]
    position = Vector(params["position"])
    width = params.get("width", 0.04)
    height = params.get("height", 0.01)
    depth = params.get("depth", 0.01)

    obj = get_mesh_object(head_name)
    ensure_object_mode()

    # Create mouth depression using multiple proportional edits
    # Center
    proportional_edit({
        "name": head_name,
        "position": list(position),
        "offset": [0, -depth, 0],
        "radius": width * 0.5,
        "falloff": "SMOOTH"
    })

    # Smooth the edges
    sculpt_smooth({
        "name": head_name,
        "position": list(position),
        "radius": width * 0.7,
        "strength": 0.4,
        "iterations": 2
    })

    return {
        "head": head_name,
        "mouth_position": list(position),
        "width": width,
        "height": height,
    }


def create_nose_bump(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a nose protrusion on a head mesh.

    params:
        head: head mesh object name
        position: [x, y, z] nose tip position
        width: nose width (default 0.02)
        height: nose height/protrusion (default 0.025)
        length: nose length from bridge to tip (default 0.03)
    """
    head_name = params["head"]
    position = Vector(params["position"])
    width = params.get("width", 0.02)
    height = params.get("height", 0.025)
    length = params.get("length", 0.03)

    obj = get_mesh_object(head_name)
    ensure_object_mode()

    # Create nose tip protrusion
    proportional_edit({
        "name": head_name,
        "position": list(position),
        "offset": [0, height, 0],  # Push outward
        "radius": width,
        "falloff": "SPHERE"
    })

    # Create nose bridge (above the tip)
    bridge_pos = position + Vector([0, 0, length * 0.7])
    proportional_edit({
        "name": head_name,
        "position": list(bridge_pos),
        "offset": [0, height * 0.5, 0],
        "radius": width * 0.7,
        "falloff": "SMOOTH"
    })

    # Smooth transitions
    sculpt_smooth({
        "name": head_name,
        "position": list(position),
        "radius": width * 1.5,
        "strength": 0.3,
        "iterations": 1
    })

    return {
        "head": head_name,
        "nose_position": list(position),
        "width": width,
        "height": height,
    }


def add_cartoon_outline(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add cartoon-style outline to an object using solidify modifier.

    params:
        name: object name
        thickness: outline thickness (default 0.02)
        color: [r, g, b] outline color (default black)
    """
    object_name = params["name"]
    thickness = params.get("thickness", 0.02)
    color = params.get("color", [0.0, 0.0, 0.0, 1.0])

    obj = get_mesh_object(object_name)

    # Create outline material
    from .materials import create_cartoon_outline_material, assign_material

    outline_mat_name = f"{object_name}_Outline"
    create_cartoon_outline_material({
        "name": outline_mat_name,
        "color": color,
    })

    # Add material to object
    obj.data.materials.append(bpy.data.materials[outline_mat_name])
    outline_slot = len(obj.material_slots) - 1

    # Add solidify modifier for outline
    add_solidify_modifier({
        "name": object_name,
        "thickness": thickness,
        "offset": 1.0,  # Outside
        "use_rim": False,
        "use_flip_normals": True,  # Important for outline effect
        "material_offset": outline_slot,
    })

    return {
        "name": object_name,
        "outline_material": outline_mat_name,
        "thickness": thickness,
    }


MESH_EDITING_HANDLERS = {
    "extrude_faces": extrude_faces,
    "bevel_edges": bevel_edges,
    "boolean_operation": boolean_operation,
    "subdivide_mesh": subdivide_mesh,
    "add_subdivision_surface": add_subdivision_surface,
    "inset_faces": inset_faces,
    "smooth_mesh": smooth_mesh,
    # New vertex-level editing functions
    "get_mesh_data": get_mesh_data,
    "set_vertex_positions": set_vertex_positions,
    "proportional_edit": proportional_edit,
    "get_vertices_in_radius": get_vertices_in_radius,
    "sculpt_grab": sculpt_grab,
    "sculpt_inflate": sculpt_inflate,
    "sculpt_smooth": sculpt_smooth,
    "join_objects": join_objects,
    # Native Blender sculpt mode
    "enter_sculpt_mode": enter_sculpt_mode,
    "exit_sculpt_mode": exit_sculpt_mode,
    "set_sculpt_brush": set_sculpt_brush,
    "sculpt_stroke": sculpt_stroke,
    "remesh_object": remesh_object,
    "apply_symmetry": apply_symmetry,
    "sculpt_mask": sculpt_mask,
    "mesh_filter": mesh_filter,
    "cloth_filter": cloth_filter,
    "color_filter": color_filter,
    "set_pivot_position": set_pivot_position,
    # Modifier tools
    "add_shrinkwrap_modifier": add_shrinkwrap_modifier,
    "add_solidify_modifier": add_solidify_modifier,
    "add_mirror_modifier": add_mirror_modifier,
    # Face integration tools
    "create_eye_socket": create_eye_socket,
    "create_integrated_eye": create_integrated_eye,
    "create_mouth_opening": create_mouth_opening,
    "create_nose_bump": create_nose_bump,
    "add_cartoon_outline": add_cartoon_outline,
}

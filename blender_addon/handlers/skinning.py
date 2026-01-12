"""Handlers for skin modifier and armature-based mesh generation.

The skin modifier creates mesh geometry around a skeleton of edges,
perfect for generating humanoid bodies with proper joint topology.
"""

import bpy
import math
from typing import Any, Dict, List
from mathutils import Vector
from ..utils.serializers import serialize_object


def create_armature(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an armature object.

    params:
        name: armature name (default "Armature")
        location: [x, y, z] position (default [0, 0, 0])
    """
    name = params.get("name", "Armature")
    location = params.get("location", [0, 0, 0])

    # Create armature data
    armature = bpy.data.armatures.new(name)
    armature.display_type = 'OCTAHEDRAL'

    # Create armature object
    obj = bpy.data.objects.new(name, armature)
    obj.location = location
    bpy.context.collection.objects.link(obj)

    # Select and activate
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return serialize_object(obj)


def add_bone(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add a bone to an armature.

    params:
        armature: armature object name
        name: bone name
        head: [x, y, z] head (start) position
        tail: [x, y, z] tail (end) position
        parent: parent bone name (optional)
        connected: connect to parent tail (default False)
        roll: bone roll angle in radians (default 0)
    """
    armature_name = params["armature"]
    bone_name = params["name"]
    head = params["head"]
    tail = params["tail"]
    parent_name = params.get("parent")
    connected = params.get("connected", False)
    roll = params.get("roll", 0.0)

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != 'ARMATURE':
        raise ValueError(f"'{armature_name}' is not an armature object")

    # Must be in edit mode to add bones
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Create new bone
    bone = obj.data.edit_bones.new(bone_name)
    bone.head = head
    bone.tail = tail
    bone.roll = roll

    # Set parent if specified
    if parent_name:
        parent = obj.data.edit_bones.get(parent_name)
        if parent:
            bone.parent = parent
            bone.use_connect = connected

    bpy.ops.object.mode_set(mode='OBJECT')

    return {
        "armature": armature_name,
        "bone": bone_name,
        "head": list(head),
        "tail": list(tail),
    }


def create_skin_mesh(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mesh with skin modifier from a vertex/edge skeleton.

    The skin modifier generates mesh geometry around edges, creating
    a natural-looking surface. Great for humanoid bodies.

    params:
        name: mesh name
        vertices: list of [x, y, z] vertex positions
        edges: list of [v1, v2] vertex index pairs defining connections
        root_vertex: index of root vertex (default 0)
        default_radius: default skin radius (default 0.1)
        subdivision_levels: subdivision surface levels (default 1)
    """
    name = params["name"]
    vertices = params["vertices"]
    edges = params["edges"]
    root_vertex = params.get("root_vertex", 0)
    default_radius = params.get("default_radius", 0.1)
    subdivision_levels = params.get("subdivision_levels", 1)

    if not vertices or not edges:
        raise ValueError("Must provide vertices and edges")

    # Create mesh
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, [])
    mesh.update()

    # Create object
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Select and activate
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Add skin modifier
    skin_mod = obj.modifiers.new("Skin", 'SKIN')

    # Set root vertex
    obj.data.skin_vertices[0].data[root_vertex].use_root = True

    # Set default radius for all vertices
    for sv in obj.data.skin_vertices[0].data:
        sv.radius = (default_radius, default_radius)

    # Add subdivision surface for smoothness
    if subdivision_levels > 0:
        subsurf = obj.modifiers.new("Subdivision", 'SUBSURF')
        subsurf.levels = subdivision_levels
        subsurf.render_levels = subdivision_levels + 1

    return serialize_object(obj)


def set_skin_radius(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set skin radius for specific vertices.

    params:
        name: skin mesh object name
        vertices: list of {"index": int, "radius": [rx, ry]} or
                  {"index": int, "radius": float} for uniform radius
    """
    name = params["name"]
    vertex_data = params["vertices"]

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    if not obj.data.skin_vertices:
        raise ValueError(f"Object '{name}' does not have skin data")

    skin_verts = obj.data.skin_vertices[0].data
    modified = 0

    for v_data in vertex_data:
        idx = v_data["index"]
        radius = v_data["radius"]

        if idx < len(skin_verts):
            if isinstance(radius, (int, float)):
                skin_verts[idx].radius = (radius, radius)
            else:
                skin_verts[idx].radius = tuple(radius)
            modified += 1

    return {
        "name": name,
        "modified_vertices": modified,
    }


def set_skin_root(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set which vertex is the root of the skin mesh.

    params:
        name: skin mesh object name
        vertex_index: index of vertex to set as root
    """
    name = params["name"]
    vertex_index = params["vertex_index"]

    obj = bpy.data.objects.get(name)
    if not obj or not obj.data.skin_vertices:
        raise ValueError(f"'{name}' is not a skin mesh")

    skin_verts = obj.data.skin_vertices[0].data

    # Clear existing roots
    for sv in skin_verts:
        sv.use_root = False

    # Set new root
    if vertex_index < len(skin_verts):
        skin_verts[vertex_index].use_root = True

    return {
        "name": name,
        "root_vertex": vertex_index,
    }


def mark_skin_loose(params: Dict[str, Any]) -> Dict[str, Any]:
    """Mark vertices as loose (disconnected from parent branch).

    params:
        name: skin mesh object name
        vertices: list of vertex indices to mark as loose
        loose: whether to mark as loose (True) or connected (False)
    """
    name = params["name"]
    vertices = params["vertices"]
    loose = params.get("loose", True)

    obj = bpy.data.objects.get(name)
    if not obj or not obj.data.skin_vertices:
        raise ValueError(f"'{name}' is not a skin mesh")

    skin_verts = obj.data.skin_vertices[0].data

    for idx in vertices:
        if idx < len(skin_verts):
            skin_verts[idx].use_loose = loose

    return {
        "name": name,
        "marked_vertices": len(vertices),
    }


def apply_skin_modifier(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the skin modifier to convert to regular mesh.

    params:
        name: skin mesh object name
        apply_subdivision: also apply subdivision surface (default True)
    """
    name = params["name"]
    apply_subdivision = params.get("apply_subdivision", True)

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    bpy.context.view_layer.objects.active = obj

    # Find and apply skin modifier
    for mod in obj.modifiers:
        if mod.type == 'SKIN':
            bpy.ops.object.modifier_apply(modifier=mod.name)
            break

    # Optionally apply subdivision
    if apply_subdivision:
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                bpy.ops.object.modifier_apply(modifier=mod.name)
                break

    return serialize_object(obj, detailed=True)


def create_humanoid_skeleton(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a basic humanoid skeleton structure for skin modifier.

    This creates a complete vertex/edge structure suitable for
    generating a humanoid body with the skin modifier.

    params:
        name: mesh name (default "HumanoidSkeleton")
        height: total height (default 1.8)
        style: 'realistic', 'cartoon', 'chibi' (default 'realistic')
    """
    name = params.get("name", "HumanoidSkeleton")
    height = params.get("height", 1.8)
    style = params.get("style", "realistic").lower()

    # Define proportions based on style
    if style == "cartoon":
        head_ratio = 0.25  # Larger head
        torso_ratio = 0.3
        leg_ratio = 0.35
    elif style == "chibi":
        head_ratio = 0.35  # Very large head
        torso_ratio = 0.25
        leg_ratio = 0.3
    else:  # realistic
        head_ratio = 0.12
        torso_ratio = 0.35
        leg_ratio = 0.45

    # Calculate absolute sizes
    h = height
    head_size = h * head_ratio
    torso_height = h * torso_ratio
    leg_height = h * leg_ratio

    # Define vertices (skeleton points)
    vertices = [
        # Spine (0-4)
        [0, 0, 0],                              # 0: Hips center
        [0, 0, torso_height * 0.4],             # 1: Lower spine
        [0, 0, torso_height * 0.7],             # 2: Mid spine
        [0, 0, torso_height],                   # 3: Upper spine/shoulders
        [0, 0, torso_height + head_size * 0.3], # 4: Neck
        [0, 0, torso_height + head_size],       # 5: Head top

        # Left arm (6-9)
        [0.15, 0, torso_height],                # 6: L shoulder
        [0.35, 0, torso_height - 0.1],          # 7: L elbow
        [0.5, 0, torso_height - 0.2],           # 8: L wrist
        [0.55, 0, torso_height - 0.25],         # 9: L hand

        # Right arm (10-13)
        [-0.15, 0, torso_height],               # 10: R shoulder
        [-0.35, 0, torso_height - 0.1],         # 11: R elbow
        [-0.5, 0, torso_height - 0.2],          # 12: R wrist
        [-0.55, 0, torso_height - 0.25],        # 13: R hand

        # Left leg (14-17)
        [0.1, 0, 0],                            # 14: L hip
        [0.1, 0, -leg_height * 0.5],            # 15: L knee
        [0.1, 0, -leg_height],                  # 16: L ankle
        [0.1, 0.08, -leg_height],               # 17: L toe

        # Right leg (18-21)
        [-0.1, 0, 0],                           # 18: R hip
        [-0.1, 0, -leg_height * 0.5],           # 19: R knee
        [-0.1, 0, -leg_height],                 # 20: R ankle
        [-0.1, 0.08, -leg_height],              # 21: R toe
    ]

    # Scale vertices by height factor
    scale = height / 1.8
    vertices = [[v[0] * scale, v[1] * scale, v[2] * scale] for v in vertices]

    # Define edges (connections)
    edges = [
        # Spine
        [0, 1], [1, 2], [2, 3], [3, 4], [4, 5],
        # Left arm
        [3, 6], [6, 7], [7, 8], [8, 9],
        # Right arm
        [3, 10], [10, 11], [11, 12], [12, 13],
        # Left leg
        [0, 14], [14, 15], [15, 16], [16, 17],
        # Right leg
        [0, 18], [18, 19], [19, 20], [20, 21],
    ]

    # Create the skin mesh
    result = create_skin_mesh({
        "name": name,
        "vertices": vertices,
        "edges": edges,
        "root_vertex": 0,
        "default_radius": 0.05 * scale,
        "subdivision_levels": 2,
    })

    # Define radius for each body part
    radii = [
        {"index": 0, "radius": [0.12 * scale, 0.08 * scale]},   # Hips
        {"index": 1, "radius": [0.1 * scale, 0.06 * scale]},    # Lower spine
        {"index": 2, "radius": [0.11 * scale, 0.07 * scale]},   # Mid spine
        {"index": 3, "radius": [0.13 * scale, 0.08 * scale]},   # Shoulders
        {"index": 4, "radius": [0.04 * scale, 0.04 * scale]},   # Neck
        {"index": 5, "radius": [0.1 * scale, 0.11 * scale]},    # Head

        # Arms (get thinner toward hands)
        {"index": 6, "radius": 0.045 * scale},
        {"index": 7, "radius": 0.035 * scale},
        {"index": 8, "radius": 0.025 * scale},
        {"index": 9, "radius": 0.03 * scale},   # Hand slightly wider

        {"index": 10, "radius": 0.045 * scale},
        {"index": 11, "radius": 0.035 * scale},
        {"index": 12, "radius": 0.025 * scale},
        {"index": 13, "radius": 0.03 * scale},

        # Legs (get thinner toward feet)
        {"index": 14, "radius": [0.08 * scale, 0.06 * scale]},
        {"index": 15, "radius": 0.05 * scale},
        {"index": 16, "radius": 0.035 * scale},
        {"index": 17, "radius": [0.04 * scale, 0.02 * scale]},  # Foot

        {"index": 18, "radius": [0.08 * scale, 0.06 * scale]},
        {"index": 19, "radius": 0.05 * scale},
        {"index": 20, "radius": 0.035 * scale},
        {"index": 21, "radius": [0.04 * scale, 0.02 * scale]},
    ]

    # Apply radii
    set_skin_radius({
        "name": name,
        "vertices": radii,
    })

    return {
        "name": name,
        "style": style,
        "height": height,
        "vertex_count": len(vertices),
        "message": "Humanoid skeleton created. Use apply_skin_modifier to convert to mesh.",
    }


def create_limb_skeleton(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a limb (arm or leg) skeleton structure.

    params:
        name: mesh name
        type: 'arm' or 'leg'
        length: total length
        segments: number of segments (default 3)
        start_position: [x, y, z] starting position
        direction: [x, y, z] direction vector
    """
    name = params["name"]
    limb_type = params.get("type", "arm").lower()
    length = params.get("length", 0.6)
    segments = params.get("segments", 3)
    start = params.get("start_position", [0, 0, 0])
    direction = params.get("direction", [1, 0, 0])

    # Normalize direction
    dir_vec = Vector(direction).normalized()

    # Create vertices along the limb
    vertices = []
    segment_length = length / segments

    for i in range(segments + 1):
        pos = Vector(start) + dir_vec * (i * segment_length)
        vertices.append(list(pos))

    # Create edges
    edges = [[i, i+1] for i in range(segments)]

    # Define radii (taper toward end)
    if limb_type == "arm":
        start_radius = 0.045
        end_radius = 0.025
    else:  # leg
        start_radius = 0.07
        end_radius = 0.035

    result = create_skin_mesh({
        "name": name,
        "vertices": vertices,
        "edges": edges,
        "root_vertex": 0,
        "default_radius": start_radius,
    })

    # Set tapered radii
    radii = []
    for i in range(segments + 1):
        t = i / segments
        radius = start_radius + t * (end_radius - start_radius)
        radii.append({"index": i, "radius": radius})

    set_skin_radius({"name": name, "vertices": radii})

    return result


SKINNING_HANDLERS = {
    "create_armature": create_armature,
    "add_bone": add_bone,
    "create_skin_mesh": create_skin_mesh,
    "set_skin_radius": set_skin_radius,
    "set_skin_root": set_skin_root,
    "mark_skin_loose": mark_skin_loose,
    "apply_skin_modifier": apply_skin_modifier,
    "create_humanoid_skeleton": create_humanoid_skeleton,
    "create_limb_skeleton": create_limb_skeleton,
}

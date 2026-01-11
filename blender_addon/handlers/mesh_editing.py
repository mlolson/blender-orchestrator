"""Handlers for mesh editing operations."""

import bpy
from typing import Any, Dict, List
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
    mod.solver = "FAST"

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


MESH_EDITING_HANDLERS = {
    "extrude_faces": extrude_faces,
    "bevel_edges": bevel_edges,
    "boolean_operation": boolean_operation,
    "subdivide_mesh": subdivide_mesh,
    "add_subdivision_surface": add_subdivision_surface,
    "inset_faces": inset_faces,
    "smooth_mesh": smooth_mesh,
}

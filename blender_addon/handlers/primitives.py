"""Handlers for primitive mesh creation."""

import bpy
from typing import Any, Dict
from ..utils.serializers import serialize_object


def create_cube(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a cube primitive."""
    size = params.get("size", 2.0)
    location = tuple(params.get("location", [0, 0, 0]))
    name = params.get("name")

    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object

    if name:
        obj.name = name

    return serialize_object(obj)


def create_sphere(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a UV sphere primitive."""
    radius = params.get("radius", 1.0)
    segments = params.get("segments", 32)
    rings = params.get("rings", 16)
    location = tuple(params.get("location", [0, 0, 0]))
    name = params.get("name")

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=segments,
        ring_count=rings,
        location=location,
    )
    obj = bpy.context.active_object

    if name:
        obj.name = name

    return serialize_object(obj)


def create_cylinder(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a cylinder primitive."""
    radius = params.get("radius", 1.0)
    depth = params.get("depth", 2.0)
    vertices = params.get("vertices", 32)
    location = tuple(params.get("location", [0, 0, 0]))
    name = params.get("name")

    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=depth,
        vertices=vertices,
        location=location,
    )
    obj = bpy.context.active_object

    if name:
        obj.name = name

    return serialize_object(obj)


def create_cone(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a cone primitive."""
    radius1 = params.get("radius1", 1.0)  # Bottom radius
    radius2 = params.get("radius2", 0.0)  # Top radius
    depth = params.get("depth", 2.0)
    vertices = params.get("vertices", 32)
    location = tuple(params.get("location", [0, 0, 0]))
    name = params.get("name")

    bpy.ops.mesh.primitive_cone_add(
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        vertices=vertices,
        location=location,
    )
    obj = bpy.context.active_object

    if name:
        obj.name = name

    return serialize_object(obj)


def create_torus(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a torus primitive."""
    major_radius = params.get("major_radius", 1.0)
    minor_radius = params.get("minor_radius", 0.25)
    major_segments = params.get("major_segments", 48)
    minor_segments = params.get("minor_segments", 12)
    location = tuple(params.get("location", [0, 0, 0]))
    name = params.get("name")

    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=location,
    )
    obj = bpy.context.active_object

    if name:
        obj.name = name

    return serialize_object(obj)


def create_plane(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a plane primitive."""
    size = params.get("size", 2.0)
    location = tuple(params.get("location", [0, 0, 0]))
    name = params.get("name")

    bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    obj = bpy.context.active_object

    if name:
        obj.name = name

    return serialize_object(obj)


# Handler registry for primitives
PRIMITIVE_HANDLERS = {
    "create_cube": create_cube,
    "create_sphere": create_sphere,
    "create_cylinder": create_cylinder,
    "create_cone": create_cone,
    "create_torus": create_torus,
    "create_plane": create_plane,
}

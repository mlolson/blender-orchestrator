"""Handlers for object transformations."""

import bpy
import math
from typing import Any, Dict, Union
from ..utils.serializers import serialize_object


def get_object(name: str) -> bpy.types.Object:
    """Get object by name, raise if not found."""
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    return obj


def move_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Move an object to a new location or by an offset."""
    name = params["name"]
    obj = get_object(name)

    if "location" in params:
        obj.location = tuple(params["location"])
    elif "offset" in params:
        offset = params["offset"]
        obj.location.x += offset[0]
        obj.location.y += offset[1]
        obj.location.z += offset[2]

    return serialize_object(obj)


def rotate_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Rotate an object (angles in degrees)."""
    name = params["name"]
    obj = get_object(name)

    if "rotation" in params:
        # Rotation in degrees, convert to radians
        rotation = params["rotation"]
        obj.rotation_euler = (
            math.radians(rotation[0]),
            math.radians(rotation[1]),
            math.radians(rotation[2]),
        )
    elif "rotation_offset" in params:
        offset = params["rotation_offset"]
        obj.rotation_euler.x += math.radians(offset[0])
        obj.rotation_euler.y += math.radians(offset[1])
        obj.rotation_euler.z += math.radians(offset[2])

    return serialize_object(obj)


def scale_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Scale an object."""
    name = params["name"]
    obj = get_object(name)

    if "scale" in params:
        scale = params["scale"]
        if isinstance(scale, (int, float)):
            obj.scale = (scale, scale, scale)
        else:
            obj.scale = tuple(scale)
    elif "scale_factor" in params:
        factor = params["scale_factor"]
        if isinstance(factor, (int, float)):
            obj.scale.x *= factor
            obj.scale.y *= factor
            obj.scale.z *= factor
        else:
            obj.scale.x *= factor[0]
            obj.scale.y *= factor[1]
            obj.scale.z *= factor[2]

    return serialize_object(obj)


def duplicate_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Duplicate an object."""
    name = params["name"]
    obj = get_object(name)
    new_name = params.get("new_name")
    linked = params.get("linked", False)

    # Select only this object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Duplicate
    bpy.ops.object.duplicate(linked=linked)
    new_obj = bpy.context.active_object

    if new_name:
        new_obj.name = new_name

    # Apply offset if provided
    if "offset" in params:
        offset = params["offset"]
        new_obj.location.x += offset[0]
        new_obj.location.y += offset[1]
        new_obj.location.z += offset[2]

    return serialize_object(new_obj)


def delete_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete an object."""
    name = params["name"]
    obj = get_object(name)

    # Store name before deletion
    deleted_name = obj.name

    # Select and delete
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.delete()

    return {"deleted": deleted_name}


def set_origin(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set the origin of an object."""
    name = params["name"]
    origin_type = params.get("type", "ORIGIN_CENTER_OF_MASS")
    # Valid types: ORIGIN_GEOMETRY, ORIGIN_CENTER_OF_MASS, ORIGIN_CENTER_OF_VOLUME, ORIGIN_CURSOR

    obj = get_object(name)

    # Select only this object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.origin_set(type=origin_type)

    return serialize_object(obj)


TRANSFORM_HANDLERS = {
    "move_object": move_object,
    "rotate_object": rotate_object,
    "scale_object": scale_object,
    "duplicate_object": duplicate_object,
    "delete_object": delete_object,
    "set_origin": set_origin,
}

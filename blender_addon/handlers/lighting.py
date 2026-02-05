"""Handlers for light creation and manipulation."""

import bpy
import math
from typing import Any, Dict
from ..utils.serializers import serialize_object


def create_point_light(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a point light (omnidirectional light source)."""
    location = tuple(params.get("location", [0, 0, 3]))
    name = params.get("name")
    energy = params.get("energy", 1000.0)  # Watts
    color = params.get("color", [1.0, 1.0, 1.0])
    radius = params.get("radius", 0.25)  # Soft shadow radius

    bpy.ops.object.light_add(type="POINT", location=location)
    obj = bpy.context.active_object
    light = obj.data

    light.energy = energy
    light.color = tuple(color[:3])
    light.shadow_soft_size = radius

    if name:
        obj.name = name
        light.name = name

    result = serialize_object(obj)
    result["light"] = {
        "type": "POINT",
        "energy": light.energy,
        "color": list(light.color),
        "radius": light.shadow_soft_size,
    }
    return result


def create_sun_light(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a sun light (directional light for outdoor scenes)."""
    location = tuple(params.get("location", [0, 0, 10]))
    rotation = params.get("rotation", [45, 0, 45])  # Degrees
    name = params.get("name")
    energy = params.get("energy", 5.0)  # Sun uses different scale
    color = params.get("color", [1.0, 1.0, 1.0])
    angle = params.get("angle", 0.526)  # Angular diameter in radians (~30 degrees)

    # Convert rotation from degrees to radians
    rotation_rad = tuple(math.radians(r) for r in rotation)

    bpy.ops.object.light_add(type="SUN", location=location, rotation=rotation_rad)
    obj = bpy.context.active_object
    light = obj.data

    light.energy = energy
    light.color = tuple(color[:3])
    light.angle = angle

    if name:
        obj.name = name
        light.name = name

    result = serialize_object(obj)
    result["light"] = {
        "type": "SUN",
        "energy": light.energy,
        "color": list(light.color),
        "angle": light.angle,
    }
    return result


def create_spot_light(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a spot light (cone-shaped light for focused lighting)."""
    location = tuple(params.get("location", [0, 0, 5]))
    rotation = params.get("rotation", [0, 0, 0])  # Degrees
    name = params.get("name")
    energy = params.get("energy", 1000.0)  # Watts
    color = params.get("color", [1.0, 1.0, 1.0])
    spot_size = params.get("spot_size", 45.0)  # Cone angle in degrees
    spot_blend = params.get("spot_blend", 0.15)  # Edge softness (0-1)
    radius = params.get("radius", 0.25)  # Soft shadow radius

    # Convert rotation from degrees to radians
    rotation_rad = tuple(math.radians(r) for r in rotation)

    bpy.ops.object.light_add(type="SPOT", location=location, rotation=rotation_rad)
    obj = bpy.context.active_object
    light = obj.data

    light.energy = energy
    light.color = tuple(color[:3])
    light.spot_size = math.radians(spot_size)
    light.spot_blend = spot_blend
    light.shadow_soft_size = radius

    if name:
        obj.name = name
        light.name = name

    result = serialize_object(obj)
    result["light"] = {
        "type": "SPOT",
        "energy": light.energy,
        "color": list(light.color),
        "spot_size_degrees": spot_size,
        "spot_blend": light.spot_blend,
        "radius": light.shadow_soft_size,
    }
    return result


def create_area_light(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an area light (rectangular or disk-shaped soft light)."""
    location = tuple(params.get("location", [0, 0, 3]))
    rotation = params.get("rotation", [0, 0, 0])  # Degrees
    name = params.get("name")
    energy = params.get("energy", 1000.0)  # Watts
    color = params.get("color", [1.0, 1.0, 1.0])
    shape = params.get("shape", "RECTANGLE")  # SQUARE, RECTANGLE, DISK, ELLIPSE
    size = params.get("size", 1.0)  # Primary size
    size_y = params.get("size_y")  # Secondary size for RECTANGLE/ELLIPSE

    # Convert rotation from degrees to radians
    rotation_rad = tuple(math.radians(r) for r in rotation)

    bpy.ops.object.light_add(type="AREA", location=location, rotation=rotation_rad)
    obj = bpy.context.active_object
    light = obj.data

    light.energy = energy
    light.color = tuple(color[:3])
    light.shape = shape
    light.size = size
    if size_y is not None and shape in ("RECTANGLE", "ELLIPSE"):
        light.size_y = size_y

    if name:
        obj.name = name
        light.name = name

    result = serialize_object(obj)
    result["light"] = {
        "type": "AREA",
        "energy": light.energy,
        "color": list(light.color),
        "shape": light.shape,
        "size": light.size,
        "size_y": getattr(light, "size_y", None),
    }
    return result


def set_light_properties(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify properties of an existing light."""
    name = params.get("name")
    obj = bpy.data.objects.get(name)

    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != "LIGHT":
        raise ValueError(f"Object '{name}' is not a light (type: {obj.type})")

    light = obj.data

    if "energy" in params:
        light.energy = params["energy"]
    if "color" in params:
        light.color = tuple(params["color"][:3])

    # Type-specific properties
    if light.type == "POINT":
        if "radius" in params:
            light.shadow_soft_size = params["radius"]
    elif light.type == "SUN":
        if "angle" in params:
            light.angle = params["angle"]
    elif light.type == "SPOT":
        if "spot_size" in params:
            light.spot_size = math.radians(params["spot_size"])
        if "spot_blend" in params:
            light.spot_blend = params["spot_blend"]
        if "radius" in params:
            light.shadow_soft_size = params["radius"]
    elif light.type == "AREA":
        if "shape" in params:
            light.shape = params["shape"]
        if "size" in params:
            light.size = params["size"]
        if "size_y" in params:
            light.size_y = params["size_y"]

    result = serialize_object(obj)
    result["light"] = {
        "type": light.type,
        "energy": light.energy,
        "color": list(light.color),
    }
    return result


def get_light_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information about a light."""
    name = params.get("name")
    obj = bpy.data.objects.get(name)

    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != "LIGHT":
        raise ValueError(f"Object '{name}' is not a light (type: {obj.type})")

    light = obj.data
    result = serialize_object(obj)

    light_info = {
        "type": light.type,
        "energy": light.energy,
        "color": list(light.color),
        "use_shadow": light.use_shadow,
    }

    if light.type == "POINT":
        light_info["radius"] = light.shadow_soft_size
    elif light.type == "SUN":
        light_info["angle"] = light.angle
        light_info["angle_degrees"] = math.degrees(light.angle)
    elif light.type == "SPOT":
        light_info["spot_size"] = light.spot_size
        light_info["spot_size_degrees"] = math.degrees(light.spot_size)
        light_info["spot_blend"] = light.spot_blend
        light_info["radius"] = light.shadow_soft_size
    elif light.type == "AREA":
        light_info["shape"] = light.shape
        light_info["size"] = light.size
        if light.shape in ("RECTANGLE", "ELLIPSE"):
            light_info["size_y"] = light.size_y

    result["light"] = light_info
    return result


def list_lights(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all lights in the scene."""
    type_filter = params.get("type")

    lights = []
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT":
            if type_filter and obj.data.type != type_filter:
                continue
            light = obj.data
            lights.append({
                "name": obj.name,
                "type": light.type,
                "location": list(obj.location),
                "energy": light.energy,
                "color": list(light.color),
                "visible": not obj.hide_viewport,
            })

    return {
        "lights": lights,
        "count": len(lights),
    }


# Handler registry for lighting
LIGHTING_HANDLERS = {
    "create_point_light": create_point_light,
    "create_sun_light": create_sun_light,
    "create_spot_light": create_spot_light,
    "create_area_light": create_area_light,
    "set_light_properties": set_light_properties,
    "get_light_info": get_light_info,
    "list_lights": list_lights,
}

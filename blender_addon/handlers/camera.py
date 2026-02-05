"""Handlers for camera creation and manipulation."""

import bpy
import math
from typing import Any, Dict
from mathutils import Vector
from ..utils.serializers import serialize_object


def create_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a camera in the scene."""
    location = tuple(params.get("location", [0, -10, 5]))
    rotation = params.get("rotation", [60, 0, 0])  # Degrees - default looks at origin
    name = params.get("name")
    lens = params.get("lens", 50.0)  # Focal length in mm
    sensor_width = params.get("sensor_width", 36.0)  # mm
    clip_start = params.get("clip_start", 0.1)
    clip_end = params.get("clip_end", 1000.0)
    camera_type = params.get("type", "PERSP")  # PERSP, ORTHO, PANO

    # Convert rotation from degrees to radians
    rotation_rad = tuple(math.radians(r) for r in rotation)

    bpy.ops.object.camera_add(location=location, rotation=rotation_rad)
    obj = bpy.context.active_object
    camera = obj.data

    camera.lens = lens
    camera.sensor_width = sensor_width
    camera.clip_start = clip_start
    camera.clip_end = clip_end
    camera.type = camera_type

    if name:
        obj.name = name
        camera.name = name

    result = serialize_object(obj)
    result["camera"] = {
        "type": camera.type,
        "lens": camera.lens,
        "sensor_width": camera.sensor_width,
        "clip_start": camera.clip_start,
        "clip_end": camera.clip_end,
    }
    return result


def set_active_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set a camera as the active scene camera."""
    name = params.get("name")
    obj = bpy.data.objects.get(name)

    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != "CAMERA":
        raise ValueError(f"Object '{name}' is not a camera (type: {obj.type})")

    bpy.context.scene.camera = obj

    result = serialize_object(obj)
    result["is_active"] = True
    return result


def look_at(params: Dict[str, Any]) -> Dict[str, Any]:
    """Point a camera (or any object) at a target location or object."""
    name = params.get("name")
    target = params.get("target")  # Can be object name or [x, y, z]
    
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    # Determine target location
    if isinstance(target, str):
        target_obj = bpy.data.objects.get(target)
        if not target_obj:
            raise ValueError(f"Target object '{target}' not found")
        target_loc = target_obj.location
    elif isinstance(target, (list, tuple)) and len(target) == 3:
        target_loc = Vector(target)
    else:
        raise ValueError("Target must be an object name or [x, y, z] coordinates")

    # Calculate direction and rotation
    direction = target_loc - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

    result = serialize_object(obj)
    result["looking_at"] = list(target_loc)
    return result


def set_camera_properties(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify properties of an existing camera."""
    name = params.get("name")
    obj = bpy.data.objects.get(name)

    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != "CAMERA":
        raise ValueError(f"Object '{name}' is not a camera (type: {obj.type})")

    camera = obj.data

    if "lens" in params:
        camera.lens = params["lens"]
    if "sensor_width" in params:
        camera.sensor_width = params["sensor_width"]
    if "clip_start" in params:
        camera.clip_start = params["clip_start"]
    if "clip_end" in params:
        camera.clip_end = params["clip_end"]
    if "type" in params:
        camera.type = params["type"]
    if "ortho_scale" in params and camera.type == "ORTHO":
        camera.ortho_scale = params["ortho_scale"]
    if "dof_enabled" in params:
        camera.dof.use_dof = params["dof_enabled"]
    if "dof_focus_distance" in params:
        camera.dof.focus_distance = params["dof_focus_distance"]
    if "dof_aperture" in params:
        camera.dof.aperture_fstop = params["dof_aperture"]

    result = serialize_object(obj)
    result["camera"] = {
        "type": camera.type,
        "lens": camera.lens,
        "sensor_width": camera.sensor_width,
        "clip_start": camera.clip_start,
        "clip_end": camera.clip_end,
        "dof_enabled": camera.dof.use_dof,
    }
    return result


def get_camera_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information about a camera."""
    name = params.get("name")
    obj = bpy.data.objects.get(name)

    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != "CAMERA":
        raise ValueError(f"Object '{name}' is not a camera (type: {obj.type})")

    camera = obj.data
    result = serialize_object(obj)

    camera_info = {
        "type": camera.type,
        "lens": camera.lens,
        "sensor_width": camera.sensor_width,
        "sensor_height": camera.sensor_height,
        "clip_start": camera.clip_start,
        "clip_end": camera.clip_end,
        "is_active": bpy.context.scene.camera == obj,
    }

    if camera.type == "ORTHO":
        camera_info["ortho_scale"] = camera.ortho_scale

    # Depth of field
    camera_info["dof"] = {
        "enabled": camera.dof.use_dof,
        "focus_distance": camera.dof.focus_distance,
        "aperture_fstop": camera.dof.aperture_fstop,
    }
    if camera.dof.focus_object:
        camera_info["dof"]["focus_object"] = camera.dof.focus_object.name

    result["camera"] = camera_info
    return result


def list_cameras(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all cameras in the scene."""
    cameras = []
    active_camera = bpy.context.scene.camera

    for obj in bpy.context.scene.objects:
        if obj.type == "CAMERA":
            camera = obj.data
            cameras.append({
                "name": obj.name,
                "location": list(obj.location),
                "type": camera.type,
                "lens": camera.lens,
                "is_active": obj == active_camera,
                "visible": not obj.hide_viewport,
            })

    return {
        "cameras": cameras,
        "count": len(cameras),
        "active": active_camera.name if active_camera else None,
    }


def frame_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """Position camera to frame specified objects or the entire scene."""
    camera_name = params.get("camera")
    object_names = params.get("objects")  # List of object names, or None for all
    padding = params.get("padding", 1.2)  # Multiplier for distance

    # Get camera
    if camera_name:
        camera_obj = bpy.data.objects.get(camera_name)
        if not camera_obj or camera_obj.type != "CAMERA":
            raise ValueError(f"Camera '{camera_name}' not found")
    else:
        camera_obj = bpy.context.scene.camera
        if not camera_obj:
            raise ValueError("No active camera in scene")

    # Get objects to frame
    if object_names:
        objects = [bpy.data.objects.get(n) for n in object_names]
        objects = [o for o in objects if o is not None]
        if not objects:
            raise ValueError("No valid objects found to frame")
    else:
        objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        if not objects:
            raise ValueError("No mesh objects in scene to frame")

    # Calculate bounding box center and size
    min_co = Vector((float("inf"), float("inf"), float("inf")))
    max_co = Vector((float("-inf"), float("-inf"), float("-inf")))

    for obj in objects:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_co.x = min(min_co.x, world_corner.x)
            min_co.y = min(min_co.y, world_corner.y)
            min_co.z = min(min_co.z, world_corner.z)
            max_co.x = max(max_co.x, world_corner.x)
            max_co.y = max(max_co.y, world_corner.y)
            max_co.z = max(max_co.z, world_corner.z)

    center = (min_co + max_co) / 2
    size = max_co - min_co
    max_dim = max(size.x, size.y, size.z)

    # Calculate camera distance based on focal length
    camera = camera_obj.data
    fov = 2 * math.atan(camera.sensor_width / (2 * camera.lens))
    distance = (max_dim * padding) / (2 * math.tan(fov / 2))

    # Position camera
    # Default: position camera along -Y axis looking at center
    camera_obj.location = Vector((center.x, center.y - distance, center.z + max_dim * 0.3))

    # Point at center
    direction = center - camera_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera_obj.rotation_euler = rot_quat.to_euler()

    result = serialize_object(camera_obj)
    result["framed"] = {
        "objects": [o.name for o in objects],
        "center": list(center),
        "distance": distance,
    }
    return result


# Handler registry for cameras
CAMERA_HANDLERS = {
    "create_camera": create_camera,
    "set_active_camera": set_active_camera,
    "look_at": look_at,
    "set_camera_properties": set_camera_properties,
    "get_camera_info": get_camera_info,
    "list_cameras": list_cameras,
    "frame_objects": frame_objects,
}

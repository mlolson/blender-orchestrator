"""Serialization utilities for Blender objects."""

import bpy
import math
from typing import Any, Dict


def serialize_object(obj: bpy.types.Object, detailed: bool = False) -> Dict[str, Any]:
    """Serialize a Blender object to a dictionary.

    Args:
        obj: The Blender object to serialize.
        detailed: If True, include additional details like mesh info, materials, etc.

    Returns:
        Dictionary representation of the object.
    """
    data = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": [math.degrees(r) for r in obj.rotation_euler],
        "scale": list(obj.scale),
        "visible": obj.visible_get(),
    }

    if detailed:
        # Add mesh data if applicable
        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            data["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons),
            }

        # Add material info
        data["materials"] = [
            slot.material.name if slot.material else None
            for slot in obj.material_slots
        ]

        # Add modifier info
        data["modifiers"] = [
            {"name": mod.name, "type": mod.type} for mod in obj.modifiers
        ]

        # Add parent info
        data["parent"] = obj.parent.name if obj.parent else None

        # Add children
        data["children"] = [child.name for child in obj.children]

        # Add bounding box
        if obj.type == "MESH":
            bbox = [list(v) for v in obj.bound_box]
            data["bounding_box"] = bbox

    return data


def serialize_material(mat: bpy.types.Material) -> Dict[str, Any]:
    """Serialize a Blender material to a dictionary."""
    data = {"name": mat.name, "use_nodes": mat.use_nodes}

    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            data["color"] = list(bsdf.inputs["Base Color"].default_value)
            data["metallic"] = bsdf.inputs["Metallic"].default_value
            data["roughness"] = bsdf.inputs["Roughness"].default_value

    return data


def serialize_scene_summary(scene: bpy.types.Scene) -> Dict[str, Any]:
    """Serialize a scene summary."""
    # Count objects by type
    type_counts: Dict[str, int] = {}
    for obj in bpy.data.objects:
        obj_type = obj.type
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

    # Get camera info
    camera_info = None
    if scene.camera:
        camera_info = {
            "name": scene.camera.name,
            "location": list(scene.camera.location),
        }

    # Get render settings
    render_info = {
        "engine": scene.render.engine,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "fps": scene.render.fps,
    }

    return {
        "scene_name": scene.name,
        "object_counts": type_counts,
        "total_objects": len(bpy.data.objects),
        "camera": camera_info,
        "render_settings": render_info,
        "material_count": len(bpy.data.materials),
        "frame_current": scene.frame_current,
        "frame_range": [scene.frame_start, scene.frame_end],
    }

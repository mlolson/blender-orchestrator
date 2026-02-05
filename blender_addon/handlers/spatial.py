"""Handlers for spatial reasoning operations."""

import bpy
import mathutils
from typing import Any, Dict, List, Optional, Tuple
from ..utils.serializers import serialize_object
import math


def _get_object_bounds(obj) -> Tuple[mathutils.Vector, mathutils.Vector]:
    """Get world-space bounding box min/max for an object."""
    if obj.type == 'MESH' and obj.data:
        # Get world-space bounding box corners
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
        # For non-mesh objects, use location with small bounds
        loc = obj.matrix_world.translation
        offset = mathutils.Vector((0.1, 0.1, 0.1))
        return loc - offset, loc + offset


def _get_object_size_category(obj) -> str:
    """Categorize object size as tiny/small/medium/large/huge."""
    min_b, max_b = _get_object_bounds(obj)
    dims = max_b - min_b
    max_dim = max(dims.x, dims.y, dims.z)
    
    if max_dim < 0.1:
        return "tiny"
    elif max_dim < 0.5:
        return "small"
    elif max_dim < 2.0:
        return "medium"
    elif max_dim < 5.0:
        return "large"
    else:
        return "huge"


def _get_position_description(location: mathutils.Vector, scene_bounds: Tuple[mathutils.Vector, mathutils.Vector]) -> str:
    """Describe position in human-readable terms relative to scene."""
    min_b, max_b = scene_bounds
    center = (min_b + max_b) / 2
    size = max_b - min_b
    
    # Avoid division by zero
    if size.x < 0.01: size.x = 1.0
    if size.y < 0.01: size.y = 1.0
    if size.z < 0.01: size.z = 1.0
    
    # Normalize position to -1 to 1 range
    rel = mathutils.Vector((
        (location.x - center.x) / (size.x / 2),
        (location.y - center.y) / (size.y / 2),
        (location.z - center.z) / (size.z / 2)
    ))
    
    parts = []
    
    # Height description
    if location.z < 0.1:
        parts.append("on floor")
    elif rel.z > 0.5:
        parts.append("high up")
    elif rel.z < -0.3:
        parts.append("low")
    
    # Horizontal position
    h_parts = []
    if rel.x > 0.3:
        h_parts.append("right")
    elif rel.x < -0.3:
        h_parts.append("left")
    
    if rel.y > 0.3:
        h_parts.append("back")
    elif rel.y < -0.3:
        h_parts.append("front")
    
    if h_parts:
        parts.append("-".join(h_parts))
    elif not parts:
        parts.append("center")
    
    return ", ".join(parts)


def _get_facing_direction(obj) -> str:
    """Get the direction an object is facing based on its rotation."""
    # Get the forward vector (local -Y in Blender convention)
    forward = obj.matrix_world.to_quaternion() @ mathutils.Vector((0, -1, 0))
    
    # Determine primary direction
    abs_x, abs_y = abs(forward.x), abs(forward.y)
    
    if abs_x > abs_y:
        return "+X (right)" if forward.x > 0 else "-X (left)"
    else:
        return "+Y (back)" if forward.y > 0 else "-Y (front)"


def _calculate_distance(obj1, obj2) -> float:
    """Calculate distance between two object centers."""
    return (obj1.matrix_world.translation - obj2.matrix_world.translation).length


def _get_scene_bounds(objects: List) -> Tuple[mathutils.Vector, mathutils.Vector]:
    """Calculate the bounding box of all objects in the scene."""
    if not objects:
        return mathutils.Vector((0, 0, 0)), mathutils.Vector((1, 1, 1))
    
    all_min = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    all_max = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in objects:
        min_b, max_b = _get_object_bounds(obj)
        all_min.x = min(all_min.x, min_b.x)
        all_min.y = min(all_min.y, min_b.y)
        all_min.z = min(all_min.z, min_b.z)
        all_max.x = max(all_max.x, max_b.x)
        all_max.y = max(all_max.y, max_b.y)
        all_max.z = max(all_max.z, max_b.z)
    
    return all_min, all_max


def _get_object_type_category(obj) -> str:
    """Get a semantic category for the object type."""
    type_map = {
        'MESH': 'object',
        'CAMERA': 'camera',
        'LIGHT': 'lighting',
        'EMPTY': 'helper',
        'ARMATURE': 'rig',
        'CURVE': 'curve',
        'FONT': 'text',
        'SURFACE': 'surface',
        'META': 'metaball',
        'LATTICE': 'deformer',
        'GPENCIL': 'drawing',
        'SPEAKER': 'audio',
    }
    return type_map.get(obj.type, 'other')


def get_semantic_scene_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get an enhanced scene summary with spatial semantics."""
    scene = bpy.context.scene
    detail_level = params.get("detail_level", "standard")
    
    # Get all visible objects
    visible_objects = [obj for obj in bpy.data.objects if obj.visible_get()]
    mesh_objects = [obj for obj in visible_objects if obj.type == 'MESH']
    
    # Calculate scene bounds
    scene_bounds = _get_scene_bounds(visible_objects)
    scene_size = scene_bounds[1] - scene_bounds[0]
    
    # Determine scene scale
    max_dim = max(scene_size.x, scene_size.y, scene_size.z)
    if max_dim < 2:
        scale_desc = "small-scale (tabletop/miniature)"
    elif max_dim < 10:
        scale_desc = "room-scale"
    elif max_dim < 50:
        scale_desc = "building-scale"
    else:
        scale_desc = "large-scale (outdoor/landscape)"
    
    # Count objects by type
    type_counts = {}
    for obj in visible_objects:
        cat = _get_object_type_category(obj)
        type_counts[cat] = type_counts.get(cat, 0) + 1
    
    # Find spatial clusters (simple proximity-based grouping)
    clusters = []
    if mesh_objects and detail_level in ("standard", "detailed"):
        # Simple clustering: objects within 2m of each other
        assigned = set()
        for obj in mesh_objects:
            if obj.name in assigned:
                continue
            cluster = [obj.name]
            assigned.add(obj.name)
            for other in mesh_objects:
                if other.name not in assigned:
                    if _calculate_distance(obj, other) < 2.0:
                        cluster.append(other.name)
                        assigned.add(other.name)
            if len(cluster) > 1:
                clusters.append(cluster)
    
    # Build object details (for standard and detailed levels)
    objects_info = []
    if detail_level in ("standard", "detailed"):
        for obj in mesh_objects[:20]:  # Limit to 20 objects to avoid huge responses
            obj_info = {
                "name": obj.name,
                "type": obj.type,
                "size_category": _get_object_size_category(obj),
                "position_description": _get_position_description(
                    obj.matrix_world.translation, scene_bounds
                ),
                "position_exact": list(obj.matrix_world.translation),
            }
            
            if detail_level == "detailed":
                obj_info["facing"] = _get_facing_direction(obj)
                obj_info["dimensions"] = list(obj.dimensions)
                
                # Find 3 nearest neighbors
                distances = []
                for other in mesh_objects:
                    if other.name != obj.name:
                        dist = _calculate_distance(obj, other)
                        distances.append((other.name, round(dist, 2)))
                distances.sort(key=lambda x: x[1])
                obj_info["nearby_objects"] = distances[:3]
            
            objects_info.append(obj_info)
    
    # Get camera info
    camera_info = None
    if scene.camera:
        cam = scene.camera
        cam_forward = cam.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1))
        camera_info = {
            "name": cam.name,
            "position": list(cam.matrix_world.translation),
            "looking_toward": f"({cam_forward.x:.2f}, {cam_forward.y:.2f}, {cam_forward.z:.2f})",
        }
    
    # Build natural language summary
    obj_types_str = ", ".join(f"{v} {k}{'s' if v > 1 else ''}" for k, v in type_counts.items())
    summary = f"Scene with {len(visible_objects)} visible objects ({obj_types_str}). "
    summary += f"Scene scale: {scale_desc}. "
    summary += f"Bounds: {scene_size.x:.1f}m × {scene_size.y:.1f}m × {scene_size.z:.1f}m. "
    
    if clusters:
        summary += f"Found {len(clusters)} object clusters. "
    
    if camera_info:
        summary += f"Camera '{camera_info['name']}' is active."
    
    return {
        "summary": summary,
        "scene_name": scene.name,
        "total_objects": len(visible_objects),
        "mesh_objects": len(mesh_objects),
        "object_counts_by_category": type_counts,
        "bounds": {
            "min": list(scene_bounds[0]),
            "max": list(scene_bounds[1]),
            "size": list(scene_size),
        },
        "scale_description": scale_desc,
        "clusters": clusters,
        "objects": objects_info,
        "camera": camera_info,
        "coordinate_system": "Blender: X=right, Y=back, Z=up",
    }


def get_spatial_relationships(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get spatial relationships for a specific object."""
    name = params["name"]
    max_distance = params.get("max_distance", 5.0)
    
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    obj_loc = obj.matrix_world.translation
    obj_min, obj_max = _get_object_bounds(obj)
    
    relationships = []
    
    for other in bpy.data.objects:
        if other.name == name or not other.visible_get():
            continue
        
        other_loc = other.matrix_world.translation
        distance = (obj_loc - other_loc).length
        
        if distance > max_distance:
            continue
        
        other_min, other_max = _get_object_bounds(other)
        
        # Determine spatial relationships
        rel_types = []
        
        # Check if on top of
        if obj_min.z >= other_max.z - 0.1 and obj_min.z <= other_max.z + 0.2:
            # Check horizontal overlap
            h_overlap = (obj_min.x < other_max.x and obj_max.x > other_min.x and
                        obj_min.y < other_max.y and obj_max.y > other_min.y)
            if h_overlap:
                rel_types.append("on_top_of")
        
        # Check if below
        if obj_max.z <= other_min.z + 0.1:
            rel_types.append("below")
        
        # Check if inside (bounding box containment)
        if (obj_min.x >= other_min.x and obj_max.x <= other_max.x and
            obj_min.y >= other_min.y and obj_max.y <= other_max.y and
            obj_min.z >= other_min.z and obj_max.z <= other_max.z):
            rel_types.append("inside")
        
        # Directional relationships
        diff = other_loc - obj_loc
        
        if abs(diff.x) > 0.5:
            rel_types.append("right_of" if diff.x > 0 else "left_of")
        
        if abs(diff.y) > 0.5:
            rel_types.append("behind" if diff.y > 0 else "in_front_of")
        
        # Distance category
        if distance < 0.5:
            distance_cat = "touching"
        elif distance < 1.5:
            distance_cat = "near"
        elif distance < 3.0:
            distance_cat = "medium_distance"
        else:
            distance_cat = "far"
        
        # Check if facing
        forward = obj.matrix_world.to_quaternion() @ mathutils.Vector((0, -1, 0))
        to_other = (other_loc - obj_loc).normalized()
        if forward.dot(to_other) > 0.7:
            rel_types.append("facing")
        
        if rel_types or distance < max_distance:
            relationships.append({
                "object": other.name,
                "type": other.type,
                "distance": round(distance, 2),
                "distance_category": distance_cat,
                "relationships": rel_types if rel_types else ["nearby"],
                "direction": {
                    "x": "right" if diff.x > 0.5 else "left" if diff.x < -0.5 else "aligned",
                    "y": "behind" if diff.y > 0.5 else "front" if diff.y < -0.5 else "aligned",
                    "z": "above" if diff.z > 0.5 else "below" if diff.z < -0.5 else "same_level",
                }
            })
    
    # Sort by distance
    relationships.sort(key=lambda x: x["distance"])
    
    return {
        "object": name,
        "position": list(obj_loc),
        "size_category": _get_object_size_category(obj),
        "facing_direction": _get_facing_direction(obj),
        "relationships": relationships,
        "relationship_count": len(relationships),
    }


SPATIAL_HANDLERS = {
    "get_semantic_scene_summary": get_semantic_scene_summary,
    "get_spatial_relationships": get_spatial_relationships,
}

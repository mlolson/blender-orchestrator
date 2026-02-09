"""Handlers for spatial reasoning operations."""

import bpy
import mathutils
from typing import Any, Dict, List, Optional, Tuple
from ..utils.serializers import serialize_object
import math
import re


def _get_object_bounds(obj) -> Tuple[mathutils.Vector, mathutils.Vector]:
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
    
    if size.x < 0.01: size.x = 1.0
    if size.y < 0.01: size.y = 1.0
    if size.z < 0.01: size.z = 1.0
    
    rel = mathutils.Vector((
        (location.x - center.x) / (size.x / 2),
        (location.y - center.y) / (size.y / 2),
        (location.z - center.z) / (size.z / 2)
    ))
    
    parts = []
    
    if location.z < 0.1:
        parts.append("on floor")
    elif rel.z > 0.5:
        parts.append("high up")
    elif rel.z < -0.3:
        parts.append("low")
    
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
    forward = obj.matrix_world.to_quaternion() @ mathutils.Vector((0, -1, 0))
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


def _find_object_by_name(name: str):
    """Find an object by exact or partial name match."""
    obj = bpy.data.objects.get(name)
    if obj:
        return obj
    
    name_lower = name.lower()
    for obj in bpy.data.objects:
        if name_lower in obj.name.lower():
            return obj
    
    for obj in bpy.data.objects:
        obj_words = obj.name.lower().replace("_", " ").replace(".", " ").split()
        if name_lower in obj_words:
            return obj
    
    return None


def _check_bounds_overlap(min1, max1, min2, max2) -> bool:
    """Check if two bounding boxes overlap."""
    return (min1.x < max2.x and max1.x > min2.x and
            min1.y < max2.y and max1.y > min2.y and
            min1.z < max2.z and max1.z > min2.z)


def _check_on_top_of(obj, other) -> bool:
    """Check if obj is on top of other."""
    obj_min, obj_max = _get_object_bounds(obj)
    other_min, other_max = _get_object_bounds(other)
    
    if not (obj_min.z >= other_max.z - 0.1 and obj_min.z <= other_max.z + 0.3):
        return False
    
    h_overlap = (obj_min.x < other_max.x and obj_max.x > other_min.x and
                obj_min.y < other_max.y and obj_max.y > other_min.y)
    return h_overlap


def _check_inside(obj, other) -> bool:
    """Check if obj is inside other's bounding box."""
    obj_min, obj_max = _get_object_bounds(obj)
    other_min, other_max = _get_object_bounds(other)
    
    return (obj_min.x >= other_min.x and obj_max.x <= other_max.x and
            obj_min.y >= other_min.y and obj_max.y <= other_max.y and
            obj_min.z >= other_min.z and obj_max.z <= other_max.z)


# ============================================================================
# SEMANTIC SCENE SUMMARY (from PR #4)
# ============================================================================

def get_semantic_scene_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get an enhanced scene summary with spatial semantics."""
    scene = bpy.context.scene
    detail_level = params.get("detail_level", "standard")
    
    visible_objects = [obj for obj in bpy.data.objects if obj.visible_get()]
    mesh_objects = [obj for obj in visible_objects if obj.type == 'MESH']
    
    scene_bounds = _get_scene_bounds(visible_objects)
    scene_size = scene_bounds[1] - scene_bounds[0]
    
    max_dim = max(scene_size.x, scene_size.y, scene_size.z)
    if max_dim < 2:
        scale_desc = "small-scale (tabletop/miniature)"
    elif max_dim < 10:
        scale_desc = "room-scale"
    elif max_dim < 50:
        scale_desc = "building-scale"
    else:
        scale_desc = "large-scale (outdoor/landscape)"
    
    type_counts = {}
    for obj in visible_objects:
        cat = _get_object_type_category(obj)
        type_counts[cat] = type_counts.get(cat, 0) + 1
    
    clusters = []
    if mesh_objects and detail_level in ("standard", "detailed"):
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
    
    objects_info = []
    if detail_level in ("standard", "detailed"):
        for obj in mesh_objects[:20]:
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
                
                distances = []
                for other in mesh_objects:
                    if other.name != obj.name:
                        dist = _calculate_distance(obj, other)
                        distances.append((other.name, round(dist, 2)))
                distances.sort(key=lambda x: x[1])
                obj_info["nearby_objects"] = distances[:3]
            
            objects_info.append(obj_info)
    
    camera_info = None
    if scene.camera:
        cam = scene.camera
        cam_forward = cam.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1))
        camera_info = {
            "name": cam.name,
            "position": list(cam.matrix_world.translation),
            "looking_toward": f"({cam_forward.x:.2f}, {cam_forward.y:.2f}, {cam_forward.z:.2f})",
        }
    
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
        
        rel_types = []
        
        if obj_min.z >= other_max.z - 0.1 and obj_min.z <= other_max.z + 0.2:
            h_overlap = (obj_min.x < other_max.x and obj_max.x > other_min.x and
                        obj_min.y < other_max.y and obj_max.y > other_min.y)
            if h_overlap:
                rel_types.append("on_top_of")
        
        if obj_max.z <= other_min.z + 0.1:
            rel_types.append("below")
        
        if (obj_min.x >= other_min.x and obj_max.x <= other_max.x and
            obj_min.y >= other_min.y and obj_max.y <= other_max.y and
            obj_min.z >= other_min.z and obj_max.z <= other_max.z):
            rel_types.append("inside")
        
        diff = other_loc - obj_loc
        
        if abs(diff.x) > 0.5:
            rel_types.append("right_of" if diff.x > 0 else "left_of")
        
        if abs(diff.y) > 0.5:
            rel_types.append("behind" if diff.y > 0 else "in_front_of")
        
        if distance < 0.5:
            distance_cat = "touching"
        elif distance < 1.5:
            distance_cat = "near"
        elif distance < 3.0:
            distance_cat = "medium_distance"
        else:
            distance_cat = "far"
        
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
    
    relationships.sort(key=lambda x: x["distance"])
    
    return {
        "object": name,
        "position": list(obj_loc),
        "size_category": _get_object_size_category(obj),
        "facing_direction": _get_facing_direction(obj),
        "relationships": relationships,
        "relationship_count": len(relationships),
    }


# ============================================================================
# SPATIAL QUERIES (from PR #5)
# ============================================================================

def query_spatial(params: Dict[str, Any]) -> Dict[str, Any]:
    """Answer natural language spatial queries about the scene."""
    question = params["question"].lower().strip()
    
    query_type = None
    reference_obj_name = None
    
    patterns = [
        (r"what(?:'s| is) on (?:the )?(.+?)[\?\.]?$", "on"),
        (r"what(?:'s| is) (?:to the )?left of (?:the )?(.+?)[\?\.]?$", "left_of"),
        (r"what(?:'s| is) (?:to the )?right of (?:the )?(.+?)[\?\.]?$", "right_of"),
        (r"what(?:'s| is) in front of (?:the )?(.+?)[\?\.]?$", "in_front_of"),
        (r"what(?:'s| is) behind (?:the )?(.+?)[\?\.]?$", "behind"),
        (r"what(?:'s| is) above (?:the )?(.+?)[\?\.]?$", "above"),
        (r"what(?:'s| is) (?:below|under) (?:the )?(.+?)[\?\.]?$", "below"),
        (r"what(?:'s| is) (?:near|next to|beside) (?:the )?(.+?)[\?\.]?$", "near"),
        (r"what(?:'s| is) (?:inside|in) (?:the )?(.+?)[\?\.]?$", "inside"),
        (r"is there anything (on|near|behind|above|below|left of|right of|in front of|inside|in) (?:the )?(.+?)[\?\.]?$", "is_there"),
    ]
    
    for pattern, qtype in patterns:
        match = re.match(pattern, question)
        if match:
            if qtype == "is_there":
                relation = match.group(1).replace(" ", "_")
                reference_obj_name = match.group(2)
                query_type = relation
            else:
                query_type = qtype
                reference_obj_name = match.group(1)
            break
    
    if not query_type or not reference_obj_name:
        return {
            "success": False,
            "error": "Could not parse the question. Try formats like: 'what is on the table?', 'what is near the chair?'",
            "question": question,
        }
    
    reference_obj = _find_object_by_name(reference_obj_name)
    
    if not reference_obj:
        available = [obj.name for obj in bpy.data.objects if obj.visible_get()]
        return {
            "success": False,
            "error": f"Could not find object matching '{reference_obj_name}'",
            "question": question,
            "available_objects": available[:20],
        }
    
    results = []
    ref_loc = reference_obj.matrix_world.translation
    
    for obj in bpy.data.objects:
        if obj.name == reference_obj.name or not obj.visible_get():
            continue
        
        obj_loc = obj.matrix_world.translation
        distance = _calculate_distance(obj, reference_obj)
        
        if query_type != "near" and distance > 10:
            continue
        
        matches = False
        
        if query_type == "on":
            matches = _check_on_top_of(obj, reference_obj)
        elif query_type == "left_of":
            diff = obj_loc - ref_loc
            matches = diff.x < -0.3 and abs(diff.y) < 2 and distance < 5
        elif query_type == "right_of":
            diff = obj_loc - ref_loc
            matches = diff.x > 0.3 and abs(diff.y) < 2 and distance < 5
        elif query_type == "in_front_of":
            diff = obj_loc - ref_loc
            matches = diff.y < -0.3 and abs(diff.x) < 2 and distance < 5
        elif query_type == "behind":
            diff = obj_loc - ref_loc
            matches = diff.y > 0.3 and abs(diff.x) < 2 and distance < 5
        elif query_type == "above":
            diff = obj_loc - ref_loc
            matches = diff.z > 0.3 and distance < 5
        elif query_type == "below":
            diff = obj_loc - ref_loc
            matches = diff.z < -0.3 and distance < 5
        elif query_type == "near":
            matches = distance < 3.0
        elif query_type == "inside" or query_type == "in":
            matches = _check_inside(obj, reference_obj)
        
        if matches:
            results.append({
                "name": obj.name,
                "type": obj.type,
                "distance": round(distance, 2),
                "position": list(obj_loc),
            })
    
    results.sort(key=lambda x: x["distance"])
    
    return {
        "success": True,
        "question": question,
        "query_type": query_type,
        "reference_object": reference_obj.name,
        "results": results,
        "count": len(results),
    }


def find_placement_position(params: Dict[str, Any]) -> Dict[str, Any]:
    """Find a valid position to place an object near another object."""
    reference_name = params["reference"]
    relation = params.get("relation", "on")
    object_size = params.get("object_size", [0.5, 0.5, 0.5])
    
    reference = _find_object_by_name(reference_name)
    if not reference:
        raise ValueError(f"Reference object '{reference_name}' not found")
    
    ref_min, ref_max = _get_object_bounds(reference)
    ref_center = reference.matrix_world.translation
    
    if relation == "on":
        position = mathutils.Vector((ref_center.x, ref_center.y, ref_max.z + object_size[2] / 2))
    elif relation == "next_to" or relation == "beside":
        position = mathutils.Vector((ref_max.x + object_size[0] / 2 + 0.1, ref_center.y, ref_center.z))
    elif relation == "left_of":
        position = mathutils.Vector((ref_min.x - object_size[0] / 2 - 0.1, ref_center.y, ref_center.z))
    elif relation == "right_of":
        position = mathutils.Vector((ref_max.x + object_size[0] / 2 + 0.1, ref_center.y, ref_center.z))
    elif relation == "in_front_of":
        position = mathutils.Vector((ref_center.x, ref_min.y - object_size[1] / 2 - 0.1, ref_center.z))
    elif relation == "behind":
        position = mathutils.Vector((ref_center.x, ref_max.y + object_size[1] / 2 + 0.1, ref_center.z))
    else:
        raise ValueError(f"Unknown relation '{relation}'")
    
    collisions = []
    for obj in bpy.data.objects:
        if obj.name == reference_name or not obj.visible_get():
            continue
        
        obj_min, obj_max = _get_object_bounds(obj)
        place_min = position - mathutils.Vector(object_size) / 2
        place_max = position + mathutils.Vector(object_size) / 2
        
        if _check_bounds_overlap(place_min, place_max, obj_min, obj_max):
            collisions.append(obj.name)
    
    return {
        "reference": reference.name,
        "relation": relation,
        "suggested_position": list(position),
        "collisions": collisions,
        "has_collisions": len(collisions) > 0,
    }


# ============================================================================
# TRANSFORM VALIDATION (from PR #6)
# ============================================================================

def validate_transform(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a transformation before applying it."""
    name = params["name"]
    action = params.get("action", "move")
    
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    issues = []
    warnings = []
    suggestions = []
    
    current_loc = obj.location.copy()
    current_rot = obj.rotation_euler.copy()
    current_scale = obj.scale.copy()
    current_min, current_max = _get_object_bounds(obj)
    
    new_location = None
    new_rotation = None
    new_scale = None
    
    if action == "move":
        delta = params.get("delta", [0, 0, 0])
        absolute = params.get("absolute")
        
        if absolute:
            new_location = mathutils.Vector(absolute)
        else:
            new_location = current_loc + mathutils.Vector(delta)
    
    elif action == "rotate":
        delta = params.get("delta", [0, 0, 0])
        absolute = params.get("absolute")
        
        if absolute:
            new_rotation = mathutils.Euler([math.radians(a) for a in absolute])
        else:
            new_rotation = mathutils.Euler([
                current_rot.x + math.radians(delta[0]),
                current_rot.y + math.radians(delta[1]),
                current_rot.z + math.radians(delta[2]),
            ])
    
    elif action == "scale":
        factor = params.get("factor", [1, 1, 1])
        absolute = params.get("absolute")
        
        if absolute:
            new_scale = mathutils.Vector(absolute)
        else:
            new_scale = mathutils.Vector([
                current_scale.x * factor[0],
                current_scale.y * factor[1],
                current_scale.z * factor[2],
            ])
        
        for i, (axis, val) in enumerate(zip(['X', 'Y', 'Z'], new_scale)):
            if val < 0.01:
                issues.append(f"{axis} scale ({val:.3f}) is extremely small")
            elif val > 100:
                warnings.append(f"{axis} scale ({val:.1f}) is very large")
            elif val < 0:
                issues.append(f"{axis} scale is negative ({val:.2f})")
    
    # Calculate new bounds
    if new_location:
        offset = new_location - current_loc
        new_min = current_min + offset
        new_max = current_max + offset
    else:
        new_min, new_max = current_min, current_max
    
    # Check for collisions
    collisions = []
    for other in bpy.data.objects:
        if other.name == name or not other.visible_get():
            continue
        if other.type not in ('MESH', 'CURVE', 'SURFACE', 'META'):
            continue
        
        other_min, other_max = _get_object_bounds(other)
        currently_overlapping = _check_bounds_overlap(current_min, current_max, other_min, other_max)
        would_overlap = _check_bounds_overlap(new_min, new_max, other_min, other_max)
        
        if would_overlap and not currently_overlapping:
            collisions.append(other.name)
    
    if collisions:
        issues.append(f"Would collide with: {', '.join(collisions)}")
        suggestions.append("Try a smaller movement or different direction")
    
    if new_min.z < -0.1:
        warnings.append(f"Object would go below ground (Z min = {new_min.z:.2f})")
    
    if new_location:
        distance = (new_location - current_loc).length
        if distance > 50:
            warnings.append(f"Large movement ({distance:.1f}m)")
    
    valid = len(issues) == 0
    
    result = {
        "valid": valid,
        "object": name,
        "action": action,
        "current_position": list(current_loc),
        "current_rotation": [math.degrees(r) for r in current_rot],
        "current_scale": list(current_scale),
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "message": "Transform is valid" if valid else f"Transform has {len(issues)} issue(s)",
    }
    
    if new_location:
        result["new_position"] = list(new_location)
    if new_rotation:
        result["new_rotation"] = [math.degrees(r) for r in new_rotation]
    if new_scale:
        result["new_scale"] = list(new_scale)
    
    return result


def get_safe_movement_range(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate how far an object can safely move in each direction."""
    name = params["name"]
    max_distance = params.get("max_distance", 10.0)
    step_size = params.get("step_size", 0.1)
    
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    current_min, current_max = _get_object_bounds(obj)
    current_loc = obj.location.copy()
    
    collision_objects = []
    for other in bpy.data.objects:
        if other.name == name or not other.visible_get():
            continue
        if other.type not in ('MESH', 'CURVE', 'SURFACE', 'META'):
            continue
        collision_objects.append((other.name, *_get_object_bounds(other)))
    
    directions = {
        "+X (right)": mathutils.Vector((1, 0, 0)),
        "-X (left)": mathutils.Vector((-1, 0, 0)),
        "+Y (back)": mathutils.Vector((0, 1, 0)),
        "-Y (front)": mathutils.Vector((0, -1, 0)),
        "+Z (up)": mathutils.Vector((0, 0, 1)),
        "-Z (down)": mathutils.Vector((0, 0, -1)),
    }
    
    safe_distances = {}
    
    for dir_name, direction in directions.items():
        safe_dist = max_distance
        
        for dist in [i * step_size for i in range(1, int(max_distance / step_size) + 1)]:
            test_offset = direction * dist
            test_min = current_min + test_offset
            test_max = current_max + test_offset
            
            if direction.z < 0 and test_min.z < 0:
                safe_dist = min(safe_dist, dist - step_size)
                break
            
            collision = False
            for other_name, other_min, other_max in collision_objects:
                if _check_bounds_overlap(test_min, test_max, other_min, other_max):
                    safe_dist = min(safe_dist, dist - step_size)
                    collision = True
                    break
            
            if collision:
                break
        
        safe_distances[dir_name] = max(0, safe_dist)
    
    return {
        "object": name,
        "position": list(current_loc),
        "safe_distances": safe_distances,
        "max_checked": max_distance,
    }


# ============================================================================
# SEMANTIC MOVEMENT (from PR #7 - already merged)
# ============================================================================

def _parse_position_instruction(instruction: str) -> Dict[str, Any]:
    """Parse a natural language positioning instruction."""
    instruction = instruction.lower().strip()
    
    result = {
        "action": None,
        "reference_object": None,
        "relation": None,
        "direction": None,
        "distance": None,
        "modifier": None,
    }
    
    patterns = [
        (r"(?:place|put|move|set) (?:it |this )?on (?:the )?(left|right) (?:corner |side )?of (?:the )?(.+?)$", "corner"),
        (r"(?:place|put|move|set) (?:it |this )?on (?:the |top of )?(?:the )?(.+?)$", "on"),
        (r"(?:place|put|move|set) (?:it |this )?(?:next to|beside) (?:the )?(.+?)$", "next_to"),
        (r"(?:place|put|move|set) (?:it |this )?(?:to the )?(left|right) of (?:the )?(.+?)$", "side"),
        (r"(?:place|put|move|set) (?:it |this )?(in front of|behind) (?:the )?(.+?)$", "front_back"),
        (r"(?:place|put|move|set) (?:it |this )?(above|below|under|over) (?:the )?(.+?)$", "vertical"),
        (r"(?:place|put|move|set) (?:it |this )?(?:near|close to) (?:the )?(.+?)$", "near"),
        (r"(?:place|put|move|set) (?:it |this )?(?:at |in )?(?:the )?center of (?:the )?(.+?)$", "center"),
        (r"move (?:it |this )?(\d+(?:\.\d+)?)\s*(?:m(?:eters?)?)?\s*(left|right|forward|back(?:ward)?|up|down)", "relative"),
        (r"move (?:it |this )?(left|right|forward|back(?:ward)?|up|down)", "relative_no_dist"),
    ]
    
    for pattern, action_type in patterns:
        match = re.search(pattern, instruction)
        if match:
            groups = match.groups()
            
            if action_type == "on":
                result["action"] = "place"
                result["relation"] = "on"
                result["reference_object"] = groups[0]
            elif action_type == "corner":
                result["action"] = "place"
                result["relation"] = "on"
                result["modifier"] = groups[0]
                result["reference_object"] = groups[1]
            elif action_type == "next_to":
                result["action"] = "place"
                result["relation"] = "next_to"
                result["reference_object"] = groups[0]
            elif action_type == "side":
                result["action"] = "place"
                result["relation"] = groups[0] + "_of"
                result["reference_object"] = groups[1]
            elif action_type == "front_back":
                rel = "in_front_of" if "front" in groups[0] else "behind"
                result["action"] = "place"
                result["relation"] = rel
                result["reference_object"] = groups[1]
            elif action_type == "vertical":
                rel = "above" if groups[0] in ("above", "over") else "below"
                result["action"] = "place"
                result["relation"] = rel
                result["reference_object"] = groups[1]
            elif action_type == "near":
                result["action"] = "place"
                result["relation"] = "near"
                result["reference_object"] = groups[0]
            elif action_type == "center":
                result["action"] = "place"
                result["relation"] = "center"
                result["reference_object"] = groups[0]
            elif action_type == "relative":
                result["action"] = "move_relative"
                result["distance"] = float(groups[0])
                result["direction"] = groups[1].replace("backward", "back")
            elif action_type == "relative_no_dist":
                result["action"] = "move_relative"
                result["distance"] = 1.0
                result["direction"] = groups[0].replace("backward", "back")
            break
    
    return result


def move_object_semantic(params: Dict[str, Any]) -> Dict[str, Any]:
    """Move an object using natural language instructions."""
    name = params["name"]
    instruction = params["instruction"]
    dry_run = params.get("dry_run", False)
    
    obj = _find_object_by_name(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    parsed = _parse_position_instruction(instruction)
    
    if not parsed["action"]:
        return {
            "success": False,
            "error": f"Could not parse instruction: '{instruction}'",
            "hint": "Try: 'place on the desk', 'move 2 meters left', 'put next to the chair'",
            "parsed": parsed,
        }
    
    obj_min, obj_max = _get_object_bounds(obj)
    obj_size = obj_max - obj_min
    original_location = obj.location.copy()
    new_location = None
    
    if parsed["action"] == "move_relative":
        direction_vectors = {
            "left": mathutils.Vector((-1, 0, 0)),
            "right": mathutils.Vector((1, 0, 0)),
            "forward": mathutils.Vector((0, -1, 0)),
            "back": mathutils.Vector((0, 1, 0)),
            "up": mathutils.Vector((0, 0, 1)),
            "down": mathutils.Vector((0, 0, -1)),
        }
        
        direction = parsed["direction"]
        distance = parsed["distance"]
        
        if direction not in direction_vectors:
            return {"success": False, "error": f"Unknown direction: {direction}"}
        
        offset = direction_vectors[direction] * distance
        new_location = original_location + offset
    
    elif parsed["action"] == "place":
        ref_name = parsed["reference_object"]
        reference = _find_object_by_name(ref_name)
        
        if not reference:
            available = [o.name for o in bpy.data.objects if o.visible_get() and o.type == 'MESH'][:10]
            return {
                "success": False,
                "error": f"Reference object '{ref_name}' not found",
                "available_objects": available,
            }
        
        ref_min, ref_max = _get_object_bounds(reference)
        ref_center = reference.matrix_world.translation
        
        relation = parsed["relation"]
        
        if relation == "on":
            if parsed.get("modifier") == "left":
                new_location = mathutils.Vector((ref_min.x + obj_size.x/2 + 0.05, ref_center.y, ref_max.z + obj_size.z/2))
            elif parsed.get("modifier") == "right":
                new_location = mathutils.Vector((ref_max.x - obj_size.x/2 - 0.05, ref_center.y, ref_max.z + obj_size.z/2))
            else:
                new_location = mathutils.Vector((ref_center.x, ref_center.y, ref_max.z + obj_size.z/2))
        elif relation == "next_to":
            new_location = mathutils.Vector((ref_max.x + obj_size.x/2 + 0.2, ref_center.y, max(ref_min.z, 0)))
        elif relation == "left_of":
            new_location = mathutils.Vector((ref_min.x - obj_size.x/2 - 0.2, ref_center.y, max(ref_min.z, 0)))
        elif relation == "right_of":
            new_location = mathutils.Vector((ref_max.x + obj_size.x/2 + 0.2, ref_center.y, max(ref_min.z, 0)))
        elif relation == "in_front_of":
            new_location = mathutils.Vector((ref_center.x, ref_min.y - obj_size.y/2 - 0.2, max(ref_min.z, 0)))
        elif relation == "behind":
            new_location = mathutils.Vector((ref_center.x, ref_max.y + obj_size.y/2 + 0.2, max(ref_min.z, 0)))
        elif relation == "above":
            new_location = mathutils.Vector((ref_center.x, ref_center.y, ref_max.z + obj_size.z/2 + 0.5))
        elif relation == "below":
            new_location = mathutils.Vector((ref_center.x, ref_center.y, ref_min.z - obj_size.z/2 - 0.2))
        elif relation == "near":
            new_location = mathutils.Vector((ref_max.x + obj_size.x/2 + 0.5, ref_center.y, max(ref_min.z, 0)))
        elif relation == "center":
            new_location = mathutils.Vector((ref_center.x, ref_center.y, ref_center.z))
    
    if new_location is None:
        return {"success": False, "error": "Could not calculate target position", "parsed": parsed}
    
    if not dry_run:
        obj.location = new_location
        bpy.context.view_layer.update()
    
    return {
        "success": True,
        "object": obj.name,
        "instruction": instruction,
        "parsed": parsed,
        "original_position": list(original_location),
        "new_position": list(new_location),
        "movement": list(new_location - original_location),
        "dry_run": dry_run,
    }


SPATIAL_HANDLERS = {
    "get_semantic_scene_summary": get_semantic_scene_summary,
    "get_spatial_relationships": get_spatial_relationships,
    "query_spatial": query_spatial,
    "find_placement_position": find_placement_position,
    "validate_transform": validate_transform,
    "get_safe_movement_range": get_safe_movement_range,
    "move_object_semantic": move_object_semantic,
}

"""Handlers for spatial reasoning operations."""

import bpy
import mathutils
from typing import Any, Dict, List, Optional, Tuple
from ..utils.serializers import serialize_object
import math


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


def _get_transformed_bounds(obj, new_location=None, new_rotation=None, new_scale=None):
    """Calculate bounds after a hypothetical transformation."""
    # Store original transform
    orig_loc = obj.location.copy()
    orig_rot = obj.rotation_euler.copy()
    orig_scale = obj.scale.copy()
    
    # Apply hypothetical transform
    if new_location is not None:
        obj.location = mathutils.Vector(new_location)
    if new_rotation is not None:
        obj.rotation_euler = mathutils.Euler(new_rotation)
    if new_scale is not None:
        obj.scale = mathutils.Vector(new_scale)
    
    # Update matrix
    bpy.context.view_layer.update()
    
    # Get new bounds
    new_min, new_max = _get_object_bounds(obj)
    
    # Restore original transform
    obj.location = orig_loc
    obj.rotation_euler = orig_rot
    obj.scale = orig_scale
    bpy.context.view_layer.update()
    
    return new_min, new_max


def _check_bounds_overlap(min1, max1, min2, max2) -> bool:
    """Check if two bounding boxes overlap."""
    return (min1.x < max2.x and max1.x > min2.x and
            min1.y < max2.y and max1.y > min2.y and
            min1.z < max2.z and max1.z > min2.z)


def validate_transform(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a transformation before applying it.
    
    Check if moving/rotating/scaling an object would cause issues like:
    - Collisions with other objects
    - Going out of scene bounds
    - Extreme scale changes
    """
    name = params["name"]
    action = params.get("action", "move")  # move, rotate, scale
    
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    issues = []
    warnings = []
    suggestions = []
    
    # Get current state
    current_loc = obj.location.copy()
    current_rot = obj.rotation_euler.copy()
    current_scale = obj.scale.copy()
    current_min, current_max = _get_object_bounds(obj)
    
    # Calculate new transform
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
        
        # Check for extreme scales
        for i, (axis, val) in enumerate(zip(['X', 'Y', 'Z'], new_scale)):
            if val < 0.01:
                issues.append(f"{axis} scale ({val:.3f}) is extremely small")
            elif val > 100:
                warnings.append(f"{axis} scale ({val:.1f}) is very large")
            elif val < 0:
                issues.append(f"{axis} scale is negative ({val:.2f}) - may cause inverted normals")
    
    # Get new bounds after transform
    new_min, new_max = _get_transformed_bounds(obj, new_location, new_rotation, new_scale)
    
    # Check for collisions with other objects
    collisions = []
    for other in bpy.data.objects:
        if other.name == name or not other.visible_get():
            continue
        if other.type not in ('MESH', 'CURVE', 'SURFACE', 'META'):
            continue
        
        other_min, other_max = _get_object_bounds(other)
        
        # Check if currently overlapping
        currently_overlapping = _check_bounds_overlap(current_min, current_max, other_min, other_max)
        
        # Check if would overlap after transform
        would_overlap = _check_bounds_overlap(new_min, new_max, other_min, other_max)
        
        if would_overlap and not currently_overlapping:
            collisions.append(other.name)
    
    if collisions:
        issues.append(f"Would collide with: {', '.join(collisions)}")
        suggestions.append("Try a smaller movement or move in a different direction")
    
    # Check if going below ground (Z < 0)
    if new_min.z < -0.1:
        warnings.append(f"Object would go below ground (Z min = {new_min.z:.2f})")
        suggestions.append("Consider adjusting Z position to stay above ground")
    
    # Check for very large movements
    if new_location:
        distance = (new_location - current_loc).length
        if distance > 50:
            warnings.append(f"Large movement ({distance:.1f}m) - verify this is intended")
    
    # Build result
    valid = len(issues) == 0
    
    result = {
        "valid": valid,
        "object": name,
        "action": action,
        "current_position": list(current_loc),
        "current_rotation": [math.degrees(r) for r in current_rot],
        "current_scale": list(current_scale),
    }
    
    if new_location:
        result["new_position"] = list(new_location)
    if new_rotation:
        result["new_rotation"] = [math.degrees(r) for r in new_rotation]
    if new_scale:
        result["new_scale"] = list(new_scale)
    
    result["issues"] = issues
    result["warnings"] = warnings
    result["suggestions"] = suggestions
    
    if valid:
        result["message"] = "Transform is valid and can be applied"
    else:
        result["message"] = f"Transform has {len(issues)} issue(s) that should be addressed"
    
    return result


def get_safe_movement_range(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate how far an object can safely move in each direction without collisions."""
    name = params["name"]
    max_distance = params.get("max_distance", 10.0)
    step_size = params.get("step_size", 0.1)
    
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    current_min, current_max = _get_object_bounds(obj)
    current_loc = obj.location.copy()
    
    # Get all potential collision objects
    collision_objects = []
    for other in bpy.data.objects:
        if other.name == name or not other.visible_get():
            continue
        if other.type not in ('MESH', 'CURVE', 'SURFACE', 'META'):
            continue
        collision_objects.append((other.name, *_get_object_bounds(other)))
    
    # Check each direction
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
        
        # Check incrementally
        for dist in [i * step_size for i in range(1, int(max_distance / step_size) + 1)]:
            test_offset = direction * dist
            test_min = current_min + test_offset
            test_max = current_max + test_offset
            
            # Check ground collision for down movement
            if direction.z < 0 and test_min.z < 0:
                safe_dist = min(safe_dist, dist - step_size)
                break
            
            # Check object collisions
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


SPATIAL_HANDLERS = {
    "validate_transform": validate_transform,
    "get_safe_movement_range": get_safe_movement_range,
}

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


def _calculate_distance(obj1, obj2) -> float:
    """Calculate distance between two object centers."""
    return (obj1.matrix_world.translation - obj2.matrix_world.translation).length


def _check_on_top_of(obj, other) -> bool:
    """Check if obj is on top of other."""
    obj_min, obj_max = _get_object_bounds(obj)
    other_min, other_max = _get_object_bounds(other)
    
    # Check if obj's bottom is near other's top
    if not (obj_min.z >= other_max.z - 0.1 and obj_min.z <= other_max.z + 0.3):
        return False
    
    # Check horizontal overlap
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


def _get_relative_direction(from_obj, to_obj) -> Dict[str, str]:
    """Get the direction from one object to another."""
    diff = to_obj.matrix_world.translation - from_obj.matrix_world.translation
    
    return {
        "x": "right" if diff.x > 0.3 else "left" if diff.x < -0.3 else "aligned",
        "y": "behind" if diff.y > 0.3 else "front" if diff.y < -0.3 else "aligned",
        "z": "above" if diff.z > 0.3 else "below" if diff.z < -0.3 else "same_level",
    }


def query_spatial(params: Dict[str, Any]) -> Dict[str, Any]:
    """Answer natural language spatial queries about the scene.
    
    Supports queries like:
    - "what is on the table?"
    - "what is to the left of the chair?"
    - "what is near the desk?"
    - "what is above the floor?"
    - "is there anything behind the sofa?"
    """
    question = params["question"].lower().strip()
    
    # Parse the question to extract the query type and reference object
    query_type = None
    reference_obj_name = None
    
    # Patterns for different query types
    patterns = [
        # "what is on [the] X" / "what's on [the] X"
        (r"what(?:'s| is) on (?:the )?(.+?)[\?\.]?$", "on"),
        # "what is to the left of [the] X"
        (r"what(?:'s| is) (?:to the )?left of (?:the )?(.+?)[\?\.]?$", "left_of"),
        # "what is to the right of [the] X"
        (r"what(?:'s| is) (?:to the )?right of (?:the )?(.+?)[\?\.]?$", "right_of"),
        # "what is in front of [the] X"
        (r"what(?:'s| is) in front of (?:the )?(.+?)[\?\.]?$", "in_front_of"),
        # "what is behind [the] X"
        (r"what(?:'s| is) behind (?:the )?(.+?)[\?\.]?$", "behind"),
        # "what is above [the] X"
        (r"what(?:'s| is) above (?:the )?(.+?)[\?\.]?$", "above"),
        # "what is below [the] X" / "what is under [the] X"
        (r"what(?:'s| is) (?:below|under) (?:the )?(.+?)[\?\.]?$", "below"),
        # "what is near [the] X" / "what is next to [the] X"
        (r"what(?:'s| is) (?:near|next to|beside) (?:the )?(.+?)[\?\.]?$", "near"),
        # "what is inside [the] X" / "what is in [the] X"
        (r"what(?:'s| is) (?:inside|in) (?:the )?(.+?)[\?\.]?$", "inside"),
        # "is there anything [relation] [the] X"
        (r"is there anything (on|near|behind|above|below|left of|right of|in front of|inside|in) (?:the )?(.+?)[\?\.]?$", "is_there"),
    ]
    
    for pattern, qtype in patterns:
        match = re.match(pattern, question)
        if match:
            if qtype == "is_there":
                # Special handling for "is there" queries
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
            "error": "Could not parse the question. Try formats like: 'what is on the table?', 'what is near the chair?', 'what is to the left of the desk?'",
            "question": question,
        }
    
    # Find the reference object (case-insensitive partial match)
    reference_obj = None
    ref_name_lower = reference_obj_name.lower()
    
    for obj in bpy.data.objects:
        if ref_name_lower in obj.name.lower():
            reference_obj = obj
            break
    
    if not reference_obj:
        # Try to match common words
        for obj in bpy.data.objects:
            obj_words = obj.name.lower().replace("_", " ").replace(".", " ").split()
            if ref_name_lower in obj_words:
                reference_obj = obj
                break
    
    if not reference_obj:
        available = [obj.name for obj in bpy.data.objects if obj.visible_get()]
        return {
            "success": False,
            "error": f"Could not find object matching '{reference_obj_name}'",
            "question": question,
            "available_objects": available[:20],
        }
    
    # Find objects matching the spatial relationship
    results = []
    ref_loc = reference_obj.matrix_world.translation
    
    for obj in bpy.data.objects:
        if obj.name == reference_obj.name or not obj.visible_get():
            continue
        
        obj_loc = obj.matrix_world.translation
        distance = _calculate_distance(obj, reference_obj)
        
        # Skip objects too far away for most queries
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
    
    # Sort by distance
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
    """Find a valid position to place an object near another object.
    
    Useful for commands like "place a lamp on the desk" or "put the chair next to the table".
    """
    reference_name = params["reference"]
    relation = params.get("relation", "on")  # on, next_to, behind, in_front_of, left_of, right_of
    object_size = params.get("object_size", [0.5, 0.5, 0.5])  # approximate size of object to place
    
    reference = bpy.data.objects.get(reference_name)
    if not reference:
        # Try case-insensitive partial match
        for obj in bpy.data.objects:
            if reference_name.lower() in obj.name.lower():
                reference = obj
                break
    
    if not reference:
        raise ValueError(f"Reference object '{reference_name}' not found")
    
    ref_min, ref_max = _get_object_bounds(reference)
    ref_center = reference.matrix_world.translation
    ref_size = ref_max - ref_min
    
    # Calculate placement position based on relation
    if relation == "on":
        # Place on top center
        position = mathutils.Vector((
            ref_center.x,
            ref_center.y,
            ref_max.z + object_size[2] / 2
        ))
    
    elif relation == "next_to" or relation == "beside":
        # Place to the right by default
        position = mathutils.Vector((
            ref_max.x + object_size[0] / 2 + 0.1,
            ref_center.y,
            ref_center.z
        ))
    
    elif relation == "left_of":
        position = mathutils.Vector((
            ref_min.x - object_size[0] / 2 - 0.1,
            ref_center.y,
            ref_center.z
        ))
    
    elif relation == "right_of":
        position = mathutils.Vector((
            ref_max.x + object_size[0] / 2 + 0.1,
            ref_center.y,
            ref_center.z
        ))
    
    elif relation == "in_front_of":
        position = mathutils.Vector((
            ref_center.x,
            ref_min.y - object_size[1] / 2 - 0.1,
            ref_center.z
        ))
    
    elif relation == "behind":
        position = mathutils.Vector((
            ref_center.x,
            ref_max.y + object_size[1] / 2 + 0.1,
            ref_center.z
        ))
    
    else:
        raise ValueError(f"Unknown relation '{relation}'. Use: on, next_to, left_of, right_of, in_front_of, behind")
    
    # Check for collisions with existing objects
    collisions = []
    for obj in bpy.data.objects:
        if obj.name == reference_name or not obj.visible_get():
            continue
        
        obj_min, obj_max = _get_object_bounds(obj)
        
        # Check if placement would overlap
        place_min = position - mathutils.Vector(object_size) / 2
        place_max = position + mathutils.Vector(object_size) / 2
        
        overlap = (place_min.x < obj_max.x and place_max.x > obj_min.x and
                  place_min.y < obj_max.y and place_max.y > obj_min.y and
                  place_min.z < obj_max.z and place_max.z > obj_min.z)
        
        if overlap:
            collisions.append(obj.name)
    
    return {
        "reference": reference.name,
        "relation": relation,
        "suggested_position": list(position),
        "collisions": collisions,
        "has_collisions": len(collisions) > 0,
        "suggestion": f"Place at ({position.x:.2f}, {position.y:.2f}, {position.z:.2f})" + 
                      (f" - Warning: may overlap with {', '.join(collisions)}" if collisions else " - Clear space"),
    }


SPATIAL_HANDLERS = {
    "query_spatial": query_spatial,
    "find_placement_position": find_placement_position,
}

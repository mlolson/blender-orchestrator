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


def _find_object_by_name(name: str):
    """Find an object by exact or partial name match."""
    # Try exact match first
    obj = bpy.data.objects.get(name)
    if obj:
        return obj
    
    # Try case-insensitive partial match
    name_lower = name.lower()
    for obj in bpy.data.objects:
        if name_lower in obj.name.lower():
            return obj
    
    # Try word match
    for obj in bpy.data.objects:
        obj_words = obj.name.lower().replace("_", " ").replace(".", " ").split()
        if name_lower in obj_words:
            return obj
    
    return None


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
    
    # Patterns for different types of instructions
    patterns = [
        # "place/put/move X on [the] Y"
        (r"(?:place|put|move|set) (?:it |this )?on (?:the |top of )?(?:the )?(.+?)$", "on"),
        # "place X on the left/right corner of Y"
        (r"(?:place|put|move|set) (?:it |this )?on (?:the )?(left|right) (?:corner |side )?of (?:the )?(.+?)$", "corner"),
        # "place X next to / beside Y"
        (r"(?:place|put|move|set) (?:it |this )?(?:next to|beside) (?:the )?(.+?)$", "next_to"),
        # "place X to the left/right of Y"
        (r"(?:place|put|move|set) (?:it |this )?(?:to the )?(left|right) of (?:the )?(.+?)$", "side"),
        # "place X in front of / behind Y"
        (r"(?:place|put|move|set) (?:it |this )?(in front of|behind) (?:the )?(.+?)$", "front_back"),
        # "place X above / below Y"
        (r"(?:place|put|move|set) (?:it |this )?(above|below|under|over) (?:the )?(.+?)$", "vertical"),
        # "place X near Y" / "place X close to Y"
        (r"(?:place|put|move|set) (?:it |this )?(?:near|close to) (?:the )?(.+?)$", "near"),
        # "place X at the center of Y"
        (r"(?:place|put|move|set) (?:it |this )?(?:at |in )?(?:the )?center of (?:the )?(.+?)$", "center"),
        # "move X [distance] [direction]" - e.g., "move it 2 meters left"
        (r"move (?:it |this )?(\d+(?:\.\d+)?)\s*(?:m(?:eters?)?)?\s*(left|right|forward|back(?:ward)?|up|down)", "relative"),
        # "move X [direction]" - e.g., "move it left"
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
                result["modifier"] = groups[0]  # left or right
                result["reference_object"] = groups[1]
            
            elif action_type == "next_to":
                result["action"] = "place"
                result["relation"] = "next_to"
                result["reference_object"] = groups[0]
            
            elif action_type == "side":
                result["action"] = "place"
                result["relation"] = groups[0] + "_of"  # left_of or right_of
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
                result["distance"] = 1.0  # default 1 meter
                result["direction"] = groups[0].replace("backward", "back")
            
            break
    
    return result


def move_object_semantic(params: Dict[str, Any]) -> Dict[str, Any]:
    """Move an object using natural language instructions.
    
    Supports instructions like:
    - "place on the desk"
    - "put on the left corner of the table"
    - "move next to the chair"
    - "place in front of the camera"
    - "move 2 meters left"
    - "put behind the sofa"
    """
    name = params["name"]
    instruction = params["instruction"]
    dry_run = params.get("dry_run", False)
    
    obj = _find_object_by_name(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    
    # Parse the instruction
    parsed = _parse_position_instruction(instruction)
    
    if not parsed["action"]:
        return {
            "success": False,
            "error": f"Could not parse instruction: '{instruction}'",
            "hint": "Try formats like: 'place on the desk', 'move 2 meters left', 'put next to the chair'",
            "parsed": parsed,
        }
    
    obj_min, obj_max = _get_object_bounds(obj)
    obj_size = obj_max - obj_min
    original_location = obj.location.copy()
    new_location = None
    
    if parsed["action"] == "move_relative":
        # Relative movement in a direction
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
            return {
                "success": False,
                "error": f"Unknown direction: {direction}",
            }
        
        offset = direction_vectors[direction] * distance
        new_location = original_location + offset
    
    elif parsed["action"] == "place":
        # Placement relative to another object
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
        ref_size = ref_max - ref_min
        
        relation = parsed["relation"]
        
        if relation == "on":
            # Place on top
            if parsed.get("modifier") == "left":
                # Left corner
                new_location = mathutils.Vector((
                    ref_min.x + obj_size.x / 2 + 0.05,
                    ref_center.y,
                    ref_max.z + obj_size.z / 2
                ))
            elif parsed.get("modifier") == "right":
                # Right corner
                new_location = mathutils.Vector((
                    ref_max.x - obj_size.x / 2 - 0.05,
                    ref_center.y,
                    ref_max.z + obj_size.z / 2
                ))
            else:
                # Center
                new_location = mathutils.Vector((
                    ref_center.x,
                    ref_center.y,
                    ref_max.z + obj_size.z / 2
                ))
        
        elif relation == "next_to":
            # Place beside (default to right side)
            new_location = mathutils.Vector((
                ref_max.x + obj_size.x / 2 + 0.2,
                ref_center.y,
                max(ref_min.z, 0)
            ))
        
        elif relation == "left_of":
            new_location = mathutils.Vector((
                ref_min.x - obj_size.x / 2 - 0.2,
                ref_center.y,
                max(ref_min.z, 0)
            ))
        
        elif relation == "right_of":
            new_location = mathutils.Vector((
                ref_max.x + obj_size.x / 2 + 0.2,
                ref_center.y,
                max(ref_min.z, 0)
            ))
        
        elif relation == "in_front_of":
            new_location = mathutils.Vector((
                ref_center.x,
                ref_min.y - obj_size.y / 2 - 0.2,
                max(ref_min.z, 0)
            ))
        
        elif relation == "behind":
            new_location = mathutils.Vector((
                ref_center.x,
                ref_max.y + obj_size.y / 2 + 0.2,
                max(ref_min.z, 0)
            ))
        
        elif relation == "above":
            new_location = mathutils.Vector((
                ref_center.x,
                ref_center.y,
                ref_max.z + obj_size.z / 2 + 0.5
            ))
        
        elif relation == "below":
            new_location = mathutils.Vector((
                ref_center.x,
                ref_center.y,
                ref_min.z - obj_size.z / 2 - 0.2
            ))
        
        elif relation == "near":
            # Place nearby (offset in X)
            new_location = mathutils.Vector((
                ref_max.x + obj_size.x / 2 + 0.5,
                ref_center.y,
                max(ref_min.z, 0)
            ))
        
        elif relation == "center":
            new_location = mathutils.Vector((
                ref_center.x,
                ref_center.y,
                ref_center.z
            ))
    
    if new_location is None:
        return {
            "success": False,
            "error": "Could not calculate target position",
            "parsed": parsed,
        }
    
    # Apply the movement (unless dry run)
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
    "move_object_semantic": move_object_semantic,
}

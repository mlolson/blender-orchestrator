"""Handlers for metaball operations.

Metaballs create organic shapes that automatically blend where they overlap,
making them ideal for character bodies, organic forms, and smooth transitions.
"""

import bpy
from mathutils import Euler, Quaternion
from typing import Any, Dict
from ..utils.serializers import serialize_object


def create_metaball_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a metaball object.

    Metaballs are implicit surfaces that automatically blend together
    when they overlap, creating smooth organic shapes.

    params:
        name: object name (default "Metaball")
        resolution: viewport resolution (default 0.2, lower = smoother but slower)
        render_resolution: render resolution (default 0.1)
        threshold: surface threshold (default 0.0)
        location: [x, y, z] position (default [0, 0, 0])
        radius: initial element radius (default 1.0)
    """
    name = params.get("name", "Metaball")
    resolution = params.get("resolution", 0.2)
    render_resolution = params.get("render_resolution", 0.1)
    threshold = params.get("threshold", 0.6)  # Must be > 0 for surface to appear
    location = tuple(params.get("location", [0, 0, 0]))
    radius = params.get("radius", 1.0)

    # Get proper context for operator - need a 3D View context
    window = bpy.context.window
    screen = window.screen
    area = None
    region = None

    # Find a VIEW_3D area
    for a in screen.areas:
        if a.type == 'VIEW_3D':
            area = a
            for r in a.regions:
                if r.type == 'WINDOW':
                    region = r
                    break
            break

    if area and region:
        # Use context override for Blender 4.x
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.object.metaball_add(type='BALL', radius=radius, location=location)
    else:
        # Fallback - try without override
        bpy.ops.object.metaball_add(type='BALL', radius=radius, location=location)

    obj = bpy.context.active_object

    # Get the metaball data
    mball = obj.data

    # Set resolution settings
    mball.resolution = resolution
    mball.render_resolution = render_resolution
    mball.threshold = threshold

    # Rename object (but keep data name matching for metaball family system)
    if name and name != "Mball":
        obj.name = name
        # Also rename data to match (important for metaball families)
        mball.name = name

    # Force depsgraph update
    bpy.context.view_layer.update()

    # Also trigger a scene update
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()

    return serialize_object(obj)


def add_metaball_element(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add an element to a metaball object.

    Elements are the building blocks of metaballs. Multiple elements
    blend together to create the final surface.

    params:
        name: metaball object name
        type: element type - 'BALL', 'CAPSULE', 'PLANE', 'ELLIPSOID', 'CUBE'
        location: [x, y, z] position relative to object origin
        radius: base radius (default 1.0)
        size_x: X scale for ellipsoid (default 1.0)
        size_y: Y scale for ellipsoid (default 1.0)
        size_z: Z scale for ellipsoid (default 1.0)
        rotation: [x, y, z] rotation in radians (default [0, 0, 0])
        stiffness: blending stiffness (default 2.0, higher = sharper edges, less blending)
        negative: if True, subtracts from surface (default False)
    """
    object_name = params["name"]
    element_type = params.get("type", "BALL").upper()
    location = params.get("location", [0, 0, 0])
    radius = params.get("radius", 1.0)
    size_x = params.get("size_x", 1.0)
    size_y = params.get("size_y", 1.0)
    size_z = params.get("size_z", 1.0)
    rotation = params.get("rotation", [0, 0, 0])
    stiffness = params.get("stiffness", 2.0)
    negative = params.get("negative", False)

    # Validate element type
    valid_types = ['BALL', 'CAPSULE', 'PLANE', 'ELLIPSOID', 'CUBE']
    if element_type not in valid_types:
        raise ValueError(f"Invalid element type '{element_type}'. Must be one of: {valid_types}")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        raise ValueError(f"Object '{object_name}' not found")
    if obj.type != 'META':
        raise ValueError(f"Object '{object_name}' is not a metaball (type: {obj.type})")

    mball = obj.data

    # Add new element
    elem = mball.elements.new()
    elem.type = element_type
    elem.co = location
    elem.radius = radius
    elem.size_x = size_x
    elem.size_y = size_y
    elem.size_z = size_z
    elem.stiffness = stiffness
    elem.use_negative = negative

    # Handle rotation - convert Euler to Quaternion if needed
    # Metaball elements use quaternion rotation
    if rotation and rotation != [0, 0, 0]:
        euler = Euler(rotation, 'XYZ')
        elem.rotation = euler.to_quaternion()

    return {
        "name": object_name,
        "element_count": len(mball.elements),
        "element_type": element_type,
        "location": list(location),
        "radius": radius,
    }


def remove_metaball_element(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove an element from a metaball by index.

    params:
        name: metaball object name
        index: element index to remove (0-based)
    """
    object_name = params["name"]
    index = params["index"]

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != 'META':
        raise ValueError(f"'{object_name}' is not a metaball object")

    mball = obj.data

    if index < 0 or index >= len(mball.elements):
        raise ValueError(f"Element index {index} out of range (0-{len(mball.elements)-1})")

    mball.elements.remove(mball.elements[index])

    return {
        "name": object_name,
        "removed_index": index,
        "remaining_elements": len(mball.elements),
    }


def modify_metaball_element(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify an existing metaball element.

    params:
        name: metaball object name
        index: element index to modify
        type: new element type (optional)
        location: new [x, y, z] position (optional)
        radius: new radius (optional)
        size_x/y/z: new scale factors (optional)
        stiffness: new stiffness (optional)
        negative: new negative flag (optional)
    """
    object_name = params["name"]
    index = params["index"]

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != 'META':
        raise ValueError(f"'{object_name}' is not a metaball object")

    mball = obj.data

    if index < 0 or index >= len(mball.elements):
        raise ValueError(f"Element index {index} out of range")

    elem = mball.elements[index]

    # Apply modifications
    if "type" in params:
        elem.type = params["type"].upper()
    if "location" in params:
        elem.co = params["location"]
    if "radius" in params:
        elem.radius = params["radius"]
    if "size_x" in params:
        elem.size_x = params["size_x"]
    if "size_y" in params:
        elem.size_y = params["size_y"]
    if "size_z" in params:
        elem.size_z = params["size_z"]
    if "stiffness" in params:
        elem.stiffness = params["stiffness"]
    if "negative" in params:
        elem.use_negative = params["negative"]

    return {
        "name": object_name,
        "modified_index": index,
        "type": elem.type,
        "location": list(elem.co),
        "radius": elem.radius,
    }


def get_metaball_elements(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get all elements in a metaball object.

    params:
        name: metaball object name
    """
    object_name = params["name"]

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != 'META':
        raise ValueError(f"'{object_name}' is not a metaball object")

    mball = obj.data

    elements = []
    for i, elem in enumerate(mball.elements):
        elements.append({
            "index": i,
            "type": elem.type,
            "location": list(elem.co),
            "radius": elem.radius,
            "size_x": elem.size_x,
            "size_y": elem.size_y,
            "size_z": elem.size_z,
            "stiffness": elem.stiffness,
            "negative": elem.use_negative,
        })

    return {
        "name": object_name,
        "data_name": mball.name,  # The actual metaball data block name
        "is_editmode": obj.mode == 'EDIT',
        "element_count": len(elements),
        "elements": elements,
        "resolution": mball.resolution,
        "render_resolution": mball.render_resolution,
        "threshold": mball.threshold,
    }


def set_metaball_resolution(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set metaball resolution settings.

    params:
        name: metaball object name
        resolution: viewport resolution (lower = smoother)
        render_resolution: render resolution (optional)
        threshold: surface threshold (optional)
    """
    object_name = params["name"]

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != 'META':
        raise ValueError(f"'{object_name}' is not a metaball object")

    mball = obj.data

    if "resolution" in params:
        mball.resolution = params["resolution"]
    if "render_resolution" in params:
        mball.render_resolution = params["render_resolution"]
    if "threshold" in params:
        mball.threshold = params["threshold"]

    return {
        "name": object_name,
        "resolution": mball.resolution,
        "render_resolution": mball.render_resolution,
        "threshold": mball.threshold,
    }


def convert_metaball_to_mesh(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a metaball to an editable mesh.

    This "freezes" the metaball surface into a regular mesh that can
    be edited with standard mesh tools.

    params:
        name: metaball object name
        new_name: name for the resulting mesh (optional, defaults to original name)
        keep_original: keep the metaball object (default False)
    """
    object_name = params["name"]
    new_name = params.get("new_name", object_name)
    keep_original = params.get("keep_original", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        raise ValueError(f"Object '{object_name}' not found")

    # Ensure object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Select and activate
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if keep_original:
        # Duplicate first
        bpy.ops.object.duplicate()
        obj = bpy.context.active_object
        obj.name = new_name

    # Convert to mesh
    bpy.ops.object.convert(target='MESH')

    # Get the new mesh object (convert replaces the original)
    obj = bpy.context.active_object

    # Rename if needed
    if not keep_original and new_name != object_name:
        obj.name = new_name

    return serialize_object(obj, detailed=True)


def create_metaball_body(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a basic humanoid body shape using metaballs.

    This is a convenience function that creates a complete body structure
    with natural blending between parts.

    params:
        name: object name (default "MetaballBody")
        style: 'realistic', 'cartoon', or 'chibi' (default 'realistic')
        scale: overall scale factor (default 1.0)
        resolution: metaball resolution (default 0.1)
    """
    name = params.get("name", "MetaballBody")
    style = params.get("style", "realistic").lower()
    scale = params.get("scale", 1.0)
    resolution = params.get("resolution", 0.1)

    # Define body proportions based on style
    if style == "cartoon":
        proportions = {
            "head_size": 0.18,
            "head_height": 1.5,
            "torso_height": 0.9,
            "torso_width": 0.12,
            "hip_width": 0.1,
            "arm_radius": 0.04,
            "leg_radius": 0.05,
        }
    elif style == "chibi":
        proportions = {
            "head_size": 0.25,
            "head_height": 1.2,
            "torso_height": 0.5,
            "torso_width": 0.1,
            "hip_width": 0.08,
            "arm_radius": 0.03,
            "leg_radius": 0.04,
        }
    else:  # realistic
        proportions = {
            "head_size": 0.12,
            "head_height": 1.65,
            "torso_height": 1.2,
            "torso_width": 0.15,
            "hip_width": 0.14,
            "arm_radius": 0.04,
            "leg_radius": 0.06,
        }

    # Apply scale
    for key in proportions:
        proportions[key] *= scale

    # Create metaball object
    create_metaball_object({
        "name": name,
        "resolution": resolution,
        "location": [0, 0, 0],
    })

    # Head
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, proportions["head_height"]],
        "radius": proportions["head_size"],
        "size_x": 1.0,
        "size_y": 1.15,
        "size_z": 1.1,
        "stiffness": 2.0,
    })

    # Neck
    add_metaball_element({
        "name": name,
        "type": "CAPSULE",
        "location": [0, 0, proportions["head_height"] - proportions["head_size"] - 0.05 * scale],
        "radius": 0.035 * scale,
        "size_z": 0.15,
        "stiffness": 3.0,
    })

    # Upper torso (chest)
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, proportions["torso_height"]],
        "radius": proportions["torso_width"],
        "size_x": 1.1,
        "size_y": 0.7,
        "size_z": 0.6,
        "stiffness": 2.0,
    })

    # Lower torso (waist)
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, proportions["torso_height"] - 0.2 * scale],
        "radius": proportions["torso_width"] * 0.7,
        "size_x": 0.9,
        "size_y": 0.6,
        "size_z": 0.5,
        "stiffness": 2.5,
    })

    # Hips
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, proportions["torso_height"] - 0.4 * scale],
        "radius": proportions["hip_width"],
        "size_x": 1.2,
        "size_y": 0.8,
        "size_z": 0.5,
        "stiffness": 2.0,
    })

    # Arms (simplified as capsules)
    for side in [1, -1]:  # Right and left
        # Upper arm
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * 0.2 * scale, 0, proportions["torso_height"]],
            "radius": proportions["arm_radius"],
            "size_z": 0.25,
            "stiffness": 2.5,
        })
        # Forearm
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * 0.35 * scale, 0, proportions["torso_height"] - 0.15 * scale],
            "radius": proportions["arm_radius"] * 0.85,
            "size_z": 0.2,
            "stiffness": 2.5,
        })

    # Legs (simplified as capsules)
    for side in [1, -1]:
        # Upper leg
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * 0.08 * scale, 0, proportions["torso_height"] - 0.7 * scale],
            "radius": proportions["leg_radius"],
            "size_z": 0.35,
            "stiffness": 2.0,
        })
        # Lower leg
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * 0.08 * scale, 0, proportions["torso_height"] - 1.1 * scale],
            "radius": proportions["leg_radius"] * 0.8,
            "size_z": 0.3,
            "stiffness": 2.0,
        })

    return {
        "name": name,
        "style": style,
        "scale": scale,
        "message": f"Created {style} body with metaballs. Use convert_metaball_to_mesh to finalize.",
    }


METABALL_HANDLERS = {
    "create_metaball_object": create_metaball_object,
    "add_metaball_element": add_metaball_element,
    "remove_metaball_element": remove_metaball_element,
    "modify_metaball_element": modify_metaball_element,
    "get_metaball_elements": get_metaball_elements,
    "set_metaball_resolution": set_metaball_resolution,
    "convert_metaball_to_mesh": convert_metaball_to_mesh,
    "create_metaball_body": create_metaball_body,
}

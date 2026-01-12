"""Humanoid character templates with proper proportions.

These templates provide pre-configured character bases using metaballs
and skin modifiers for natural-looking organic forms.
"""

import bpy
from typing import Any, Dict
from ..handlers.metaballs import (
    create_metaball_object,
    add_metaball_element,
    convert_metaball_to_mesh,
)
from ..handlers.materials import (
    create_toon_shader,
    create_skin_shader,
    assign_material,
)
from ..handlers.mesh_editing import (
    mesh_filter,
    add_subdivision_surface,
    create_integrated_eye,
    create_mouth_opening,
    create_nose_bump,
    add_cartoon_outline,
)


# =============================================================================
# Proportion Constants
# =============================================================================

REALISTIC_PROPORTIONS = {
    "name": "Realistic",
    "total_heads": 7.5,          # Total height in head units
    "head_width": 0.75,          # Head width relative to height
    "shoulder_width": 2.0,       # Shoulders in head widths
    "hip_width": 1.5,            # Hips in head widths
    "arm_length": 3.0,           # Arm length in head heights
    "leg_length": 4.0,           # Leg length in head heights
    "torso_length": 2.5,         # Torso in head heights
    "eye_spacing": 1.0,          # Eyes are one eye-width apart
    "eye_level": 0.5,            # Eyes at half head height
}

CARTOON_PROPORTIONS = {
    "name": "Cartoon",
    "total_heads": 4.0,          # Shorter, cuter proportions
    "head_width": 1.2,           # Wider, rounder head
    "shoulder_width": 1.8,
    "hip_width": 1.2,
    "arm_length": 2.0,
    "leg_length": 2.0,
    "torso_length": 1.5,
    "eye_spacing": 1.2,          # Eyes slightly further apart
    "eye_level": 0.45,           # Eyes slightly lower
    "eye_size": 2.0,             # 2x larger eyes
}

CHIBI_PROPORTIONS = {
    "name": "Chibi",
    "total_heads": 2.5,          # Very short body
    "head_width": 1.4,           # Very round head
    "shoulder_width": 1.5,
    "hip_width": 1.0,
    "arm_length": 1.2,
    "leg_length": 1.0,
    "torso_length": 0.8,
    "eye_spacing": 1.0,
    "eye_level": 0.4,            # Eyes lower on face
    "eye_size": 3.0,             # Very large eyes
}


# =============================================================================
# Template Definitions
# =============================================================================

def create_character_from_template(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a complete character from a template.

    params:
        name: character name (default "Character")
        style: 'realistic', 'cartoon', 'chibi' (default 'cartoon')
        height: total height in Blender units (default 1.8)
        head_height: explicit head height (optional, calculated from height if not set)
        skin_color: [r, g, b] skin color (default warm skin tone)
        eye_color: [r, g, b] eye/iris color (default brown)
        add_eyes: create eyes (default True)
        add_face_features: create nose/mouth (default True)
        add_outline: add cartoon outline for toon style (default False)
        apply_material: apply toon/skin shader (default True)
        convert_to_mesh: convert metaballs to mesh (default True)
    """
    name = params.get("name", "Character")
    style = params.get("style", "cartoon").lower()
    height = params.get("height", 1.8)
    skin_color = params.get("skin_color", [0.85, 0.65, 0.55, 1.0])
    eye_color = params.get("eye_color", [0.3, 0.2, 0.15, 1.0])
    add_eyes = params.get("add_eyes", True)
    add_face_features = params.get("add_face_features", True)
    add_outline = params.get("add_outline", False)
    apply_material = params.get("apply_material", True)
    convert_to_mesh = params.get("convert_to_mesh", True)

    # Get proportions for style
    if style == "realistic":
        props = REALISTIC_PROPORTIONS.copy()
    elif style == "chibi":
        props = CHIBI_PROPORTIONS.copy()
    else:
        props = CARTOON_PROPORTIONS.copy()

    # Calculate dimensions
    head_height = params.get("head_height", height / props["total_heads"])
    head_width = head_height * props["head_width"]

    # Create body using metaballs
    body_name = f"{name}_Body"
    _create_metaball_body(body_name, head_height, props, style)

    # Convert to mesh if requested
    if convert_to_mesh:
        convert_metaball_to_mesh({"name": body_name})

        # Apply smoothing
        mesh_filter({
            "name": body_name,
            "filter_type": "SMOOTH",
            "strength": 0.3,
            "iterations": 2,
        })

        # Add subdivision for smoothness
        add_subdivision_surface({
            "name": body_name,
            "levels": 1,
            "render_levels": 2,
        })

    # Create and apply material
    if apply_material:
        if style in ["cartoon", "chibi"]:
            mat_name = f"{name}_ToonMat"
            shadow_color = [c * 0.6 for c in skin_color[:3]] + [1.0]
            create_toon_shader({
                "name": mat_name,
                "base_color": skin_color,
                "shadow_color": shadow_color,
                "steps": 3,
            })
        else:
            mat_name = f"{name}_SkinMat"
            create_skin_shader({
                "name": mat_name,
                "base_color": skin_color,
                "subsurface": 0.3,
            })

        assign_material({
            "object_name": body_name,
            "material_name": mat_name,
        })

    # Add face features
    head_center_z = height - head_height * 0.5  # Approximate head center
    eye_y = head_width * 0.4  # Forward position

    if add_eyes and convert_to_mesh:
        eye_scale = props.get("eye_size", 1.0)
        eye_spacing = head_width * 0.15 * props["eye_spacing"]
        eye_z = head_center_z + head_height * (props["eye_level"] - 0.5)
        eye_radius = head_width * 0.06 * eye_scale

        # Right eye
        create_integrated_eye({
            "head": body_name,
            "position": [eye_spacing, eye_y, eye_z],
            "radius": eye_radius,
            "iris_color": eye_color,
            "socket_depth": eye_radius * 0.3,
        })

        # Left eye
        create_integrated_eye({
            "head": body_name,
            "position": [-eye_spacing, eye_y, eye_z],
            "radius": eye_radius,
            "iris_color": eye_color,
            "socket_depth": eye_radius * 0.3,
        })

    if add_face_features and convert_to_mesh:
        # Nose
        nose_z = head_center_z - head_height * 0.1
        create_nose_bump({
            "head": body_name,
            "position": [0, eye_y + head_width * 0.1, nose_z],
            "width": head_width * 0.08,
            "height": head_width * 0.1,
        })

        # Mouth
        mouth_z = head_center_z - head_height * 0.25
        create_mouth_opening({
            "head": body_name,
            "position": [0, eye_y, mouth_z],
            "width": head_width * 0.15,
            "depth": head_width * 0.02,
        })

    # Add cartoon outline if requested
    if add_outline and convert_to_mesh and style in ["cartoon", "chibi"]:
        add_cartoon_outline({
            "name": body_name,
            "thickness": head_height * 0.01,
        })

    return {
        "name": name,
        "body": body_name,
        "style": style,
        "height": height,
        "head_height": head_height,
        "proportions": props["name"],
    }


def _create_metaball_body(name: str, head_height: float, props: Dict, style: str) -> None:
    """Internal function to create metaball body structure."""
    h = head_height
    total_h = h * props["total_heads"]

    # Resolution based on style (cartoon needs less detail)
    resolution = 0.08 if style == "realistic" else 0.1

    # Create metaball object
    create_metaball_object({
        "name": name,
        "resolution": resolution,
        "location": [0, 0, 0],
    })

    # Head - slightly elliptical, wider than tall
    head_z = total_h - h * 0.5
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, head_z],
        "radius": h * 0.5,
        "size_x": props["head_width"],
        "size_y": props["head_width"] * 1.1,  # Slightly deeper
        "size_z": 1.0,
        "stiffness": 2.0,
    })

    # Neck
    neck_z = total_h - h * 1.1
    add_metaball_element({
        "name": name,
        "type": "CAPSULE",
        "location": [0, 0, neck_z],
        "radius": h * 0.12,
        "size_z": 0.25,
        "stiffness": 3.0,
    })

    # Torso - chest
    torso_start = total_h - h * 1.3
    chest_z = torso_start
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, chest_z],
        "radius": h * 0.35,
        "size_x": props["shoulder_width"] * 0.35,
        "size_y": 0.6,
        "size_z": 0.7,
        "stiffness": 2.0,
    })

    # Torso - waist (narrower)
    waist_z = chest_z - h * 0.5
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, waist_z],
        "radius": h * 0.25,
        "size_x": 0.9,
        "size_y": 0.5,
        "size_z": 0.6,
        "stiffness": 2.5,
    })

    # Torso - hips (wider)
    hip_z = waist_z - h * 0.4
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, hip_z],
        "radius": h * 0.28,
        "size_x": props["hip_width"] * 0.35,
        "size_y": 0.6,
        "size_z": 0.5,
        "stiffness": 2.0,
    })

    # Arms
    shoulder_x = h * props["shoulder_width"] * 0.22
    shoulder_z = chest_z + h * 0.1
    arm_radius = h * 0.1

    for side in [1, -1]:
        # Upper arm
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * shoulder_x, 0, shoulder_z - h * 0.3],
            "radius": arm_radius,
            "size_z": 0.5,
            "stiffness": 2.5,
        })

        # Forearm
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * (shoulder_x + h * 0.15), 0, shoulder_z - h * 0.7],
            "radius": arm_radius * 0.85,
            "size_z": 0.45,
            "stiffness": 2.5,
        })

        # Hand (small ball)
        add_metaball_element({
            "name": name,
            "type": "BALL",
            "location": [side * (shoulder_x + h * 0.25), 0, shoulder_z - h * 1.0],
            "radius": arm_radius * 0.9,
            "stiffness": 2.0,
        })

    # Legs
    leg_x = h * 0.15
    leg_start_z = hip_z - h * 0.2
    leg_radius = h * 0.13

    for side in [1, -1]:
        # Upper leg (thigh)
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * leg_x, 0, leg_start_z - h * 0.5],
            "radius": leg_radius,
            "size_z": 0.6,
            "stiffness": 2.0,
        })

        # Lower leg
        add_metaball_element({
            "name": name,
            "type": "CAPSULE",
            "location": [side * leg_x, 0, leg_start_z - h * 1.2],
            "radius": leg_radius * 0.75,
            "size_z": 0.55,
            "stiffness": 2.0,
        })

        # Foot
        add_metaball_element({
            "name": name,
            "type": "ELLIPSOID",
            "location": [side * leg_x, h * 0.08, leg_start_z - h * 1.7],
            "radius": h * 0.08,
            "size_x": 0.6,
            "size_y": 1.5,
            "size_z": 0.4,
            "stiffness": 2.5,
        })


def create_head_only(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create just a head with face features.

    params:
        name: head name (default "Head")
        style: 'realistic', 'cartoon', 'chibi' (default 'cartoon')
        size: head height (default 0.25)
        skin_color: [r, g, b] skin color
        eye_color: [r, g, b] iris color
        add_eyes: create eyes (default True)
        add_features: create nose/mouth (default True)
    """
    name = params.get("name", "Head")
    style = params.get("style", "cartoon").lower()
    size = params.get("size", 0.25)
    skin_color = params.get("skin_color", [0.85, 0.65, 0.55, 1.0])
    eye_color = params.get("eye_color", [0.3, 0.5, 0.7, 1.0])
    add_eyes = params.get("add_eyes", True)
    add_features = params.get("add_features", True)

    props = CARTOON_PROPORTIONS if style in ["cartoon", "chibi"] else REALISTIC_PROPORTIONS

    # Create metaball head
    create_metaball_object({
        "name": name,
        "resolution": 0.06,
    })

    # Main head shape
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, 0, 0],
        "radius": size * 0.5,
        "size_x": props["head_width"],
        "size_y": props["head_width"] * 1.1,
        "size_z": 1.0,
        "stiffness": 2.0,
    })

    # Jaw/chin (slightly lower and forward)
    add_metaball_element({
        "name": name,
        "type": "ELLIPSOID",
        "location": [0, size * 0.1, -size * 0.2],
        "radius": size * 0.2,
        "size_x": 0.8,
        "size_y": 0.7,
        "size_z": 0.6,
        "stiffness": 2.5,
    })

    # Convert to mesh
    convert_metaball_to_mesh({"name": name})

    # Smooth
    mesh_filter({
        "name": name,
        "filter_type": "SMOOTH",
        "strength": 0.3,
        "iterations": 2,
    })

    # Apply material
    if style in ["cartoon", "chibi"]:
        mat_name = f"{name}_Mat"
        shadow_color = [c * 0.6 for c in skin_color[:3]] + [1.0]
        create_toon_shader({
            "name": mat_name,
            "base_color": skin_color,
            "shadow_color": shadow_color,
        })
    else:
        mat_name = f"{name}_Mat"
        create_skin_shader({
            "name": mat_name,
            "base_color": skin_color,
        })

    assign_material({
        "object_name": name,
        "material_name": mat_name,
    })

    # Add eyes
    if add_eyes:
        eye_scale = props.get("eye_size", 1.0)
        eye_spacing = size * 0.15
        eye_z = size * (props["eye_level"] - 0.5)
        eye_y = size * 0.4
        eye_radius = size * 0.06 * eye_scale

        for side in [1, -1]:
            side_name = "R" if side > 0 else "L"
            create_integrated_eye({
                "head": name,
                "position": [side * eye_spacing, eye_y, eye_z],
                "radius": eye_radius,
                "iris_color": eye_color,
            })

    # Add features
    if add_features:
        nose_z = -size * 0.1
        nose_y = size * 0.45
        create_nose_bump({
            "head": name,
            "position": [0, nose_y, nose_z],
            "width": size * 0.08,
            "height": size * 0.08,
        })

        mouth_z = -size * 0.25
        create_mouth_opening({
            "head": name,
            "position": [0, nose_y - size * 0.05, mouth_z],
            "width": size * 0.12,
        })

    return {
        "name": name,
        "style": style,
        "size": size,
    }


def list_available_templates(params: Dict[str, Any]) -> Dict[str, Any]:
    """List available character templates and their descriptions."""
    return {
        "templates": [
            {
                "name": "create_character_from_template",
                "description": "Create a complete humanoid character",
                "styles": ["realistic", "cartoon", "chibi"],
                "params": ["name", "style", "height", "skin_color", "eye_color", "add_eyes", "add_outline"],
            },
            {
                "name": "create_head_only",
                "description": "Create just a head with face features",
                "styles": ["realistic", "cartoon", "chibi"],
                "params": ["name", "style", "size", "skin_color", "eye_color"],
            },
        ],
        "proportion_presets": [
            {
                "name": "realistic",
                "total_heads": 7.5,
                "description": "Anatomically accurate human proportions",
            },
            {
                "name": "cartoon",
                "total_heads": 4.0,
                "description": "Pixar/Disney style with larger head and eyes",
            },
            {
                "name": "chibi",
                "total_heads": 2.5,
                "description": "Cute anime style with very large head",
            },
        ],
    }


TEMPLATE_HANDLERS = {
    "create_character_from_template": create_character_from_template,
    "create_head_only": create_head_only,
    "list_available_templates": list_available_templates,
}

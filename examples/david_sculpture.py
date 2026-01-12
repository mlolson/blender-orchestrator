"""
Create a character inspired by Michelangelo's David sculpture.

This script uses the new metaball and material tools to create
a classical Renaissance-style figure with marble material.

Run this script in Blender's Python console or Text Editor after
installing the blender_addon.
"""

import bpy
import sys
import os

# Add the addon path if needed
addon_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_path not in sys.path:
    sys.path.append(addon_path)

from blender_addon.handlers.metaballs import (
    create_metaball_object,
    add_metaball_element,
    convert_metaball_to_mesh,
)
from blender_addon.handlers.mesh_editing import (
    mesh_filter,
    add_subdivision_surface,
    sculpt_inflate,
    proportional_edit,
    remesh_object,
)
from blender_addon.handlers.materials import (
    create_material,
    assign_material,
)


def create_marble_material(name="Marble"):
    """Create a classical marble material like the David statue."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get the principled BSDF
    bsdf = nodes.get("Principled BSDF")

    # Marble base color - warm white with slight cream tint
    bsdf.inputs["Base Color"].default_value = (0.95, 0.93, 0.88, 1.0)

    # Subtle subsurface for translucency (marble has some)
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.1
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = 0.1

    # Smooth but not perfectly polished
    bsdf.inputs["Roughness"].default_value = 0.35

    # Add subtle noise texture for marble veining
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)

    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, 0)
    noise.inputs['Scale'].default_value = 15.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.6

    # Color ramp for subtle veining
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-200, 0)
    ramp.color_ramp.elements[0].color = (0.92, 0.90, 0.85, 1.0)  # Slightly darker
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[1].color = (0.98, 0.96, 0.92, 1.0)  # Lighter
    ramp.color_ramp.elements[1].position = 0.6

    # Mix the noise with base color
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.location = (0, 0)
    mix.inputs['Factor'].default_value = 0.3  # Subtle effect
    mix.inputs['A'].default_value = (0.95, 0.93, 0.88, 1.0)

    # Connect nodes
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], mix.inputs['B'])
    links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])

    return mat


def create_david():
    """Create Michelangelo's David using metaballs."""

    print("Creating David sculpture...")

    # Classical proportions: 8 heads tall (idealized Greek/Renaissance)
    head_height = 0.22
    total_height = head_height * 8  # ~1.76m

    # Create metaball object with fine resolution for smooth surface
    create_metaball_object({
        "name": "David",
        "resolution": 0.06,  # Fine resolution for smooth marble
        "location": [0, 0, 0],
    })

    # =========================================
    # HEAD - Idealized classical proportions
    # =========================================
    head_z = total_height - head_height * 0.5

    # Main head/cranium
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, 0, head_z],
        "radius": head_height * 0.48,
        "size_x": 0.85,
        "size_y": 1.0,
        "size_z": 1.0,
        "stiffness": 2.0,
    })

    # Brow ridge
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, head_height * 0.25, head_z + head_height * 0.1],
        "radius": head_height * 0.15,
        "size_x": 2.0,
        "size_y": 0.5,
        "size_z": 0.4,
        "stiffness": 3.0,
    })

    # Nose
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, head_height * 0.35, head_z - head_height * 0.05],
        "radius": head_height * 0.08,
        "size_x": 0.4,
        "size_y": 1.0,
        "size_z": 0.8,
        "stiffness": 3.5,
    })

    # Chin/jaw
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, head_height * 0.15, head_z - head_height * 0.25],
        "radius": head_height * 0.18,
        "size_x": 0.9,
        "size_y": 0.7,
        "size_z": 0.6,
        "stiffness": 2.5,
    })

    # =========================================
    # NECK - Strong, muscular
    # =========================================
    neck_z = head_z - head_height * 0.6
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [0, 0, neck_z],
        "radius": head_height * 0.25,
        "size_z": 0.4,
        "stiffness": 2.5,
    })

    # Trapezius muscles (neck to shoulder)
    for side in [1, -1]:
        add_metaball_element({
            "name": "David",
            "type": "ELLIPSOID",
            "location": [side * head_height * 0.4, -head_height * 0.1, neck_z - head_height * 0.2],
            "radius": head_height * 0.2,
            "size_x": 1.2,
            "size_y": 0.8,
            "size_z": 0.6,
            "stiffness": 2.5,
        })

    # =========================================
    # TORSO - Muscular, athletic build
    # =========================================
    chest_z = total_height - head_height * 2.5

    # Chest/pectorals
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, head_height * 0.1, chest_z],
        "radius": head_height * 0.7,
        "size_x": 1.3,
        "size_y": 0.7,
        "size_z": 0.8,
        "stiffness": 2.0,
    })

    # Individual pectorals for definition
    for side in [1, -1]:
        add_metaball_element({
            "name": "David",
            "type": "ELLIPSOID",
            "location": [side * head_height * 0.35, head_height * 0.2, chest_z + head_height * 0.1],
            "radius": head_height * 0.25,
            "size_x": 1.0,
            "size_y": 0.8,
            "size_z": 0.6,
            "stiffness": 2.5,
        })

    # Ribcage
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, 0, chest_z - head_height * 0.5],
        "radius": head_height * 0.55,
        "size_x": 1.1,
        "size_y": 0.75,
        "size_z": 0.9,
        "stiffness": 2.0,
    })

    # Waist (narrower - V-taper)
    waist_z = chest_z - head_height * 1.0
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, 0, waist_z],
        "radius": head_height * 0.4,
        "size_x": 1.0,
        "size_y": 0.65,
        "size_z": 0.7,
        "stiffness": 2.5,
    })

    # Abdominals (subtle definition)
    for i in range(3):
        ab_z = chest_z - head_height * (0.4 + i * 0.25)
        add_metaball_element({
            "name": "David",
            "type": "ELLIPSOID",
            "location": [0, head_height * 0.15, ab_z],
            "radius": head_height * 0.15,
            "size_x": 1.5,
            "size_y": 0.5,
            "size_z": 0.4,
            "stiffness": 3.5,
        })

    # Hips/pelvis
    hip_z = waist_z - head_height * 0.4
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, 0, hip_z],
        "radius": head_height * 0.5,
        "size_x": 1.1,
        "size_y": 0.8,
        "size_z": 0.6,
        "stiffness": 2.0,
    })

    # =========================================
    # ARMS - Contrapposto pose (right arm down, left up)
    # =========================================
    shoulder_z = chest_z + head_height * 0.3

    # RIGHT ARM - hanging down at side
    # Deltoid
    add_metaball_element({
        "name": "David",
        "type": "BALL",
        "location": [head_height * 0.75, 0, shoulder_z],
        "radius": head_height * 0.22,
        "stiffness": 2.0,
    })

    # Upper arm (bicep/tricep)
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.85, 0, shoulder_z - head_height * 0.6],
        "radius": head_height * 0.16,
        "size_z": 0.7,
        "stiffness": 2.0,
    })

    # Forearm
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.9, head_height * 0.1, shoulder_z - head_height * 1.3],
        "radius": head_height * 0.12,
        "size_z": 0.6,
        "stiffness": 2.0,
    })

    # Hand (simplified)
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [head_height * 0.95, head_height * 0.15, shoulder_z - head_height * 1.8],
        "radius": head_height * 0.1,
        "size_x": 0.6,
        "size_y": 0.4,
        "size_z": 1.0,
        "stiffness": 2.5,
    })

    # LEFT ARM - bent, hand near face (iconic pose)
    # Deltoid
    add_metaball_element({
        "name": "David",
        "type": "BALL",
        "location": [-head_height * 0.75, 0, shoulder_z],
        "radius": head_height * 0.22,
        "stiffness": 2.0,
    })

    # Upper arm (angled up toward shoulder)
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.7, head_height * 0.2, shoulder_z - head_height * 0.3],
        "radius": head_height * 0.16,
        "size_z": 0.5,
        "rotation": [0.5, 0, 0.3],  # Angled
        "stiffness": 2.0,
    })

    # Forearm (bent toward head)
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.45, head_height * 0.35, shoulder_z + head_height * 0.1],
        "radius": head_height * 0.12,
        "size_z": 0.5,
        "stiffness": 2.0,
    })

    # Hand near shoulder/chest
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [-head_height * 0.25, head_height * 0.4, shoulder_z + head_height * 0.3],
        "radius": head_height * 0.1,
        "size_x": 0.6,
        "size_y": 0.4,
        "size_z": 1.0,
        "stiffness": 2.5,
    })

    # =========================================
    # LEGS - Contrapposto (weight on right leg)
    # =========================================
    leg_start_z = hip_z - head_height * 0.3

    # RIGHT LEG - straight, weight-bearing
    # Thigh
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.25, 0, leg_start_z - head_height * 0.8],
        "radius": head_height * 0.22,
        "size_z": 1.0,
        "stiffness": 2.0,
    })

    # Knee
    add_metaball_element({
        "name": "David",
        "type": "BALL",
        "location": [head_height * 0.25, head_height * 0.05, leg_start_z - head_height * 1.6],
        "radius": head_height * 0.15,
        "stiffness": 2.5,
    })

    # Calf
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.25, -head_height * 0.05, leg_start_z - head_height * 2.3],
        "radius": head_height * 0.14,
        "size_z": 0.8,
        "stiffness": 2.0,
    })

    # Ankle/foot
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [head_height * 0.25, head_height * 0.1, leg_start_z - head_height * 3.0],
        "radius": head_height * 0.1,
        "size_x": 0.7,
        "size_y": 1.5,
        "size_z": 0.4,
        "stiffness": 2.5,
    })

    # LEFT LEG - relaxed, slightly bent
    # Thigh (slightly angled)
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.3, head_height * 0.1, leg_start_z - head_height * 0.8],
        "radius": head_height * 0.21,
        "size_z": 0.95,
        "stiffness": 2.0,
    })

    # Knee (slightly forward)
    add_metaball_element({
        "name": "David",
        "type": "BALL",
        "location": [-head_height * 0.35, head_height * 0.15, leg_start_z - head_height * 1.55],
        "radius": head_height * 0.14,
        "stiffness": 2.5,
    })

    # Calf
    add_metaball_element({
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.35, 0, leg_start_z - head_height * 2.25],
        "radius": head_height * 0.13,
        "size_z": 0.75,
        "stiffness": 2.0,
    })

    # Ankle/foot (toe pointing slightly out)
    add_metaball_element({
        "name": "David",
        "type": "ELLIPSOID",
        "location": [-head_height * 0.4, head_height * 0.15, leg_start_z - head_height * 2.9],
        "radius": head_height * 0.1,
        "size_x": 0.7,
        "size_y": 1.5,
        "size_z": 0.4,
        "stiffness": 2.5,
    })

    # =========================================
    # Convert to mesh and refine
    # =========================================
    print("Converting to mesh...")
    convert_metaball_to_mesh({"name": "David"})

    # Smooth the surface
    print("Smoothing surface...")
    mesh_filter({
        "name": "David",
        "filter_type": "SMOOTH",
        "strength": 0.3,
        "iterations": 2,
    })

    # Add subdivision for smooth marble appearance
    add_subdivision_surface({
        "name": "David",
        "levels": 2,
        "render_levels": 3,
    })

    # =========================================
    # Apply marble material
    # =========================================
    print("Applying marble material...")
    marble_mat = create_marble_material("CarraraMarble")

    obj = bpy.data.objects.get("David")
    if obj:
        if len(obj.material_slots) == 0:
            obj.data.materials.append(marble_mat)
        else:
            obj.material_slots[0].material = marble_mat

    # =========================================
    # Position and rotate for display
    # =========================================
    if obj:
        # Slight rotation to show contrapposto
        obj.rotation_euler[2] = 0.15  # Slight turn

    print("David sculpture created successfully!")
    print(f"Height: {total_height:.2f}m ({total_height/head_height:.1f} heads)")

    return {"name": "David", "height": total_height}


# Run if executed directly in Blender
if __name__ == "__main__":
    # Clear existing objects (optional)
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.object.delete()

    create_david()

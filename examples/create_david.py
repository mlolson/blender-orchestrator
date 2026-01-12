#!/usr/bin/env python3
"""
Create Michelangelo's David sculpture via Blender MCP HTTP server.

Prerequisites:
1. Blender running with the addon installed and server started
   IMPORTANT: If you've updated the addon code, you must restart Blender
   or disable/re-enable the addon for changes to take effect!
2. httpx installed: pip install httpx

Usage:
    python create_david.py

The sculpture uses metaballs for organic forms with classical 8-head
proportions and contrapposto pose. After conversion, it applies a
Carrara marble material.
"""

import httpx
import sys


def send_command(action: str, params: dict) -> dict:
    """Send a command to Blender's HTTP server."""
    try:
        response = httpx.post(
            "http://localhost:8765",
            json={"action": action, "params": params},
            timeout=30.0,
        )
        result = response.json()
        if not result.get("success"):
            print(f"  Error: {result.get('error', 'Unknown error')}")
            return {}
        return result.get("result", {})
    except httpx.ConnectError:
        print("ERROR: Cannot connect to Blender. Make sure:")
        print("  1. Blender is running")
        print("  2. The MCP addon is installed")
        print("  3. Server is started (check addon panel)")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        return {}


def create_david():
    """Create Michelangelo's David sculpture."""

    print("=" * 50)
    print("  Creating Michelangelo's David Sculpture")
    print("=" * 50)

    # Clear any existing David object
    send_command("delete_object", {"name": "David"})
    send_command("delete_object", {"name": "David.001"})

    # Classical proportions: 8 heads tall (idealized Renaissance)
    head_height = 0.22
    total_height = head_height * 8  # ~1.76m

    # =========================================
    # Create metaball base
    # =========================================
    print("\n[1/6] Creating metaball structure...")

    send_command("create_metaball_object", {
        "name": "David",
        "resolution": 0.06,
        "threshold": 0.6,  # Must be > 0 for surface to appear
        "location": [0, 0, 0],
    })

    # =========================================
    # HEAD
    # =========================================
    print("[2/6] Sculpting head and face...")
    head_z = total_height - head_height * 0.5

    # Main cranium
    send_command("add_metaball_element", {
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
    send_command("add_metaball_element", {
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
    send_command("add_metaball_element", {
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
    send_command("add_metaball_element", {
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, head_height * 0.15, head_z - head_height * 0.25],
        "radius": head_height * 0.18,
        "size_x": 0.9,
        "size_y": 0.7,
        "size_z": 0.6,
        "stiffness": 2.5,
    })

    # Neck
    neck_z = head_z - head_height * 0.6
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [0, 0, neck_z],
        "radius": head_height * 0.25,
        "size_z": 0.4,
        "stiffness": 2.5,
    })

    # =========================================
    # TORSO - Athletic, muscular
    # =========================================
    print("[3/6] Building muscular torso...")
    chest_z = total_height - head_height * 2.5

    # Main chest
    send_command("add_metaball_element", {
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, head_height * 0.1, chest_z],
        "radius": head_height * 0.7,
        "size_x": 1.3,
        "size_y": 0.7,
        "size_z": 0.8,
        "stiffness": 2.0,
    })

    # Pectorals
    for side in [1, -1]:
        send_command("add_metaball_element", {
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
    send_command("add_metaball_element", {
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, 0, chest_z - head_height * 0.5],
        "radius": head_height * 0.55,
        "size_x": 1.1,
        "size_y": 0.75,
        "size_z": 0.9,
        "stiffness": 2.0,
    })

    # Waist
    waist_z = chest_z - head_height * 1.0
    send_command("add_metaball_element", {
        "name": "David",
        "type": "ELLIPSOID",
        "location": [0, 0, waist_z],
        "radius": head_height * 0.4,
        "size_x": 1.0,
        "size_y": 0.65,
        "size_z": 0.7,
        "stiffness": 2.5,
    })

    # Abdominals
    for i in range(3):
        ab_z = chest_z - head_height * (0.4 + i * 0.25)
        send_command("add_metaball_element", {
            "name": "David",
            "type": "ELLIPSOID",
            "location": [0, head_height * 0.15, ab_z],
            "radius": head_height * 0.15,
            "size_x": 1.5,
            "size_y": 0.5,
            "size_z": 0.4,
            "stiffness": 3.5,
        })

    # Hips
    hip_z = waist_z - head_height * 0.4
    send_command("add_metaball_element", {
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
    # ARMS - Contrapposto pose
    # =========================================
    print("[4/6] Forming arms in contrapposto pose...")
    shoulder_z = chest_z + head_height * 0.3

    # RIGHT ARM - hanging down
    send_command("add_metaball_element", {
        "name": "David",
        "type": "BALL",
        "location": [head_height * 0.75, 0, shoulder_z],
        "radius": head_height * 0.22,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.85, 0, shoulder_z - head_height * 0.6],
        "radius": head_height * 0.16,
        "size_z": 0.7,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.9, head_height * 0.1, shoulder_z - head_height * 1.3],
        "radius": head_height * 0.12,
        "size_z": 0.6,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "ELLIPSOID",
        "location": [head_height * 0.95, head_height * 0.15, shoulder_z - head_height * 1.8],
        "radius": head_height * 0.1,
        "size_x": 0.6,
        "size_y": 0.4,
        "size_z": 1.0,
        "stiffness": 2.5,
    })

    # LEFT ARM - bent toward shoulder
    send_command("add_metaball_element", {
        "name": "David",
        "type": "BALL",
        "location": [-head_height * 0.75, 0, shoulder_z],
        "radius": head_height * 0.22,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.65, head_height * 0.15, shoulder_z - head_height * 0.35],
        "radius": head_height * 0.16,
        "size_z": 0.55,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.45, head_height * 0.35, shoulder_z + head_height * 0.1],
        "radius": head_height * 0.12,
        "size_z": 0.5,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
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
    # LEGS - Weight on right leg
    # =========================================
    print("[5/6] Sculpting legs...")
    leg_start_z = hip_z - head_height * 0.3

    # RIGHT LEG - straight, weight-bearing
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.25, 0, leg_start_z - head_height * 0.8],
        "radius": head_height * 0.22,
        "size_z": 1.0,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "BALL",
        "location": [head_height * 0.25, head_height * 0.05, leg_start_z - head_height * 1.6],
        "radius": head_height * 0.15,
        "stiffness": 2.5,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [head_height * 0.25, -head_height * 0.05, leg_start_z - head_height * 2.3],
        "radius": head_height * 0.14,
        "size_z": 0.8,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "ELLIPSOID",
        "location": [head_height * 0.25, head_height * 0.1, leg_start_z - head_height * 3.0],
        "radius": head_height * 0.1,
        "size_x": 0.7,
        "size_y": 1.5,
        "size_z": 0.4,
        "stiffness": 2.5,
    })

    # LEFT LEG - relaxed
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.3, head_height * 0.1, leg_start_z - head_height * 0.8],
        "radius": head_height * 0.21,
        "size_z": 0.95,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "BALL",
        "location": [-head_height * 0.35, head_height * 0.15, leg_start_z - head_height * 1.55],
        "radius": head_height * 0.14,
        "stiffness": 2.5,
    })
    send_command("add_metaball_element", {
        "name": "David",
        "type": "CAPSULE",
        "location": [-head_height * 0.35, 0, leg_start_z - head_height * 2.25],
        "radius": head_height * 0.13,
        "size_z": 0.75,
        "stiffness": 2.0,
    })
    send_command("add_metaball_element", {
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
    # Finalize
    # =========================================
    print("[6/6] Converting to mesh and applying marble material...")

    # Convert to mesh and get the actual object name
    result = send_command("convert_metaball_to_mesh", {"name": "David"})
    mesh_name = result.get("name", "David") if result else "David"
    print(f"  Converted to mesh: {mesh_name}")

    # Smooth
    send_command("mesh_filter", {
        "name": mesh_name,
        "filter_type": "SMOOTH",
        "strength": 0.3,
        "iterations": 2,
    })

    # Add subdivision
    send_command("add_subdivision_surface", {
        "name": mesh_name,
        "levels": 2,
        "render_levels": 3,
    })

    # Create marble-like material (white/cream with low roughness)
    send_command("create_material", {
        "name": "CarraraMarble",
        "color": [0.95, 0.93, 0.88, 1.0],
        "roughness": 0.35,
        "metallic": 0.0,
    })

    # Assign material
    send_command("assign_material", {
        "object_name": mesh_name,
        "material_name": "CarraraMarble",
    })

    # Rotate slightly for better view
    send_command("rotate_object", {
        "name": mesh_name,
        "rotation": [0, 0, 8.6],  # ~8.6 degrees
    })

    print("\n" + "=" * 50)
    print("  David sculpture created successfully!")
    print(f"  Height: {total_height:.2f}m (8 heads)")
    print("  Style: Classical Renaissance contrapposto")
    print("=" * 50)


if __name__ == "__main__":
    create_david()

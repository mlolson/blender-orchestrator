"""Handlers for material operations."""

import bpy
from typing import Any, Dict, List, Optional
from ..utils.serializers import serialize_material


def create_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new material with Principled BSDF."""
    name = params.get("name", "Material")
    color = params.get("color", [0.8, 0.8, 0.8, 1.0])  # RGBA
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.5)
    specular = params.get("specular", 0.5)

    # Ensure color has alpha
    if len(color) == 3:
        color = list(color) + [1.0]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Get the Principled BSDF node
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        # Specular input name changed in Blender 4.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular

    return serialize_material(mat)


def assign_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Assign a material to an object."""
    object_name = params["object_name"]
    material_name = params["material_name"]
    slot_index = params.get("slot_index", 0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        raise ValueError(f"Object '{object_name}' not found")

    mat = bpy.data.materials.get(material_name)
    if not mat:
        raise ValueError(f"Material '{material_name}' not found")

    # Ensure object has material slots
    if len(obj.material_slots) == 0:
        obj.data.materials.append(mat)
    else:
        if slot_index >= len(obj.material_slots):
            obj.data.materials.append(mat)
        else:
            obj.material_slots[slot_index].material = mat

    return {
        "object": object_name,
        "material": material_name,
        "slot_index": slot_index,
    }


def modify_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify an existing material's properties."""
    material_name = params["material_name"]

    mat = bpy.data.materials.get(material_name)
    if not mat:
        raise ValueError(f"Material '{material_name}' not found")

    if not mat.use_nodes:
        mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        raise ValueError("Material does not have a Principled BSDF node")

    if "color" in params:
        color = params["color"]
        if len(color) == 3:
            color = list(color) + [1.0]
        bsdf.inputs["Base Color"].default_value = color

    if "metallic" in params:
        bsdf.inputs["Metallic"].default_value = params["metallic"]

    if "roughness" in params:
        bsdf.inputs["Roughness"].default_value = params["roughness"]

    if "specular" in params:
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = params["specular"]
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = params["specular"]

    return serialize_material(mat)


def list_materials(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all materials in the file."""
    materials = []
    for mat in bpy.data.materials:
        materials.append(serialize_material(mat))

    return {"materials": materials, "count": len(materials)}


def delete_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a material."""
    material_name = params["material_name"]

    mat = bpy.data.materials.get(material_name)
    if not mat:
        raise ValueError(f"Material '{material_name}' not found")

    deleted_name = mat.name
    bpy.data.materials.remove(mat)

    return {"deleted": deleted_name}


def create_and_assign_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a material and assign it to an object in one step."""
    object_name = params["object_name"]
    name = params.get("name", "Material")
    color = params.get("color", [0.8, 0.8, 0.8, 1.0])
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.5)

    # Create material
    mat_result = create_material({
        "name": name,
        "color": color,
        "metallic": metallic,
        "roughness": roughness,
    })

    # Assign to object
    assign_result = assign_material({
        "object_name": object_name,
        "material_name": mat_result["name"],
    })

    return {
        "material": mat_result,
        "assignment": assign_result,
    }


MATERIAL_HANDLERS = {
    "create_material": create_material,
    "assign_material": assign_material,
    "modify_material": modify_material,
    "list_materials": list_materials,
    "delete_material": delete_material,
    "create_and_assign_material": create_and_assign_material,
}

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
    all_slots = params.get("all_slots", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        raise ValueError(f"Object '{object_name}' not found")

    mat = bpy.data.materials.get(material_name)
    if not mat:
        raise ValueError(f"Material '{material_name}' not found")

    if all_slots:
        # Replace material on every existing slot
        if len(obj.material_slots) == 0:
            obj.data.materials.append(mat)
            slots_replaced = 1
        else:
            slots_replaced = len(obj.material_slots)
            for i in range(slots_replaced):
                obj.material_slots[i].material = mat
        return {
            "object": object_name,
            "material": material_name,
            "all_slots": True,
            "slots_replaced": slots_replaced,
        }

    # Single slot assignment (original behavior)
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


def create_toon_shader(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a cel-shaded toon material for Pixar/cartoon style.

    Uses Shader to RGB to capture lighting and a color ramp
    to create stepped/quantized shading.

    params:
        name: material name (default "ToonMaterial")
        base_color: [r, g, b, a] lit/highlight color (default warm skin tone)
        shadow_color: [r, g, b, a] shadow color (default darker skin tone)
        steps: number of shading steps (2-5, default 3)
        outline: whether to add outline via solidify modifier (default False)
        outline_thickness: thickness of outline (default 0.02)
    """
    name = params.get("name", "ToonMaterial")
    base_color = params.get("base_color", [0.9, 0.7, 0.6, 1.0])
    shadow_color = params.get("shadow_color", [0.5, 0.35, 0.3, 1.0])
    steps = params.get("steps", 3)

    # Ensure RGBA
    if len(base_color) == 3:
        base_color = list(base_color) + [1.0]
    if len(shadow_color) == 3:
        shadow_color = list(shadow_color) + [1.0]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # Diffuse BSDF for capturing light
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-200, 100)
    diffuse.inputs['Color'].default_value = (1, 1, 1, 1)  # White to capture pure light

    # Shader to RGB - converts lighting to color values
    shader_to_rgb = nodes.new('ShaderNodeShaderToRGB')
    shader_to_rgb.location = (0, 100)

    # Color ramp for stepped shading
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (200, 100)

    # Configure color ramp for stepped shading
    ramp = color_ramp.color_ramp
    ramp.interpolation = 'CONSTANT'

    # Remove existing elements and create new ones
    while len(ramp.elements) > 1:
        ramp.elements.remove(ramp.elements[0])

    # Create stepped gradient from shadow to base color
    step_size = 1.0 / steps
    for i in range(steps):
        pos = i * step_size + 0.01  # Slight offset to avoid edge issues
        if i == 0:
            ramp.elements[0].position = pos
            elem = ramp.elements[0]
        else:
            elem = ramp.elements.new(pos)

        # Interpolate between shadow and base color
        t = i / (steps - 1) if steps > 1 else 1
        elem.color = [
            shadow_color[j] + t * (base_color[j] - shadow_color[j])
            for j in range(4)
        ]

    # Mix shader to combine with emission for more control
    mix_rgb = nodes.new('ShaderNodeMix')
    mix_rgb.data_type = 'RGBA'
    mix_rgb.location = (400, 100)
    mix_rgb.inputs['Factor'].default_value = 0.0  # Use color ramp output directly

    # Emission shader for flat look (optional)
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (400, -100)
    emission.inputs['Strength'].default_value = 0.0  # Disabled by default

    # Link nodes
    links.new(diffuse.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    links.new(shader_to_rgb.outputs['Color'], color_ramp.inputs['Fac'])

    # For now, output color ramp directly as emission for flat look
    # This gives the classic toon shader appearance
    final_emission = nodes.new('ShaderNodeEmission')
    final_emission.location = (400, 0)
    final_emission.inputs['Strength'].default_value = 1.0

    links.new(color_ramp.outputs['Color'], final_emission.inputs['Color'])
    links.new(final_emission.outputs['Emission'], output.inputs['Surface'])

    return serialize_material(mat)


def create_skin_shader(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a realistic skin shader with subsurface scattering.

    Subsurface scattering simulates light penetrating and scattering
    within the skin, giving it a natural, fleshy appearance.

    params:
        name: material name (default "SkinMaterial")
        base_color: [r, g, b, a] skin color
        subsurface: subsurface scattering amount (0-1, default 0.3)
        subsurface_radius: [r, g, b] scattering radius per channel
                           (default [1.0, 0.2, 0.1] - red scatters most)
        subsurface_color: [r, g, b, a] subsurface color (default reddish)
        roughness: surface roughness (default 0.4)
        specular: specular amount (default 0.5)
    """
    name = params.get("name", "SkinMaterial")
    base_color = params.get("base_color", [0.8, 0.6, 0.5, 1.0])
    subsurface = params.get("subsurface", 0.3)
    subsurface_radius = params.get("subsurface_radius", [1.0, 0.2, 0.1])
    subsurface_color = params.get("subsurface_color", [0.9, 0.4, 0.3, 1.0])
    roughness = params.get("roughness", 0.4)
    specular = params.get("specular", 0.5)

    # Ensure RGBA
    if len(base_color) == 3:
        base_color = list(base_color) + [1.0]
    if len(subsurface_color) == 3:
        subsurface_color = list(subsurface_color) + [1.0]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness

        # Subsurface scattering (Blender 4.0+ uses Subsurface Weight)
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = subsurface
        elif "Subsurface" in bsdf.inputs:
            bsdf.inputs["Subsurface"].default_value = subsurface

        # Subsurface radius
        if "Subsurface Radius" in bsdf.inputs:
            bsdf.inputs["Subsurface Radius"].default_value = subsurface_radius

        # Subsurface color (for versions that support it)
        if "Subsurface Color" in bsdf.inputs:
            bsdf.inputs["Subsurface Color"].default_value = subsurface_color

        # Specular (handle Blender 4.0+ naming)
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular

    return serialize_material(mat)


def create_eye_shader(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a realistic eye material with iris, pupil, and cornea.

    Creates a shader with:
    - Dark pupil center
    - Colored iris ring
    - Clear, glossy cornea with refraction

    params:
        name: material name (default "EyeMaterial")
        iris_color: [r, g, b, a] iris color (default blue)
        pupil_size: pupil radius relative to iris (0-1, default 0.3)
        iris_detail: amount of iris detail/texture (0-1, default 0.5)
        cornea_ior: index of refraction for cornea (default 1.376)
        wetness: eye wetness/glossiness (default 0.95)
    """
    name = params.get("name", "EyeMaterial")
    iris_color = params.get("iris_color", [0.2, 0.4, 0.7, 1.0])
    pupil_size = params.get("pupil_size", 0.3)
    iris_detail = params.get("iris_detail", 0.5)
    cornea_ior = params.get("cornea_ior", 1.376)
    wetness = params.get("wetness", 0.95)

    if len(iris_color) == 3:
        iris_color = list(iris_color) + [1.0]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get existing nodes
    bsdf = nodes.get("Principled BSDF")
    output = nodes.get("Material Output")

    # Texture coordinate for iris pattern
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)

    # Mapping for centering
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-600, 0)
    mapping.inputs['Location'].default_value = (0.5, 0.5, 0)

    # Gradient texture for radial pattern
    gradient = nodes.new('ShaderNodeTexGradient')
    gradient.gradient_type = 'SPHERICAL'
    gradient.location = (-400, 0)

    # Color ramp for pupil and iris
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-200, 0)

    # Configure color ramp: black pupil -> iris color -> white edge
    ramp = color_ramp.color_ramp
    ramp.elements[0].position = 0.0
    ramp.elements[0].color = (0, 0, 0, 1)  # Black pupil

    # Add iris color stop
    iris_elem = ramp.elements.new(pupil_size)
    iris_elem.color = iris_color

    ramp.elements[1].position = 0.7
    ramp.elements[1].color = iris_color

    # Optional noise for iris detail
    if iris_detail > 0:
        noise = nodes.new('ShaderNodeTexNoise')
        noise.location = (-400, -200)
        noise.inputs['Scale'].default_value = 50.0
        noise.inputs['Detail'].default_value = 8.0

        mix_detail = nodes.new('ShaderNodeMix')
        mix_detail.data_type = 'RGBA'
        mix_detail.location = (0, -100)
        mix_detail.inputs['Factor'].default_value = iris_detail * 0.3

        links.new(color_ramp.outputs['Color'], mix_detail.inputs['A'])
        links.new(noise.outputs['Fac'], mix_detail.inputs['B'])
        links.new(mix_detail.outputs['Result'], bsdf.inputs['Base Color'])
    else:
        links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])

    # Configure BSDF for glossy eye
    bsdf.inputs['Roughness'].default_value = 1.0 - wetness
    bsdf.inputs['IOR'].default_value = cornea_ior

    # Coat for wet look (Blender 4.0+)
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs['Coat Weight'].default_value = 0.5
        bsdf.inputs['Coat Roughness'].default_value = 0.0

    # Link texture coordinates
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
    links.new(gradient.outputs['Fac'], color_ramp.inputs['Fac'])

    return serialize_material(mat)


def create_cartoon_outline_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a solid black material for cartoon outlines.

    Used with solidify modifier (flip normals) for outline effect.

    params:
        name: material name (default "OutlineMaterial")
        color: [r, g, b, a] outline color (default black)
    """
    name = params.get("name", "OutlineMaterial")
    color = params.get("color", [0.0, 0.0, 0.0, 1.0])

    if len(color) == 3:
        color = list(color) + [1.0]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear and create emission shader for solid color
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (200, 0)

    emission = nodes.new('ShaderNodeEmission')
    emission.location = (0, 0)
    emission.inputs['Color'].default_value = color
    emission.inputs['Strength'].default_value = 1.0

    links.new(emission.outputs['Emission'], output.inputs['Surface'])

    return serialize_material(mat)


def create_glass_shader(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a glass/transparent material.

    params:
        name: material name (default "GlassMaterial")
        color: [r, g, b, a] glass tint color
        ior: index of refraction (default 1.45 for glass)
        roughness: surface roughness (default 0.0 for clear glass)
        transmission: transmission amount (default 1.0)
    """
    name = params.get("name", "GlassMaterial")
    color = params.get("color", [1.0, 1.0, 1.0, 1.0])
    ior = params.get("ior", 1.45)
    roughness = params.get("roughness", 0.0)
    transmission = params.get("transmission", 1.0)

    if len(color) == 3:
        color = list(color) + [1.0]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Enable transparency in EEVEE
    mat.blend_method = 'HASHED'
    mat.shadow_method = 'HASHED'

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["IOR"].default_value = ior

        # Transmission (Blender 4.0+ uses Transmission Weight)
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission

    return serialize_material(mat)


MATERIAL_HANDLERS = {
    "create_material": create_material,
    "assign_material": assign_material,
    "modify_material": modify_material,
    "list_materials": list_materials,
    "delete_material": delete_material,
    "create_and_assign_material": create_and_assign_material,
    # New advanced shaders
    "create_toon_shader": create_toon_shader,
    "create_skin_shader": create_skin_shader,
    "create_eye_shader": create_eye_shader,
    "create_cartoon_outline_material": create_cartoon_outline_material,
    "create_glass_shader": create_glass_shader,
}

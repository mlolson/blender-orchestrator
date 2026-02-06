"""Handlers for applying textures to materials."""

import bpy
import os
import tempfile
import urllib.request
from typing import Any, Dict, Optional
from pathlib import Path
from ..utils.serializers import serialize_material


def apply_texture_to_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a texture image to a material.

    Args:
        params: Dictionary with:
            - material_name: Name of the material to modify
            - texture_path: Path to the texture image file
            - texture_type: Type of texture map (diffuse, normal, roughness, metallic, ao)
            - uv_scale: Optional [x, y] UV scaling
            - strength: Optional strength multiplier (for normal maps)

    Returns:
        Updated material data
    """
    material_name = params.get("material_name")
    texture_path = params.get("texture_path")
    texture_type = params.get("texture_type", "diffuse")
    uv_scale = params.get("uv_scale", [1.0, 1.0])
    strength = params.get("strength", 1.0)

    if not material_name:
        return {"error": "material_name is required"}
    if not texture_path:
        return {"error": "texture_path is required"}

    mat = bpy.data.materials.get(material_name)
    if not mat:
        return {"error": f"Material '{material_name}' not found"}

    if not Path(texture_path).exists():
        return {"error": f"Texture file not found: {texture_path}"}

    # Ensure material uses nodes
    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get or create texture coordinate and mapping nodes
    tex_coord = _get_or_create_node(nodes, 'ShaderNodeTexCoord', 'Texture Coordinate')
    tex_coord.location = (-1000, 0)

    mapping = _get_or_create_node(nodes, 'ShaderNodeMapping', 'Mapping')
    mapping.location = (-800, 0)
    mapping.inputs['Scale'].default_value = (uv_scale[0], uv_scale[1], 1.0)

    # Link tex coord to mapping if not already
    if not mapping.inputs['Vector'].is_linked:
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

    # Load the image
    img = bpy.data.images.load(texture_path, check_existing=True)

    # Create image texture node
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = img
    tex_node.name = f"{texture_type.capitalize()} Texture"

    # Position based on texture type
    y_positions = {
        "diffuse": 300,
        "normal": 100,
        "roughness": -100,
        "metallic": -300,
        "ao": -500,
        "ambient_occlusion": -500,
    }
    tex_node.location = (-400, y_positions.get(texture_type, 0))

    # Link mapping to texture
    links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])

    # Get the Principled BSDF
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        return {"error": "Material does not have a Principled BSDF node"}

    # Connect based on texture type
    if texture_type == "diffuse":
        tex_node.image.colorspace_settings.name = 'sRGB'
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    elif texture_type == "normal":
        tex_node.image.colorspace_settings.name = 'Non-Color'
        # Create normal map node
        normal_map = nodes.new('ShaderNodeNormalMap')
        normal_map.location = (-200, 100)
        normal_map.inputs['Strength'].default_value = strength

        links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])

    elif texture_type == "roughness":
        tex_node.image.colorspace_settings.name = 'Non-Color'
        links.new(tex_node.outputs['Color'], bsdf.inputs['Roughness'])

    elif texture_type == "metallic":
        tex_node.image.colorspace_settings.name = 'Non-Color'
        links.new(tex_node.outputs['Color'], bsdf.inputs['Metallic'])

    elif texture_type in ("ao", "ambient_occlusion"):
        tex_node.image.colorspace_settings.name = 'Non-Color'
        # Mix AO with base color
        mix_node = nodes.new('ShaderNodeMix')
        mix_node.data_type = 'RGBA'
        mix_node.location = (-100, 300)
        mix_node.blend_type = 'MULTIPLY'
        mix_node.inputs['Factor'].default_value = 1.0

        # Reconnect base color through AO
        base_link = None
        for link in bsdf.inputs['Base Color'].links:
            base_link = link.from_socket
            break

        if base_link:
            links.new(base_link, mix_node.inputs['A'])
        links.new(tex_node.outputs['Color'], mix_node.inputs['B'])
        links.new(mix_node.outputs['Result'], bsdf.inputs['Base Color'])

    result = serialize_material(mat)
    result["texture_applied"] = texture_type
    result["texture_path"] = texture_path
    return result


def create_pbr_material_from_textures(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a complete PBR material from texture files.

    Args:
        params: Dictionary with:
            - name: Name for the new material
            - diffuse_path: Path to diffuse/albedo texture
            - normal_path: Optional path to normal map
            - roughness_path: Optional path to roughness map
            - metallic_path: Optional path to metallic map
            - ao_path: Optional path to ambient occlusion map
            - uv_scale: Optional [x, y] UV scaling
            - object_name: Optional object to assign material to

    Returns:
        Created material data
    """
    name = params.get("name", "PBR_Material")
    diffuse_path = params.get("diffuse_path")
    normal_path = params.get("normal_path")
    roughness_path = params.get("roughness_path")
    metallic_path = params.get("metallic_path")
    ao_path = params.get("ao_path")
    uv_scale = params.get("uv_scale", [1.0, 1.0])
    object_name = params.get("object_name")

    if not diffuse_path:
        return {"error": "diffuse_path is required"}

    # Create new material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get the Principled BSDF
    bsdf = nodes.get("Principled BSDF")
    output = nodes.get("Material Output")

    # Position BSDF
    bsdf.location = (200, 0)
    output.location = (500, 0)

    # Create texture coordinate and mapping nodes
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1000, 0)

    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-800, 0)
    mapping.inputs['Scale'].default_value = (uv_scale[0], uv_scale[1], 1.0)

    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

    textures_applied = []

    # Apply diffuse texture
    if diffuse_path and Path(diffuse_path).exists():
        diffuse_tex = _create_texture_node(nodes, links, mapping, diffuse_path, (-400, 300), 'sRGB')
        links.new(diffuse_tex.outputs['Color'], bsdf.inputs['Base Color'])
        textures_applied.append("diffuse")

    # Apply normal map
    if normal_path and Path(normal_path).exists():
        normal_tex = _create_texture_node(nodes, links, mapping, normal_path, (-400, 100), 'Non-Color')
        normal_map = nodes.new('ShaderNodeNormalMap')
        normal_map.location = (-100, 100)
        links.new(normal_tex.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
        textures_applied.append("normal")

    # Apply roughness map
    if roughness_path and Path(roughness_path).exists():
        roughness_tex = _create_texture_node(nodes, links, mapping, roughness_path, (-400, -100), 'Non-Color')
        links.new(roughness_tex.outputs['Color'], bsdf.inputs['Roughness'])
        textures_applied.append("roughness")

    # Apply metallic map
    if metallic_path and Path(metallic_path).exists():
        metallic_tex = _create_texture_node(nodes, links, mapping, metallic_path, (-400, -300), 'Non-Color')
        links.new(metallic_tex.outputs['Color'], bsdf.inputs['Metallic'])
        textures_applied.append("metallic")

    # Apply AO map (multiply with diffuse)
    if ao_path and Path(ao_path).exists():
        ao_tex = _create_texture_node(nodes, links, mapping, ao_path, (-400, -500), 'Non-Color')

        # Find diffuse connection and insert AO multiply
        diffuse_socket = None
        for link in bsdf.inputs['Base Color'].links:
            diffuse_socket = link.from_socket
            break

        if diffuse_socket:
            mix_node = nodes.new('ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.location = (-100, 300)
            mix_node.blend_type = 'MULTIPLY'
            mix_node.inputs['Factor'].default_value = 1.0

            # Disconnect and reconnect through mix
            links.new(diffuse_socket, mix_node.inputs['A'])
            links.new(ao_tex.outputs['Color'], mix_node.inputs['B'])
            links.new(mix_node.outputs['Result'], bsdf.inputs['Base Color'])
        textures_applied.append("ao")

    # Assign to object if specified
    if object_name:
        obj = bpy.data.objects.get(object_name)
        if obj:
            if len(obj.material_slots) == 0:
                obj.data.materials.append(mat)
            else:
                obj.material_slots[0].material = mat

    result = serialize_material(mat)
    result["textures_applied"] = textures_applied
    if object_name:
        result["assigned_to"] = object_name
    return result


def apply_texture_from_url(params: Dict[str, Any]) -> Dict[str, Any]:
    """Download a texture from URL and apply it to a material.

    Args:
        params: Dictionary with:
            - material_name: Name of the material to modify
            - url: URL to download the texture from
            - texture_type: Type of texture map
            - uv_scale: Optional UV scaling

    Returns:
        Updated material data
    """
    url = params.get("url")
    if not url:
        return {"error": "url is required"}

    # Download to temp file
    suffix = ".png"
    url_path = url.split("?")[0]
    if "." in Path(url_path).name:
        suffix = Path(url_path).suffix

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = tmp_file.name
        urllib.request.urlretrieve(url, tmp_path)
    except Exception as e:
        return {"error": f"Failed to download texture: {str(e)}"}

    # Apply the texture
    apply_params = {
        "material_name": params.get("material_name"),
        "texture_path": tmp_path,
        "texture_type": params.get("texture_type", "diffuse"),
        "uv_scale": params.get("uv_scale", [1.0, 1.0]),
        "strength": params.get("strength", 1.0),
    }

    result = apply_texture_to_material(apply_params)

    if "error" not in result:
        result["source_url"] = url

    return result


def create_material_with_texture(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new material with a texture applied.

    Args:
        params: Dictionary with:
            - name: Name for the new material
            - texture_path: Path to the texture image
            - texture_type: Type of texture (default: diffuse)
            - object_name: Optional object to assign material to

    Returns:
        Created material data
    """
    name = params.get("name", "TexturedMaterial")
    texture_path = params.get("texture_path")
    texture_type = params.get("texture_type", "diffuse")
    object_name = params.get("object_name")

    if not texture_path:
        return {"error": "texture_path is required"}

    # Create new material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Apply texture
    result = apply_texture_to_material({
        "material_name": mat.name,
        "texture_path": texture_path,
        "texture_type": texture_type,
        "uv_scale": params.get("uv_scale", [1.0, 1.0]),
    })

    if "error" in result:
        # Clean up material on failure
        bpy.data.materials.remove(mat)
        return result

    # Assign to object if specified
    if object_name:
        obj = bpy.data.objects.get(object_name)
        if obj:
            if len(obj.material_slots) == 0:
                obj.data.materials.append(mat)
            else:
                obj.material_slots[0].material = mat
            result["assigned_to"] = object_name

    return result


def _get_or_create_node(nodes, node_type: str, name: str):
    """Get existing node by name or create new one."""
    for node in nodes:
        if node.name == name:
            return node
    node = nodes.new(node_type)
    node.name = name
    return node


def _create_texture_node(nodes, links, mapping, image_path: str, location: tuple, colorspace: str):
    """Create and configure an image texture node."""
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.location = location
    tex_node.image = bpy.data.images.load(image_path, check_existing=True)
    tex_node.image.colorspace_settings.name = colorspace
    links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
    return tex_node


# Handler registry for texture application
TEXTURE_APPLICATION_HANDLERS = {
    "apply_texture_to_material": apply_texture_to_material,
    "create_pbr_material_from_textures": create_pbr_material_from_textures,
    "apply_texture_from_url": apply_texture_from_url,
    "create_material_with_texture": create_material_with_texture,
    "apply_texture": create_material_with_texture,
}

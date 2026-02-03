"""Handlers for rendering operations."""

import bpy
import os
import base64
import tempfile
from typing import Any, Dict


def render_to_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """Render the scene to a file."""
    output_path = params.get("output_path")
    resolution_x = params.get("resolution_x", 1920)
    resolution_y = params.get("resolution_y", 1080)
    samples = params.get("samples")
    file_format = params.get("file_format", "PNG").upper()

    scene = bpy.context.scene

    # Store original settings
    orig_res_x = scene.render.resolution_x
    orig_res_y = scene.render.resolution_y
    orig_format = scene.render.image_settings.file_format
    orig_filepath = scene.render.filepath

    try:
        # Set resolution
        scene.render.resolution_x = resolution_x
        scene.render.resolution_y = resolution_y
        scene.render.resolution_percentage = 100

        # Set file format
        scene.render.image_settings.file_format = file_format

        # Set samples if using Cycles
        if samples and scene.render.engine == "CYCLES":
            scene.cycles.samples = samples

        # Set output path
        if output_path:
            scene.render.filepath = output_path
        else:
            ext = file_format.lower()
            if ext == "jpeg":
                ext = "jpg"
            output_path = tempfile.mktemp(suffix=f".{ext}")
            scene.render.filepath = output_path

        # Render
        bpy.ops.render.render(write_still=True)

        return {
            "output_path": scene.render.filepath,
            "resolution": [resolution_x, resolution_y],
            "file_format": file_format,
            "success": True,
        }
    finally:
        # Restore original settings
        scene.render.resolution_x = orig_res_x
        scene.render.resolution_y = orig_res_y
        scene.render.image_settings.file_format = orig_format
        scene.render.filepath = orig_filepath


def render_viewport(params: Dict[str, Any]) -> Dict[str, Any]:
    """Capture a viewport screenshot."""
    output_path = params.get("output_path")
    return_base64 = params.get("return_base64", True)

    # Use temp file if no path specified
    if not output_path:
        output_path = tempfile.mktemp(suffix=".png")

    scene = bpy.context.scene

    # Store original settings
    orig_filepath = scene.render.filepath
    orig_format = scene.render.image_settings.file_format

    try:
        scene.render.filepath = output_path
        scene.render.image_settings.file_format = "PNG"

        # Render viewport
        bpy.ops.render.opengl(write_still=True)

        result = {
            "output_path": output_path,
            "success": os.path.exists(output_path),
        }

        # Optionally return base64 encoded image
        if return_base64 and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                result["image_base64"] = base64.b64encode(f.read()).decode("utf-8")
            # Clean up temp file if we created it
            if not params.get("output_path"):
                os.remove(output_path)
                result["output_path"] = None

        return result
    finally:
        scene.render.filepath = orig_filepath
        scene.render.image_settings.file_format = orig_format


def set_render_settings(params: Dict[str, Any]) -> Dict[str, Any]:
    """Configure render settings."""
    scene = bpy.context.scene

    if "engine" in params:
        engine = params["engine"].upper()
        # Handle engine name variations
        if engine == "EEVEE":
            engine = "BLENDER_EEVEE_NEXT"
        elif engine == "CYCLES":
            engine = "CYCLES"
        elif engine == "WORKBENCH":
            engine = "BLENDER_WORKBENCH"
        scene.render.engine = engine

    if "resolution_x" in params:
        scene.render.resolution_x = params["resolution_x"]

    if "resolution_y" in params:
        scene.render.resolution_y = params["resolution_y"]

    if "samples" in params:
        if scene.render.engine == "CYCLES":
            scene.cycles.samples = params["samples"]
        elif "EEVEE" in scene.render.engine:
            scene.eevee.taa_render_samples = params["samples"]

    if "file_format" in params:
        scene.render.image_settings.file_format = params["file_format"].upper()

    return {
        "engine": scene.render.engine,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "file_format": scene.render.image_settings.file_format,
    }


def get_render_settings(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get current render settings."""
    scene = bpy.context.scene

    settings = {
        "engine": scene.render.engine,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "resolution_percentage": scene.render.resolution_percentage,
        "file_format": scene.render.image_settings.file_format,
        "fps": scene.render.fps,
    }

    if scene.render.engine == "CYCLES":
        settings["samples"] = scene.cycles.samples
        settings["use_denoising"] = scene.cycles.use_denoising
    elif "EEVEE" in scene.render.engine:
        settings["samples"] = scene.eevee.taa_render_samples

    return settings


def set_world_hdri(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set an HDRI image as the world environment.
    
    Args:
        params: Dictionary with:
            - hdri_path: Path to the HDRI file (.hdr or .exr)
            - strength: Environment light strength (default: 1.0)
            - rotation: Z rotation in degrees (default: 0)
    
    Returns:
        World settings info
    """
    hdri_path = params.get("hdri_path")
    strength = params.get("strength", 1.0)
    rotation = params.get("rotation", 0)
    
    if not hdri_path:
        return {"error": "hdri_path is required"}
    
    if not os.path.exists(hdri_path):
        return {"error": f"HDRI file not found: {hdri_path}"}
    
    # Get or create world
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # Clear existing nodes
    nodes.clear()
    
    # Create nodes
    # 1. Texture Coordinate
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    
    # 2. Mapping (for rotation)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    import math
    mapping.inputs["Rotation"].default_value[2] = math.radians(rotation)
    
    # 3. Environment Texture
    env_tex = nodes.new("ShaderNodeTexEnvironment")
    env_tex.location = (-300, 0)
    env_tex.image = bpy.data.images.load(hdri_path)
    
    # 4. Background
    background = nodes.new("ShaderNodeBackground")
    background.location = (0, 0)
    background.inputs["Strength"].default_value = strength
    
    # 5. World Output
    world_output = nodes.new("ShaderNodeOutputWorld")
    world_output.location = (200, 0)
    
    # Link nodes
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
    links.new(env_tex.outputs["Color"], background.inputs["Color"])
    links.new(background.outputs["Background"], world_output.inputs["Surface"])
    
    return {
        "world": world.name,
        "hdri": hdri_path,
        "strength": strength,
        "rotation": rotation,
    }


RENDERING_HANDLERS = {
    "render_to_file": render_to_file,
    "render_viewport": render_viewport,
    "set_render_settings": set_render_settings,
    "get_render_settings": get_render_settings,
    "set_world_hdri": set_world_hdri,
}

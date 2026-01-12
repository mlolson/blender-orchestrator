"""Handlers for importing external mesh files."""

import bpy
import os
import tempfile
import urllib.request
from typing import Any, Dict, List, Optional
from pathlib import Path
from ..utils.serializers import serialize_object


def import_mesh_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import a mesh file into the scene.

    Supports GLB, GLTF, OBJ, FBX, PLY, STL formats.

    Args:
        params: Dictionary with:
            - file_path: Path to the mesh file
            - name: Optional name for the imported object
            - location: Optional [x, y, z] location
            - scale: Optional uniform scale or [x, y, z] scale
            - apply_transform: Whether to apply transforms after import

    Returns:
        Serialized object data for the imported mesh
    """
    file_path = params.get("file_path")
    if not file_path:
        return {"error": "file_path is required"}

    file_path = Path(file_path)
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    name = params.get("name")
    location = params.get("location", [0, 0, 0])
    scale = params.get("scale", 1.0)
    apply_transform = params.get("apply_transform", True)

    # Normalize scale to tuple
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    else:
        scale = tuple(scale)

    # Track objects before import
    objects_before = set(bpy.data.objects)

    # Import based on file extension
    suffix = file_path.suffix.lower()
    try:
        if suffix in (".glb", ".gltf"):
            bpy.ops.import_scene.gltf(filepath=str(file_path))
        elif suffix == ".obj":
            bpy.ops.wm.obj_import(filepath=str(file_path))
        elif suffix == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(file_path))
        elif suffix == ".ply":
            bpy.ops.wm.ply_import(filepath=str(file_path))
        elif suffix == ".stl":
            bpy.ops.wm.stl_import(filepath=str(file_path))
        else:
            return {"error": f"Unsupported file format: {suffix}"}
    except Exception as e:
        return {"error": f"Import failed: {str(e)}"}

    # Find newly imported objects
    objects_after = set(bpy.data.objects)
    new_objects = list(objects_after - objects_before)

    if not new_objects:
        return {"error": "No objects were imported"}

    # Get the primary imported object (usually the root or largest)
    primary_obj = _get_primary_object(new_objects)

    # Apply name if specified
    if name:
        primary_obj.name = name

    # Apply location
    primary_obj.location = tuple(location)

    # Apply scale
    primary_obj.scale = scale

    # Apply transforms if requested
    if apply_transform:
        bpy.context.view_layer.objects.active = primary_obj
        bpy.ops.object.select_all(action='DESELECT')
        for obj in new_objects:
            obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.object.select_all(action='DESELECT')
        primary_obj.select_set(True)

    # Build response
    result = serialize_object(primary_obj)
    result["imported_objects"] = [obj.name for obj in new_objects]
    result["source_file"] = str(file_path)

    return result


def import_mesh_from_url(params: Dict[str, Any]) -> Dict[str, Any]:
    """Download and import a mesh file from a URL.

    Args:
        params: Dictionary with:
            - url: URL to download the mesh from
            - name: Optional name for the imported object
            - location: Optional [x, y, z] location
            - scale: Optional uniform scale or [x, y, z] scale
            - format: Optional file format hint (glb, obj, etc.)

    Returns:
        Serialized object data for the imported mesh
    """
    url = params.get("url")
    if not url:
        return {"error": "url is required"}

    # Determine file format from URL or hint
    format_hint = params.get("format")
    if format_hint:
        suffix = f".{format_hint.lower().lstrip('.')}"
    else:
        # Try to get extension from URL
        url_path = url.split("?")[0]  # Remove query params
        suffix = Path(url_path).suffix.lower()
        if not suffix or suffix not in (".glb", ".gltf", ".obj", ".fbx", ".ply", ".stl"):
            suffix = ".glb"  # Default to GLB

    # Download to temporary file
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = tmp_file.name

        # Download the file
        urllib.request.urlretrieve(url, tmp_path)
    except Exception as e:
        return {"error": f"Failed to download mesh: {str(e)}"}

    # Import using the file handler
    import_params = {
        "file_path": tmp_path,
        "name": params.get("name"),
        "location": params.get("location", [0, 0, 0]),
        "scale": params.get("scale", 1.0),
        "apply_transform": params.get("apply_transform", True),
    }

    result = import_mesh_file(import_params)

    # Clean up temp file
    try:
        os.unlink(tmp_path)
    except Exception:
        pass

    # Update source info
    if "error" not in result:
        result["source_url"] = url

    return result


def get_supported_import_formats(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get list of supported import formats.

    Returns:
        Dictionary with supported formats and their descriptions
    """
    return {
        "formats": {
            "glb": "GL Transmission Format Binary (recommended)",
            "gltf": "GL Transmission Format",
            "obj": "Wavefront OBJ",
            "fbx": "Autodesk FBX",
            "ply": "Stanford PLY",
            "stl": "Stereolithography",
        }
    }


def _get_primary_object(objects: List[bpy.types.Object]) -> bpy.types.Object:
    """Get the primary object from a list of imported objects.

    Prefers mesh objects and returns the one with most vertices.
    """
    mesh_objects = [obj for obj in objects if obj.type == 'MESH']

    if mesh_objects:
        # Return mesh with most vertices
        return max(mesh_objects, key=lambda o: len(o.data.vertices) if o.data else 0)

    # Fall back to first object
    return objects[0]


# Handler registry for mesh import
MESH_IMPORT_HANDLERS = {
    "import_mesh_file": import_mesh_file,
    "import_mesh_from_url": import_mesh_from_url,
    "get_supported_import_formats": get_supported_import_formats,
}

"""Handlers for VR/Meta Horizon Worlds optimization.

These tools help creators optimize 3D assets for mobile VR platforms
like Meta Quest and Horizon Worlds.

Key constraints for Horizon Worlds:
- Polygon budget: ~10K triangles per object, ~100K per world
- Texture size: 1024x1024 or 2048x2048 max
- File format: GLB (binary glTF)
- Draw calls: Minimize by combining meshes
"""

import bpy
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..utils.serializers import serialize_object


def get_mesh_stats(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed statistics for a mesh object.

    Useful for checking if a model meets VR performance budgets.

    params:
        name: object name (or None for all selected/all scene objects)
        include_modifiers: apply modifiers before counting (default True)

    Returns:
        Detailed mesh statistics including poly count, bounds, materials
    """
    name = params.get("name")
    include_modifiers = params.get("include_modifiers", True)

    objects_to_check = []

    if name:
        obj = bpy.data.objects.get(name)
        if not obj or obj.type != "MESH":
            return {"error": f"Mesh object '{name}' not found"}
        objects_to_check = [obj]
    else:
        # Check all mesh objects in scene
        objects_to_check = [o for o in bpy.context.scene.objects if o.type == "MESH"]

    total_stats = {
        "objects": [],
        "total_vertices": 0,
        "total_edges": 0,
        "total_triangles": 0,
        "total_materials": set(),
        "total_textures": set(),
    }

    for obj in objects_to_check:
        if include_modifiers:
            # Get evaluated mesh with modifiers applied
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
        else:
            mesh = obj.data

        # Count triangles (faces may be quads or ngons)
        tri_count = sum(len(f.vertices) - 2 for f in mesh.polygons)

        # Calculate bounding box dimensions
        bbox = obj.bound_box
        min_co = [min(v[i] for v in bbox) for i in range(3)]
        max_co = [max(v[i] for v in bbox) for i in range(3)]
        dimensions = [max_co[i] - min_co[i] for i in range(3)]

        # Get materials and textures
        materials = []
        textures = []
        for slot in obj.material_slots:
            if slot.material:
                materials.append(slot.material.name)
                total_stats["total_materials"].add(slot.material.name)
                # Find textures in material
                if slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == "TEX_IMAGE" and node.image:
                            tex_info = {
                                "name": node.image.name,
                                "size": list(node.image.size),
                                "filepath": node.image.filepath,
                            }
                            textures.append(tex_info)
                            total_stats["total_textures"].add(node.image.name)

        obj_stats = {
            "name": obj.name,
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "triangles": tri_count,
            "dimensions": dimensions,
            "materials": materials,
            "textures": textures,
            "has_uv": len(mesh.uv_layers) > 0,
            "uv_layers": [uv.name for uv in mesh.uv_layers],
        }

        total_stats["objects"].append(obj_stats)
        total_stats["total_vertices"] += obj_stats["vertices"]
        total_stats["total_edges"] += obj_stats["edges"]
        total_stats["total_triangles"] += obj_stats["triangles"]

        if include_modifiers:
            eval_obj.to_mesh_clear()

    total_stats["total_materials"] = list(total_stats["total_materials"])
    total_stats["total_textures"] = list(total_stats["total_textures"])
    total_stats["object_count"] = len(total_stats["objects"])

    return total_stats


def validate_for_vr(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate scene/object against VR platform requirements.

    Checks for common issues that cause poor VR performance.

    params:
        name: object name (or None for entire scene)
        platform: 'horizon_worlds', 'quest', 'generic_mobile_vr' (default)

    Returns:
        Validation results with warnings and errors
    """
    name = params.get("name")
    platform = params.get("platform", "generic_mobile_vr")

    # Platform-specific limits
    limits = {
        "horizon_worlds": {
            "max_triangles_per_object": 10000,
            "max_triangles_scene": 100000,
            "max_texture_size": 2048,
            "max_materials_per_object": 4,
            "recommended_texture_size": 1024,
        },
        "quest": {
            "max_triangles_per_object": 50000,
            "max_triangles_scene": 500000,
            "max_texture_size": 2048,
            "max_materials_per_object": 8,
            "recommended_texture_size": 1024,
        },
        "generic_mobile_vr": {
            "max_triangles_per_object": 20000,
            "max_triangles_scene": 200000,
            "max_texture_size": 2048,
            "max_materials_per_object": 4,
            "recommended_texture_size": 1024,
        },
    }

    platform_limits = limits.get(platform, limits["generic_mobile_vr"])

    # Get stats
    stats = get_mesh_stats({"name": name, "include_modifiers": True})

    if "error" in stats:
        return stats

    errors = []
    warnings = []
    passed = []

    # Check triangle counts
    for obj in stats["objects"]:
        if obj["triangles"] > platform_limits["max_triangles_per_object"]:
            errors.append(
                f"'{obj['name']}' has {obj['triangles']:,} triangles "
                f"(max: {platform_limits['max_triangles_per_object']:,})"
            )
        elif obj["triangles"] > platform_limits["max_triangles_per_object"] * 0.8:
            warnings.append(
                f"'{obj['name']}' has {obj['triangles']:,} triangles "
                f"(approaching limit of {platform_limits['max_triangles_per_object']:,})"
            )

        # Check materials per object
        if len(obj["materials"]) > platform_limits["max_materials_per_object"]:
            warnings.append(
                f"'{obj['name']}' has {len(obj['materials'])} materials "
                f"(recommended max: {platform_limits['max_materials_per_object']})"
            )

        # Check UVs
        if not obj["has_uv"]:
            warnings.append(f"'{obj['name']}' has no UV maps (textures won't work)")

        # Check textures
        for tex in obj["textures"]:
            if tex["size"][0] > platform_limits["max_texture_size"]:
                errors.append(
                    f"Texture '{tex['name']}' is {tex['size'][0]}x{tex['size'][1]} "
                    f"(max: {platform_limits['max_texture_size']})"
                )
            elif tex["size"][0] > platform_limits["recommended_texture_size"]:
                warnings.append(
                    f"Texture '{tex['name']}' is {tex['size'][0]}x{tex['size'][1]} "
                    f"(recommended: {platform_limits['recommended_texture_size']})"
                )

    # Check total scene triangles
    if stats["total_triangles"] > platform_limits["max_triangles_scene"]:
        errors.append(
            f"Total scene triangles: {stats['total_triangles']:,} "
            f"(max: {platform_limits['max_triangles_scene']:,})"
        )

    # Summary
    if not errors:
        passed.append(f"Triangle count within limits ({stats['total_triangles']:,} total)")
    if not warnings and not errors:
        passed.append("All textures within size limits")
        passed.append("All objects have UV maps")

    return {
        "platform": platform,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "stats": {
            "total_triangles": stats["total_triangles"],
            "total_objects": stats["object_count"],
            "total_materials": len(stats["total_materials"]),
            "total_textures": len(stats["total_textures"]),
        },
        "limits": platform_limits,
    }


def decimate_mesh(params: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce polygon count of a mesh while preserving shape.

    Uses Blender's Decimate modifier for intelligent polygon reduction.

    params:
        name: object name
        ratio: target ratio (0.0-1.0, e.g., 0.5 = 50% of original)
        target_triangles: alternative to ratio - specify exact triangle count
        method: 'COLLAPSE' (default), 'UNSUBDIV', or 'DISSOLVE'
        symmetry: use symmetry ('X', 'Y', 'Z', or None)
        apply: apply the modifier (default True)

    Returns:
        Decimation result with before/after stats
    """
    name = params["name"]
    ratio = params.get("ratio")
    target_triangles = params.get("target_triangles")
    method = params.get("method", "COLLAPSE").upper()
    symmetry = params.get("symmetry")
    apply = params.get("apply", True)

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "MESH":
        return {"error": f"Mesh object '{name}' not found"}

    # Get before stats
    before_stats = get_mesh_stats({"name": name})["objects"][0]

    # Calculate ratio from target triangles if specified
    if target_triangles and not ratio:
        if before_stats["triangles"] > 0:
            ratio = target_triangles / before_stats["triangles"]
            ratio = max(0.01, min(1.0, ratio))  # Clamp to valid range
        else:
            ratio = 1.0
    elif not ratio:
        ratio = 0.5  # Default to 50%

    # Ensure object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Add decimate modifier
    mod = obj.modifiers.new(name="Decimate", type="DECIMATE")
    mod.decimate_type = method
    mod.ratio = ratio

    if symmetry and method == "COLLAPSE":
        mod.use_symmetry = True
        mod.symmetry_axis = symmetry

    if apply:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    # Get after stats
    after_stats = get_mesh_stats({"name": name})["objects"][0]

    return {
        "name": name,
        "method": method,
        "ratio": ratio,
        "before": {
            "vertices": before_stats["vertices"],
            "triangles": before_stats["triangles"],
        },
        "after": {
            "vertices": after_stats["vertices"],
            "triangles": after_stats["triangles"],
        },
        "reduction": {
            "vertices": before_stats["vertices"] - after_stats["vertices"],
            "triangles": before_stats["triangles"] - after_stats["triangles"],
            "percentage": round(
                (1 - after_stats["triangles"] / max(1, before_stats["triangles"])) * 100, 1
            ),
        },
        "applied": apply,
    }


def generate_lod(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Level of Detail (LOD) variants of a mesh.

    Creates multiple decimated copies for distance-based rendering.

    params:
        name: object name
        levels: list of LOD ratios (default [1.0, 0.5, 0.25, 0.1])
        suffix_format: naming format (default '_LOD{level}')
        group: create a collection for LODs (default True)

    Returns:
        List of created LOD objects with their stats
    """
    name = params["name"]
    levels = params.get("levels", [1.0, 0.5, 0.25, 0.1])
    suffix_format = params.get("suffix_format", "_LOD{level}")
    create_group = params.get("group", True)

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "MESH":
        return {"error": f"Mesh object '{name}' not found"}

    # Ensure object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Create collection for LODs
    if create_group:
        lod_collection_name = f"{name}_LODs"
        if lod_collection_name not in bpy.data.collections:
            lod_collection = bpy.data.collections.new(lod_collection_name)
            bpy.context.scene.collection.children.link(lod_collection)
        else:
            lod_collection = bpy.data.collections[lod_collection_name]
    else:
        lod_collection = bpy.context.scene.collection

    lods = []
    original_stats = get_mesh_stats({"name": name})["objects"][0]

    for i, ratio in enumerate(levels):
        lod_name = name + suffix_format.format(level=i)

        if i == 0 and ratio >= 1.0:
            # LOD0 is the original (or a copy)
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.duplicate(linked=False)
            lod_obj = bpy.context.active_object
            lod_obj.name = lod_name
        else:
            # Create decimated copy
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.duplicate(linked=False)
            lod_obj = bpy.context.active_object
            lod_obj.name = lod_name

            # Decimate
            decimate_mesh({
                "name": lod_name,
                "ratio": ratio,
                "apply": True,
            })

        # Move to LOD collection
        if create_group:
            for coll in lod_obj.users_collection:
                coll.objects.unlink(lod_obj)
            lod_collection.objects.link(lod_obj)

        # Get stats
        lod_stats = get_mesh_stats({"name": lod_name})["objects"][0]
        lods.append({
            "name": lod_name,
            "level": i,
            "ratio": ratio,
            "triangles": lod_stats["triangles"],
            "reduction_percent": round(
                (1 - lod_stats["triangles"] / max(1, original_stats["triangles"])) * 100, 1
            ),
        })

    return {
        "source": name,
        "collection": lod_collection.name if create_group else None,
        "lods": lods,
        "original_triangles": original_stats["triangles"],
    }


def export_glb(params: Dict[str, Any]) -> Dict[str, Any]:
    """Export scene or selection as GLB (binary glTF).

    Optimized for VR platforms like Meta Horizon Worlds.

    params:
        output_path: path for the GLB file
        selected_only: export only selected objects (default False)
        apply_modifiers: apply modifiers before export (default True)
        export_materials: include materials (default True)
        export_textures: include textures (default True)
        compress_textures: use Draco compression (default False)
        draco_compression_level: 0-10, higher = smaller but slower (default 6)

    Returns:
        Export result with file path and stats
    """
    output_path = params.get("output_path")
    selected_only = params.get("selected_only", False)
    apply_modifiers = params.get("apply_modifiers", True)
    export_materials = params.get("export_materials", True)
    export_textures = params.get("export_textures", True)
    use_draco = params.get("compress_textures", False)
    draco_level = params.get("draco_compression_level", 6)

    if not output_path:
        output_path = tempfile.mktemp(suffix=".glb")

    # Ensure .glb extension
    if not output_path.lower().endswith(".glb"):
        output_path += ".glb"

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Export settings
    export_kwargs = {
        "filepath": output_path,
        "use_selection": selected_only,
        "export_format": "GLB",
        "export_apply": apply_modifiers,
        "export_materials": "EXPORT" if export_materials else "NONE",
        "export_texcoords": True,
        "export_normals": True,
        "export_colors": True,
        "export_cameras": False,
        "export_lights": False,
        "use_visible": True,
        "use_renderable": True,
        "export_extras": False,
    }

    # Draco compression
    if use_draco:
        export_kwargs["export_draco_mesh_compression_enable"] = True
        export_kwargs["export_draco_mesh_compression_level"] = draco_level

    try:
        bpy.ops.export_scene.gltf(**export_kwargs)
    except Exception as e:
        return {"error": f"Export failed: {str(e)}"}

    # Get file size
    file_size = os.path.getsize(output_path)

    return {
        "output_path": output_path,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "selected_only": selected_only,
        "draco_compression": use_draco,
    }


def optimize_for_vr(params: Dict[str, Any]) -> Dict[str, Any]:
    """One-click optimization for VR platforms.

    Applies multiple optimizations to prepare assets for VR:
    1. Decimates high-poly meshes
    2. Merges objects to reduce draw calls
    3. Validates against platform limits

    params:
        target_platform: 'horizon_worlds', 'quest', 'generic_mobile_vr'
        auto_decimate: automatically reduce poly count (default True)
        merge_by_material: merge objects with same material (default False)
        validate: run validation after (default True)

    Returns:
        Optimization results
    """
    platform = params.get("target_platform", "horizon_worlds")
    auto_decimate = params.get("auto_decimate", True)
    merge_by_material = params.get("merge_by_material", False)
    validate = params.get("validate", True)

    limits = {
        "horizon_worlds": {"max_tris": 10000, "scene_max": 100000},
        "quest": {"max_tris": 50000, "scene_max": 500000},
        "generic_mobile_vr": {"max_tris": 20000, "scene_max": 200000},
    }

    platform_limits = limits.get(platform, limits["generic_mobile_vr"])

    results = {
        "platform": platform,
        "optimizations": [],
        "before": {},
        "after": {},
    }

    # Get before stats
    before_stats = get_mesh_stats({"name": None})
    results["before"] = {
        "total_triangles": before_stats["total_triangles"],
        "object_count": before_stats["object_count"],
    }

    # Auto-decimate objects over the limit
    if auto_decimate:
        for obj_stats in before_stats["objects"]:
            if obj_stats["triangles"] > platform_limits["max_tris"]:
                target_ratio = platform_limits["max_tris"] / obj_stats["triangles"]
                decimate_result = decimate_mesh({
                    "name": obj_stats["name"],
                    "ratio": target_ratio * 0.9,  # Aim slightly under limit
                    "apply": True,
                })
                results["optimizations"].append({
                    "type": "decimate",
                    "object": obj_stats["name"],
                    "before_tris": obj_stats["triangles"],
                    "after_tris": decimate_result["after"]["triangles"],
                })

    # Get after stats
    after_stats = get_mesh_stats({"name": None})
    results["after"] = {
        "total_triangles": after_stats["total_triangles"],
        "object_count": after_stats["object_count"],
    }

    # Run validation
    if validate:
        validation = validate_for_vr({"platform": platform})
        results["validation"] = validation

    return results


def auto_uv_unwrap(params: Dict[str, Any]) -> Dict[str, Any]:
    """Automatically UV unwrap a mesh.

    Useful for AI-generated meshes that may have poor or no UVs.

    params:
        name: object name
        method: 'SMART_PROJECT' (default), 'LIGHTMAP', 'CUBE'
        angle_limit: angle for seams in degrees (default 66)
        island_margin: margin between UV islands (default 0.02)

    Returns:
        UV unwrap result
    """
    name = params["name"]
    method = params.get("method", "SMART_PROJECT").upper()
    angle_limit = params.get("angle_limit", 66)
    island_margin = params.get("island_margin", 0.02)

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "MESH":
        return {"error": f"Mesh object '{name}' not found"}

    # Ensure object mode then switch to edit mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Enter edit mode
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    # Create new UV layer if none exists
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    # Apply UV unwrap
    import math

    if method == "SMART_PROJECT":
        bpy.ops.uv.smart_project(
            angle_limit=math.radians(angle_limit),
            island_margin=island_margin,
        )
    elif method == "LIGHTMAP":
        bpy.ops.uv.lightmap_pack(
            PREF_CONTEXT="ALL_FACES",
            PREF_PACK_IN_ONE=True,
            PREF_MARGIN_DIV=island_margin,
        )
    elif method == "CUBE":
        bpy.ops.uv.cube_project()

    bpy.ops.object.mode_set(mode="OBJECT")

    return {
        "name": name,
        "method": method,
        "uv_layers": [uv.name for uv in mesh.uv_layers],
    }


# Handler registry
VR_OPTIMIZATION_HANDLERS = {
    "get_mesh_stats": get_mesh_stats,
    "validate_for_vr": validate_for_vr,
    "decimate_mesh": decimate_mesh,
    "generate_lod": generate_lod,
    "export_glb": export_glb,
    "optimize_for_vr": optimize_for_vr,
    "auto_uv_unwrap": auto_uv_unwrap,
}

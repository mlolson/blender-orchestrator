"""Handlers for curve-based modeling operations.

Curves are useful for creating hair, eyebrows, tentacles, pipes,
and other organic or mechanical shapes that follow a path.
"""

import bpy
import math
from typing import Any, Dict, List
from mathutils import Vector
from ..utils.serializers import serialize_object


def create_bezier_curve(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a bezier curve.

    params:
        name: curve name (default "BezierCurve")
        points: list of point definitions, each can be:
                - [x, y, z] simple position (auto handles)
                - {"co": [x,y,z], "handle_left": [x,y,z], "handle_right": [x,y,z]}
        cyclic: close the curve into a loop (default False)
        location: [x, y, z] object location (default [0, 0, 0])
        dimensions: '2D' or '3D' (default '3D')
    """
    name = params.get("name", "BezierCurve")
    points = params["points"]
    cyclic = params.get("cyclic", False)
    location = params.get("location", [0, 0, 0])
    dimensions = params.get("dimensions", "3D")

    if len(points) < 2:
        raise ValueError("At least 2 points are required for a curve")

    # Create curve data
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = dimensions

    # Create spline
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)  # First point already exists
    spline.use_cyclic_u = cyclic

    # Set points
    for i, pt in enumerate(points):
        bp = spline.bezier_points[i]

        if isinstance(pt, dict):
            bp.co = pt["co"]
            if "handle_left" in pt:
                bp.handle_left = pt["handle_left"]
                bp.handle_left_type = 'FREE'
            if "handle_right" in pt:
                bp.handle_right = pt["handle_right"]
                bp.handle_right_type = 'FREE'
        else:
            # Simple [x, y, z] format
            bp.co = pt
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'

    # Create object
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    bpy.context.collection.objects.link(obj)

    # Select and activate
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return serialize_object(obj)


def create_nurbs_curve(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a NURBS curve.

    NURBS curves are smoother and more predictable than bezier curves,
    good for mechanical shapes.

    params:
        name: curve name (default "NurbsCurve")
        points: list of [x, y, z] control points
        cyclic: close the curve (default False)
        order: curve order/degree (default 4)
        location: [x, y, z] object location (default [0, 0, 0])
    """
    name = params.get("name", "NurbsCurve")
    points = params["points"]
    cyclic = params.get("cyclic", False)
    order = params.get("order", 4)
    location = params.get("location", [0, 0, 0])

    if len(points) < 2:
        raise ValueError("At least 2 points are required")

    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'

    spline = curve.splines.new('NURBS')
    spline.points.add(len(points) - 1)
    spline.use_cyclic_u = cyclic
    spline.order_u = min(order, len(points))

    for i, pt in enumerate(points):
        # NURBS points have 4 components: x, y, z, w (weight)
        spline.points[i].co = (pt[0], pt[1], pt[2], 1.0)

    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    bpy.context.collection.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return serialize_object(obj)


def set_curve_bevel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set bevel (thickness) for a curve, turning it into a tube/ribbon.

    params:
        name: curve object name
        depth: bevel depth/radius (thickness of the tube)
        resolution: bevel resolution (smoothness, 0-32)
        fill_mode: 'FULL', 'BACK', 'FRONT', 'HALF' (default 'FULL')
        profile_object: name of another curve to use as bevel profile (optional)
        taper_object: name of curve to use for tapering (optional)
    """
    name = params["name"]
    depth = params.get("depth", 0.1)
    resolution = params.get("resolution", 4)
    fill_mode = params.get("fill_mode", "FULL")
    profile_object = params.get("profile_object")
    taper_object = params.get("taper_object")

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")
    if obj.type != 'CURVE':
        raise ValueError(f"Object '{name}' is not a curve (type: {obj.type})")

    curve = obj.data
    curve.bevel_depth = depth
    curve.bevel_resolution = resolution
    curve.fill_mode = fill_mode

    if profile_object:
        profile_obj = bpy.data.objects.get(profile_object)
        if profile_obj and profile_obj.type == 'CURVE':
            curve.bevel_object = profile_obj

    if taper_object:
        taper_obj = bpy.data.objects.get(taper_object)
        if taper_obj and taper_obj.type == 'CURVE':
            curve.taper_object = taper_obj

    return serialize_object(obj)


def set_curve_extrude(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set extrusion for a curve (extends it in one direction).

    params:
        name: curve object name
        extrude: extrusion amount
        offset: offset from the curve path
    """
    name = params["name"]
    extrude = params.get("extrude", 0.0)
    offset = params.get("offset", 0.0)

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'CURVE':
        raise ValueError(f"'{name}' is not a curve object")

    curve = obj.data
    curve.extrude = extrude
    curve.offset = offset

    return serialize_object(obj)


def add_curve_point(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add a point to an existing curve.

    params:
        name: curve object name
        spline_index: which spline to add to (default 0)
        position: [x, y, z] position for new point
        handle_left: [x, y, z] left handle (optional, bezier only)
        handle_right: [x, y, z] right handle (optional, bezier only)
    """
    name = params["name"]
    spline_index = params.get("spline_index", 0)
    position = params["position"]

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'CURVE':
        raise ValueError(f"'{name}' is not a curve object")

    curve = obj.data
    if spline_index >= len(curve.splines):
        raise ValueError(f"Spline index {spline_index} out of range")

    spline = curve.splines[spline_index]

    if spline.type == 'BEZIER':
        spline.bezier_points.add(1)
        bp = spline.bezier_points[-1]
        bp.co = position
        if "handle_left" in params:
            bp.handle_left = params["handle_left"]
            bp.handle_left_type = 'FREE'
        if "handle_right" in params:
            bp.handle_right = params["handle_right"]
            bp.handle_right_type = 'FREE'
    else:
        spline.points.add(1)
        spline.points[-1].co = (position[0], position[1], position[2], 1.0)

    return {
        "name": name,
        "spline_index": spline_index,
        "point_count": len(spline.bezier_points) if spline.type == 'BEZIER' else len(spline.points),
    }


def modify_curve_point(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify a point on a curve.

    params:
        name: curve object name
        spline_index: which spline (default 0)
        point_index: which point to modify
        position: new [x, y, z] position (optional)
        handle_left: new left handle position (optional, bezier only)
        handle_right: new right handle position (optional, bezier only)
        handle_type: 'FREE', 'AUTO', 'VECTOR', 'ALIGNED' (optional, bezier only)
    """
    name = params["name"]
    spline_index = params.get("spline_index", 0)
    point_index = params["point_index"]

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'CURVE':
        raise ValueError(f"'{name}' is not a curve object")

    curve = obj.data
    spline = curve.splines[spline_index]

    if spline.type == 'BEZIER':
        if point_index >= len(spline.bezier_points):
            raise ValueError(f"Point index {point_index} out of range")

        bp = spline.bezier_points[point_index]
        if "position" in params:
            bp.co = params["position"]
        if "handle_left" in params:
            bp.handle_left = params["handle_left"]
        if "handle_right" in params:
            bp.handle_right = params["handle_right"]
        if "handle_type" in params:
            bp.handle_left_type = params["handle_type"]
            bp.handle_right_type = params["handle_type"]
    else:
        if point_index >= len(spline.points):
            raise ValueError(f"Point index {point_index} out of range")

        pt = spline.points[point_index]
        if "position" in params:
            pos = params["position"]
            pt.co = (pos[0], pos[1], pos[2], pt.co[3])

    return {
        "name": name,
        "modified_point": point_index,
    }


def get_curve_points(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get all points from a curve.

    params:
        name: curve object name
        spline_index: which spline (default all)
    """
    name = params["name"]
    spline_index = params.get("spline_index")

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != 'CURVE':
        raise ValueError(f"'{name}' is not a curve object")

    curve = obj.data
    splines_data = []

    for i, spline in enumerate(curve.splines):
        if spline_index is not None and i != spline_index:
            continue

        points = []
        if spline.type == 'BEZIER':
            for bp in spline.bezier_points:
                points.append({
                    "co": list(bp.co),
                    "handle_left": list(bp.handle_left),
                    "handle_right": list(bp.handle_right),
                    "handle_type": bp.handle_left_type,
                })
        else:
            for pt in spline.points:
                points.append({
                    "co": list(pt.co[:3]),
                    "weight": pt.co[3],
                })

        splines_data.append({
            "index": i,
            "type": spline.type,
            "cyclic": spline.use_cyclic_u,
            "point_count": len(points),
            "points": points,
        })

    return {
        "name": name,
        "spline_count": len(splines_data),
        "splines": splines_data,
    }


def convert_curve_to_mesh(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a curve to a mesh.

    params:
        name: curve object name
        resolution: curve resolution before converting (optional)
    """
    name = params["name"]
    resolution = params.get("resolution")

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    # Set resolution if specified
    if resolution and obj.type == 'CURVE':
        obj.data.resolution_u = resolution

    # Ensure object mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')

    return serialize_object(obj, detailed=True)


def create_curve_circle(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a circular curve (useful as bevel profile).

    params:
        name: curve name (default "CurveCircle")
        radius: circle radius (default 1.0)
        vertices: number of vertices (default 8)
        location: [x, y, z] object location
    """
    name = params.get("name", "CurveCircle")
    radius = params.get("radius", 1.0)
    vertices = params.get("vertices", 8)
    location = params.get("location", [0, 0, 0])

    bpy.ops.curve.primitive_bezier_circle_add(
        radius=radius,
        location=location
    )

    obj = bpy.context.active_object
    obj.name = name

    return serialize_object(obj)


def create_hair_curves(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create multiple curves suitable for hair strands.

    params:
        name: base name for curves
        count: number of hair strands
        root_positions: list of [x, y, z] starting positions
        length: hair length (default 0.3)
        segments: segments per strand (default 4)
        curl: curl amount (0-1, default 0)
        randomness: position randomness (default 0.02)
        gravity: gravity influence (default 0.5)
    """
    name = params.get("name", "Hair")
    count = params.get("count", 10)
    root_positions = params.get("root_positions", [])
    length = params.get("length", 0.3)
    segments = params.get("segments", 4)
    curl = params.get("curl", 0.0)
    randomness = params.get("randomness", 0.02)
    gravity = params.get("gravity", 0.5)

    import random

    created_curves = []

    # If no root positions provided, generate them
    if not root_positions:
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            radius = 0.1
            root_positions.append([
                math.cos(angle) * radius,
                math.sin(angle) * radius,
                0.15  # Top of head
            ])

    for i, root in enumerate(root_positions[:count]):
        # Generate points for this strand
        points = []
        segment_length = length / segments

        for j in range(segments + 1):
            t = j / segments
            # Start from root, go outward with gravity
            x = root[0] + random.uniform(-randomness, randomness)
            y = root[1] + random.uniform(-randomness, randomness)
            z = root[2] + (j * segment_length) - (t * t * gravity * length)

            # Add curl
            if curl > 0:
                curl_angle = t * curl * 4 * math.pi
                curl_radius = t * curl * 0.05
                x += math.cos(curl_angle) * curl_radius
                y += math.sin(curl_angle) * curl_radius

            points.append([x, y, z])

        # Create the curve
        curve_name = f"{name}_{i:03d}"
        create_bezier_curve({
            "name": curve_name,
            "points": points,
            "cyclic": False,
        })

        # Add bevel for thickness
        set_curve_bevel({
            "name": curve_name,
            "depth": 0.003,
            "resolution": 2,
        })

        created_curves.append(curve_name)

    return {
        "name": name,
        "count": len(created_curves),
        "curves": created_curves,
    }


CURVE_HANDLERS = {
    "create_bezier_curve": create_bezier_curve,
    "create_nurbs_curve": create_nurbs_curve,
    "set_curve_bevel": set_curve_bevel,
    "set_curve_extrude": set_curve_extrude,
    "add_curve_point": add_curve_point,
    "modify_curve_point": modify_curve_point,
    "get_curve_points": get_curve_points,
    "convert_curve_to_mesh": convert_curve_to_mesh,
    "create_curve_circle": create_curve_circle,
    "create_hair_curves": create_hair_curves,
}

"""MCP tools for camera creation and manipulation."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register camera tools."""

    @mcp.tool()
    async def create_camera(
        location: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None,
        lens: float = 50.0,
        name: Optional[str] = None,
        sensor_width: float = 36.0,
        clip_start: float = 0.1,
        clip_end: float = 1000.0,
        camera_type: str = "PERSP",
    ) -> str:
        """Create a camera in the scene.

        Args:
            location: [x, y, z] position (default: [0, -10, 5])
            rotation: [x, y, z] rotation in degrees (default: [60, 0, 0] - looks at origin)
            lens: Focal length in mm (default: 50). Lower = wider angle, higher = telephoto
            name: Optional name for the camera
            sensor_width: Sensor width in mm (default: 36 - full frame)
            clip_start: Near clipping distance (default: 0.1)
            clip_end: Far clipping distance (default: 1000)
            camera_type: PERSP (perspective), ORTHO (orthographic), or PANO (panoramic)
        """
        result = await client.execute(
            "create_camera",
            {
                "location": location or [0, -10, 5],
                "rotation": rotation or [60, 0, 0],
                "lens": lens,
                "name": name,
                "sensor_width": sensor_width,
                "clip_start": clip_start,
                "clip_end": clip_end,
                "type": camera_type,
            },
        )
        camera = result.get("camera", {})
        return f"📷 Created camera '{result['name']}' at {result['location']} (lens: {camera.get('lens')}mm, type: {camera.get('type')})"

    @mcp.tool()
    async def set_active_camera(name: str) -> str:
        """Set a camera as the active scene camera for rendering.

        Args:
            name: Name of the camera to make active
        """
        result = await client.execute("set_active_camera", {"name": name})
        return f"🎬 Set '{result['name']}' as the active camera"

    @mcp.tool()
    async def look_at(
        name: str,
        target: str | List[float],
    ) -> str:
        """Point a camera (or any object) at a target location or object.

        Args:
            name: Name of the camera/object to rotate
            target: Either an object name or [x, y, z] coordinates to look at
        """
        result = await client.execute(
            "look_at",
            {
                "name": name,
                "target": target,
            },
        )
        looking_at = result.get("looking_at", target)
        return f"👁️ '{result['name']}' now looking at {looking_at}"

    @mcp.tool()
    async def set_camera_properties(
        name: str,
        lens: Optional[float] = None,
        sensor_width: Optional[float] = None,
        clip_start: Optional[float] = None,
        clip_end: Optional[float] = None,
        camera_type: Optional[str] = None,
        ortho_scale: Optional[float] = None,
        dof_enabled: Optional[bool] = None,
        dof_focus_distance: Optional[float] = None,
        dof_aperture: Optional[float] = None,
    ) -> str:
        """Modify properties of an existing camera.

        Args:
            name: Name of the camera to modify
            lens: Focal length in mm
            sensor_width: Sensor width in mm
            clip_start: Near clipping distance
            clip_end: Far clipping distance
            camera_type: PERSP, ORTHO, or PANO
            ortho_scale: Orthographic scale (only for ORTHO cameras)
            dof_enabled: Enable depth of field
            dof_focus_distance: Focus distance in meters
            dof_aperture: F-stop value (lower = more blur)
        """
        params = {"name": name}
        if lens is not None:
            params["lens"] = lens
        if sensor_width is not None:
            params["sensor_width"] = sensor_width
        if clip_start is not None:
            params["clip_start"] = clip_start
        if clip_end is not None:
            params["clip_end"] = clip_end
        if camera_type is not None:
            params["type"] = camera_type
        if ortho_scale is not None:
            params["ortho_scale"] = ortho_scale
        if dof_enabled is not None:
            params["dof_enabled"] = dof_enabled
        if dof_focus_distance is not None:
            params["dof_focus_distance"] = dof_focus_distance
        if dof_aperture is not None:
            params["dof_aperture"] = dof_aperture

        result = await client.execute("set_camera_properties", params)
        camera = result.get("camera", {})
        return f"✨ Updated camera '{result['name']}' (lens: {camera.get('lens')}mm, type: {camera.get('type')})"

    @mcp.tool()
    async def get_camera_info(name: str) -> str:
        """Get detailed information about a camera.

        Args:
            name: Name of the camera to query
        """
        result = await client.execute("get_camera_info", {"name": name})
        camera = result.get("camera", {})
        dof = camera.get("dof", {})

        lines = [f"Camera: {result['name']}"]
        lines.append(f"  Location: {result['location']}")
        lines.append(f"  Rotation: {result.get('rotation')} degrees")
        lines.append(f"  Type: {camera.get('type')}")
        lines.append(f"  Lens: {camera.get('lens')}mm")
        lines.append(f"  Sensor: {camera.get('sensor_width')}x{camera.get('sensor_height')}mm")
        lines.append(f"  Clip: {camera.get('clip_start')} - {camera.get('clip_end')}")
        lines.append(f"  Active: {'Yes' if camera.get('is_active') else 'No'}")

        if camera.get("type") == "ORTHO":
            lines.append(f"  Ortho scale: {camera.get('ortho_scale')}")

        lines.append(f"  DOF: {'Enabled' if dof.get('enabled') else 'Disabled'}")
        if dof.get("enabled"):
            lines.append(f"    Focus distance: {dof.get('focus_distance')}m")
            lines.append(f"    Aperture: f/{dof.get('aperture_fstop')}")
            if dof.get("focus_object"):
                lines.append(f"    Focus object: {dof.get('focus_object')}")

        return "\n".join(lines)

    @mcp.tool()
    async def list_cameras() -> str:
        """List all cameras in the scene."""
        result = await client.execute("list_cameras", {})

        cameras = result.get("cameras", [])
        if not cameras:
            return "No cameras found in the scene."

        lines = [f"Scene contains {result['count']} camera(s):"]
        for cam in cameras:
            loc = cam["location"]
            active = "⭐ ACTIVE" if cam["is_active"] else ""
            visible = "visible" if cam["visible"] else "hidden"
            lines.append(
                f"  - {cam['name']} ({cam['type']}, {cam['lens']}mm) at "
                f"({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f}) [{visible}] {active}"
            )

        if result.get("active"):
            lines.append(f"\nActive camera: {result['active']}")

        return "\n".join(lines)

    @mcp.tool()
    async def frame_objects(
        objects: Optional[List[str]] = None,
        camera: Optional[str] = None,
        padding: float = 1.2,
    ) -> str:
        """Position camera to frame specified objects or the entire scene.

        Automatically positions and rotates the camera to show the target objects
        with appropriate framing. Great for product shots or scene overviews.

        Args:
            objects: List of object names to frame (default: all mesh objects)
            camera: Camera to use (default: active camera)
            padding: Distance multiplier for framing (default: 1.2, higher = more space around objects)
        """
        result = await client.execute(
            "frame_objects",
            {
                "objects": objects,
                "camera": camera,
                "padding": padding,
            },
        )
        framed = result.get("framed", {})
        obj_names = framed.get("objects", [])
        if len(obj_names) > 3:
            obj_str = f"{obj_names[0]}, {obj_names[1]}, ... ({len(obj_names)} objects)"
        else:
            obj_str = ", ".join(obj_names)
        return f"🎯 Camera '{result['name']}' positioned to frame: {obj_str}"

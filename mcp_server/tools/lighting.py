"""MCP tools for light creation and manipulation."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register lighting tools."""

    @mcp.tool()
    async def create_point_light(
        location: Optional[List[float]] = None,
        energy: float = 1000.0,
        color: Optional[List[float]] = None,
        radius: float = 0.25,
        name: Optional[str] = None,
    ) -> str:
        """Create a point light (omnidirectional light source).

        Point lights emit light equally in all directions from a single point,
        like a light bulb. Great for indoor lighting and localized illumination.

        Args:
            location: [x, y, z] position (default: [0, 0, 3])
            energy: Light intensity in Watts (default: 1000)
            color: [r, g, b] values 0-1 (default: [1, 1, 1] white)
            radius: Soft shadow radius for realistic shadows (default: 0.25)
            name: Optional name for the light
        """
        result = await client.execute(
            "create_point_light",
            {
                "location": location or [0, 0, 3],
                "energy": energy,
                "color": color or [1.0, 1.0, 1.0],
                "radius": radius,
                "name": name,
            },
        )
        light = result.get("light", {})
        return f"💡 Created point light '{result['name']}' at {result['location']} (energy: {light.get('energy')}W)"

    @mcp.tool()
    async def create_sun_light(
        rotation: Optional[List[float]] = None,
        energy: float = 5.0,
        color: Optional[List[float]] = None,
        angle: float = 0.526,
        location: Optional[List[float]] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a sun light (directional light for outdoor scenes).

        Sun lights simulate distant light sources like the sun. All rays are parallel,
        creating consistent shadows. Position doesn't affect lighting, only rotation matters.

        Args:
            rotation: [x, y, z] rotation in degrees (default: [45, 0, 45])
            energy: Light intensity (default: 5.0 - sun uses different scale than other lights)
            color: [r, g, b] values 0-1 (default: [1, 1, 1] white)
            angle: Angular diameter in radians for soft shadows (default: 0.526)
            location: [x, y, z] position - cosmetic only (default: [0, 0, 10])
            name: Optional name for the light
        """
        result = await client.execute(
            "create_sun_light",
            {
                "location": location or [0, 0, 10],
                "rotation": rotation or [45, 0, 45],
                "energy": energy,
                "color": color or [1.0, 1.0, 1.0],
                "angle": angle,
                "name": name,
            },
        )
        light = result.get("light", {})
        rot = rotation or [45, 0, 45]
        return f"☀️ Created sun light '{result['name']}' with rotation ({rot[0]}°, {rot[1]}°, {rot[2]}°) (energy: {light.get('energy')})"

    @mcp.tool()
    async def create_spot_light(
        location: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None,
        energy: float = 1000.0,
        color: Optional[List[float]] = None,
        spot_size: float = 45.0,
        spot_blend: float = 0.15,
        radius: float = 0.25,
        name: Optional[str] = None,
    ) -> str:
        """Create a spot light (cone-shaped light for focused lighting).

        Spot lights emit light in a cone shape, like a flashlight or stage spotlight.
        Great for dramatic lighting, highlighting objects, or architectural lighting.

        Args:
            location: [x, y, z] position (default: [0, 0, 5])
            rotation: [x, y, z] rotation in degrees pointing the light (default: [0, 0, 0])
            energy: Light intensity in Watts (default: 1000)
            color: [r, g, b] values 0-1 (default: [1, 1, 1] white)
            spot_size: Cone angle in degrees (default: 45)
            spot_blend: Edge softness 0-1, higher = softer edges (default: 0.15)
            radius: Soft shadow radius (default: 0.25)
            name: Optional name for the light
        """
        result = await client.execute(
            "create_spot_light",
            {
                "location": location or [0, 0, 5],
                "rotation": rotation or [0, 0, 0],
                "energy": energy,
                "color": color or [1.0, 1.0, 1.0],
                "spot_size": spot_size,
                "spot_blend": spot_blend,
                "radius": radius,
                "name": name,
            },
        )
        light = result.get("light", {})
        return f"🔦 Created spot light '{result['name']}' at {result['location']} (cone: {spot_size}°, energy: {light.get('energy')}W)"

    @mcp.tool()
    async def create_area_light(
        location: Optional[List[float]] = None,
        rotation: Optional[List[float]] = None,
        energy: float = 1000.0,
        color: Optional[List[float]] = None,
        shape: str = "RECTANGLE",
        size: float = 1.0,
        size_y: Optional[float] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create an area light (rectangular or disk-shaped soft light).

        Area lights simulate real-world light panels and softboxes. They produce
        the most realistic soft shadows. Larger area = softer shadows.

        Args:
            location: [x, y, z] position (default: [0, 0, 3])
            rotation: [x, y, z] rotation in degrees (default: [0, 0, 0])
            energy: Light intensity in Watts (default: 1000)
            color: [r, g, b] values 0-1 (default: [1, 1, 1] white)
            shape: SQUARE, RECTANGLE, DISK, or ELLIPSE (default: RECTANGLE)
            size: Primary size in meters (default: 1.0)
            size_y: Secondary size for RECTANGLE/ELLIPSE (default: same as size)
            name: Optional name for the light
        """
        result = await client.execute(
            "create_area_light",
            {
                "location": location or [0, 0, 3],
                "rotation": rotation or [0, 0, 0],
                "energy": energy,
                "color": color or [1.0, 1.0, 1.0],
                "shape": shape,
                "size": size,
                "size_y": size_y,
                "name": name,
            },
        )
        light = result.get("light", {})
        shape_str = light.get("shape", shape)
        return f"📐 Created {shape_str.lower()} area light '{result['name']}' at {result['location']} ({size}m, energy: {light.get('energy')}W)"

    @mcp.tool()
    async def set_light_properties(
        name: str,
        energy: Optional[float] = None,
        color: Optional[List[float]] = None,
        radius: Optional[float] = None,
        spot_size: Optional[float] = None,
        spot_blend: Optional[float] = None,
        shape: Optional[str] = None,
        size: Optional[float] = None,
        size_y: Optional[float] = None,
        angle: Optional[float] = None,
    ) -> str:
        """Modify properties of an existing light.

        Args:
            name: Name of the light to modify
            energy: New intensity value
            color: New [r, g, b] color values 0-1
            radius: Soft shadow radius (point/spot lights)
            spot_size: Cone angle in degrees (spot lights only)
            spot_blend: Edge softness 0-1 (spot lights only)
            shape: SQUARE/RECTANGLE/DISK/ELLIPSE (area lights only)
            size: Primary size (area lights only)
            size_y: Secondary size (area lights only)
            angle: Angular diameter in radians (sun lights only)
        """
        params = {"name": name}
        if energy is not None:
            params["energy"] = energy
        if color is not None:
            params["color"] = color
        if radius is not None:
            params["radius"] = radius
        if spot_size is not None:
            params["spot_size"] = spot_size
        if spot_blend is not None:
            params["spot_blend"] = spot_blend
        if shape is not None:
            params["shape"] = shape
        if size is not None:
            params["size"] = size
        if size_y is not None:
            params["size_y"] = size_y
        if angle is not None:
            params["angle"] = angle

        result = await client.execute("set_light_properties", params)
        light = result.get("light", {})
        return f"✨ Updated light '{result['name']}' (type: {light.get('type')}, energy: {light.get('energy')})"

    @mcp.tool()
    async def get_light_info(name: str) -> str:
        """Get detailed information about a light.

        Args:
            name: Name of the light to query
        """
        result = await client.execute("get_light_info", {"name": name})
        light = result.get("light", {})

        lines = [f"Light: {result['name']}"]
        lines.append(f"  Type: {light.get('type')}")
        lines.append(f"  Location: {result['location']}")
        lines.append(f"  Rotation: {result.get('rotation')} degrees")
        lines.append(f"  Energy: {light.get('energy')}")
        lines.append(f"  Color: {light.get('color')}")
        lines.append(f"  Shadows: {'enabled' if light.get('use_shadow') else 'disabled'}")

        if light.get("type") == "POINT":
            lines.append(f"  Radius: {light.get('radius')}")
        elif light.get("type") == "SUN":
            lines.append(f"  Angle: {light.get('angle_degrees')}°")
        elif light.get("type") == "SPOT":
            lines.append(f"  Spot size: {light.get('spot_size_degrees')}°")
            lines.append(f"  Spot blend: {light.get('spot_blend')}")
            lines.append(f"  Radius: {light.get('radius')}")
        elif light.get("type") == "AREA":
            lines.append(f"  Shape: {light.get('shape')}")
            lines.append(f"  Size: {light.get('size')}")
            if light.get("size_y"):
                lines.append(f"  Size Y: {light.get('size_y')}")

        return "\n".join(lines)

    @mcp.tool()
    async def list_lights(
        type_filter: Optional[str] = None,
    ) -> str:
        """List all lights in the scene.

        Args:
            type_filter: Filter by light type - POINT, SUN, SPOT, or AREA
        """
        result = await client.execute(
            "list_lights",
            {"type": type_filter},
        )

        lights = result.get("lights", [])
        if not lights:
            if type_filter:
                return f"No {type_filter} lights found in the scene."
            return "No lights found in the scene."

        lines = [f"Scene contains {result['count']} light(s):"]
        for light in lights:
            loc = light["location"]
            visible = "visible" if light["visible"] else "hidden"
            energy = light["energy"]
            lines.append(
                f"  - {light['name']} ({light['type']}) at ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f}) "
                f"[{energy}W, {visible}]"
            )

        return "\n".join(lines)

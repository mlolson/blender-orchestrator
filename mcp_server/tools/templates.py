"""MCP tools for character templates.

Pre-configured templates for quickly creating characters with
proper proportions and integrated features.
"""

from typing import Optional, List


def register_tools(mcp, client):
    """Register template tools."""

    @mcp.tool()
    async def create_character_from_template(
        name: str = "Character",
        style: str = "cartoon",
        height: float = 1.8,
        skin_color: Optional[List[float]] = None,
        eye_color: Optional[List[float]] = None,
        add_eyes: bool = True,
        add_face_features: bool = True,
        add_outline: bool = False,
    ) -> str:
        """Create a complete character from a template.

        This creates a full humanoid character with proper proportions,
        materials, and optional face features based on the selected style.

        Args:
            name: Character name (default: "Character")
            style: Style preset - 'realistic', 'cartoon', 'chibi' (default: 'cartoon')
            height: Total height in Blender units (default: 1.8)
            skin_color: [r, g, b] skin color (default: warm skin tone)
            eye_color: [r, g, b] iris color (default: brown)
            add_eyes: Create eyes with shaders (default: True)
            add_face_features: Create nose and mouth (default: True)
            add_outline: Add cartoon outline for toon styles (default: False)
        """
        result = await client.execute(
            "create_character_from_template",
            {
                "name": name,
                "style": style,
                "height": height,
                "skin_color": skin_color or [0.85, 0.65, 0.55, 1.0],
                "eye_color": eye_color or [0.3, 0.2, 0.15, 1.0],
                "add_eyes": add_eyes,
                "add_face_features": add_face_features,
                "add_outline": add_outline,
            },
        )
        return (
            f"Created {result['proportions']} character '{result['name']}' "
            f"(height: {result['height']}, head: {result['head_height']:.3f})"
        )

    @mcp.tool()
    async def create_head_only(
        name: str = "Head",
        style: str = "cartoon",
        size: float = 0.25,
        skin_color: Optional[List[float]] = None,
        eye_color: Optional[List[float]] = None,
        add_eyes: bool = True,
        add_features: bool = True,
    ) -> str:
        """Create just a head with face features.

        Good for portraits, character busts, or when you want more control
        over the body separately.

        Args:
            name: Head name (default: "Head")
            style: Style preset - 'realistic', 'cartoon', 'chibi' (default: 'cartoon')
            size: Head height in Blender units (default: 0.25)
            skin_color: [r, g, b] skin color
            eye_color: [r, g, b] iris color
            add_eyes: Create eyes (default: True)
            add_features: Create nose and mouth (default: True)
        """
        result = await client.execute(
            "create_head_only",
            {
                "name": name,
                "style": style,
                "size": size,
                "skin_color": skin_color or [0.85, 0.65, 0.55, 1.0],
                "eye_color": eye_color or [0.3, 0.5, 0.7, 1.0],
                "add_eyes": add_eyes,
                "add_features": add_features,
            },
        )
        return f"Created {result['style']} head '{result['name']}' (size: {result['size']})"

    @mcp.tool()
    async def list_available_templates() -> str:
        """List available character templates and their options."""
        result = await client.execute(
            "list_available_templates",
            {},
        )

        output = "Available Templates:\n"
        for t in result['templates']:
            output += f"\n{t['name']}:\n  {t['description']}\n"
            output += f"  Styles: {', '.join(t['styles'])}\n"

        output += "\nProportion Presets:\n"
        for p in result['proportion_presets']:
            output += f"\n{p['name']} ({p['total_heads']} heads tall):\n  {p['description']}\n"

        return output

    @mcp.tool()
    async def create_integrated_eye(
        head: str,
        position: List[float],
        radius: float = 0.025,
        iris_color: Optional[List[float]] = None,
        create_socket: bool = True,
    ) -> str:
        """Create an eye properly integrated into a head mesh.

        This creates both the eye socket depression and eyeball,
        avoiding the 'stuck-on' look of separate eye spheres.

        Args:
            head: Head mesh object name
            position: [x, y, z] eye center position
            radius: Eye radius (default: 0.025)
            iris_color: [r, g, b] iris color (default: blue)
            create_socket: Create socket depression (default: True)
        """
        result = await client.execute(
            "create_integrated_eye",
            {
                "head": head,
                "position": position,
                "radius": radius,
                "iris_color": iris_color or [0.2, 0.4, 0.7, 1.0],
                "create_socket": create_socket,
            },
        )
        return f"Created eye '{result['eye_name']}' integrated into '{result['head']}'"

    @mcp.tool()
    async def add_cartoon_outline(
        name: str,
        thickness: float = 0.02,
        color: Optional[List[float]] = None,
    ) -> str:
        """Add cartoon-style outline to an object.

        Uses solidify modifier with flipped normals for the classic
        cartoon/anime outline effect.

        Args:
            name: Object name
            thickness: Outline thickness (default: 0.02)
            color: [r, g, b] outline color (default: black)
        """
        result = await client.execute(
            "add_cartoon_outline",
            {
                "name": name,
                "thickness": thickness,
                "color": color or [0.0, 0.0, 0.0, 1.0],
            },
        )
        return f"Added outline to '{result['name']}' with thickness {result['thickness']}"

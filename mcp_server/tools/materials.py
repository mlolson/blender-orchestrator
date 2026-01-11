"""MCP tools for material operations."""

from typing import Optional, List
import json


def register_tools(mcp, client):
    """Register material tools."""

    @mcp.tool()
    async def create_material(
        name: str = "Material",
        color: Optional[List[float]] = None,
        metallic: float = 0.0,
        roughness: float = 0.5,
    ) -> str:
        """Create a new PBR material.

        Args:
            name: Name for the material (default: "Material")
            color: RGB or RGBA color values 0.0-1.0 (default: [0.8, 0.8, 0.8])
            metallic: Metallic factor 0.0-1.0 (default: 0.0)
            roughness: Roughness factor 0.0-1.0 (default: 0.5)
        """
        result = await client.execute(
            "create_material",
            {
                "name": name,
                "color": color or [0.8, 0.8, 0.8, 1.0],
                "metallic": metallic,
                "roughness": roughness,
            },
        )
        return f"Created material '{result['name']}' with color {result.get('color', [])[:3]}, metallic={result.get('metallic', 0)}, roughness={result.get('roughness', 0.5)}"

    @mcp.tool()
    async def assign_material(
        object_name: str,
        material_name: str,
    ) -> str:
        """Assign an existing material to an object.

        Args:
            object_name: Name of the object
            material_name: Name of the material to assign
        """
        result = await client.execute(
            "assign_material",
            {
                "object_name": object_name,
                "material_name": material_name,
            },
        )
        return f"Assigned material '{result['material']}' to '{result['object']}'"

    @mcp.tool()
    async def modify_material(
        material_name: str,
        color: Optional[List[float]] = None,
        metallic: Optional[float] = None,
        roughness: Optional[float] = None,
    ) -> str:
        """Modify properties of an existing material.

        Args:
            material_name: Name of the material to modify
            color: New RGB or RGBA color values 0.0-1.0
            metallic: New metallic factor 0.0-1.0
            roughness: New roughness factor 0.0-1.0
        """
        params = {"material_name": material_name}
        if color is not None:
            params["color"] = color
        if metallic is not None:
            params["metallic"] = metallic
        if roughness is not None:
            params["roughness"] = roughness

        result = await client.execute("modify_material", params)
        return f"Modified material '{result['name']}'"

    @mcp.tool()
    async def list_materials() -> str:
        """List all materials in the Blender file."""
        result = await client.execute("list_materials", {})
        materials = result.get("materials", [])

        if not materials:
            return "No materials found in the scene."

        lines = [f"Found {result['count']} material(s):"]
        for mat in materials:
            color = mat.get("color", [])[:3] if mat.get("color") else "N/A"
            lines.append(
                f"  - {mat['name']}: color={color}, metallic={mat.get('metallic', 'N/A')}, roughness={mat.get('roughness', 'N/A')}"
            )

        return "\n".join(lines)

    @mcp.tool()
    async def create_and_assign_material(
        object_name: str,
        material_name: str = "Material",
        color: Optional[List[float]] = None,
        metallic: float = 0.0,
        roughness: float = 0.5,
    ) -> str:
        """Create a new material and assign it to an object in one step.

        Args:
            object_name: Name of the object to assign the material to
            material_name: Name for the new material (default: "Material")
            color: RGB or RGBA color values 0.0-1.0 (default: [0.8, 0.8, 0.8])
            metallic: Metallic factor 0.0-1.0 (default: 0.0)
            roughness: Roughness factor 0.0-1.0 (default: 0.5)
        """
        result = await client.execute(
            "create_and_assign_material",
            {
                "object_name": object_name,
                "name": material_name,
                "color": color or [0.8, 0.8, 0.8, 1.0],
                "metallic": metallic,
                "roughness": roughness,
            },
        )
        mat = result.get("material", {})
        return f"Created and assigned material '{mat.get('name', material_name)}' to '{object_name}'"

    @mcp.tool()
    async def delete_material(material_name: str) -> str:
        """Delete a material from the Blender file.

        Args:
            material_name: Name of the material to delete
        """
        result = await client.execute(
            "delete_material",
            {"material_name": material_name},
        )
        return f"Deleted material '{result['deleted']}'"

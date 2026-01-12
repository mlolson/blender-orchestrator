"""MCP tools for skin modifier and skeleton-based mesh generation.

The skin modifier creates mesh geometry around a skeleton of edges,
perfect for generating humanoid bodies with proper joint topology.
"""

from typing import Optional, List, Dict


def register_tools(mcp, client):
    """Register skinning/skeleton tools."""

    @mcp.tool()
    async def create_skin_mesh(
        name: str,
        vertices: List[List[float]],
        edges: List[List[int]],
        default_radius: float = 0.1,
        subdivision_levels: int = 1,
    ) -> str:
        """Create a mesh with skin modifier from vertices and edges.

        The skin modifier generates smooth mesh geometry around connected edges,
        perfect for creating humanoid bodies with natural joint topology.

        Args:
            name: Mesh name
            vertices: List of [x, y, z] vertex positions forming the skeleton
            edges: List of [v1, v2] vertex index pairs defining connections
            default_radius: Initial skin radius (default: 0.1)
            subdivision_levels: Subdivision for smoothness (default: 1)
        """
        result = await client.execute(
            "create_skin_mesh",
            {
                "name": name,
                "vertices": vertices,
                "edges": edges,
                "default_radius": default_radius,
                "subdivision_levels": subdivision_levels,
            },
        )
        return f"Created skin mesh '{result['name']}'"

    @mcp.tool()
    async def set_skin_radius(
        name: str,
        vertices: List[Dict],
    ) -> str:
        """Set skin radius for specific vertices.

        This controls how thick the generated mesh is at each point.

        Args:
            name: Skin mesh object name
            vertices: List of {"index": int, "radius": float or [rx, ry]} dicts
        """
        result = await client.execute(
            "set_skin_radius",
            {
                "name": name,
                "vertices": vertices,
            },
        )
        return f"Modified {result['modified_vertices']} vertex radii on '{result['name']}'"

    @mcp.tool()
    async def apply_skin_modifier(
        name: str,
        apply_subdivision: bool = True,
    ) -> str:
        """Apply the skin modifier to convert to a regular mesh.

        Args:
            name: Skin mesh object name
            apply_subdivision: Also apply subdivision surface (default: True)
        """
        result = await client.execute(
            "apply_skin_modifier",
            {
                "name": name,
                "apply_subdivision": apply_subdivision,
            },
        )
        return f"Applied skin modifier to '{result['name']}' ({result['vertex_count']} vertices)"

    @mcp.tool()
    async def create_humanoid_skeleton(
        name: str = "HumanoidSkeleton",
        height: float = 1.8,
        style: str = "realistic",
    ) -> str:
        """Create a complete humanoid skeleton structure for skin modifier.

        This creates a vertex/edge skeleton suitable for generating a
        humanoid body with proper proportions and joint topology.

        Args:
            name: Mesh name (default: "HumanoidSkeleton")
            height: Total height in Blender units (default: 1.8)
            style: Proportion style - 'realistic', 'cartoon', 'chibi' (default: 'realistic')
        """
        result = await client.execute(
            "create_humanoid_skeleton",
            {
                "name": name,
                "height": height,
                "style": style,
            },
        )
        return f"Created {result['style']} humanoid skeleton '{result['name']}' with {result['vertex_count']} vertices. {result['message']}"

    @mcp.tool()
    async def create_armature(
        name: str = "Armature",
        location: Optional[List[float]] = None,
    ) -> str:
        """Create an armature (skeleton) object for rigging.

        Args:
            name: Armature name (default: "Armature")
            location: [x, y, z] position (default: [0, 0, 0])
        """
        result = await client.execute(
            "create_armature",
            {
                "name": name,
                "location": location or [0, 0, 0],
            },
        )
        return f"Created armature '{result['name']}'"

    @mcp.tool()
    async def add_bone(
        armature: str,
        name: str,
        head: List[float],
        tail: List[float],
        parent: Optional[str] = None,
        connected: bool = False,
    ) -> str:
        """Add a bone to an armature.

        Args:
            armature: Armature object name
            name: Bone name
            head: [x, y, z] bone head (start) position
            tail: [x, y, z] bone tail (end) position
            parent: Parent bone name (optional)
            connected: Connect to parent's tail (default: False)
        """
        result = await client.execute(
            "add_bone",
            {
                "armature": armature,
                "name": name,
                "head": head,
                "tail": tail,
                "parent": parent,
                "connected": connected,
            },
        )
        return f"Added bone '{result['bone']}' to armature '{result['armature']}'"

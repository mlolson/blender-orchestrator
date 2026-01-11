"""MCP tools for Blender operations."""

from . import primitives
from . import transforms
from . import mesh_editing
from . import materials
from . import rendering
from . import scene


def register_all_tools(mcp, client):
    """Register all tool modules with the MCP server."""
    primitives.register_tools(mcp, client)
    transforms.register_tools(mcp, client)
    mesh_editing.register_tools(mcp, client)
    materials.register_tools(mcp, client)
    rendering.register_tools(mcp, client)
    scene.register_tools(mcp, client)

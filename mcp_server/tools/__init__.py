"""MCP tools for Blender operations."""

from . import primitives
from . import transforms
from . import mesh_editing
from . import materials
from . import rendering
from . import scene
from . import metaballs
from . import curves
from . import skinning
from . import templates
from . import ai_mesh_generation
from . import polyhaven
from . import ai_texture_generation
from . import spatial
from . import lighting


def register_all_tools(mcp, client):
    """Register all tool modules with the MCP server."""
    primitives.register_tools(mcp, client)
    transforms.register_tools(mcp, client)
    mesh_editing.register_tools(mcp, client)
    materials.register_tools(mcp, client)
    rendering.register_tools(mcp, client)
    scene.register_tools(mcp, client)
    # New tools for improved character creation
    metaballs.register_tools(mcp, client)
    curves.register_tools(mcp, client)
    skinning.register_tools(mcp, client)
    templates.register_tools(mcp, client)
    # AI-powered generation tools
    ai_mesh_generation.register_tools(mcp, client)
    # Free asset library tools
    polyhaven.register_tools(mcp, client)
    ai_texture_generation.register_tools(mcp, client)
    # Spatial reasoning tools
    spatial.register_tools(mcp, client)
    # Lighting tools
    lighting.register_tools(mcp, client)

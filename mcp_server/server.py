"""MCP Server for Blender integration with Claude."""

from mcp.server.fastmcp import FastMCP
from .blender_client import BlenderClient
from .tools import register_all_tools

# Initialize MCP server
mcp = FastMCP("blender-mcp")

# Initialize Blender client
client = BlenderClient(host="localhost", port=8765)

# Register all tools
register_all_tools(mcp, client)


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

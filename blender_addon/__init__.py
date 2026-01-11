bl_info = {
    "name": "Blender MCP Bridge",
    "author": "Claude Code",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP",
    "description": "HTTP server bridge for MCP integration with Claude",
    "category": "Development",
}

import bpy
from .operators.server_operator import (
    BLENDER_OT_mcp_server_start,
    BLENDER_OT_mcp_server_stop,
)
from .server.http_server import get_server


class MCP_PT_main_panel(bpy.types.Panel):
    """MCP Server Control Panel"""
    bl_label = "MCP Server"
    bl_idname = "MCP_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MCP'

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        server = get_server()
        is_running = server is not None and server.running

        if is_running:
            layout.label(text=f"Server running on port {server.port}", icon='CHECKMARK')
            layout.operator("blender.mcp_server_stop", text="Stop Server", icon='CANCEL')
        else:
            layout.label(text="Server stopped", icon='X')
            layout.operator("blender.mcp_server_start", text="Start Server", icon='PLAY')

        layout.separator()
        layout.prop(context.scene, "mcp_server_port")


def register():
    bpy.types.Scene.mcp_server_port = bpy.props.IntProperty(
        name="Port",
        description="Port for the MCP HTTP server",
        default=8765,
        min=1024,
        max=65535
    )

    bpy.utils.register_class(BLENDER_OT_mcp_server_start)
    bpy.utils.register_class(BLENDER_OT_mcp_server_stop)
    bpy.utils.register_class(MCP_PT_main_panel)


def unregister():
    # Stop server if running
    server = get_server()
    if server and server.running:
        server.shutdown()

    bpy.utils.unregister_class(MCP_PT_main_panel)
    bpy.utils.unregister_class(BLENDER_OT_mcp_server_stop)
    bpy.utils.unregister_class(BLENDER_OT_mcp_server_start)

    del bpy.types.Scene.mcp_server_port


if __name__ == "__main__":
    register()

"""Modal timer operator for MCP server."""

import bpy
from ..server.http_server import BlenderHTTPServer, get_server, set_server
from ..handlers import get_handler_registry


class BLENDER_OT_mcp_server_start(bpy.types.Operator):
    """Start the MCP HTTP server."""

    bl_idname = "blender.mcp_server_start"
    bl_label = "Start MCP Server"
    bl_options = {"REGISTER"}

    _timer = None

    def modal(self, context, event):
        if event.type == "TIMER":
            server = get_server()
            if server and server.running:
                # Poll for new connections
                server.poll()
                # Process any queued requests (in main thread - safe for Blender API)
                server.process_queue(get_handler_registry())
            else:
                # Server was stopped
                self.cancel(context)
                return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        # Check if server already running
        existing_server = get_server()
        if existing_server and existing_server.running:
            self.report({"WARNING"}, "Server is already running")
            return {"CANCELLED"}

        # Get port from scene property
        port = context.scene.mcp_server_port

        # Start server
        server = BlenderHTTPServer(host="localhost", port=port)
        try:
            server.start()
        except OSError as e:
            self.report({"ERROR"}, f"Failed to start server: {e}")
            return {"CANCELLED"}

        set_server(server)

        # Start timer (poll every 0.01 seconds for responsiveness)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)

        self.report({"INFO"}, f"MCP Server started on port {port}")
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None


class BLENDER_OT_mcp_server_stop(bpy.types.Operator):
    """Stop the MCP HTTP server."""

    bl_idname = "blender.mcp_server_stop"
    bl_label = "Stop MCP Server"
    bl_options = {"REGISTER"}

    def execute(self, context):
        server = get_server()
        if server and server.running:
            server.shutdown()
            set_server(None)
            self.report({"INFO"}, "MCP Server stopped")
        else:
            self.report({"WARNING"}, "Server is not running")

        return {"FINISHED"}

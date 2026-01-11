"""Non-blocking HTTP server for Blender MCP bridge."""

import http.server
import json
import select
import socketserver
import threading
import time
from queue import Queue, Empty
from typing import Any, Callable, Dict, Optional

# Global server instance
_server: Optional["BlenderHTTPServer"] = None


def get_server() -> Optional["BlenderHTTPServer"]:
    """Get the global server instance."""
    return _server


def set_server(server: Optional["BlenderHTTPServer"]) -> None:
    """Set the global server instance."""
    global _server
    _server = server


class NonBlockingHTTPServer(socketserver.TCPServer):
    """HTTP server that can be polled without blocking."""

    allow_reuse_address = True
    timeout = 0  # Non-blocking

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        request_queue: Queue,
        response_dict: Dict[str, Any],
    ):
        self.request_queue = request_queue
        self.response_dict = response_dict
        self.response_events: Dict[str, threading.Event] = {}
        super().__init__(server_address, RequestHandlerClass)

    def handle_request_noblock(self) -> None:
        """Handle one request if available, non-blocking."""
        try:
            ready = select.select([self.socket], [], [], 0)
            if ready[0]:
                self.handle_request()
        except Exception:
            pass


class BlenderRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles HTTP requests and queues them for main thread processing."""

    def do_POST(self) -> None:
        """Handle POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            request = json.loads(post_data.decode("utf-8"))
            request_id = f"{id(request)}_{time.time()}"
            request["_request_id"] = request_id

            # Create event for this request
            event = threading.Event()
            self.server.response_events[request_id] = event

            # Queue request for main thread
            self.server.request_queue.put(request)

            # Wait for response (with timeout)
            event.wait(timeout=30.0)

            # Get response
            if request_id in self.server.response_dict:
                response = self.server.response_dict.pop(request_id)
                self._send_json_response(200, response)
            else:
                self._send_json_response(
                    500, {"success": False, "error": "Request timeout"}
                )

            # Cleanup
            if request_id in self.server.response_events:
                del self.server.response_events[request_id]

        except json.JSONDecodeError as e:
            self._send_json_response(400, {"success": False, "error": f"Invalid JSON: {e}"})
        except Exception as e:
            self._send_json_response(500, {"success": False, "error": str(e)})

    def do_GET(self) -> None:
        """Handle GET requests (health check)."""
        if self.path == "/health":
            self._send_json_response(200, {"status": "ok", "server": "blender-mcp"})
        else:
            self._send_json_response(404, {"error": "Not found"})

    def _send_json_response(self, status: int, data: Dict[str, Any]) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


class BlenderHTTPServer:
    """Manages the HTTP server lifecycle."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.request_queue: Queue = Queue()
        self.response_dict: Dict[str, Any] = {}
        self.server: Optional[NonBlockingHTTPServer] = None
        self.running = False

    def start(self) -> None:
        """Start the server."""
        if self.running:
            return

        self.server = NonBlockingHTTPServer(
            (self.host, self.port),
            BlenderRequestHandler,
            self.request_queue,
            self.response_dict,
        )
        self.running = True
        print(f"Blender MCP server started on {self.host}:{self.port}")

    def poll(self) -> None:
        """Poll for requests (called from modal timer)."""
        if self.server and self.running:
            self.server.handle_request_noblock()

    def process_queue(self, handler_registry: Dict[str, Callable]) -> None:
        """Process queued requests in main thread."""
        try:
            request = self.request_queue.get_nowait()
            request_id = request.pop("_request_id")

            # Route to appropriate handler
            action = request.get("action")
            handler = handler_registry.get(action)

            if handler:
                try:
                    result = handler(request.get("params", {}))
                    response = {"success": True, "result": result}
                except Exception as e:
                    response = {"success": False, "error": str(e)}
            else:
                response = {"success": False, "error": f"Unknown action: {action}"}

            # Store response and signal
            self.response_dict[request_id] = response
            if self.server and request_id in self.server.response_events:
                self.server.response_events[request_id].set()

        except Empty:
            pass

    def shutdown(self) -> None:
        """Shutdown the server."""
        if self.server:
            self.running = False
            self.server.server_close()
            self.server = None
            print("Blender MCP server stopped")

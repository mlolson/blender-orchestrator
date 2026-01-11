"""MCP tools for rendering operations."""

from typing import Optional


def register_tools(mcp, client):
    """Register rendering tools."""

    @mcp.tool()
    async def render_image(
        output_path: Optional[str] = None,
        resolution_x: int = 1920,
        resolution_y: int = 1080,
        samples: Optional[int] = None,
        file_format: str = "PNG",
    ) -> str:
        """Render the current scene to an image file.

        Args:
            output_path: Path to save the rendered image (uses temp file if not specified)
            resolution_x: Image width in pixels (default: 1920)
            resolution_y: Image height in pixels (default: 1080)
            samples: Render samples (for Cycles engine)
            file_format: Image format - PNG, JPEG, etc. (default: PNG)
        """
        result = await client.execute(
            "render_to_file",
            {
                "output_path": output_path,
                "resolution_x": resolution_x,
                "resolution_y": resolution_y,
                "samples": samples,
                "file_format": file_format,
            },
        )
        return f"Rendered image to '{result['output_path']}' at {result['resolution'][0]}x{result['resolution'][1]}"

    @mcp.tool()
    async def capture_viewport(
        output_path: Optional[str] = None,
    ) -> str:
        """Capture a screenshot of the current 3D viewport.

        This captures what you see in the viewport, which is faster than a full render.
        Returns a base64-encoded PNG image that can be displayed directly.

        Args:
            output_path: Optional path to save the image (uses temp file if not specified)
        """
        result = await client.execute(
            "render_viewport",
            {
                "output_path": output_path,
                "return_base64": True,
            },
        )

        if result.get("image_base64"):
            # Return as data URL for direct display
            return f"data:image/png;base64,{result['image_base64']}"
        elif result.get("output_path"):
            return f"Viewport captured to '{result['output_path']}'"
        else:
            return "Viewport capture completed"

    @mcp.tool()
    async def set_render_settings(
        engine: Optional[str] = None,
        resolution_x: Optional[int] = None,
        resolution_y: Optional[int] = None,
        samples: Optional[int] = None,
        file_format: Optional[str] = None,
    ) -> str:
        """Configure render settings.

        Args:
            engine: Render engine - EEVEE, CYCLES, or WORKBENCH
            resolution_x: Image width in pixels
            resolution_y: Image height in pixels
            samples: Render samples (affects quality and render time)
            file_format: Output format - PNG, JPEG, OPEN_EXR, etc.
        """
        params = {}
        if engine is not None:
            params["engine"] = engine
        if resolution_x is not None:
            params["resolution_x"] = resolution_x
        if resolution_y is not None:
            params["resolution_y"] = resolution_y
        if samples is not None:
            params["samples"] = samples
        if file_format is not None:
            params["file_format"] = file_format

        result = await client.execute("set_render_settings", params)
        return f"Render settings updated: engine={result['engine']}, resolution={result['resolution'][0]}x{result['resolution'][1]}, format={result['file_format']}"

    @mcp.tool()
    async def get_render_settings() -> str:
        """Get current render settings."""
        result = await client.execute("get_render_settings", {})

        lines = ["Current render settings:"]
        lines.append(f"  Engine: {result['engine']}")
        lines.append(f"  Resolution: {result['resolution'][0]}x{result['resolution'][1]} ({result.get('resolution_percentage', 100)}%)")
        lines.append(f"  Format: {result['file_format']}")
        lines.append(f"  FPS: {result.get('fps', 'N/A')}")
        if "samples" in result:
            lines.append(f"  Samples: {result['samples']}")
        if "use_denoising" in result:
            lines.append(f"  Denoising: {result['use_denoising']}")

        return "\n".join(lines)

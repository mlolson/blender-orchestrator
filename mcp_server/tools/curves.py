"""MCP tools for curve-based modeling.

Curves are useful for creating hair, eyebrows, tentacles, pipes,
and other shapes that follow a path.
"""

from typing import Optional, List, Dict, Any


def register_tools(mcp, client):
    """Register curve modeling tools."""

    @mcp.tool()
    async def create_bezier_curve(
        name: str = "BezierCurve",
        points: Optional[List[List[float]]] = None,
        cyclic: bool = False,
        location: Optional[List[float]] = None,
    ) -> str:
        """Create a bezier curve from control points.

        Args:
            name: Curve name (default: "BezierCurve")
            points: List of [x, y, z] control points (at least 2 required)
            cyclic: Close the curve into a loop (default: False)
            location: [x, y, z] object location
        """
        if not points or len(points) < 2:
            points = [[0, 0, 0], [1, 0, 0], [2, 0, 1]]

        result = await client.execute(
            "create_bezier_curve",
            {
                "name": name,
                "points": points,
                "cyclic": cyclic,
                "location": location or [0, 0, 0],
            },
        )
        return f"Created bezier curve '{result['name']}'"

    @mcp.tool()
    async def set_curve_bevel(
        name: str,
        depth: float = 0.1,
        resolution: int = 4,
    ) -> str:
        """Add thickness/bevel to a curve, turning it into a tube.

        Args:
            name: Curve object name
            depth: Tube radius/thickness (default: 0.1)
            resolution: Smoothness of the tube (0-32, default: 4)
        """
        result = await client.execute(
            "set_curve_bevel",
            {
                "name": name,
                "depth": depth,
                "resolution": resolution,
            },
        )
        return f"Set bevel on curve '{result['name']}' with depth {depth}"

    @mcp.tool()
    async def convert_curve_to_mesh(name: str) -> str:
        """Convert a curve to a mesh for further editing.

        Args:
            name: Curve object name
        """
        result = await client.execute(
            "convert_curve_to_mesh",
            {"name": name},
        )
        return f"Converted curve to mesh '{result['name']}' ({result['vertex_count']} vertices)"

    @mcp.tool()
    async def create_hair_curves(
        name: str = "Hair",
        count: int = 10,
        length: float = 0.3,
        segments: int = 4,
        curl: float = 0.0,
        gravity: float = 0.5,
    ) -> str:
        """Create multiple curves suitable for hair strands.

        Args:
            name: Base name for the hair curves
            count: Number of hair strands (default: 10)
            length: Hair length (default: 0.3)
            segments: Segments per strand (default: 4)
            curl: Curl amount 0-1 (default: 0, no curl)
            gravity: How much strands droop (default: 0.5)
        """
        result = await client.execute(
            "create_hair_curves",
            {
                "name": name,
                "count": count,
                "length": length,
                "segments": segments,
                "curl": curl,
                "gravity": gravity,
            },
        )
        return f"Created {result['count']} hair curves"

    @mcp.tool()
    async def get_curve_points(name: str) -> str:
        """Get all control points from a curve.

        Args:
            name: Curve object name
        """
        result = await client.execute(
            "get_curve_points",
            {"name": name},
        )
        splines_info = []
        for s in result['splines']:
            splines_info.append(f"  Spline {s['index']}: {s['type']}, {s['point_count']} points")
        return f"Curve '{result['name']}' has {result['spline_count']} splines:\n" + "\n".join(splines_info)

    @mcp.tool()
    async def create_curve_circle(
        name: str = "CurveCircle",
        radius: float = 1.0,
        location: Optional[List[float]] = None,
    ) -> str:
        """Create a circular curve (useful as bevel profile).

        Args:
            name: Curve name (default: "CurveCircle")
            radius: Circle radius (default: 1.0)
            location: [x, y, z] object location
        """
        result = await client.execute(
            "create_curve_circle",
            {
                "name": name,
                "radius": radius,
                "location": location or [0, 0, 0],
            },
        )
        return f"Created curve circle '{result['name']}'"

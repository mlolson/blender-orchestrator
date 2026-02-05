"""MCP tools for spatial reasoning and scene understanding."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register spatial reasoning tools."""

    @mcp.tool()
    async def validate_transform(
        name: str,
        action: str = "move",
        delta: Optional[List[float]] = None,
        absolute: Optional[List[float]] = None,
        factor: Optional[List[float]] = None,
    ) -> str:
        """Validate a transformation before applying it.
        
        Check if moving, rotating, or scaling an object would cause problems
        like collisions with other objects, going below ground, or extreme scales.
        
        ALWAYS use this before applying transforms to avoid errors.
        
        Args:
            name: Name of the object to transform
            action: Type of transform - "move", "rotate", or "scale"
            delta: Relative change [x, y, z] (for move: meters, rotate: degrees, scale: multiplier)
            absolute: Absolute target value [x, y, z] (overrides delta)
            factor: Scale factor [x, y, z] (for scale action only)
        
        Returns:
            Validation result with issues, warnings, and suggestions
        
        Examples:
            validate_transform("Chair", "move", delta=[1, 0, 0])
            validate_transform("Table", "rotate", absolute=[0, 0, 45])
            validate_transform("Lamp", "scale", factor=[2, 2, 2])
        """
        params = {"name": name, "action": action}
        
        if absolute is not None:
            params["absolute"] = absolute
        elif delta is not None:
            params["delta"] = delta
        elif factor is not None:
            params["factor"] = factor
        else:
            params["delta"] = [0, 0, 0]  # Default to no change for validation check
        
        result = await client.execute("validate_transform", params)
        
        lines = [f"Transform validation for '{result['object']}' ({result['action']}):"]
        lines.append("")
        
        # Show current state
        lines.append("Current state:")
        lines.append(f"  Position: ({result['current_position'][0]:.2f}, {result['current_position'][1]:.2f}, {result['current_position'][2]:.2f})")
        lines.append(f"  Rotation: ({result['current_rotation'][0]:.1f}°, {result['current_rotation'][1]:.1f}°, {result['current_rotation'][2]:.1f}°)")
        lines.append(f"  Scale: ({result['current_scale'][0]:.2f}, {result['current_scale'][1]:.2f}, {result['current_scale'][2]:.2f})")
        
        # Show proposed state
        lines.append("")
        lines.append("After transform:")
        if "new_position" in result:
            pos = result["new_position"]
            lines.append(f"  Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        if "new_rotation" in result:
            rot = result["new_rotation"]
            lines.append(f"  Rotation: ({rot[0]:.1f}°, {rot[1]:.1f}°, {rot[2]:.1f}°)")
        if "new_scale" in result:
            scl = result["new_scale"]
            lines.append(f"  Scale: ({scl[0]:.2f}, {scl[1]:.2f}, {scl[2]:.2f})")
        
        lines.append("")
        
        # Show validation result
        if result["valid"]:
            lines.append("✅ VALID - Transform can be applied safely")
        else:
            lines.append("❌ INVALID - Issues found:")
            for issue in result["issues"]:
                lines.append(f"   • {issue}")
        
        if result["warnings"]:
            lines.append("")
            lines.append("⚠️  Warnings:")
            for warning in result["warnings"]:
                lines.append(f"   • {warning}")
        
        if result["suggestions"]:
            lines.append("")
            lines.append("💡 Suggestions:")
            for suggestion in result["suggestions"]:
                lines.append(f"   • {suggestion}")
        
        return "\n".join(lines)

    @mcp.tool()
    async def get_safe_movement_range(
        name: str,
        max_distance: float = 10.0,
    ) -> str:
        """Calculate how far an object can safely move in each direction.
        
        Returns the maximum distance the object can move in each direction
        (±X, ±Y, ±Z) before hitting another object or the ground.
        
        Useful for understanding movement constraints before repositioning.
        
        Args:
            name: Name of the object to analyze
            max_distance: Maximum distance to check (meters)
        
        Returns:
            Safe movement distances for each direction
        """
        result = await client.execute(
            "get_safe_movement_range",
            {"name": name, "max_distance": max_distance},
        )
        
        lines = [f"Safe movement range for '{result['object']}':"]
        pos = result["position"]
        lines.append(f"Current position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        lines.append("")
        
        lines.append("Maximum safe movement:")
        for direction, distance in result["safe_distances"].items():
            if distance >= result["max_checked"]:
                lines.append(f"  {direction}: >{distance:.1f}m (clear)")
            elif distance < 0.1:
                lines.append(f"  {direction}: BLOCKED")
            else:
                lines.append(f"  {direction}: {distance:.1f}m")
        
        return "\n".join(lines)

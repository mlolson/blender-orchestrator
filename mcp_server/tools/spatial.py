"""MCP tools for spatial reasoning and scene understanding."""

from typing import Optional


def register_tools(mcp, client):
    """Register spatial reasoning tools."""

    @mcp.tool()
    async def move_object_semantic(
        name: str,
        instruction: str,
        dry_run: bool = False,
    ) -> str:
        """Move an object using natural language instructions.
        
        Instead of specifying exact coordinates, describe where you want
        the object to go in plain English.
        
        Supported instructions:
        - "place on the desk" / "put on the table"
        - "put on the left corner of the table"
        - "move next to the chair"
        - "place to the left of the sofa"
        - "put in front of the camera"
        - "move behind the bookshelf"
        - "place above the floor"
        - "move 2 meters left"
        - "move 1.5m forward"
        
        Args:
            name: Name of the object to move
            instruction: Natural language positioning instruction
            dry_run: If True, calculate but don't apply the movement
        
        Returns:
            New position and movement details
        
        Examples:
            move_object_semantic("Lamp", "place on the desk")
            move_object_semantic("Chair", "move 1 meter back")
            move_object_semantic("Vase", "put on the left corner of the table")
        """
        result = await client.execute(
            "move_object_semantic",
            {"name": name, "instruction": instruction, "dry_run": dry_run},
        )
        
        if not result.get("success"):
            lines = [f"❌ Failed to move '{name}'"]
            lines.append(f"   Error: {result.get('error', 'Unknown error')}")
            if result.get("hint"):
                lines.append(f"   Hint: {result['hint']}")
            if result.get("available_objects"):
                lines.append(f"   Available: {', '.join(result['available_objects'][:5])}")
            return "\n".join(lines)
        
        lines = [f"{'🔍 DRY RUN - ' if result['dry_run'] else ''}Moving '{result['object']}':"]
        lines.append(f"   Instruction: {result['instruction']}")
        lines.append("")
        
        orig = result["original_position"]
        new = result["new_position"]
        move = result["movement"]
        
        lines.append(f"   From: ({orig[0]:.2f}, {orig[1]:.2f}, {orig[2]:.2f})")
        lines.append(f"   To:   ({new[0]:.2f}, {new[1]:.2f}, {new[2]:.2f})")
        lines.append(f"   Movement: ({move[0]:+.2f}, {move[1]:+.2f}, {move[2]:+.2f})")
        
        parsed = result.get("parsed", {})
        if parsed.get("relation") and parsed.get("reference_object"):
            lines.append(f"   Relation: {parsed['relation'].replace('_', ' ')} '{parsed['reference_object']}'")
        elif parsed.get("direction"):
            lines.append(f"   Direction: {parsed['distance']}m {parsed['direction']}")
        
        if result["dry_run"]:
            lines.append("")
            lines.append("   ℹ️  Dry run - object not moved. Remove dry_run=True to apply.")
        else:
            lines.append("")
            lines.append("   ✅ Object moved successfully")
        
        return "\n".join(lines)

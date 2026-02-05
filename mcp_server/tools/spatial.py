"""MCP tools for spatial reasoning and scene understanding."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register spatial reasoning tools."""

    @mcp.tool()
    async def query_spatial(question: str) -> str:
        """Answer natural language spatial queries about the scene.
        
        Ask questions about object positions and relationships in plain English.
        
        Supported query formats:
        - "what is on the table?"
        - "what is to the left of the chair?"
        - "what is near the desk?"
        - "what is above the floor?"
        - "what is behind the sofa?"
        - "what is in front of the camera?"
        - "is there anything inside the box?"
        
        Args:
            question: Natural language question about spatial relationships
        
        Returns:
            List of objects matching the spatial query with distances
        """
        result = await client.execute("query_spatial", {"question": question})
        
        if not result.get("success"):
            error_msg = result.get("error", "Query failed")
            lines = [f"❌ {error_msg}"]
            if result.get("available_objects"):
                lines.append("\nAvailable objects:")
                for obj in result["available_objects"][:10]:
                    lines.append(f"  • {obj}")
            return "\n".join(lines)
        
        lines = [f"Query: {result['question']}"]
        lines.append(f"Looking for objects {result['query_type'].replace('_', ' ')} '{result['reference_object']}'")
        lines.append("")
        
        if result["count"] == 0:
            lines.append("No objects found matching this query.")
        else:
            lines.append(f"Found {result['count']} object(s):")
            for obj in result["results"]:
                lines.append(f"  • {obj['name']} ({obj['type']}) - {obj['distance']}m away")
        
        return "\n".join(lines)

    @mcp.tool()
    async def find_placement_position(
        reference: str,
        relation: str = "on",
        object_size: Optional[List[float]] = None,
    ) -> str:
        """Find a valid position to place an object relative to another object.
        
        Use this before placing objects to get correct positioning.
        
        Args:
            reference: Name of the reference object (e.g., "Table", "Desk")
            relation: Spatial relation - "on", "next_to", "left_of", "right_of", 
                     "in_front_of", "behind"
            object_size: Approximate [width, depth, height] of object to place.
                        Defaults to [0.5, 0.5, 0.5] meters.
        
        Returns:
            Suggested position coordinates and collision warnings
        
        Example:
            find_placement_position("Desk", "on", [0.3, 0.3, 0.4])
            → Place at (1.20, 2.00, 0.85) - Clear space
        """
        if object_size is None:
            object_size = [0.5, 0.5, 0.5]
        
        result = await client.execute(
            "find_placement_position",
            {
                "reference": reference,
                "relation": relation,
                "object_size": object_size,
            },
        )
        
        lines = [f"Placement position {relation.replace('_', ' ')} '{result['reference']}':"]
        lines.append("")
        pos = result["suggested_position"]
        lines.append(f"📍 Suggested position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        
        if result["has_collisions"]:
            lines.append(f"⚠️  Warning: May overlap with: {', '.join(result['collisions'])}")
            lines.append("   Consider adjusting position or clearing space first.")
        else:
            lines.append("✅ Clear space - no collisions detected")
        
        return "\n".join(lines)

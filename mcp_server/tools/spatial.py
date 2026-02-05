"""MCP tools for spatial reasoning and scene understanding."""

from typing import Optional, List


def register_tools(mcp, client):
    """Register spatial reasoning tools."""

    # ========================================================================
    # SEMANTIC SCENE SUMMARY (from PR #4)
    # ========================================================================

    @mcp.tool()
    async def get_semantic_scene_summary(
        detail_level: str = "standard",
    ) -> str:
        """Get an enhanced scene summary with spatial semantics and object relationships.
        
        This provides a natural language understanding of the scene layout,
        including object positions described in human-readable terms.
        
        Args:
            detail_level: "minimal", "standard", or "detailed"
        
        Returns:
            Semantic description including summary, bounds, scale, objects, clusters
        """
        result = await client.execute(
            "get_semantic_scene_summary",
            {"detail_level": detail_level},
        )
        
        lines = ["=" * 50, "SCENE SUMMARY", "=" * 50, ""]
        lines.append(result["summary"])
        lines.append("")
        lines.append(f"Coordinate system: {result['coordinate_system']}")
        lines.append(f"Scene bounds: {result['bounds']['size'][0]:.1f}m × {result['bounds']['size'][1]:.1f}m × {result['bounds']['size'][2]:.1f}m")
        lines.append(f"Scale: {result['scale_description']}")
        lines.append("")
        
        if result.get("camera"):
            cam = result["camera"]
            lines.append(f"📷 Camera: {cam['name']} at ({cam['position'][0]:.1f}, {cam['position'][1]:.1f}, {cam['position'][2]:.1f})")
            lines.append(f"   Looking toward: {cam['looking_toward']}")
            lines.append("")
        
        if result.get("clusters"):
            lines.append("📦 Object Clusters:")
            for i, cluster in enumerate(result["clusters"], 1):
                lines.append(f"   Cluster {i}: {', '.join(cluster)}")
            lines.append("")
        
        if result.get("objects"):
            lines.append("📍 Objects:")
            for obj in result["objects"]:
                pos_desc = obj.get("position_description", "unknown")
                size = obj.get("size_category", "medium")
                lines.append(f"   • {obj['name']} ({size}, {pos_desc})")
                
                if detail_level == "detailed" and obj.get("nearby_objects"):
                    nearby_str = ", ".join(f"{n[0]} ({n[1]}m)" for n in obj["nearby_objects"])
                    lines.append(f"     └─ Nearby: {nearby_str}")
        
        return "\n".join(lines)

    @mcp.tool()
    async def get_spatial_relationships(
        name: str,
        max_distance: float = 5.0,
    ) -> str:
        """Get spatial relationships for a specific object.
        
        Returns what objects are near, on top of, behind, in front of, etc.
        
        Args:
            name: Name of the object to analyze
            max_distance: Maximum distance to search (meters)
        """
        result = await client.execute(
            "get_spatial_relationships",
            {"name": name, "max_distance": max_distance},
        )
        
        lines = [f"Spatial relationships for '{result['object']}':"]
        lines.append(f"  Position: ({result['position'][0]:.2f}, {result['position'][1]:.2f}, {result['position'][2]:.2f})")
        lines.append(f"  Size: {result['size_category']}")
        lines.append(f"  Facing: {result['facing_direction']}")
        lines.append("")
        
        if not result["relationships"]:
            lines.append("  No objects found within range.")
        else:
            lines.append(f"  Related objects ({result['relationship_count']}):")
            for rel in result["relationships"]:
                rel_types = ", ".join(rel["relationships"])
                lines.append(f"    • {rel['object']} ({rel['type']})")
                lines.append(f"      Distance: {rel['distance']}m ({rel['distance_category']})")
                lines.append(f"      Relations: {rel_types}")
        
        return "\n".join(lines)

    # ========================================================================
    # SPATIAL QUERIES (from PR #5)
    # ========================================================================

    @mcp.tool()
    async def query_spatial(question: str) -> str:
        """Answer natural language spatial queries about the scene.
        
        Supported queries:
        - "what is on the table?"
        - "what is to the left of the chair?"
        - "what is near the desk?"
        - "what is behind the sofa?"
        
        Args:
            question: Natural language question about spatial relationships
        """
        result = await client.execute("query_spatial", {"question": question})
        
        if not result.get("success"):
            lines = [f"❌ {result.get('error', 'Query failed')}"]
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
        """Find a valid position to place an object relative to another.
        
        Args:
            reference: Reference object name
            relation: "on", "next_to", "left_of", "right_of", "in_front_of", "behind"
            object_size: [width, depth, height] in meters
        """
        if object_size is None:
            object_size = [0.5, 0.5, 0.5]
        
        result = await client.execute(
            "find_placement_position",
            {"reference": reference, "relation": relation, "object_size": object_size},
        )
        
        lines = [f"Placement position {relation.replace('_', ' ')} '{result['reference']}':"]
        pos = result["suggested_position"]
        lines.append(f"📍 Suggested: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        
        if result["has_collisions"]:
            lines.append(f"⚠️  Warning: May overlap with: {', '.join(result['collisions'])}")
        else:
            lines.append("✅ Clear space")
        
        return "\n".join(lines)

    # ========================================================================
    # TRANSFORM VALIDATION (from PR #6)
    # ========================================================================

    @mcp.tool()
    async def validate_transform(
        name: str,
        action: str = "move",
        delta: Optional[List[float]] = None,
        absolute: Optional[List[float]] = None,
        factor: Optional[List[float]] = None,
    ) -> str:
        """Validate a transformation before applying it.
        
        Check for collisions, ground penetration, extreme scales, etc.
        
        Args:
            name: Object name
            action: "move", "rotate", or "scale"
            delta: Relative change [x, y, z]
            absolute: Absolute target [x, y, z]
            factor: Scale factor [x, y, z]
        """
        params = {"name": name, "action": action}
        
        if absolute is not None:
            params["absolute"] = absolute
        elif delta is not None:
            params["delta"] = delta
        elif factor is not None:
            params["factor"] = factor
        else:
            params["delta"] = [0, 0, 0]
        
        result = await client.execute("validate_transform", params)
        
        lines = [f"Transform validation for '{result['object']}' ({result['action']}):"]
        lines.append("")
        lines.append("Current state:")
        lines.append(f"  Position: ({result['current_position'][0]:.2f}, {result['current_position'][1]:.2f}, {result['current_position'][2]:.2f})")
        
        if "new_position" in result:
            pos = result["new_position"]
            lines.append(f"\nAfter transform:")
            lines.append(f"  Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        
        lines.append("")
        if result["valid"]:
            lines.append("✅ VALID - Transform can be applied")
        else:
            lines.append("❌ INVALID:")
            for issue in result["issues"]:
                lines.append(f"   • {issue}")
        
        if result["warnings"]:
            lines.append("\n⚠️  Warnings:")
            for w in result["warnings"]:
                lines.append(f"   • {w}")
        
        if result["suggestions"]:
            lines.append("\n💡 Suggestions:")
            for s in result["suggestions"]:
                lines.append(f"   • {s}")
        
        return "\n".join(lines)

    @mcp.tool()
    async def get_safe_movement_range(
        name: str,
        max_distance: float = 10.0,
    ) -> str:
        """Calculate how far an object can safely move in each direction.
        
        Args:
            name: Object name
            max_distance: Maximum distance to check (meters)
        """
        result = await client.execute(
            "get_safe_movement_range",
            {"name": name, "max_distance": max_distance},
        )
        
        lines = [f"Safe movement range for '{result['object']}':"]
        pos = result["position"]
        lines.append(f"Position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
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

    # ========================================================================
    # SEMANTIC MOVEMENT (from PR #7 - already merged)
    # ========================================================================

    @mcp.tool()
    async def move_object_semantic(
        name: str,
        instruction: str,
        dry_run: bool = False,
    ) -> str:
        """Move an object using natural language instructions.
        
        Examples:
        - "place on the desk"
        - "put on the left corner of the table"
        - "move next to the chair"
        - "move 2 meters left"
        
        Args:
            name: Object to move
            instruction: Natural language positioning instruction
            dry_run: Preview without applying
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
        
        if result["dry_run"]:
            lines.append("\n   ℹ️  Dry run - object not moved")
        else:
            lines.append("\n   ✅ Object moved successfully")
        
        return "\n".join(lines)

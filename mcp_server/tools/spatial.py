"""MCP tools for spatial reasoning and scene understanding."""

from typing import Optional


def register_tools(mcp, client):
    """Register spatial reasoning tools."""

    @mcp.tool()
    async def get_semantic_scene_summary(
        detail_level: str = "standard",
    ) -> str:
        """Get an enhanced scene summary with spatial semantics and object relationships.
        
        This provides a natural language understanding of the scene layout,
        including object positions described in human-readable terms,
        spatial clustering, and scene scale.
        
        Args:
            detail_level: Level of detail - "minimal", "standard", or "detailed".
                         "minimal" = summary only
                         "standard" = summary + object list with positions
                         "detailed" = all above + nearby objects for each
        
        Returns:
            Semantic description of the scene including:
            - Natural language summary
            - Scene bounds and scale (room-scale, building-scale, etc.)
            - Object list with position descriptions (left, right, front, back, etc.)
            - Spatial clusters (groups of nearby objects)
            - Camera information
        """
        result = await client.execute(
            "get_semantic_scene_summary",
            {"detail_level": detail_level},
        )
        
        lines = ["=" * 50]
        lines.append("SCENE SUMMARY")
        lines.append("=" * 50)
        lines.append("")
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
            lines.append("📦 Object Clusters (nearby objects):")
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
        relative to the specified object.
        
        Args:
            name: Name of the object to analyze
            max_distance: Maximum distance (meters) to search for related objects
        
        Returns:
            List of spatial relationships including:
            - Distance to nearby objects
            - Relationship types (on_top_of, behind, left_of, facing, etc.)
            - Direction descriptions
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
                dir_info = rel.get("direction", {})
                if dir_info:
                    lines.append(f"      Direction: x={dir_info.get('x', '?')}, y={dir_info.get('y', '?')}, z={dir_info.get('z', '?')}")
        
        return "\n".join(lines)

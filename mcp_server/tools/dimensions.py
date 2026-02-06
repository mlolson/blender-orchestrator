"""MCP tools for querying real-world object dimensions and placement rules."""

import json
import os
from typing import Optional


# Load the dimensions database once at module level
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "object_dimensions.json")

def _load_dimensions_db() -> dict:
    """Load the object dimensions database from JSON."""
    with open(_DATA_PATH, "r") as f:
        return json.load(f)


def register_tools(mcp, client):
    """Register object dimension tools."""

    @mcp.tool()
    async def get_object_dimensions(object_type: str) -> str:
        """Get real-world dimensions and placement rules for an object type.

        Returns dimension ranges (min/max in meters) and placement hints
        including wall proximity, clearances, and typical groupings.

        Args:
            object_type: Type of object (e.g. "dining_chair", "sofa_3seat", "bookshelf")
        """
        db = _load_dimensions_db()
        objects = db.get("objects", {})

        obj = objects.get(object_type)
        if not obj:
            # Try fuzzy match
            matches = [k for k in objects if object_type.lower() in k.lower()]
            if matches:
                return (
                    f"Object '{object_type}' not found. Did you mean one of: "
                    + ", ".join(matches)
                )
            return (
                f"Object '{object_type}' not found in database. "
                f"Use list_known_objects() to see available types."
            )

        dims = obj["dimensions"]
        placement = obj["placement"]

        lines = [
            f"=== {object_type} ===",
            f"Category: {obj['category']}",
            "",
            "Dimensions (meters):",
            f"  Width:  {dims['width'][0]:.2f} - {dims['width'][1]:.2f}",
            f"  Depth:  {dims['depth'][0]:.2f} - {dims['depth'][1]:.2f}",
            f"  Height: {dims['height'][0]:.2f} - {dims['height'][1]:.2f}",
            "",
            "Placement rules:",
            f"  Against wall: {'yes' if placement['against_wall'] else 'no'}",
            f"  Floor clearance: {placement['floor_clearance']:.2f}m",
            f"  Clearance front: {placement['clearance_front']:.2f}m",
            f"  Clearance back:  {placement['clearance_back']:.2f}m",
            f"  Clearance sides: {placement['clearance_sides']:.2f}m",
        ]

        if placement["typical_groupings"]:
            lines.append(f"  Typically grouped with: {', '.join(placement['typical_groupings'])}")

        return "\n".join(lines)

    @mcp.tool()
    async def list_known_objects(category: Optional[str] = None) -> str:
        """List all known object types in the dimensions database.

        Args:
            category: Optional filter by category (seating, tables, storage,
                      lighting, decor, appliances, outdoor, office)
        """
        db = _load_dimensions_db()
        objects = db.get("objects", {})

        if category:
            filtered = {k: v for k, v in objects.items() if v["category"] == category}
            if not filtered:
                categories = sorted(set(v["category"] for v in objects.values()))
                return (
                    f"No objects found in category '{category}'. "
                    f"Available categories: {', '.join(categories)}"
                )
            objects = filtered

        # Group by category
        by_category = {}
        for name, data in objects.items():
            cat = data["category"]
            by_category.setdefault(cat, []).append(name)

        lines = [f"Known objects ({len(objects)} total):", ""]
        for cat in sorted(by_category.keys()):
            items = sorted(by_category[cat])
            lines.append(f"  {cat.upper()}:")
            for item in items:
                dims = objects[item]["dimensions"]
                lines.append(
                    f"    • {item}  "
                    f"({dims['width'][0]:.2f}-{dims['width'][1]:.2f} × "
                    f"{dims['depth'][0]:.2f}-{dims['depth'][1]:.2f} × "
                    f"{dims['height'][0]:.2f}-{dims['height'][1]:.2f}m)"
                )
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    async def get_placement_rules(object_type: str) -> str:
        """Get placement hints and spatial rules for an object type.

        Returns wall affinity, required clearances, floor clearance,
        and objects it is typically grouped with.

        Args:
            object_type: Type of object (e.g. "dining_chair", "bookshelf")
        """
        db = _load_dimensions_db()
        objects = db.get("objects", {})

        obj = objects.get(object_type)
        if not obj:
            matches = [k for k in objects if object_type.lower() in k.lower()]
            if matches:
                return (
                    f"Object '{object_type}' not found. Did you mean one of: "
                    + ", ".join(matches)
                )
            return (
                f"Object '{object_type}' not found in database. "
                f"Use list_known_objects() to see available types."
            )

        placement = obj["placement"]
        dims = obj["dimensions"]

        lines = [
            f"=== Placement rules for {object_type} ===",
            "",
        ]

        # Wall placement
        if placement["against_wall"]:
            lines.append("📐 Wall placement: Should be placed against a wall")
        else:
            lines.append("📐 Wall placement: Can be placed freely (not wall-dependent)")

        # Floor clearance
        if placement["floor_clearance"] > 0:
            lines.append(
                f"📏 Floor clearance: {placement['floor_clearance']:.2f}m "
                f"(mount/hang at this height above floor)"
            )
        else:
            lines.append("📏 Floor clearance: Sits on floor")

        # Clearance zones
        lines.append("")
        lines.append("🔲 Required clearance zones:")
        lines.append(f"  Front: {placement['clearance_front']:.2f}m")
        lines.append(f"  Back:  {placement['clearance_back']:.2f}m")
        lines.append(f"  Sides: {placement['clearance_sides']:.2f}m")

        # Footprint
        lines.append("")
        avg_w = (dims["width"][0] + dims["width"][1]) / 2
        avg_d = (dims["depth"][0] + dims["depth"][1]) / 2
        total_w = avg_w + 2 * placement["clearance_sides"]
        total_d = avg_d + placement["clearance_front"] + placement["clearance_back"]
        lines.append(
            f"📦 Total footprint (avg dims + clearance): "
            f"{total_w:.2f}m × {total_d:.2f}m"
        )

        # Groupings
        if placement["typical_groupings"]:
            lines.append("")
            lines.append("🔗 Typically placed with:")
            for group in placement["typical_groupings"]:
                lines.append(f"  • {group}")

        return "\n".join(lines)

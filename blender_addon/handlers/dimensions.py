"""Handlers for object dimensions and placement rule queries."""

import json
import os
from typing import Any, Dict


# Load dimensions database
_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "mcp_server", "data", "object_dimensions.json"
)


def _load_db() -> dict:
    """Load the object dimensions database."""
    with open(_DATA_PATH, "r") as f:
        return json.load(f)


def get_object_dimensions(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return dimension ranges and placement rules for an object type."""
    object_type = params["object_type"]
    db = _load_db()
    objects = db.get("objects", {})

    obj = objects.get(object_type)
    if not obj:
        matches = [k for k in objects if object_type.lower() in k.lower()]
        raise ValueError(
            f"Object '{object_type}' not found. "
            + (f"Did you mean: {', '.join(matches)}" if matches else "Use list_known_objects to see available types.")
        )

    return {
        "object_type": object_type,
        "category": obj["category"],
        "dimensions": obj["dimensions"],
        "placement": obj["placement"],
    }


def list_known_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all known object types, optionally filtered by category."""
    category = params.get("category")
    db = _load_db()
    objects = db.get("objects", {})

    if category:
        filtered = {k: v for k, v in objects.items() if v["category"] == category}
        if not filtered:
            categories = sorted(set(v["category"] for v in objects.values()))
            raise ValueError(
                f"No objects in category '{category}'. Available: {', '.join(categories)}"
            )
        objects = filtered

    by_category = {}
    for name, data in objects.items():
        cat = data["category"]
        by_category.setdefault(cat, []).append({
            "name": name,
            "dimensions": data["dimensions"],
        })

    return {
        "total": sum(len(v) for v in by_category.values()),
        "categories": by_category,
    }


def get_placement_rules(params: Dict[str, Any]) -> Dict[str, Any]:
    """Return placement hints for an object type."""
    object_type = params["object_type"]
    db = _load_db()
    objects = db.get("objects", {})

    obj = objects.get(object_type)
    if not obj:
        matches = [k for k in objects if object_type.lower() in k.lower()]
        raise ValueError(
            f"Object '{object_type}' not found. "
            + (f"Did you mean: {', '.join(matches)}" if matches else "Use list_known_objects to see available types.")
        )

    return {
        "object_type": object_type,
        "category": obj["category"],
        "placement": obj["placement"],
        "dimensions": obj["dimensions"],
    }


DIMENSIONS_HANDLERS = {
    "get_object_dimensions": get_object_dimensions,
    "list_known_objects": list_known_objects,
    "get_placement_rules": get_placement_rules,
}

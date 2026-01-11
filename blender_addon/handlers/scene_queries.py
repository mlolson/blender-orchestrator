"""Handlers for scene query operations."""

import bpy
from typing import Any, Dict, List
from ..utils.serializers import serialize_object, serialize_scene_summary


def list_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all objects in the scene."""
    type_filter = params.get("type")
    name_filter = params.get("name_contains")

    objects = []
    for obj in bpy.data.objects:
        # Apply type filter
        if type_filter and obj.type != type_filter.upper():
            continue

        # Apply name filter
        if name_filter and name_filter.lower() not in obj.name.lower():
            continue

        objects.append({
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "visible": obj.visible_get(),
        })

    return {"objects": objects, "count": len(objects)}


def get_object_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information about a specific object."""
    name = params["name"]

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    return serialize_object(obj, detailed=True)


def get_scene_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get a summary of the current scene."""
    scene = bpy.context.scene
    return serialize_scene_summary(scene)


def get_selected_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get information about currently selected objects."""
    selected = []
    for obj in bpy.context.selected_objects:
        selected.append(serialize_object(obj))

    active = None
    if bpy.context.active_object:
        active = serialize_object(bpy.context.active_object)

    return {
        "selected": selected,
        "active": active,
        "count": len(selected),
    }


def select_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Select an object by name."""
    name = params["name"]
    add_to_selection = params.get("add", False)

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    if not add_to_selection:
        bpy.ops.object.select_all(action="DESELECT")

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return serialize_object(obj)


def deselect_all(params: Dict[str, Any]) -> Dict[str, Any]:
    """Deselect all objects."""
    bpy.ops.object.select_all(action="DESELECT")
    return {"success": True}


def set_object_visibility(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set object visibility."""
    name = params["name"]
    visible = params.get("visible", True)
    viewport = params.get("viewport", True)
    render = params.get("render", True)

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    if viewport:
        obj.hide_viewport = not visible
    if render:
        obj.hide_render = not visible

    return {
        "name": obj.name,
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
    }


def get_object_children(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get all children of an object."""
    name = params["name"]
    recursive = params.get("recursive", False)

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found")

    def get_children_recursive(parent):
        children = []
        for child in parent.children:
            children.append(serialize_object(child))
            if recursive:
                children.extend(get_children_recursive(child))
        return children

    children = get_children_recursive(obj)

    return {
        "parent": obj.name,
        "children": children,
        "count": len(children),
    }


def set_parent(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set the parent of an object."""
    child_name = params["child"]
    parent_name = params.get("parent")  # None to clear parent

    child = bpy.data.objects.get(child_name)
    if not child:
        raise ValueError(f"Child object '{child_name}' not found")

    if parent_name:
        parent = bpy.data.objects.get(parent_name)
        if not parent:
            raise ValueError(f"Parent object '{parent_name}' not found")
        child.parent = parent
    else:
        child.parent = None

    return serialize_object(child)


SCENE_QUERY_HANDLERS = {
    "list_objects": list_objects,
    "get_object_info": get_object_info,
    "get_scene_summary": get_scene_summary,
    "get_selected_objects": get_selected_objects,
    "select_object": select_object,
    "deselect_all": deselect_all,
    "set_object_visibility": set_object_visibility,
    "get_object_children": get_object_children,
    "set_parent": set_parent,
}

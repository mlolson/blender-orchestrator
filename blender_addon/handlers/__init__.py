from .primitives import PRIMITIVE_HANDLERS
from .transforms import TRANSFORM_HANDLERS
from .mesh_editing import MESH_EDITING_HANDLERS
from .materials import MATERIAL_HANDLERS
from .rendering import RENDERING_HANDLERS
from .scene_queries import SCENE_QUERY_HANDLERS


def get_handler_registry():
    """Combine all handlers into a single registry."""
    registry = {}
    registry.update(PRIMITIVE_HANDLERS)
    registry.update(TRANSFORM_HANDLERS)
    registry.update(MESH_EDITING_HANDLERS)
    registry.update(MATERIAL_HANDLERS)
    registry.update(RENDERING_HANDLERS)
    registry.update(SCENE_QUERY_HANDLERS)
    return registry

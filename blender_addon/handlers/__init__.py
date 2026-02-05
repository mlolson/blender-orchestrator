from .primitives import PRIMITIVE_HANDLERS
from .transforms import TRANSFORM_HANDLERS
from .mesh_editing import MESH_EDITING_HANDLERS
from .materials import MATERIAL_HANDLERS
from .rendering import RENDERING_HANDLERS
from .scene_queries import SCENE_QUERY_HANDLERS
from .metaballs import METABALL_HANDLERS
from .curves import CURVE_HANDLERS
from .skinning import SKINNING_HANDLERS
from .mesh_import import MESH_IMPORT_HANDLERS
from .texture_application import TEXTURE_APPLICATION_HANDLERS
from .spatial import SPATIAL_HANDLERS
from .lighting import LIGHTING_HANDLERS
from ..templates import TEMPLATE_HANDLERS


def get_handler_registry():
    """Combine all handlers into a single registry."""
    registry = {}
    registry.update(PRIMITIVE_HANDLERS)
    registry.update(TRANSFORM_HANDLERS)
    registry.update(MESH_EDITING_HANDLERS)
    registry.update(MATERIAL_HANDLERS)
    registry.update(RENDERING_HANDLERS)
    registry.update(SCENE_QUERY_HANDLERS)
    # New handlers for improved character creation
    registry.update(METABALL_HANDLERS)
    registry.update(CURVE_HANDLERS)
    registry.update(SKINNING_HANDLERS)
    # AI generation support handlers
    registry.update(MESH_IMPORT_HANDLERS)
    registry.update(TEXTURE_APPLICATION_HANDLERS)
    registry.update(TEMPLATE_HANDLERS)
    # Spatial reasoning handlers
    registry.update(SPATIAL_HANDLERS)
    # Lighting handlers
    registry.update(LIGHTING_HANDLERS)
    return registry

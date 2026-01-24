"""AI generation clients for mesh and texture generation."""

from .base import (
    GenerationStatus,
    MeshGenerationResult,
    TextureGenerationResult,
    MeshGenerationProvider,
    TextureGenerationProvider,
)
from .config import get_ai_config, AIConfig
from .registry import (
    get_registry,
    reset_registry,
    ProviderRegistry,
    ProviderInfo,
    MeshCapability,
    TextureCapability,
)

# Auto-register available providers
def _register_providers():
    """Register all available providers with the registry."""
    registry = get_registry()

    # Register Meshy for mesh generation
    from .meshy_client import MeshyClient

    registry.register_mesh_provider(
        name="meshy",
        provider_class=MeshyClient,
        capabilities=[
            MeshCapability.TEXT_TO_3D,
            MeshCapability.IMAGE_TO_3D,
            MeshCapability.MESH_REFINEMENT,
        ],
        description="Meshy AI - High quality text and image to 3D generation",
    )

    # Future providers will be registered here:
    # registry.register_texture_provider(
    #     name="stability",
    #     provider_class=StabilityClient,
    #     capabilities=[...],
    #     description="Stability AI - Texture generation",
    # )


# Register providers on module import
_register_providers()

__all__ = [
    # Base types
    "GenerationStatus",
    "MeshGenerationResult",
    "TextureGenerationResult",
    "MeshGenerationProvider",
    "TextureGenerationProvider",
    # Config
    "get_ai_config",
    "AIConfig",
    # Registry
    "get_registry",
    "reset_registry",
    "ProviderRegistry",
    "ProviderInfo",
    "MeshCapability",
    "TextureCapability",
]

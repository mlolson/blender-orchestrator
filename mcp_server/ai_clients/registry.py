"""Provider registry for AI generation services.

The registry is the central hub for discovering and instantiating
AI generation providers. It enables an extensible architecture where
new providers can be added with minimal code changes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Type, Any

from .base import MeshGenerationProvider, TextureGenerationProvider
from .config import get_ai_config


class MeshCapability(Enum):
    """Capabilities that mesh generation providers can support."""

    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    MESH_TEXTURING = "mesh_texturing"  # Apply textures to existing mesh
    MESH_REFINEMENT = "mesh_refinement"


class TextureCapability(Enum):
    """Capabilities that texture generation providers can support."""

    TEXT_TO_TEXTURE = "text_to_texture"
    SEAMLESS_GENERATION = "seamless_generation"
    PBR_MAPS = "pbr_maps"  # Can generate normal, roughness, etc.
    MESH_UV_TEXTURING = "mesh_uv_texturing"  # Texture based on UV layout


@dataclass
class ProviderInfo:
    """Metadata about a registered provider."""

    name: str
    provider_type: str  # "mesh", "texture", or "both"
    description: str
    capabilities: List[str]
    is_configured: bool  # True if API key is available

    def has_capability(self, capability: MeshCapability | TextureCapability) -> bool:
        """Check if provider has a specific capability."""
        return capability.value in self.capabilities


@dataclass
class _ProviderRegistration:
    """Internal registration data for a provider."""

    provider_class: Type
    capabilities: List[str]
    description: str


class ProviderRegistry:
    """Central registry for AI generation providers.

    Usage:
        registry = get_registry()

        # Get a provider instance
        mesh_provider = registry.get_mesh_provider("meshy")
        result = await mesh_provider.generate_from_text("a chair")

        # List available providers
        providers = registry.list_mesh_providers()
        for p in providers:
            print(f"{p.name}: {p.description} (configured: {p.is_configured})")
    """

    def __init__(self):
        self._mesh_providers: Dict[str, _ProviderRegistration] = {}
        self._texture_providers: Dict[str, _ProviderRegistration] = {}
        self._instances: Dict[str, Any] = {}

    def register_mesh_provider(
        self,
        name: str,
        provider_class: Type[MeshGenerationProvider],
        capabilities: List[MeshCapability],
        description: str = "",
    ) -> None:
        """Register a mesh generation provider.

        Args:
            name: Unique identifier for the provider (e.g., "meshy", "tripo")
            provider_class: Class implementing MeshGenerationProvider
            capabilities: List of MeshCapability enums this provider supports
            description: Human-readable description
        """
        self._mesh_providers[name] = _ProviderRegistration(
            provider_class=provider_class,
            capabilities=[c.value for c in capabilities],
            description=description,
        )

    def register_texture_provider(
        self,
        name: str,
        provider_class: Type[TextureGenerationProvider],
        capabilities: List[TextureCapability],
        description: str = "",
    ) -> None:
        """Register a texture generation provider.

        Args:
            name: Unique identifier for the provider (e.g., "stability")
            provider_class: Class implementing TextureGenerationProvider
            capabilities: List of TextureCapability enums this provider supports
            description: Human-readable description
        """
        self._texture_providers[name] = _ProviderRegistration(
            provider_class=provider_class,
            capabilities=[c.value for c in capabilities],
            description=description,
        )

    def get_mesh_provider(self, name: str) -> MeshGenerationProvider:
        """Get or create a mesh provider instance.

        Args:
            name: Provider name (e.g., "meshy")

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider is not registered or not configured
        """
        if name not in self._mesh_providers:
            available = list(self._mesh_providers.keys())
            raise ValueError(
                f"Unknown mesh provider '{name}'. Available: {available}"
            )

        # Check if configured
        config = get_ai_config()
        if not config.has_provider(name):
            raise ValueError(
                f"Provider '{name}' is not configured. "
                f"Set {name.upper()}_API_KEY environment variable or add to config."
            )

        # Return cached instance or create new one
        cache_key = f"mesh:{name}"
        if cache_key not in self._instances:
            registration = self._mesh_providers[name]
            self._instances[cache_key] = registration.provider_class()

        return self._instances[cache_key]

    def get_texture_provider(self, name: str) -> TextureGenerationProvider:
        """Get or create a texture provider instance.

        Args:
            name: Provider name (e.g., "stability")

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider is not registered or not configured
        """
        if name not in self._texture_providers:
            available = list(self._texture_providers.keys())
            raise ValueError(
                f"Unknown texture provider '{name}'. Available: {available}"
            )

        # Check if configured
        config = get_ai_config()
        if not config.has_provider(name):
            raise ValueError(
                f"Provider '{name}' is not configured. "
                f"Set {name.upper()}_API_KEY environment variable or add to config."
            )

        # Return cached instance or create new one
        cache_key = f"texture:{name}"
        if cache_key not in self._instances:
            registration = self._texture_providers[name]
            self._instances[cache_key] = registration.provider_class()

        return self._instances[cache_key]

    def list_mesh_providers(self) -> List[ProviderInfo]:
        """List all registered mesh providers with their status.

        Returns:
            List of ProviderInfo with configuration status
        """
        config = get_ai_config()
        providers = []

        for name, reg in self._mesh_providers.items():
            providers.append(
                ProviderInfo(
                    name=name,
                    provider_type="mesh",
                    description=reg.description,
                    capabilities=reg.capabilities,
                    is_configured=config.has_provider(name),
                )
            )

        return providers

    def list_texture_providers(self) -> List[ProviderInfo]:
        """List all registered texture providers with their status.

        Returns:
            List of ProviderInfo with configuration status
        """
        config = get_ai_config()
        providers = []

        for name, reg in self._texture_providers.items():
            providers.append(
                ProviderInfo(
                    name=name,
                    provider_type="texture",
                    description=reg.description,
                    capabilities=reg.capabilities,
                    is_configured=config.has_provider(name),
                )
            )

        return providers

    def get_default_mesh_provider(self) -> Optional[str]:
        """Get the first configured mesh provider.

        Returns:
            Provider name or None if no providers are configured
        """
        config = get_ai_config()
        for name in self._mesh_providers:
            if config.has_provider(name):
                return name
        return None

    def get_default_texture_provider(self) -> Optional[str]:
        """Get the first configured texture provider.

        Returns:
            Provider name or None if no providers are configured
        """
        config = get_ai_config()
        for name in self._texture_providers:
            if config.has_provider(name):
                return name
        return None

    def clear_cache(self) -> None:
        """Clear cached provider instances.

        Useful for testing or when configuration changes.
        """
        self._instances.clear()


# Global singleton instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry.

    Returns:
        ProviderRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry.

    Useful for testing.
    """
    global _registry
    _registry = None

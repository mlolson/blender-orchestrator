"""Abstract base classes for AI generation providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class GenerationStatus(Enum):
    """Status of an AI generation request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MeshGenerationResult:
    """Result from a mesh generation API call."""
    status: GenerationStatus
    mesh_url: Optional[str] = None
    mesh_format: str = "glb"
    local_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None
    provider: str = ""
    model_id: str = ""
    generation_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TextureGenerationResult:
    """Result from a texture generation API call."""
    status: GenerationStatus
    texture_url: Optional[str] = None
    texture_type: str = "diffuse"
    local_path: Optional[str] = None
    resolution: tuple = (1024, 1024)
    error: Optional[str] = None
    provider: str = ""
    model_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MeshGenerationProvider(ABC):
    """Abstract base class for mesh generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    async def generate_from_text(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        output_format: str = "glb",
        **kwargs
    ) -> MeshGenerationResult:
        """Generate a 3D mesh from a text description.

        Args:
            prompt: Text description of the 3D object to generate
            negative_prompt: Things to avoid in generation
            output_format: Desired mesh format (glb, obj, ply)
            **kwargs: Provider-specific parameters

        Returns:
            MeshGenerationResult with status and file path/URL
        """
        pass

    @abstractmethod
    async def generate_from_image(
        self,
        image_path: str,
        output_format: str = "glb",
        **kwargs
    ) -> MeshGenerationResult:
        """Generate a 3D mesh from a reference image.

        Args:
            image_path: Path to the input image
            output_format: Desired mesh format
            **kwargs: Provider-specific parameters

        Returns:
            MeshGenerationResult with status and file path/URL
        """
        pass

    @abstractmethod
    async def check_status(self, prediction_id: str) -> MeshGenerationResult:
        """Check the status of an ongoing generation.

        Args:
            prediction_id: ID of the generation request

        Returns:
            MeshGenerationResult with current status
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported output mesh formats."""
        pass

    @abstractmethod
    def get_available_models(self) -> Dict[str, str]:
        """Return dict of available models {name: description}."""
        pass


class TextureGenerationProvider(ABC):
    """Abstract base class for texture generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    async def generate_texture(
        self,
        prompt: str,
        texture_type: str = "diffuse",
        resolution: tuple = (1024, 1024),
        seamless: bool = True,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate a texture from a text description.

        Args:
            prompt: Description of the desired texture
            texture_type: Type of map (diffuse, normal, roughness, metallic)
            resolution: Output resolution as (width, height)
            seamless: Whether to generate a tileable texture
            **kwargs: Provider-specific parameters

        Returns:
            TextureGenerationResult with status and file path/URL
        """
        pass

    @abstractmethod
    async def generate_from_mesh(
        self,
        mesh_path: str,
        prompt: str,
        **kwargs
    ) -> TextureGenerationResult:
        """Generate a texture specifically for a mesh.

        Args:
            mesh_path: Path to the mesh file
            prompt: Description of the desired texture style
            **kwargs: Provider-specific parameters

        Returns:
            TextureGenerationResult with status and file path/URL
        """
        pass

    @abstractmethod
    def get_supported_texture_types(self) -> List[str]:
        """Return list of supported texture map types."""
        pass

    @abstractmethod
    def get_supported_resolutions(self) -> List[tuple]:
        """Return list of supported output resolutions."""
        pass

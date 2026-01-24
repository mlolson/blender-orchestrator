# Implementation Plan: AI Mesh and Texture Generation Services

## Overview

This plan outlines the work needed to complete AI-powered mesh and texture generation for the Blender MCP tools. The architecture is designed to be **extensible**, allowing new AI providers to be added with minimal code changes.

## Current State

### What's Already Built
- **Meshy mesh generation (text-to-3D)**: Fully working via `generate_mesh_from_text` MCP tool
- **Abstract base classes**: `MeshGenerationProvider` and `TextureGenerationProvider` in `base.py`
- **Result dataclasses**: `MeshGenerationResult` and `TextureGenerationResult`
- **Mesh import pipeline**: Handlers for importing GLB, OBJ, FBX, PLY, STL files
- **Texture application handlers**: Blender-side code to apply textures to materials
- **Configuration system**: Supports environment variables and JSON config files

### What's Missing
1. **Provider Registry** - No central way to discover/instantiate providers
2. **Image-to-3D MCP tool** - API client exists but not exposed as MCP tool
3. **Texture generation providers** - No implementations of `TextureGenerationProvider`
4. **Texture generation MCP tools** - No `generate_texture`, `generate_pbr_material_textures`, etc.

---

## Extensible Architecture Design

The goal is to make adding a new provider (e.g., Tripo AI, OpenArt, Replicate) as simple as:
1. Create a new client class implementing the abstract interface
2. Register it with the provider registry
3. Add configuration for API keys

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Tools                                │
│  (generate_mesh_from_text, generate_texture, etc.)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Provider Registry                            │
│  - get_mesh_provider(name) -> MeshGenerationProvider            │
│  - get_texture_provider(name) -> TextureGenerationProvider      │
│  - list_mesh_providers() -> [ProviderInfo]                      │
│  - list_texture_providers() -> [ProviderInfo]                   │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   MeshyClient    │ │ StabilityClient  │ │  Future Provider │
│ (implements both)│ │ (textures only)  │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### Abstract Interfaces (Already Exist)

**File:** `mcp_server/ai_clients/base.py`

```python
class MeshGenerationProvider(ABC):
    @property
    def provider_name(self) -> str: ...
    async def generate_from_text(...) -> MeshGenerationResult: ...
    async def generate_from_image(...) -> MeshGenerationResult: ...
    def get_supported_formats(self) -> List[str]: ...
    def get_available_models(self) -> Dict[str, str]: ...

class TextureGenerationProvider(ABC):
    @property
    def provider_name(self) -> str: ...
    async def generate_texture(...) -> TextureGenerationResult: ...
    async def generate_from_mesh(...) -> TextureGenerationResult: ...
    def get_supported_texture_types(self) -> List[str]: ...
    def get_supported_resolutions(self) -> List[tuple]: ...
```

### New: Provider Registry

**File:** `mcp_server/ai_clients/registry.py` (new)

The registry is the central hub for provider discovery and instantiation.

```python
@dataclass
class ProviderInfo:
    """Metadata about a registered provider."""
    name: str
    provider_type: str  # "mesh", "texture", or "both"
    description: str
    capabilities: List[str]  # e.g., ["text_to_3d", "image_to_3d"]
    is_configured: bool  # True if API key is available

class ProviderRegistry:
    """Central registry for AI generation providers."""

    _mesh_providers: Dict[str, Type[MeshGenerationProvider]]
    _texture_providers: Dict[str, Type[TextureGenerationProvider]]
    _instances: Dict[str, Any]  # Cached provider instances

    def register_mesh_provider(
        self,
        name: str,
        provider_class: Type[MeshGenerationProvider],
        capabilities: List[str],
        description: str = ""
    ) -> None:
        """Register a mesh generation provider."""
        ...

    def register_texture_provider(
        self,
        name: str,
        provider_class: Type[TextureGenerationProvider],
        capabilities: List[str],
        description: str = ""
    ) -> None:
        """Register a texture generation provider."""
        ...

    def get_mesh_provider(self, name: str) -> MeshGenerationProvider:
        """Get or create a mesh provider instance."""
        ...

    def get_texture_provider(self, name: str) -> TextureGenerationProvider:
        """Get or create a texture provider instance."""
        ...

    def list_mesh_providers(self) -> List[ProviderInfo]:
        """List all registered mesh providers with status."""
        ...

    def list_texture_providers(self) -> List[ProviderInfo]:
        """List all registered texture providers with status."""
        ...

    def get_default_mesh_provider(self) -> Optional[str]:
        """Get the first configured mesh provider."""
        ...

    def get_default_texture_provider(self) -> Optional[str]:
        """Get the first configured texture provider."""
        ...

# Global singleton
_registry: Optional[ProviderRegistry] = None

def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    ...
```

### New: Provider Capabilities

Providers declare their capabilities so tools can query what's possible:

```python
class MeshCapability(Enum):
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    MESH_TEXTURING = "mesh_texturing"  # Apply textures to existing mesh
    MESH_REFINEMENT = "mesh_refinement"

class TextureCapability(Enum):
    TEXT_TO_TEXTURE = "text_to_texture"
    SEAMLESS_GENERATION = "seamless_generation"
    PBR_MAPS = "pbr_maps"  # Can generate normal, roughness, etc.
    MESH_UV_TEXTURING = "mesh_uv_texturing"  # Texture based on UV layout
```

---

## Phase 1: Provider Registry Infrastructure

### 1.1 Create Provider Registry

**File:** `mcp_server/ai_clients/registry.py` (new)

**Work:**
- Implement `ProviderInfo` dataclass
- Implement `ProviderRegistry` class with registration and retrieval methods
- Add capability enums
- Create global singleton with `get_registry()`

### 1.2 Register Existing Meshy Provider

**File:** `mcp_server/ai_clients/__init__.py`

**Work:**
- Import registry
- Auto-register `MeshyClient` on module load:
```python
from .registry import get_registry, MeshCapability

registry = get_registry()
registry.register_mesh_provider(
    name="meshy",
    provider_class=MeshyClient,
    capabilities=[
        MeshCapability.TEXT_TO_3D,
        MeshCapability.IMAGE_TO_3D,
        MeshCapability.MESH_REFINEMENT
    ],
    description="Meshy AI - High quality text and image to 3D"
)
```

### 1.3 Update MCP Tools to Use Registry

**File:** `mcp_server/tools/ai_mesh_generation.py`

**Work:**
- Replace direct `MeshyClient` instantiation with registry lookup
- Use `get_registry().get_mesh_provider(provider_name)`
- This allows the `provider` parameter to work with any registered provider

---

## Phase 2: Complete Meshy Integration

### 2.1 Add `generate_mesh_from_image` MCP Tool

**File:** `mcp_server/tools/ai_mesh_generation.py`

**Work:**
- Add new MCP tool that uses registry to get provider
- Parameters: `image_path`, `provider`, `import_to_scene`, `location`, `name`

```python
@mcp.tool()
async def generate_mesh_from_image(
    image_path: str,
    provider: str = "meshy",
    import_to_scene: bool = True,
    location: Optional[List[float]] = None,
    name: Optional[str] = None
) -> dict:
    registry = get_registry()
    mesh_provider = registry.get_mesh_provider(provider)
    result = await mesh_provider.generate_from_image(image_path)
    ...
```

---

## Phase 3: Texture Generation Provider

### Recommended First Provider: Stability AI

**Rationale:**
- Well-documented REST API
- High-quality image generation suitable for textures
- Already referenced in project README
- Good starting point; others can be added later

**Alternative providers to support later:**
- **Meshy Texturing**: Texture existing 3D models (different use case)
- **Tripo AI**: Strong for 3D, could add texture support
- **Replicate**: Run various open-source models

### 3.1 Create Stability AI Client

**File:** `mcp_server/ai_clients/stability_client.py` (new)

**Work:**
- Implement `StabilityClient` class extending `TextureGenerationProvider`
- Key methods from the abstract interface:
  - `generate_texture()` - Generate single texture
  - `generate_from_mesh()` - Generate texture for specific mesh (may return not supported)
  - `get_supported_texture_types()` - Return ["diffuse", "normal", "roughness", ...]
  - `get_supported_resolutions()` - Return [(512, 512), (1024, 1024), ...]

**Implementation notes:**
- Use Stability's image generation with texture-specific prompts
- For seamless textures, append "seamless, tileable" to prompts
- For normal maps, either use specialized model or post-process

```python
class StabilityClient(TextureGenerationProvider):

    @property
    def provider_name(self) -> str:
        return "stability"

    async def generate_texture(
        self,
        prompt: str,
        texture_type: str = "diffuse",
        resolution: tuple = (1024, 1024),
        seamless: bool = True,
        **kwargs
    ) -> TextureGenerationResult:
        # Build prompt with texture-specific modifiers
        full_prompt = self._build_texture_prompt(prompt, texture_type, seamless)
        # Call Stability API
        # Download and return result
        ...

    async def generate_from_mesh(
        self,
        mesh_path: str,
        prompt: str,
        **kwargs
    ) -> TextureGenerationResult:
        # Stability doesn't support this directly
        # Could potentially render mesh views and use img2img
        raise NotImplementedError("Use generate_texture for standalone textures")

    def get_supported_texture_types(self) -> List[str]:
        return ["diffuse", "normal", "roughness", "metallic", "ambient_occlusion"]

    def get_supported_resolutions(self) -> List[tuple]:
        return [(512, 512), (1024, 1024), (2048, 2048)]
```

### 3.2 Register Stability Provider

**File:** `mcp_server/ai_clients/__init__.py`

**Work:**
```python
registry.register_texture_provider(
    name="stability",
    provider_class=StabilityClient,
    capabilities=[
        TextureCapability.TEXT_TO_TEXTURE,
        TextureCapability.SEAMLESS_GENERATION,
        TextureCapability.PBR_MAPS
    ],
    description="Stability AI - High quality texture generation"
)
```

### 3.3 Update Configuration

**File:** `mcp_server/ai_clients/config.py`

**Work:**
- Add `STABILITY_API_KEY` environment variable handling
- Add Stability AI base URL and defaults

```python
# In _load_from_env():
stability_key = os.getenv("STABILITY_API_KEY")
if stability_key:
    self._configs["stability"] = ProviderConfig(
        api_key=stability_key,
        base_url="https://api.stability.ai/v2beta",
        timeout=300,
    )
```

---

## Phase 4: Texture Generation MCP Tools

### 4.1 Create Texture Generation Tools

**File:** `mcp_server/tools/ai_texture_generation.py` (new)

**Tools to implement:**

#### `generate_texture`
```python
@mcp.tool()
async def generate_texture(
    prompt: str,
    texture_type: str = "diffuse",
    resolution: int = 1024,
    seamless: bool = True,
    provider: Optional[str] = None,  # None = use default
    apply_to_object: Optional[str] = None,
    material_name: Optional[str] = None
) -> dict:
    registry = get_registry()
    provider_name = provider or registry.get_default_texture_provider()
    texture_provider = registry.get_texture_provider(provider_name)
    result = await texture_provider.generate_texture(...)
    ...
```

#### `generate_pbr_material_textures`
```python
@mcp.tool()
async def generate_pbr_material_textures(
    prompt: str,
    include_normal: bool = True,
    include_roughness: bool = True,
    include_metallic: bool = False,
    include_ao: bool = False,
    resolution: int = 1024,
    provider: Optional[str] = None,
    apply_to_object: Optional[str] = None,
    material_name: Optional[str] = None
) -> dict:
    # Generate multiple textures and combine into PBR material
    ...
```

#### `apply_texture_to_object`
```python
@mcp.tool()
async def apply_texture_to_object(
    texture_path: str,
    object_name: str,
    texture_type: str = "diffuse",
    create_material: bool = True,
    material_name: Optional[str] = None
) -> dict:
    # Call existing Blender handler
    ...
```

#### `list_texture_generation_providers`
```python
@mcp.tool()
async def list_texture_generation_providers() -> dict:
    registry = get_registry()
    providers = registry.list_texture_providers()
    return {
        "providers": [
            {
                "name": p.name,
                "description": p.description,
                "capabilities": p.capabilities,
                "configured": p.is_configured
            }
            for p in providers
        ]
    }
```

### 4.2 Register Tools

**File:** `mcp_server/tools/__init__.py`

**Work:**
- Import and register `ai_texture_generation` module

---

## Phase 5: Blender Handler Verification

### 5.1 Verify Texture Handler Registration

**File:** `blender_addon/handlers/__init__.py`

**Work:**
- Ensure these handlers are registered in action map:
  - `apply_texture_to_material`
  - `create_pbr_material_from_textures`
  - `apply_texture_from_url`
  - `create_material_with_texture`

---

## Adding a New Provider (Future)

To add a new provider (e.g., Tripo AI), developers would:

### 1. Create the client

**File:** `mcp_server/ai_clients/tripo_client.py`

```python
from .base import MeshGenerationProvider, MeshGenerationResult

class TripoClient(MeshGenerationProvider):
    @property
    def provider_name(self) -> str:
        return "tripo"

    async def generate_from_text(self, prompt, **kwargs) -> MeshGenerationResult:
        # Implementation
        ...

    # ... implement other abstract methods
```

### 2. Register it

**File:** `mcp_server/ai_clients/__init__.py`

```python
from .tripo_client import TripoClient

registry.register_mesh_provider(
    name="tripo",
    provider_class=TripoClient,
    capabilities=[MeshCapability.TEXT_TO_3D, MeshCapability.IMAGE_TO_3D],
    description="Tripo AI - Fast 3D generation"
)
```

### 3. Add configuration

**File:** `mcp_server/ai_clients/config.py`

```python
tripo_key = os.getenv("TRIPO_API_KEY")
if tripo_key:
    self._configs["tripo"] = ProviderConfig(...)
```

That's it. The MCP tools automatically work with the new provider via the `provider` parameter.

---

## Configuration

Users configure API keys in priority order:

### 1. Environment Variables (Highest Priority)
```bash
export MESHY_API_KEY="msy_..."
export STABILITY_API_KEY="sk-..."
export TRIPO_API_KEY="..."  # Future
```

### 2. Project Root Config
**File:** `config.json`
```json
{
  "meshy_api_key": "msy_...",
  "stability_api_key": "sk-..."
}
```

### 3. User Config File
**File:** `~/.config/blender-mcp/ai_providers.json`
```json
{
  "meshy": {
    "api_key": "msy_...",
    "timeout": 600
  },
  "stability": {
    "api_key": "sk-...",
    "timeout": 300
  }
}
```

---

## Implementation Order

| Phase | Description | Dependency |
|-------|-------------|------------|
| 1 | Provider Registry infrastructure | None |
| 2 | Complete Meshy (add image-to-3D tool) | Phase 1 |
| 3 | Stability AI texture client | Phase 1 |
| 4 | Texture generation MCP tools | Phase 1, 3 |
| 5 | Blender handler verification | None |

Phases 2, 3, and 5 can be done in parallel after Phase 1 is complete.

---

## File Summary

| File | Action | Description |
|------|--------|-------------|
| `mcp_server/ai_clients/registry.py` | **Create** | Provider registry with discovery |
| `mcp_server/ai_clients/base.py` | Modify | Add capability enums |
| `mcp_server/ai_clients/__init__.py` | Modify | Auto-register providers, export registry |
| `mcp_server/ai_clients/config.py` | Modify | Add Stability AI configuration |
| `mcp_server/ai_clients/stability_client.py` | **Create** | Stability AI texture client |
| `mcp_server/tools/ai_mesh_generation.py` | Modify | Use registry, add image-to-3D tool |
| `mcp_server/tools/ai_texture_generation.py` | **Create** | Texture generation MCP tools |
| `mcp_server/tools/__init__.py` | Modify | Register texture tools |
| `blender_addon/handlers/__init__.py` | Verify | Ensure handler registration |

---

## Testing Plan

### Unit Tests
- Test registry registration and retrieval
- Test provider capability queries
- Test configuration loading from all sources
- Mock API responses for client tests

### Integration Tests
- Generate texture with Stability and verify file created
- Generate PBR set and verify all maps created
- Switch providers via parameter and verify correct client used

### End-to-End Tests
- Full workflow: generate mesh -> generate textures -> apply to mesh
- Verify provider listing shows correct configured status

---

## Sources

- [Stability AI API Documentation](https://platform.stability.ai/docs/api-reference)
- [Meshy AI](https://www.meshy.ai/)
- [Tripo AI](https://www.tripo3d.ai/)
- [3D AI Studio](https://www.3daistudio.com/TextureGeneration)

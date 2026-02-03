# Competitive Analysis: blender-orchestrator vs blender-mcp

## Overview

**Our repo:** `mlolson/blender-orchestrator`  
**Competition:** `ahujasid/blender-mcp` (14K+ stars, very popular)

## Feature Comparison

| Feature | Ours | Theirs | Winner |
|---------|------|--------|--------|
| **Core MCP Integration** | ✅ HTTP-based | ✅ Socket-based | Tie |
| **Object manipulation** | ✅ | ✅ | Tie |
| **Material control** | ✅ | ✅ | Tie |
| **Scene inspection** | ✅ | ✅ | Tie |
| **Arbitrary code execution** | ❌ | ✅ | Them |
| **Viewport screenshots** | ❌ | ✅ | Them |
| **AI mesh generation** | ✅ Meshy | ✅ Hyper3D, Hunyuan3D | Tie |
| **AI texture generation** | ✅ Stability AI | ❌ | **Us** |
| **Poly Haven integration** | ❌ | ✅ | Them |
| **Sketchfab integration** | ❌ | ✅ | Them |
| **VR optimization tools** | ✅ | ❌ | **Us** |
| **Mesh decimation/LOD** | ✅ | ❌ | **Us** |
| **Sculpting tools** | ✅ | ❌ | **Us** |
| **Skinning/rigging** | ✅ | ❌ | **Us** |
| **Metaballs/curves** | ✅ | ❌ | **Us** |
| **Template system** | ✅ | ❌ | **Us** |
| **Installation simplicity** | ❌ Complex | ✅ `uvx blender-mcp` | Them |

## Our Competitive Advantages

### 1. VR/Horizon Worlds Focus
- Mesh validation against platform limits
- Automatic decimation to target poly counts
- LOD generation
- GLB export optimization
- **This is a unique differentiator**

### 2. AI Texture Generation
- Stability AI integration for texture maps
- Full PBR material generation (diffuse, normal, roughness, metallic, AO)
- **They don't have this**

### 3. Advanced Mesh Editing
- Sculpting tools (grab, inflate, smooth, etc.)
- Proportional editing
- Native Blender sculpt mode access
- Remeshing
- **More comprehensive than their basic operations**

### 4. Character Creation
- Skinning/rigging tools
- Humanoid templates
- Eye/face integration tools

## Their Advantages (Gaps We Need to Fill)

### 1. Poly Haven Integration (HIGH PRIORITY)
- Free, CC0 licensed assets
- HDRIs (lighting), textures, 3D models
- Huge library, very popular
- **Should be our top priority to add**

### 2. Viewport Screenshots (HIGH PRIORITY)
- Let AI "see" what it's building
- Critical for iterative design
- Already have `capture_viewport` but may need MCP exposure

### 3. Sketchfab Integration (MEDIUM)
- Massive library of 3D models
- Many free, some premium
- Good for finding reference models

### 4. Arbitrary Code Execution (LOW)
- Escape hatch for edge cases
- Security risk, but useful
- Could add with warnings

### 5. Installation Simplicity (MEDIUM)
- They publish to PyPI
- `uvx blender-mcp` just works
- We require more manual setup

### 6. More AI Providers (MEDIUM)
- Hunyuan3D (free/open source)
- Tripo AI
- More options = more flexibility

## Recommended Roadmap

### Phase 1: Close the Gaps (Immediate)
1. **Poly Haven integration** - HDRIs, textures, models
2. **Viewport screenshots MCP tool** - Critical for AI understanding
3. **Simplify installation** - Publish to PyPI

### Phase 2: Extend Our Lead (Next)
4. **More AI mesh providers** - Hunyuan3D, Tripo
5. **Sketchfab integration**
6. **Arbitrary code execution** (with safety warnings)

### Phase 3: Differentiation (Ongoing)
7. **VR-specific templates** - Horizon Worlds common objects
8. **End-to-end workflows** - Scene building guides
9. **Animation support** - For VR experiences
10. **Performance profiling** - Real-time poly count displays

## Positioning Strategy

**Their positioning:** General-purpose Blender AI assistant  
**Our positioning:** **VR/Horizon Worlds focused** professional tool

Key messages:
- "Built for VR creators"
- "From AI generation to Quest-ready in minutes"
- "The only Blender MCP with VR optimization"
- "AI textures + AI meshes + VR export"

## Technical Notes

### Poly Haven API
- Endpoint: `https://api.polyhaven.com`
- Types: `hdris`, `textures`, `models`
- Free, no API key required
- CC0 licensed (free for any use)

Key endpoints:
- `GET /assets?type=<type>&categories=<cats>` - List assets
- `GET /files/{id}` - Get download URLs
- `GET /categories/{type}` - List categories

### Viewport Screenshots
We have `capture_viewport` handler but need to:
1. Ensure it returns base64 for MCP
2. Add as proper MCP tool
3. Consider auto-capture after operations

---

*Analysis by Kit, 2026-02-02*

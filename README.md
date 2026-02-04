# Agentic Blender Orchestrator 

MCP tooling suite for creation of 3D scenes, with plug-innable mesh and image generation service integration. 

**Create 3D models in Blender using natural language.** MCP server lets agent directly control Blender, enabling you to build complex 3D scenes through conversation. 

**Seamless integration with mesh and image generation services** 
Plug in the API keys to mesh generation services like meshy, or image generation service like stability, Replicate, or Leonardo.ai. The agent can make use of them via standardized MCP APIs.

## Why Use This?

- **AI-powered generation**: Generate 3D meshes from text descriptions or reference images using Meshy and Stability AI.
- **Rapid prototyping**: Iterate on designs through conversation, getting immediate visual feedback.
- **Automation**: Script complex modeling workflows without writing Blender Python code.
- **VR-ready exports**: Optimize and export models for Meta Quest and Horizon Worlds.
- **Free assets**: Access thousands of CC0 HDRIs, textures, and models from Poly Haven.


## Quick Start

### Requirements

- Blender 4.0+
- Python 3.10+
- uv (recommended) or pip

### Installation

**1. Install Python dependencies**

```bash
cd /path/to/blender-orchestrator
uv venv && source .venv/bin/activate
uv pip install -e .
```

**2. Install the Blender add-on**

```bash
python scripts/install_addon.py
```

Or manually: Blender → Edit → Preferences → Add-ons → Install → select `blender_addon` folder → enable "Blender MCP Bridge"

**3. Configure Agent**

Add to your Agent Desktop config (`~/Library/Application Support/Agent/Agent_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["--directory", "/path/to/blender-orchestrator", "run", "blender-mcp"]
    }
  }
}
```

For Claude Code CLI, add the same to `.claude/settings.json`.

### Usage

1. Open Blender
2. Press `N` in the 3D Viewport → MCP tab → Click "Start Server"
3. Start talking to Claude about your 3D scene

---

## Features

### Primitives & Transforms

Create and manipulate basic shapes with full control over position, rotation, and scale.

| Tool | Description |
|------|-------------|
| `create_cube`, `create_sphere`, `create_cylinder`, `create_cone`, `create_torus`, `create_plane` | Create primitive shapes |
| `move_object`, `rotate_object`, `scale_object` | Transform objects (absolute or relative) |
| `duplicate_object`, `delete_object` | Copy or remove objects |
| `set_origin`, `set_parent` | Control object origin and hierarchy |

### Mesh Editing

Modify geometry with professional modeling operations.

| Tool | Description |
|------|-------------|
| `extrude_faces` | Extrude faces along normals |
| `bevel_edges` | Add bevels with configurable segments |
| `boolean_operation` | Union, difference, or intersect meshes |
| `subdivide_mesh`, `add_subdivision_surface` | Increase mesh resolution |
| `inset_faces`, `smooth_mesh` | Topology and smoothing operations |

### Procedural Generation

Create complex organic and geometric forms.

| Tool | Description |
|------|-------------|
| `create_metaball`, `add_metaball_element` | Organic blob-like shapes that blend together |
| `create_bezier_curve`, `curve_to_mesh` | Spline-based modeling |
| `create_skin_mesh` | Generate smooth surfaces from edge skeletons |
| `create_character_from_template` | Pre-built character rigs (realistic, cartoon, chibi) |

### Materials & Textures

Full PBR material support with AI-powered texture generation.

| Tool | Description |
|------|-------------|
| `create_material`, `assign_material`, `modify_material` | PBR material workflow |
| `generate_texture` | AI-generated textures from text |
| `generate_pbr_material_textures` | Complete material sets (diffuse, normal, roughness, metallic) |

### Rendering & Visualization

| Tool | Description |
|------|-------------|
| `render_image` | Full render to file (EEVEE, Cycles, Workbench) |
| `capture_viewport` | Quick viewport screenshot |
| `set_render_settings`, `get_render_settings` | Configure resolution, samples, format |
| `set_world_hdri` | Apply HDRI environment lighting |

### Scene Management

| Tool | Description |
|------|-------------|
| `list_objects`, `get_object_info`, `get_scene_summary` | Query scene state |
| `select_object`, `deselect_all`, `set_object_visibility` | Selection and visibility |
| `check_blender_connection` | Verify server status |

### AI-Powered 3D Generation

Generate complete 3D models from text or images using cloud AI APIs.

| Tool | Description |
|------|-------------|
| `generate_mesh_from_text` | Text-to-3D model generation |
| `generate_mesh_from_image` | Image-to-3D model generation |
| `import_mesh_file` | Import GLB, OBJ, FBX, PLY, STL |

### VR Optimization

Tools for optimizing 3D assets for VR platforms.

| Tool | Description |
|------|-------------|
| `validate_for_vr` | Check if model meets VR platform limits |
| `optimize_for_vr` | Decimate and optimize for VR platforms |
| `generate_lod_chain` | Create LOD variants for performance |
| `export_vr_scene` | Export optimized GLB for VR |

### Poly Haven (Free Assets)

Access thousands of free CC0 assets from [Poly Haven](https://polyhaven.com).

| Tool | Description |
|------|-------------|
| `search_polyhaven` | Search free CC0 assets |
| `list_polyhaven_categories` | Browse available categories |
| `download_polyhaven_hdri` | Download and apply HDRI lighting |
| `download_polyhaven_texture` | Download PBR texture sets |
| `download_polyhaven_model` | Download and import 3D models |

---

## AI Generation Setup

Generate 3D meshes using Meshy and textures using Replicate.

### Configuration

Set API keys via environment variables:

```bash
export MESHY_API_KEY="msy_your_key_here"
export REPLICATE_API_TOKEN="r8_your_token_here"
```

Or create `~/.config/blender-mcp/ai_providers.json`:

```json
{
  "meshy": { "api_key": "msy_your_key_here", "timeout": 600 },
  "replicate": { "api_key": "r8_your_token_here", "timeout": 300 }
}
```

### Available Providers

| Provider | Capability | Notes |
|----------|------------|-------|
| Meshy | Text-to-3D, Image-to-3D | Best quality, multiple art styles |
| Replicate | Texture generation | Pay-per-use (~$0.002/image), SDXL and specialized models |

### Text-to-3D Examples

```
"Generate a wooden treasure chest"
"Create a cartoon dog in the scene"
"Make a realistic medieval castle tower"
```

Art styles: `realistic`, `cartoon`, `sculpture`, `pbr`

### Image-to-3D Tips

- Use images with a single object on a clean background
- Ensure good lighting and centered composition
- Avoid cluttered scenes

### API Costs

- **Meshy**: Credit-based, ~20 credits per generation. See [meshy.ai/pricing](https://www.meshy.ai/pricing)
- **Replicate**: Pay-per-use, ~$0.002 per texture. See [replicate.com/pricing](https://replicate.com/pricing)

---

## VR Optimization

Built-in tools for optimizing 3D assets for VR platforms, with presets for Meta Horizon Worlds.

### Platform Presets

| Preset | Max Tris/Object | Max Tris/Scene | Max Texture |
|--------|-----------------|----------------|-------------|
| `horizon_worlds` | 10,000 | 100,000 | 2048px |
| `quest` | 50,000 | 200,000 | 4096px |
| `mobile_vr` | 20,000 | 150,000 | 2048px |

### Validation

Check if your model is VR-ready:

```
validate_for_vr(
    object_name="Chair",
    platform="horizon_worlds"
)
```

Returns warnings for poly count, texture size, and material issues.

### Optimization

Automatically optimize models:

```
optimize_for_vr(
    object_name="Chair",
    platform="horizon_worlds",
    target_triangles=10000,
    merge_by_distance=True
)
```

### LOD Generation

Create level-of-detail variants:

```
generate_lod_chain(
    object_name="Chair",
    lod_levels=[1.0, 0.5, 0.25, 0.1]
)
```

### GLB Export

Export optimized scenes:

```
export_vr_scene(
    output_path="/path/to/scene.glb",
    platform="horizon_worlds",
    include_all_objects=True
)
```

---

## Poly Haven Integration

Access thousands of free CC0 assets from [Poly Haven](https://polyhaven.com) — no API key required.

### Search Assets

```
search_polyhaven(
    query="brick",
    asset_type="texture",
    limit=10
)
```

Asset types: `hdri`, `texture`, `model`

### Download HDRI Lighting

Apply realistic environment lighting:

```
download_polyhaven_hdri(
    asset_id="industrial_sunset_02",
    resolution="4k",
    apply_to_scene=True
)
```

### Download Textures

Get complete PBR texture sets:

```
download_polyhaven_texture(
    asset_id="brick_wall_02",
    resolution="2k",
    apply_to_object="Cube"
)
```

### Download Models

Import ready-to-use 3D models:

```
download_polyhaven_model(
    asset_id="wooden_chair",
    import_to_scene=True,
    location=[0, 0, 0]
)
```

### Browse Categories

```
list_polyhaven_categories(asset_type="textures")
```

All Poly Haven assets are **CC0 licensed** — free for any use, no attribution required.

---

## Troubleshooting

**"Cannot connect to Blender server"**
- Ensure Blender is running with the MCP Bridge add-on enabled
- Click "Start Server" in the MCP panel (press `N` → MCP tab)
- Check that port 8765 is available

**"Object not found"**
- Object names are case-sensitive
- Use `list_objects` to see exact names

**Test the connection manually:**

```bash
curl http://localhost:8765/health
```

---

## Architecture

```
blender-orchestrator/
├── blender_addon/          # Blender add-on (HTTP server + handlers)
│   ├── server/             # Non-blocking HTTP server
│   ├── handlers/           # Operation implementations
│   └── templates/          # Character templates
│
├── mcp_server/             # MCP server
│   ├── server.py           # FastMCP entry point
│   ├── blender_client.py   # HTTP client for Blender communication
│   ├── tools/              # Tool definitions (one module per category)
│   └── ai_clients/         # AI provider implementations
│
└── scripts/                # Installation helpers
```

### Adding New Tools

1. Create handler in `blender_addon/handlers/`
2. Register in `blender_addon/handlers/__init__.py`
3. Create MCP tool in `mcp_server/tools/`
4. Register in `mcp_server/tools/__init__.py`

---

## License

MIT

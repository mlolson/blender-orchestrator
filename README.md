# Agentic Blender Orchestrator

Create 3D models in Blender using natural language. MCP server lets agent directly control Blender, enabling you to build complex 3D scenes through conversation. Scene comprehension tooling and skills gives LLM improved spatial awareness for better results.

---

## Samples created solely with prompts to Claude Opus 4.6

![Prompt generated loft scene](https://github.com/mlolson/blender-orchestrator/blob/main/examples/room.png "Loft with furniture")
![Prompt generated forest scene](https://github.com/mlolson/blender-orchestrator/blob/main/examples/forest.png "Forest scene")
![Prompt generated bug character](https://github.com/mlolson/blender-orchestrator/blob/main/examples/bug.png "Bug character")
![Prompt generated rocket](https://github.com/mlolson/blender-orchestrator/blob/main/examples/rocket.png "Saturn V rocket")

## Features

### 🧠 Spatial Intelligence Suite
Spatial intelligence suite helps AI understand space.

- **Natural language positioning** — Say "place the lamp on the nightstand" and it figures out the coordinates, checks for collisions, and handles stacking.
- **Real-world dimensions database** — 55+ common objects (furniture, appliances, decor) with accurate real-world measurements. The AI knows a kitchen counter is 0.9m tall and a doorway is 2.1m × 0.9m.
- **Collision detection & safe movement** — Validate transforms before applying them. Query how far an object can move in each direction without hitting anything.
- **Spatial queries** — Ask "what's on the table?" or "what's near the door?" and get answers.
- **Scene Building Guide** — A comprehensive [reference doc](docs/SCENE_BUILDING_GUIDE.md) that AI agents can read before building a scene, covering room dimensions, placement rules, common mistakes, and worked examples.

### 🗺️ Multi-View ASCII Floor Plans
ASCII visualizer tool gives the LLM a way to understand spatial relationships between objects. Renders the scene from any angle — top, bottom, front, back, left, right, or all six at once. Configurable resolution up to 120×120 cells.

```
--- Top (looking down, +Z) ---
Axes: horizontal=X, vertical=Y | 5.3m x 4.3m (cell: 0.25m, grid: 21x17)

WWWWWWWWWWWWWWWWWWWWW
W...................W
W...................W
W..TTTTTT..........W
W..TTTTTT..........W
W..TTTTTT....SS....W
W............SS....W
W...................W
W.......CCCC.......W
W.......CCCC.......W
W...................W
WWWWWWWWWWWWWWWWWWWWW

Legend: C=Couch, S=Shelf, T=Table, W=Wall_Back
```

### 💡 Complete Lighting System
Full control over all four Blender light types — point, sun, spot, and area lights. Set color, intensity, shadow properties, cone angles, and more. Previously only HDRI environment lighting was available; now you can build precise studio setups, dramatic spotlights, or warm interior scenes.

### 📷 Camera Tools
Create perspective, orthographic, and panoramic cameras. Auto-frame objects for product shots. Set depth of field, adjust lens focal length, and control clipping planes. Essential for rendering composed shots of your scenes.

### 🏠 Room Creation
One command creates a properly dimensioned room with floor and four walls. Specify width, depth, height, and wall thickness — then start furnishing. Combined with the dimensions database and spatial tools, the AI can furnish a realistic room from a single prompt.

### 🌍 Plugin Model and Texture generation services
Extensible architecture allows you to plug in texture and model gen services of your choice, including Replicate, Meshy, Stability.ai, and more.

Built in access to thousands of free CC0 assets from [Poly Haven](https://polyhaven.com) — no API key needed. Download HDRIs for environment lighting, PBR texture sets for realistic materials, and ready-to-use 3D models. All assets are CC0 licensed (free for any use, no attribution required).

---

## Why Use This?

- **Spatial intelligence**: AI understands real-world dimensions, detects collisions, and reasons about object relationships — not just coordinates.
- **AI-powered generation**: Generate 3D meshes from text descriptions or reference images using Meshy and Stability AI.
- **Complete scene control**: Lighting, cameras, materials, rendering — everything you need to go from empty scene to finished render.
- **Rapid prototyping**: Iterate on designs through conversation, getting immediate visual feedback.
- **VR-ready exports**: Optimize and export models for Meta Quest and Horizon Worlds with built-in platform presets.
- **Free assets**: Thousands of CC0 HDRIs, textures, and models from Poly Haven — no API key required.


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

### Lighting

Create and control lights for realistic or stylized scene illumination.

| Tool | Description |
|------|-------------|
| `create_point_light` | Omnidirectional light (light bulbs, lanterns) |
| `create_sun_light` | Directional light for outdoor scenes |
| `create_spot_light` | Cone-shaped focused light (flashlight, stage light) |
| `create_area_light` | Soft rectangular/disk light (softboxes, panels) |
| `set_light_properties` | Modify existing light settings |
| `get_light_info`, `list_lights` | Query light information |

### Cameras

Create and position cameras for rendering and visualization.

| Tool | Description |
|------|-------------|
| `create_camera` | Create perspective, orthographic, or panoramic camera |
| `set_active_camera` | Set which camera is used for rendering |
| `look_at` | Point camera at a target object or location |
| `frame_objects` | Auto-position camera to frame objects nicely |
| `set_camera_properties` | Adjust lens, DOF, clipping, etc. |
| `get_camera_info`, `list_cameras` | Query camera information |

### Spatial Reasoning & Scene Intelligence

Tools for understanding and manipulating scene layout with real-world spatial awareness.

| Tool | Description |
|------|-------------|
| `get_semantic_scene_summary` | Enhanced scene summary with spatial semantics, clusters, and object relationships |
| `get_spatial_relationships` | Get what's near, on top of, behind, or in front of an object |
| `query_spatial` | Answer natural language questions ("what is on the table?") |
| `find_placement_position` | Find collision-free position relative to another object |
| `validate_transform` | Check a move/rotate/scale for collisions before applying |
| `get_safe_movement_range` | Calculate how far an object can move in each direction |
| `move_object_semantic` | Move objects with natural language ("place on the desk") |
| `get_object_dimensions` | Look up real-world dimensions for 55+ common objects |
| `list_known_objects` | Browse the dimensions database by category |
| `get_placement_rules` | Get placement guidelines (clearances, heights, spacing) |
| `show_floor_plan` | ASCII visualization from any angle (top/bottom/front/back/left/right/all) |
| `create_room_bounds` | Create a properly dimensioned room (floor + 4 walls) |

See the **[Scene Building Guide](docs/SCENE_BUILDING_GUIDE.md)** for detailed usage patterns and examples.

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

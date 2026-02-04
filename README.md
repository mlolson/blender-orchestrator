# Agentic Blender Orchestrator 

MCP tooling suite for creation of 3D scenes, with plug-innable mesh and image generation service integration. 

**Create 3D models in Blender using natural language.** MCP server lets agent directly control Blender, enabling you to build complex 3D scenes through conversation. 

**Seamless integration with mesh and image generation services** 
Plug in the API keys to mesh generation services like meshy, or image generation service like stability, Replicate, or Leonardo.ai. The agent can make use of them via standardized MCP APIs.

## Why Use This?

- **AI-powered generation**: Generate 3D meshes from text descriptions or reference images using Meshy and Stability AI.
- **Rapid prototyping**: Iterate on designs through conversation, getting immediate visual feedback.
- **Automation**: Script complex modeling workflows without writing Blender Python code.


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

For Calide Code CLI, add the same to `.claude/settings.json`.

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

---

## AI Generation Setup

Generate 3D meshes and textures using Meshy and Stability AI.

### Configuration

Set API keys via environment variables:

```bash
export MESHY_API_KEY="msy_your_key_here"
export STABILITY_API_KEY="sk-your_key_here"
```

Or create `~/.config/blender-mcp/ai_providers.json`:

```json
{
  "meshy": { "api_key": "msy_your_key_here", "timeout": 600 },
  "stability": { "api_key": "sk-your_key_here", "timeout": 300 }
}
```

### Available Models

| Provider | Capability | Notes |
|----------|------------|-------|
| Meshy | Text-to-3D, Image-to-3D | Best quality, multiple art styles |
| Stability | Image-to-3D, Textures | Fast generation |

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

Both providers use credit-based pricing. See [meshy.ai/pricing](https://www.meshy.ai/pricing) and Stability AI documentation.

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

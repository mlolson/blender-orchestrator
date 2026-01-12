# Blender MCP Tools

MCP (Model Context Protocol) server that allows Claude to create and edit 3D models in Blender.

## Architecture

```
Claude Code  <-->  MCP Server (Python)  <-->  Blender Add-on (HTTP Server)
```

- **Blender Add-on**: Runs an HTTP server inside Blender that exposes the Blender Python API
- **MCP Server**: Connects to the Blender add-on and exposes tools to Claude

## Requirements

- Blender 4.0+
- Python 3.10+
- uv (recommended) or pip

## Installation

### 1. Install Python Dependencies

```bash
cd /path/to/blender_tools
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 2. Install Blender Add-on

Option A - Using the install script (recommended):

```bash
python scripts/install_addon.py
```

Option B - Manual installation:

1. Open Blender
2. Go to Edit > Preferences > Add-ons
3. Click "Install..."
4. Navigate to the `blender_addon` folder and select it
5. Enable "Blender MCP Bridge" in the add-ons list

### 3. Configure Claude Code

Add the MCP server to your Claude configuration.

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
    "mcpServers": {
        "blender": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/blender_tools",
                "run",
                "blender-mcp"
            ]
        }
    }
}
```

**For Claude Code CLI** (`.claude/settings.json`):

```json
{
    "mcpServers": {
        "blender": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/blender_tools",
                "run",
                "blender-mcp"
            ]
        }
    }
}
```

## Usage

1. **Start Blender** and open/create a scene

2. **Start the MCP server in Blender**:
   - Press `N` in the 3D Viewport to open the sidebar
   - Find the "MCP" tab
   - Click "Start Server"
   - You should see "Server running on port 8765"

3. **Use Claude** to interact with Blender:
   ```
   "Create a red cube at position (2, 0, 0)"
   "List all objects in the scene"
   "Take a viewport screenshot"
   "Create a metallic gold sphere and place it next to the cube"
   ```

## Available Tools

### Primitives
- `create_cube` - Create a cube
- `create_sphere` - Create a UV sphere
- `create_cylinder` - Create a cylinder
- `create_cone` - Create a cone
- `create_torus` - Create a torus (donut)
- `create_plane` - Create a plane

### Transforms
- `move_object` - Move an object
- `rotate_object` - Rotate an object
- `scale_object` - Scale an object
- `duplicate_object` - Duplicate an object
- `delete_object` - Delete an object
- `set_origin` - Set object origin point

### Mesh Editing
- `extrude_faces` - Extrude faces along normals
- `bevel_edges` - Bevel edges
- `boolean_operation` - Boolean operations (union, difference, intersect)
- `subdivide_mesh` - Subdivide mesh
- `add_subdivision_surface` - Add subdivision surface modifier
- `inset_faces` - Inset faces
- `smooth_mesh` - Smooth mesh vertices

### Materials
- `create_material` - Create a PBR material
- `assign_material` - Assign material to object
- `modify_material` - Modify material properties
- `list_materials` - List all materials
- `create_and_assign_material` - Create and assign in one step
- `delete_material` - Delete a material

### Rendering
- `render_image` - Render scene to file
- `capture_viewport` - Capture viewport screenshot (fast)
- `set_render_settings` - Configure render settings
- `get_render_settings` - Get current render settings

### Scene Management
- `list_objects` - List all objects
- `get_object_info` - Get detailed object info
- `get_scene_summary` - Get scene summary
- `get_selected_objects` - Get selected objects
- `select_object` - Select an object
- `deselect_all` - Deselect all objects
- `set_object_visibility` - Show/hide objects
- `set_parent` - Set object parent
- `check_blender_connection` - Check if Blender is connected

### AI Mesh Generation
- `generate_mesh_from_text` - Generate 3D mesh from text description
- `generate_mesh_from_image` - Generate 3D mesh from reference image
- `import_mesh_file` - Import mesh file (GLB, OBJ, FBX, PLY, STL)
- `list_mesh_generation_providers` - Show available AI providers

### AI Texture Generation
- `generate_texture` - Generate texture from text description
- `generate_pbr_material_textures` - Generate complete PBR material
- `apply_texture_to_object` - Apply texture file to object
- `list_texture_generation_providers` - Show available AI providers

---

## AI-Powered Generation

Generate 3D meshes and textures using cloud AI APIs from Meshy and Stability AI.

### Configuration

Set environment variables for the AI providers you want to use:

```bash
# For Meshy (text-to-3D and image-to-3D)
export MESHY_API_KEY="msy_your_key_here"

# For Stability AI (image-to-3D and textures)
export STABILITY_API_KEY="sk-your_key_here"
```

Or create a config file at `~/.config/blender-mcp/ai_providers.json`:

```json
{
  "meshy": {
    "api_key": "msy_your_key_here",
    "timeout": 600
  },
  "stability": {
    "api_key": "sk-your_key_here",
    "timeout": 300
  }
}
```

### Mesh Generation

#### Available Models

| Provider | Model | Input Type | Description |
|----------|-------|------------|-------------|
| Meshy | `latest` (Meshy-6) | Text or Image | Best quality, recommended |
| Meshy | `meshy-5` | Text or Image | Previous generation |
| Stability | `stable-fast-3d` | Image only | Stability's image-to-3D |

#### Text-to-3D

Generate a 3D mesh from a text description:

```
generate_mesh_from_text(
    prompt="a wooden chair",
    provider="meshy",
    art_style="realistic",
    refine=True,
    import_to_scene=True,
    location=[0, 0, 0],
    name="Chair"
)
```

Art styles: `realistic`, `cartoon`, `sculpture`, `pbr`

Example prompts:
- "a medieval castle tower"
- "a red sports car"
- "a cartoon dog"
- "a wooden treasure chest"

#### Image-to-3D

Generate a 3D mesh from a reference image:

```
generate_mesh_from_image(
    image_path="/path/to/photo.png",
    provider="meshy",
    import_to_scene=True,
    location=[0, 0, 0],
    name="MyModel"
)
```

Tips for best results:
- Use images with a single object on a clean/white background
- Ensure the object is well-lit and centered
- Avoid cluttered backgrounds

### Texture Generation

#### Single Texture

Generate a texture map:

```
generate_texture(
    prompt="weathered wood planks",
    texture_type="diffuse",
    resolution=1024,
    seamless=True,
    provider="stability",
    apply_to_object="Cube"
)
```

Texture types: `diffuse`, `normal`, `roughness`, `metallic`, `ambient_occlusion`

#### Complete PBR Material

Generate multiple texture maps for a full PBR material:

```
generate_pbr_material_textures(
    prompt="rusty corroded metal",
    apply_to_object="Cube",
    include_normal=True,
    include_roughness=True,
    include_metallic=True,
    resolution=1024,
    provider="stability"
)
```

Example prompts:
- "cobblestone path"
- "brushed aluminum"
- "mossy stone wall"
- "worn leather"
- "sci-fi metal panels"

### API Costs

AI generation uses paid APIs:
- **Meshy**: Credit-based, ~20 credits per generation. See [meshy.ai/pricing](https://www.meshy.ai/pricing)
- **Stability AI**: Credit-based, varies by model

Check provider websites for current pricing.

---

## Testing the Connection

You can test if the Blender server is running:

```bash
# Health check
curl http://localhost:8765/health

# Test an action
curl -X POST http://localhost:8765 \
  -H "Content-Type: application/json" \
  -d '{"action": "list_objects", "params": {}}'
```

## Troubleshooting

### "Cannot connect to Blender server"
- Make sure Blender is running
- Make sure the MCP Bridge add-on is enabled
- Make sure you clicked "Start Server" in the MCP panel
- Check that port 8765 is not in use by another application

### "Object not found"
- Object names in Blender are case-sensitive
- Use `list_objects` to see exact object names

### Server not starting
- Check Blender's console for error messages
- Try a different port if 8765 is in use

## Development

### Project Structure

```
blender_tools/
├── blender_addon/          # Blender add-on
│   ├── __init__.py         # Add-on registration
│   ├── server/             # HTTP server
│   ├── handlers/           # Blender operation handlers
│   │   ├── mesh_import.py      # AI mesh import handlers
│   │   └── texture_application.py  # Texture application handlers
│   ├── operators/          # Blender operators
│   └── utils/              # Utilities
│
├── mcp_server/             # MCP server
│   ├── server.py           # FastMCP server
│   ├── blender_client.py   # HTTP client
│   ├── tools/              # MCP tool definitions
│   │   ├── ai_mesh_generation.py    # AI mesh generation tools
│   │   └── ai_texture_generation.py # AI texture generation tools
│   └── ai_clients/         # AI provider clients
│       ├── base.py             # Abstract base classes
│       ├── config.py           # API key management
│       ├── meshy_client.py     # Meshy API client
│       └── stability_client.py # Stability AI client
│
└── scripts/                # Helper scripts
```

### Adding New Tools

1. Add handler in `blender_addon/handlers/`
2. Register handler in `blender_addon/handlers/__init__.py`
3. Add MCP tool in `mcp_server/tools/`
4. Register tool module in `mcp_server/tools/__init__.py`

## License

MIT

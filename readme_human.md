# Blender MCP Tools - Setup Guide

A step-by-step guide to setting up Blender MCP Tools with AI-powered mesh and texture generation.

## Quick Start

1. Install dependencies
2. Install the Blender addon
3. Configure Claude Desktop
4. (Optional) Set up AI API keys
5. Start using it!

---

## Step 1: Install Python Dependencies

Open a terminal and navigate to the project folder:

```bash
cd /path/to/blender_tools

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

Or if you use `uv`:

```bash
cd /path/to/blender_tools
uv venv
source .venv/bin/activate
uv pip install -e .
```

---

## Step 2: Install the Blender Addon

### Option A: Automatic Installation

```bash
python scripts/install_addon.py
```

### Option B: Manual Installation

1. Open Blender
2. Go to **Edit → Preferences → Add-ons**
3. Click **Install...**
4. Navigate to `blender_tools/blender_addon` and select the folder
5. Check the box next to **"Blender MCP Bridge"** to enable it

### Verify Installation

- Press `N` in the 3D Viewport to open the sidebar
- Look for the **"MCP"** tab
- Click **"Start Server"**
- You should see "Server running on port 8765"

---

## Step 3: Configure Claude Desktop

Find your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this configuration (create the file if it doesn't exist):

```json
{
    "mcpServers": {
        "blender": {
            "command": "uv",
            "args": [
                "--directory",
                "/full/path/to/blender_tools",
                "run",
                "blender-mcp"
            ]
        }
    }
}
```

**Important:** Replace `/full/path/to/blender_tools` with the actual path to your installation.

### Alternative: Using pip instead of uv

If you installed with pip instead of uv:

```json
{
    "mcpServers": {
        "blender": {
            "command": "/full/path/to/blender_tools/.venv/bin/blender-mcp"
        }
    }
}
```

---

## Step 4: Set Up AI API Keys (Optional)

To use AI-powered mesh and texture generation, you need API keys from one or both providers.

### Getting a Meshy API Key

Meshy is recommended for text-to-3D and image-to-3D generation.

1. Go to [meshy.ai](https://www.meshy.ai)
2. Click **Sign Up** and create an account
3. Go to **Settings → API** or visit [meshy.ai/api](https://www.meshy.ai/api)
4. Click **Create API Key**
5. Copy the key (starts with `msy_`)

**Cost:** Credit-based system, ~20 credits per generation. New accounts get free credits to start. See [meshy.ai/pricing](https://www.meshy.ai/pricing) for details.

**Test Mode:** During development, you can use the test key `msy_dummy_api_key_for_test_mode_12345678` to explore the API without using credits.

### Getting a Stability AI API Key

Stability AI is good for texture generation and image-to-3D.

1. Go to [platform.stability.ai](https://platform.stability.ai)
2. Click **Sign Up** and create an account
3. Go to [platform.stability.ai/account/keys](https://platform.stability.ai/account/keys)
4. Click **Create API Key**
5. Copy the key (starts with `sk-`)

**Cost:** Credit-based system. Check their pricing page for current rates.

### Configuring API Keys

#### Option A: Environment Variables (Recommended)

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`):

```bash
# Meshy API (for mesh generation)
export MESHY_API_KEY="msy_your_key_here"

# Stability AI (for textures and mesh generation)
export STABILITY_API_KEY="sk-your_key_here"
```

Then reload your shell:

```bash
source ~/.zshrc  # or ~/.bashrc
```

#### Option B: Configuration File

Create the config directory and file:

```bash
mkdir -p ~/.config/blender-mcp
```

Create `~/.config/blender-mcp/ai_providers.json`:

```json
{
  "meshy": {
    "api_key": "msy_your_key_here",
    "timeout": 600
  },
  "stability": {
    "api_key": "sk_your_key_here",
    "timeout": 300
  }
}
```

**Security Note:** Keep your API keys private. Don't commit them to version control.

---

## Step 5: Test the Setup

### Test Blender Connection

1. Start Blender
2. Enable the MCP addon and click "Start Server"
3. In a terminal, run:

```bash
curl http://localhost:8765/health
```

You should see: `{"status": "ok"}`

### Test with Claude

1. Restart Claude Desktop (to pick up the new config)
2. Start a new conversation
3. Ask Claude: "List all objects in the Blender scene"

If connected, Claude will show the objects in your scene.

### Test AI Generation (if configured)

Ask Claude:
- "What AI mesh generation providers are available?"
- "Generate a 3D model of a wooden chair"
- "Create a rusty metal texture and apply it to the default cube"

---

## Usage Examples

### Basic 3D Modeling

```
"Create a red cube at position 2, 0, 0"
"Add a blue metallic sphere next to it"
"Create a simple house with walls and a roof"
```

### AI Mesh Generation

```
"Generate a 3D mesh of a medieval sword"
"Create a 3D model from this image: /path/to/reference.png"
```

### AI Texture Generation

```
"Generate a wood texture and apply it to the floor"
"Create a full PBR material for weathered stone and apply it to the walls"
```

---

## Troubleshooting

### "Cannot connect to Blender"

1. Make sure Blender is running
2. Check the MCP addon is enabled (Edit → Preferences → Add-ons)
3. Click "Start Server" in the MCP panel (press N to see sidebar)
4. Check port 8765 isn't used by another app

### "API key not configured"

1. Verify your API key is correct
2. Check environment variable is set: `echo $MESHY_API_KEY`
3. Restart Claude Desktop after setting environment variables
4. Try the config file method if env vars aren't working

### AI generation fails

1. Check you have credits/balance with the provider
2. Verify your API key hasn't expired
3. Check your internet connection
4. Try a simpler prompt

### Claude doesn't see the Blender server

1. Check the path in `claude_desktop_config.json` is correct
2. Restart Claude Desktop completely
3. Check Claude's MCP logs for errors

---

## Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Open an issue on GitHub for bugs or feature requests

---

## Summary Checklist

- [ ] Python dependencies installed
- [ ] Blender addon installed and enabled
- [ ] Claude Desktop configured with correct path
- [ ] Blender server running (port 8765)
- [ ] (Optional) Meshy API key configured
- [ ] (Optional) Stability AI API key configured
- [ ] Claude Desktop restarted after config changes

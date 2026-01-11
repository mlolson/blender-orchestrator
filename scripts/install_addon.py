#!/usr/bin/env python3
"""Script to install the Blender addon by creating a symlink."""

import os
import sys
import platform
from pathlib import Path


def get_blender_addons_path() -> Path:
    """Get the Blender addons directory path based on the OS."""
    system = platform.system()
    home = Path.home()

    if system == "Darwin":  # macOS
        # Try different Blender versions
        for version in ["4.3", "4.2", "4.1", "4.0"]:
            path = home / "Library" / "Application Support" / "Blender" / version / "scripts" / "addons"
            if path.parent.parent.exists():
                return path
        # Default to 4.0
        return home / "Library" / "Application Support" / "Blender" / "4.0" / "scripts" / "addons"

    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        for version in ["4.3", "4.2", "4.1", "4.0"]:
            path = Path(appdata) / "Blender Foundation" / "Blender" / version / "scripts" / "addons"
            if path.parent.parent.exists():
                return path
        return Path(appdata) / "Blender Foundation" / "Blender" / "4.0" / "scripts" / "addons"

    else:  # Linux
        for version in ["4.3", "4.2", "4.1", "4.0"]:
            path = home / ".config" / "blender" / version / "scripts" / "addons"
            if path.parent.parent.exists():
                return path
        return home / ".config" / "blender" / "4.0" / "scripts" / "addons"


def main():
    # Get paths
    script_dir = Path(__file__).parent
    addon_src = script_dir.parent / "blender_addon"
    addons_dir = get_blender_addons_path()
    addon_dest = addons_dir / "blender_mcp_bridge"

    print(f"Addon source: {addon_src}")
    print(f"Addon destination: {addon_dest}")

    # Create addons directory if it doesn't exist
    addons_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing symlink or directory
    if addon_dest.exists() or addon_dest.is_symlink():
        if addon_dest.is_symlink():
            addon_dest.unlink()
            print(f"Removed existing symlink: {addon_dest}")
        else:
            print(f"Warning: {addon_dest} exists and is not a symlink.")
            print("Please remove it manually and run this script again.")
            sys.exit(1)

    # Create symlink
    try:
        addon_dest.symlink_to(addon_src)
        print(f"Created symlink: {addon_dest} -> {addon_src}")
        print()
        print("Installation complete!")
        print()
        print("Next steps:")
        print("1. Open Blender")
        print("2. Go to Edit > Preferences > Add-ons")
        print('3. Search for "Blender MCP Bridge"')
        print("4. Enable the add-on")
        print("5. In the 3D Viewport sidebar (press N), find the MCP tab")
        print("6. Click 'Start Server'")
    except OSError as e:
        print(f"Error creating symlink: {e}")
        print()
        print("On Windows, you may need to run this script as Administrator,")
        print("or enable Developer Mode in Windows Settings.")
        sys.exit(1)


if __name__ == "__main__":
    main()

---
name: blender-orchestrator
description: Build 3D scenes in Blender via MCP tools. Use when creating, modifying, or rendering 3D scenes, placing objects with spatial awareness, setting up lighting/cameras, generating meshes from text/images, or exporting for VR. Covers all blender-orchestrator MCP tools.
---

# Blender Orchestrator

Control Blender through MCP tools. The server must be running in Blender (N panel → MCP tab → Start Server).

## Core Workflow

1. **Room first** — `create_room_bounds` or manually create floor + walls
2. **Anchor objects** — Place the largest piece (sofa, bed, table) to define the room's purpose
3. **Secondary furniture** — Position relative to anchors using `find_placement_position` or `move_object_semantic`
4. **Details** — Small objects, decor, rugs
5. **Lighting** — Layer multiple light types for realism
6. **Camera** — Frame the scene for rendering
7. **Render** — `render_image` or `capture_viewport`

## Coordinate System

- **X** = left/right, **Y** = back/front, **Z** = up
- Ground plane is Z = 0
- Place room corner near origin so positions = meters from corner

## Spatial Tools (use these heavily)

**Before placing any object**, look up its real-world size:
```
get_object_dimensions(object_type="dining_table")
```

**Place objects relative to others** (handles collision + stacking):
```
find_placement_position(reference_object="Desk", relationship="on_top")
move_object_semantic(object_name="Lamp", description="place on the nightstand")
```

**Check the scene layout** with ASCII visualization:
```
show_floor_plan(view="top")           # top-down view
show_floor_plan(view="front")         # front elevation  
show_floor_plan(view="all")           # all 6 sides
show_floor_plan(view="top", cell_size=0.1, max_grid=120)  # high resolution
```

**Validate before moving** to avoid collisions:
```
validate_transform(object_name="Chair", new_location=[2, 3, 0])
get_safe_movement_range(object_name="Table")
```

**Query spatial relationships:**
```
get_spatial_relationships(object_name="Table")
query_spatial(question="what is on the desk?")
get_semantic_scene_summary()
```

## Object Dimensions Database

55+ objects across 8 categories. Always use real dimensions — don't guess.

```
list_known_objects()                              # all categories
list_known_objects(category="living_room")         # by category  
get_object_dimensions(object_type="sofa_3seat")    # specific object
get_placement_rules(room_type="bedroom")           # clearance/spacing rules
```

Categories: bedroom, living_room, dining_room, kitchen, bathroom, office, outdoor, decor

## Primitives & Transforms

```
create_cube(name="Table", size=1, location=[x,y,z], scale=[w,d,h])
create_sphere, create_cylinder, create_cone, create_torus, create_plane
move_object(name, location), rotate_object(name, rotation), scale_object(name, scale)
duplicate_object(name), delete_object(name)
```

Key: `size=1` with `scale=[w,d,h]` gives exact meter dimensions.

## Mesh Editing

`extrude_faces`, `bevel_edges`, `boolean_operation` (union/difference/intersect), `subdivide_mesh`, `add_subdivision_surface`, `inset_faces`, `smooth_mesh`

## Materials & Textures

```
create_material(name="Wood", base_color=[0.4, 0.25, 0.1], roughness=0.7)
assign_material(object_name="Table", material_name="Wood")
generate_texture(prompt="oak wood grain")
generate_pbr_material_textures(prompt="brushed metal", object_name="Lamp")
```

## Lighting

Four light types — layer them for realistic scenes:

| Tool | Use for |
|------|---------|
| `create_point_light` | Bulbs, lanterns — omnidirectional |
| `create_sun_light` | Outdoor/directional — no falloff |
| `create_spot_light` | Flashlights, stage lights — cone shaped |
| `create_area_light` | Softboxes, ceiling panels — soft shadows |

All take `location`, `energy`, `color=[r,g,b]`. Spot adds `spot_angle`, `spot_blend`. Area adds `size`.

Modify with `set_light_properties`. Query with `get_light_info`, `list_lights`.

**Interior recipe:** Area light on ceiling (200W) + point lights for lamps (30W, warm color `[1, 0.9, 0.7]`).

## Cameras

```
create_camera(name="Main", location=[x,y,z], lens=50)
look_at(camera="Main", target_object="Table")
frame_objects(camera="Main", object_names=["Sofa","Table"])  # auto-position
set_active_camera(name="Main")
set_camera_properties(name="Main", dof_enabled=True, focus_object="Chair")
```

Types: perspective (default), orthographic, panoramic.

## Rendering

```
render_image(filepath="/tmp/render.png", engine="CYCLES", samples=128)
capture_viewport(filepath="/tmp/preview.png")
set_render_settings(resolution_x=1920, resolution_y=1080)
set_world_hdri(hdri_path="/path/to/env.hdr")
```

## AI Mesh Generation

Requires API keys (MESHY_API_KEY, REPLICATE_API_TOKEN).

```
generate_mesh_from_text(prompt="wooden treasure chest", art_style="realistic")
generate_mesh_from_image(image_path="/path/to/ref.png")
import_mesh_file(filepath="/path/to/model.glb")
```

## Poly Haven (Free CC0 Assets)

No API key needed. Thousands of free HDRIs, textures, and models.

```
search_polyhaven(query="brick", asset_type="texture")
download_polyhaven_hdri(asset_id="industrial_sunset_02", resolution="4k", apply_to_scene=True)
download_polyhaven_texture(asset_id="brick_wall_02", resolution="2k", apply_to_object="Wall")
download_polyhaven_model(asset_id="wooden_chair", import_to_scene=True)
```

## VR Export

```
validate_for_vr(object_name="Chair", platform="horizon_worlds")
optimize_for_vr(object_name="Chair", platform="horizon_worlds", target_triangles=10000)
generate_lod_chain(object_name="Chair", lod_levels=[1.0, 0.5, 0.25, 0.1])
export_vr_scene(output_path="/path/to/scene.glb", platform="horizon_worlds")
```

Platform presets: `horizon_worlds` (10K tri/obj), `quest` (50K), `mobile_vr` (20K).

## Procedural & Advanced

- **Metaballs:** `create_metaball`, `add_metaball_element` — organic blobby shapes
- **Curves:** `create_bezier_curve`, `curve_to_mesh` — spline modeling
- **Skin mesh:** `create_skin_mesh` — smooth surfaces from edge skeletons
- **Character templates:** `create_character_from_template` — realistic, cartoon, chibi rigs

## Common Mistakes

1. **Guessing dimensions** — Always use `get_object_dimensions` for real sizes
2. **Objects inside each other** — Use `validate_transform` before placement
3. **Floating objects** — Z position = half the object height for ground contact
4. **Flat lighting** — Use 2-3 lights minimum, vary types and warmth
5. **No floor plan check** — Run `show_floor_plan` periodically to verify layout

For detailed scene building patterns and worked examples, read [references/scene-building-guide.md](references/scene-building-guide.md).

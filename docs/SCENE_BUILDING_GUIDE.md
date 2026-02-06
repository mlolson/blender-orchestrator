# Scene Building Guide for AI Agents

This guide teaches you how to build realistic 3D interior scenes in Blender using the orchestrator tools. Read this before creating any scene.

## Coordinate System

Blender uses **right-hand coordinates**:
- **X** = left (−) / right (+)
- **Y** = back (−) / front (+)
- **Z** = up

The ground plane is Z = 0. All heights are measured from Z = 0.

---

## Step-by-Step Workflow

### 1. Define the Room

Create walls and floor first. This establishes the spatial boundaries everything else lives inside.

```
# A 5m × 4m living room with 2.7m ceiling
create_cube(name="Floor", size=1, location=[2.5, 2.0, -0.05], scale=[5.0, 4.0, 0.1])
create_cube(name="Wall_Back", size=1, location=[2.5, 0.0, 1.35], scale=[5.0, 0.15, 2.7])
create_cube(name="Wall_Left", size=1, location=[0.0, 2.0, 1.35], scale=[0.15, 4.0, 2.7])
create_cube(name="Wall_Right", size=1, location=[5.0, 2.0, 1.35], scale=[0.15, 4.0, 2.7])
create_cube(name="Wall_Front", size=1, location=[2.5, 4.0, 1.35], scale=[5.0, 0.15, 2.7])
```

**Tip:** Place the room so that one corner is near the origin (0, 0, 0). This makes coordinate math easy — positions are just real-world meters from that corner.

### 2. Place Anchor / Focal Objects

These are the largest, most important pieces that define the room's function: a bed in a bedroom, a sofa in a living room, a dining table in a dining room.

```
# Sofa against back wall, centered in a 5m-wide room
# Typical 3-seat sofa: 2.2m wide × 0.9m deep × 0.85m high
create_cube(name="Sofa", size=1, location=[2.5, 0.6, 0.425], scale=[2.2, 0.9, 0.85])
```

Position anchors first because everything else arranges around them.

### 3. Add Secondary Furniture

Pieces that support or relate to the anchor: coffee table in front of the sofa, nightstands beside the bed, chairs around the dining table.

```
# Coffee table centered in front of sofa, 0.5m gap for legs
# Typical coffee table: 1.2m × 0.6m × 0.45m
create_cube(name="CoffeeTable", size=1, location=[2.5, 1.55, 0.225], scale=[1.2, 0.6, 0.45])

# TV stand against the opposite wall (Y=3.8), facing the sofa
create_cube(name="TVStand", size=1, location=[2.5, 3.8, 0.3], scale=[1.5, 0.45, 0.6])
```

### 4. Add Details and Décor

Small objects that make the scene feel lived-in: lamps, books, cushions, plants, rugs.

```
# Table lamp on the TV stand
create_cylinder(name="Lamp_Base", radius=0.08, depth=0.25, location=[3.1, 3.8, 0.725])
create_cone(name="Lamp_Shade", radius1=0.15, radius2=0.05, depth=0.2, location=[3.1, 3.8, 0.95])

# Rug under coffee table
create_plane(name="Rug", size=1, location=[2.5, 1.3, 0.005], scale=[2.0, 1.5, 1.0])
```

### 5. Set Up Lighting

Interior scenes need warm, layered light. Combine multiple light types.

```
# Main ceiling light
create_area_light(name="CeilingLight", location=[2.5, 2.0, 2.6], energy=200, size=0.5)

# Warm accent lamp (simulating the table lamp)
create_point_light(name="LampGlow", location=[3.1, 3.8, 0.9], energy=30, color=[1.0, 0.9, 0.7])

# Soft fill from a window direction
create_area_light(name="WindowLight", location=[5.0, 2.0, 2.0], energy=100, size=1.5,
                  rotation=[0, -90, 0])
```

### 6. Position Camera and Review

```
# Camera from corner, looking at the scene
create_camera(name="MainCamera", location=[0.5, -0.5, 1.7], rotation=[75, 0, 25])
look_at(camera_name="MainCamera", target_location=[2.5, 2.0, 0.8])

# Review the scene
get_semantic_scene_summary(detail_level="detailed")
capture_viewport()
```

---

## Common Room Dimensions (meters)

Use these as starting points. All values are interior dimensions (wall-to-wall).

| Room Type | Small | Medium | Large |
|-----------|-------|--------|-------|
| Living Room | 3.5 × 4.0 | 5.0 × 4.0 | 7.0 × 5.0 |
| Bedroom | 3.0 × 3.0 | 4.0 × 4.5 | 5.0 × 5.5 |
| Kitchen | 2.5 × 3.0 | 3.5 × 4.0 | 5.0 × 4.5 |
| Bathroom | 1.5 × 2.0 | 2.5 × 3.0 | 3.5 × 3.5 |
| Home Office | 2.5 × 3.0 | 3.0 × 4.0 | 4.5 × 5.0 |
| Dining Room | 3.0 × 3.0 | 4.0 × 4.5 | 5.5 × 5.0 |

**Ceiling height:** 2.4m (low) · 2.7m (standard) · 3.0m+ (high)

---

## Common Object Dimensions (meters)

### Living Room
| Object | Width (X) | Depth (Y) | Height (Z) |
|--------|-----------|-----------|------------|
| 3-seat sofa | 2.0–2.4 | 0.85–0.95 | 0.80–0.90 |
| 2-seat sofa / loveseat | 1.4–1.7 | 0.85 | 0.80–0.85 |
| Armchair | 0.80–0.95 | 0.85 | 0.80–0.90 |
| Coffee table | 1.0–1.3 | 0.50–0.65 | 0.40–0.50 |
| TV (55″ on stand) | 1.25 | 0.08 | 0.72 |
| TV stand | 1.2–1.8 | 0.40–0.50 | 0.45–0.60 |
| Bookshelf | 0.80–1.2 | 0.30 | 1.8–2.0 |
| Floor lamp | 0.30 | 0.30 | 1.5–1.8 |

### Bedroom
| Object | Width (X) | Depth (Y) | Height (Z) |
|--------|-----------|-----------|------------|
| Double bed | 1.40 | 2.00 | 0.55 (mattress top) |
| Queen bed | 1.60 | 2.00 | 0.55 |
| King bed | 1.80 | 2.00 | 0.55 |
| Nightstand | 0.45–0.55 | 0.40 | 0.55–0.65 |
| Dresser | 1.2–1.5 | 0.50 | 0.80 |
| Wardrobe | 1.0–2.0 | 0.60 | 2.0–2.2 |

### Dining Room
| Object | Width (X) | Depth (Y) | Height (Z) |
|--------|-----------|-----------|------------|
| Dining table (4-seat) | 1.2 | 0.80 | 0.75 |
| Dining table (6-seat) | 1.6–1.8 | 0.90 | 0.75 |
| Dining table (8-seat) | 2.2 | 1.0 | 0.75 |
| Dining chair | 0.45 | 0.50 | 0.90 (seat at 0.45) |

### Kitchen
| Object | Width (X) | Depth (Y) | Height (Z) |
|--------|-----------|-----------|------------|
| Kitchen counter | varies | 0.60 | 0.90 |
| Bar stool | 0.40 | 0.40 | 0.75 (seat) |
| Refrigerator | 0.70 | 0.70 | 1.8 |

### Office
| Object | Width (X) | Depth (Y) | Height (Z) |
|--------|-----------|-----------|------------|
| Desk | 1.2–1.6 | 0.60–0.80 | 0.73 |
| Office chair | 0.60 | 0.60 | 0.90–1.2 |
| Monitor (27″) | 0.62 | 0.20 | 0.37 |

---

## Object Placement Rules of Thumb

### Spacing and Clearance
- **Walking path:** 0.9m minimum clearance
- **Sofa to coffee table:** 0.40–0.50m gap
- **Chair pull-back space:** 0.75m behind dining chairs
- **Bedside clearance:** 0.60m on at least one side of the bed
- **Doorway clearance:** 0.80m minimum; keep path clear

### Arrangement Patterns

**Living Room:**
- Sofa faces the focal point (TV, fireplace, window)
- Sofa is typically against or near a wall (back of sofa Y ≈ wall Y + sofa depth/2)
- Coffee table is centered in front of the sofa
- Armchairs flank the sofa or sit perpendicular to it
- Rug anchors the seating group — extend under front legs of sofa

**Bedroom:**
- Bed centered on the longest wall, headboard flush with wall
- Nightstands on both sides of the bed, tops aligned with mattress height
- Dresser on the opposite wall, facing the bed
- Wardrobe against a side wall, near the door

**Dining Room:**
- Table centered in the room
- Chairs evenly spaced around the table, pushed in (edge of chair ≈ edge of table)
- Allow 0.75m+ behind chairs for pull-back
- Pendant light directly above center of table, at Z ≈ 1.8–2.0m

**Kitchen:**
- Counters along walls (the "work triangle": sink, stove, fridge within ~3–6m total path)
- Island centered with 1.0m clearance on all walkable sides
- Bar stools tucked under island overhang

**Office:**
- Desk facing a wall or window
- Chair behind desk (between desk and wall behind)
- Monitor on desk, centered or slightly off-center
- Bookshelf along a side wall

### Positioning Objects ON Other Objects

When placing something on a surface, set Z = surface_height + object_height/2:

```
# Place a book (0.03m tall) on a desk (0.73m high)
# Book Z = 0.73 + 0.03/2 = 0.745
create_cube(name="Book", size=1, location=[1.0, 0.5, 0.745], scale=[0.22, 0.15, 0.03])
```

Or use the spatial tool:

```
find_placement_position(reference="Desk", relation="on", object_size=[0.22, 0.15, 0.03])
```

### Positioning Objects NEXT TO Other Objects

Add half-widths of both objects plus a small gap:

```
# Nightstand (0.50m wide) next to a queen bed (1.60m wide)
# Bed center X = 2.0, bed edge = 2.0 + 1.6/2 = 2.8
# Nightstand center X = 2.8 + gap(0.02) + 0.5/2 = 3.07
create_cube(name="Nightstand", size=1, location=[3.07, 0.5, 0.3], scale=[0.50, 0.40, 0.60])
```

Or use:

```
find_placement_position(reference="Bed", relation="right_of", object_size=[0.5, 0.4, 0.6])
```

---

## Tool Usage Patterns

### Recommended Tool Order

| Phase | Tools |
|-------|-------|
| 1. Setup | `check_blender_connection` |
| 2. Room shell | `create_cube` (floor, walls, ceiling) |
| 3. Major furniture | `create_cube` (rough shapes) or `download_polyhaven_model` / `generate_mesh_from_text` |
| 4. Smaller objects | `create_cube`, `create_cylinder`, `create_cone`, `create_sphere` |
| 5. Materials | `create_and_assign_material`, `generate_pbr_material_textures`, `download_polyhaven_texture` |
| 6. Lighting | `create_area_light`, `create_point_light`, `create_sun_light` |
| 7. Camera | `create_camera`, `look_at`, `frame_objects` |
| 8. Review | `get_semantic_scene_summary`, `capture_viewport`, `render_image` |
| 9. Adjust | `move_object`, `scale_object`, `move_object_semantic`, `validate_transform` |

### When to Use Spatial Tools

- **`get_semantic_scene_summary`** — After placing several objects, to understand the overall layout
- **`get_spatial_relationships`** — To check what's near a specific object before adding more
- **`find_placement_position`** — When you need to place something relative to an existing object and want collision-free coordinates
- **`validate_transform`** — Before moving objects, to check for collisions or ground penetration
- **`move_object_semantic`** — When a natural language instruction is easier than calculating coordinates ("place on the desk", "move next to the chair")
- **`query_spatial`** — To answer questions like "what is on the table?" or "what is to the left of the sofa?"

### Using Poly Haven for Realism

Primitive cubes are fine for layout, but swap them for real models when possible:

```
# Search for a sofa model
search_polyhaven(query="sofa", asset_type="model")

# Download and place it
download_polyhaven_model(asset_id="sofa_03", import_to_scene=True, location=[2.5, 0.6, 0])

# Apply realistic materials
download_polyhaven_texture(asset_id="leather_brown", resolution="2k", apply_to_object="sofa_03")
```

---

## Common Mistakes to Avoid

### ❌ Everything at the Origin
**Problem:** Placing all objects at (0, 0, 0) and trying to move them later.
**Fix:** Calculate the correct position *before* creating each object. Use the room corner as your reference point.

### ❌ Wrong Scale
**Problem:** A chair that's 5m tall or a table that's 10cm wide.
**Fix:** Always check the dimension tables above. When using `create_cube(size=1)`, the `scale` parameter directly sets the dimensions in meters.

### ❌ Floating Objects
**Problem:** Objects hovering above the floor because Z was set to 0 (centers the object at ground level, half of it underground, but thin objects appear to float).
**Fix:** For an object of height H sitting on the floor: Z = H / 2. A 0.75m tall table → Z = 0.375.

### ❌ Objects Inside the Floor
**Problem:** Opposite of floating — large objects with Z=0 are half-buried.
**Fix:** Same rule: Z = height / 2 for floor-standing objects.

### ❌ Ignoring Room Boundaries
**Problem:** Furniture placed outside the walls or intersecting them.
**Fix:** Keep all object positions within your room bounds. For a 5×4m room: all X values between 0.15 and 4.85 (wall thickness), all Y between 0.15 and 3.85.

### ❌ Too Sparse
**Problem:** A room with only 2–3 objects feels empty and unrealistic.
**Fix:** Real rooms have layers: big furniture → small furniture → décor → textiles → lighting. A typical living room has 15–25 objects.

### ❌ Too Crowded
**Problem:** Objects jammed together with no walkable space.
**Fix:** Maintain 0.9m+ walkways. Stand back and use `capture_viewport` to visually check.

### ❌ Everything Perfectly Aligned
**Problem:** Every object on a perfect grid looks sterile.
**Fix:** Offset small objects slightly (±0.05m). Rotate décor items a few degrees. Real rooms aren't perfectly symmetric.

### ❌ No Material Variation
**Problem:** Every surface is the same default grey.
**Fix:** Assign materials as you go. Different colors and textures make spaces readable: wood for floors, fabric for sofas, metal for fixtures.

---

## Spatial Calculation Cheatsheet

### Object on floor
```
Z = object_height / 2
```

### Object on a surface
```
Z = surface_top + object_height / 2
```

### Object against a wall (back wall at Y=0, wall thickness 0.15m)
```
Y = wall_Y + wall_thickness/2 + object_depth/2
  = 0 + 0.075 + object_depth/2
```

### Object centered in room
```
X = room_width / 2
Y = room_depth / 2
```

### Chair around a table (4 chairs, table at center_x, center_y)
```
Chair_North: (center_x, center_y + table_depth/2 + 0.1, seat_Z)
Chair_South: (center_x, center_y - table_depth/2 - 0.1, seat_Z)
Chair_East:  (center_x + table_width/2 + 0.1, center_y, seat_Z)  # rotated 90°
Chair_West:  (center_x - table_width/2 - 0.1, center_y, seat_Z)  # rotated -90°
```

### Spacing N objects evenly along a wall
```
spacing = wall_length / (N + 1)
position_i = wall_start + spacing * i   (for i = 1..N)
```

---

## Example: Complete Living Room

Here's a complete, realistic living room scene with coordinates:

```python
# Room: 5.0m × 4.0m × 2.7m, corner at origin
# Floor
create_cube(name="Floor", size=1, location=[2.5, 2.0, -0.05], scale=[5.0, 4.0, 0.1])

# Walls (0.15m thick)
create_cube(name="Wall_Back", size=1, location=[2.5, 0.075, 1.35], scale=[5.0, 0.15, 2.7])
create_cube(name="Wall_Front", size=1, location=[2.5, 3.925, 1.35], scale=[5.0, 0.15, 2.7])
create_cube(name="Wall_Left", size=1, location=[0.075, 2.0, 1.35], scale=[0.15, 4.0, 2.7])
create_cube(name="Wall_Right", size=1, location=[4.925, 2.0, 1.35], scale=[0.15, 4.0, 2.7])

# Sofa (2.2 × 0.9 × 0.85), against back wall
create_cube(name="Sofa", size=1, location=[2.5, 0.6, 0.425], scale=[2.2, 0.9, 0.85])

# Coffee table (1.2 × 0.6 × 0.45), 0.45m in front of sofa
create_cube(name="CoffeeTable", size=1, location=[2.5, 1.5, 0.225], scale=[1.2, 0.6, 0.45])

# TV stand (1.5 × 0.45 × 0.5), against front wall
create_cube(name="TVStand", size=1, location=[2.5, 3.55, 0.25], scale=[1.5, 0.45, 0.5])

# TV on stand (1.25 × 0.08 × 0.72)
create_cube(name="TV", size=1, location=[2.5, 3.5, 0.86], scale=[1.25, 0.08, 0.72])

# Armchair (0.85 × 0.85 × 0.85), left side facing center
create_cube(name="Armchair", size=1, location=[0.65, 1.5, 0.425], scale=[0.85, 0.85, 0.85])
rotate_object(name="Armchair", rotation=[0, 0, -30])

# Side table (0.5 × 0.5 × 0.55) next to armchair
create_cube(name="SideTable", size=1, location=[0.65, 0.75, 0.275], scale=[0.5, 0.5, 0.55])

# Bookshelf (1.0 × 0.3 × 1.9) against right wall
create_cube(name="Bookshelf", size=1, location=[4.6, 1.2, 0.95], scale=[1.0, 0.3, 1.9])

# Rug (2.5 × 1.8 × 0.01) under seating area
create_plane(name="Rug", size=1, location=[2.5, 1.2, 0.005], scale=[2.5, 1.8, 1.0])

# Floor lamp (behind armchair)
create_cylinder(name="FloorLamp_Pole", radius=0.03, depth=1.6, location=[0.3, 0.9, 0.8])
create_sphere(name="FloorLamp_Shade", radius=0.15, location=[0.3, 0.9, 1.65])

# Materials
create_and_assign_material(name="WoodFloor", object_name="Floor",
    base_color=[0.45, 0.30, 0.18, 1.0], roughness=0.6)
create_and_assign_material(name="WhiteWall", object_name="Wall_Back",
    base_color=[0.92, 0.91, 0.88, 1.0], roughness=0.9)
assign_material(object_name="Wall_Front", material_name="WhiteWall")
assign_material(object_name="Wall_Left", material_name="WhiteWall")
assign_material(object_name="Wall_Right", material_name="WhiteWall")
create_and_assign_material(name="GraySofa", object_name="Sofa",
    base_color=[0.35, 0.38, 0.42, 1.0], roughness=0.85)

# Lighting
create_area_light(name="CeilingLight", location=[2.5, 2.0, 2.6], energy=150, size=0.6)
create_point_light(name="LampLight", location=[0.3, 0.9, 1.6], energy=25,
    color=[1.0, 0.92, 0.78])

# Camera
create_camera(name="Camera", location=[-0.5, -0.8, 1.8])
look_at(camera_name="Camera", target_location=[2.5, 2.0, 0.8])

# Review
get_semantic_scene_summary(detail_level="detailed")
```

This produces a room with ~15 objects, proper proportions, walkable paths, and layered lighting — a solid foundation to refine with better models, textures, and details.

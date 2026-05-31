"""
materials.py — Create golf course material templates for Blender/OPCD.

Part of the Ellensburg Golf Club GS Pro course build pipeline.
Pipeline stage: After terrain import, before vegetation placement.

Usage:
    1. Open your Blender project (after running import_dem.py)
    2. Go to Scripting workspace
    3. Open this file and press "Run Script"
    4. All materials are created and available in the material browser
    5. Select objects and use apply_material_to_selected() or the
       operator from the Object menu

Materials are tuned for the semi-arid Central Washington environment:
- Grass is slightly more brown/yellow than Pacific NW coastal courses
- Sand bunkers use the tan/beige of local river sand
- Trees include Ponderosa pine bark and cottonwood textures

Each material uses the Principled BSDF shader for PBR compatibility
with Unity/GS Pro export.
"""

import bpy
import math


# ---------------------------------------------------------------------------
# Material definitions
# ---------------------------------------------------------------------------

# Each material is defined as a dict with Principled BSDF parameters.
# Colors are in linear sRGB (Blender's internal color space).
# All values are tuned for realistic golf course appearance.

MATERIAL_DEFS = {
    # -----------------------------------------------------------------------
    # PLAYING SURFACES
    # -----------------------------------------------------------------------
    "Fairway": {
        "description": "Mowed fairway grass — short, green, slightly glossy from blade sheen",
        "base_color": (0.12, 0.22, 0.06, 1.0),      # Medium green
        "roughness": 0.7,
        "specular": 0.3,                               # Slight sheen from grass blades
        "subsurface": 0.05,                            # Very slight translucency
        "subsurface_color": (0.15, 0.25, 0.05, 1.0),
        "normal_strength": 0.3,                        # Subtle grass blade texture
        "normal_scale": 50.0,                          # Fine grain
        "bump_strength": 0.1,
    },

    "Green": {
        "description": "Putting green — very short, dense, dark green, smooth surface",
        "base_color": (0.08, 0.18, 0.04, 1.0),        # Darker green than fairway
        "roughness": 0.55,                              # Smoother than fairway
        "specular": 0.4,                                # More sheen from dense, short grass
        "subsurface": 0.08,
        "subsurface_color": (0.10, 0.20, 0.04, 1.0),
        "normal_strength": 0.15,                        # Very fine texture
        "normal_scale": 80.0,
        "bump_strength": 0.05,
    },

    "Rough": {
        "description": "Primary rough — longer grass, less maintained, muted color",
        "base_color": (0.16, 0.22, 0.08, 1.0),        # More yellow-green (semi-arid)
        "roughness": 0.85,                              # Rougher surface from longer grass
        "specular": 0.2,
        "subsurface": 0.03,
        "subsurface_color": (0.18, 0.22, 0.08, 1.0),
        "normal_strength": 0.5,                         # More visible grass texture
        "normal_scale": 30.0,
        "bump_strength": 0.2,
    },

    "HeavyRough": {
        "description": "Deep rough / native area — tall grass, brownish-green (Kittitas valley native)",
        "base_color": (0.20, 0.22, 0.10, 1.0),        # Brown-green native grass
        "roughness": 0.92,
        "specular": 0.15,
        "subsurface": 0.02,
        "subsurface_color": (0.22, 0.20, 0.10, 1.0),
        "normal_strength": 0.7,
        "normal_scale": 20.0,
        "bump_strength": 0.3,
    },

    "TeeBox": {
        "description": "Tee box surface — well-maintained, slightly different hue from fairway",
        "base_color": (0.10, 0.20, 0.05, 1.0),        # Between green and fairway color
        "roughness": 0.65,
        "specular": 0.35,
        "subsurface": 0.06,
        "subsurface_color": (0.12, 0.22, 0.05, 1.0),
        "normal_strength": 0.25,
        "normal_scale": 60.0,
        "bump_strength": 0.08,
    },

    "FringeCollar": {
        "description": "Fringe/collar around greens — transitional grass length",
        "base_color": (0.11, 0.20, 0.06, 1.0),        # Between green and fairway
        "roughness": 0.65,
        "specular": 0.32,
        "subsurface": 0.05,
        "subsurface_color": (0.13, 0.22, 0.06, 1.0),
        "normal_strength": 0.25,
        "normal_scale": 55.0,
        "bump_strength": 0.1,
    },

    # -----------------------------------------------------------------------
    # HAZARDS
    # -----------------------------------------------------------------------
    "Bunker": {
        "description": "Sand bunker — tan/beige river sand typical of Central WA",
        "base_color": (0.55, 0.48, 0.35, 1.0),        # Tan/beige sand
        "roughness": 0.95,                              # Very rough sand surface
        "specular": 0.1,                                # Sand barely reflects
        "subsurface": 0.0,
        "subsurface_color": (0.55, 0.48, 0.35, 1.0),
        "normal_strength": 0.8,                         # Visible sand grain texture
        "normal_scale": 100.0,
        "bump_strength": 0.15,
    },

    "Water": {
        "description": "Water hazard — reflective blue with slight transparency",
        "base_color": (0.02, 0.08, 0.15, 1.0),        # Deep blue-green
        "roughness": 0.05,                              # Very smooth/reflective
        "specular": 0.8,                                # Highly reflective
        "subsurface": 0.0,
        "subsurface_color": (0.02, 0.08, 0.15, 1.0),
        "transmission": 0.3,                            # Partial transparency
        "transmission_roughness": 0.1,
        "ior": 1.333,                                   # Water's index of refraction
        "alpha": 0.85,                                  # Slight transparency
        "normal_strength": 0.2,                         # Subtle surface ripples
        "normal_scale": 15.0,
        "bump_strength": 0.05,
    },

    # -----------------------------------------------------------------------
    # HARDSCAPE
    # -----------------------------------------------------------------------
    "CartPath": {
        "description": "Cart path — gray asphalt/concrete surface",
        "base_color": (0.35, 0.33, 0.30, 1.0),        # Gray concrete
        "roughness": 0.75,
        "specular": 0.3,
        "subsurface": 0.0,
        "subsurface_color": (0.35, 0.33, 0.30, 1.0),
        "normal_strength": 0.4,                         # Visible aggregate texture
        "normal_scale": 40.0,
        "bump_strength": 0.1,
    },

    "DirtPath": {
        "description": "Worn dirt path / bare ground",
        "base_color": (0.30, 0.25, 0.18, 1.0),        # Brown dirt
        "roughness": 0.90,
        "specular": 0.1,
        "subsurface": 0.0,
        "subsurface_color": (0.30, 0.25, 0.18, 1.0),
        "normal_strength": 0.6,
        "normal_scale": 25.0,
        "bump_strength": 0.2,
    },

    # -----------------------------------------------------------------------
    # VEGETATION
    # -----------------------------------------------------------------------
    "TreeTrunk_Ponderosa": {
        "description": "Ponderosa pine bark — orange-brown, deeply furrowed puzzle-bark",
        "base_color": (0.30, 0.18, 0.08, 1.0),        # Orange-brown bark
        "roughness": 0.95,
        "specular": 0.05,
        "subsurface": 0.0,
        "subsurface_color": (0.30, 0.18, 0.08, 1.0),
        "normal_strength": 1.0,                         # Deep bark furrows
        "normal_scale": 8.0,
        "bump_strength": 0.4,
    },

    "TreeTrunk_Cottonwood": {
        "description": "Cottonwood bark — gray, deeply furrowed on mature trees",
        "base_color": (0.28, 0.26, 0.22, 1.0),        # Gray-brown bark
        "roughness": 0.92,
        "specular": 0.08,
        "subsurface": 0.0,
        "subsurface_color": (0.28, 0.26, 0.22, 1.0),
        "normal_strength": 0.9,
        "normal_scale": 6.0,
        "bump_strength": 0.35,
    },

    "Foliage_Pine": {
        "description": "Ponderosa pine needles — dark green, long needles in clusters",
        "base_color": (0.05, 0.12, 0.04, 1.0),        # Dark pine green
        "roughness": 0.75,
        "specular": 0.2,
        "subsurface": 0.15,                             # Needle translucency
        "subsurface_color": (0.08, 0.15, 0.03, 1.0),
        "normal_strength": 0.4,
        "normal_scale": 10.0,
        "bump_strength": 0.15,
        "alpha": 0.95,                                  # Slight gaps in canopy
    },

    "Foliage_Cottonwood": {
        "description": "Cottonwood leaves — lighter green, broad leaves, flutter in wind",
        "base_color": (0.10, 0.20, 0.06, 1.0),        # Lighter deciduous green
        "roughness": 0.6,
        "specular": 0.25,
        "subsurface": 0.2,                              # Leaf translucency
        "subsurface_color": (0.12, 0.25, 0.05, 1.0),
        "normal_strength": 0.3,
        "normal_scale": 15.0,
        "bump_strength": 0.1,
        "alpha": 0.9,
    },

    "Foliage_Willow": {
        "description": "Willow leaves — long, narrow, sage-green",
        "base_color": (0.12, 0.18, 0.08, 1.0),        # Sage green
        "roughness": 0.55,
        "specular": 0.3,
        "subsurface": 0.18,
        "subsurface_color": (0.14, 0.22, 0.08, 1.0),
        "normal_strength": 0.25,
        "normal_scale": 20.0,
        "bump_strength": 0.08,
        "alpha": 0.88,
    },

    # -----------------------------------------------------------------------
    # STRUCTURES
    # -----------------------------------------------------------------------
    "Clubhouse_Walls": {
        "description": "Clubhouse exterior walls — light painted wood/stucco",
        "base_color": (0.60, 0.55, 0.48, 1.0),        # Light tan/cream
        "roughness": 0.65,
        "specular": 0.3,
        "subsurface": 0.0,
        "subsurface_color": (0.60, 0.55, 0.48, 1.0),
        "normal_strength": 0.3,
        "normal_scale": 30.0,
        "bump_strength": 0.1,
    },

    "Clubhouse_Roof": {
        "description": "Clubhouse roof — dark composite shingle",
        "base_color": (0.15, 0.13, 0.12, 1.0),        # Dark gray
        "roughness": 0.85,
        "specular": 0.15,
        "subsurface": 0.0,
        "subsurface_color": (0.15, 0.13, 0.12, 1.0),
        "normal_strength": 0.5,
        "normal_scale": 12.0,
        "bump_strength": 0.2,
    },

    "Concrete": {
        "description": "Generic concrete — sidewalks, foundations",
        "base_color": (0.45, 0.43, 0.40, 1.0),
        "roughness": 0.80,
        "specular": 0.2,
        "subsurface": 0.0,
        "subsurface_color": (0.45, 0.43, 0.40, 1.0),
        "normal_strength": 0.35,
        "normal_scale": 35.0,
        "bump_strength": 0.1,
    },
}

# Mapping from GS Pro / OPCD feature type names to material names.
# Used by apply_material_by_feature_type().
FEATURE_TYPE_MAP = {
    "fairway": "Fairway",
    "green": "Green",
    "putting_green": "Green",
    "rough": "Rough",
    "heavy_rough": "HeavyRough",
    "native": "HeavyRough",
    "tee": "TeeBox",
    "tee_box": "TeeBox",
    "teebox": "TeeBox",
    "fringe": "FringeCollar",
    "collar": "FringeCollar",
    "bunker": "Bunker",
    "sand": "Bunker",
    "sand_trap": "Bunker",
    "water": "Water",
    "pond": "Water",
    "creek": "Water",
    "river": "Water",
    "cart_path": "CartPath",
    "cartpath": "CartPath",
    "path": "CartPath",
    "dirt": "DirtPath",
    "tree_trunk": "TreeTrunk_Ponderosa",
    "trunk_ponderosa": "TreeTrunk_Ponderosa",
    "trunk_cottonwood": "TreeTrunk_Cottonwood",
    "pine": "Foliage_Pine",
    "pine_foliage": "Foliage_Pine",
    "ponderosa": "Foliage_Pine",
    "cottonwood": "Foliage_Cottonwood",
    "deciduous": "Foliage_Cottonwood",
    "willow": "Foliage_Willow",
    "building": "Clubhouse_Walls",
    "clubhouse": "Clubhouse_Walls",
    "roof": "Clubhouse_Roof",
    "concrete": "Concrete",
}


# ---------------------------------------------------------------------------
# Material creation functions
# ---------------------------------------------------------------------------

def create_noise_texture_node(nodes, links, location, scale=10.0):
    """
    Create a Noise Texture node for procedural surface detail.
    Returns the node so its outputs can be connected.
    """
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = location
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.6
    noise.inputs['Distortion'].default_value = 0.0
    return noise


def create_bump_node(nodes, links, location, strength=0.1):
    """
    Create a Bump node for surface detail.
    Returns the node.
    """
    bump = nodes.new('ShaderNodeBump')
    bump.location = location
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = 0.02
    return bump


def create_material(name, mat_def):
    """
    Create a single Blender material from a material definition dict.
    Uses the Principled BSDF shader with procedural noise for surface detail.

    Args:
        name: Material name (e.g., "Fairway")
        mat_def: Dict of material parameters (from MATERIAL_DEFS)

    Returns:
        The created bpy.types.Material
    """
    # Remove existing material with same name
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Enable backface culling for performance
    mat.use_backface_culling = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # --- Output node ---
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    # --- Principled BSDF ---
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)

    # Set base properties
    bsdf.inputs['Base Color'].default_value = mat_def["base_color"]
    bsdf.inputs['Roughness'].default_value = mat_def["roughness"]

    # Specular handling differs between Blender 3.x and 4.x
    # Blender 4.0+ renamed "Specular" to "Specular IOR Level"
    specular_input = None
    for input_name in ['Specular IOR Level', 'Specular']:
        if input_name in bsdf.inputs:
            specular_input = bsdf.inputs[input_name]
            break
    if specular_input:
        specular_input.default_value = mat_def.get("specular", 0.5)

    # Subsurface scattering (for grass translucency)
    if mat_def.get("subsurface", 0) > 0:
        # Blender 4.0+ changed subsurface parameter names
        if 'Subsurface Weight' in bsdf.inputs:
            bsdf.inputs['Subsurface Weight'].default_value = mat_def["subsurface"]
        elif 'Subsurface' in bsdf.inputs:
            bsdf.inputs['Subsurface'].default_value = mat_def["subsurface"]

        if 'Subsurface Color' in bsdf.inputs:
            bsdf.inputs['Subsurface Color'].default_value = mat_def.get(
                "subsurface_color", mat_def["base_color"])

    # Transmission (for water)
    if mat_def.get("transmission", 0) > 0:
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = mat_def["transmission"]
        elif 'Transmission' in bsdf.inputs:
            bsdf.inputs['Transmission'].default_value = mat_def["transmission"]

    # IOR (for water)
    if "ior" in mat_def:
        bsdf.inputs['IOR'].default_value = mat_def["ior"]

    # Alpha (for transparency)
    if mat_def.get("alpha", 1.0) < 1.0:
        bsdf.inputs['Alpha'].default_value = mat_def["alpha"]
        # blend_method / shadow_method were removed from Material in
        # Blender 4.2+ (EEVEE Next). Guard the ATTRIBUTE itself — the
        # assignment `mat.shadow_method = ...` is attempted even when the
        # right-hand value is None, which raises AttributeError on 4.2+.
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
        if hasattr(mat, 'shadow_method'):
            mat.shadow_method = 'HASHED'

    # Emission color (Blender 4.x)
    if 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = (0, 0, 0, 1)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # --- Procedural noise for surface detail ---
    # This gives each surface a subtle texture without needing image textures.
    # For final production, these can be replaced with photo textures.

    normal_strength = mat_def.get("normal_strength", 0)
    if normal_strength > 0:
        # Texture Coordinate for consistent mapping
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (-600, 0)

        # Primary noise texture
        noise = create_noise_texture_node(
            nodes, links, (-400, 0),
            scale=mat_def.get("normal_scale", 30.0)
        )
        links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])

        # Bump node converts noise to normal perturbation
        bump = create_bump_node(
            nodes, links, (200, -200),
            strength=mat_def.get("bump_strength", 0.1)
        )
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

        # Color variation: mix the base color with noise for natural variation
        color_mix = nodes.new('ShaderNodeMixRGB')
        color_mix.location = (0, 200)
        color_mix.blend_type = 'OVERLAY'
        color_mix.inputs['Fac'].default_value = 0.15  # Subtle variation
        color_mix.inputs['Color1'].default_value = mat_def["base_color"]

        # Secondary noise for color variation (larger scale)
        color_noise = create_noise_texture_node(
            nodes, links, (-400, 300),
            scale=mat_def.get("normal_scale", 30.0) * 0.3  # Larger features
        )
        links.new(tex_coord.outputs['Object'], color_noise.inputs['Vector'])
        links.new(color_noise.outputs['Color'], color_mix.inputs['Color2'])
        links.new(color_mix.outputs['Color'], bsdf.inputs['Base Color'])

    # Store the description as a custom property for reference
    mat["description"] = mat_def.get("description", "")
    mat["feature_type"] = name

    return mat


def create_all_materials():
    """
    Create all golf course materials defined in MATERIAL_DEFS.
    Existing materials with the same names are replaced.

    Returns:
        Dict mapping material names to Blender material objects.
    """
    created = {}
    print(f"\n{'='*60}")
    print("  CREATING GOLF COURSE MATERIALS")
    print(f"{'='*60}\n")

    for name, mat_def in MATERIAL_DEFS.items():
        mat = create_material(name, mat_def)
        created[name] = mat
        print(f"  [+] {name}: {mat_def.get('description', '')}")

    print(f"\n  Created {len(created)} materials")
    print(f"{'='*60}\n")
    return created


# ---------------------------------------------------------------------------
# Material application functions
# ---------------------------------------------------------------------------

def apply_material_to_selected(material_name):
    """
    Apply a material to all currently selected objects in Blender.

    Args:
        material_name: Name of the material (must exist in bpy.data.materials)
    """
    if material_name not in bpy.data.materials:
        print(f"[materials] Material '{material_name}' not found. Run create_all_materials() first.")
        return

    mat = bpy.data.materials[material_name]
    count = 0

    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
            count += 1

    print(f"[materials] Applied '{material_name}' to {count} objects")


def apply_material_by_feature_type(feature_type):
    """
    Apply a material to selected objects based on GS Pro feature type name.
    This handles common naming variations (e.g., "tee", "tee_box", "teebox").

    Args:
        feature_type: String like "fairway", "green", "bunker", etc.
    """
    feature_key = feature_type.lower().strip()

    if feature_key not in FEATURE_TYPE_MAP:
        print(f"[materials] Unknown feature type: '{feature_type}'")
        print(f"[materials] Known types: {', '.join(sorted(FEATURE_TYPE_MAP.keys()))}")
        return

    material_name = FEATURE_TYPE_MAP[feature_key]
    apply_material_to_selected(material_name)


def apply_material_to_object(obj, material_name):
    """
    Apply a material to a specific object by reference.

    Args:
        obj: Blender object (bpy.types.Object)
        material_name: Name of the material
    """
    if material_name not in bpy.data.materials:
        print(f"[materials] Material '{material_name}' not found.")
        return

    mat = bpy.data.materials[material_name]

    if obj.type != 'MESH':
        print(f"[materials] Object '{obj.name}' is not a mesh, skipping.")
        return

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    print(f"[materials] Applied '{material_name}' to '{obj.name}'")


def list_materials():
    """Print all available golf course materials and their descriptions."""
    print(f"\n{'='*60}")
    print("  AVAILABLE GOLF COURSE MATERIALS")
    print(f"{'='*60}\n")

    for name in sorted(MATERIAL_DEFS.keys()):
        mat_def = MATERIAL_DEFS[name]
        exists = "Y" if name in bpy.data.materials else " "
        print(f"  [{exists}] {name:25s} — {mat_def.get('description', '')}")

    print(f"\n  Total: {len(MATERIAL_DEFS)} materials defined")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Blender Operator — adds "Apply Golf Material" to the Object menu
# ---------------------------------------------------------------------------

class OBJECT_OT_apply_golf_material(bpy.types.Operator):
    """Apply a golf course material to selected objects"""
    bl_idname = "object.apply_golf_material"
    bl_label = "Apply Golf Material"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: bpy.props.EnumProperty(
        name="Material",
        description="Golf course material to apply",
        items=lambda self, context: [
            (name, name, mat_def.get("description", ""))
            for name, mat_def in sorted(MATERIAL_DEFS.items())
        ],
    )

    def execute(self, context):
        if self.material_name not in bpy.data.materials:
            # Create the material if it doesn't exist yet
            if self.material_name in MATERIAL_DEFS:
                create_material(self.material_name, MATERIAL_DEFS[self.material_name])
            else:
                self.report({'ERROR'}, f"Unknown material: {self.material_name}")
                return {'CANCELLED'}

        apply_material_to_selected(self.material_name)
        self.report({'INFO'}, f"Applied '{self.material_name}' to selected objects")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_apply_golf_material.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_apply_golf_material)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_apply_golf_material)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


# ---------------------------------------------------------------------------
# Main — when run directly from Blender's text editor
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    register()
    materials = create_all_materials()
    list_materials()
    print("\nUsage:")
    print("  1. Select objects in viewport")
    print("  2. Run: apply_material_to_selected('Fairway')")
    print("  3. Or use: apply_material_by_feature_type('bunker')")
    print("  4. Or use: Object menu > Apply Golf Material")

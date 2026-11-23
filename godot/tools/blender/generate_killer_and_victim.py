"""
Generador procedural en Blender para los personajes de la cinemática:
1. El Asesino (killer.glb): figura adulta estilizada y amenazante, rostro
   prácticamente cubierto por una capucha y máscara de tela oscura con ojos
   hundidos, chaqueta elegante de cuero negro con solapas y manchas reales de
   sangre, pantalones oscuros de vestir combinados, botas y un trapo arrugado
   con somnífero en la mano.
2. El Protagonista (victim_adult.glb): adulto vestido solo con camisa ligera.

Exporta .glb optimizados para Android (Godot 4.7.2) y renderiza PNG en artifacts.
"""

import math
import os
import random
import bpy
import bmesh
from mathutils import Vector


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def clamp_val(v, lo, hi):
    return max(lo, min(hi, v))


def make_pbr_material(name, base_color, roughness=0.5, metallic=0.0, emission=(0.0, 0.0, 0.0), emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*emission, 1.0)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_leather_blood_material(name):
    """Cuero negro elegante (satinado) con salpicaduras y escurrimientos de sangre embebidos."""
    rng = random.Random(42)
    size = 512
    img = bpy.data.images.new(name=f"{name}_Tex", width=size, height=size, alpha=False)
    pixels = [0.0] * (size * size * 4)

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            grain = (rng.random() - 0.5) * 0.012
            pixels[idx] = max(0.0, 0.025 + grain)
            pixels[idx + 1] = max(0.0, 0.022 + grain)
            pixels[idx + 2] = max(0.0, 0.028 + grain)
            pixels[idx + 3] = 1.0

    # Manchas y escurrimientos de sangre visibles en frente, solapas y mangas
    splats = [
        (64, 64, 48), (190, 90, 52), (320, 75, 44), (440, 110, 50),
        (110, 220, 58), (256, 256, 70), (390, 240, 56), (80, 390, 48),
        (220, 410, 56), (360, 385, 62), (450, 430, 46), (150, 140, 38),
    ]
    for cx, cy, rad in splats:
        for y in range(max(0, cy - rad), min(size, cy + rad)):
            for x in range(max(0, cx - rad), min(size, cx + rad)):
                dx = (x - cx) / float(rad)
                dy = (y - cy) / float(rad)
                dist = math.sqrt(dx * dx + dy * dy) + rng.uniform(-0.25, 0.25)
                if dist < 0.88:
                    idx = (y * size + x) * 4
                    blend = clamp_val(1.0 - dist / 0.88, 0.0, 1.0)
                    pixels[idx] = pixels[idx] * (1.0 - blend) + 0.45 * blend
                    pixels[idx + 1] = pixels[idx + 1] * (1.0 - blend) + 0.012 * blend
                    pixels[idx + 2] = pixels[idx + 2] * (1.0 - blend) + 0.015 * blend
        for dy in range(1, int(rad * 1.4)):
            yy = cy - dy
            if 0 <= yy < size:
                for dx in range(-3, 4):
                    xx = cx + dx
                    if 0 <= xx < size:
                        idx = (yy * size + xx) * 4
                        pixels[idx] = 0.36
                        pixels[idx + 1] = 0.010
                        pixels[idx + 2] = 0.012

    img.pixels = pixels
    img.pack()

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.24
    bsdf.inputs["Metallic"].default_value = 0.08

    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = img
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def create_box(name, location, scale, material, rotation=(0, 0, 0), bevel=0.012, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new(name="Bevel", type="BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def create_cylinder(name, location, radius, depth, material, rotation=(0, 0, 0), vertices=16, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def create_sphere(name, location, scale, material, segments=18, rings=14, rotation=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=0.5, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def create_crumpled_rag(name, location, material, parent=None):
    """Genera un trapo arrugado irregular (no una esfera lisa) para el somnífero."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.068, location=location)
    obj = bpy.context.active_object
    obj.name = name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    rng = random.Random(99)
    for v in bm.verts:
        v.co.x *= 1.35 + rng.uniform(-0.28, 0.28)
        v.co.y *= 0.85 + rng.uniform(-0.25, 0.25)
        v.co.z *= 1.15 + rng.uniform(-0.30, 0.30)
    bm.to_mesh(obj.data)
    bm.free()
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def build_killer_asset(output_glb):
    clear_scene()

    mat_leather_blood = make_leather_blood_material("Mat_KillerLeatherBlood")
    mat_trousers = make_pbr_material("Mat_KillerTrousers", (0.042, 0.038, 0.046), roughness=0.66, metallic=0.04)
    mat_boots = make_pbr_material("Mat_KillerBoots", (0.018, 0.018, 0.022), roughness=0.22, metallic=0.12)
    mat_hood_mask = make_pbr_material("Mat_KillerMask", (0.022, 0.020, 0.025), roughness=0.84)
    mat_shirt_inner = make_pbr_material("Mat_KillerInnerShirt", (0.11, 0.022, 0.026), roughness=0.74)
    mat_gloves = make_pbr_material("Mat_KillerGloves", (0.02, 0.018, 0.022), roughness=0.28, metallic=0.08)
    mat_rag = make_pbr_material("Mat_ChloroformRag", (0.64, 0.61, 0.54), roughness=0.92)
    mat_eye_shadow = make_pbr_material("Mat_EyeVoid", (0.004, 0.004, 0.005), roughness=0.95)
    mat_eye_glint = make_pbr_material("Mat_EyeGlint", (0.62, 0.66, 0.72), roughness=0.15, emission=(0.45, 0.48, 0.54), emission_strength=0.65)
    mat_metal_buckle = make_pbr_material("Mat_Buckle", (0.38, 0.40, 0.44), roughness=0.22, metallic=0.90)

    root = bpy.data.objects.new("KillerRoot", None)
    bpy.context.collection.objects.link(root)

    # Piernas largas con pantalón oscuro elegante combinado + botas lustradas
    for side, sx in [("L", -0.115), ("R", 0.115)]:
        create_cylinder(f"Killer_Boot_{side}", (sx, 0.0, 0.14), 0.066, 0.28, mat_boots, parent=root)
        create_box(f"Killer_BootFoot_{side}", (sx, -0.05, 0.04), (0.105, 0.23, 0.08), mat_boots, bevel=0.016, parent=root)
        create_cylinder(f"Killer_TrouserShin_{side}", (sx, 0.0, 0.43), 0.070, 0.36, mat_trousers, parent=root)
        create_cylinder(f"Killer_TrouserThigh_{side}", (sx, 0.0, 0.75), 0.085, 0.38, mat_trousers, parent=root)

    # Pelvis y cinturón elegante
    create_box("Killer_Pelvis", (0.0, 0.0, 0.94), (0.35, 0.20, 0.15), mat_trousers, bevel=0.022, parent=root)
    create_box("Killer_Belt", (0.0, 0.0, 0.99), (0.37, 0.215, 0.042), mat_boots, bevel=0.008, parent=root)
    create_box("Killer_BeltBuckle", (0.0, -0.112, 0.99), (0.060, 0.016, 0.048), mat_metal_buckle, bevel=0.004, parent=root)

    # Chaqueta de cuero elegante ensangrentada (envuelve completamente el torso)
    create_box("Killer_JacketTorso", (0.0, 0.0, 1.22), (0.43, 0.245, 0.50), mat_leather_blood, bevel=0.030, parent=root)
    create_box("Killer_JacketHem", (0.0, 0.006, 0.96), (0.44, 0.25, 0.14), mat_leather_blood, bevel=0.024, parent=root)
    # Pequeña abertura en V superior dejando ver camisa oscura
    create_box("Killer_InnerCollarV", (0.0, -0.112, 1.38), (0.11, 0.028, 0.18), mat_shirt_inner, bevel=0.008, parent=root)
    # Solapas elegantes de cuero con sangre
    create_box("Killer_Lapel_L", (-0.082, -0.125, 1.33), (0.075, 0.024, 0.24), mat_leather_blood, rotation=(0.05, 0.0, 0.25), bevel=0.008, parent=root)
    create_box("Killer_Lapel_R", (0.082, -0.125, 1.33), (0.075, 0.024, 0.24), mat_leather_blood, rotation=(0.05, 0.0, -0.25), bevel=0.008, parent=root)
    # Botones metálicos en fila vertical
    for idx, bz in enumerate([1.07, 1.15, 1.23]):
        create_cylinder(f"Killer_Button_{idx}", (0.02, -0.128, bz), 0.011, 0.012, mat_metal_buckle, rotation=(math.radians(90), 0, 0), parent=root)

    # Hombros estructurados
    create_sphere("Killer_Shoulder_L", (-0.23, 0.0, 1.43), (0.16, 0.18, 0.15), mat_leather_blood, parent=root)
    create_sphere("Killer_Shoulder_R", (0.23, 0.0, 1.43), (0.16, 0.18, 0.15), mat_leather_blood, parent=root)

    # Brazo izquierdo abajo con guante
    create_cylinder("Killer_UpperArm_L", (-0.26, 0.0, 1.27), 0.060, 0.30, mat_leather_blood, rotation=(0, -0.08, 0), parent=root)
    create_cylinder("Killer_Forearm_L", (-0.28, -0.04, 1.02), 0.052, 0.28, mat_leather_blood, rotation=(0.24, -0.05, 0), parent=root)
    create_sphere("Killer_Hand_L", (-0.29, -0.08, 0.87), (0.072, 0.092, 0.115), mat_gloves, parent=root)

    # Brazo derecho extendido sosteniendo el trapo arrugado con somnífero
    create_cylinder("Killer_UpperArm_R", (0.26, -0.05, 1.29), 0.060, 0.30, mat_leather_blood, rotation=(0.38, 0.08, 0), parent=root)
    create_cylinder("Killer_Forearm_R", (0.24, -0.24, 1.18), 0.052, 0.29, mat_leather_blood, rotation=(1.15, 0.0, -0.15), parent=root)
    create_sphere("Killer_Hand_R", (0.20, -0.37, 1.16), (0.078, 0.095, 0.105), mat_gloves, parent=root)
    create_crumpled_rag("Killer_ChloroformRag", (0.17, -0.43, 1.15), mat_rag, parent=root)

    # Cuello cubierto + rostro tapado con máscara oscura + capucha profunda estilizada (sin cajas flotantes)
    create_cylinder("Killer_NeckWrap", (0.0, 0.0, 1.52), 0.072, 0.14, mat_hood_mask, parent=root)
    create_sphere("Killer_MaskedHead", (0.0, -0.015, 1.66), (0.20, 0.22, 0.26), mat_hood_mask, parent=root)
    # Capucha de cuero envolvente hacia atrás y arriba
    create_sphere("Killer_HoodWrap", (0.0, 0.025, 1.69), (0.25, 0.27, 0.31), mat_leather_blood, rotation=(0.22, 0, 0), parent=root)
    create_sphere("Killer_HoodPeak", (0.0, -0.035, 1.77), (0.22, 0.21, 0.14), mat_leather_blood, rotation=(0.35, 0, 0), parent=root)
    # Bufanda/paño cubriendo nariz y boca (prácticamente todo tapado)
    create_cylinder("Killer_FaceMaskLower", (0.0, -0.025, 1.60), 0.108, 0.11, mat_hood_mask, parent=root)

    # Cuencas oscuras profundas y leve destello en los ojos bajo la sombra de la capucha
    for side, ex in [("L", -0.040), ("R", 0.040)]:
        create_sphere(f"Killer_EyeSocket_{side}", (ex, -0.110, 1.68), (0.042, 0.025, 0.024), mat_eye_shadow, parent=root)
        create_sphere(f"Killer_EyeGlint_{side}", (ex, -0.118, 1.68), (0.013, 0.010, 0.011), mat_eye_glint, parent=root)

    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=output_glb, export_format="GLB", export_apply=True)

    render_preview(
        "/app/applet/.aistudio/artifacts/killer_preview.png",
        cam_loc=(0.88, -2.15, 1.42),
        target_loc=(0.0, 0.0, 1.12),
        key_loc=(-1.35, -1.85, 2.2),
        rim_loc=(1.1, 1.5, 2.0),
    )


def build_victim_adult_asset(output_glb):
    clear_scene()
    mat_skin = make_pbr_material("Mat_Skin", (0.58, 0.45, 0.38), roughness=0.65)
    mat_shirt = make_pbr_material("Mat_ThinShirt", (0.62, 0.64, 0.68), roughness=0.85)
    mat_pants = make_pbr_material("Mat_SleepPants", (0.14, 0.16, 0.21), roughness=0.82)
    mat_hair = make_pbr_material("Mat_Hair", (0.09, 0.07, 0.05), roughness=0.75)

    root = bpy.data.objects.new("VictimRoot", None)
    bpy.context.collection.objects.link(root)

    for side, sx in [("L", -0.105), ("R", 0.105)]:
        create_cylinder(f"Victim_LegLower_{side}", (sx, 0, 0.26), 0.055, 0.44, mat_pants, parent=root)
        create_cylinder(f"Victim_LegUpper_{side}", (sx, 0, 0.66), 0.074, 0.42, mat_pants, parent=root)
    create_box("Victim_Pelvis", (0, 0, 0.91), (0.32, 0.19, 0.14), mat_pants, bevel=0.02, parent=root)
    create_box("Victim_ThinShirtTorso", (0, 0, 1.19), (0.35, 0.20, 0.46), mat_shirt, bevel=0.02, parent=root)
    for side, ax in [("L", -0.22), ("R", 0.22)]:
        create_cylinder(f"Victim_ShirtSleeve_{side}", (ax, 0, 1.33), 0.056, 0.16, mat_shirt, parent=root)
        create_cylinder(f"Victim_BareArm_{side}", (ax, 0, 1.07), 0.044, 0.38, mat_skin, parent=root)
    create_cylinder("Victim_Neck", (0, 0, 1.46), 0.052, 0.10, mat_skin, parent=root)
    create_sphere("Victim_Head", (0, 0, 1.59), (0.19, 0.22, 0.24), mat_skin, parent=root)
    create_sphere("Victim_Hair", (0, 0.02, 1.63), (0.20, 0.23, 0.21), mat_hair, parent=root)

    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=output_glb, export_format="GLB", export_apply=True)


def render_preview(out_png, cam_loc, target_loc, key_loc, rim_loc):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = False
    scene.cycles.samples = 48
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_png

    world = bpy.data.worlds.new("HorrorPreviewWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.015, 0.018, 0.026, 1.0)
        bg.inputs["Strength"].default_value = 0.6

    key_data = bpy.data.lights.new(name="KeyLight", type="AREA")
    key_data.energy = 115.0
    key_data.color = (0.72, 0.80, 0.95)
    key_data.size = 1.4
    key_obj = bpy.data.objects.new(name="KeyLight", object_data=key_data)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = key_loc
    direction = Vector(target_loc) - Vector(key_loc)
    key_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    rim_data = bpy.data.lights.new(name="RimLight", type="POINT")
    rim_data.energy = 70.0
    rim_data.color = (0.85, 0.18, 0.16)
    rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = rim_loc

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = cam_loc
    cam_dir = Vector(target_loc) - Vector(cam_loc)
    cam_obj.rotation_euler = cam_dir.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build_killer_asset("/app/applet/godot/assets/models/characters/killer.glb")
    build_victim_adult_asset("/app/applet/godot/assets/models/characters/victim_adult.glb")
    print("Personajes refinados y exportados correctamente.")

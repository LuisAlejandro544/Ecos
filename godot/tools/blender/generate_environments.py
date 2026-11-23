"""
Generador procedural en Blender para la cabaña del protagonista en el bosque (cabin_intro.glb)
y la casa tenebrosa completa del asesino (killer_house.glb) con colisiones automáticas
(-colonly) para Godot 4.7.2, cama llena de sangre, sangre en paredes, mesa de noche
ensangrentada y habitaciones interconectadas caminables.

Además genera renders PNG en .aistudio/artifacts/ para verificar visualmente los modelos.
"""

import math
import os
import bpy
from mathutils import Vector


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_pbr(name, color, roughness=0.8, metallic=0.0, emission=(0, 0, 0), emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*emission, 1.0)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_blood_stained_material(name, base_col, blood_col=(0.24, 0.01, 0.012), scale=3.2, threshold=0.53):
    """Genera textura PNG empaquetada con suciedad y manchas de sangre compatible al 100% con .glb."""
    import random
    rng = random.Random(hash(name) & 0xFFFF)
    size = 256
    img = bpy.data.images.new(name=f"{name}_Tex", width=size, height=size, alpha=False)
    pixels = [0.0] * (size * size * 4)

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            grime = (rng.random() - 0.5) * 0.03
            pixels[idx] = max(0.0, min(1.0, base_col[0] + grime))
            pixels[idx + 1] = max(0.0, min(1.0, base_col[1] + grime))
            pixels[idx + 2] = max(0.0, min(1.0, base_col[2] + grime))
            pixels[idx + 3] = 1.0

    num_splats = int((1.0 - threshold) * 28) + 6
    for _ in range(num_splats):
        cx = rng.randint(15, size - 15)
        cy = rng.randint(15, size - 15)
        rad = rng.randint(14, 42)
        for y in range(max(0, cy - rad), min(size, cy + rad)):
            for x in range(max(0, cx - rad), min(size, cx + rad)):
                dx = (x - cx) / float(rad)
                dy = (y - cy) / float(rad)
                dist = math.sqrt(dx * dx + dy * dy) + rng.uniform(-0.22, 0.22)
                if dist < 0.88:
                    idx = (y * size + x) * 4
                    blend = max(0.0, min(1.0, 1.0 - dist / 0.88))
                    pixels[idx] = pixels[idx] * (1.0 - blend) + blood_col[0] * blend
                    pixels[idx + 1] = pixels[idx + 1] * (1.0 - blend) + blood_col[1] * blend
                    pixels[idx + 2] = pixels[idx + 2] * (1.0 - blend) + blood_col[2] * blend

    img.pixels = pixels
    img.pack()

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.78

    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = img
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def add_box(name, loc, size, mat=None, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def add_wall_with_col(name, loc, size, mat, rot=(0, 0, 0), parent=None):
    """Crea un muro visual y un collider invisible -colonly que Godot 4 convierte en StaticBody3D."""
    vis = add_box(name, loc, size, mat, rot=rot, parent=parent)
    add_box(f"{name}-colonly", loc, size, None, rot=rot, parent=parent)
    return vis


def make_organic_blood_decal_material(name, seed=77):
    """Genera textura RGBA transparente con salpicaduras y escurrimientos reales de sangre."""
    import random
    rng = random.Random(seed)
    size = 256
    img = bpy.data.images.new(name=f"{name}_Tex", width=size, height=size, alpha=True)
    pixels = [0.0] * (size * size * 4)

    # Salpicaduras irregulares principales + gotas
    blobs = [
        (128, 148, 52), (88, 125, 34), (165, 118, 30),
        (115, 86, 26), (146, 175, 24), (72, 165, 16), (185, 155, 18),
    ]
    for cx, cy, rad in blobs:
        for y in range(max(0, cy - rad), min(size, cy + rad)):
            for x in range(max(0, cx - rad), min(size, cx + rad)):
                dx = (x - cx) / float(rad)
                dy = (y - cy) / float(rad)
                d = math.sqrt(dx * dx + dy * dy) + rng.uniform(-0.28, 0.25)
                if d < 0.85:
                    idx = (y * size + x) * 4
                    a = max(0.0, min(0.95, (1.0 - d / 0.85) * 1.4))
                    pixels[idx] = 0.26 + rng.uniform(-0.04, 0.08)
                    pixels[idx + 1] = 0.008
                    pixels[idx + 2] = 0.010
                    pixels[idx + 3] = max(pixels[idx + 3], a)

    # Escurrimientos verticales hacia abajo
    for dx_center, start_y, length, half_w in [(95, 140, 95, 3), (128, 155, 115, 4), (162, 125, 85, 3), (112, 100, 65, 2)]:
        for dy in range(length):
            yy = start_y - dy
            if 0 <= yy < size:
                fade = 1.0 - (dy / float(length)) * 0.45
                for dx in range(-half_w, half_w + 1):
                    xx = dx_center + dx
                    if 0 <= xx < size:
                        idx = (yy * size + xx) * 4
                        pixels[idx] = 0.22
                        pixels[idx + 1] = 0.006
                        pixels[idx + 2] = 0.008
                        pixels[idx + 3] = max(pixels[idx + 3], 0.88 * fade)

    img.pixels = pixels
    img.pack()

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.18

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    return mat


def add_blood_splat(name, loc, size, mat_blood, rot=(0, 0, 0), parent=None):
    """Plano con salpicadura orgánica transparente sobre paredes, cama o mesa de noche."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0], size[1], 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat_blood:
        obj.data.materials.append(mat_blood)
    if parent:
        obj.parent = parent
    return obj


def build_cabin_intro(output_glb):
    """Construye la cabaña del usuario en el bosque para la cinemática de secuestro."""
    clear_scene()
    mat_wood_wall = make_pbr("Mat_CabinTimber", (0.14, 0.09, 0.06), roughness=0.88)
    mat_wood_floor = make_pbr("Mat_CabinFloor", (0.10, 0.065, 0.042), roughness=0.82)
    mat_bed_wood = make_pbr("Mat_BedWood", (0.09, 0.055, 0.035), roughness=0.75)
    mat_sheets = make_pbr("Mat_CabinSheets", (0.25, 0.27, 0.31), roughness=0.92)
    mat_pillow = make_pbr("Mat_Pillow", (0.55, 0.56, 0.58), roughness=0.9)
    mat_pine_dark = make_pbr("Mat_ForestPine", (0.025, 0.038, 0.025), roughness=0.95)
    mat_trunk = make_pbr("Mat_TreeTrunk", (0.05, 0.035, 0.025), roughness=0.92)

    root = bpy.data.objects.new("CabinIntroRoot", None)
    bpy.context.collection.objects.link(root)

    # Piso y techo de la cabaña (5m x 5m)
    add_box("Cabin_Floor", (0, 0, -0.05), (5.2, 5.2, 0.1), mat_wood_floor, parent=root)
    add_box("Cabin_Ceiling", (0, 0, 2.95), (5.2, 5.2, 0.12), mat_wood_wall, parent=root)

    # Paredes (ventana abierta en la pared Norte Y=+2.5 por donde entra el asesino)
    add_box("Cabin_Wall_South", (0, -2.55, 1.45), (5.2, 0.15, 2.9), mat_wood_wall, parent=root)
    add_box("Cabin_Wall_West", (-2.55, 0, 1.45), (0.15, 5.2, 2.9), mat_wood_wall, parent=root)
    add_box("Cabin_Wall_East", (2.55, 0, 1.45), (0.15, 5.2, 2.9), mat_wood_wall, parent=root)
    add_box("Cabin_Wall_North_L", (-1.6, 2.55, 1.45), (2.0, 0.15, 2.9), mat_wood_wall, parent=root)
    add_box("Cabin_Wall_North_R", (1.6, 2.55, 1.45), (2.0, 0.15, 2.9), mat_wood_wall, parent=root)
    add_box("Cabin_Wall_North_Bot", (0, 2.55, 0.42), (1.2, 0.15, 0.85), mat_wood_wall, parent=root)
    add_box("Cabin_Wall_North_Top", (0, 2.55, 2.55), (1.2, 0.15, 0.7), mat_wood_wall, parent=root)
    add_box("Cabin_WindowFrame_L", (-0.62, 2.55, 1.52), (0.07, 0.18, 1.38), mat_bed_wood, parent=root)
    add_box("Cabin_WindowFrame_R", (0.62, 2.55, 1.52), (0.07, 0.18, 1.38), mat_bed_wood, parent=root)
    add_box("Cabin_WindowSill", (0, 2.52, 0.85), (1.32, 0.24, 0.06), mat_bed_wood, parent=root)

    # Cama del protagonista en la esquina izquierda
    add_box("Cabin_BedFrame", (-1.35, -0.6, 0.24), (1.2, 2.1, 0.35), mat_bed_wood, parent=root)
    add_box("Cabin_BedMattress", (-1.35, -0.6, 0.48), (1.12, 1.98, 0.18), mat_sheets, parent=root)
    add_box("Cabin_BedPillow", (-1.35, -1.35, 0.62), (0.68, 0.34, 0.12), mat_pillow, parent=root)
    add_box("Cabin_Nightstand", (-0.42, -1.35, 0.30), (0.48, 0.45, 0.60), mat_bed_wood, parent=root)

    tree_positions = [(-1.8, 5.2), (0.2, 6.4), (1.9, 5.0), (-0.7, 8.0), (1.2, 7.6)]
    for i, (tx, ty) in enumerate(tree_positions):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.18, depth=4.5, location=(tx, ty, 2.2))
        tr = bpy.context.active_object
        tr.name = f"Forest_Trunk_{i}"
        tr.data.materials.append(mat_trunk)
        tr.parent = root
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.95, radius2=0.0, depth=2.8, location=(tx, ty, 3.6))
        cn = bpy.context.active_object
        cn.name = f"Forest_Canopy_{i}"
        cn.data.materials.append(mat_pine_dark)
        cn.parent = root

    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=output_glb, export_format="GLB", export_apply=True)

    render_house_preview(
        "/app/applet/.aistudio/artifacts/cabin_intro_preview.png",
        cam_loc=(1.75, -1.9, 1.55),
        target_loc=(-0.55, 0.6, 1.05),
        lights=[((-0.2, 3.8, 2.1), (0.55, 0.68, 0.92), 180.0), ((-1.1, -0.8, 1.8), (0.75, 0.62, 0.45), 35.0)],
    )


def build_killer_house(output_glb):
    """
    Construye la casa del asesino con paredes desgastadas, sangre orgánica en paredes,
    cama ensangrentada, mesa de noche ensangrentada con carta del asesino y pasillo/sala.
    """
    clear_scene()

    mat_wall_blood = make_blood_stained_material("Mat_WallGrimeBlood", (0.22, 0.20, 0.18), (0.28, 0.012, 0.014), scale=2.2, threshold=0.60)
    mat_wall_dark = make_pbr("Mat_WallDecayed", (0.18, 0.17, 0.16), roughness=0.90)
    mat_floor_wood = make_blood_stained_material("Mat_HouseFloor", (0.15, 0.10, 0.072), (0.22, 0.012, 0.012), scale=2.8, threshold=0.62)
    mat_ceiling = make_pbr("Mat_CeilingDark", (0.09, 0.085, 0.08), roughness=0.95)
    mat_iron = make_pbr("Mat_RustedIron", (0.11, 0.085, 0.075), roughness=0.52, metallic=0.65)
    mat_blood_mattress = make_blood_stained_material("Mat_BloodMattress", (0.36, 0.31, 0.27), (0.36, 0.010, 0.012), scale=3.6, threshold=0.45)
    mat_blood_decal = make_organic_blood_decal_material("Mat_OrganicBloodDecal", seed=77)
    mat_blood_decal2 = make_organic_blood_decal_material("Mat_OrganicBloodDecal2", seed=123)
    mat_nightstand = make_blood_stained_material("Mat_BloodNightstand", (0.16, 0.095, 0.06), (0.30, 0.012, 0.014), scale=4.5, threshold=0.50)
    mat_letter_paper = make_pbr("Mat_KillerLetterPaper", (0.78, 0.70, 0.56), roughness=0.85, emission=(0.18, 0.14, 0.09), emission_strength=0.18)
    mat_wood_prop = make_pbr("Mat_DarkWoodProp", (0.16, 0.10, 0.065), roughness=0.80)
    mat_lamp_glow = make_pbr("Mat_LampBulb", (0.95, 0.65, 0.35), roughness=0.2, emission=(0.95, 0.55, 0.24), emission_strength=3.5)

    root = bpy.data.objects.new("KillerHouseRoot", None)
    bpy.context.collection.objects.link(root)

    add_wall_with_col("House_Floor", (0.0, 1.75, -0.05), (9.4, 12.0, 0.1), mat_floor_wood, parent=root)
    add_box("House_Ceiling", (0.0, 1.75, 3.05), (9.4, 12.0, 0.12), mat_ceiling, parent=root)

    add_wall_with_col("Wall_Ext_South", (0.0, -4.1, 1.5), (9.4, 0.2, 3.0), mat_wall_blood, parent=root)
    add_wall_with_col("Wall_Ext_North", (0.0, 7.6, 1.5), (9.4, 0.2, 3.0), mat_wall_dark, parent=root)
    add_wall_with_col("Wall_Ext_West", (-4.6, 1.75, 1.5), (0.2, 12.0, 3.0), mat_wall_blood, parent=root)
    add_wall_with_col("Wall_Ext_East", (4.6, 1.75, 1.5), (0.2, 12.0, 3.0), mat_wall_dark, parent=root)

    add_wall_with_col("Wall_Bedroom_Div_L", (-1.85, 0.8, 1.5), (5.5, 0.18, 3.0), mat_wall_blood, parent=root)
    add_wall_with_col("Wall_Bedroom_Div_R", (3.35, 0.8, 1.5), (2.5, 0.18, 3.0), mat_wall_dark, parent=root)
    add_box("Wall_Bedroom_DoorHeader", (1.5, 0.8, 2.55), (1.25, 0.18, 0.9), mat_wall_dark, parent=root)
    add_wall_with_col("Bedroom_DoorLeaf", (0.95, 1.32, 1.05), (0.06, 1.05, 2.1), mat_wood_prop, rot=(0, 0, -0.35), parent=root)

    # Cama llena de sangre
    add_wall_with_col("BloodBed_Frame", (-2.4, -2.4, 0.26), (1.45, 2.25, 0.34), mat_iron, parent=root)
    add_box("BloodBed_Headboard", (-2.4, -3.48, 0.65), (1.45, 0.08, 1.05), mat_iron, parent=root)
    add_box("BloodBed_Mattress", (-2.4, -2.4, 0.50), (1.36, 2.12, 0.20), mat_blood_mattress, parent=root)
    add_box("BloodBed_Pillow", (-2.4, -3.15, 0.65), (0.85, 0.38, 0.13), mat_blood_mattress, parent=root)
    add_blood_splat("BloodBed_Pool", (-2.35, -2.25, 0.605), (1.15, 1.45, 1.0), mat_blood_decal, parent=root)

    # Mesa de noche ensangrentada + lámpara + Carta del Asesino
    add_wall_with_col("Nightstand_Body", (-1.18, -3.15, 0.34), (0.58, 0.52, 0.68), mat_nightstand, parent=root)
    add_blood_splat("Nightstand_BloodTop", (-1.15, -3.14, 0.686), (0.48, 0.44, 1.0), mat_blood_decal2, parent=root)
    add_box("Nightstand_LampBase", (-1.30, -3.26, 0.74), (0.14, 0.14, 0.12), mat_iron, parent=root)
    add_box("Nightstand_LampBulb", (-1.30, -3.26, 0.84), (0.07, 0.07, 0.08), mat_lamp_glow, parent=root)
    add_box("Killer_Letter_Mesh", (-1.06, -3.04, 0.694), (0.22, 0.28, 0.008), mat_letter_paper, rot=(0, 0, 0.18), parent=root)
    add_blood_splat("Killer_Letter_BloodCorner", (-1.02, -2.99, 0.700), (0.14, 0.14, 1.0), mat_blood_decal, parent=root)

    # Salpicaduras orgánicas de sangre en las paredes (rotadas verticalmente contra la pared)
    add_blood_splat("BloodWall_South_1", (-2.35, -3.98, 1.45), (1.65, 1.45, 1.0), mat_blood_decal, rot=(-math.radians(90), 0, 0), parent=root)
    add_blood_splat("BloodWall_South_2", (-1.05, -3.98, 1.15), (1.05, 1.15, 1.0), mat_blood_decal2, rot=(-math.radians(90), 0, 0), parent=root)
    add_blood_splat("BloodWall_West_1", (-4.48, -2.05, 1.45), (1.75, 1.45, 1.0), mat_blood_decal, rot=(-math.radians(90), 0, -math.radians(90)), parent=root)
    add_blood_splat("BloodWall_West_Streak", (-4.48, 2.5, 1.25), (1.5, 1.2, 1.0), mat_blood_decal2, rot=(-math.radians(90), 0, -math.radians(90)), parent=root)
    add_blood_splat("BloodFloor_Trail", (-1.6, -0.5, 0.006), (1.2, 1.6, 1.0), mat_blood_decal, rot=(0, 0, 0.2), parent=root)

    # Sala principal (Norte) y puerta sellada
    add_wall_with_col("Living_Table", (-1.8, 4.5, 0.42), (1.8, 0.95, 0.84), mat_wood_prop, parent=root)
    add_blood_splat("Living_TableBlood", (-1.7, 4.5, 0.846), (1.1, 0.75, 1.0), mat_blood_decal2, parent=root)
    add_wall_with_col("Living_FallenChair", (0.2, 3.8, 0.24), (0.55, 0.55, 0.48), mat_wood_prop, rot=(1.35, 0.2, 0.4), parent=root)
    add_wall_with_col("Living_Shelf", (3.95, 4.8, 1.0), (0.65, 1.8, 2.0), mat_wood_prop, parent=root)
    add_wall_with_col("ExitDoor_Frame", (0.2, 7.45, 1.15), (1.25, 0.14, 2.3), mat_wood_prop, parent=root)
    add_box("ExitDoor_Plank1", (0.2, 7.36, 1.35), (1.45, 0.06, 0.16), mat_nightstand, rot=(0, 0.18, 0), parent=root)
    add_box("ExitDoor_Plank2", (0.2, 7.36, 0.85), (1.45, 0.06, 0.16), mat_nightstand, rot=(0, -0.14, 0), parent=root)

    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=output_glb, export_format="GLB", export_apply=True)

    render_house_preview(
        "/app/applet/.aistudio/artifacts/killer_house_preview.png",
        cam_loc=(1.95, 0.15, 1.88),
        target_loc=(-2.05, -2.65, 0.82),
        lights=[((-1.3, -3.1, 1.45), (0.95, 0.54, 0.28), 140.0), ((0.6, -0.4, 2.45), (0.48, 0.58, 0.82), 95.0)],
    )


def render_house_preview(out_png, cam_loc, target_loc, lights):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = False
    scene.cycles.samples = 48
    scene.render.resolution_x = 896
    scene.render.resolution_y = 640
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_png

    world = bpy.data.worlds.new("HousePreviewWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.01, 0.012, 0.018, 1.0)
        bg.inputs["Strength"].default_value = 0.4

    for idx, (loc, col, energy) in enumerate(lights):
        ld = bpy.data.lights.new(name=f"HouseLight_{idx}", type="POINT")
        ld.energy = energy
        ld.color = col
        lo = bpy.data.objects.new(name=f"HouseLight_{idx}", object_data=ld)
        bpy.context.collection.objects.link(lo)
        lo.location = loc

    cam_data = bpy.data.cameras.new("HousePreviewCam")
    cam_data.lens = 24.0
    cam_obj = bpy.data.objects.new("HousePreviewCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = cam_loc
    cam_dir = Vector(target_loc) - Vector(cam_loc)
    cam_obj.rotation_euler = cam_dir.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build_cabin_intro("/app/applet/godot/assets/models/environments/cabin_intro.glb")
    build_killer_house("/app/applet/godot/assets/models/environments/killer_house.glb")
    print("Cabaña y casa del asesino exportadas a .glb y renderizadas a PNG.")

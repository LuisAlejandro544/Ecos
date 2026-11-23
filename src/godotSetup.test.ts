import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

/**
 * Suite de pruebas unitarias para verificar la integridad estructural del proyecto
 * Godot 4.7.2 móvil de terror, sus assets 3D .glb generados con Blender,
 * el fallback Vulkan 1.1 -> OpenGL ES 3.0 y las escenas/pantallas modulares.
 */
const godotRoot = path.resolve(process.cwd(), 'godot');

test('project.godot usa Godot 4.7, Vulkan mobile con respaldo OpenGL ES 3.0 y escena principal válida', () => {
  const projectGodotPath = path.join(godotRoot, 'project.godot');
  assert.equal(fs.existsSync(projectGodotPath), true, 'Debe existir godot/project.godot');

  const content = fs.readFileSync(projectGodotPath, 'utf8');
  assert.match(content, /config_version=5/);
  assert.match(content, /config\/features=PackedStringArray\("4\.7", "Mobile"\)/);
  assert.match(content, /renderer\/rendering_method="mobile"/);
  assert.match(content, /renderer\/rendering_method\.mobile="mobile"/);
  assert.match(content, /rendering_device\/fallback_to_opengl3=true/);
  assert.match(content, /run\/main_scene="res:\/\/scenes\/ui\/main_menu\.tscn"/);
  assert.match(content, /GameState="\*res:\/\/scripts\/core\/game_state\.gd"/);
  assert.match(content, /AudioDirector="\*res:\/\/scripts\/audio\/audio_director\.gd"/);
  assert.match(content, /AtmosphereDirector="\*res:\/\/scripts\/atmosphere\/atmosphere_director\.gd"/);
});

test('export_presets.cfg configura APK (no AAB) con soporte ARM 32 y 64 bits', () => {
  const exportPresetsPath = path.join(godotRoot, 'export_presets.cfg');
  assert.equal(fs.existsSync(exportPresetsPath), true, 'Debe existir godot/export_presets.cfg');

  const content = fs.readFileSync(exportPresetsPath, 'utf8');
  assert.match(content, /platform="Android"/);
  assert.match(content, /gradle_build\/export_format=0/);
  assert.match(content, /architectures\/armeabi-v7a=true/);
  assert.match(content, /architectures\/arm64-v8a=true/);
  assert.match(content, /\.apk"/);
});

test('todos los recursos, escenas, scripts modulares y modelos .glb de Blender existen', () => {
  const requiredFiles = [
    'assets/branding/icon.svg',
    'assets/models/characters/killer.glb',
    'assets/models/characters/victim_adult.glb',
    'assets/models/environments/cabin_intro.glb',
    'assets/models/environments/killer_house.glb',
    'tools/blender/generate_killer_and_victim.py',
    'tools/blender/generate_environments.py',
    'resources/environments/abyss_horror_env.tres',
    'resources/audio/horror_bus_layout.tres',
    'scenes/ui/main_menu.tscn',
    'scenes/ui/options_screen.tscn',
    'scenes/ui/controls_screen.tscn',
    'scenes/ui/mobile_hud.tscn',
    'scenes/cutscenes/abduction_cutscene.tscn',
    'scenes/levels/killer_house_level.tscn',
    'scripts/core/game_state.gd',
    'scripts/audio/audio_director.gd',
    'scripts/atmosphere/atmosphere_director.gd',
    'scripts/player/first_person_controller.gd',
    'scripts/cutscenes/abduction_cutscene.gd',
    'scripts/levels/killer_house_level.gd',
    'scripts/ui/main_menu.gd',
    'scripts/ui/options_screen.gd',
    'scripts/ui/controls_screen.gd',
    'scripts/ui/mobile_hud.gd',
  ];

  for (const relPath of requiredFiles) {
    const fullPath = path.join(godotRoot, relPath);
    assert.equal(fs.existsSync(fullPath), true, `Falta archivo modular: ${relPath}`);
    assert.ok(fs.statSync(fullPath).size > 0, `Archivo vacío: ${relPath}`);
  }
});

test('todas las referencias res:// dentro de las escenas .tscn existen realmente', () => {
  const scenes = [
    'scenes/ui/main_menu.tscn',
    'scenes/ui/options_screen.tscn',
    'scenes/ui/controls_screen.tscn',
    'scenes/ui/mobile_hud.tscn',
    'scenes/cutscenes/abduction_cutscene.tscn',
    'scenes/levels/killer_house_level.tscn',
  ];
  const resRegex = /path="res:\/\/([^"]+)"/g;

  for (const sceneRel of scenes) {
    const sceneContent = fs.readFileSync(path.join(godotRoot, sceneRel), 'utf8');
    let match: RegExpExecArray | null;
    while ((match = resRegex.exec(sceneContent)) !== null) {
      const targetPath = path.join(godotRoot, match[1]);
      assert.equal(fs.existsSync(targetPath), true, `Recurso roto en ${sceneRel}: res://${match[1]}`);
    }
  }
});

test('existen las vistas previas PNG en .aistudio/artifacts/', () => {
  const artifactsDir = path.resolve(process.cwd(), '.aistudio/artifacts');
  const previews = ['killer_preview.png', 'cabin_intro_preview.png', 'killer_house_preview.png'];
  for (const png of previews) {
    const fullPath = path.join(artifactsDir, png);
    assert.equal(fs.existsSync(fullPath), true, `Falta render PNG: ${png}`);
    const header = fs.readFileSync(fullPath).subarray(0, 4);
    assert.deepEqual([...header], [0x89, 0x50, 0x4e, 0x47], `PNG inválido: ${png}`);
  }
});

test('existe workflow manual de GitHub Actions para compilar APK Debug en Godot 4.7.2', () => {
  const workflowPath = path.resolve(process.cwd(), '.github/workflows/build-android-debug-apk.yml');
  assert.equal(fs.existsSync(workflowPath), true, 'Debe existir .github/workflows/build-android-debug-apk.yml');

  const yml = fs.readFileSync(workflowPath, 'utf8');
  assert.match(yml, /workflow_dispatch:/);
  assert.doesNotMatch(yml, /^\s*push:/m);
  assert.doesNotMatch(yml, /^\s*pull_request:/m);
  assert.doesNotMatch(yml, /android-actions\/setup-android/);
  assert.match(yml, /sdkmanager/);
  assert.match(yml, /4\.7\.2-stable/);
  assert.match(yml, /4\.7\.2\.stable/);
  assert.match(yml, /--export-debug/);
  assert.match(yml, /Android APK \(Uptodown \/ Terceros\)/);
});

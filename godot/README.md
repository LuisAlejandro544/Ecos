# Ecos en la Penumbra — Juego Móvil 3D de Terror (Godot 4.7.2 + Blender .glb)

Proyecto modular configurado para **Android (APK)** con **Godot Engine 4.7.2** y modelos 3D generados mediante scripts de **Blender** en formato **`.glb`** (glTF 2.0 binario con texturas empaquetadas).

## 1. Historia y Mecánicas Implementadas
- **Cinemática Inicial (`scenes/cutscenes/abduction_cutscene.tscn`)**:
  - El protagonista adulto duerme en su cabaña en el bosque usando solo una camisa ligera (sin suéter).
  - Un asesino encapuchado/cubierto con chaqueta elegante de cuero ensangrentada, pantalones oscuros y trapo con somnífero entra por la ventana, lo duerme y lo lleva a su casa.
- **Casa del Asesino (`scenes/levels/killer_house_level.tscn`)**:
  - Despiertas en una **cama llena de sangre** dentro de un cuarto oscuro con **sangre en las paredes**.
  - Junto a la cama está la **mesa de noche ensangrentada** con la **Carta del Asesino** (se lee en un popup modal al apuntar y tocar *Leer Carta*).
  - **Sensación de frío**: al no llevar suéter, el frío corporal aumenta progresivamente.
  - **Regla de 3 Noches**: el contador muestra `NOCHE 1 / 3` (y desde Pausa puedes probar la progresión de captura entre noches).

## 2. Gráficos en Android (Vulkan 1.1 + Respaldo OpenGL ES 3.0)
- `renderer/rendering_method.mobile="mobile"` usa **Vulkan** automáticamente si el procesador/GPU del teléfono soporta Vulkan 1.1.
- `rendering_device/fallback_to_opengl3=true` cambia automáticamente a **OpenGL ES 3.0 (Compatibility)** si el dispositivo no soporta Vulkan, evitando cierres inesperados.

## 3. Modelos 3D con Blender (`.glb`)
Los scripts en `godot/tools/blender/` generan los `.glb` optimizados para móvil (con colisiones `-colonly` automáticas para Godot 4) y vistas previas `.png` en `.aistudio/artifacts/`:
- `godot/assets/models/characters/killer.glb`
- `godot/assets/models/characters/victim_adult.glb`
- `godot/assets/models/environments/cabin_intro.glb`
- `godot/assets/models/environments/killer_house.glb`

## 4. Pantallas y Controles Cómodos
- **Pantallas separadas**: Menú Principal (`main_menu.tscn`), Opciones (`options_screen.tscn`), Controles (`controls_screen.tscn`), Cinemática (`abduction_cutscene.tscn`) y Casa del Asesino (`killer_house_level.tscn`).
- **HUD Táctil Móvil (`mobile_hud.tscn`)**: Joystick izquierdo amplio, zona táctil derecha para cámara y botones grandes de *Linterna*, *Interactuar*, *Correr*, *Agachar* y *Pausa*.

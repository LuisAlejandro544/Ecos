extends Node
## Módulo central de estado, noches, frío y ciclo de vida (Autoload: GameState).
##
## ¿Para qué sirve este archivo?
## Administra el progreso de las 3 noches para escapar, la sensación de frío
## del protagonista (por llevar solo camisa y no suéter), la lectura de la carta,
## las preferencias de audio/sensibilidad táctil y la detección del backend gráfico
## activo (Vulkan 1.1 o OpenGL ES 3.0 de respaldo).

signal scene_change_requested(scene_path: String)
signal pause_state_changed(is_paused: bool)
signal night_changed(current_night: int, max_nights: int)
signal cold_changed(cold_level: float)
signal game_over_reached()

## Límite de FPS estable para cuidar la batería y temperatura en móviles.
@export var target_mobile_fps: int = 60

## Progreso de noches (el asesino da 3 noches para escapar).
var current_night: int = 1
const MAX_NIGHTS: int = 3

## Nivel de frío corporal (0.0 = normal, 1.0 = hipotermia/temblor fuerte).
## Empieza algo elevado porque el protagonista fue secuestrado solo en camisa.
var cold_level: float = 0.28

## Indica si el jugador ya leyó la carta en la mesa de noche.
var has_read_killer_letter: bool = false

## Estado actual de pausa.
var is_paused: bool = false

## Ajustes de usuario (pantalla de Opciones).
var touch_sensitivity: float = 0.32
var ambience_volume: float = 0.85
var sfx_volume: float = 0.90


func _ready() -> void:
	# Configura el ciclo de vida móvil y mantiene la pantalla encendida en escenas oscuras.
	process_mode = Node.PROCESS_MODE_ALWAYS
	Engine.max_fps = target_mobile_fps
	DisplayServer.screen_set_keep_on(true)


func get_active_graphics_backend_label() -> String:
	# Informa qué API gráfica está usando Godot 4.7.2 en este teléfono:
	# si soporta Vulkan 1.1 usa Vulkan (Mobile), y si no, OpenGL ES (Compatibility).
	if RenderingServer.get_rendering_device() != null:
		return "Vulkan 1.1 (Renderizador Móvil)"
	return "OpenGL ES 3.0 (Modo Compatibilidad)"


func reset_new_run() -> void:
	# Reinicia la partida desde la Noche 1 con frío inicial por falta de suéter.
	current_night = 1
	cold_level = 0.28
	has_read_killer_letter = false
	set_paused(false)
	night_changed.emit(current_night, MAX_NIGHTS)
	cold_changed.emit(cold_level)


func set_cold_level(value: float) -> void:
	# Actualiza gradualmente el nivel de frío y notifica al HUD.
	var clamped: float = clampf(value, 0.0, 1.0)
	if not is_equal_approx(cold_level, clamped):
		cold_level = clamped
		cold_changed.emit(cold_level)


func register_capture_and_advance_night() -> bool:
	# Cuando el asesino atrapa al jugador, avanza la noche.
	# Devuelve true si aún quedan noches para despertar, o false si superó las 3 noches.
	if current_night < MAX_NIGHTS:
		current_night += 1
		cold_level = clampf(cold_level + 0.12, 0.28, 0.85)
		night_changed.emit(current_night, MAX_NIGHTS)
		cold_changed.emit(cold_level)
		return true
	game_over_reached.emit()
	return false


func set_paused(paused: bool) -> void:
	if is_paused == paused:
		return
	is_paused = paused
	get_tree().paused = is_paused
	pause_state_changed.emit(is_paused)


func change_scene(scene_path: String) -> void:
	# Valida la ruta antes de cambiar de pantalla para evitar cierres en móvil.
	if not ResourceLoader.exists(scene_path):
		push_error("GameState: Escena no encontrada -> " + scene_path)
		return
	set_paused(false)
	scene_change_requested.emit(scene_path)
	get_tree().change_scene_to_file(scene_path)


func _notification(what: int) -> void:
	# Pausa automáticamente si el usuario sale de la app en Android.
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		set_paused(true)

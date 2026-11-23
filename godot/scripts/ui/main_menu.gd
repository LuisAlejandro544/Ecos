extends Control
## Pantalla principal del menú (MainMenu).
##
## ¿Para qué sirve este archivo?
## Muestra la pantalla de título oscura del juego móvil de terror, informa
## el motor gráfico activo (Vulkan 1.1 o OpenGL ES 3.0 de respaldo) y ofrece
## botones cómodos para iniciar la cinemática, entrar directo a la casa,
## abrir Opciones o consultar Controles en pantallas separadas.

const CUTSCENE_SCENE: String = "res://scenes/cutscenes/abduction_cutscene.tscn"
const HOUSE_SCENE: String = "res://scenes/levels/killer_house_level.tscn"
const OPTIONS_SCENE: String = "res://scenes/ui/options_screen.tscn"
const CONTROLS_SCENE: String = "res://scenes/ui/controls_screen.tscn"

@onready var backend_label: Label = $Margin/Layout/FooterBar/GraphicsBackendLabel
@onready var btn_play_cutscene: Button = $Margin/Layout/MenuCard/VBox/PlayCutsceneButton
@onready var btn_play_house: Button = $Margin/Layout/MenuCard/VBox/DirectHouseButton
@onready var btn_options: Button = $Margin/Layout/MenuCard/VBox/OptionsButton
@onready var btn_controls: Button = $Margin/Layout/MenuCard/VBox/ControlsButton


func _ready() -> void:
	# Muestra en pantalla si el dispositivo usa Vulkan 1.1 o OpenGL ES 3.0.
	if backend_label != null:
		backend_label.text = "Gráficos: " + GameState.get_active_graphics_backend_label()

	if btn_play_cutscene != null:
		btn_play_cutscene.pressed.connect(func():
			GameState.reset_new_run()
			GameState.change_scene(CUTSCENE_SCENE)
		)
	if btn_play_house != null:
		btn_play_house.pressed.connect(func():
			GameState.reset_new_run()
			GameState.change_scene(HOUSE_SCENE)
		)
	if btn_options != null:
		btn_options.pressed.connect(func(): GameState.change_scene(OPTIONS_SCENE))
	if btn_controls != null:
		btn_controls.pressed.connect(func(): GameState.change_scene(CONTROLS_SCENE))

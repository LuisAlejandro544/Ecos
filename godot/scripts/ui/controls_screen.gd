extends Control
## Pantalla aparte de Guía de Controles Táctiles (ControlsScreen).
##
## ¿Para qué sirve este archivo?
## Explica visualmente la distribución cómoda de controles móviles antes de jugar:
## joystick izquierdo para caminar, zona derecha para mirar y botones grandes
## para Linterna, Interactuar (leer carta), Agacharse y Correr.

const MAIN_MENU_SCENE: String = "res://scenes/ui/main_menu.tscn"

@onready var back_button: Button = $Margin/Panel/VBox/BackButton


func _ready() -> void:
	if back_button != null:
		back_button.pressed.connect(func(): GameState.change_scene(MAIN_MENU_SCENE))

extends Control
## Pantalla aparte de Opciones (OptionsScreen).
##
## ¿Para qué sirve este archivo?
## Permite ajustar cómodamente desde el teléfono la sensibilidad táctil
## de la cámara y los volúmenes de Ambiente y Efectos, además de mostrar
## la API gráfica detectada (Vulkan 1.1 / OpenGL ES).

const MAIN_MENU_SCENE: String = "res://scenes/ui/main_menu.tscn"

@onready var sens_slider: HSlider = $Margin/Panel/VBox/SensRow/SensSlider
@onready var sens_value_label: Label = $Margin/Panel/VBox/SensRow/SensValue
@onready var amb_slider: HSlider = $Margin/Panel/VBox/AmbRow/AmbSlider
@onready var sfx_slider: HSlider = $Margin/Panel/VBox/SfxRow/SfxSlider
@onready var backend_info: Label = $Margin/Panel/VBox/BackendInfo
@onready var back_button: Button = $Margin/Panel/VBox/BackButton


func _ready() -> void:
	if backend_info != null:
		backend_info.text = "Motor gráfico activo: " + GameState.get_active_graphics_backend_label()

	if sens_slider != null:
		sens_slider.value = GameState.touch_sensitivity
		_update_sens_text(GameState.touch_sensitivity)
		sens_slider.value_changed.connect(func(val: float):
			GameState.touch_sensitivity = val
			_update_sens_text(val)
		)

	if amb_slider != null:
		amb_slider.value = GameState.ambience_volume
		amb_slider.value_changed.connect(func(val: float):
			GameState.ambience_volume = val
			AudioDirector.set_bus_volume_linear(&"Ambience", val)
		)

	if sfx_slider != null:
		sfx_slider.value = GameState.sfx_volume
		sfx_slider.value_changed.connect(func(val: float):
			GameState.sfx_volume = val
			AudioDirector.set_bus_volume_linear(&"SFX", val)
		)

	if back_button != null:
		back_button.pressed.connect(func(): GameState.change_scene(MAIN_MENU_SCENE))


func _update_sens_text(val: float) -> void:
	if sens_value_label != null:
		sens_value_label.text = "%.2f" % val

extends CanvasLayer
## Interfaz móvil cómoda y modales de la partida (MobileHUD).
##
## ¿Para qué sirve este archivo?
## Provee controles táctiles ergonómicos para pulgares (joystick virtual amplio
## a la izquierda, arrastre suave de cámara a la derecha, botones grandes y cómodos
## de Linterna, Interactuar y Agacharse/Correr), además del indicador de 3 noches,
## sensación de frío (sin suéter), popup de la Carta del Asesino y popup de Pausa.

@export var player_path: NodePath

@onready var joystick_area: Control = $TouchLayer/JoystickArea
@onready var joystick_knob: ColorRect = $TouchLayer/JoystickArea/JoystickRing/JoystickKnob
@onready var look_area: Control = $TouchLayer/LookArea

@onready var btn_interact: Button = $TouchLayer/ActionCluster/InteractButton
@onready var btn_flashlight: Button = $TouchLayer/ActionCluster/FlashlightButton
@onready var btn_crouch: Button = $TouchLayer/ActionCluster/CrouchButton
@onready var btn_sprint: Button = $TouchLayer/ActionCluster/SprintButton
@onready var btn_pause: Button = $TopBar/PauseButton

@onready var night_label: Label = $TopBar/StatusPanel/HBox/NightLabel
@onready var cold_label: Label = $TopBar/StatusPanel/HBox/ColdLabel
@onready var cold_vignette: ColorRect = $ColdVignette
@onready var prompt_banner: Label = $PromptBanner

@onready var letter_popup: Control = $LetterPopup
@onready var letter_close_btn: Button = $LetterPopup/Panel/Margin/VBox/CloseLetterButton
@onready var pause_popup: Control = $PausePopup
@onready var resume_btn: Button = $PausePopup/Panel/VBox/ResumeButton
@onready var next_night_btn: Button = $PausePopup/Panel/VBox/SimulateNightButton
@onready var main_menu_btn: Button = $PausePopup/Panel/VBox/MenuButton

const MAIN_MENU_SCENE: String = "res://scenes/ui/main_menu.tscn"

var _player: Node = null
var _joy_touch_index: int = -1
var _look_touch_index: int = -1
var _joy_center: Vector2 = Vector2.ZERO
var _joy_radius: float = 78.0


func _ready() -> void:
	if player_path != NodePath(""):
		_player = get_node_or_null(player_path)

	if _player != null:
		_player.interactable_focused.connect(_on_interactable_focused)
		_player.interactable_cleared.connect(_on_interactable_cleared)
		_player.interaction_triggered.connect(_on_interaction_triggered)

	GameState.night_changed.connect(_on_night_changed)
	GameState.cold_changed.connect(_on_cold_changed)
	_on_night_changed(GameState.current_night, GameState.MAX_NIGHTS)
	_on_cold_changed(GameState.cold_level)

	if joystick_area != null:
		joystick_area.gui_input.connect(_on_joystick_gui_input)
	if look_area != null:
		look_area.gui_input.connect(_on_look_gui_input)

	if btn_interact != null:
		btn_interact.visible = false
		btn_interact.pressed.connect(func():
			if _player != null:
				_player.trigger_focus_interaction()
		)
	if btn_flashlight != null:
		btn_flashlight.pressed.connect(func():
			if _player != null:
				_player.toggle_flashlight()
		)
	if btn_crouch != null:
		btn_crouch.pressed.connect(func():
			if _player != null:
				_player.toggle_crouch()
		)
	if btn_sprint != null:
		btn_sprint.button_down.connect(func():
			if _player != null:
				_player.set_sprint(true)
		)
		btn_sprint.button_up.connect(func():
			if _player != null:
				_player.set_sprint(false)
		)

	if btn_pause != null:
		btn_pause.pressed.connect(_open_pause_popup)
	if letter_close_btn != null:
		letter_close_btn.pressed.connect(_close_letter_popup)
	if resume_btn != null:
		resume_btn.pressed.connect(_close_pause_popup)
	if main_menu_btn != null:
		main_menu_btn.pressed.connect(func(): GameState.change_scene(MAIN_MENU_SCENE))
	if next_night_btn != null:
		next_night_btn.pressed.connect(_on_simulate_night_capture)

	if letter_popup != null:
		letter_popup.visible = false
	if pause_popup != null:
		pause_popup.visible = false
	if prompt_banner != null:
		prompt_banner.visible = false


func _on_joystick_gui_input(event: InputEvent) -> void:
	# Joystick táctil ergonómico que soporta multi-touch sin interferir con la cámara.
	if event is InputEventScreenTouch:
		if event.pressed and _joy_touch_index == -1:
			_joy_touch_index = event.index
			_joy_center = joystick_area.size * 0.5
			_update_joystick(event.position)
		elif not event.pressed and event.index == _joy_touch_index:
			_joy_touch_index = -1
			_reset_joystick()
	elif event is InputEventScreenDrag and event.index == _joy_touch_index:
		_update_joystick(event.position)


func _update_joystick(local_pos: Vector2) -> void:
	var offset: Vector2 = local_pos - _joy_center
	if offset.length() > _joy_radius:
		offset = offset.normalized() * _joy_radius
	if joystick_knob != null:
		joystick_knob.position = _joy_center + offset - (joystick_knob.size * 0.5)
	if _player != null:
		# Invertimos Y porque en pantalla arriba es negativo y avanzar es positivo.
		_player.set_touch_move_vector(Vector2(offset.x / _joy_radius, -offset.y / _joy_radius))


func _reset_joystick() -> void:
	if joystick_knob != null and joystick_area != null:
		joystick_knob.position = (joystick_area.size * 0.5) - (joystick_knob.size * 0.5)
	if _player != null:
		_player.set_touch_move_vector(Vector2.ZERO)


func _on_look_gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and _look_touch_index == -1:
			_look_touch_index = event.index
		elif not event.pressed and event.index == _look_touch_index:
			_look_touch_index = -1
	elif event is InputEventScreenDrag and event.index == _look_touch_index:
		if _player != null:
			_player.add_look_delta(event.relative)


func _on_interactable_focused(prompt_text: String, _target_id: String) -> void:
	if btn_interact != null:
		btn_interact.visible = true
		btn_interact.text = prompt_text
	if prompt_banner != null:
		prompt_banner.visible = true
		prompt_banner.text = prompt_text


func _on_interactable_cleared() -> void:
	if btn_interact != null:
		btn_interact.visible = false
	if prompt_banner != null:
		prompt_banner.visible = false


func _on_interaction_triggered(target_id: String) -> void:
	if target_id == "killer_letter":
		GameState.has_read_killer_letter = true
		if letter_popup != null:
			letter_popup.visible = true
			GameState.set_paused(true)
	elif target_id == "exit_door":
		if prompt_banner != null:
			prompt_banner.visible = true
			prompt_banner.text = "Puerta sellada con tablones y cadenas. Necesitas escapar antes de la Noche 3."


func _close_letter_popup() -> void:
	if letter_popup != null:
		letter_popup.visible = false
	GameState.set_paused(false)


func _open_pause_popup() -> void:
	if pause_popup != null:
		pause_popup.visible = true
	GameState.set_paused(true)


func _close_pause_popup() -> void:
	if pause_popup != null:
		pause_popup.visible = false
	GameState.set_paused(false)


func _on_simulate_night_capture() -> void:
	# Permite probar el ciclo de 3 noches (al ser atrapado avanzas de noche y despiertas de nuevo).
	_close_pause_popup()
	var can_continue: bool = GameState.register_capture_and_advance_night()
	if can_continue:
		get_tree().reload_current_scene()
	else:
		GameState.change_scene(MAIN_MENU_SCENE)


func _on_night_changed(night: int, max_nights: int) -> void:
	if night_label != null:
		night_label.text = "NOCHE %d / %d" % [night, max_nights]


func _on_cold_changed(cold: float) -> void:
	if cold_label != null:
		var pct: int = int(round(cold * 100.0))
		cold_label.text = "FRÍO (sin suéter): %d%%" % pct
	if cold_vignette != null:
		cold_vignette.color = Color(0.55, 0.72, 0.92, clampf((cold - 0.25) * 0.28, 0.0, 0.26))

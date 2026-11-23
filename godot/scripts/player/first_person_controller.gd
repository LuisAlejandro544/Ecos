extends CharacterBody3D
## Controlador modular en primera persona para móvil (PlayerController).
##
## ¿Para qué sirve este archivo?
## Gestiona el movimiento suave con joystick táctil o teclado, rotación de cámara
## por arrastre táctil, linterna parpadeante, detección de objetos interactuables
## (como la carta del asesino en la mesa de noche o la puerta cerrada), secuencia
## de despertar en la cama ensangrentada y sensación progresiva de frío.

signal interactable_focused(prompt_text: String, target_id: String)
signal interactable_cleared()
signal interaction_triggered(target_id: String)
signal flashlight_toggled(is_on: bool)

@export var walk_speed: float = 2.85
@export var sprint_speed: float = 4.35
@export var crouch_speed: float = 1.65
@export var gravity_force: float = 14.0

@onready var head_pivot: Node3D = $HeadPivot
@onready var camera: Camera3D = $HeadPivot/Camera3D
@onready var flashlight: SpotLight3D = $HeadPivot/Camera3D/Flashlight
@onready var interact_ray: RayCast3D = $HeadPivot/Camera3D/InteractRay
@onready var body_collision: CollisionShape3D = $CollisionShape3D

var _touch_move_vector: Vector2 = Vector2.ZERO
var _is_sprinting: bool = false
var _is_crouching: bool = false
var _flashlight_on: bool = true
var _is_waking_up: bool = true
var _yaw: float = 0.0
var _pitch: float = 0.0
var _focused_id: String = ""
var _flicker_timer: float = 0.0
var _base_flashlight_energy: float = 2.4
var _standing_head_y: float = 1.62
var _crouch_head_y: float = 1.02


func _ready() -> void:
	# Inicia el despertar desde la cama llena de sangre.
	_yaw = rotation.y
	if flashlight != null:
		_base_flashlight_energy = flashlight.light_energy
		flashlight.visible = _flashlight_on
	play_wakeup_sequence()


func play_wakeup_sequence() -> void:
	# Anima suavemente la cámara desde estar acostado en la cama hacia ponerse de pie.
	_is_waking_up = true
	if head_pivot != null:
		head_pivot.position.y = 0.72
		head_pivot.rotation.z = 0.38
		_pitch = -0.18
		head_pivot.rotation.x = _pitch
		var tw: Tween = create_tween()
		tw.set_parallel(true)
		tw.tween_property(head_pivot, "position:y", _standing_head_y, 2.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		tw.tween_property(head_pivot, "rotation:z", 0.0, 2.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		tw.tween_property(head_pivot, "rotation:x", 0.0, 2.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		tw.finished.connect(func():
			_pitch = 0.0
			_is_waking_up = false
		)
	else:
		_is_waking_up = false


func set_touch_move_vector(vec: Vector2) -> void:
	# Recibe la dirección del joystick virtual (X: izq/der, Y: arriba/abajo).
	_touch_move_vector = vec


func add_look_delta(delta_px: Vector2) -> void:
	# Rota la cabeza del jugador según el arrastre del pulgar derecho.
	if _is_waking_up:
		return
	var sens: float = GameState.touch_sensitivity * 0.012
	_yaw -= delta_px.x * sens
	_pitch = clampf(_pitch - delta_px.y * sens, deg_to_rad(-72.0), deg_to_rad(75.0))
	rotation.y = _yaw
	if head_pivot != null:
		head_pivot.rotation.x = _pitch


func toggle_flashlight() -> void:
	_flashlight_on = not _flashlight_on
	if flashlight != null:
		flashlight.visible = _flashlight_on
	flashlight_toggled.emit(_flashlight_on)


func set_sprint(active: bool) -> void:
	_is_sprinting = active and not _is_crouching


func toggle_crouch() -> void:
	_is_crouching = not _is_crouching
	if _is_crouching:
		_is_sprinting = false


func trigger_focus_interaction() -> void:
	if _focused_id != "":
		interaction_triggered.emit(_focused_id)


func _physics_process(delta: float) -> void:
	if _is_waking_up:
		return

	_update_gravity(delta)
	_update_movement(delta)
	_update_crouch_height(delta)
	_update_flashlight_flicker(delta)
	_update_cold_feeling(delta)
	_update_interaction_ray()


func _update_gravity(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity_force * delta
	else:
		velocity.y = 0.0


func _update_movement(delta: float) -> void:
	# Combina el joystick táctil móvil con las acciones estándar de entrada.
	var input_dir: Vector2 = _touch_move_vector
	if input_dir.length_squared() < 0.01:
		input_dir = Input.get_vector("move_left", "move_right", "move_backward", "move_forward")

	# Joystick: Y positivo arriba -> avanzar (-Z en Godot).
	var forward: Vector3 = -global_transform.basis.z
	var right: Vector3 = global_transform.basis.x
	var move_dir: Vector3 = (right * input_dir.x + forward * input_dir.y)
	if move_dir.length() > 1.0:
		move_dir = move_dir.normalized()

	var current_speed: float = walk_speed
	if _is_crouching:
		current_speed = crouch_speed
	elif _is_sprinting:
		current_speed = sprint_speed

	velocity.x = lerpf(velocity.x, move_dir.x * current_speed, clampf(delta * 10.0, 0.0, 1.0))
	velocity.z = lerpf(velocity.z, move_dir.z * current_speed, clampf(delta * 10.0, 0.0, 1.0))
	move_and_slide()


func _update_crouch_height(delta: float) -> void:
	if head_pivot == null:
		return
	var target_y: float = _crouch_head_y if _is_crouching else _standing_head_y
	head_pivot.position.y = lerpf(head_pivot.position.y, target_y, clampf(delta * 8.0, 0.0, 1.0))


func _update_flashlight_flicker(delta: float) -> void:
	# Parpadeo sutil e inquietante de la linterna dentro de la casa del asesino.
	if flashlight == null or not _flashlight_on:
		return
	_flicker_timer += delta
	var wave: float = sin(_flicker_timer * 7.5) * sin(_flicker_timer * 19.3)
	if wave > 0.86:
		flashlight.light_energy = _base_flashlight_energy * 0.35
	else:
		flashlight.light_energy = _base_flashlight_energy


func _update_cold_feeling(delta: float) -> void:
	# Al no tener suéter (solo camisa), el frío sube lento en habitaciones abiertas.
	var new_cold: float = clampf(GameState.cold_level + delta * 0.008, 0.25, 0.92)
	GameState.set_cold_level(new_cold)


func _update_interaction_ray() -> void:
	if interact_ray == null:
		return
	interact_ray.force_raycast_update()
	if interact_ray.is_colliding():
		var collider: Object = interact_ray.get_collider()
		if collider != null and collider.has_meta("interact_id"):
			var id_str: String = str(collider.get_meta("interact_id"))
			var prompt: String = str(collider.get_meta("interact_prompt", "Interactuar"))
			if id_str != _focused_id:
				_focused_id = id_str
				interactable_focused.emit(prompt, id_str)
			return
	if _focused_id != "":
		_focused_id = ""
		interactable_cleared.emit()

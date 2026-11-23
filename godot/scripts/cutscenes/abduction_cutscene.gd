extends Node3D
## Escena de cinemática inicial: el secuestro en la cabaña del bosque.
##
## ¿Para qué sirve este archivo?
## Reproduce la secuencia cinematográfica 3D donde el protagonista adulto
## duerme en su cabaña (solo con camisa, sin suéter), el asesino cubierto con
## chaqueta de cuero ensangrentada y pantalón oscuro entra por la ventana,
## lo duerme con un trapo con somnífero y lo traslada a su casa otorgándole
## 3 noches para escapar.

@onready var cutscene_camera: Camera3D = $CutsceneCamera
@onready var killer_node: Node3D = $KillerModel
@onready var victim_node: Node3D = $VictimModel
@onready var subtitle_label: Label = $CanvasLayer/MarginContainer/VBoxContainer/SubtitlePanel/SubtitleLabel
@onready var fade_overlay: ColorRect = $CanvasLayer/FadeOverlay
@onready var skip_button: Button = $CanvasLayer/SkipButton

const KILLER_HOUSE_SCENE: String = "res://scenes/levels/killer_house_level.tscn"

var _elapsed: float = 0.0
var _stage: int = 0
var _is_transitioning: bool = false


func _ready() -> void:
	# Reinicia los datos de partida al iniciar la cinemática.
	GameState.reset_new_run()
	AudioDirector.set_tension_level(0.15)
	if skip_button != null:
		skip_button.pressed.connect(_on_skip_pressed)

	# Posición inicial del asesino entrando desde la ventana Norte de la cabaña.
	if killer_node != null:
		killer_node.position = Vector3(0.0, 0.35, -2.95)
		killer_node.rotation.y = 0.0

	# Protagonista acostado sobre la cama de la cabaña solo con su camisa (cabeza en almohada Z=1.34).
	if victim_node != null:
		victim_node.position = Vector3(-1.35, 0.64, -0.25)
		victim_node.rotation = Vector3(1.5708, 0.0, 0.0)

	if fade_overlay != null:
		fade_overlay.color = Color(0.0, 0.0, 0.0, 1.0)
		var tw: Tween = create_tween()
		tw.tween_property(fade_overlay, "color:a", 0.0, 1.5)

	_set_subtitle("Cabaña del Bosque — 02:18 AM. Afuera el bosque murmura... y solo llevas una camisa.")


func _process(delta: float) -> void:
	if _is_transitioning:
		return
	_elapsed += delta

	# Etapa 1 (0s - 4.5s): El asesino se cuela por la ventana abierta en la oscuridad.
	if _elapsed < 4.5:
		if killer_node != null:
			var t1: float = clampf(_elapsed / 4.5, 0.0, 1.0)
			killer_node.position = Vector3(0.0, lerpf(0.35, 0.0, t1), lerpf(-2.95, -1.65, t1))
		if cutscene_camera != null:
			cutscene_camera.position = Vector3(1.1, 1.48, 0.35)
			cutscene_camera.look_at(Vector3(-0.35, 1.15, -1.75), Vector3.UP)

	# Etapa 2 (4.5s - 9.5s): Se acerca lentamente hacia la cama con la chaqueta de cuero ensangrentada.
	elif _elapsed < 9.5:
		if _stage < 1:
			_stage = 1
			AudioDirector.set_tension_level(0.55)
			_set_subtitle("Alguien entró por la ventana... No alcanzas a distinguir su rostro bajo la capucha.")
		if killer_node != null:
			var t2: float = clampf((_elapsed - 4.5) / 5.0, 0.0, 1.0)
			killer_node.position = Vector3(lerpf(0.0, -0.78, t2), 0.0, lerpf(-1.65, 0.65, t2))
			killer_node.rotation.y = lerpf(0.0, -0.52, t2)
		if cutscene_camera != null:
			cutscene_camera.position = Vector3(lerpf(1.1, -0.35, (_elapsed - 4.5) / 5.0), 1.32, lerpf(0.35, 1.65, (_elapsed - 4.5) / 5.0))
			cutscene_camera.look_at(Vector3(-0.85, 1.25, 0.65), Vector3.UP)

	# Etapa 3 (9.5s - 14.5s): Presiona el trapo con somnífero y todo se vuelve oscuro.
	elif _elapsed < 14.5:
		if _stage < 2:
			_stage = 2
			AudioDirector.set_tension_level(0.95)
			_set_subtitle("El trapo húmedo te cubre la boca. Sientes un olor químico dulce... y todo se apaga.")
		if killer_node != null:
			var t3: float = clampf((_elapsed - 9.5) / 3.0, 0.0, 1.0)
			killer_node.position = Vector3(-0.78, lerpf(0.0, -0.18, t3), lerpf(0.65, 0.92, t3))
		if fade_overlay != null:
			var alpha: float = clampf((_elapsed - 10.5) / 3.6, 0.0, 1.0)
			fade_overlay.color.a = alpha

	# Etapa 4 (14.5s - 17.5s): Frase final del asesino antes de despertar en su casa.
	elif _elapsed < 17.5:
		if _stage < 3:
			_stage = 3
			_set_subtitle("«Bienvenido a mi casa. Tienes 3 noches para salir... si el frío no te detiene antes.»")
	else:
		_finish_cutscene()


func _set_subtitle(text: String) -> void:
	if subtitle_label != null:
		subtitle_label.text = text


func _on_skip_pressed() -> void:
	_finish_cutscene()


func _finish_cutscene() -> void:
	if _is_transitioning:
		return
	_is_transitioning = true
	GameState.change_scene(KILLER_HOUSE_SCENE)

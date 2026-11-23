extends Node3D
## Nivel jugable: La Casa del Asesino (KillerHouseLevel).
##
## ¿Para qué sirve este archivo?
## Carga el escenario 3D killer_house.glb generado en Blender, posiciona al
## jugador adulto despertando sobre la cama llena de sangre junto a la mesa
## de noche ensangrentada, habilita la interacción con la Carta del Asesino
## y la puerta sellada, y conecta la iluminación/atmósfera tenebrosa.

@onready var world_env: WorldEnvironment = $WorldEnvironment
@onready var player: CharacterBody3D = $Player
@onready var nightstand_lamp_light: OmniLight3D = $NightstandLampLight
@onready var hallway_light: OmniLight3D = $HallwayFlickerLight

var _flicker_acc: float = 0.0


func _ready() -> void:
	# Conecta el entorno tenebroso al AtmosphereDirector para controlar niebla y opresión.
	if world_env != null and world_env.environment != null:
		AtmosphereDirector.register_environment(world_env.environment)
		AtmosphereDirector.apply_abyss_intensity(0.45)

	AudioDirector.set_tension_level(0.35)


func _process(delta: float) -> void:
	# Parpadeo suave de la bombilla del pasillo para mantener tensión constante.
	_flicker_acc += delta
	if hallway_light != null:
		var pulse: float = sin(_flicker_acc * 4.2) * sin(_flicker_acc * 11.7)
		hallway_light.light_energy = 0.25 if pulse > 0.78 else 0.78

extends Node
## Director modular de audio tenebroso (Autoload: AudioDirector).
##
## ¿Para qué sirve este archivo?
## Administra los buses de sonido definidos en horror_bus_layout.tres
## (Ambience, SFX, Whispers, Heartbeat) y permite ajustar la tensión sonora
## de manera gradual sin saturar el mezclador de Android.

## Nivel normalizado de tensión (0.0 = calma tensa, 1.0 = pánico máximo).
var tension_level: float = 0.0


func set_tension_level(value: float) -> void:
	# Limita la tensión entre 0 y 1 y ajusta el volumen del bus Heartbeat
	# para reforzar la inmersión en momentos críticos.
	tension_level = clampf(value, 0.0, 1.0)
	var heartbeat_bus_idx: int = AudioServer.get_bus_index(&"Heartbeat")
	if heartbeat_bus_idx != -1:
		var target_db: float = lerpf(-28.0, -2.0, tension_level)
		AudioServer.set_bus_volume_db(heartbeat_bus_idx, target_db)


func set_bus_volume_linear(bus_name: StringName, linear_volume: float) -> void:
	# Convierte un porcentaje lineal (0.0 a 1.0) a decibelios seguros para Godot AudioServer.
	var bus_idx: int = AudioServer.get_bus_index(bus_name)
	if bus_idx == -1:
		push_warning("AudioDirector: No se encontró el bus de audio -> " + String(bus_name))
		return
	var clamped_volume: float = clampf(linear_volume, 0.0001, 1.0)
	AudioServer.set_bus_volume_db(bus_idx, linear_to_db(clamped_volume))

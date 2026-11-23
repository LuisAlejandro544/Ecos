extends Node3D
## Escena inicial de arranque modular (Boot).
##
## ¿Para qué sirve este archivo?
## Es el punto de entrada definido en project.godot (`run/main_scene`).
## Conecta el WorldEnvironment inicial con el AtmosphereDirector y verifica
## que la configuración base de Godot 4.7.2 arranque limpia antes de añadir
## el menú principal y los niveles del juego de terror.

@onready var world_environment: WorldEnvironment = $WorldEnvironment


func _ready() -> void:
	# Registra el entorno tenebroso en AtmosphereDirector para permitir cambios dinámicos.
	if world_environment != null and world_environment.environment != null:
		AtmosphereDirector.register_environment(world_environment.environment)
		AtmosphereDirector.apply_abyss_intensity(0.35)

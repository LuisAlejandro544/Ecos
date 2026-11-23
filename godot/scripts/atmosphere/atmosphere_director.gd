extends Node
## Director modular de atmósfera y niebla (Autoload: AtmosphereDirector).
##
## ¿Para qué sirve este archivo?
## Controla dinámicamente los parámetros del Environment (densidad de niebla,
## luz ambiental y contraste) compatible con el renderizador Mobile (Vulkan)
## de Godot 4.7.2, permitiendo oscurecer o espesar la neblina en tiempo real.

signal atmosphere_updated(fog_density: float, ambient_energy: float)

## Referencia opcional al Environment activo en la escena actual.
var active_environment: Environment = null


func register_environment(env: Environment) -> void:
	# Registra el recurso Environment de la escena activa para modificarlo de forma segura.
	active_environment = env


func apply_abyss_intensity(intensity: float) -> void:
	# Ajusta la opresión visual (0.0 = penumbra base, 1.0 = oscuridad sofocante)
	# sin usar niebla volumétrica pesada, manteniendo alto rendimiento en móviles.
	if active_environment == null:
		return
	var t: float = clampf(intensity, 0.0, 1.0)
	var new_fog_density: float = lerpf(0.065, 0.16, t)
	var new_ambient_energy: float = lerpf(0.32, 0.10, t)
	active_environment.fog_density = new_fog_density
	active_environment.ambient_light_energy = new_ambient_energy
	atmosphere_updated.emit(new_fog_density, new_ambient_energy)

extends Node3D
class_name ElectroTrap

const COST := 1000

@onready var model_holder: Node3D = $ModelHolder
@onready var arc_wall: MeshInstance3D = $ArcWall
@onready var trap_light: OmniLight3D = $OmniLight3D
@onready var kill_area: Area3D = $KillArea

var is_running: bool = false
var cooldown: float = 0.0
var run_timer: float = 0.0


func _ready() -> void:
	if ResourceLoader.exists("res://assets/models/props/electro_trap.glb"):
		var inst := (load("res://assets/models/props/electro_trap.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
	arc_wall.visible = false
	trap_light.light_energy = 0.0


func _process(delta: float) -> void:
	if is_running:
		run_timer -= delta
		for body in kill_area.get_overlapping_bodies():
			if body.is_in_group("zombies") and body.has_method("take_damage"):
				body.take_damage(99999.0, false, body.global_position, Vector3.UP)
		if run_timer <= 0.0:
			is_running = false
			arc_wall.visible = false
			trap_light.light_energy = 0.0
			cooldown = 28.0
	elif cooldown > 0.0:
		cooldown = maxf(0.0, cooldown - delta)


func get_interact_prompt(_player: Node) -> String:
	if not GameManager.power_on:
		return "Electro-Shock Trap — Power Required!"
	if is_running:
		return "Electro-Shock Trap Active!"
	if cooldown > 0.0:
		return "Trap Cooling Down (%ds)..." % int(ceilf(cooldown))
	return "[E] Activate Electro-Shock Trap [Cost: %d]" % COST


func interact(_player: Node) -> void:
	if not GameManager.power_on or is_running or cooldown > 0.0:
		return
	if GameManager.spend_points(COST):
		is_running = true
		run_timer = 22.0
		arc_wall.visible = true
		trap_light.light_energy = 4.5
		AudioManager.play_3d("power_on", global_position, 0.2, 0.0)

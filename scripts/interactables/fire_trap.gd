extends Node3D
class_name FireTrap

const COST := 1000
const ACTIVE_DURATION := 20.0
const COOLDOWN_DURATION := 28.0
const PANZER_TICK_INTERVAL := 0.25
const PANZER_TICK_DAMAGE := 110.0
const PLAYER_TICK_INTERVAL := 0.45
const PLAYER_BURN_DAMAGE := 12.0

@onready var model_holder: Node3D = $ModelHolder
@onready var burner_holder: Node3D = $BurnerHolder
@onready var flame_wall: MeshInstance3D = $FlameWall
@onready var flame_particles: GPUParticles3D = $FlameParticles
@onready var trap_light: OmniLight3D = $OmniLight3D
@onready var console_light: OmniLight3D = $ConsoleLight
@onready var kill_area: Area3D = $KillArea

var is_running: bool = false
var cooldown: float = 0.0
var run_timer: float = 0.0

var _lever: Node3D = null
var _lamp_mat: StandardMaterial3D = null
var _panzer_tick_cd: Dictionary = {}
var _player_tick_cd: float = 0.0


func _ready() -> void:
	add_to_group("fire_traps")
	GameManager.power_activated.connect(_refresh_console_visuals)
	if ResourceLoader.exists("res://assets/models/props/fire_trap.glb"):
		var inst := (load("res://assets/models/props/fire_trap.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		_lever = inst.find_child("PullLever", true, false) as Node3D
		var lamp := inst.find_child("IndicatorLamp", true, false) as Node3D
		_lamp_mat = _extract_lamp_mat(lamp)
	if ResourceLoader.exists("res://assets/models/props/fire_trap_burner.glb"):
		var burner := (load("res://assets/models/props/fire_trap_burner.glb") as PackedScene).instantiate()
		burner_holder.add_child(burner)
	set_trap_active(false, true)
	_refresh_console_visuals()


func _extract_lamp_mat(node: Node) -> StandardMaterial3D:
	if node == null:
		return null
	var stack: Array[Node] = [node]
	while not stack.is_empty():
		var cur: Node = stack.pop_back()
		if cur is MeshInstance3D:
			var mi := cur as MeshInstance3D
			var mat := mi.get_active_material(0)
			if mat is StandardMaterial3D:
				var dup := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				mi.set_surface_override_material(0, dup)
				return dup
		for ch in cur.get_children():
			stack.append(ch)
	return null


func _refresh_console_visuals() -> void:
	var col := Color(1.0, 0.20, 0.12)
	var lamp_e := 0.7
	var light_e := 0.8
	if is_running:
		col = Color(1.0, 0.45, 0.08)
		lamp_e = 2.8
		light_e = 2.2
	elif cooldown > 0.0:
		col = Color(0.96, 0.65, 0.14)
		lamp_e = 1.2
		light_e = 1.0
	elif GameManager.power_on:
		col = Color(0.20, 0.96, 0.36)
		lamp_e = 2.2
		light_e = 1.6

	if _lamp_mat:
		_lamp_mat.albedo_color = col
		_lamp_mat.emission_enabled = true
		_lamp_mat.emission = col
		_lamp_mat.emission_energy_multiplier = lamp_e
	if console_light:
		console_light.light_color = col
		console_light.light_energy = light_e


func set_trap_active(active: bool, immediate: bool = false) -> void:
	is_running = active
	flame_wall.visible = active
	flame_particles.emitting = active
	if not active:
		trap_light.light_energy = 0.0
		_panzer_tick_cd.clear()
		_player_tick_cd = 0.0
	else:
		run_timer = ACTIVE_DURATION
		trap_light.light_energy = 5.4
		_panzer_tick_cd.clear()
		_player_tick_cd = 0.0
	if _lever:
		var target_rot := 58.0 if active else 0.0
		if immediate:
			_lever.rotation_degrees.x = target_rot
		else:
			create_tween().tween_property(_lever, "rotation_degrees:x", target_rot, 0.25)
	_refresh_console_visuals()


func _process(delta: float) -> void:
	if is_running:
		run_timer -= delta
		trap_light.light_energy = 5.2 + sin(Time.get_ticks_msec() * 0.024) * 1.1
		_apply_fire_damage(delta)
		if run_timer <= 0.0:
			cooldown = COOLDOWN_DURATION
			set_trap_active(false)
	elif cooldown > 0.0:
		cooldown = maxf(0.0, cooldown - delta)
		if cooldown <= 0.0:
			_refresh_console_visuals()


func _apply_fire_damage(delta: float) -> void:
	_player_tick_cd = maxf(0.0, _player_tick_cd - delta)
	var to_erase: Array = []
	for kid in _panzer_tick_cd.keys():
		var nxt := float(_panzer_tick_cd[kid]) - delta
		if nxt <= 0.0:
			to_erase.append(kid)
		else:
			_panzer_tick_cd[kid] = nxt
	for kid in to_erase:
		_panzer_tick_cd.erase(kid)

	for body in kill_area.get_overlapping_bodies():
		if body.is_in_group("zombies") and body.has_method("take_damage"):
			if body is PanzerBossAI:
				var bid := body.get_instance_id()
				if not _panzer_tick_cd.has(bid):
					_panzer_tick_cd[bid] = PANZER_TICK_INTERVAL
					body.take_damage(PANZER_TICK_DAMAGE, false, body.global_position + Vector3(0.0, 1.0, 0.0), Vector3.UP)
			else:
				body.take_damage(99999.0, false, body.global_position, Vector3.UP)
		elif body.is_in_group("player") and body.has_method("take_damage"):
			if not GameManager.has_perk("phdflopper") and _player_tick_cd <= 0.0:
				_player_tick_cd = PLAYER_TICK_INTERVAL
				body.take_damage(PLAYER_BURN_DAMAGE, global_position + Vector3(3.85, 0.8, 0.0), true)


func get_interact_prompt(_player: Node) -> String:
	if not GameManager.power_on:
		return "Fire Trap — Power Must Be Turned On!"
	if is_running:
		return "Fire Trap Active! (%ds)" % int(ceilf(run_timer))
	if cooldown > 0.0:
		return "Fire Trap Cooling Down (%ds)..." % int(ceilf(cooldown))
	return "[E] Activate Fire Trap [Cost: %d]" % COST


func interact(_player: Node) -> void:
	if not GameManager.power_on or is_running or cooldown > 0.0:
		return
	if GameManager.spend_points(COST):
		set_trap_active(true)
		AudioManager.play_3d("explosion", global_position + Vector3(3.85, 0.5, 0.0), 0.15, -3.0, 32.0)

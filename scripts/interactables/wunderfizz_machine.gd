extends Node3D
class_name WunderfizzMachine

const COST := 1500
const SPIN_DURATION := 2.4
const TAKE_TIMEOUT := 9.0

enum FizzState { IDLE, SPINNING, READY_TAKE }

@onready var model_holder: Node3D = $ModelHolder
@onready var fizz_light: OmniLight3D = $OmniLight3D

var state: FizzState = FizzState.IDLE
var _orb_node: Node3D = null
var _tesla_ring: Node3D = null
var _spin_bottle: Node3D = null
var _orb_mat: StandardMaterial3D = null
var _bottle_mat: StandardMaterial3D = null

var _spin_timer: float = 0.0
var _cycle_timer: float = 0.0
var _take_timer: float = 0.0
var _spin_base_y: float = 1.48
var _chosen_perk: String = ""
var _last_paid_cost: int = COST
var _idle_color := Color(0.14, 0.92, 1.0)


func _ready() -> void:
	add_to_group("wunderfizz_machines")
	GameManager.power_activated.connect(_refresh_power_visuals)
	if ResourceLoader.exists("res://assets/models/props/der_wunderfizz.glb"):
		var inst := (load("res://assets/models/props/der_wunderfizz.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		_orb_node = inst.find_child("OrbNode", true, false) as Node3D
		_tesla_ring = inst.find_child("TeslaRing", true, false) as Node3D
		_spin_bottle = inst.find_child("SpinBottle", true, false) as Node3D
		if _spin_bottle:
			_spin_base_y = _spin_bottle.position.y
			_spin_bottle.visible = false
		_orb_mat = _duplicate_emissive_mat(_orb_node)
		_bottle_mat = _duplicate_emissive_mat(_spin_bottle)
	_refresh_power_visuals()


func _duplicate_emissive_mat(root: Node) -> StandardMaterial3D:
	if root == null:
		return null
	var queue: Array[Node] = [root]
	while not queue.is_empty():
		var n: Node = queue.pop_front()
		if n is MeshInstance3D:
			var mi := n as MeshInstance3D
			var mat := mi.get_active_material(0)
			if mat is StandardMaterial3D:
				var dup := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				mi.set_surface_override_material(0, dup)
				return dup
		for ch in n.get_children():
			queue.append(ch)
	return null


func _set_glow_color(col: Color, orb_energy: float = 2.4, bottle_energy: float = 1.7) -> void:
	if _orb_mat:
		_orb_mat.albedo_color = col
		_orb_mat.emission_enabled = true
		_orb_mat.emission = col
		_orb_mat.emission_energy_multiplier = orb_energy
	if _bottle_mat:
		_bottle_mat.albedo_color = col
		_bottle_mat.emission_enabled = true
		_bottle_mat.emission = col
		_bottle_mat.emission_energy_multiplier = bottle_energy
	if fizz_light:
		fizz_light.light_color = col


func _refresh_power_visuals() -> void:
	if fizz_light == null:
		return
	if not GameManager.power_on:
		fizz_light.light_energy = 0.25
		_set_glow_color(_idle_color, 0.35, 0.35)
		return
	match state:
		FizzState.IDLE:
			fizz_light.light_energy = 2.1
			_set_glow_color(_idle_color, 2.2, 1.4)
		FizzState.SPINNING:
			fizz_light.light_energy = 3.8
		FizzState.READY_TAKE:
			fizz_light.light_energy = 4.2


func _process(delta: float) -> void:
	if _orb_node:
		var spd := 6.5 if state == FizzState.SPINNING else (2.4 if GameManager.power_on else 0.35)
		_orb_node.rotate_y(delta * spd)
	if _tesla_ring:
		var rspd := -9.0 if state == FizzState.SPINNING else (-3.2 if GameManager.power_on else -0.4)
		_tesla_ring.rotate_y(delta * rspd)
		_tesla_ring.rotate_x(delta * rspd * 0.45)

	if state == FizzState.SPINNING:
		_spin_timer -= delta
		_cycle_timer -= delta
		if _spin_bottle:
			_spin_bottle.visible = true
			_spin_bottle.rotate_y(delta * 8.0)
			_spin_bottle.position.y = _spin_base_y + sin(_spin_timer * 10.0) * 0.05
		if _cycle_timer <= 0.0:
			_cycle_timer = 0.12
			var pool := GameManager.get_unowned_perks()
			if pool.is_empty():
				for k in GameManager.PERK_INFO.keys():
					pool.append(str(k))
			if not pool.is_empty():
				var preview_id: String = pool[randi() % pool.size()]
				var pcol: Color = GameManager.PERK_INFO.get(preview_id, {}).get("color", _idle_color)
				_set_glow_color(pcol, 2.8, 2.2)
		if _spin_timer <= 0.0:
			_finish_spin()
	elif state == FizzState.READY_TAKE:
		_take_timer -= delta
		if _spin_bottle:
			_spin_bottle.visible = true
			_spin_bottle.rotate_y(delta * 2.8)
			_spin_bottle.position.y = _spin_base_y + 0.06
		if _take_timer <= 0.0:
			_reset_to_idle()


func get_interact_prompt(_player: Node) -> String:
	if not GameManager.power_on:
		return "Der Wunderfizz — Power Must Be Turned On!"
	match state:
		FizzState.SPINNING:
			return "Der Wunderfizz Spinning..."
		FizzState.READY_TAKE:
			var pname := str(GameManager.PERK_INFO.get(_chosen_perk, {}).get("name", _chosen_perk))
			return "[E] Drink %s" % pname
		_:
			if GameManager.perks.size() >= GameManager.max_perks:
				return "Perk Limit Reached (%d/%d)" % [GameManager.perks.size(), GameManager.max_perks]
			if GameManager.get_unowned_perks().is_empty():
				return "All Perks Already Active!"
			return "[E] Der Wunderfizz [Cost: %d]" % COST


func interact(_player: Node) -> void:
	if not GameManager.power_on:
		return
	if state == FizzState.IDLE:
		if GameManager.perks.size() >= GameManager.max_perks:
			return
		var unowned := GameManager.get_unowned_perks()
		if unowned.is_empty():
			return
		if GameManager.spend_points(COST):
			_last_paid_cost = COST
			_start_spin(unowned)
	elif state == FizzState.READY_TAKE:
		if GameManager.can_buy_perk(_chosen_perk):
			var info: Dictionary = GameManager.PERK_INFO.get(_chosen_perk, {})
			if GameManager.grant_perk(_chosen_perk, true):
				GameManager.powerup_banner.emit("%s ACQUIRED!" % str(info.get("name", _chosen_perk)).to_upper(), info.get("color", _idle_color))
		else:
			GameManager.add_points(_last_paid_cost, "Wunderfizz Refund")
		_reset_to_idle()


func _start_spin(candidates: Array[String]) -> void:
	state = FizzState.SPINNING
	_spin_timer = SPIN_DURATION
	_cycle_timer = 0.0
	_chosen_perk = candidates[randi() % candidates.size()]
	if _spin_bottle:
		_spin_bottle.visible = true
	AudioManager.play_3d("mystery_box_jingle", global_position, 0.0, 0.0)
	_refresh_power_visuals()


func _finish_spin() -> void:
	if _chosen_perk == "" or GameManager.has_perk(_chosen_perk):
		var unowned := GameManager.get_unowned_perks()
		if unowned.is_empty():
			GameManager.add_points(_last_paid_cost, "Wunderfizz Refund")
			_reset_to_idle()
			return
		_chosen_perk = unowned[randi() % unowned.size()]

	state = FizzState.READY_TAKE
	_take_timer = TAKE_TIMEOUT
	var col: Color = GameManager.PERK_INFO.get(_chosen_perk, {}).get("color", _idle_color)
	_set_glow_color(col, 3.0, 2.5)
	if _spin_bottle:
		_spin_bottle.visible = true
		_spin_bottle.position.y = _spin_base_y + 0.06
	AudioManager.play_3d("powerup_collect", global_position, 0.05, 0.0)
	_refresh_power_visuals()


func _reset_to_idle() -> void:
	state = FizzState.IDLE
	_chosen_perk = ""
	if _spin_bottle:
		_spin_bottle.visible = false
		_spin_bottle.position.y = _spin_base_y
	_refresh_power_visuals()

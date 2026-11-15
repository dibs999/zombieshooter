extends Node3D
class_name QuestCanister

signal filled(canister: QuestCanister)

const REQUIRED_SOULS := 5
const CAPTURE_RADIUS := 6.5

@export var canister_index: int = 0

@onready var model_holder: Node3D = $ModelHolder
@onready var glow_light: OmniLight3D = $OmniLight3D

var is_active: bool = false
var is_filled: bool = false
var souls: int = 0

var _fill_core: Node3D = null
var _fill_mat: StandardMaterial3D = null


func _ready() -> void:
	add_to_group("quest_canisters")
	if ResourceLoader.exists("res://assets/models/props/quest_canister.glb"):
		var inst := (load("res://assets/models/props/quest_canister.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		_fill_core = inst.find_child("FillCore", true, false) as Node3D
		_fill_mat = _extract_fill_mat(_fill_core)
	_refresh_visuals()


func _extract_fill_mat(root: Node) -> StandardMaterial3D:
	if root == null:
		return null
	var stack: Array[Node] = [root]
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


func set_active(active: bool) -> void:
	is_active = active
	_refresh_visuals()


func reset_state() -> void:
	is_active = false
	is_filled = false
	souls = 0
	_refresh_visuals()


func can_absorb_soul_at(pos: Vector3) -> bool:
	if not is_active or is_filled:
		return false
	return global_position.distance_to(pos) <= CAPTURE_RADIUS


func add_soul() -> bool:
	if not is_active or is_filled:
		return false
	souls = mini(REQUIRED_SOULS, souls + 1)
	AudioManager.play_3d("perk_drink" if souls >= REQUIRED_SOULS else "hitmarker", global_position, 0.08, -2.0, 28.0)
	if souls >= REQUIRED_SOULS:
		is_filled = true
		_refresh_visuals()
		emit_signal("filled", self)
	else:
		_refresh_visuals()
	return true


func _refresh_visuals() -> void:
	var ratio := clampf(float(souls) / float(REQUIRED_SOULS), 0.0, 1.0)
	if _fill_core:
		_fill_core.scale.y = maxf(0.04, ratio)
		_fill_core.visible = is_active or souls > 0
	var col := Color(0.16, 0.88, 1.0)
	var em_energy := 0.3
	var light_e := 0.25
	if is_filled:
		col = Color(0.24, 1.0, 0.56)
		em_energy = 2.8
		light_e = 2.6
	elif is_active:
		col = Color(0.18, 0.90, 1.0)
		em_energy = 1.2 + ratio * 1.4
		light_e = 1.2 + ratio * 1.1

	if _fill_mat:
		_fill_mat.albedo_color = col
		_fill_mat.emission_enabled = true
		_fill_mat.emission = col
		_fill_mat.emission_energy_multiplier = em_energy
	if glow_light:
		glow_light.light_color = col
		glow_light.light_energy = light_e

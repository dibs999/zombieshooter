extends Node3D
class_name QuestResonator

signal attuned(resonator: QuestResonator)

@export var resonator_index: int = 0

@onready var model_holder: Node3D = $ModelHolder
@onready var hit_area: Area3D = $HitArea
@onready var glow_light: OmniLight3D = $OmniLight3D

var is_active: bool = false
var is_attuned: bool = false

var _crystal: Node3D = null
var _crystal_mat: StandardMaterial3D = null


func _ready() -> void:
	add_to_group("quest_resonators")
	if ResourceLoader.exists("res://assets/models/props/quest_resonator.glb"):
		var inst := (load("res://assets/models/props/quest_resonator.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		_crystal = inst.find_child("SpireCrystal", true, false) as Node3D
		_crystal_mat = _extract_crystal_mat(_crystal)
	_refresh_visuals()


func _extract_crystal_mat(root: Node) -> StandardMaterial3D:
	if root == null:
		return null
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var cur: Node = stack.pop_back()
		if cur is MeshInstance3D:
			var mi := cur as MeshInstance3D
			var mat := mi.get_active_material(0)
			if mat is StandardMaterial3D and (mat as StandardMaterial3D).emission_enabled:
				var dup := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				mi.set_surface_override_material(0, dup)
				return dup
		for ch in cur.get_children():
			stack.append(ch)
	return null


func _process(delta: float) -> void:
	if _crystal:
		var spd := 3.6 if is_attuned else (1.8 if is_active else 0.45)
		_crystal.rotate_y(delta * spd)


func set_active(active: bool) -> void:
	is_active = active
	_refresh_visuals()


func reset_state() -> void:
	is_active = false
	is_attuned = false
	_refresh_visuals()


func trigger_quest_hit() -> void:
	if not is_active or is_attuned:
		return
	is_attuned = true
	_refresh_visuals()
	AudioManager.play_3d("powerup_collect", global_position, 0.08, 2.0, 40.0)
	emit_signal("attuned", self)


func _refresh_visuals() -> void:
	if hit_area:
		hit_area.collision_layer = 16 if (is_active and not is_attuned) else 0
	var col := Color(0.55, 0.34, 0.14)
	var em_energy := 0.45
	var light_e := 0.35
	if is_attuned:
		col = Color(0.18, 0.94, 1.0)
		em_energy = 3.2
		light_e = 2.6
	elif is_active:
		col = Color(1.0, 0.56, 0.12)
		em_energy = 2.4
		light_e = 1.9

	if _crystal_mat:
		_crystal_mat.albedo_color = col
		_crystal_mat.emission_enabled = true
		_crystal_mat.emission = col
		_crystal_mat.emission_energy_multiplier = em_energy
	if glow_light:
		glow_light.light_color = col
		glow_light.light_energy = light_e

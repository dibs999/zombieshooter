extends Node3D
class_name BloodDecal

const MAX_ACTIVE_DECALS := 24
static var _active_decals: Array[Node] = []

@onready var quad_mesh: MeshInstance3D = $Quad

var _age: float = 0.0
var _lifetime: float = 22.0
var _target_scale: float = 1.0
var _mat: StandardMaterial3D = null


func setup(p_scale: float = 1.0) -> void:
	_target_scale = p_scale
	rotation.y = randf_range(0.0, TAU)
	scale = Vector3(0.25 * _target_scale, 1.0, 0.25 * _target_scale)


func _ready() -> void:
	_active_decals = _active_decals.filter(func(n): return is_instance_valid(n))
	_active_decals.append(self)
	while _active_decals.size() > MAX_ACTIVE_DECALS:
		var old: Node = _active_decals.pop_front()
		if is_instance_valid(old) and old != self:
			old.queue_free()

	global_position.y = maxf(0.012, global_position.y + 0.012)
	if quad_mesh:
		_mat = StandardMaterial3D.new()
		_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		_mat.roughness = 0.14
		_mat.metallic = 0.05
		_mat.albedo_color = Color(0.85, 0.85, 0.85, 0.92)
		if ResourceLoader.exists("res://assets/textures/characters/blood_pool_decal.png"):
			_mat.albedo_texture = load("res://assets/textures/characters/blood_pool_decal.png")
		else:
			_mat.albedo_color = Color(0.32, 0.02, 0.02, 0.85)
		quad_mesh.material_override = _mat

	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3(_target_scale, 1.0, _target_scale), 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func _process(delta: float) -> void:
	_age += delta
	if _age >= _lifetime:
		queue_free()
		return
	if _age > _lifetime - 2.5 and _mat != null:
		_mat.albedo_color.a = clampf((_lifetime - _age) / 2.5, 0.0, 0.92)

extends Node3D
class_name BloodDecal

const MAX_ACTIVE_DECALS := 16
static var _active_decals: Array[Node] = []
static var _shared_mat: StandardMaterial3D = null

@onready var quad_mesh: MeshInstance3D = $Quad

var _age: float = 0.0
var _lifetime: float = 22.0
var _target_scale: float = 1.0


static func _get_shared_mat() -> StandardMaterial3D:
	if _shared_mat == null:
		var m := StandardMaterial3D.new()
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.roughness = 0.14
		m.metallic = 0.05
		m.albedo_color = Color(0.85, 0.85, 0.85, 0.92)
		if ResourceLoader.exists("res://assets/textures/characters/blood_pool_decal.png"):
			m.albedo_texture = load("res://assets/textures/characters/blood_pool_decal.png")
		else:
			m.albedo_color = Color(0.32, 0.02, 0.02, 0.85)
		_shared_mat = m
	return _shared_mat


var _wall_mode: bool = false


func setup(p_scale: float = 1.0, wall_mode: bool = false) -> void:
	_target_scale = p_scale
	_wall_mode = wall_mode
	if not wall_mode:
		rotation.y = randf_range(0.0, TAU)
	scale = Vector3(0.25 * _target_scale, 1.0, 0.25 * _target_scale)


func _ready() -> void:
	for i in range(_active_decals.size() - 1, -1, -1):
		if not is_instance_valid(_active_decals[i]):
			_active_decals.remove_at(i)
	_active_decals.append(self)
	while _active_decals.size() > MAX_ACTIVE_DECALS:
		var old: Node = _active_decals.pop_front()
		if is_instance_valid(old) and old != self:
			old.queue_free()

	if not _wall_mode:
		global_position.y = maxf(0.012, global_position.y + 0.012)
	if quad_mesh:
		quad_mesh.material_override = _get_shared_mat()
		quad_mesh.transparency = 0.0

	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3(_target_scale, 1.0, _target_scale), 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func _exit_tree() -> void:
	_active_decals.erase(self)


static func clear_shared_caches() -> void:
	for d in _active_decals:
		if is_instance_valid(d) and not d.is_inside_tree() and not d.is_queued_for_deletion():
			d.free()
	_active_decals.clear()
	_shared_mat = null


func _process(delta: float) -> void:
	_age += delta
	if _age >= _lifetime:
		queue_free()
		return
	if _age > _lifetime - 2.5 and quad_mesh != null:
		quad_mesh.transparency = clampf(1.0 - (_lifetime - _age) / 2.5, 0.0, 1.0)

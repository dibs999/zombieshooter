extends Node3D
class_name GibChunk

const MAX_ACTIVE_GIBS := 18
static var _active_gibs: Array[Node] = []
static var _mesh_armor: BoxMesh = null
static var _mesh_skull: SphereMesh = null
static var _mesh_flesh: SphereMesh = null
static var _mat_armor: StandardMaterial3D = null
static var _mat_skull: StandardMaterial3D = null
static var _mat_flesh: StandardMaterial3D = null

@onready var mesh_inst: MeshInstance3D = $MeshInstance3D

var _vel: Vector3 = Vector3.ZERO
var _ang_vel: Vector3 = Vector3.ZERO
var _age: float = 0.0
var _lifetime: float = 3.8
var _settled: bool = false
var _bounces: int = 0


static func _ensure_shared_assets() -> void:
	if _mesh_armor == null:
		_mesh_armor = BoxMesh.new()
		_mesh_armor.size = Vector3(0.18, 0.04, 0.18)
	if _mesh_skull == null:
		_mesh_skull = SphereMesh.new()
		_mesh_skull.radius = 0.075
		_mesh_skull.height = 0.12
		_mesh_skull.radial_segments = 8
		_mesh_skull.rings = 5
	if _mesh_flesh == null:
		_mesh_flesh = SphereMesh.new()
		_mesh_flesh.radius = 0.072
		_mesh_flesh.height = 0.125
		_mesh_flesh.radial_segments = 7
		_mesh_flesh.rings = 4
	if _mat_armor == null:
		_mat_armor = StandardMaterial3D.new()
		var arm_tex := _load_char_tex("panzer_armor_albedo")
		if arm_tex != null:
			_mat_armor.albedo_texture = arm_tex
		else:
			_mat_armor.albedo_color = Color(0.28, 0.26, 0.24)
		_mat_armor.metallic = 0.82
		_mat_armor.roughness = 0.42
	if _mat_skull == null:
		_mat_skull = StandardMaterial3D.new()
		_mat_skull.albedo_color = Color(0.68, 0.52, 0.42)
		_mat_skull.roughness = 0.48
	if _mat_flesh == null:
		_mat_flesh = StandardMaterial3D.new()
		var gore_alb := _load_char_tex("gore_flesh_albedo")
		if gore_alb != null:
			_mat_flesh.albedo_texture = gore_alb
		else:
			_mat_flesh.albedo_color = Color(0.45, 0.04, 0.04)
		var gore_nor := _load_char_tex("gore_flesh_normal")
		if gore_nor != null:
			_mat_flesh.normal_enabled = true
			_mat_flesh.normal_texture = gore_nor
		_mat_flesh.roughness = 0.22


func setup(kind: String, impulse: Vector3) -> void:
	_vel = impulse
	_ang_vel = Vector3(
		randf_range(-11.0, 11.0),
		randf_range(-11.0, 11.0),
		randf_range(-11.0, 11.0)
	)
	if mesh_inst == null:
		mesh_inst = get_node_or_null("MeshInstance3D") as MeshInstance3D
	if mesh_inst == null:
		return

	_ensure_shared_assets()
	match kind:
		"armor":
			mesh_inst.mesh = _mesh_armor
			mesh_inst.material_override = _mat_armor
			mesh_inst.scale = Vector3(randf_range(0.78, 1.32), randf_range(0.75, 1.25), randf_range(0.78, 1.32))
		"skull":
			mesh_inst.mesh = _mesh_skull
			mesh_inst.material_override = _mat_skull
			var s := randf_range(0.80, 1.26)
			mesh_inst.scale = Vector3(s, s * randf_range(0.88, 1.22), s)
		_:
			mesh_inst.mesh = _mesh_flesh
			mesh_inst.material_override = _mat_flesh
			var sf := randf_range(0.76, 1.32)
			mesh_inst.scale = Vector3(sf, sf * randf_range(0.9, 1.3), sf)


static func _load_char_tex(stem: String) -> Texture2D:
	for ext in [".jpg", ".png"]:
		var p := "res://assets/textures/characters/%s%s" % [stem, ext]
		if ResourceLoader.exists(p):
			return load(p) as Texture2D
	return null


func _ready() -> void:
	for i in range(_active_gibs.size() - 1, -1, -1):
		if not is_instance_valid(_active_gibs[i]):
			_active_gibs.remove_at(i)
	_active_gibs.append(self)
	while _active_gibs.size() > MAX_ACTIVE_GIBS:
		var old: Node = _active_gibs.pop_front()
		if is_instance_valid(old) and old != self:
			old.queue_free()


func _exit_tree() -> void:
	_active_gibs.erase(self)


static func clear_shared_caches() -> void:
	for g in _active_gibs:
		if is_instance_valid(g) and not g.is_inside_tree() and not g.is_queued_for_deletion():
			g.free()
	_active_gibs.clear()
	_mesh_armor = null
	_mesh_skull = null
	_mesh_flesh = null
	_mat_armor = null
	_mat_skull = null
	_mat_flesh = null


func _process(delta: float) -> void:
	_age += delta
	if _age >= _lifetime:
		queue_free()
		return

	if not _settled:
		_vel.y -= 16.5 * delta
		global_position += _vel * delta
		rotation += _ang_vel * delta
		if global_position.y <= 0.055:
			global_position.y = 0.055
			if _bounces < 2 and absf(_vel.y) > 1.2:
				_vel.y = absf(_vel.y) * 0.34
				_vel.x *= 0.55
				_vel.z *= 0.55
				_ang_vel *= 0.5
				_bounces += 1
			else:
				_vel = Vector3.ZERO
				_ang_vel = Vector3.ZERO
				_settled = true
	elif _age > _lifetime - 0.7:
		var t := clampf((_lifetime - _age) / 0.7, 0.0, 1.0)
		scale = Vector3.ONE * maxf(0.05, t)

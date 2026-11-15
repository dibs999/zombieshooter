extends Node3D
class_name GibChunk

const MAX_ACTIVE_GIBS := 28
static var _active_gibs: Array[Node] = []

@onready var mesh_inst: MeshInstance3D = $MeshInstance3D

var _vel: Vector3 = Vector3.ZERO
var _ang_vel: Vector3 = Vector3.ZERO
var _age: float = 0.0
var _lifetime: float = 3.8
var _settled: bool = false
var _bounces: int = 0


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

	var mat := StandardMaterial3D.new()
	match kind:
		"armor":
			var box := BoxMesh.new()
			box.size = Vector3(randf_range(0.14, 0.24), randf_range(0.03, 0.05), randf_range(0.14, 0.24))
			mesh_inst.mesh = box
			var arm_tex := _load_char_tex("panzer_armor_albedo")
			if arm_tex != null:
				mat.albedo_texture = arm_tex
			else:
				mat.albedo_color = Color(0.28, 0.26, 0.24)
			mat.metallic = 0.82
			mat.roughness = 0.42
		"skull":
			var sph := SphereMesh.new()
			sph.radius = randf_range(0.06, 0.095)
			sph.height = sph.radius * randf_range(1.4, 1.9)
			sph.radial_segments = 8
			sph.rings = 5
			mesh_inst.mesh = sph
			mat.albedo_color = Color(0.68, 0.52, 0.42)
			mat.roughness = 0.48
		_:
			var chunk := SphereMesh.new()
			chunk.radius = randf_range(0.055, 0.095)
			chunk.height = chunk.radius * randf_range(1.5, 2.2)
			chunk.radial_segments = 7
			chunk.rings = 4
			mesh_inst.mesh = chunk
			var gore_alb := _load_char_tex("gore_flesh_albedo")
			if gore_alb != null:
				mat.albedo_texture = gore_alb
			else:
				mat.albedo_color = Color(0.45, 0.04, 0.04)
			var gore_nor := _load_char_tex("gore_flesh_normal")
			if gore_nor != null:
				mat.normal_enabled = true
				mat.normal_texture = gore_nor
			mat.roughness = 0.22
	mesh_inst.material_override = mat


func _load_char_tex(stem: String) -> Texture2D:
	for ext in [".jpg", ".png"]:
		var p := "res://assets/textures/characters/%s%s" % [stem, ext]
		if ResourceLoader.exists(p):
			return load(p) as Texture2D
	return null


func _ready() -> void:
	_active_gibs = _active_gibs.filter(func(n): return is_instance_valid(n))
	_active_gibs.append(self)
	while _active_gibs.size() > MAX_ACTIVE_GIBS:
		var old: Node = _active_gibs.pop_front()
		if is_instance_valid(old) and old != self:
			old.queue_free()


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

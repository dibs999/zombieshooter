extends Node3D
class_name WpnShellCasing

@onready var mesh_inst: MeshInstance3D = $MeshInstance3D

var _vel: Vector3 = Vector3.ZERO
var _ang_vel: Vector3 = Vector3.ZERO
var _age: float = 0.0
var _floor_y: float = 0.02
var _clinked: bool = false
var _is_shotgun: bool = false

const GRAVITY := 12.5
const MAX_LIFE := 1.6
const MAX_SHELLS := 14

static var _active_shells: Array[Node] = []
static var _shotgun_hull_mesh: CylinderMesh = null


static func clear_shared_caches() -> void:
	for s in _active_shells:
		if is_instance_valid(s) and not s.is_inside_tree() and not s.is_queued_for_deletion():
			s.free()
	_active_shells.clear()
	_shotgun_hull_mesh = null


static func _get_shotgun_hull_mesh() -> CylinderMesh:
	if _shotgun_hull_mesh == null:
		var hull := CylinderMesh.new()
		hull.top_radius = 0.0095
		hull.bottom_radius = 0.0095
		hull.height = 0.056
		hull.radial_segments = 8
		hull.rings = 1
		var red_mat := StandardMaterial3D.new()
		red_mat.albedo_color = Color(0.68, 0.08, 0.08)
		red_mat.roughness = 0.45
		red_mat.metallic = 0.15
		hull.material = red_mat
		_shotgun_hull_mesh = hull
	return _shotgun_hull_mesh


func setup(eject_vel: Vector3, start_basis: Basis, shotgun_hull: bool = false) -> void:
	_vel = eject_vel
	_is_shotgun = shotgun_hull
	global_transform.basis = start_basis
	_ang_vel = Vector3(randf_range(-18.0, 18.0), randf_range(-14.0, 14.0), randf_range(-24.0, 24.0))
	if shotgun_hull and mesh_inst:
		mesh_inst.mesh = _get_shotgun_hull_mesh()


func _ready() -> void:
	for i in range(_active_shells.size() - 1, -1, -1):
		if not is_instance_valid(_active_shells[i]):
			_active_shells.remove_at(i)
	_active_shells.append(self)
	while _active_shells.size() > MAX_SHELLS:
		var old := _active_shells.pop_front() as Node
		if is_instance_valid(old) and old != self:
			old.queue_free()

	_floor_y = global_position.y - 1.55
	var w3d := get_world_3d()
	if w3d:
		var space := w3d.direct_space_state
		if space:
			var q := PhysicsRayQueryParameters3D.create(global_position, global_position + Vector3.DOWN * 6.0)
			q.collision_mask = 1
			var hit := space.intersect_ray(q)
			if not hit.is_empty():
				_floor_y = (hit["position"] as Vector3).y + 0.012


func _exit_tree() -> void:
	_active_shells.erase(self)


func _process(delta: float) -> void:
	_age += delta
	if _age >= MAX_LIFE:
		queue_free()
		return

	if _vel == Vector3.ZERO and _ang_vel == Vector3.ZERO:
		return

	_vel.y -= GRAVITY * delta
	global_position += _vel * delta
	rotation += _ang_vel * delta

	if global_position.y <= _floor_y:
		global_position.y = _floor_y
		if absf(_vel.y) > 0.65:
			_vel.y = absf(_vel.y) * 0.42
			_vel.x *= 0.58
			_vel.z *= 0.58
			_ang_vel *= 0.65
			if not _clinked:
				_clinked = true
				AudioManager.play_3d("shell_clink", global_position, 0.14, -10.0, 10.0)
		else:
			_vel = Vector3.ZERO
			_ang_vel = Vector3.ZERO

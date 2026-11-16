extends Decal
class_name WpnBulletDecal

static var _active_decals: Array[Decal] = []
const MAX_DECALS := 24

static var _tex_concrete: Texture2D = null
static var _tex_metal: Texture2D = null


static func _get_decal_texture(is_metal: bool) -> Texture2D:
	if is_metal:
		if _tex_metal == null:
			_tex_metal = load("res://assets/textures/weapons/bullet_hole_metal.png") as Texture2D
		return _tex_metal
	if _tex_concrete == null:
		_tex_concrete = load("res://assets/textures/weapons/bullet_hole_concrete.png") as Texture2D
	return _tex_concrete


static func clear_shared_caches() -> void:
	for d in _active_decals:
		if is_instance_valid(d) and not d.is_inside_tree() and not d.is_queued_for_deletion():
			d.free()
	_active_decals.clear()
	_tex_concrete = null
	_tex_metal = null


func setup(hit_pos: Vector3, hit_normal: Vector3, is_metal: bool = false) -> void:
	texture_albedo = _get_decal_texture(is_metal)
	distance_fade_enabled = true
	distance_fade_begin = 18.0
	distance_fade_length = 6.0
	var s := randf_range(0.085, 0.125)
	size = Vector3(s, 0.10, s)
	global_position = hit_pos + hit_normal * 0.012

	var n := hit_normal.normalized()
	if n.length_squared() < 0.01:
		n = Vector3.UP
	var up_ref := Vector3.FORWARD if absf(n.y) > 0.96 else Vector3.UP
	var x_axis := up_ref.cross(n).normalized()
	var z_axis := n.cross(x_axis).normalized()
	# Decal projects along -Y in local space, so +Y points outward along surface normal
	global_transform.basis = Basis(x_axis, n, z_axis)
	rotate_object_local(Vector3.UP, randf_range(0.0, TAU))

	for i in range(_active_decals.size() - 1, -1, -1):
		if not is_instance_valid(_active_decals[i]):
			_active_decals.remove_at(i)

	_active_decals.append(self)
	while _active_decals.size() > MAX_DECALS:
		var oldest := _active_decals.pop_front() as Decal
		if is_instance_valid(oldest) and oldest != self:
			oldest.queue_free()

	var tw := create_tween()
	tw.tween_interval(8.5)
	tw.tween_property(self, "modulate:a", 0.0, 1.5)
	tw.tween_callback(_cleanup)


func _exit_tree() -> void:
	_active_decals.erase(self)


func _cleanup() -> void:
	_active_decals.erase(self)
	if is_instance_valid(self) and not is_queued_for_deletion():
		queue_free()

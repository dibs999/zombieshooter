extends Node3D

@onready var light: OmniLight3D = $OmniLight3D

var _mat_core: StandardMaterial3D
var _mat_glow: StandardMaterial3D
var _segments_root: Node3D
var _tween: Tween
var _arc_color: Color = Color(0.28, 0.94, 1.0)


func setup(from_pos: Vector3, to_pos: Vector3, arc_color: Color = Color(0.28, 0.94, 1.0), hold_for_capture: bool = false) -> void:
	global_position = from_pos
	_arc_color = arc_color
	var delta := to_pos - from_pos
	var dist := delta.length()
	if dist < 0.05:
		queue_free()
		return

	_segments_root = Node3D.new()
	add_child(_segments_root)

	_mat_core = StandardMaterial3D.new()
	_mat_core.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_core.albedo_color = Color(0.94, 0.99, 1.0, 1.0)
	_mat_core.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat_core.emission_enabled = true
	_mat_core.emission = Color(0.95, 1.0, 1.0)
	_mat_core.emission_energy_multiplier = 3.6

	_mat_glow = StandardMaterial3D.new()
	_mat_glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_glow.albedo_color = Color(arc_color.r, arc_color.g, arc_color.b, 0.72)
	_mat_glow.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat_glow.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_mat_glow.emission_enabled = true
	_mat_glow.emission = arc_color
	_mat_glow.emission_energy_multiplier = 2.8

	var steps := clampi(int(ceilf(dist / 0.55)), 4, 10)
	var fwd := delta.normalized()
	var up_ref := Vector3.UP if absf(fwd.y) < 0.9 else Vector3.RIGHT
	var side_a := fwd.cross(up_ref).normalized()
	var side_b := fwd.cross(side_a).normalized()

	var pts: Array[Vector3] = [Vector3.ZERO]
	for i in range(1, steps):
		var t := float(i) / float(steps)
		var base_p := delta * t
		var jitter_amp := minf(0.28, dist * 0.09) * sin(t * PI)
		var offset := side_a * randf_range(-jitter_amp, jitter_amp) + side_b * randf_range(-jitter_amp, jitter_amp)
		pts.append(base_p + offset)
	pts.append(delta)

	for i in range(pts.size() - 1):
		_add_seg(pts[i], pts[i + 1], 0.022, _mat_core)
		_add_seg(pts[i], pts[i + 1], 0.056, _mat_glow)

	if pts.size() >= 4:
		var fork_idx := clampi(pts.size() / 2 + randi_range(-1, 0), 1, pts.size() - 2)
		var fork_origin := pts[fork_idx]
		var fork_dir := (fwd * randf_range(0.35, 0.75) + side_a * randf_range(-0.85, 0.85) + side_b * randf_range(-0.65, 0.65)).normalized()
		var fork_len := clampf(dist * 0.24, 0.28, 0.72)
		var fork_mid := fork_origin + fork_dir * (fork_len * 0.5) + side_b * randf_range(-0.10, 0.10)
		var fork_end := fork_origin + fork_dir * fork_len + side_a * randf_range(-0.12, 0.12)
		_add_seg(fork_origin, fork_mid, 0.013, _mat_core)
		_add_seg(fork_origin, fork_mid, 0.034, _mat_glow)
		_add_seg(fork_mid, fork_end, 0.009, _mat_core)
		_add_seg(fork_mid, fork_end, 0.024, _mat_glow)

	if light:
		light.global_position = (from_pos + to_pos) * 0.5
		light.light_color = arc_color
		light.light_energy = 4.5

	if not hold_for_capture:
		_tween = create_tween()
		_tween.set_parallel(true)
		_tween.tween_property(_mat_core, "albedo_color:a", 0.0, 0.28)
		_tween.tween_property(_mat_glow, "albedo_color:a", 0.0, 0.28)
		if light:
			_tween.tween_property(light, "light_energy", 0.0, 0.28)
		_tween.set_parallel(false)
		_tween.tween_callback(queue_free)


func pause_decay() -> void:
	if _tween and _tween.is_valid():
		_tween.kill()
	_tween = null
	if _mat_core:
		_mat_core.albedo_color = Color(0.94, 0.99, 1.0, 1.0)
	if _mat_glow:
		_mat_glow.albedo_color = Color(_arc_color.r, _arc_color.g, _arc_color.b, 0.72)
	if light:
		light.light_energy = 4.5


func _add_seg(a: Vector3, b: Vector3, radius: float, mat: Material) -> void:
	var diff := b - a
	var seg_len := diff.length()
	if seg_len < 0.005:
		return
	var mi := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = radius
	cyl.bottom_radius = radius
	cyl.height = seg_len
	cyl.radial_segments = 5
	cyl.rings = 1
	cyl.material = mat
	mi.mesh = cyl
	_segments_root.add_child(mi)
	mi.position = (a + b) * 0.5
	var dir := diff.normalized()
	var up := Vector3.FORWARD if absf(dir.dot(Vector3.UP)) > 0.98 else Vector3.UP
	var basis := Basis.looking_at(dir, up)
	mi.basis = basis * Basis(Vector3.RIGHT, PI * 0.5)

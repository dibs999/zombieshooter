extends Node3D

@export var max_scale: float = 5.5
@export var duration: float = 0.42
@export var ring_color: Color = Color(0.75, 0.25, 1.0)

@onready var ring: MeshInstance3D = $Ring
@onready var flash: OmniLight3D = $Flash


func _ready() -> void:
	for c in get_children():
		if c is CPUParticles3D:
			(c as CPUParticles3D).emitting = true

	if ring:
		ring.scale = Vector3(0.35, 0.35, 0.35)
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(ring_color.r, ring_color.g, ring_color.b, 0.88)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		ring.material_override = mat

		var tw := create_tween()
		tw.set_parallel(true)
		tw.tween_property(ring, "scale", Vector3(max_scale, 1.0, max_scale), duration).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(mat, "albedo_color:a", 0.0, duration)
		if flash:
			flash.light_color = ring_color
			tw.tween_property(flash, "light_energy", 0.0, duration)
		tw.set_parallel(false)
		tw.tween_callback(queue_free)
	else:
		get_tree().create_timer(duration).timeout.connect(queue_free)

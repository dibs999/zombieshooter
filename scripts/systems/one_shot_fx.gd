extends Node3D

@export var lifetime: float = 0.85


func _ready() -> void:
	for c in get_children():
		if c is CPUParticles3D:
			(c as CPUParticles3D).emitting = true
		elif c is OmniLight3D:
			var l := c as OmniLight3D
			var tw := l.create_tween()
			tw.tween_property(l, "light_energy", 0.0, 0.25)
	get_tree().create_timer(lifetime).timeout.connect(queue_free)

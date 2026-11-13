extends RigidBody3D

var fuse: float = 2.2
var explosion_fx_scene: PackedScene = preload("res://scenes/fx/explosion_fx.tscn")


func _ready() -> void:
	if ResourceLoader.exists("res://assets/models/weapons/frag_grenade.glb"):
		var m := (load("res://assets/models/weapons/frag_grenade.glb") as PackedScene).instantiate()
		add_child(m)


func _process(delta: float) -> void:
	fuse -= delta
	if fuse <= 0.0:
		_detonate()


func _detonate() -> void:
	AudioManager.play_3d("explosion", global_position, 0.05, 3.0)
	var fx := explosion_fx_scene.instantiate() as Node3D
	get_tree().current_scene.add_child(fx)
	fx.global_position = global_position

	var dmg_base := 550.0 + float(GameManager.current_round) * 65.0
	for z in get_tree().get_nodes_in_group("zombies"):
		var d: float = (z as Node3D).global_position.distance_to(global_position)
		if d <= 5.5 and z.has_method("take_damage"):
			var falloff: float = 1.0 - (d / 6.0)
			z.take_damage(dmg_base * falloff, false, (z as Node3D).global_position, ((z as Node3D).global_position - global_position).normalized())

	queue_free()

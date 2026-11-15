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
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	target_parent.add_child(fx)
	fx.global_position = global_position

	var dmg_base := 550.0 + float(GameManager.current_round) * 65.0
	for z in get_tree().get_nodes_in_group("zombies"):
		var z3 := z as Node3D
		if z3 == null:
			continue
		var d: float = z3.global_position.distance_to(global_position)
		if d <= 5.5 and z.has_method("take_damage"):
			var falloff: float = 1.0 - (d / 6.0)
			z.take_damage(dmg_base * falloff, false, z3.global_position, (z3.global_position - global_position).normalized())

	# Frag splash hurts player close-up unless PhD Flopper blocks explosive self-damage
	for p in get_tree().get_nodes_in_group("player"):
		var p3 := p as Node3D
		if p3 == null:
			continue
		var pd := p3.global_position.distance_to(global_position)
		if pd <= 2.9 and p.has_method("take_damage"):
			var self_dmg := clampf((1.0 - pd / 3.1) * 38.0, 8.0, 32.0)
			p.take_damage(self_dmg, global_position, true)

	queue_free()

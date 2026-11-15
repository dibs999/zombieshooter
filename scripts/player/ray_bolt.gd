extends Node3D

var dir: Vector3 = Vector3.FORWARD
var speed: float = 42.0
var damage: float = 750.0
var radius: float = 3.6
var lifetime: float = 3.0
var player_ref: Node = null
var explosion_fx_scene: PackedScene = preload("res://scenes/fx/explosion_fx.tscn")


func setup(p_dir: Vector3, p_damage: float, p_radius: float, color: Color, p_player: Node) -> void:
	dir = p_dir.normalized()
	damage = p_damage
	radius = p_radius
	player_ref = p_player
	if has_node("MeshInstance3D"):
		var mi := $MeshInstance3D as MeshInstance3D
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = color
		mat.emission_enabled = true
		mat.emission = color
		mat.emission_energy_multiplier = 2.6
		mi.material_override = mat
	if has_node("OmniLight3D"):
		($OmniLight3D as OmniLight3D).light_color = color
	if has_node("TrailParticles"):
		var tp := $TrailParticles as CPUParticles3D
		tp.color = color
		tp.emitting = true


func _physics_process(delta: float) -> void:
	lifetime -= delta
	if lifetime <= 0.0:
		queue_free()
		return
	var step := dir * speed * delta
	var space := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(global_position, global_position + step)
	query.collision_mask = 1 | 4 | 8 | 16
	query.collide_with_areas = true
	query.collide_with_bodies = true
	var exclude_list: Array[RID] = []
	if player_ref and player_ref is CollisionObject3D:
		exclude_list.append((player_ref as CollisionObject3D).get_rid())

	for _step in range(12):
		query.exclude = exclude_list
		var res := space.intersect_ray(query)
		if res.is_empty():
			break
		var col: Object = res["collider"]
		if _try_trigger_quest(col):
			_explode(res["position"])
			return
		var col_layer := 0
		if col is CollisionObject3D:
			col_layer = (col as CollisionObject3D).collision_layer
		if (col_layer & 16) != 0 and not (col is Node and ((col as Node).is_in_group("zombies") or (col as Node).is_in_group("zombie_head"))):
			if col is CollisionObject3D:
				exclude_list.append((col as CollisionObject3D).get_rid())
				continue
		_explode(res["position"])
		return
	global_position += step


func _try_trigger_quest(col: Object) -> bool:
	if col == null:
		return false
	if col.has_method("trigger_quest_hit"):
		col.trigger_quest_hit()
		return true
	if col is Node:
		var p := (col as Node).get_parent()
		if p != null and p.has_method("trigger_quest_hit"):
			p.trigger_quest_hit()
			return true
	return false


func _explode(pos: Vector3) -> void:
	AudioManager.play_3d("explosion", pos, 0.08, -2.0)
	var fx := explosion_fx_scene.instantiate() as Node3D
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	target_parent.add_child(fx)
	fx.global_position = pos

	var hit_any := false
	var killed_any := false
	for z in get_tree().get_nodes_in_group("zombies"):
		var z3 := z as Node3D
		if z3 == null:
			continue
		var d: float = z3.global_position.distance_to(pos)
		if d <= radius and z.has_method("take_damage"):
			var falloff: float = clampf(1.0 - (d / (radius * 1.15)), 0.35, 1.0)
			var k: bool = z.take_damage(damage * falloff, false, z3.global_position, (z3.global_position - pos).normalized())
			hit_any = true
			killed_any = killed_any or k

	# Explosive splash hurts player at close range UNLESS PhD Flopper is owned!
	if player_ref != null and is_instance_valid(player_ref) and player_ref is Node3D:
		var pd: float = (player_ref as Node3D).global_position.distance_to(pos)
		if pd <= minf(radius, 3.2):
			var self_dmg := clampf((1.0 - pd / 3.4) * 32.0, 6.0, 28.0)
			if player_ref.has_method("take_damage"):
				player_ref.take_damage(self_dmg, pos, true)

	if hit_any:
		AudioManager.play_2d("hitmarker", 0.05, -4.0)
		GameManager.hitmarker_triggered.emit(killed_any, false)
	queue_free()

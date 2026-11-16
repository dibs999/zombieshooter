extends CharacterBody3D
class_name ZombieAI

enum State { APPROACHING_WINDOW, BREAKING_BARRIER, VAULTING, CHASING, DEAD }

@onready var nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var head_area: Area3D = $HeadArea
@onready var body_area: Area3D = $BodyArea
@onready var model_root: Node3D = $ModelRoot

var variant: String = "soldier"
var max_hp: float = 150.0
var hp: float = 150.0
var move_speed: float = 2.1
var attack_damage: float = 45.0
var is_sprinter: bool = false
var is_brute: bool = false
var is_crawler: bool = false

var state: State = State.CHASING
var target_window: Node = null
var vault_progress: float = 0.0
var vault_start: Vector3 = Vector3.ZERO
var vault_mid: Vector3 = Vector3.ZERO
var vault_end: Vector3 = Vector3.ZERO

var is_head_popped: bool = false
var is_arm_l_severed: bool = false
var is_arm_r_severed: bool = false

var _attack_cd: float = 0.0
var _tear_cd: float = 0.0
var _groan_cd: float = 2.0
var _repath_cd: float = 0.0
var _stagger_timer: float = 0.0
var _leg_damage: float = 0.0

var _anim_player: AnimationPlayer = null
var _skeleton: Skeleton3D = null
var _head_bone_idx: int = -1
var _arm_l_bone_idx: int = -1
var _arm_r_bone_idx: int = -1
var _current_anim: String = ""

var _mesh_head: Node3D = null
var _mesh_arm_l: Node3D = null
var _mesh_arm_r: Node3D = null
var _mesh_legs: Node3D = null
var _mesh_torso: Node3D = null
var _stump_head: Node3D = null
var _stump_arm_l: Node3D = null
var _stump_arm_r: Node3D = null
var _stump_legs: Node3D = null
var _player: Node3D = null
var _head_sync_tick: int = 0
var _head_synced_once: bool = false

var _gib_scene: PackedScene = preload("res://scenes/fx/gib_chunk.tscn")
var _blood_decal_scene: PackedScene = preload("res://scenes/fx/blood_decal.tscn")
var _blood_burst_scene: PackedScene = preload("res://scenes/fx/blood_burst.tscn")

signal died(zombie: ZombieAI, was_headshot: bool, death_pos: Vector3, force_drop: bool)


func setup(p_variant: String, p_hp: float, p_speed: float, p_window: Node = null) -> void:
	var variant_changed := (variant != p_variant)
	variant = p_variant
	is_brute = (variant == "brute")
	is_crawler = (variant == "crawler")
	max_hp = p_hp * (2.6 if is_brute else (0.72 if is_crawler else 1.0))
	hp = max_hp
	move_speed = p_speed * (0.85 if is_brute else (0.58 if is_crawler else 1.0))
	if is_crawler:
		move_speed = minf(move_speed, 1.45)
	is_sprinter = (not is_crawler) and (move_speed >= 3.8)
	attack_damage = 65.0 if is_brute else (32.0 if is_crawler else 45.0)
	target_window = p_window
	is_head_popped = false
	is_arm_l_severed = false
	is_arm_r_severed = false
	_leg_damage = 0.0
	_stagger_timer = 0.0
	_head_synced_once = false

	if target_window != null:
		state = State.APPROACHING_WINDOW
	else:
		state = State.CHASING
	if is_node_ready() and (variant_changed or model_root.get_child_count() == 0):
		_load_variant_model()
		_play_anim(_locomotion_anim())


func _ready() -> void:
	add_to_group("zombies")
	head_area.add_to_group("zombie_head")
	head_area.set_meta("zombie_owner", self)
	body_area.set_meta("zombie_owner", self)
	_groan_cd = randf_range(1.2, 6.0)
	_head_sync_tick = randi() & 3

	if model_root.get_child_count() == 0:
		_load_variant_model()

	_play_anim(_locomotion_anim())


func _get_player() -> Node3D:
	if _player != null and is_instance_valid(_player) and _player.is_inside_tree():
		return _player
	_player = get_tree().get_first_node_in_group("player") as Node3D
	return _player


func _locomotion_anim() -> String:
	if is_crawler:
		return "Crawl"
	return "Run" if is_sprinter else "Walk"


func _load_variant_model() -> void:
	for ch in model_root.get_children():
		model_root.remove_child(ch)
		ch.queue_free()
	_anim_player = null
	_skeleton = null
	_head_bone_idx = -1
	_arm_l_bone_idx = -1
	_arm_r_bone_idx = -1
	_current_anim = ""
	_mesh_head = null
	_mesh_arm_l = null
	_mesh_arm_r = null
	_mesh_legs = null
	_mesh_torso = null
	_stump_head = null
	_stump_arm_l = null
	_stump_arm_r = null
	_stump_legs = null

	var model_path := "res://assets/models/characters/zombie_%s.glb" % variant
	if ResourceLoader.exists(model_path):
		var inst := (load(model_path) as PackedScene).instantiate()
		model_root.add_child(inst)
		_find_rig_nodes(inst)
		_mesh_head = inst.find_child("Mesh_Head", true, false) as Node3D
		_mesh_arm_l = inst.find_child("Mesh_Arm_L", true, false) as Node3D
		_mesh_arm_r = inst.find_child("Mesh_Arm_R", true, false) as Node3D
		_mesh_legs = inst.find_child("Mesh_Legs", true, false) as Node3D
		_mesh_torso = inst.find_child("Mesh_Torso", true, false) as Node3D
		_stump_head = inst.find_child("Stump_Head", true, false) as Node3D
		_stump_arm_l = inst.find_child("Stump_Arm_L", true, false) as Node3D
		_stump_arm_r = inst.find_child("Stump_Arm_R", true, false) as Node3D
		_stump_legs = inst.find_child("Stump_Legs", true, false) as Node3D

		for snode in [_stump_head, _stump_arm_l, _stump_arm_r, _stump_legs]:
			if snode != null:
				snode.visible = false

		if is_crawler:
			_configure_crawler_collision_and_visuals()
		else:
			head_area.position.y = 1.94 if is_brute else 1.62
			body_area.position.y = 1.08 if is_brute else 0.88
			($BodyCollision as CollisionShape3D).position.y = 1.08 if is_brute else 0.90


func _configure_crawler_collision_and_visuals() -> void:
	if _mesh_legs != null:
		_mesh_legs.visible = false
	if _stump_legs != null:
		_stump_legs.visible = true
	head_area.position = Vector3(0.0, 0.48, -0.45)
	body_area.position.y = 0.36
	var body_col := $BodyCollision as CollisionShape3D
	if body_col != null:
		body_col.position.y = 0.38
		if body_col.shape is CapsuleShape3D:
			var dup := body_col.shape.duplicate() as CapsuleShape3D
			dup.height = 0.72
			dup.radius = 0.36
			body_col.shape = dup
	var area_col := body_area.get_node_or_null("CollisionShape3D") as CollisionShape3D
	if area_col != null and area_col.shape is CapsuleShape3D:
		var dup_a := area_col.shape.duplicate() as CapsuleShape3D
		dup_a.height = 0.72
		dup_a.radius = 0.42
		area_col.shape = dup_a


func _find_rig_nodes(node: Node) -> void:
	if node is AnimationPlayer and _anim_player == null:
		_anim_player = node as AnimationPlayer
		for anim_name in _anim_player.get_animation_list():
			if anim_name in ["Idle", "Walk", "Run", "Crawl"]:
				_anim_player.get_animation(anim_name).loop_mode = Animation.LOOP_LINEAR
	elif node is Skeleton3D and _skeleton == null:
		_skeleton = node as Skeleton3D
		_head_bone_idx = _skeleton.find_bone("Head")
		if _head_bone_idx < 0:
			_head_bone_idx = _skeleton.find_bone("head")
		_arm_l_bone_idx = _skeleton.find_bone("lowerarm_l")
		_arm_r_bone_idx = _skeleton.find_bone("lowerarm_r")
	for c in node.get_children():
		_find_rig_nodes(c)


func _play_anim(anim_name: String, force_restart: bool = false) -> void:
	if _anim_player == null:
		return
	var target := anim_name
	if not _anim_player.has_animation(target):
		if target in ["DeathBack", "DeathFwd"]:
			target = "Death"
		elif target in ["Tear", "Vault"]:
			target = "Attack" if target == "Tear" else "Walk"
		elif target == "Crawl":
			target = "Walk"
		else:
			return
	if not force_restart and _current_anim == target and _anim_player.is_playing():
		return
	var blend := 0.0 if _current_anim == "" else 0.16
	_current_anim = target
	_anim_player.play(target, blend)


func _physics_process(delta: float) -> void:
	if state == State.DEAD or GameManager.is_game_over:
		return

	_attack_cd = maxf(0.0, _attack_cd - delta)
	_stagger_timer = maxf(0.0, _stagger_timer - delta)
	_groan_cd -= delta
	if _groan_cd <= 0.0:
		_groan_cd = randf_range(4.5, 11.0)
		AudioManager.play_3d("zombie_groan_1" if randi() % 2 == 0 else "zombie_groan_2", global_position, 0.14, -7.0)

	# Track animated head bone for crisp headshot collision (every tick within 14m or first tick; 1-in-4 beyond)
	_head_sync_tick = (_head_sync_tick + 1) & 3
	if not is_head_popped and _skeleton != null and _head_bone_idx >= 0:
		var p_node := _get_player()
		var need_sync := (not _head_synced_once) or p_node == null or (_head_sync_tick == 0) or global_position.distance_squared_to(p_node.global_position) <= 196.0
		if need_sync:
			_head_synced_once = true
			var bone_pose := _skeleton.get_bone_global_pose(_head_bone_idx)
			head_area.global_position = _skeleton.to_global(bone_pose.origin) + Vector3(0, 0.06 if is_crawler else 0.12, 0)

	match state:
		State.APPROACHING_WINDOW:
			_process_approaching_window(delta)
		State.BREAKING_BARRIER:
			_process_breaking_barrier(delta)
		State.VAULTING:
			_process_vaulting(delta)
		State.CHASING:
			_process_chasing(delta)


func _process_approaching_window(delta: float) -> void:
	if not is_instance_valid(target_window):
		state = State.CHASING
		return
	var goal: Vector3 = target_window.get_outside_pos()
	var to_goal := goal - global_position
	to_goal.y = 0.0
	if to_goal.length() < 0.45:
		state = State.BREAKING_BARRIER
		_tear_cd = 0.4
		return
	var dir := to_goal.normalized()
	var spd := move_speed * (0.45 if _stagger_timer > 0.0 else 1.0)
	velocity.x = dir.x * spd
	velocity.z = dir.z * spd
	velocity.y = -9.8 * delta if not is_on_floor() else 0.0
	move_and_slide()
	_face_direction(dir, delta)
	if _stagger_timer <= 0.0:
		_play_anim(_locomotion_anim())


func _process_breaking_barrier(delta: float) -> void:
	if not is_instance_valid(target_window):
		state = State.CHASING
		return
	var look_dir: Vector3 = (target_window.get_inside_pos() - global_position)
	look_dir.y = 0.0
	_face_direction(look_dir.normalized(), delta)

	if target_window.has_planks():
		_tear_cd -= delta
		if _tear_cd <= 0.0:
			_tear_cd = 1.35
			_play_anim("Crawl" if is_crawler else "Tear", true)
			target_window.tear_plank()
	else:
		state = State.VAULTING
		vault_progress = 0.0
		vault_start = global_position
		vault_mid = target_window.get_sill_pos()
		vault_end = target_window.get_inside_pos()
		set_collision_mask_value(1, false)
		_play_anim("Crawl" if is_crawler else "Vault", true)


func _process_vaulting(delta: float) -> void:
	vault_progress += delta / (0.95 if is_crawler else 0.72)
	if vault_progress >= 1.0:
		global_position = vault_end
		set_collision_mask_value(1, true)
		state = State.CHASING
		return
	var p: Vector3
	if vault_progress < 0.5:
		p = vault_start.lerp(vault_mid, vault_progress * 2.0)
	else:
		p = vault_mid.lerp(vault_end, (vault_progress - 0.5) * 2.0)
	global_position = p


func _process_chasing(delta: float) -> void:
	var player := _get_player()
	if player == null:
		return

	var dist := global_position.distance_to(player.global_position)
	if dist <= 1.85:
		velocity.x = 0.0
		velocity.z = 0.0
		_face_direction((player.global_position - global_position).normalized(), delta)
		if _attack_cd <= 0.0:
			_attack_cd = 1.15
			_play_anim("Crawl" if is_crawler else "Attack", true)
			if player.has_method("take_damage"):
				player.take_damage(attack_damage)
		return

	_repath_cd -= delta
	if _repath_cd <= 0.0:
		_repath_cd = 0.22 if dist < 12.0 else 0.45
		nav_agent.target_position = player.global_position

	var move_dir := Vector3.ZERO
	if not nav_agent.is_navigation_finished():
		var next_pt := nav_agent.get_next_path_position()
		move_dir = next_pt - global_position
		move_dir.y = 0.0
	if move_dir.length_squared() < 0.01:
		move_dir = player.global_position - global_position
		move_dir.y = 0.0
	if move_dir.length_squared() > 0.001:
		move_dir = move_dir.normalized()

	var spd := move_speed * (0.45 if _stagger_timer > 0.0 else 1.0)
	velocity.x = move_dir.x * spd
	velocity.z = move_dir.z * spd
	if not is_on_floor():
		velocity.y -= 15.0 * delta
	else:
		velocity.y = 0.0
	move_and_slide()
	_face_direction(move_dir, delta)
	if _stagger_timer <= 0.0 and _attack_cd <= 0.55:
		_play_anim(_locomotion_anim())


func _face_direction(dir: Vector3, delta: float) -> void:
	if dir.length_squared() < 0.001:
		return
	var target_yaw := atan2(-dir.x, -dir.z)
	rotation.y = lerp_angle(rotation.y, target_yaw, delta * 9.5)


func take_damage(amount: float, is_headshot: bool, hit_pos: Vector3, hit_dir: Vector3, is_melee: bool = false) -> bool:
	if state == State.DEAD:
		return false

	var insta: bool = float(GameManager.active_powerups.get("insta_kill", 0.0)) > 0.0 and not is_brute
	var eff_dmg := amount
	if is_brute and not is_headshot:
		eff_dmg *= 0.65

	if insta:
		hp = 0.0
	else:
		hp -= eff_dmg

	if hp <= 0.0:
		_die(is_headshot, is_melee, false, hit_pos, hit_dir)
		return true

	# Non-lethal localized dismemberment & stagger logic
	GameManager.add_points(10, "Hit")
	var is_aoe_origin := hit_pos.distance_squared_to(global_position) < 0.04
	var local_hit := to_local(hit_pos)

	if is_aoe_origin and not is_brute and not is_crawler and eff_dmg >= max_hp * 0.42:
		become_crawler(hit_dir)
	elif not is_aoe_origin and not is_crawler and not is_brute:
		# Check leg hit (low Y) -> accumulate toward crawler transition
		if local_hit.y >= 0.04 and local_hit.y <= 0.84:
			_leg_damage += eff_dmg
			if _leg_damage >= max_hp * 0.38 or eff_dmg >= 68.0:
				become_crawler(hit_dir)
		# Check heavy arm hits -> sever individual arms
		elif not is_arm_l_severed and _skeleton != null and _arm_l_bone_idx >= 0 and eff_dmg >= 48.0:
			var arm_l_pos := _skeleton.to_global(_skeleton.get_bone_global_pose(_arm_l_bone_idx).origin)
			if hit_pos.distance_to(arm_l_pos) < 0.36:
				_dismember_arm("L", hit_dir)
		elif not is_arm_r_severed and _skeleton != null and _arm_r_bone_idx >= 0 and eff_dmg >= 48.0:
			var arm_r_pos := _skeleton.to_global(_skeleton.get_bone_global_pose(_arm_r_bone_idx).origin)
			if hit_pos.distance_to(arm_r_pos) < 0.36:
				_dismember_arm("R", hit_dir)

	if not is_crawler and not is_brute and eff_dmg >= max_hp * 0.25:
		_stagger_timer = 0.35
		_play_anim("Hit", true)

	return false


func become_crawler(hit_dir: Vector3 = Vector3.UP) -> void:
	if is_crawler or is_brute or state == State.DEAD:
		return
	is_crawler = true
	is_sprinter = false
	move_speed = minf(move_speed, 1.35)
	_stagger_timer = 0.0
	_configure_crawler_collision_and_visuals()
	var leg_origin := global_position + Vector3(0, 0.42, 0)
	_spawn_gibs(leg_origin, hit_dir, 4, 2)
	_spawn_blood_burst(leg_origin)
	_spawn_blood_decal(global_position, 1.05)
	_play_anim("Crawl", true)


func _dismember_head(hit_dir: Vector3) -> void:
	if is_head_popped:
		return
	is_head_popped = true
	if _mesh_head != null:
		_mesh_head.visible = false
	if _stump_head != null:
		_stump_head.visible = true
	head_area.set_deferred("monitoring", false)
	head_area.set_deferred("monitorable", false)
	var head_origin := global_position + Vector3(0, 1.85 if is_brute else (0.50 if is_crawler else 1.56), 0)
	if _skeleton != null and _head_bone_idx >= 0:
		head_origin = _skeleton.to_global(_skeleton.get_bone_global_pose(_head_bone_idx).origin)
	_spawn_gibs(head_origin, hit_dir + Vector3(0, 0.9, 0), 4, 3)
	_spawn_blood_burst(head_origin)


func _dismember_arm(side: String, hit_dir: Vector3) -> void:
	if side == "L":
		if is_arm_l_severed:
			return
		is_arm_l_severed = true
		if _mesh_arm_l != null:
			_mesh_arm_l.visible = false
		if _stump_arm_l != null:
			_stump_arm_l.visible = true
		var p := _skeleton.to_global(_skeleton.get_bone_global_pose(_arm_l_bone_idx).origin) if (_skeleton and _arm_l_bone_idx >= 0) else (global_position + Vector3(-0.3, 1.15, 0))
		_spawn_gibs(p, hit_dir, 3, 1)
		_spawn_blood_burst(p)
	else:
		if is_arm_r_severed:
			return
		is_arm_r_severed = true
		if _mesh_arm_r != null:
			_mesh_arm_r.visible = false
		if _stump_arm_r != null:
			_stump_arm_r.visible = true
		var p := _skeleton.to_global(_skeleton.get_bone_global_pose(_arm_r_bone_idx).origin) if (_skeleton and _arm_r_bone_idx >= 0) else (global_position + Vector3(0.3, 1.15, 0))
		_spawn_gibs(p, hit_dir, 3, 1)
		_spawn_blood_burst(p)


func _fx_parent() -> Node:
	var p := get_parent()
	if p != null and p != get_tree().root:
		return p
	return get_tree().current_scene if get_tree().current_scene != null else p


func _spawn_gibs(origin: Vector3, hit_dir: Vector3, flesh_count: int, skull_count: int) -> void:
	if not is_inside_tree():
		return
	var parent_node := _fx_parent()
	if parent_node == null:
		return
	var base_dir := hit_dir.normalized() if hit_dir.length_squared() > 0.001 else Vector3.UP
	for i in range(flesh_count + skull_count):
		var g := _gib_scene.instantiate() as GibChunk
		parent_node.add_child(g)
		g.global_position = origin + Vector3(randf_range(-0.1, 0.1), randf_range(-0.05, 0.1), randf_range(-0.1, 0.1))
		var impulse := (base_dir * randf_range(1.6, 3.8)) + Vector3(randf_range(-2.2, 2.2), randf_range(2.6, 5.2), randf_range(-2.2, 2.2))
		g.setup("skull" if i >= flesh_count else "flesh", impulse)


func _spawn_blood_burst(origin: Vector3) -> void:
	if not is_inside_tree():
		return
	var parent_node := _fx_parent()
	if parent_node == null:
		return
	var fx := _blood_burst_scene.instantiate() as Node3D
	parent_node.add_child(fx)
	fx.global_position = origin


func _spawn_blood_decal(pos: Vector3, p_scale: float = 1.0) -> void:
	if not is_inside_tree():
		return
	var parent_node := _fx_parent()
	if parent_node == null:
		return
	var d := _blood_decal_scene.instantiate() as BloodDecal
	d.setup(p_scale)
	parent_node.add_child(d)
	d.global_position = Vector3(pos.x, 0.0, pos.z)


func kill_by_nuke() -> void:
	if state == State.DEAD:
		return
	_die(false, false, true, global_position + Vector3.UP, Vector3.UP)


func _die(was_headshot: bool, is_melee: bool, from_nuke: bool, hit_pos: Vector3, hit_dir: Vector3) -> void:
	state = State.DEAD
	remove_from_group("zombies")
	set_physics_process(false)
	head_area.set_deferred("monitoring", false)
	head_area.set_deferred("monitorable", false)
	body_area.set_deferred("monitoring", false)
	body_area.set_deferred("monitorable", false)
	($BodyCollision as CollisionShape3D).set_deferred("disabled", true)

	if not from_nuke:
		GameManager.stats["kills"] += 1
		if was_headshot:
			GameManager.stats["headshots"] += 1
			GameManager.add_points(100, "Headshot")
			_dismember_head(hit_dir)
		elif is_melee:
			GameManager.add_points(130, "Melee Kill")
		else:
			GameManager.add_points(60, "Kill")
			if hit_pos.distance_squared_to(global_position) < 0.04:
				# Explosion kill blasts extra gore chunks!
				_spawn_gibs(global_position + Vector3(0, 0.9, 0), Vector3.UP, 4, 2)
		_spawn_blood_decal(global_position, 1.35 if is_brute else 1.0)

	var death_anim := "DeathFwd" if (was_headshot or is_crawler or randf() < 0.45) else "DeathBack"
	_play_anim(death_anim, true)
	emit_signal("died", self, was_headshot, global_position, is_brute and not from_nuke)
	get_tree().create_timer(2.4).timeout.connect(queue_free)

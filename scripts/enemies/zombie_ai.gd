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

var state: State = State.CHASING
var target_window: Node = null
var vault_progress: float = 0.0
var vault_start: Vector3 = Vector3.ZERO
var vault_mid: Vector3 = Vector3.ZERO
var vault_end: Vector3 = Vector3.ZERO

var _attack_cd: float = 0.0
var _tear_cd: float = 0.0
var _groan_cd: float = 2.0
var _repath_cd: float = 0.0
var _anim_player: AnimationPlayer = null
var _skeleton: Skeleton3D = null
var _head_bone_idx: int = -1
var _current_anim: String = ""

signal died(zombie: ZombieAI, was_headshot: bool, death_pos: Vector3, force_drop: bool)


func setup(p_variant: String, p_hp: float, p_speed: float, p_window: Node = null) -> void:
	var variant_changed := (variant != p_variant)
	variant = p_variant
	is_brute = (variant == "brute")
	max_hp = p_hp * (2.6 if is_brute else 1.0)
	hp = max_hp
	move_speed = p_speed * (0.85 if is_brute else 1.0)
	is_sprinter = move_speed >= 3.8
	attack_damage = 65.0 if is_brute else 45.0
	target_window = p_window
	if target_window != null:
		state = State.APPROACHING_WINDOW
	else:
		state = State.CHASING
	if is_node_ready() and (variant_changed or model_root.get_child_count() == 0):
		_load_variant_model()
		_play_anim("Run" if is_sprinter else "Walk")


func _ready() -> void:
	add_to_group("zombies")
	head_area.add_to_group("zombie_head")
	head_area.set_meta("zombie_owner", self)
	body_area.set_meta("zombie_owner", self)
	_groan_cd = randf_range(1.2, 6.0)

	if model_root.get_child_count() == 0:
		_load_variant_model()

	_play_anim("Run" if is_sprinter else "Walk")


func _load_variant_model() -> void:
	for ch in model_root.get_children():
		ch.queue_free()
	_anim_player = null
	_skeleton = null
	_head_bone_idx = -1
	_current_anim = ""

	var model_path := "res://assets/models/characters/zombie_%s.glb" % variant
	if ResourceLoader.exists(model_path):
		var inst := (load(model_path) as PackedScene).instantiate()
		model_root.add_child(inst)
		_find_rig_nodes(inst)
		head_area.position.y = 1.92 if is_brute else 1.62
		($BodyCollision as CollisionShape3D).position.y = 1.08 if is_brute else 0.90


func _find_rig_nodes(node: Node) -> void:
	if node is AnimationPlayer and _anim_player == null:
		_anim_player = node as AnimationPlayer
		for anim_name in _anim_player.get_animation_list():
			if anim_name in ["Idle", "Walk", "Run"]:
				_anim_player.get_animation(anim_name).loop_mode = Animation.LOOP_LINEAR
	elif node is Skeleton3D and _skeleton == null:
		_skeleton = node as Skeleton3D
		_head_bone_idx = _skeleton.find_bone("Head")
	for c in node.get_children():
		_find_rig_nodes(c)


func _play_anim(anim_name: String) -> void:
	if _anim_player == null or _current_anim == anim_name:
		return
	if _anim_player.has_animation(anim_name):
		var blend := 0.0 if _current_anim == "" else 0.18
		_current_anim = anim_name
		_anim_player.play(anim_name, blend)


func _physics_process(delta: float) -> void:
	if state == State.DEAD or GameManager.is_game_over:
		return

	_attack_cd = maxf(0.0, _attack_cd - delta)
	_groan_cd -= delta
	if _groan_cd <= 0.0:
		_groan_cd = randf_range(4.5, 11.0)
		AudioManager.play_3d("zombie_groan_1" if randi() % 2 == 0 else "zombie_groan_2", global_position, 0.14, -7.0)

	# Track animated head bone for crisp headshot collision!
	if _skeleton != null and _head_bone_idx >= 0:
		var bone_pose := _skeleton.get_bone_global_pose(_head_bone_idx)
		head_area.global_position = _skeleton.to_global(bone_pose.origin) + Vector3(0, 0.12, 0)

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
	velocity.x = dir.x * move_speed
	velocity.z = dir.z * move_speed
	velocity.y = -9.8 * delta if not is_on_floor() else 0.0
	move_and_slide()
	_face_direction(dir, delta)
	_play_anim("Run" if is_sprinter else "Walk")


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
			_play_anim("Attack")
			target_window.tear_plank()
	else:
		state = State.VAULTING
		vault_progress = 0.0
		vault_start = global_position
		vault_mid = target_window.get_sill_pos()
		vault_end = target_window.get_inside_pos()
		set_collision_mask_value(1, false)
		_play_anim("Walk")


func _process_vaulting(delta: float) -> void:
	vault_progress += delta / 0.72
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
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return

	var dist := global_position.distance_to(player.global_position)
	if dist <= 1.85:
		velocity.x = 0.0
		velocity.z = 0.0
		_face_direction((player.global_position - global_position).normalized(), delta)
		if _attack_cd <= 0.0:
			_attack_cd = 1.15
			_play_anim("Attack")
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

	velocity.x = move_dir.x * move_speed
	velocity.z = move_dir.z * move_speed
	if not is_on_floor():
		velocity.y -= 15.0 * delta
	else:
		velocity.y = 0.0
	move_and_slide()
	_face_direction(move_dir, delta)
	_play_anim("Run" if is_sprinter else "Walk")


func _face_direction(dir: Vector3, delta: float) -> void:
	if dir.length_squared() < 0.001:
		return
	var target_yaw := atan2(-dir.x, -dir.z)
	rotation.y = lerp_angle(rotation.y, target_yaw, delta * 9.5)


func take_damage(amount: float, is_headshot: bool, _hit_pos: Vector3, _hit_dir: Vector3, is_melee: bool = false) -> bool:
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
		_die(is_headshot, is_melee, false)
		return true
	else:
		GameManager.add_points(10, "Hit")
		return false


func kill_by_nuke() -> void:
	if state == State.DEAD:
		return
	_die(false, false, true)


func _die(was_headshot: bool, is_melee: bool, from_nuke: bool) -> void:
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
		elif is_melee:
			GameManager.add_points(130, "Melee Kill")
		else:
			GameManager.add_points(60, "Kill")

	_play_anim("Death")
	emit_signal("died", self, was_headshot, global_position, is_brute and not from_nuke)
	get_tree().create_timer(2.4).timeout.connect(queue_free)

extends CharacterBody3D
class_name PlayerController

const BASE_WALK_SPEED := 5.2
const BASE_SPRINT_SPEED := 7.6
const CROUCH_SPEED := 3.0
const JUMP_VELOCITY := 4.8
const GRAVITY := 15.0
const SLIDE_DURATION := 0.68
const SLIDE_COOLDOWN := 0.85

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var col_shape: CollisionShape3D = $CollisionShape3D
@onready var interact_ray: RayCast3D = $Head/Camera3D/InteractRay
@onready var weapon_ctrl: WeaponController = $Head/Camera3D/WeaponController

var max_hp: float = 100.0
var hp: float = 100.0
var max_stamina: float = 100.0
var stamina: float = 100.0
var time_since_damage: float = 99.0

var is_downed: bool = false
var revive_timer: float = 0.0
const REVIVE_DURATION := 6.5

var is_crouching: bool = false
var is_sprinting: bool = false
var is_sliding: bool = false
var _slide_timer: float = 0.0
var _slide_cooldown: float = 0.0
var _slide_dir: Vector3 = Vector3.FORWARD
var _slide_speed: float = 0.0
var _was_sprinting_timer: float = 0.0

var _was_grounded: bool = true
var _air_peak_y: float = 0.0
var _footstep_dist: float = 0.0

var _bob_time: float = 0.0
var _bob_weight: float = 0.0
var _sprint_blend: float = 0.0
var _cam_roll: float = 0.0
var _recoil_pitch: float = 0.0
var _recoil_yaw: float = 0.0
var _trauma: float = 0.0
var _trauma_time: float = 0.0
var _last_prompt: String = ""
var _hold_repair_timer: float = 0.0
var _noclip_input: bool = false
var _grounded_override: bool = false

var _grenade_scene: PackedScene = preload("res://scenes/fx/frag_grenade_proj.tscn")
var _phd_shockwave_scene: PackedScene = preload("res://scenes/fx/wpn_phd_shockwave.tscn")


static func _exp_alpha(speed: float, delta: float) -> float:
	return clampf(1.0 - exp(-speed * maxf(delta, 0.0)), 0.0, 1.0)


func is_grounded() -> bool:
	return _grounded_override or is_on_floor()


func _ready() -> void:
	add_to_group("player")
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	camera.fov = SettingsManager.fov
	_air_peak_y = global_position.y
	SettingsManager.settings_changed.connect(_on_settings_changed)
	GameManager.perks_changed.connect(_on_perks_changed)
	GameManager.round_changed.connect(_on_round_changed)
	GameManager.player_health_changed.emit(hp, max_hp)
	GameManager.player_stamina_changed.emit(stamina, max_stamina)


func _on_settings_changed() -> void:
	if camera and (weapon_ctrl == null or not weapon_ctrl.is_aiming):
		camera.fov = SettingsManager.fov


func _on_perks_changed(_perks: Array[String]) -> void:
	var new_max := 250.0 if GameManager.has_perk("juggernog") else 100.0
	if new_max > max_hp:
		hp += (new_max - max_hp)
	max_hp = new_max
	hp = minf(hp, max_hp)
	GameManager.player_health_changed.emit(hp, max_hp)


func _on_round_changed(_r: int, _is_dog: bool) -> void:
	if weapon_ctrl:
		weapon_ctrl.grenades = mini(4, weapon_ctrl.grenades + 2)
		weapon_ctrl.emit_hud()


func _unhandled_input(event: InputEvent) -> void:
	if GameManager.is_game_over or get_tree().paused:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var mm := event as InputEventMouseMotion
		var aiming := weapon_ctrl != null and weapon_ctrl.is_aiming
		var sens := SettingsManager.mouse_sensitivity * (0.65 if aiming else 1.0)
		rotate_y(-mm.relative.x * sens)
		var y_sign := 1.0 if SettingsManager.invert_y else -1.0
		head.rotation.x = clampf(head.rotation.x + mm.relative.y * sens * y_sign, -1.42, 1.42)
		if weapon_ctrl:
			weapon_ctrl.add_look_sway(mm.relative)


func _process(delta: float) -> void:
	if GameManager.is_game_over or get_tree().paused:
		return
	_update_camera_motion(delta)


func _physics_process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	_handle_health_and_downed(delta)
	_handle_movement(delta)
	_handle_interaction(delta)

	if Input.is_action_just_pressed("grenade") and not is_downed:
		_throw_grenade()


func start_slide(slide_dir: Vector3 = Vector3.ZERO) -> void:
	if is_downed or is_sliding or _slide_cooldown > 0.0:
		return
	var d := slide_dir
	d.y = 0.0
	if d.length_squared() < 0.01:
		d = -transform.basis.z
		d.y = 0.0
	_slide_dir = d.normalized()
	is_sliding = true
	is_crouching = true
	is_sprinting = false
	_slide_timer = SLIDE_DURATION
	_slide_cooldown = SLIDE_COOLDOWN
	var has_staminup := GameManager.has_perk("staminup")
	_slide_speed = 11.4 * (1.12 if has_staminup else 1.0)
	AudioManager.play_2d("slide_scrape", 0.06, -3.0)


func _finish_slide(trigger_phd: bool) -> void:
	if not is_sliding:
		return
	is_sliding = false
	_slide_timer = 0.0
	if trigger_phd and GameManager.has_perk("phdflopper"):
		trigger_phd_explosion()


func _handle_movement(delta: float) -> void:
	_slide_cooldown = maxf(0.0, _slide_cooldown - delta)
	var grounded_now := is_grounded()
	if not grounded_now:
		_air_peak_y = maxf(_air_peak_y, global_position.y)
	elif not _was_grounded:
		var drop := _air_peak_y - global_position.y
		_air_peak_y = global_position.y
		# Landing impact: camera dip + shake scaled by fall height (CoD weighty landing)
		if drop > 0.55 and not is_downed:
			var impact := clampf((drop - 0.55) / 3.2, 0.0, 1.0)
			_recoil_pitch = clampf(_recoil_pitch - 0.028 - 0.05 * impact, -0.22, 0.25)
			add_camera_trauma(0.10 + 0.18 * impact)
		if drop >= 2.2 and GameManager.has_perk("phdflopper") and not is_downed:
			trigger_phd_explosion()
	else:
		_air_peak_y = global_position.y
	_was_grounded = grounded_now

	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	elif Input.is_action_just_pressed("jump") and not is_downed:
		if is_sliding:
			_finish_slide(false)
			velocity.y = JUMP_VELOCITY * 1.05
		elif not is_crouching:
			velocity.y = JUMP_VELOCITY

	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var dir := (transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()

	if is_sprinting:
		_was_sprinting_timer = 0.18
	else:
		_was_sprinting_timer = maxf(0.0, _was_sprinting_timer - delta)

	var horiz_v := Vector2(velocity.x, velocity.z).length()
	if Input.is_action_just_pressed("crouch") and not is_downed and not is_sliding:
		if (is_sprinting or (_was_sprinting_timer > 0.0 and horiz_v >= 4.8)) and grounded_now and _slide_cooldown <= 0.0:
			var sdir := dir if dir.length_squared() > 0.04 else -transform.basis.z
			start_slide(sdir)

	if is_sliding:
		if is_downed:
			_finish_slide(false)
		else:
			is_crouching = true
			_slide_timer -= delta
			_slide_speed = lerpf(_slide_speed, CROUCH_SPEED, _exp_alpha(3.2, delta))
			velocity.x = _slide_dir.x * _slide_speed
			velocity.z = _slide_dir.z * _slide_speed
			if _slide_timer <= 0.0:
				_finish_slide(true)
			move_and_slide()
			return

	is_crouching = Input.is_action_pressed("crouch") or is_downed

	var aiming := weapon_ctrl != null and weapon_ctrl.is_aiming
	var wants_sprint := Input.is_action_pressed("sprint") and input_dir.y < -0.1 and not is_crouching and not aiming and not is_downed
	var has_staminup := GameManager.has_perk("staminup")
	is_sprinting = false

	if wants_sprint and stamina > 2.0 and dir.length() > 0.1:
		is_sprinting = true
		var drain := 12.0 if has_staminup else 24.0
		stamina = maxf(0.0, stamina - drain * delta)
	else:
		var regen := 38.0 if has_staminup else 20.0
		stamina = minf(max_stamina, stamina + regen * delta)
	GameManager.player_stamina_changed.emit(stamina, max_stamina)

	var speed := BASE_WALK_SPEED
	if is_downed:
		speed = 1.8
	elif is_crouching:
		speed = CROUCH_SPEED
	elif is_sprinting:
		speed = BASE_SPRINT_SPEED * (1.25 if has_staminup else 1.0)
	elif has_staminup:
		speed *= 1.08

	if aiming and not is_downed:
		speed *= 0.68

	var accel := 12.0 if is_on_floor() else 4.0
	var vel_alpha := _exp_alpha(accel, delta)
	velocity.x = lerpf(velocity.x, dir.x * speed, vel_alpha)
	velocity.z = lerpf(velocity.z, dir.z * speed, vel_alpha)
	if dir.length_squared() < 0.0001 and Vector2(velocity.x, velocity.z).length_squared() < 0.0001:
		velocity.x = 0.0
		velocity.z = 0.0
	move_and_slide()

	# Footstep cadence (metal deck in East Courtyard vs concrete/stone elsewhere)
	var post_horiz := Vector2(velocity.x, velocity.z).length()
	if grounded_now and not is_downed and post_horiz > 0.65:
		_footstep_dist += post_horiz * delta
		var stride := 1.25 if is_crouching else (1.85 if is_sprinting else 1.55)
		if _footstep_dist >= stride:
			_footstep_dist = 0.0
			var on_metal := global_position.x >= 10.0 and global_position.x <= 24.0 and absf(global_position.z) <= 8.0
			var step_sfx := "footstep_metal" if on_metal else "footstep_stone"
			var vol := -7.5 if is_sprinting else (-15.0 if is_crouching else -11.5)
			AudioManager.play_2d(step_sfx, 0.09, vol)
	elif not grounded_now or post_horiz <= 0.35:
		_footstep_dist = 0.0


func _update_camera_motion(delta: float) -> void:
	# Visual crouch height, recoil recovery, and headbob run in _process alongside WeaponController
	# so Camera3D and ViewmodelPivot stay frame-synchronized with zero 60Hz-vs-render-FPS beat jitter.
	var target_h := 0.66 if is_sliding else (0.85 if (is_crouching or is_downed) else 1.62)
	var h_speed := 15.0 if is_sliding else 12.0
	head.position.y = lerpf(head.position.y, target_h, _exp_alpha(h_speed, delta))
	if absf(head.position.y - target_h) < 0.00001:
		head.position.y = target_h

	var recoil_alpha := _exp_alpha(11.0, delta)
	_recoil_pitch = lerpf(_recoil_pitch, 0.0, recoil_alpha)
	_recoil_yaw = lerpf(_recoil_yaw, 0.0, recoil_alpha)
	if absf(_recoil_pitch) < 0.00001:
		_recoil_pitch = 0.0
	if absf(_recoil_yaw) < 0.00001:
		_recoil_yaw = 0.0

	var target_roll := deg_to_rad(5.5) if is_sliding else 0.0
	_cam_roll = lerpf(_cam_roll, target_roll, _exp_alpha(12.0, delta))
	if absf(_cam_roll - target_roll) < 0.00001:
		_cam_roll = target_roll

	var shake_x := 0.0
	var shake_y := 0.0
	var shake_z := 0.0
	if _trauma > 0.0001:
		_trauma_time += delta * 34.0
		var s := _trauma * _trauma
		shake_x = sin(_trauma_time * 1.13) * 0.028 * s
		shake_y = cos(_trauma_time * 1.47) * 0.022 * s
		shake_z = sin(_trauma_time * 1.89) * 0.036 * s
		_trauma = maxf(0.0, _trauma - delta * 2.4)
		if _trauma <= 0.0001:
			_trauma = 0.0

	camera.rotation.x = _recoil_pitch + shake_x
	camera.rotation.y = _recoil_yaw + shake_y
	camera.rotation.z = _cam_roll + shake_z

	var horiz_speed := Vector2(velocity.x, velocity.z).length()
	var grounded := is_grounded()
	var aiming := weapon_ctrl != null and weapon_ctrl.is_aiming
	var speed_weight := clampf((horiz_speed - 0.25) / 1.5, 0.0, 1.0)
	var target_bob_weight := speed_weight * (0.35 if aiming else 1.0) if (grounded and not is_sliding) else 0.0
	_bob_weight = lerpf(_bob_weight, target_bob_weight, _exp_alpha(10.0, delta))
	_sprint_blend = lerpf(_sprint_blend, 1.0 if (is_sprinting and grounded and not aiming and not is_sliding) else 0.0, _exp_alpha(8.0, delta))
	if _bob_weight < 0.0001 and target_bob_weight == 0.0:
		_bob_weight = 0.0
	if _sprint_blend < 0.0001 and (not is_sprinting or not grounded or aiming or is_sliding):
		_sprint_blend = 0.0

	var bob_target := Vector3.ZERO
	if _bob_weight > 0.0001:
		var bob_dt := clampf(delta, 0.0, 0.15)
		_bob_time = fmod(_bob_time + bob_dt * maxf(horiz_speed, 0.5) * 1.9, TAU * 100.0)
		var bob_amp_y := lerpf(0.018, 0.032, _sprint_blend)
		bob_target = Vector3(
			cos(_bob_time) * 0.014 * _bob_weight,
			sin(_bob_time * 2.0) * bob_amp_y * _bob_weight,
			0.0
		)
	camera.position = camera.position.lerp(bob_target, _exp_alpha(14.0, delta))
	if bob_target == Vector3.ZERO and camera.position.length_squared() < 1e-10:
		camera.position = Vector3.ZERO


func add_camera_recoil(pitch: float, yaw: float) -> void:
	_recoil_pitch = clampf(_recoil_pitch + pitch, -0.22, 0.25)
	_recoil_yaw = clampf(_recoil_yaw + randf_range(-yaw, yaw), -0.15, 0.15)


func add_camera_trauma(amount: float) -> void:
	_trauma = clampf(_trauma + amount, 0.0, 1.0)


func trigger_phd_explosion(origin: Vector3 = Vector3.INF) -> int:
	var pos := global_position if origin == Vector3.INF else origin
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	if target_parent:
		var fx := _phd_shockwave_scene.instantiate() as Node3D
		target_parent.add_child(fx)
		fx.global_position = pos + Vector3(0.0, 0.16, 0.0)
	AudioManager.play_2d("phd_nuke", 0.05, 0.0)
	add_camera_trauma(0.45)

	var hits := 0
	var any_kill := false
	var dmg_base := 950.0 + float(GameManager.current_round) * 90.0
	var rad := 5.5
	for z in get_tree().get_nodes_in_group("zombies"):
		var z3 := z as Node3D
		if z3 == null or not is_instance_valid(z3):
			continue
		var d := z3.global_position.distance_to(pos)
		if d <= rad and z.has_method("take_damage"):
			var falloff := clampf(1.0 - (d / (rad * 1.1)), 0.45, 1.0)
			var dir := (z3.global_position - pos)
			dir = dir.normalized() if dir.length_squared() > 0.001 else Vector3.UP
			var k: bool = z.take_damage(dmg_base * falloff, false, z3.global_position + Vector3(0, 0.8, 0), dir)
			hits += 1
			any_kill = any_kill or k
	if hits > 0:
		AudioManager.play_2d("hitmarker", 0.05, -3.0)
		GameManager.hitmarker_triggered.emit(any_kill, false)
	return hits


func _handle_health_and_downed(delta: float) -> void:
	if is_downed:
		revive_timer += delta
		GameManager.player_downed_changed.emit(true, clampf(revive_timer / REVIVE_DURATION, 0.0, 1.0))
		if revive_timer >= REVIVE_DURATION:
			_complete_self_revive()
		return

	time_since_damage += delta
	if time_since_damage >= 3.6 and hp < max_hp:
		hp = minf(max_hp, hp + 40.0 * delta)
		GameManager.player_health_changed.emit(hp, max_hp)


func take_damage(amount: float, source_pos: Vector3 = Vector3.INF, is_explosive: bool = false) -> void:
	if is_explosive and GameManager.has_perk("phdflopper"):
		return
	if GameManager.is_game_over or is_downed:
		return

	var src := source_pos
	if src == Vector3.INF:
		var best_d := 7.5
		for z in get_tree().get_nodes_in_group("zombies"):
			var z3 := z as Node3D
			if z3 == null or not is_instance_valid(z3):
				continue
			var d := z3.global_position.distance_to(global_position)
			if d < best_d:
				best_d = d
				src = z3.global_position
	if src != Vector3.INF:
		get_tree().call_group("hud", "on_player_damaged", amount, src, global_position, global_transform.basis)

	hp -= amount
	time_since_damage = 0.0
	AudioManager.play_2d("player_hurt", 0.08, 0.0)
	add_camera_recoil(randf_range(0.03, 0.06), 0.05)
	add_camera_trauma(0.28)

	if hp <= 0.0:
		if GameManager.has_perk("quickrevive") and GameManager.quick_revive_uses_left > 0:
			_enter_last_stand()
		else:
			hp = 0.0
			GameManager.player_health_changed.emit(hp, max_hp)
			GameManager.trigger_game_over()
	else:
		GameManager.player_health_changed.emit(hp, max_hp)


func _enter_last_stand() -> void:
	is_downed = true
	is_sliding = false
	revive_timer = 0.0
	hp = 35.0
	GameManager.quick_revive_uses_left -= 1
	GameManager.lose_all_perks()
	max_hp = 100.0
	GameManager.player_health_changed.emit(hp, max_hp)
	GameManager.player_downed_changed.emit(true, 0.0)
	GameManager.powerup_banner.emit("LAST STAND — SELF REVIVING...", Color(0.35, 0.78, 1.0))


func _complete_self_revive() -> void:
	is_downed = false
	revive_timer = 0.0
	hp = max_hp
	GameManager.player_downed_changed.emit(false, 0.0)
	GameManager.player_health_changed.emit(hp, max_hp)
	AudioManager.play_2d("powerup_collect", 0.0, 1.0)
	GameManager.powerup_banner.emit("REVIVED!", Color(0.35, 1.0, 0.55))
	# Shockwave clears nearby zombies so player isn't trapped
	for z in get_tree().get_nodes_in_group("zombies"):
		if z.global_position.distance_to(global_position) <= 6.5 and z.has_method("take_damage"):
			z.take_damage(99999.0, false, z.global_position, Vector3.UP)


func _handle_interaction(delta: float) -> void:
	if is_downed:
		_set_prompt("")
		return
	var prompt := ""
	if interact_ray and interact_ray.is_colliding():
		var col := interact_ray.get_collider()
		var target: Node = col
		if target and not target.has_method("get_interact_prompt") and target.get_parent():
			target = target.get_parent()
		if target and target.has_method("get_interact_prompt"):
			prompt = str(target.get_interact_prompt(self))
			if Input.is_action_just_pressed("interact") and target.has_method("interact"):
				target.interact(self)
			elif Input.is_action_pressed("interact") and target.has_method("interact_hold"):
				var repair_interval := 0.30 if GameManager.has_perk("speedcola") else 0.62
				_hold_repair_timer += delta
				if _hold_repair_timer >= repair_interval:
					_hold_repair_timer = 0.0
					target.interact_hold(self)
			else:
				_hold_repair_timer = 0.45
	_set_prompt(prompt)


func _set_prompt(text: String) -> void:
	if text != _last_prompt:
		_last_prompt = text
		GameManager.prompt_changed.emit(text)


func _throw_grenade() -> void:
	if weapon_ctrl.grenades <= 0:
		return
	weapon_ctrl.grenades -= 1
	weapon_ctrl.emit_hud()
	AudioManager.play_2d("knife_slash", 0.1, -4.0)
	var g := _grenade_scene.instantiate() as RigidBody3D
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	target_parent.add_child(g)
	g.global_position = camera.global_position - camera.global_transform.basis.z * 0.65
	var throw_dir := (-camera.global_transform.basis.z + Vector3.UP * 0.24).normalized()
	g.linear_velocity = throw_dir * 16.5 + velocity * 0.35


func refill_all_ammo() -> void:
	if weapon_ctrl:
		weapon_ctrl.refill_all_ammo()


func give_weapon(weapon_id: String) -> void:
	if weapon_ctrl:
		weapon_ctrl.give_or_replace_weapon(weapon_id)


func has_weapon(weapon_id: String) -> bool:
	return weapon_ctrl != null and weapon_ctrl.has_weapon(weapon_id)


func pack_current_weapon() -> bool:
	return weapon_ctrl != null and weapon_ctrl.pack_current_weapon()


func get_current_weapon_state() -> Dictionary:
	return weapon_ctrl.get_current_state() if weapon_ctrl else {}

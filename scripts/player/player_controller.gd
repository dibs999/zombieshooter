extends CharacterBody3D
class_name PlayerController

const BASE_WALK_SPEED := 5.2
const BASE_SPRINT_SPEED := 7.6
const CROUCH_SPEED := 3.0
const JUMP_VELOCITY := 4.8
const GRAVITY := 15.0

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
var _bob_time: float = 0.0
var _recoil_pitch: float = 0.0
var _recoil_yaw: float = 0.0
var _last_prompt: String = ""
var _hold_repair_timer: float = 0.0
var _noclip_input: bool = false

var _grenade_scene: PackedScene = preload("res://scenes/fx/frag_grenade_proj.tscn")


func _ready() -> void:
	add_to_group("player")
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	camera.fov = SettingsManager.fov
	SettingsManager.settings_changed.connect(_on_settings_changed)
	GameManager.perks_changed.connect(_on_perks_changed)
	GameManager.round_changed.connect(_on_round_changed)
	GameManager.player_health_changed.emit(hp, max_hp)
	GameManager.player_stamina_changed.emit(stamina, max_stamina)


func _on_settings_changed() -> void:
	if camera and weapon_ctrl and not weapon_ctrl.is_aiming:
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
		var sens := SettingsManager.mouse_sensitivity * (0.65 if weapon_ctrl.is_aiming else 1.0)
		rotate_y(-mm.relative.x * sens)
		var y_sign := 1.0 if SettingsManager.invert_y else -1.0
		head.rotation.x = clampf(head.rotation.x + mm.relative.y * sens * y_sign, -1.42, 1.42)
		weapon_ctrl.add_look_sway(mm.relative)


func _physics_process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	_handle_health_and_downed(delta)
	_handle_movement(delta)
	_handle_interaction(delta)

	if Input.is_action_just_pressed("grenade") and not is_downed:
		_throw_grenade()


func _handle_movement(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	elif Input.is_action_just_pressed("jump") and not is_downed and not is_crouching:
		velocity.y = JUMP_VELOCITY

	is_crouching = Input.is_action_pressed("crouch") or is_downed
	var target_h := 0.85 if is_crouching else 1.62
	head.position.y = lerpf(head.position.y, target_h, delta * 12.0)

	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var dir := (transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()

	var wants_sprint := Input.is_action_pressed("sprint") and input_dir.y < -0.1 and not is_crouching and not weapon_ctrl.is_aiming and not is_downed
	var has_staminup := GameManager.has_perk("staminup")
	var is_sprinting := false

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

	if weapon_ctrl.is_aiming and not is_downed:
		speed *= 0.68

	var accel := 12.0 if is_on_floor() else 4.0
	velocity.x = lerpf(velocity.x, dir.x * speed, accel * delta)
	velocity.z = lerpf(velocity.z, dir.z * speed, accel * delta)
	move_and_slide()

	# Smooth camera recoil recovery & subtle headbob
	_recoil_pitch = lerpf(_recoil_pitch, 0.0, delta * 11.0)
	_recoil_yaw = lerpf(_recoil_yaw, 0.0, delta * 11.0)
	var horiz_speed := Vector2(velocity.x, velocity.z).length()
	if is_on_floor() and horiz_speed > 0.4:
		_bob_time += delta * horiz_speed * 1.9
		camera.position.y = sin(_bob_time * 2.0) * (0.032 if is_sprinting else 0.018)
		camera.position.x = cos(_bob_time) * 0.014
	else:
		camera.position = camera.position.lerp(Vector3.ZERO, delta * 8.0)

	camera.rotation.x = _recoil_pitch
	camera.rotation.y = _recoil_yaw


func add_camera_recoil(pitch: float, yaw: float) -> void:
	_recoil_pitch = clampf(_recoil_pitch + pitch, -0.22, 0.25)
	_recoil_yaw = clampf(_recoil_yaw + randf_range(-yaw, yaw), -0.15, 0.15)


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


func take_damage(amount: float) -> void:
	if GameManager.is_game_over or is_downed:
		return
	hp -= amount
	time_since_damage = 0.0
	AudioManager.play_2d("player_hurt", 0.08, 0.0)
	add_camera_recoil(randf_range(0.03, 0.06), 0.05)

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
	get_tree().current_scene.add_child(g)
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

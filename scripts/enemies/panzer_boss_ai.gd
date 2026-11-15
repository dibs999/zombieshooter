extends CharacterBody3D
class_name PanzerBossAI

@onready var nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var head_area: Area3D = $HeadArea
@onready var body_area: Area3D = $BodyArea
@onready var model_root: Node3D = $ModelRoot
@onready var visor_light: OmniLight3D = $VisorLight
@onready var flame_pivot: Node3D = $FlamePivot
@onready var flame_particles: CPUParticles3D = $FlamePivot/FlameParticles
@onready var flame_light: OmniLight3D = $FlamePivot/FlameLight

var max_hp: float = 1400.0
var hp: float = 1400.0
var move_speed: float = 2.65
var claw_damage: float = 65.0
var flame_tick_damage: float = 12.0
var is_dead: bool = false

var plate_hp: Dictionary = {
	"chest": 320.0,
	"shoulder_l": 220.0,
	"shoulder_r": 220.0,
	"visor": 260.0,
}

var _plate_nodes: Dictionary = {}
var _anim_player: AnimationPlayer = null
var _skeleton: Skeleton3D = null
var _head_bone_idx: int = -1
var _lowerarm_r_bone_idx: int = -1
var _hand_r_bone_idx: int = -1
var _current_anim: String = ""

var _attack_cd: float = 0.0
var _repath_cd: float = 0.0
var _stomp_sfx_cd: float = 0.0
var _flame_burst_timer: float = 0.0
var _flame_cooldown: float = 1.8
var _flame_tick_cd: float = 0.0
var _is_flaming: bool = false

var _gib_scene: PackedScene = preload("res://scenes/fx/gib_chunk.tscn")
var _sparks_scene: PackedScene = preload("res://scenes/fx/impact_sparks.tscn")
var _blood_decal_scene: PackedScene = preload("res://scenes/fx/blood_decal.tscn")

signal died(boss: PanzerBossAI, was_headshot: bool, death_pos: Vector3, force_drop: bool)


func setup(p_round: int = 8, p_hp_override: float = -1.0) -> void:
	max_hp = p_hp_override if p_hp_override > 0.0 else (1400.0 + float(maxi(0, p_round - 8)) * 280.0)
	hp = max_hp
	var scale_f := maxf(1.0, max_hp / 1400.0)
	plate_hp = {
		"chest": 320.0 * scale_f,
		"shoulder_l": 220.0 * scale_f,
		"shoulder_r": 220.0 * scale_f,
		"visor": 260.0 * scale_f,
	}
	if is_node_ready() and model_root.get_child_count() == 0:
		_load_model()


func _ready() -> void:
	add_to_group("zombies")
	add_to_group("panzer_boss")
	head_area.add_to_group("zombie_head")
	head_area.set_meta("zombie_owner", self)
	body_area.set_meta("zombie_owner", self)
	if flame_particles != null and flame_particles.scale_amount_curve == null:
		var sc := Curve.new()
		sc.add_point(Vector2(0.0, 0.38))
		sc.add_point(Vector2(0.42, 1.38))
		sc.add_point(Vector2(1.0, 1.92))
		flame_particles.scale_amount_curve = sc
	if model_root.get_child_count() == 0:
		_load_model()
	_set_flamethrower_active(false)
	AudioManager.play_3d("boss_roar", global_position, 0.06, 2.0, 48.0)
	_play_anim("Walk")


func _load_model() -> void:
	for ch in model_root.get_children():
		model_root.remove_child(ch)
		ch.queue_free()
	_anim_player = null
	_skeleton = null
	_head_bone_idx = -1
	_lowerarm_r_bone_idx = -1
	_hand_r_bone_idx = -1
	_plate_nodes.clear()

	if ResourceLoader.exists("res://assets/models/characters/panzer_boss.glb"):
		var inst := (load("res://assets/models/characters/panzer_boss.glb") as PackedScene).instantiate()
		model_root.add_child(inst)
		_find_nodes(inst)
		_plate_nodes["chest"] = inst.find_child("ArmorPlate_Chest", true, false) as Node3D
		_plate_nodes["shoulder_l"] = inst.find_child("ArmorPlate_Shoulder_L", true, false) as Node3D
		_plate_nodes["shoulder_r"] = inst.find_child("ArmorPlate_Shoulder_R", true, false) as Node3D
		_plate_nodes["visor"] = inst.find_child("Helmet_VisorPlate", true, false) as Node3D


func _find_nodes(n: Node) -> void:
	if n is AnimationPlayer and _anim_player == null:
		_anim_player = n as AnimationPlayer
		for a in ["Idle", "Walk", "Run", "FlameAttack"]:
			if _anim_player.has_animation(a):
				_anim_player.get_animation(a).loop_mode = Animation.LOOP_LINEAR
	elif n is Skeleton3D and _skeleton == null:
		_skeleton = n as Skeleton3D
		_head_bone_idx = _skeleton.find_bone("Head")
		if _head_bone_idx < 0:
			_head_bone_idx = _skeleton.find_bone("head")
		_lowerarm_r_bone_idx = _skeleton.find_bone("lowerarm_r")
		_hand_r_bone_idx = _skeleton.find_bone("hand_r")
	for c in n.get_children():
		_find_nodes(c)


func _play_anim(a: String, force_restart: bool = false) -> void:
	if _anim_player == null or not _anim_player.has_animation(a):
		return
	if not force_restart and _current_anim == a and _anim_player.is_playing():
		return
	var blend := 0.0 if _current_anim == "" else 0.16
	_current_anim = a
	_anim_player.play(a, blend)


func is_plate_intact(plate_key: String) -> bool:
	return float(plate_hp.get(plate_key, 0.0)) > 0.0


func get_intact_plates() -> Array[String]:
	var out: Array[String] = []
	for k in ["chest", "shoulder_l", "shoulder_r", "visor"]:
		if is_plate_intact(k):
			out.append(k)
	return out


func _sync_flame_pivot_to_nozzle() -> void:
	if flame_pivot == null or not is_inside_tree():
		return
	var boss_fwd := -global_transform.basis.z
	boss_fwd.y = 0.0
	boss_fwd = boss_fwd.normalized() if boss_fwd.length_squared() > 0.001 else Vector3.FORWARD
	if _skeleton != null and _hand_r_bone_idx >= 0 and _lowerarm_r_bone_idx >= 0:
		var elbow_pos := _skeleton.to_global(_skeleton.get_bone_global_pose(_lowerarm_r_bone_idx).origin)
		var hand_pos := _skeleton.to_global(_skeleton.get_bone_global_pose(_hand_r_bone_idx).origin)
		var arm_dir := hand_pos - elbow_pos
		if arm_dir.length_squared() > 0.0004:
			arm_dir = arm_dir.normalized()
		else:
			arm_dir = boss_fwd
		var horiz_arm := Vector3(arm_dir.x, 0.0, arm_dir.z)
		horiz_arm = horiz_arm.normalized() if horiz_arm.length_squared() > 0.001 else boss_fwd
		var blend_horiz := boss_fwd.lerp(horiz_arm, 0.35).normalized()
		var aim := Vector3(blend_horiz.x, clampf(arm_dir.y, -0.18, 0.02), blend_horiz.z).normalized()
		flame_pivot.global_position = hand_pos + arm_dir * 0.34 + Vector3(0.0, -0.02, 0.0)
		if aim.cross(Vector3.UP).length_squared() > 0.001:
			flame_pivot.look_at(flame_pivot.global_position + aim, Vector3.UP)


func _set_flamethrower_active(active: bool) -> void:
	_is_flaming = active
	if active:
		_sync_flame_pivot_to_nozzle()
	if flame_particles != null:
		flame_particles.emitting = active
	if flame_light != null:
		flame_light.light_energy = 3.8 if active else 0.0


func _physics_process(delta: float) -> void:
	if is_dead or GameManager.is_game_over:
		if _is_flaming:
			_set_flamethrower_active(false)
		return

	_attack_cd = maxf(0.0, _attack_cd - delta)
	_flame_cooldown = maxf(0.0, _flame_cooldown - delta)
	_stomp_sfx_cd -= delta

	if _skeleton != null and _head_bone_idx >= 0:
		var hpose := _skeleton.get_bone_global_pose(_head_bone_idx)
		head_area.global_position = _skeleton.to_global(hpose.origin) + Vector3(0, 0.16, 0)

	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return

	var to_player := player.global_position - global_position
	var horiz := Vector3(to_player.x, 0.0, to_player.z)
	var dist := horiz.length()
	var fwd := -global_transform.basis.z
	fwd.y = 0.0
	if fwd.length_squared() > 0.001:
		fwd = fwd.normalized()

	# Active Flamethrower Burst
	if _is_flaming:
		_flame_burst_timer -= delta
		_flame_tick_cd -= delta
		if horiz.length_squared() > 0.001:
			_face_direction(horiz.normalized(), delta * 0.7)
		_sync_flame_pivot_to_nozzle()
		if flame_light != null:
			flame_light.light_energy = 3.6 + sin(Time.get_ticks_msec() * 0.03) * 0.9
		if _flame_tick_cd <= 0.0:
			_flame_tick_cd = 0.42
			_apply_flame_cone_damage(player)
		if _flame_burst_timer <= 0.0 or dist > 7.8 or dist < 1.75:
			_set_flamethrower_active(false)
			_flame_cooldown = 3.0
		velocity.x = 0.0
		velocity.z = 0.0
		move_and_slide()
		return

	# Close-range Heavy Claw Stomp / Sweep
	if dist <= 2.30:
		velocity.x = 0.0
		velocity.z = 0.0
		if horiz.length_squared() > 0.001:
			_face_direction(horiz.normalized(), delta)
		if _attack_cd <= 0.0:
			_attack_cd = 1.45
			_play_anim("Attack", true)
			AudioManager.play_3d("explosion", global_position + Vector3(0, 1.2, 0), 0.12, -9.0, 26.0)
			if player.has_method("take_damage"):
				player.take_damage(claw_damage)
		return

	# Medium-range Flamethrower Trigger
	if dist >= 2.35 and dist <= 6.6 and _flame_cooldown <= 0.0 and horiz.length_squared() > 0.01:
		var ang := rad_to_deg(fwd.angle_to(horiz.normalized()))
		if ang <= 42.0:
			_set_flamethrower_active(true)
			_flame_burst_timer = 2.6
			_flame_tick_cd = 0.2
			_play_anim("FlameAttack", true)
			AudioManager.play_3d("boss_roar", global_position + Vector3(0, 1.4, 0), 0.14, -1.5, 40.0)
			return

	# Relentless Juggernaut Pursuit
	_repath_cd -= delta
	if _repath_cd <= 0.0:
		_repath_cd = 0.25 if dist < 14.0 else 0.50
		nav_agent.target_position = player.global_position

	var dir := Vector3.ZERO
	if not nav_agent.is_navigation_finished():
		dir = nav_agent.get_next_path_position() - global_position
		dir.y = 0.0
	if dir.length_squared() < 0.01:
		dir = horiz
	if dir.length_squared() > 0.001:
		dir = dir.normalized()

	var spd := move_speed * (1.28 if dist > 9.0 else 1.0)
	velocity.x = dir.x * spd
	velocity.z = dir.z * spd
	velocity.y = -15.0 * delta if not is_on_floor() else 0.0
	move_and_slide()
	_face_direction(dir, delta)
	if _stomp_sfx_cd <= 0.0:
		_stomp_sfx_cd = 0.72
		AudioManager.play_3d("plank_break", global_position, 0.25, -10.0, 24.0)
	if _attack_cd <= 0.65:
		_play_anim("Run" if spd > 3.0 else "Walk")


func _apply_flame_cone_damage(player: Node3D) -> void:
	var to_p := player.global_position - global_position
	to_p.y = 0.0
	var dist := to_p.length()
	if dist > 6.8 or dist < 0.1:
		return
	var fwd := -global_transform.basis.z
	fwd.y = 0.0
	if fwd.length_squared() > 0.001 and rad_to_deg(fwd.normalized().angle_to(to_p.normalized())) <= 38.0:
		if player.has_method("take_damage"):
			player.take_damage(flame_tick_damage)


func _face_direction(dir: Vector3, delta: float) -> void:
	if dir.length_squared() < 0.001:
		return
	rotation.y = lerp_angle(rotation.y, atan2(-dir.x, -dir.z), delta * 6.5)


func take_damage(amount: float, is_headshot: bool, hit_pos: Vector3, hit_dir: Vector3, is_melee: bool = false) -> bool:
	if is_dead:
		return false

	var eff_dmg := amount
	var hit_plate := ""
	var local_hit := to_local(hit_pos)
	var is_generic_pos := hit_pos.distance_squared_to(global_position) < 0.04

	if is_headshot:
		if is_plate_intact("visor"):
			hit_plate = "visor"
			eff_dmg *= 0.35
		else:
			# Exposed fiery skull/face inside shattered diving helmet = critical weakpoint!
			eff_dmg *= 1.85
	elif not is_generic_pos:
		if local_hit.y >= 1.55 and local_hit.x <= -0.28 and is_plate_intact("shoulder_l"):
			hit_plate = "shoulder_l"
			eff_dmg *= 0.55
		elif local_hit.y >= 1.55 and local_hit.x >= 0.28 and is_plate_intact("shoulder_r"):
			hit_plate = "shoulder_r"
			eff_dmg *= 0.55
		elif is_plate_intact("chest"):
			hit_plate = "chest"
			eff_dmg *= 0.50
		else:
			# Exposed glowing furnace chest core!
			eff_dmg *= 1.25
	else:
		if is_plate_intact("chest"):
			hit_plate = "chest"
			eff_dmg *= 0.55

	if hit_plate != "":
		plate_hp[hit_plate] = float(plate_hp[hit_plate]) - amount
		_spawn_sparks(hit_pos if not is_generic_pos else (global_position + Vector3(0, 1.8, 0)))
		if float(plate_hp[hit_plate]) <= 0.0:
			plate_hp[hit_plate] = 0.0
			_shatter_plate(hit_plate, hit_pos, hit_dir)

	hp -= eff_dmg
	if hp <= 0.0:
		_die(is_headshot, is_melee, false)
		return true

	GameManager.add_points(20, "Armor Hit" if hit_plate != "" else "Boss Hit")
	return false


func _fx_parent() -> Node:
	var p := get_parent()
	if p != null and p != get_tree().root:
		return p
	return get_tree().current_scene if get_tree().current_scene != null else p


func _shatter_plate(plate_key: String, hit_pos: Vector3, hit_dir: Vector3) -> void:
	var pnode := _plate_nodes.get(plate_key, null) as Node3D
	var origin := hit_pos
	if pnode != null:
		pnode.visible = false
		origin = global_position + Vector3(0, 2.25 if plate_key == "visor" else 1.75, 0)
	_spawn_sparks(origin)
	AudioManager.play_3d("explosion", origin, 0.22, -7.0, 32.0)

	if not is_inside_tree():
		return
	var parent_node := _fx_parent()
	if parent_node == null:
		return
	var base_dir := -hit_dir.normalized() if hit_dir.length_squared() > 0.001 else Vector3.UP
	for _i in range(4):
		var g := _gib_scene.instantiate() as GibChunk
		parent_node.add_child(g)
		g.global_position = origin + Vector3(randf_range(-0.15, 0.15), randf_range(-0.1, 0.15), randf_range(-0.15, 0.15))
		var impulse := base_dir * randf_range(1.8, 4.2) + Vector3(randf_range(-2.5, 2.5), randf_range(2.8, 5.2), randf_range(-2.5, 2.5))
		g.setup("armor", impulse)

	if not _is_flaming:
		_play_anim("Hit", true)


func _spawn_sparks(origin: Vector3) -> void:
	if not is_inside_tree():
		return
	var parent_node := _fx_parent()
	if parent_node == null:
		return
	var fx := _sparks_scene.instantiate() as Node3D
	parent_node.add_child(fx)
	fx.global_position = origin


func kill_by_nuke() -> void:
	if is_dead:
		return
	# Nuke deals massive shockwave damage and cracks chest armor, killing if below 55% HP
	take_damage(max_hp * 0.55, false, global_position, Vector3.UP, false)


func _die(was_headshot: bool, _is_melee: bool, from_nuke: bool) -> void:
	is_dead = true
	_set_flamethrower_active(false)
	remove_from_group("zombies")
	remove_from_group("panzer_boss")
	set_physics_process(false)
	head_area.set_deferred("monitoring", false)
	head_area.set_deferred("monitorable", false)
	body_area.set_deferred("monitoring", false)
	body_area.set_deferred("monitorable", false)
	($BodyCollision as CollisionShape3D).set_deferred("disabled", true)

	if visor_light != null:
		var tw := visor_light.create_tween()
		tw.tween_property(visor_light, "light_energy", 0.0, 1.0)

	if not from_nuke:
		GameManager.stats["kills"] += 1
		if was_headshot:
			GameManager.stats["headshots"] += 1
		GameManager.add_points(1500, "Panzersoldat Boss")

	AudioManager.play_3d("explosion", global_position + Vector3(0, 1.4, 0), 0.1, 1.5, 44.0)
	_spawn_sparks(global_position + Vector3(0, 1.6, 0))
	if is_inside_tree():
		var parent_node := _fx_parent()
		if parent_node != null:
			var dec := _blood_decal_scene.instantiate() as BloodDecal
			dec.setup(1.65)
			parent_node.add_child(dec)
			dec.global_position = Vector3(global_position.x, 0.0, global_position.z)

	_play_anim("Death", true)
	emit_signal("died", self, was_headshot, global_position, not from_nuke)
	get_tree().create_timer(3.0).timeout.connect(queue_free)

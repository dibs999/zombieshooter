extends Node3D
class_name WeaponController

@export var max_weapons: int = 2

@onready var player: PlayerController = get_parent().get_parent().get_parent() as PlayerController
@onready var camera: Camera3D = get_parent() as Camera3D
@onready var viewmodel_pivot: Node3D = $ViewmodelPivot
@onready var model_holder: Node3D = $ViewmodelPivot/ModelHolder
@onready var knife_holder: Node3D = $ViewmodelPivot/KnifeHolder
@onready var muzzle_light: OmniLight3D = $ViewmodelPivot/MuzzleLight
@onready var muzzle_flash: MeshInstance3D = $ViewmodelPivot/MuzzleFlash

var weapons: Array[Dictionary] = []
var active_idx: int = 0
var grenades: int = 2

var is_aiming: bool = false
var is_reloading: bool = false
var is_meleeing: bool = false
var _fire_cooldown: float = 0.0
var _reload_timer: float = 0.0
var _reload_total: float = 1.45
var _melee_timer: float = 0.0
var _flash_timer: float = 0.0

var _was_aiming: bool = false
var _was_key3_pressed: bool = false
var _sfx_mag_out_done: bool = false
var _sfx_mag_in_done: bool = false
var _sfx_bolt_done: bool = false

const MELEE_DURATION := 0.36

var _kick_pos: Vector3 = Vector3.ZERO
var _kick_rot: Vector3 = Vector3.ZERO
var _sway_target: Vector2 = Vector2.ZERO
var _sway_offset: Vector2 = Vector2.ZERO
var _walk_bob: float = 0.0
var _bob_weight: float = 0.0
var _horiz_smooth: float = 0.0
var _sprint_blend: float = 0.0
var _initial_equip_done: bool = false
var _hud: Node = null

# Moving weapon sub-part animation state
var _part_nodes: Dictionary = {}
var _part_rest: Dictionary = {}
var _slide_kick: float = 0.0
var _bolt_kick: float = 0.0
var _bolt_cycle: float = 0.0
var _pump_cycle: float = 0.0
var _trigger_pull: float = 0.0
var _glow_pulse: float = 0.0

var _pap_shader: Shader = preload("res://assets/shaders/pap_camo.gdshader")
var _pap_albedo: Texture2D = preload("res://assets/textures/weapons/pap_albedo.png")
var _pap_emission: Texture2D = preload("res://assets/textures/weapons/pap_emission.png")
var _pap_material: ShaderMaterial
var _flash_material: StandardMaterial3D

var _blood_fx_scene: PackedScene = preload("res://scenes/fx/blood_burst.tscn")
var _sparks_fx_scene: PackedScene = preload("res://scenes/fx/impact_sparks.tscn")
var _ray_bolt_scene: PackedScene = preload("res://scenes/fx/ray_bolt.tscn")
var _chain_arc_scene: PackedScene = preload("res://scenes/fx/wpn_chain_arc.tscn")
var _shell_casing_scene: PackedScene = preload("res://scenes/fx/wpn_shell_casing.tscn")
var _bullet_decal_scene: PackedScene = preload("res://scenes/fx/wpn_bullet_decal.tscn")
var _electric_ring_scene: PackedScene = preload("res://scenes/fx/wpn_electric_ring.tscn")


static func _exp_alpha(speed: float, delta: float) -> float:
	return clampf(1.0 - exp(-speed * maxf(delta, 0.0)), 0.0, 1.0)


func _ready() -> void:
	_pap_material = ShaderMaterial.new()
	_pap_material.shader = _pap_shader
	_pap_material.set_shader_parameter("albedo_tex", _pap_albedo)
	_pap_material.set_shader_parameter("emission_tex", _pap_emission)

	if muzzle_flash and muzzle_flash.mesh and muzzle_flash.mesh.surface_get_material(0) is StandardMaterial3D:
		_flash_material = muzzle_flash.mesh.surface_get_material(0).duplicate() as StandardMaterial3D
		muzzle_flash.material_override = _flash_material
		for ch in muzzle_flash.get_children():
			if ch is MeshInstance3D:
				(ch as MeshInstance3D).material_override = _flash_material

	if ResourceLoader.exists("res://assets/models/weapons/combat_knife.glb"):
		var k_inst := (load("res://assets/models/weapons/combat_knife.glb") as PackedScene).instantiate()
		knife_holder.add_child(k_inst)
	knife_holder.visible = false
	muzzle_light.light_energy = 0.0
	muzzle_flash.visible = false

	if not GameManager.perks_changed.is_connected(_on_perks_changed):
		GameManager.perks_changed.connect(_on_perks_changed)
	_sync_mule_kick()

	weapons.append(WeaponDB.create_weapon_state("m1911", false))
	_equip_weapon(0)


func _get_hud() -> Node:
	if _hud != null and is_instance_valid(_hud) and _hud.is_inside_tree():
		return _hud
	_hud = get_tree().get_first_node_in_group("hud")
	return _hud


func _on_perks_changed(_perks: Array[String]) -> void:
	_sync_mule_kick()


func _sync_mule_kick() -> void:
	var has_mk := GameManager.has_perk("mulekick")
	max_weapons = 3 if has_mk else 2
	if not has_mk and weapons.size() > 2:
		weapons.resize(2)
		if active_idx >= 2:
			_equip_weapon(1)
		else:
			emit_hud()


func snap_viewmodel() -> void:
	if weapons.is_empty():
		return
	var cur: Dictionary = weapons[active_idx]
	_kick_pos = Vector3.ZERO
	_kick_rot = Vector3.ZERO
	_sway_target = Vector2.ZERO
	_sway_offset = Vector2.ZERO
	_bob_weight = 0.0
	_horiz_smooth = 0.0
	_sprint_blend = 0.0
	_slide_kick = 0.0
	_bolt_kick = 0.0
	_bolt_cycle = 0.0
	_pump_cycle = 0.0
	_trigger_pull = 0.0
	_glow_pulse = 0.0
	for pname in _part_nodes.keys():
		var pnode := _part_nodes[pname] as Node3D
		if pnode and is_instance_valid(pnode) and _part_rest.has(pname):
			pnode.transform = _part_rest[pname]
	viewmodel_pivot.position = WeaponDB.get_stat(cur, "ads_pos") if is_aiming else WeaponDB.get_stat(cur, "hip_pos")
	viewmodel_pivot.rotation = Vector3(-0.28, 0.22, 0.12) if is_reloading else Vector3.ZERO
	model_holder.rotation.y = 0.0 if (is_aiming or is_meleeing) else deg_to_rad(3.5)
	if camera:
		var base_fov := SettingsManager.fov
		camera.fov = base_fov * float(WeaponDB.get_stat(cur, "ads_fov_mult")) if is_aiming else base_fov


func add_look_sway(rel: Vector2) -> void:
	var max_sway := 0.010 if is_aiming else 0.036
	var scale := 0.00028 if is_aiming else 0.00075
	_sway_target.x = clampf(_sway_target.x - rel.x * scale, -max_sway, max_sway)
	_sway_target.y = clampf(_sway_target.y + rel.y * scale, -max_sway, max_sway)


func get_crosshair_spread_px() -> float:
	if weapons.is_empty():
		return 10.0
	var cur := weapons[active_idx]
	var base := float(WeaponDB.get_stat(cur, "spread_ads")) if is_aiming else float(WeaponDB.get_stat(cur, "spread_hip"))
	if GameManager.has_perk("deadshot") and not is_aiming:
		base *= 0.55
	var move_add := clampf(_horiz_smooth * 1.15, 0.0, 9.0)
	var kick_add := clampf(_kick_pos.z * 140.0, 0.0, 14.0)
	return clampf(base * 520.0 + move_add + kick_add, 4.0, 56.0)


func _process(delta: float) -> void:
	if GameManager.is_game_over or get_tree().paused:
		return

	_fire_cooldown = maxf(0.0, _fire_cooldown - delta)
	if _flash_timer > 0.0:
		_flash_timer -= delta
		if _flash_timer <= 0.0:
			muzzle_light.light_energy = 0.0
			muzzle_flash.visible = false

	_handle_weapon_inputs(delta)
	_animate_viewmodel(delta)

	var hud := _get_hud()
	if hud and hud.has_method("set_crosshair_spread"):
		hud.call("set_crosshair_spread", get_crosshair_spread_px(), is_aiming or is_reloading or is_meleeing)


func _handle_weapon_inputs(delta: float) -> void:
	if weapons.is_empty():
		return

	if is_meleeing:
		_melee_timer -= delta
		if _melee_timer <= 0.0:
			is_meleeing = false
			knife_holder.visible = false
			model_holder.visible = true
			var cur_w: Dictionary = weapons[active_idx]
			var hip_pos: Vector3 = WeaponDB.get_stat(cur_w, "hip_pos")
			viewmodel_pivot.position = hip_pos + Vector3(0.0, -0.10, 0.04)
			viewmodel_pivot.rotation = Vector3(-0.22, 0.0, 0.0)
		return

	if is_reloading:
		_reload_timer -= delta
		var prog := clampf(1.0 - _reload_timer / maxf(0.05, _reload_total), 0.0, 1.0)
		if not _sfx_mag_out_done and prog >= 0.16:
			_sfx_mag_out_done = true
			AudioManager.play_2d("reload_mag_out", 0.05, -2.0)
		if not _sfx_mag_in_done and prog >= 0.68:
			_sfx_mag_in_done = true
			AudioManager.play_2d("reload_mag_in", 0.05, -1.5)
		if not _sfx_bolt_done and prog >= 0.85:
			_sfx_bolt_done = true
			AudioManager.play_2d("reload_bolt", 0.05, -2.5)
		if _reload_timer <= 0.0:
			_finish_reload()
		return

	var key3_now := Input.is_key_pressed(KEY_3)
	var key3_just := key3_now and not _was_key3_pressed
	_was_key3_pressed = key3_now

	if player and not player.is_downed:
		if Input.is_action_just_pressed("weapon_next") and weapons.size() > 1:
			_equip_weapon((active_idx + 1) % weapons.size())
			return
		if Input.is_action_just_pressed("weapon_prev") and weapons.size() > 1:
			_equip_weapon((active_idx - 1 + weapons.size()) % weapons.size())
			return
		if Input.is_action_just_pressed("slot_1") and weapons.size() >= 1 and active_idx != 0:
			_equip_weapon(0)
			return
		if Input.is_action_just_pressed("slot_2") and weapons.size() >= 2 and active_idx != 1:
			_equip_weapon(1)
			return
		var slot3_pressed := (InputMap.has_action("slot_3") and Input.is_action_just_pressed("slot_3")) or key3_just
		if slot3_pressed and weapons.size() >= 3 and active_idx != 2:
			_equip_weapon(2)
			return

		if Input.is_action_just_pressed("melee"):
			_perform_melee()
			return

	var sliding_block := player != null and player.is_sliding
	is_aiming = Input.is_action_pressed("aim") and not is_reloading and not is_meleeing and not sliding_block and (player == null or not player.is_downed)
	if is_aiming and not _was_aiming and GameManager.has_perk("deadshot"):
		_apply_deadshot_ads_snap()
	_was_aiming = is_aiming

	if Input.is_action_just_pressed("reload"):
		start_reload()
		return

	var cur: Dictionary = weapons[active_idx]
	var mode := str(WeaponDB.get_stat(cur, "fire_mode"))
	var wants_fire := Input.is_action_pressed("fire") if mode == "auto" else Input.is_action_just_pressed("fire")
	if wants_fire and _fire_cooldown <= 0.0:
		_try_fire()


static func _is_enemy_dead(z: Node) -> bool:
	if z == null or not is_instance_valid(z):
		return true
	if z is ZombieAI:
		return (z as ZombieAI).state == ZombieAI.State.DEAD
	if z.get("is_dead") == true:
		return true
	return false


func _apply_deadshot_ads_snap() -> void:
	if player == null or camera == null:
		return
	var cam_pos := camera.global_position
	var cam_fwd := -camera.global_transform.basis.z
	var min_dot := cos(deg_to_rad(8.5))
	var best_dot := min_dot
	var best_head_pos := Vector3.INF
	var space := get_world_3d().direct_space_state if get_world_3d() else null

	for z in get_tree().get_nodes_in_group("zombies"):
		var z3 := z as Node3D
		if _is_enemy_dead(z3):
			continue
		var head_node := z3.get("head_area") as Node3D
		var head_pos := head_node.global_position if (head_node and is_instance_valid(head_node)) else (z3.global_position + Vector3(0.0, 1.50, 0.0))
		var to_head := head_pos - cam_pos
		var dist := to_head.length()
		if dist < 0.8 or dist > 28.0:
			continue
		var dir := to_head / dist
		var d := cam_fwd.dot(dir)
		if d > best_dot:
			if space:
				var q := PhysicsRayQueryParameters3D.create(cam_pos, head_pos)
				q.collision_mask = 1
				q.collide_with_areas = false
				var wall_hit := space.intersect_ray(q)
				if not wall_hit.is_empty():
					continue
			best_dot = d
			best_head_pos = head_pos

	if best_head_pos != Vector3.INF:
		var target_dir := (best_head_pos - cam_pos).normalized()
		var cur_yaw := player.rotation.y
		var target_yaw := atan2(-target_dir.x, -target_dir.z)
		var yaw_diff := wrapf(target_yaw - cur_yaw, -PI, PI)
		var horiz_len := maxf(0.001, Vector2(target_dir.x, target_dir.z).length())
		var target_pitch := atan2(target_dir.y, horiz_len)
		var pitch_diff := target_pitch - player.head.rotation.x
		player.rotate_y(clampf(yaw_diff * 0.82, -0.15, 0.15))
		player.head.rotation.x = clampf(player.head.rotation.x + clampf(pitch_diff * 0.82, -0.15, 0.15), -1.42, 1.42)


func _animate_viewmodel(delta: float) -> void:
	if weapons.is_empty():
		return
	var cur: Dictionary = weapons[active_idx]
	var hip_pos: Vector3 = WeaponDB.get_stat(cur, "hip_pos")
	var ads_pos: Vector3 = WeaponDB.get_stat(cur, "ads_pos")
	var target_pos := ads_pos if is_aiming else hip_pos
	var target_rot := Vector3.ZERO

	# Smooth horizontal speed & grounded bob weight (zero binary threshold snapping)
	var raw_horiz := 0.0
	var grounded := false
	var sprinting := false
	var sliding := false
	if player:
		raw_horiz = Vector2(player.velocity.x, player.velocity.z).length()
		grounded = player.is_grounded()
		sliding = player.is_sliding
		sprinting = player.is_sprinting and grounded and not is_aiming and not is_reloading and not is_meleeing and not sliding

	_horiz_smooth = lerpf(_horiz_smooth, raw_horiz, _exp_alpha(14.0, delta))
	if _horiz_smooth < 0.0001 and raw_horiz == 0.0:
		_horiz_smooth = 0.0
	_sprint_blend = lerpf(_sprint_blend, 1.0 if sprinting else 0.0, _exp_alpha(9.0, delta))
	if _sprint_blend < 0.0001 and not sprinting:
		_sprint_blend = 0.0

	var move_factor := clampf((_horiz_smooth - 0.25) / 1.5, 0.0, 1.0)
	var target_bob_weight := move_factor if (grounded and not is_aiming and not is_meleeing and not sliding) else 0.0
	_bob_weight = lerpf(_bob_weight, target_bob_weight, _exp_alpha(10.0, delta))
	if _bob_weight < 0.0001 and target_bob_weight == 0.0:
		_bob_weight = 0.0

	if _bob_weight > 0.0001:
		var bob_dt := clampf(delta, 0.0, 0.15)
		_walk_bob = fmod(_walk_bob + bob_dt * maxf(_horiz_smooth, 0.5) * 1.8, TAU * 100.0)
		var sprint_amp := lerpf(1.0, 1.45, _sprint_blend)
		target_pos.x += cos(_walk_bob) * 0.010 * sprint_amp * _bob_weight
		target_pos.y += absf(sin(_walk_bob)) * 0.012 * sprint_amp * _bob_weight
		target_rot.z -= cos(_walk_bob) * 0.014 * _bob_weight

	# CoD tactical diagonal sprint cant
	if _sprint_blend > 0.0001:
		target_pos += Vector3(-0.045, -0.030, 0.022) * _sprint_blend
		target_rot += Vector3(-0.14, 0.34, 0.16) * _sprint_blend

	if sliding and not is_aiming and not is_reloading and not is_meleeing:
		target_pos += Vector3(-0.028, -0.022, 0.020)
		target_rot += Vector3(-0.06, 0.16, 0.22)

	# Two-stage exponential sway & recoil kick decay (strictly monotonic, never overshoots)
	_sway_target = _sway_target.lerp(Vector2.ZERO, _exp_alpha(10.0, delta))
	_sway_offset = _sway_offset.lerp(_sway_target, _exp_alpha(18.0, delta))
	_kick_pos = _kick_pos.lerp(Vector3.ZERO, _exp_alpha(14.0, delta))
	_kick_rot = _kick_rot.lerp(Vector3.ZERO, _exp_alpha(14.0, delta))

	if _sway_target.length_squared() < 1e-10:
		_sway_target = Vector2.ZERO
	if _sway_offset.length_squared() < 1e-10:
		_sway_offset = Vector2.ZERO
	if _kick_pos.length_squared() < 1e-10:
		_kick_pos = Vector3.ZERO
	if _kick_rot.length_squared() < 1e-10:
		_kick_rot = Vector3.ZERO

	if is_meleeing:
		var t := clampf(1.0 - (_melee_timer / MELEE_DURATION), 0.0, 1.0)
		target_pos = Vector3(0.14 - t * 0.34, -0.13 - sin(t * PI) * 0.02, -0.28 - sin(t * PI) * 0.28)
		target_rot = Vector3(-0.4, 0.9 - t * 1.8, 0.6)
	else:
		if is_reloading:
			target_pos += Vector3(0.0, -0.105, 0.035)
			target_rot += Vector3(-0.28, 0.22, 0.12)

		target_pos.x += _sway_offset.x
		target_pos.y += _sway_offset.y
		var rot_sway_mult := 0.8 if is_aiming else 1.6
		target_rot.y -= _sway_offset.x * rot_sway_mult
		target_rot.x += _sway_offset.y * (rot_sway_mult * 0.75)
		target_rot.z += _sway_offset.x * (rot_sway_mult * 0.45)

		target_pos += _kick_pos
		target_rot += _kick_rot

	var pos_speed := 24.0 if is_meleeing else (20.0 if is_aiming else 16.0)
	var rot_speed := 24.0 if is_meleeing else (20.0 if is_aiming else 18.0)
	viewmodel_pivot.position = viewmodel_pivot.position.lerp(target_pos, _exp_alpha(pos_speed, delta))
	viewmodel_pivot.rotation = viewmodel_pivot.rotation.lerp(target_rot, _exp_alpha(rot_speed, delta))
	if viewmodel_pivot.position.distance_squared_to(target_pos) < 1e-10:
		viewmodel_pivot.position = target_pos
	if viewmodel_pivot.rotation.distance_squared_to(target_rot) < 1e-10:
		viewmodel_pivot.rotation = target_rot

	var target_cant := 0.0 if (is_aiming or is_meleeing) else deg_to_rad(3.5)
	model_holder.rotation.y = lerpf(model_holder.rotation.y, target_cant, _exp_alpha(16.0, delta))
	if absf(model_holder.rotation.y - target_cant) < 0.00001:
		model_holder.rotation.y = target_cant

	_animate_weapon_parts(delta, cur)

	# Smooth ADS FOV + CoD sprint speed-widening
	if camera:
		var base_fov := SettingsManager.fov
		var target_fov := base_fov * float(WeaponDB.get_stat(cur, "ads_fov_mult")) if is_aiming else base_fov
		if not is_aiming:
			target_fov += 5.5 * _sprint_blend
		camera.fov = lerpf(camera.fov, target_fov, _exp_alpha(10.0, delta))
		if absf(camera.fov - target_fov) < 0.0001:
			camera.fov = target_fov


func _animate_weapon_parts(delta: float, cur: Dictionary) -> void:
	_slide_kick = lerpf(_slide_kick, 0.0, _exp_alpha(18.0, delta))
	_bolt_kick = lerpf(_bolt_kick, 0.0, _exp_alpha(24.0, delta))
	_trigger_pull = lerpf(_trigger_pull, 0.0, _exp_alpha(22.0, delta))
	if _bolt_cycle > 0.0:
		_bolt_cycle = maxf(0.0, _bolt_cycle - delta * 2.1)
	if _pump_cycle > 0.0:
		_pump_cycle = maxf(0.0, _pump_cycle - delta * 2.3)
	_glow_pulse += delta * 4.5

	var r_kind := str(WeaponDB.get_stat(cur, "reload_kind"))
	var u := clampf(1.0 - _reload_timer / maxf(0.05, _reload_total), 0.0, 1.0) if is_reloading else 0.0

	var slide := _part_nodes.get("Slide") as Node3D
	if slide and is_instance_valid(slide) and _part_rest.has("Slide"):
		var rest: Transform3D = _part_rest["Slide"]
		var empty_lock := 0.030 if (int(cur.get("mag", 1)) == 0 and not is_reloading) else 0.0
		var reload_rack := 0.036 * sin(clampf((u - 0.80) / 0.16, 0.0, 1.0) * PI) if (is_reloading and u > 0.80 and u < 0.96) else 0.0
		var z_off := maxf(empty_lock, maxf(_slide_kick * 0.042, reload_rack))
		slide.position = slide.position.lerp(rest.origin + Vector3(0.0, 0.0, z_off), _exp_alpha(28.0, delta))

	var bolt := _part_nodes.get("Bolt") as Node3D
	if bolt and is_instance_valid(bolt) and _part_rest.has("Bolt"):
		var rest: Transform3D = _part_rest["Bolt"]
		var target_p := rest.origin
		var target_r := rest.basis.get_euler()
		if r_kind == "bolt_clip" and _bolt_cycle > 0.0:
			var bp := 1.0 - _bolt_cycle
			if bp < 0.22:
				target_r.z += deg_to_rad(56.0) * (bp / 0.22)
			elif bp < 0.52:
				target_r.z += deg_to_rad(56.0)
				target_p.z += 0.058 * ((bp - 0.22) / 0.30)
			elif bp < 0.80:
				target_r.z += deg_to_rad(56.0)
				target_p.z += 0.058 * (1.0 - (bp - 0.52) / 0.28)
			else:
				target_r.z += deg_to_rad(56.0) * (1.0 - (bp - 0.80) / 0.20)
		elif is_reloading and u > 0.78 and u < 0.97:
			var rp := sin(clampf((u - 0.78) / 0.19, 0.0, 1.0) * PI)
			if r_kind == "bolt_clip":
				target_r.z += deg_to_rad(52.0) * rp
			target_p.z += 0.052 * rp
		else:
			target_p.z += _bolt_kick * 0.040 + _pump_cycle * 0.036
		bolt.position = bolt.position.lerp(target_p, _exp_alpha(28.0, delta))
		bolt.rotation = bolt.rotation.lerp(target_r, _exp_alpha(28.0, delta))

	var pump := _part_nodes.get("Pump") as Node3D
	if pump and is_instance_valid(pump) and _part_rest.has("Pump"):
		var rest: Transform3D = _part_rest["Pump"]
		var p_off := sin((1.0 - _pump_cycle) * PI) * 0.075 if _pump_cycle > 0.0 else 0.0
		pump.position = pump.position.lerp(rest.origin + Vector3(0.0, 0.0, p_off), _exp_alpha(26.0, delta))

	var mag := _part_nodes.get("Magazine") as Node3D
	if mag and is_instance_valid(mag) and _part_rest.has("Magazine"):
		var rest: Transform3D = _part_rest["Magazine"]
		var target_p := rest.origin
		var target_r := rest.basis.get_euler()
		if is_reloading:
			var drop := 0.0
			if u < 0.42:
				drop = clampf((u - 0.12) / 0.28, 0.0, 1.0)
			elif u < 0.56:
				drop = 1.0
			elif u < 0.78:
				drop = 1.0 - clampf((u - 0.56) / 0.20, 0.0, 1.0)
			target_p += Vector3(0.0, -0.115 * drop, 0.025 * drop)
			target_r.x += 0.18 * drop
		mag.position = mag.position.lerp(target_p, _exp_alpha(20.0, delta))
		mag.rotation = mag.rotation.lerp(target_r, _exp_alpha(20.0, delta))

	var cover := _part_nodes.get("FeedCover") as Node3D
	if cover and is_instance_valid(cover) and _part_rest.has("FeedCover"):
		var rest: Transform3D = _part_rest["FeedCover"]
		var target_r := rest.basis.get_euler()
		if is_reloading and u > 0.08 and u < 0.86:
			var open_f := clampf(minf((u - 0.08) / 0.14, (0.86 - u) / 0.12), 0.0, 1.0)
			target_r.x -= deg_to_rad(56.0) * open_f
		cover.rotation = cover.rotation.lerp(target_r, _exp_alpha(18.0, delta))

	var drum := _part_nodes.get("Drum") as Node3D
	if drum and is_instance_valid(drum) and _part_rest.has("Drum"):
		var rest: Transform3D = _part_rest["Drum"]
		var target_p := rest.origin
		if is_reloading and u > 0.22 and u < 0.72:
			var out_f := clampf(minf((u - 0.22) / 0.16, (0.72 - u) / 0.16), 0.0, 1.0)
			target_p += Vector3(-0.085, -0.065, 0.0) * out_f
		drum.position = drum.position.lerp(target_p, _exp_alpha(18.0, delta))

	var cells := _part_nodes.get("PlasmaCells") as Node3D
	if cells and is_instance_valid(cells) and _part_rest.has("PlasmaCells"):
		var rest: Transform3D = _part_rest["PlasmaCells"]
		var target_p := rest.origin
		var target_r := rest.basis.get_euler()
		if is_reloading and u > 0.14 and u < 0.82:
			var pop_f := clampf(minf((u - 0.14) / 0.18, (0.82 - u) / 0.16), 0.0, 1.0)
			target_p += Vector3(0.0, 0.065, -0.045) * pop_f
			target_r.x += 0.28 * pop_f
		cells.position = cells.position.lerp(target_p, _exp_alpha(18.0, delta))
		cells.rotation = cells.rotation.lerp(target_r, _exp_alpha(18.0, delta))

	var tubes := _part_nodes.get("VacuumTubes") as Node3D
	if tubes and is_instance_valid(tubes) and _part_rest.has("VacuumTubes"):
		var rest: Transform3D = _part_rest["VacuumTubes"]
		var bob := sin(_glow_pulse) * 0.0012
		tubes.position = tubes.position.lerp(rest.origin + Vector3(0.0, bob, 0.0), _exp_alpha(16.0, delta))

	var trig := _part_nodes.get("Trigger") as Node3D
	if trig and is_instance_valid(trig) and _part_rest.has("Trigger"):
		var rest: Transform3D = _part_rest["Trigger"]
		var target_r := rest.basis.get_euler()
		target_r.x += deg_to_rad(18.0) * _trigger_pull
		trig.rotation = trig.rotation.lerp(target_r, _exp_alpha(28.0, delta))


func _get_support_hand_transform(weapon_id: String) -> Dictionary:
	match weapon_id:
		"m1911":
			return {"pos": Vector3(-0.012, -0.044, 0.006), "rot": Vector3(deg_to_rad(10.0), deg_to_rad(-24.0), deg_to_rad(-10.0))}
		"raygun":
			return {"pos": Vector3(-0.015, -0.056, -0.018), "rot": Vector3(deg_to_rad(10.0), deg_to_rad(-20.0), deg_to_rad(-8.0))}
		"mp40":
			return {"pos": Vector3(-0.012, -0.024, -0.175), "rot": Vector3(0.0, deg_to_rad(6.0), 0.0)}
		"stg44":
			return {"pos": Vector3(-0.010, -0.008, -0.275), "rot": Vector3(0.0, deg_to_rad(4.0), 0.0)}
		"trench_shotgun":
			return {"pos": Vector3(-0.010, -0.010, -0.265), "rot": Vector3(0.0, deg_to_rad(4.0), 0.0)}
		"m14":
			return {"pos": Vector3(-0.010, -0.010, -0.255), "rot": Vector3(0.0, deg_to_rad(4.0), 0.0)}
		"kar98k":
			return {"pos": Vector3(-0.010, -0.008, -0.240), "rot": Vector3(0.0, deg_to_rad(4.0), 0.0)}
		"mg42":
			return {"pos": Vector3(-0.018, -0.032, -0.205), "rot": Vector3(0.0, deg_to_rad(8.0), 0.0)}
		"wunderwaffe":
			return {"pos": Vector3(-0.010, -0.014, -0.255), "rot": Vector3(0.0, deg_to_rad(4.0), 0.0)}
		_:
			return {"pos": Vector3(-0.012, -0.018, -0.20), "rot": Vector3.ZERO}


func _equip_weapon(idx: int) -> void:
	active_idx = clampi(idx, 0, weapons.size() - 1)
	is_reloading = false
	is_meleeing = false
	is_aiming = false
	_was_aiming = false
	_flash_timer = 0.0
	_slide_kick = 0.0
	_bolt_kick = 0.0
	_bolt_cycle = 0.0
	_pump_cycle = 0.0
	_trigger_pull = 0.0
	_part_nodes.clear()
	_part_rest.clear()
	muzzle_light.light_energy = 0.0
	muzzle_flash.visible = false
	knife_holder.visible = false
	model_holder.visible = true
	for ch in model_holder.get_children():
		model_holder.remove_child(ch)
		ch.queue_free()

	var cur := weapons[active_idx]
	var wid := str(cur.get("id", "m1911"))
	var model_path := str(WeaponDB.get_stat(cur, "model"))
	if ResourceLoader.exists(model_path):
		var inst := (load(model_path) as PackedScene).instantiate()
		model_holder.add_child(inst)
		_cache_weapon_parts(inst)
		if bool(cur.get("packed", false)):
			_apply_pap_material(inst)

	# Attach sculpted first-person gloved hands (exempt from PaP material override)
	var hands_root := Node3D.new()
	hands_root.name = "FirstPersonHands"
	model_holder.add_child(hands_root)
	if ResourceLoader.exists("res://assets/models/weapons/fp_right_hand.glb"):
		var rh := (load("res://assets/models/weapons/fp_right_hand.glb") as PackedScene).instantiate()
		hands_root.add_child(rh)
	if ResourceLoader.exists("res://assets/models/weapons/fp_left_hand.glb"):
		var lh := (load("res://assets/models/weapons/fp_left_hand.glb") as PackedScene).instantiate() as Node3D
		var xform: Dictionary = _get_support_hand_transform(wid)
		lh.position = xform["pos"]
		lh.rotation = xform["rot"]
		hands_root.add_child(lh)
	_grade_hand_materials(hands_root)

	if not _initial_equip_done:
		_initial_equip_done = true
		snap_viewmodel()
	else:
		_sway_target = Vector2.ZERO
		_sway_offset = Vector2.ZERO
		_kick_pos = Vector3(0.0, -0.05, 0.04)
		_kick_rot = Vector3(-0.10, 0.0, 0.0)
	emit_hud()


func _grade_hand_materials(root: Node) -> void:
	WeaponController.grade_hand_materials(root)


static func grade_hand_materials(root: Node) -> void:
	# Darken/weather skin & leather so hands read as shadowed gear, not pale clay
	var tints := {
		"FPSkin": Color(0.66, 0.55, 0.47),
		"TacticalLeather": Color(0.72, 0.68, 0.62),
		"GloveReinforceLeather": Color(0.8, 0.76, 0.72),
		"SleeveWool": Color(0.62, 0.66, 0.55),
		"KnitCuff": Color(0.48, 0.72, 0.58),
	}
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is MeshInstance3D:
			var mi := n as MeshInstance3D
			for surf in mi.get_surface_override_material_count():
				var mat: Material = mi.get_active_material(surf)
				if mat is StandardMaterial3D and tints.has(mat.resource_name):
					var sm := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					var tint: Color = tints[mat.resource_name]
					sm.albedo_color = sm.albedo_color * tint
					if mat.resource_name == "KnitCuff":
						# The shared sleeve atlas bleeds orange leather into the cuff UVs —
						# flatten to dark wool instead of multiplying a bad texture
						sm.albedo_texture = null
						sm.albedo_color = Color(0.14, 0.16, 0.13)
					elif mat.resource_name == "SleeveWool":
						# Same shared-atlas problem: the sleeve UVs sample a warm brown/leather
						# region that reads as bare skin in first person — flatten to olive wool
						sm.albedo_texture = null
						sm.albedo_color = Color(0.155, 0.175, 0.115)
					sm.roughness = minf(1.0, sm.roughness + 0.18)
					mi.set_surface_override_material(surf, sm)
		for c in n.get_children():
			stack.append(c)


func _cache_weapon_parts(weapon_inst: Node) -> void:
	for pname in ["Slide", "Bolt", "Pump", "Magazine", "Drum", "FeedCover", "Trigger", "VacuumTubes", "PlasmaCells"]:
		var n := weapon_inst.find_child(pname, true, false)
		if n is Node3D:
			var n3 := n as Node3D
			_part_nodes[pname] = n3
			_part_rest[pname] = n3.transform


func _apply_pap_material(node: Node) -> void:
	if node.name in ["VacuumTubes", "PlasmaCells"]:
		return
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for s in range(mi.get_surface_override_material_count()):
			var mat: Material = mi.mesh.surface_get_material(s) if mi.mesh else null
			if mat and (mat.resource_name.contains("Glow") or mat.resource_name.contains("Plasma") or mat.resource_name.contains("Tesla") or mat.resource_name.contains("Optic") or mat.resource_name.contains("Tritium") or mat.resource_name.contains("Gauge")):
				continue
			if mat is BaseMaterial3D and (mat as BaseMaterial3D).emission_enabled:
				continue
			mi.set_surface_override_material(s, _pap_material)
	for c in node.get_children():
		_apply_pap_material(c)


func _try_fire() -> void:
	var cur := weapons[active_idx]
	if int(cur["mag"]) <= 0:
		AudioManager.play_2d("empty_click", 0.05, -2.0)
		_fire_cooldown = 0.22
		if int(cur["reserve"]) > 0:
			start_reload()
		return

	cur["mag"] = int(cur["mag"]) - 1
	var rpm := float(WeaponDB.get_stat(cur, "rpm"))
	if GameManager.has_perk("doubletap"):
		rpm *= 1.33
	_fire_cooldown = 60.0 / rpm

	var sfx_key := str(WeaponDB.get_stat(cur, "sfx"))
	AudioManager.play_2d(sfx_key, 0.05, 0.0)

	# Trigger moving part kicks
	_trigger_pull = 1.0
	var r_kind := str(WeaponDB.get_stat(cur, "reload_kind"))
	if r_kind == "pistol":
		_slide_kick = 1.0
	elif r_kind == "bolt_clip":
		_bolt_cycle = 1.0
	elif r_kind == "tube_pump":
		_pump_cycle = 1.0
	else:
		_bolt_kick = 1.0

	# Muzzle flash + dynamic light
	var packed: bool = bool(cur.get("packed", false))
	var wid := str(cur.get("id", "m1911"))
	var is_ray: bool = wid == "raygun"
	var is_wunder: bool = bool(WeaponDB.get_stat(cur, "is_wunderwaffe"))
	var m_off: Vector3 = WeaponDB.get_stat(cur, "muzzle_offset")
	muzzle_light.position = m_off
	muzzle_flash.position = m_off
	var flash_col := Color(0.28, 0.95, 1.0) if (packed or is_wunder) else (Color(0.25, 1.0, 0.45) if is_ray else Color(1.0, 0.72, 0.28))
	muzzle_light.light_color = flash_col
	muzzle_light.light_energy = 6.2
	if _flash_material:
		_flash_material.albedo_color = Color(flash_col.r, flash_col.g, flash_col.b, 0.95)
	muzzle_flash.visible = true
	muzzle_flash.rotation.z = randf_range(0.0, TAU)
	muzzle_flash.scale = Vector3.ONE * randf_range(0.85, 1.35)
	_flash_timer = 0.048

	# Eject brass casing / red shotgun hull
	if bool(WeaponDB.get_stat(cur, "eject_shells")):
		_spawn_shell_casing(cur, wid == "trench_shotgun")

	# Recoil kick (bounded so high-RPM weapons & ADS stay clear of camera near plane)
	var r_pitch := float(WeaponDB.get_stat(cur, "recoil_pitch"))
	var r_yaw := float(WeaponDB.get_stat(cur, "recoil_yaw"))
	var kick_scale := 0.55 if is_aiming else 1.0
	_kick_pos.y = clampf(_kick_pos.y + 0.008 * kick_scale, 0.0, 0.025)
	_kick_pos.z = clampf(_kick_pos.z + 0.048 * kick_scale, 0.0, 0.085)
	_kick_rot.x = clampf(_kick_rot.x + r_pitch * 1.8 * kick_scale, -0.15, 0.28)
	_kick_rot.y = clampf(_kick_rot.y + randf_range(-r_yaw, r_yaw) * kick_scale, -0.06, 0.06)
	if player:
		player.add_camera_recoil(r_pitch, r_yaw)

	# Ballistics
	if is_wunder:
		_fire_wunderwaffe(cur)
	elif bool(WeaponDB.get_stat(cur, "is_explosive")):
		_fire_explosive_bolt(cur)
	else:
		_fire_hitscan_pellets(cur)

	emit_hud()


func _spawn_shell_casing(cur: Dictionary, is_shotgun: bool) -> void:
	var s_off: Vector3 = WeaponDB.get_stat(cur, "shell_offset")
	if s_off == Vector3.ZERO:
		return
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	if target_parent == null:
		return
	var sc := _shell_casing_scene.instantiate() as Node3D
	target_parent.add_child(sc)
	var world_p := viewmodel_pivot.to_global(s_off)
	sc.global_position = world_p
	var b := viewmodel_pivot.global_transform.basis
	var eject_vel := (b.x * randf_range(1.6, 2.5) + b.y * randf_range(1.4, 2.2) + b.z * randf_range(0.3, 0.8))
	if player:
		eject_vel += player.velocity * 0.4
	if sc.has_method("setup"):
		sc.setup(eject_vel, b, is_shotgun)


func _cast_bullet_ray(origin: Vector3, dir: Vector3, max_dist: float) -> Dictionary:
	var space := get_world_3d().direct_space_state
	if space == null:
		return {}
	var end := origin + dir * max_dist
	var query := PhysicsRayQueryParameters3D.create(origin, end)
	query.collision_mask = 1 | 4 | 8 | 16 # World (1) + ZombieBody (4) + ZombieHead (8) + Interactable/Quest (16)
	query.collide_with_areas = true
	query.collide_with_bodies = true
	var exclude_list: Array[RID] = []
	if player:
		exclude_list.append(player.get_rid())

	for _step in range(6):
		query.exclude = exclude_list
		var res := space.intersect_ray(query)
		if res.is_empty():
			return {}
		var col: Object = res["collider"]
		if _try_trigger_quest(col):
			res["_quest_hit"] = true
			return res
		var col_layer := 0
		if col is CollisionObject3D:
			col_layer = (col as CollisionObject3D).collision_layer
		var is_enemy_col := col is Node and ((col as Node).is_in_group("zombies") or (col as Node).is_in_group("zombie_head") or (col as Node).has_meta("zombie_owner"))
		if (col_layer & 16) != 0 and not is_enemy_col:
			if col is CollisionObject3D:
				exclude_list.append((col as CollisionObject3D).get_rid())
				continue
		return res
	return {}


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


func _fire_hitscan_pellets(cur: Dictionary) -> void:
	var pellets := int(WeaponDB.get_stat(cur, "pellets"))
	var base_dmg := float(WeaponDB.get_stat(cur, "damage"))
	if GameManager.has_perk("doubletap"):
		base_dmg *= 2.0 # Double Tap II fires 2 bullets per shot!
	var hs_mult := float(WeaponDB.get_stat(cur, "headshot_mult"))
	var has_deadshot := GameManager.has_perk("deadshot")
	if has_deadshot:
		hs_mult *= 1.35
	var spread := float(WeaponDB.get_stat(cur, "spread_ads")) if is_aiming else float(WeaponDB.get_stat(cur, "spread_hip"))
	if has_deadshot and not is_aiming:
		spread *= 0.55

	var origin := camera.global_position
	var forward := -camera.global_transform.basis.z
	var right := camera.global_transform.basis.x
	var up := camera.global_transform.basis.y

	var muzzle_world := viewmodel_pivot.to_global(WeaponDB.get_stat(cur, "muzzle_offset"))
	var any_hit := false
	var any_kill := false
	var any_hs := false
	var decals_spawned := 0

	for _p in range(pellets):
		var sx := randf_range(-spread, spread)
		var sy := randf_range(-spread, spread)
		var dir := (forward + right * sx + up * sy).normalized()
		var res := _cast_bullet_ray(origin, dir, 120.0)
		if res.is_empty():
			_spawn_tracer(muzzle_world, origin + dir * 60.0, bool(cur.get("packed", false)))
			continue

		var hit_pos: Vector3 = res["position"]
		var hit_norm: Vector3 = res["normal"]
		var col: Object = res["collider"]
		_spawn_tracer(muzzle_world, hit_pos, bool(cur.get("packed", false)))

		if bool(res.get("_quest_hit", false)):
			_spawn_fx(_sparks_fx_scene, hit_pos, hit_norm)
			any_hit = true
			continue

		var is_head := false
		var zombie: Node = null
		if col is Area3D and col.is_in_group("zombie_head"):
			is_head = true
			zombie = col.get_meta("zombie_owner", null)
		elif col is Node and (col as Node).is_in_group("zombies"):
			zombie = col as Node
		elif col is Area3D and col.has_meta("zombie_owner"):
			zombie = col.get_meta("zombie_owner", null)

		if zombie != null and zombie.has_method("take_damage"):
			var dmg := base_dmg * (hs_mult if is_head else 1.0)
			var killed: bool = zombie.take_damage(dmg, is_head, hit_pos, dir)
			any_hit = true
			any_kill = any_kill or killed
			any_hs = any_hs or is_head
			_spawn_fx(_blood_fx_scene, hit_pos, hit_norm)
		else:
			_spawn_fx(_sparks_fx_scene, hit_pos, hit_norm)
			if decals_spawned < 2:
				decals_spawned += 1
				_spawn_bullet_decal(hit_pos, hit_norm, col)

	if any_hit:
		AudioManager.play_2d("headshot_crunch" if (any_hs and any_kill) else "hitmarker", 0.06, -4.0)
		GameManager.hitmarker_triggered.emit(any_kill, any_hs)


func _spawn_bullet_decal(hit_pos: Vector3, hit_norm: Vector3, col: Object) -> void:
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	if target_parent == null:
		return
	var is_metal := false
	if absf(hit_norm.y) > 0.7 and hit_pos.x >= 10.0 and hit_pos.x <= 24.0 and absf(hit_pos.z) <= 8.0:
		is_metal = true
	elif col is Node:
		var cname := (col as Node).name.to_lower()
		if cname.contains("metal") or cname.contains("steel") or cname.contains("door") or cname.contains("tank") or cname.contains("box") or cname.contains("machine"):
			is_metal = true
	var d := _bullet_decal_scene.instantiate() as Node3D
	target_parent.add_child(d)
	if d.has_method("setup"):
		d.setup(hit_pos, hit_norm, is_metal)


func _fire_wunderwaffe(cur: Dictionary) -> void:
	var packed: bool = bool(cur.get("packed", false))
	var max_chains: int = int(WeaponDB.get_stat(cur, "chain_max"))
	var chain_radius: float = float(WeaponDB.get_stat(cur, "chain_radius"))
	var dmg: float = float(WeaponDB.get_stat(cur, "damage"))
	if GameManager.has_perk("doubletap"):
		dmg *= 1.5
	var arc_color := Color(0.68, 0.42, 1.0) if packed else Color(0.28, 0.94, 1.0)

	var origin := camera.global_position
	var dir := (-camera.global_transform.basis.z).normalized()
	var muzzle_world := viewmodel_pivot.to_global(WeaponDB.get_stat(cur, "muzzle_offset"))
	var res := _cast_bullet_ray(origin, dir, 120.0)

	var impact_pos := origin + dir * 48.0 if res.is_empty() else (res["position"] as Vector3)
	var first_zombie: Node = null
	if not res.is_empty():
		var col: Object = res["collider"]
		if col is Area3D and col.has_meta("zombie_owner"):
			first_zombie = col.get_meta("zombie_owner", null)
		elif col is Node and (col as Node).is_in_group("zombies"):
			first_zombie = col as Node
		if first_zombie == null and not bool(res.get("_quest_hit", false)):
			# Generous proximity arc snap if bolt grazes right past a horde
			var best_d := 2.6
			for z in get_tree().get_nodes_in_group("zombies"):
				var z3 := z as Node3D
				if _is_enemy_dead(z3):
					continue
				var d := z3.global_position.distance_to(impact_pos)
				if d < best_d:
					best_d = d
					first_zombie = z3

	if player:
		player.add_camera_trauma(0.18)

	if first_zombie == null:
		_spawn_chain_arc(muzzle_world, impact_pos, arc_color)
		if not res.is_empty():
			_spawn_fx(_sparks_fx_scene, impact_pos, res.get("normal", Vector3.UP))
		return

	# Chain across up to max_chains living zombies within chain_radius hops!
	var visited: Dictionary = {}
	var queue: Array[Node] = [first_zombie]
	var arc_from: Dictionary = {first_zombie: muzzle_world}
	visited[first_zombie.get_instance_id()] = true
	var chained_order: Array[Node] = []

	while not queue.is_empty() and chained_order.size() < max_chains:
		var z_cur: Node = queue.pop_front()
		if _is_enemy_dead(z_cur):
			continue
		chained_order.append(z_cur)
		var cur_pos := _zombie_chest_pos(z_cur as Node3D)
		var arc_origin: Vector3 = arc_from.get(z_cur, muzzle_world)
		_spawn_chain_arc(arc_origin, cur_pos, arc_color)

		if chained_order.size() + queue.size() >= max_chains:
			continue

		# Collect closest living neighbors within chain_radius
		var candidates: Array[Dictionary] = []
		for cand in get_tree().get_nodes_in_group("zombies"):
			var c3 := cand as Node3D
			if _is_enemy_dead(c3):
				continue
			if visited.has(cand.get_instance_id()):
				continue
			var d := _zombie_chest_pos(c3).distance_to(cur_pos)
			if d <= chain_radius:
				candidates.append({"node": cand, "dist": d})
		candidates.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["dist"]) < float(b["dist"]))
		for item in candidates:
			if chained_order.size() + queue.size() >= max_chains:
				break
			var nxt: Node = item["node"]
			visited[nxt.get_instance_id()] = true
			arc_from[nxt] = cur_pos
			queue.append(nxt)

	var any_kill := false
	for z_hit in chained_order:
		if is_instance_valid(z_hit) and z_hit.has_method("take_damage"):
			var chest := _zombie_chest_pos(z_hit as Node3D)
			var arc_o: Vector3 = arc_from.get(z_hit, muzzle_world)
			var hit_dir := (chest - arc_o).normalized() if chest.distance_squared_to(arc_o) > 0.001 else dir
			var killed: bool = z_hit.take_damage(dmg, false, chest, hit_dir)
			any_kill = any_kill or killed

	if not chained_order.is_empty():
		AudioManager.play_2d("headshot_crunch" if any_kill else "hitmarker", 0.06, -3.0)
		GameManager.hitmarker_triggered.emit(any_kill, false)


func _zombie_chest_pos(z: Node3D) -> Vector3:
	if z == null:
		return Vector3.ZERO
	var h := z.get("head_area") as Node3D
	if h and is_instance_valid(h):
		return h.global_position - Vector3(0.0, 0.35, 0.0)
	return z.global_position + Vector3(0.0, 1.15, 0.0)


func _spawn_chain_arc(from_pos: Vector3, to_pos: Vector3, arc_color: Color) -> void:
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	if target_parent == null:
		return
	var arc := _chain_arc_scene.instantiate() as Node3D
	target_parent.add_child(arc)
	if arc.has_method("setup"):
		arc.setup(from_pos, to_pos, arc_color)


func _fire_explosive_bolt(cur: Dictionary) -> void:
	var bolt := _ray_bolt_scene.instantiate() as Node3D
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	target_parent.add_child(bolt)
	var muzzle_world := viewmodel_pivot.to_global(WeaponDB.get_stat(cur, "muzzle_offset"))
	bolt.global_position = muzzle_world
	var dir := (-camera.global_transform.basis.z).normalized()
	bolt.look_at(muzzle_world + dir, Vector3.UP)
	var dmg := float(WeaponDB.get_stat(cur, "damage"))
	if GameManager.has_perk("doubletap"):
		dmg *= 1.5
	var rad := float(WeaponDB.get_stat(cur, "splash_radius"))
	var packed := bool(cur.get("packed", false))
	bolt.setup(dir, dmg, rad, Color(0.95, 0.25, 1.0) if packed else Color(0.25, 1.0, 0.45), player)


func _perform_melee() -> void:
	is_meleeing = true
	is_aiming = false
	_melee_timer = MELEE_DURATION
	_kick_pos = Vector3.ZERO
	_kick_rot = Vector3.ZERO
	model_holder.visible = false
	knife_holder.visible = true
	AudioManager.play_2d("knife_slash", 0.08, 0.0)

	var space := get_world_3d().direct_space_state
	var origin := camera.global_position
	var dir := -camera.global_transform.basis.z
	var query := PhysicsRayQueryParameters3D.create(origin, origin + dir * 2.55)
	query.collision_mask = 1 | 4 | 8
	query.collide_with_areas = true
	query.collide_with_bodies = true
	if player:
		query.exclude = [player.get_rid()]
	var res := space.intersect_ray(query)
	if not res.is_empty():
		var col: Object = res["collider"]
		var zombie: Node = null
		if col is Area3D and col.has_meta("zombie_owner"):
			zombie = col.get_meta("zombie_owner", null)
		elif col is Node and (col as Node).is_in_group("zombies"):
			zombie = col as Node
		if zombie != null and zombie.has_method("take_damage"):
			var killed: bool = zombie.take_damage(150.0, false, res["position"], dir, true)
			_spawn_fx(_blood_fx_scene, res["position"], res["normal"])
			AudioManager.play_2d("headshot_crunch", 0.06, -2.0)
			GameManager.hitmarker_triggered.emit(killed, false)


func start_reload() -> void:
	if is_reloading or is_meleeing or weapons.is_empty():
		return
	var cur := weapons[active_idx]
	if int(cur["mag"]) >= int(cur["mag_cap"]) or int(cur["reserve"]) <= 0:
		return
	is_reloading = true
	is_aiming = false
	_sfx_mag_out_done = false
	_sfx_mag_in_done = false
	_sfx_bolt_done = false
	var base_t := float(WeaponDB.get_stat(cur, "reload_time"))
	if GameManager.has_perk("speedcola"):
		base_t *= 0.5
	_reload_total = base_t
	_reload_timer = base_t
	AudioManager.play_2d("reload_click", 0.04, -2.0)

	if GameManager.has_perk("electriccherry"):
		_trigger_electric_cherry(cur)


func _trigger_electric_cherry(cur: Dictionary) -> void:
	var cap := maxi(1, int(cur["mag_cap"]))
	var emptiness := clampf(1.0 - float(cur["mag"]) / float(cap), 0.15, 1.0)
	var dmg := 120.0 + 380.0 * emptiness
	var center := (player.global_position if player else global_position) + Vector3(0.0, 0.9, 0.0)
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	if target_parent:
		var ring := _electric_ring_scene.instantiate() as Node3D
		target_parent.add_child(ring)
		ring.global_position = (player.global_position if player else global_position) + Vector3(0.0, 0.25, 0.0)
	AudioManager.play_2d("perk_electric_cherry", 0.05, -1.0)

	var hits := 0
	var any_kill := false
	for z in get_tree().get_nodes_in_group("zombies"):
		var z3 := z as Node3D
		if _is_enemy_dead(z3):
			continue
		var chest := _zombie_chest_pos(z3)
		if chest.distance_to(center) <= 4.5 and z.has_method("take_damage"):
			var dvec := (chest - center).normalized()
			var k: bool = z.take_damage(dmg, false, chest, dvec)
			hits += 1
			any_kill = any_kill or k
			if hits <= 6:
				_spawn_chain_arc(center, chest, Color(0.25, 0.92, 1.0))
	if hits > 0:
		AudioManager.play_2d("hitmarker", 0.06, -4.0)
		GameManager.hitmarker_triggered.emit(any_kill, false)


func _finish_reload() -> void:
	is_reloading = false
	var cur := weapons[active_idx]
	var needed := int(cur["mag_cap"]) - int(cur["mag"])
	var take := mini(needed, int(cur["reserve"]))
	cur["mag"] = int(cur["mag"]) + take
	cur["reserve"] = int(cur["reserve"]) - take
	AudioManager.play_2d("reload_click", 0.04, 0.0)
	emit_hud()


func refill_all_ammo() -> void:
	for w in weapons:
		w["mag"] = w["mag_cap"]
		w["reserve"] = w["reserve_cap"]
	grenades = 4
	emit_hud()


func has_weapon(weapon_id: String) -> bool:
	for w in weapons:
		if w["id"] == weapon_id:
			return true
	return false


func give_or_replace_weapon(weapon_id: String) -> void:
	for i in range(weapons.size()):
		if weapons[i]["id"] == weapon_id:
			weapons[i]["mag"] = weapons[i]["mag_cap"]
			weapons[i]["reserve"] = weapons[i]["reserve_cap"]
			_equip_weapon(i)
			return
	var state := WeaponDB.create_weapon_state(weapon_id, false)
	if weapons.size() < max_weapons:
		weapons.append(state)
		_equip_weapon(weapons.size() - 1)
	else:
		weapons[active_idx] = state
		_equip_weapon(active_idx)


func pack_current_weapon() -> bool:
	if weapons.is_empty():
		return false
	var cur := weapons[active_idx]
	if bool(cur.get("packed", false)):
		return false
	var upgraded := WeaponDB.create_weapon_state(str(cur["id"]), true)
	weapons[active_idx] = upgraded
	GameManager.stats["pap_upgrades"] += 1
	_equip_weapon(active_idx)
	return true


func get_current_state() -> Dictionary:
	return weapons[active_idx] if not weapons.is_empty() else {}


func emit_hud() -> void:
	if weapons.is_empty():
		return
	var cur := weapons[active_idx]
	var sec := ""
	if weapons.size() > 1:
		var next_name := WeaponDB.get_display_name(weapons[(active_idx + 1) % weapons.size()])
		if weapons.size() == 3:
			var third_name := WeaponDB.get_display_name(weapons[(active_idx + 2) % weapons.size()])
			sec = "%s  |  %s  [1-3]" % [next_name, third_name]
		else:
			sec = next_name
	GameManager.weapon_hud_updated.emit(
		WeaponDB.get_display_name(cur),
		bool(cur.get("packed", false)),
		int(cur["mag"]),
		int(cur["reserve"]),
		grenades,
		sec
	)


func _spawn_fx(scene: PackedScene, pos: Vector3, normal: Vector3) -> void:
	var fx := scene.instantiate() as Node3D
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	target_parent.add_child(fx)
	fx.global_position = pos + normal * 0.03


const MAX_TRACERS := 16
static var _active_tracers: Array[MeshInstance3D] = []
static var _tracer_mesh: BoxMesh = null
static var _tracer_mat_std: StandardMaterial3D = null
static var _tracer_mat_pap: StandardMaterial3D = null


static func clear_shared_caches() -> void:
	for tr in _active_tracers:
		if is_instance_valid(tr) and not tr.is_inside_tree() and not tr.is_queued_for_deletion():
			tr.free()
	_active_tracers.clear()
	_tracer_mesh = null
	_tracer_mat_std = null
	_tracer_mat_pap = null


static func _ensure_tracer_assets() -> void:
	if _tracer_mesh == null:
		_tracer_mesh = BoxMesh.new()
		_tracer_mesh.size = Vector3(0.014, 0.014, 1.0)
	if _tracer_mat_std == null:
		_tracer_mat_std = StandardMaterial3D.new()
		_tracer_mat_std.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_tracer_mat_std.albedo_color = Color(1.0, 0.85, 0.45, 0.75)
		_tracer_mat_std.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	if _tracer_mat_pap == null:
		_tracer_mat_pap = StandardMaterial3D.new()
		_tracer_mat_pap.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_tracer_mat_pap.albedo_color = Color(0.25, 0.95, 1.0, 0.85)
		_tracer_mat_pap.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA


func _spawn_tracer(from_pos: Vector3, to_pos: Vector3, packed: bool) -> void:
	var dist := from_pos.distance_to(to_pos)
	if dist < 0.25:
		return
	_ensure_tracer_assets()
	for i in range(_active_tracers.size() - 1, -1, -1):
		if not is_instance_valid(_active_tracers[i]):
			_active_tracers.remove_at(i)
	while _active_tracers.size() >= MAX_TRACERS:
		var old := _active_tracers.pop_front() as MeshInstance3D
		if is_instance_valid(old):
			old.queue_free()

	var mi := MeshInstance3D.new()
	mi.mesh = _tracer_mesh
	mi.material_override = _tracer_mat_pap if packed else _tracer_mat_std
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var target_parent: Node = get_tree().current_scene if get_tree().current_scene != null else get_tree().root
	target_parent.add_child(mi)
	_active_tracers.append(mi)
	mi.global_position = (from_pos + to_pos) * 0.5
	var dir := (to_pos - from_pos) / dist
	var up_ref := Vector3.RIGHT if absf(dir.dot(Vector3.UP)) > 0.99 else Vector3.UP
	mi.look_at(to_pos, up_ref)
	mi.scale = Vector3(1.0, 1.0, dist)
	var tw := mi.create_tween()
	tw.tween_property(mi, "transparency", 1.0, 0.07)
	tw.tween_callback(func() -> void:
		_active_tracers.erase(mi)
		if is_instance_valid(mi):
			mi.queue_free()
	)

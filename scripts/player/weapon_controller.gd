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
var _melee_timer: float = 0.0
var _flash_timer: float = 0.0

var _kick_pos: Vector3 = Vector3.ZERO
var _kick_rot: Vector3 = Vector3.ZERO
var _sway_offset: Vector2 = Vector2.ZERO
var _walk_bob: float = 0.0
var _initial_equip_done: bool = false

var _pap_shader: Shader = preload("res://assets/shaders/pap_camo.gdshader")
var _pap_albedo: Texture2D = preload("res://assets/textures/weapons/pap_albedo.png")
var _pap_emission: Texture2D = preload("res://assets/textures/weapons/pap_emission.png")
var _pap_material: ShaderMaterial

var _blood_fx_scene: PackedScene = preload("res://scenes/fx/blood_burst.tscn")
var _sparks_fx_scene: PackedScene = preload("res://scenes/fx/impact_sparks.tscn")
var _ray_bolt_scene: PackedScene = preload("res://scenes/fx/ray_bolt.tscn")


func _ready() -> void:
	_pap_material = ShaderMaterial.new()
	_pap_material.shader = _pap_shader
	_pap_material.set_shader_parameter("albedo_tex", _pap_albedo)
	_pap_material.set_shader_parameter("emission_tex", _pap_emission)

	if ResourceLoader.exists("res://assets/models/weapons/combat_knife.glb"):
		var k_inst := (load("res://assets/models/weapons/combat_knife.glb") as PackedScene).instantiate()
		knife_holder.add_child(k_inst)
	knife_holder.visible = false
	muzzle_light.light_energy = 0.0
	muzzle_flash.visible = false

	weapons.append(WeaponDB.create_weapon_state("m1911", false))
	_equip_weapon(0)


func snap_viewmodel() -> void:
	if weapons.is_empty():
		return
	var cur: Dictionary = weapons[active_idx]
	_kick_pos = Vector3.ZERO
	_kick_rot = Vector3.ZERO
	_sway_offset = Vector2.ZERO
	viewmodel_pivot.position = WeaponDB.get_stat(cur, "ads_pos") if is_aiming else WeaponDB.get_stat(cur, "hip_pos")
	viewmodel_pivot.rotation = Vector3.ZERO
	model_holder.rotation.y = 0.0 if is_aiming else deg_to_rad(3.5)


func add_look_sway(rel: Vector2) -> void:
	_sway_offset.x = clampf(_sway_offset.x - rel.x * 0.0007, -0.04, 0.04)
	_sway_offset.y = clampf(_sway_offset.y + rel.y * 0.0007, -0.04, 0.04)


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


func _handle_weapon_inputs(delta: float) -> void:
	if weapons.is_empty():
		return

	if is_meleeing:
		_melee_timer -= delta
		if _melee_timer <= 0.0:
			is_meleeing = false
			knife_holder.visible = false
			model_holder.visible = true
		return

	if is_reloading:
		_reload_timer -= delta
		if _reload_timer <= 0.0:
			_finish_reload()
		return

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

		if Input.is_action_just_pressed("melee"):
			_perform_melee()
			return

	is_aiming = Input.is_action_pressed("aim") and not is_reloading and not is_meleeing and (player == null or not player.is_downed)

	if Input.is_action_just_pressed("reload"):
		start_reload()
		return

	var cur: Dictionary = weapons[active_idx]
	var mode := str(WeaponDB.get_stat(cur, "fire_mode"))
	var wants_fire := Input.is_action_pressed("fire") if mode == "auto" else Input.is_action_just_pressed("fire")
	if wants_fire and _fire_cooldown <= 0.0:
		_try_fire()


func _animate_viewmodel(delta: float) -> void:
	if weapons.is_empty():
		return
	var cur: Dictionary = weapons[active_idx]
	var hip_pos: Vector3 = WeaponDB.get_stat(cur, "hip_pos")
	var ads_pos: Vector3 = WeaponDB.get_stat(cur, "ads_pos")
	var target_pos := ads_pos if is_aiming else hip_pos

	if is_reloading:
		target_pos += Vector3(0.0, -0.14, 0.04)

	var horiz := 0.0
	if player:
		horiz = Vector2(player.velocity.x, player.velocity.z).length()
	if horiz > 0.4 and player.is_on_floor() and not is_aiming:
		_walk_bob += delta * horiz * 1.8
		target_pos.x += cos(_walk_bob) * 0.010
		target_pos.y += absf(sin(_walk_bob)) * 0.012

	_sway_offset = _sway_offset.lerp(Vector2.ZERO, delta * 9.0)
	_kick_pos = _kick_pos.lerp(Vector3.ZERO, delta * 14.0)
	_kick_rot = _kick_rot.lerp(Vector3.ZERO, delta * 14.0)

	target_pos.x += _sway_offset.x
	target_pos.y += _sway_offset.y

	viewmodel_pivot.position = viewmodel_pivot.position.lerp(target_pos + _kick_pos, delta * 16.0)
	var target_rot := Vector3(-0.35 if is_reloading else 0.0, 0.0, 0.0) + _kick_rot
	if is_meleeing:
		var t := 1.0 - (_melee_timer / 0.36)
		viewmodel_pivot.position = Vector3(0.05 - t * 0.25, -0.14, -0.32 - sin(t * PI) * 0.28)
		target_rot = Vector3(-0.4, 0.9 - t * 1.8, 0.6)
	viewmodel_pivot.rotation = viewmodel_pivot.rotation.lerp(target_rot, delta * 18.0)
	var target_cant := 0.0 if (is_aiming or is_meleeing) else deg_to_rad(3.5)
	model_holder.rotation.y = lerpf(model_holder.rotation.y, target_cant, delta * 16.0)

	# Smooth ADS FOV
	var base_fov := SettingsManager.fov
	var target_fov := base_fov * float(WeaponDB.get_stat(cur, "ads_fov_mult")) if is_aiming else base_fov
	camera.fov = lerpf(camera.fov, target_fov, delta * 14.0)


func _equip_weapon(idx: int) -> void:
	active_idx = clampi(idx, 0, weapons.size() - 1)
	is_reloading = false
	is_aiming = false
	for ch in model_holder.get_children():
		ch.queue_free()

	var cur := weapons[active_idx]
	var model_path := str(WeaponDB.get_stat(cur, "model"))
	if ResourceLoader.exists(model_path):
		var inst := (load(model_path) as PackedScene).instantiate()
		model_holder.add_child(inst)
		if bool(cur.get("packed", false)):
			_apply_pap_material(inst)

	if not _initial_equip_done:
		_initial_equip_done = true
		snap_viewmodel()
	else:
		_kick_pos = Vector3(0, -0.05, 0.04)
	emit_hud()


func _apply_pap_material(node: Node) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for s in range(mi.get_surface_override_material_count()):
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

	# Muzzle flash + dynamic light
	var packed: bool = bool(cur.get("packed", false))
	var is_ray: bool = str(cur["id"]) == "raygun"
	var m_off: Vector3 = WeaponDB.get_stat(cur, "muzzle_offset")
	muzzle_light.position = m_off
	muzzle_flash.position = m_off
	muzzle_light.light_color = Color(0.25, 0.95, 1.0) if (packed or is_ray) else Color(1.0, 0.72, 0.28)
	muzzle_light.light_energy = 5.5
	muzzle_flash.visible = true
	muzzle_flash.rotation.z = randf_range(0.0, TAU)
	muzzle_flash.scale = Vector3.ONE * randf_range(0.85, 1.35)
	_flash_timer = 0.048

	# Recoil kick
	var r_pitch := float(WeaponDB.get_stat(cur, "recoil_pitch"))
	var r_yaw := float(WeaponDB.get_stat(cur, "recoil_yaw"))
	_kick_pos += Vector3(0.0, 0.008, 0.048)
	_kick_rot += Vector3(r_pitch * 1.8, randf_range(-r_yaw, r_yaw), 0.0)
	if player:
		player.add_camera_recoil(r_pitch, r_yaw)

	# Ballistics
	var is_explosive := bool(WeaponDB.get_stat(cur, "is_explosive"))
	if is_explosive:
		_fire_explosive_bolt(cur)
	else:
		_fire_hitscan_pellets(cur)

	emit_hud()


func _fire_hitscan_pellets(cur: Dictionary) -> void:
	var pellets := int(WeaponDB.get_stat(cur, "pellets"))
	var base_dmg := float(WeaponDB.get_stat(cur, "damage"))
	if GameManager.has_perk("doubletap"):
		base_dmg *= 2.0 # Double Tap II fires 2 bullets per shot!
	var hs_mult := float(WeaponDB.get_stat(cur, "headshot_mult"))
	var spread := float(WeaponDB.get_stat(cur, "spread_ads")) if is_aiming else float(WeaponDB.get_stat(cur, "spread_hip"))

	var space := get_world_3d().direct_space_state
	var origin := camera.global_position
	var forward := -camera.global_transform.basis.z
	var right := camera.global_transform.basis.x
	var up := camera.global_transform.basis.y

	var muzzle_world := viewmodel_pivot.to_global(WeaponDB.get_stat(cur, "muzzle_offset"))
	var any_hit := false
	var any_kill := false
	var any_hs := false

	for _p in range(pellets):
		var sx := randf_range(-spread, spread)
		var sy := randf_range(-spread, spread)
		var dir := (forward + right * sx + up * sy).normalized()
		var end := origin + dir * 120.0
		var query := PhysicsRayQueryParameters3D.create(origin, end)
		query.collision_mask = 1 | 4 | 8 # World (1) + ZombieBody (4) + ZombieHead (8)
		query.collide_with_areas = true
		query.collide_with_bodies = true
		if player:
			query.exclude = [player.get_rid()]

		var res := space.intersect_ray(query)
		if res.is_empty():
			_spawn_tracer(muzzle_world, origin + dir * 60.0, bool(cur.get("packed", false)))
			continue

		var hit_pos: Vector3 = res["position"]
		var hit_norm: Vector3 = res["normal"]
		var col: Object = res["collider"]
		_spawn_tracer(muzzle_world, hit_pos, bool(cur.get("packed", false)))

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

	if any_hit:
		AudioManager.play_2d("headshot_crunch" if (any_hs and any_kill) else "hitmarker", 0.06, -4.0)
		GameManager.hitmarker_triggered.emit(any_kill, any_hs)


func _fire_explosive_bolt(cur: Dictionary) -> void:
	var bolt := _ray_bolt_scene.instantiate() as Node3D
	get_tree().current_scene.add_child(bolt)
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
	_melee_timer = 0.36
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
	if is_reloading or weapons.is_empty():
		return
	var cur := weapons[active_idx]
	if int(cur["mag"]) >= int(cur["mag_cap"]) or int(cur["reserve"]) <= 0:
		return
	is_reloading = true
	is_aiming = false
	var base_t := float(WeaponDB.get_stat(cur, "reload_time"))
	if GameManager.has_perk("speedcola"):
		base_t *= 0.5
	_reload_timer = base_t
	AudioManager.play_2d("reload_click", 0.04, -2.0)


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
		sec = WeaponDB.get_display_name(weapons[(active_idx + 1) % weapons.size()])
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
	get_tree().current_scene.add_child(fx)
	fx.global_position = pos + normal * 0.03


func _spawn_tracer(from_pos: Vector3, to_pos: Vector3, packed: bool) -> void:
	var dist := from_pos.distance_to(to_pos)
	if dist < 0.25:
		return
	var mi := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(0.014, 0.014, dist)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color(0.25, 0.95, 1.0, 0.85) if packed else Color(1.0, 0.85, 0.45, 0.75)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mesh.material = mat
	mi.mesh = mesh
	get_tree().current_scene.add_child(mi)
	mi.global_position = (from_pos + to_pos) * 0.5
	mi.look_at(to_pos, Vector3.UP)
	var tw := mi.create_tween()
	tw.tween_property(mat, "albedo_color:a", 0.0, 0.07)
	tw.tween_callback(mi.queue_free)

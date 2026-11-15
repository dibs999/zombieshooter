extends Node

var out_dir: String = OS.get_environment("BUNKER_WPN_SHOT_DIR") if OS.has_environment("BUNKER_WPN_SHOT_DIR") else "/tmp/bunker_shots_wpn_extra"


func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(1280, 720)
	DirAccess.make_dir_recursive_absolute(out_dir)
	await _wait_frames(2)

	GameManager.reset_match()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(world)

	var player := world.get_node("Player") as PlayerController
	var rd := world.get_node("RoundDirector") as RoundDirector
	var hud := world.get_node("HUD")
	rd.set_process(false)
	player.set_physics_process(false)
	await _wait_frames(3)

	var wc := player.weapon_ctrl
	wc.set_process(false)
	GameManager.add_points(25000, "")

	# Shot 1: M1911 + anatomical MPFB2 hands & sleeve cuffs in Courtyard
	wc.give_or_replace_weapon("m1911")
	wc.snap_viewmodel()
	hud.set_crosshair_spread(wc.get_crosshair_spread_px(), false)
	hud.crosshair.modulate.a = 1.0
	_clear_hud_deltas(world)
	player.global_position = Vector3(1.5, 0.05, 6.2)
	player.rotation_degrees = Vector3(0, 14, 0)
	player.head.rotation_degrees = Vector3(-4, 0, 0)
	await _wait_frames(4)
	await _save_shot("wpn_1_m1911_hands.png")

	# Shot 2: CC0 Poly Haven Kar98k Scoped hip view + Zombie target ahead
	var z_target := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_target.setup("soldier", 400.0, 2.0, null)
	world.add_child(z_target)
	z_target.set_physics_process(false)
	z_target.global_position = Vector3(0.4, 0.0, 2.2)
	z_target.rotation_degrees.y = 165.0
	if z_target._anim_player:
		z_target._anim_player.advance(0.25)

	wc.give_or_replace_weapon("kar98k")
	wc.snap_viewmodel()
	hud.set_crosshair_spread(wc.get_crosshair_spread_px(), false)
	hud.crosshair.modulate.a = 1.0
	_clear_hud_deltas(world)
	player.global_position = Vector3(0.4, 0.05, 6.6)
	player.rotation_degrees = Vector3(0, 0, 0)
	player.head.rotation_degrees = Vector3(-2, 0, 0)
	await _wait_frames(4)
	await _save_shot("wpn_2_kar98k_hip.png")

	# Shot 3: Kar98k ADS Scope sight alignment directly onto target + zoomed FOV + hidden crosshair
	wc.is_aiming = true
	wc.snap_viewmodel()
	player.camera.fov = SettingsManager.fov * float(WeaponDB.get_stat(wc.get_current_state(), "ads_fov_mult"))
	hud.set_crosshair_spread(6.0, true)
	hud.crosshair.modulate.a = 0.0
	await _wait_frames(4)
	await _save_shot("wpn_3_kar98k_ads.png")
	wc.is_aiming = false
	player.camera.fov = SettingsManager.fov
	hud.set_crosshair_spread(wc.get_crosshair_spread_px(), false)
	hud.crosshair.modulate.a = 1.0
	z_target.queue_free()
	await _wait_frames(2)

	# Shot 4: Wunderwaffe DG-2 + chain lightning arcs across 4 zombies + muzzle flash star
	var chain_zs: Array[ZombieAI] = []
	for i in range(4):
		var cz := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
		cz.setup("soldier" if i % 2 == 0 else "scientist", 400.0, 2.0, null)
		world.add_child(cz)
		cz.set_physics_process(false)
		cz.global_position = Vector3(-1.3 + float(i) * 1.15, 0.0, 2.55 - float(i % 2) * 0.55)
		cz.rotation_degrees.y = 172.0
		if cz._anim_player:
			cz._anim_player.advance(0.18 + float(i) * 0.1)
		chain_zs.append(cz)

	wc.give_or_replace_weapon("wunderwaffe")
	wc.snap_viewmodel()
	hud.set_crosshair_spread(wc.get_crosshair_spread_px(), false)
	hud.crosshair.modulate.a = 1.0
	_clear_hud_deltas(world)
	player.global_position = Vector3(0.0, 0.05, 6.4)
	player.rotation_degrees = Vector3(0, 5, 0)
	player.head.rotation_degrees = Vector3(-2, 0, 0)
	await _wait_frames(2)
	# Spawn chain lightning arcs held open for capture + muzzle flash
	var muzzle_w := wc.viewmodel_pivot.to_global(WeaponDB.get_stat(wc.get_current_state(), "muzzle_offset"))
	var prev_pt := muzzle_w
	var chain_arcs: Array[Node] = []
	for cz in chain_zs:
		var next_pt := cz.global_position + Vector3(0, 1.15, 0)
		var arc := wc._chain_arc_scene.instantiate() as Node3D
		world.add_child(arc)
		arc.setup(prev_pt, next_pt, Color(0.28, 0.94, 1.0), true)
		chain_arcs.append(arc)
		prev_pt = next_pt
	wc.muzzle_flash.position = WeaponDB.get_stat(wc.get_current_state(), "muzzle_offset")
	wc.muzzle_light.position = wc.muzzle_flash.position
	wc.muzzle_light.light_color = Color(0.28, 0.94, 1.0)
	wc.muzzle_light.light_energy = 6.2
	if wc._flash_material:
		wc._flash_material.albedo_color = Color(0.28, 0.94, 1.0, 0.95)
	wc.muzzle_flash.visible = true
	await _wait_frames(2)
	await _save_shot("wpn_4_wunderwaffe_chain.png")
	wc.muzzle_flash.visible = false
	wc.muzzle_light.light_energy = 0.0
	for arc in chain_arcs:
		if is_instance_valid(arc):
			arc.queue_free()
	chain_arcs.clear()
	for cz in chain_zs:
		cz.queue_free()
	await _wait_frames(2)

	# Shot 5: Mid-reload Pack-a-Punched STG-44 (Spatz-447+) + ALL 9 perks + Round 7 red chalk + +100 popup + Damage Arc!
	GameManager.current_round = 7
	GameManager.round_changed.emit(7, false)
	for tw in get_tree().get_processed_tweens():
		if tw and tw.is_valid():
			tw.kill()
	for pid in ["quickrevive", "juggernog", "speedcola", "doubletap", "staminup", "mulekick", "deadshot", "phdflopper", "electriccherry"]:
		GameManager.grant_perk(pid)
	wc.weapons = [WeaponDB.create_weapon_state("m1911", false)]
	wc._equip_weapon(0)
	wc.give_or_replace_weapon("stg44")
	wc.pack_current_weapon()
	wc.give_or_replace_weapon("raygun")
	var stg_idx := -1
	for i in range(wc.weapons.size()):
		if wc.weapons[i]["id"] == "stg44":
			stg_idx = i
			break
	assert(stg_idx >= 0, "Expected stg44 in weapons loadout")
	wc._equip_weapon(stg_idx)
	assert(wc.get_current_state()["id"] == "stg44" and bool(wc.get_current_state().get("packed", false)), "Expected packed Spatz-447+ equipped")
	wc.snap_viewmodel()
	wc.weapons[wc.active_idx]["mag"] = 12
	wc.emit_hud()
	wc.start_reload()
	wc._reload_timer = wc._reload_total * 0.68
	for _i in range(30):
		wc._animate_viewmodel(0.016)
	hud.set_crosshair_spread(6.0, true)
	hud.crosshair.modulate.a = 0.0
	_clear_hud_deltas(world)
	await _wait_frames(2)
	if hud.chalk_counter:
		hud.chalk_counter.flash_amount = 0.0
		hud.chalk_counter.scale = Vector2.ONE
		hud.chalk_counter.queue_redraw()
	hud.banner_label.visible = false
	hud._banner_timer = 0.0
	GameManager.add_points(100, "Headshot")
	hud.on_player_damaged(35.0, player.global_position + Vector3(-3.5, 0.0, 2.0), player.global_position, player.global_transform.basis)
	hud._on_hitmarker(true, true)
	hud._hitmarker_timer = 2.0
	await _wait_frames(1)
	await _save_shot("wpn_5_reload_pap_hud.png")
	wc._finish_reload()
	hud.hitmarker.visible = false
	hud._hitmarker_timer = 0.0
	if hud.damage_arc:
		hud.damage_arc._pings.clear()
		hud.damage_arc.queue_redraw()
	hud.banner_label.visible = false
	hud._banner_timer = 0.0

	# Shot 6: MG42 + anatomical hands + East Courtyard power & Ray Gun close-up
	(world.get_node("Interactables/PowerSwitch") as PowerSwitch).interact(player)
	(world.get_node("Interactables/DoorSpawnEast") as BuyableDoor).interact(player)
	for pl in world._power_lights:
		pl.light_energy = float(pl.get_meta("target_energy", 2.6))
	wc.set_process(false)
	wc.give_or_replace_weapon("mg42")
	wc.snap_viewmodel()
	hud.set_crosshair_spread(wc.get_crosshair_spread_px(), false)
	hud.crosshair.modulate.a = 1.0
	_clear_hud_deltas(world)
	player.global_position = Vector3(16.0, 0.05, 0.5)
	player.rotation_degrees = Vector3(0, 48, 0)
	player.head.rotation_degrees = Vector3(-4, 0, 0)
	await _wait_frames(4)
	await _save_shot("wpn_6_mg42_courtyard.png")

	print("CAPTURED 6 WEAPON/HUD VERIFICATION SCREENSHOTS IN ", out_dir)
	AudioManager.stop_ambience()
	for p2 in AudioManager._pool_2d:
		if p2:
			p2.stop()
			p2.stream = null
	for p3 in AudioManager._pool_3d:
		if p3:
			p3.stop()
			p3.stream = null
	if AudioManager._ambience_player:
		AudioManager._ambience_player.stream = null
	world.queue_free()
	await get_tree().create_timer(0.08).timeout
	await _wait_frames(2)
	get_tree().quit(0)


func _clear_hud_deltas(world: Node) -> void:
	var db := world.get_node_or_null("HUD/BottomLeft/PointsRow/DeltaBox")
	if db:
		for ch in db.get_children():
			ch.queue_free()


func _wait_frames(n: int) -> void:
	for _i in range(n):
		await get_tree().process_frame


func _save_shot(filename: String) -> void:
	await RenderingServer.frame_post_draw
	var img: Image = get_viewport().get_texture().get_image()
	var output := out_dir.path_join(filename)
	var result := img.save_png(output)
	if result != OK:
		push_error("Screenshot save failed: %s (%d)" % [output, result])
		get_tree().quit(1)
	print("Saved: ", output)

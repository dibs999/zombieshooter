extends RefCounted
class_name TestsWpn


static func _check(runner: Node, cond: bool, msg: String) -> void:
	runner.call("_check", cond, msg)


static func run_checks(runner: Node) -> void:
	print("[Wpn] Running Stream C Weapons, Viewmodel, Wunderwaffe, Perks, HUD & Audio checks...")
	GameManager.reset_match()

	# 1. Verify all 11 weapon GLBs + FP hands + animatable child nodes
	var expected_parts := {
		"m1911": ["Receiver", "Slide", "Magazine", "Trigger"],
		"kar98k": ["Receiver", "Bolt", "Trigger"],
		"trench_shotgun": ["Receiver", "Pump", "Bolt", "Trigger"],
		"mp40": ["Receiver", "Magazine", "Bolt", "Trigger"],
		"stg44": ["Receiver", "Magazine", "Bolt", "Trigger"],
		"m14": ["Receiver", "Magazine", "Bolt", "Trigger"],
		"mg42": ["Receiver", "Drum", "FeedCover", "Bolt", "Trigger"],
		"raygun": ["Receiver", "PlasmaCells", "Trigger"],
		"wunderwaffe": ["Receiver", "VacuumTubes", "Magazine", "Trigger"],
	}
	for wid in expected_parts.keys():
		var path := "res://assets/models/weapons/%s.glb" % wid
		var exists := ResourceLoader.exists(path)
		_check(runner, exists, "Wpn model exists: " + path)
		if exists:
			var inst := (load(path) as PackedScene).instantiate()
			var ok := true
			for pname in expected_parts[wid]:
				if inst.find_child(pname, true, false) == null:
					ok = false
					printerr("    missing child node '%s' on %s" % [pname, wid])
			_check(runner, ok, "Wpn '%s' contains all animatable child nodes %s" % [wid, str(expected_parts[wid])])
			inst.free()

	for extra in ["combat_knife", "frag_grenade", "fp_right_hand", "fp_left_hand"]:
		var epath := "res://assets/models/weapons/%s.glb" % extra
		_check(runner, ResourceLoader.exists(epath), "Wpn extra model exists: " + epath)

	# 2. Verify WeaponDB Wunderwaffe DG-2 & DG-3 JZ specs
	_check(runner, WeaponDB.WEAPON_DATA.has("wunderwaffe"), "WeaponDB includes wunderwaffe")
	var w_base := WeaponDB.create_weapon_state("wunderwaffe", false)
	var w_pap := WeaponDB.create_weapon_state("wunderwaffe", true)
	_check(runner, WeaponDB.get_display_name(w_base) == "Wunderwaffe DG-2", "Wunderwaffe base name == Wunderwaffe DG-2")
	_check(runner, WeaponDB.get_display_name(w_pap) == "Wunderwaffe DG-3 JZ", "Wunderwaffe PaP name == Wunderwaffe DG-3 JZ")
	_check(runner, int(w_base["mag_cap"]) == 3 and int(w_base["reserve_cap"]) == 15, "Wunderwaffe base ammo 3/15")
	_check(runner, int(w_pap["mag_cap"]) == 6 and int(w_pap["reserve_cap"]) == 30, "Wunderwaffe PaP ammo 6/30")
	_check(runner, int(WeaponDB.get_stat(w_base, "chain_max")) == 10 and int(WeaponDB.get_stat(w_pap, "chain_max")) == 24, "Wunderwaffe chain limits 10 base / 24 PaP")

	# 3. Verify AudioManager all 46 keys loaded & 20-channel pools
	var missing_sfx := 0
	for k in AudioManager.SFX_PATHS.keys():
		if not AudioManager._streams.has(k):
			missing_sfx += 1
			printerr("    missing SFX stream: ", k)
	_check(runner, missing_sfx == 0 and AudioManager._streams.size() >= 45, "AudioManager loaded all %d SFX streams (missing=%d)" % [AudioManager._streams.size(), missing_sfx])
	_check(runner, AudioManager._pool_2d.size() >= 20 and AudioManager._pool_3d.size() >= 20, "AudioManager 2D/3D pools expanded >= 20 channels")

	# 4. Instantiate GameWorld cleanly for live mechanics checks
	var world_scene := load("res://scenes/game_world.tscn") as PackedScene
	_check(runner, world_scene != null, "Wpn: game_world.tscn loads")
	if world_scene == null:
		return
	var fx_root: Node = runner.get_tree().current_scene if runner.get_tree().current_scene != null else runner.get_tree().root
	var pre_run_children := fx_root.get_children()

	var world := world_scene.instantiate()
	runner.add_child(world)
	var rd := world.get_node_or_null("RoundDirector") as RoundDirector
	if rd:
		rd.set_process(false)
	await runner.get_tree().process_frame
	await runner.get_tree().physics_frame

	var player := world.get_node("Player") as PlayerController
	var wc := player.weapon_ctrl
	player.set_physics_process(false)
	player.global_position = Vector3(0.0, 0.05, 7.2)
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO
	wc.snap_viewmodel()

	# 5. Moving weapon parts (Slide, Bolt, Shell Casing, Bullet Decal)
	wc.give_or_replace_weapon("m1911")
	wc.snap_viewmodel()
	var pre_fx_children := fx_root.get_children()
	wc._fire_cooldown = 0.0
	wc._try_fire()
	wc._animate_viewmodel(0.016)
	var m1911_slide := wc._part_nodes.get("Slide") as Node3D
	_check(runner, m1911_slide != null and m1911_slide.position.z > 0.005, "M1911 Slide kicks back on fire")
	var spawned_shell := false
	for ch in fx_root.get_children():
		if not (ch in pre_fx_children) and ch.name.contains("Shell"):
			spawned_shell = true
	_check(runner, spawned_shell, "Firing M1911 spawns ejected brass shell casing")

	wc.give_or_replace_weapon("kar98k")
	wc.snap_viewmodel()
	wc._fire_cooldown = 0.0
	wc._try_fire()
	_check(runner, wc._bolt_cycle > 0.8, "Firing Kar98k initiates bolt cycle")
	# Aim downward at open concrete courtyard floor to verify bullet decal spawn
	player.head.rotation.x = -0.60
	wc._fire_cooldown = 0.0
	wc._try_fire()
	var spawned_decal := false
	for ch in fx_root.get_children():
		if ch is Decal:
			spawned_decal = true
	_check(runner, spawned_decal, "Hitscan world impact spawns Decal bullet hole")
	player.head.rotation = Vector3.ZERO
	player.camera.rotation = Vector3.ZERO
	player._recoil_pitch = 0.0
	player._recoil_yaw = 0.0

	# 6. Layer-16 pass-through + Easter-egg quest trigger_quest_hit()
	# Open South Spawn lane (z=2.0..7.2 is completely clear of Sherman Tank)
	var inert_wall := Area3D.new()
	inert_wall.collision_layer = 16
	inert_wall.collision_mask = 0
	var inert_cs := CollisionShape3D.new()
	var inert_box := BoxShape3D.new()
	inert_box.size = Vector3(2.0, 2.0, 0.2)
	inert_cs.shape = inert_box
	inert_wall.add_child(inert_cs)
	world.add_child(inert_wall)
	inert_wall.global_position = Vector3(0.0, 1.5, 4.8)

	var z_behind := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_behind.setup("soldier", 500.0, 2.0, null)
	world.add_child(z_behind)
	z_behind.set_physics_process(false)
	z_behind.global_position = Vector3(0.0, 0.0, 2.4)

	await runner.get_tree().physics_frame
	wc.give_or_replace_weapon("m14")
	wc.snap_viewmodel()
	wc.is_aiming = true
	player.head.rotation.x = -0.05
	player.camera.rotation = Vector3.ZERO
	player._recoil_pitch = 0.0
	player._recoil_yaw = 0.0
	wc._fire_cooldown = 0.0
	wc._try_fire()
	_check(runner, z_behind.hp < 500.0, "Bullets pass cleanly through inert Layer-16 areas to hit zombie behind")
	wc.is_aiming = false
	player.head.rotation.x = 0.0
	player.camera.rotation = Vector3.ZERO
	player._recoil_pitch = 0.0
	player._recoil_yaw = 0.0
	inert_wall.queue_free()
	z_behind.queue_free()

	var quest_target := Area3D.new()
	quest_target.collision_layer = 16
	quest_target.collision_mask = 0
	var q_script := GDScript.new()
	q_script.source_code = "extends Area3D\nvar hit_count := 0\nfunc trigger_quest_hit() -> void:\n\thit_count += 1\n"
	q_script.reload()
	quest_target.set_script(q_script)
	var q_cs := CollisionShape3D.new()
	var q_box := BoxShape3D.new()
	q_box.size = Vector3(1.5, 1.5, 0.4)
	q_cs.shape = q_box
	quest_target.add_child(q_cs)
	world.add_child(quest_target)
	quest_target.global_position = Vector3(0.0, 1.6, 3.8)
	await runner.get_tree().physics_frame
	wc._fire_cooldown = 0.0
	wc._try_fire()
	_check(runner, int(quest_target.get("hit_count")) == 1, "Shooting Easter-egg Area3D triggers trigger_quest_hit()")
	quest_target.queue_free()
	await runner.get_tree().process_frame

	# 7. Wunderwaffe DG-2 (10-chain) & DG-3 JZ (24-chain) verification
	# Open cluster inside South Spawn Courtyard (x in [-4.5..4.5], z in [2.0..5.2], clear of props)
	var cluster_offsets: Array[Vector3] = []
	for row in range(4):
		for col in range(7):
			if cluster_offsets.size() >= 26:
				break
			cluster_offsets.append(Vector3(-3.0 + float(col) * 1.0, 0.0, 5.0 - float(row) * 0.9))

	var line_zombies: Array[ZombieAI] = []
	for i in range(26):
		var zx := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
		zx.setup("soldier", 200.0, 2.0, null)
		world.add_child(zx)
		zx.set_physics_process(false)
		zx.global_position = Vector3(0.0, 0.0, 5.2) if i == 0 else cluster_offsets[i]
		line_zombies.append(zx)
	await runner.get_tree().physics_frame

	wc.give_or_replace_weapon("wunderwaffe")
	wc.snap_viewmodel()
	player.head.rotation.x = -0.14
	wc._fire_cooldown = 0.0
	wc._try_fire()
	var killed_base := 0
	for zx in line_zombies:
		if zx.state == ZombieAI.State.DEAD:
			killed_base += 1
	_check(runner, killed_base == 10, "Wunderwaffe DG-2 chains across exactly 10 zombies (killed=%d)" % killed_base)
	for zx in line_zombies:
		zx.queue_free()
	line_zombies.clear()
	await runner.get_tree().process_frame

	for i in range(26):
		var zx := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
		zx.setup("soldier", 200.0, 2.0, null)
		world.add_child(zx)
		zx.set_physics_process(false)
		zx.global_position = Vector3(0.0, 0.0, 5.2) if i == 0 else cluster_offsets[i]
		line_zombies.append(zx)
	await runner.get_tree().physics_frame

	player.pack_current_weapon()
	wc.snap_viewmodel()
	player.head.rotation.x = -0.14
	wc._fire_cooldown = 0.0
	wc._try_fire()
	var killed_pap := 0
	for zx in line_zombies:
		if zx.state == ZombieAI.State.DEAD:
			killed_pap += 1
	_check(runner, killed_pap == 24, "Wunderwaffe DG-3 JZ (PaP) chains across exactly 24 zombies (killed=%d)" % killed_pap)
	player.head.rotation.x = 0.0
	for zx in line_zombies:
		zx.queue_free()
	line_zombies.clear()
	await runner.get_tree().process_frame

	# 8. Mule Kick 3rd weapon slot + clean drop on perk loss
	GameManager.lose_all_perks()
	wc.weapons = [WeaponDB.create_weapon_state("m1911", false)]
	wc._equip_weapon(0)
	_check(runner, wc.max_weapons == 2, "Default max_weapons == 2 without Mule Kick")
	GameManager.grant_perk("mulekick")
	_check(runner, wc.max_weapons == 3, "Mule Kick raises max_weapons to 3")
	wc.give_or_replace_weapon("mp40")
	wc.give_or_replace_weapon("stg44")
	_check(runner, wc.weapons.size() == 3 and wc.active_idx == 2, "Mule Kick allows carrying 3 weapons simultaneously")
	GameManager.lose_all_perks()
	_check(runner, wc.max_weapons == 2 and wc.weapons.size() == 2 and wc.active_idx < 2, "Losing Mule Kick cleanly drops 3rd weapon slot")

	# 9. Deadshot Daiquiri spread tightening + ADS head snap
	wc.give_or_replace_weapon("stg44")
	wc.is_aiming = false
	var hip_spread_base := wc.get_crosshair_spread_px()
	GameManager.grant_perk("deadshot")
	var hip_spread_ds := wc.get_crosshair_spread_px()
	_check(runner, hip_spread_ds < hip_spread_base * 0.72, "Deadshot tightens hipfire spread significantly (%.1f -> %.1f)" % [hip_spread_base, hip_spread_ds])

	var z_ds := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_ds.setup("soldier", 250.0, 2.0, null)
	world.add_child(z_ds)
	z_ds.set_physics_process(false)
	z_ds.global_position = Vector3(0.35, 0.0, 2.2) # ~4.0 deg off-center from z=7.2, open LoS
	await runner.get_tree().process_frame
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO
	var pre_yaw := player.rotation.y
	wc._apply_deadshot_ads_snap()
	_check(runner, absf(player.rotation.y - pre_yaw) > 0.005, "Deadshot ADS snap nudges aim toward nearby zombie head inside cone")
	z_ds.queue_free()
	player.rotation = Vector3.ZERO
	player.head.rotation = Vector3.ZERO
	await runner.get_tree().process_frame

	# 10. PhD Flopper explosive immunity + slide/dive flop explosion
	player.hp = player.max_hp
	GameManager.lose_all_perks()
	player.take_damage(25.0, Vector3(0, 1, 0), true)
	_check(runner, player.hp < player.max_hp, "Explosive damage hurts player without PhD Flopper")
	player.hp = player.max_hp
	GameManager.grant_perk("phdflopper")
	player.take_damage(45.0, Vector3(0, 1, 0), true)
	_check(runner, is_equal_approx(player.hp, player.max_hp), "PhD Flopper blocks 100% explosive self-damage")

	var z_phd := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_phd.setup("soldier", 300.0, 2.0, null)
	world.add_child(z_phd)
	z_phd.set_physics_process(false)
	z_phd.global_position = player.global_position + Vector3(0.0, 0.0, -2.5)
	player.start_slide(Vector3.FORWARD)
	_check(runner, player.is_sliding, "Sprint-slide activates cleanly")
	player._update_camera_motion(0.20)
	_check(runner, player.head.position.y < 1.2, "Sprint-slide dips head camera height cleanly")
	player._finish_slide(true)
	_check(runner, not player.is_sliding and z_phd.state == ZombieAI.State.DEAD, "PhD Flopper triggers Nuke flop explosion on slide finish")
	z_phd.queue_free()

	# Fall-drop PhD trigger check
	var z_fall := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_fall.setup("soldier", 300.0, 2.0, null)
	world.add_child(z_fall)
	z_fall.set_physics_process(false)
	z_fall.global_position = player.global_position + Vector3(1.5, 0.0, 0.0)
	player._was_grounded = false
	player._air_peak_y = player.global_position.y + 3.1
	player._grounded_override = true
	player._handle_movement(0.016)
	_check(runner, z_fall.state == ZombieAI.State.DEAD, "PhD Flopper triggers Nuke explosion when landing from >=2.2m drop")
	z_fall.queue_free()
	player._grounded_override = false

	# 11. Electric Cherry reload shockwave
	GameManager.grant_perk("electriccherry")
	var z_ec := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_ec.setup("soldier", 400.0, 2.0, null)
	world.add_child(z_ec)
	z_ec.set_physics_process(false)
	z_ec.global_position = player.global_position + Vector3(-1.8, 0.0, 0.0)
	wc.weapons[wc.active_idx]["mag"] = 1
	wc.start_reload()
	_check(runner, wc.is_reloading and z_ec.hp < 400.0, "Electric Cherry reload deals electric shock damage to nearby zombie")
	z_ec.queue_free()
	wc._finish_reload()

	# 12. HUD: 9-perk support, chalk counter, directional damage arc, PaP badge
	var hud := world.get_node_or_null("HUD")
	_check(runner, hud != null and hud.is_in_group("hud"), "HUD registered in 'hud' group")
	for pid in ["quickrevive", "juggernog", "speedcola", "doubletap", "staminup", "mulekick", "deadshot", "phdflopper", "electriccherry"]:
		GameManager.grant_perk(pid)
	var perks_box := world.get_node("HUD/BottomLeft/PerksBox")
	_check(runner, perks_box.get_child_count() == 9, "HUD PerksBox displays all 9 perks simultaneously (count=%d)" % perks_box.get_child_count())

	var chalk := world.get_node_or_null("HUD/BottomLeft/ChalkRow/ChalkCounter") as HudChalkCounter
	_check(runner, chalk != null, "HUD includes HudChalkCounter")
	if chalk:
		chalk.set_round(7, false)
		_check(runner, chalk.round_num == 7, "HudChalkCounter updates round cleanly (7)")
		chalk.set_round(12, false)
		_check(runner, chalk.round_num == 12, "HudChalkCounter supports double-digit rounds cleanly (12)")

	var dmg_arc := world.get_node("HUD/DamageArc") as HudDamageArc
	if dmg_arc:
		dmg_arc._pings.clear()
	hud.on_player_damaged(25.0, player.global_position + Vector3(4.0, 0.0, 0.0), player.global_position, player.global_transform.basis)
	_check(runner, dmg_arc != null and dmg_arc._pings.size() == 1, "HUD DamageArc registers directional damage ping cleanly")

	# Clean up world + all transient FX nodes spawned on fx_root
	for ch in fx_root.get_children():
		if not (ch in pre_run_children):
			fx_root.remove_child(ch)
			ch.queue_free()
	AudioManager.stop_ambience()
	if AudioManager._ambience_player:
		AudioManager._ambience_player.stream = null
	for p2 in AudioManager._pool_2d:
		if p2:
			p2.stop()
			p2.stream = null
	for p3 in AudioManager._pool_3d:
		if p3:
			p3.stop()
			p3.stream = null
	await runner.get_tree().create_timer(0.08).timeout
	await runner.get_tree().process_frame
	await runner.get_tree().process_frame
	GameManager.reset_match()

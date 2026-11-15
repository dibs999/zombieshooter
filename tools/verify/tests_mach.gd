extends RefCounted
class_name TestsMach


static func _check(runner: Node, cond: bool, msg: String) -> void:
	runner.call("_check", cond, msg)


static func _await_body_in_area(runner: Node, area: Area3D, body: Node3D, max_frames: int = 10) -> bool:
	for _i in range(max_frames):
		await runner.get_tree().physics_frame
		if not is_instance_valid(body):
			return false
		if area.get_overlapping_bodies().has(body):
			return true
	return false


static func _aim_player_at(player: PlayerController, target_pos: Vector3) -> void:
	var eye := player.global_position + Vector3(0.0, player.head.position.y, 0.0)
	var diff := target_pos - eye
	var horiz_len := maxf(0.001, Vector2(diff.x, diff.z).length())
	player.rotation = Vector3(0.0, atan2(-diff.x, -diff.z), 0.0)
	player.head.rotation = Vector3(atan2(diff.y, horiz_len), 0.0, 0.0)
	player.camera.rotation = Vector3.ZERO
	player._recoil_pitch = 0.0
	player._recoil_yaw = 0.0
	player.weapon_ctrl.snap_viewmodel()


static func run_checks(runner: Node) -> void:
	print("[Mach] Running Stream D Perks, Wunderfizz, Fire Trap, Easter Egg Quest & Song Teddy checks...")
	GameManager.reset_match()

	# 1. Verify Stream D models, UI textures, shader, and 115 song WAV
	var model_nodes := {
		"perk_mulekick": [],
		"perk_deadshot": [],
		"perk_phdflopper": [],
		"perk_electriccherry": [],
		"der_wunderfizz": ["OrbNode", "TeslaRing", "SpinBottle"],
		"fire_trap": ["PullLever", "IndicatorLamp"],
		"fire_trap_burner": [],
		"quest_terminal": ["QuestCRTScreen", "StatusBeacon"],
		"quest_resonator": ["SpireCrystal"],
		"quest_canister": ["FillCore"],
	}
	for mname in model_nodes.keys():
		var mpath := "res://assets/models/props/%s.glb" % mname
		var exists := ResourceLoader.exists(mpath)
		_check(runner, exists, "Mach model exists: " + mpath)
		if exists:
			var inst := (load(mpath) as PackedScene).instantiate()
			var ok := true
			for cname in model_nodes[mname]:
				if inst.find_child(cname, true, false) == null:
					ok = false
					printerr("    missing child node '%s' in %s" % [cname, mname])
			_check(runner, ok, "Mach model '%s' has required nodes %s" % [mname, str(model_nodes[mname])])
			inst.free()

	for pid in ["mulekick", "deadshot", "phdflopper", "electriccherry"]:
		_check(runner, ResourceLoader.exists("res://assets/textures/ui/perk_%s.png" % pid), "Perk UI icon exists: perk_%s.png" % pid)
	_check(runner, ResourceLoader.exists("res://assets/shaders/fire_wall.gdshader"), "Fire wall shader exists")
	_check(runner, ResourceLoader.exists("res://assets/textures/props/fire_flame_sprite.png"), "Fire flame sprite exists")
	_check(runner, ResourceLoader.exists("res://assets/audio/ui/ee_song_115.wav"), "Easter egg song WAV exists")

	# 2. Verify GameManager 9-Perk Registry, 4-Perk Limit & grant_perk() compatibility
	_check(runner, GameManager.PERK_INFO.size() == 9, "GameManager.PERK_INFO registers all 9 perks")
	_check(runner, GameManager.unlocked_zones.has("north_yard") and not GameManager.unlocked_zones["north_yard"], "north_yard starts locked in GameManager.unlocked_zones")
	_check(runner, GameManager.max_perks == 4, "Default perk limit == 4")

	for pid in ["quickrevive", "juggernog", "speedcola", "doubletap"]:
		_check(runner, GameManager.grant_perk(pid, true), "Can purchase perk %d/4 (%s)" % [GameManager.perks.size(), pid])
	_check(runner, not GameManager.can_buy_perk("staminup"), "can_buy_perk blocks 5th perk at 4/4 cap")
	_check(runner, not GameManager.grant_perk("staminup", true), "grant_perk(pid, true) enforces 4/4 perk cap")
	_check(runner, GameManager.grant_perk("staminup"), "grant_perk(pid) default allows reward/test grants beyond 4-cap")
	GameManager.unlock_all_perk_slots()
	_check(runner, GameManager.max_perks == 9, "unlock_all_perk_slots() expands max_perks to 9")
	GameManager.reset_match()
	_check(runner, GameManager.max_perks == 4 and GameManager.perks.is_empty() and GameManager.quest_step == 0 and not GameManager.quest_completed, "reset_match restores perk cap 4 and resets quest state")

	# 3. Instantiate GameWorld cleanly
	var fx_root: Node = runner.get_tree().current_scene if runner.get_tree().current_scene != null else runner.get_tree().root
	var pre_children := fx_root.get_children()

	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	runner.add_child(world)
	var rd := world.get_node_or_null("RoundDirector") as RoundDirector
	if rd:
		rd.set_process(false)
	await runner.get_tree().process_frame
	await runner.get_tree().physics_frame
	await runner.get_tree().physics_frame

	var reg_ny := world.get_node_or_null("Navigation/NavRegionNorthYard") as NavigationRegion3D
	var ny_polys := reg_ny.navigation_mesh.get_polygon_count() if (reg_ny and reg_ny.navigation_mesh) else 0
	_check(runner, ny_polys > 0, "NavRegionNorthYard baked cleanly (%d polys)" % ny_polys)

	var wf := world.get_node_or_null("WorldFeatures")
	_check(runner, wf != null, "WorldFeatures loaded in GameWorld")
	var mule_mach := wf.get_node_or_null("PerkMuleKick") as PerkMachine
	var phd_mach := wf.get_node_or_null("PerkPhDFlopper") as PerkMachine
	var deadshot_mach := wf.get_node_or_null("PerkDeadshot") as PerkMachine
	var cherry_mach := wf.get_node_or_null("PerkElectricCherry") as PerkMachine
	var wunderfizz := wf.get_node_or_null("WunderfizzMachine") as WunderfizzMachine
	var fire_trap := wf.get_node_or_null("FireTrap") as FireTrap
	var quest := wf.get_node_or_null("EasterEggQuest") as EasterEggQuest
	_check(runner, mule_mach != null and phd_mach != null and deadshot_mach != null and cherry_mach != null and wunderfizz != null and fire_trap != null and quest != null, "All new machines, traps, Wunderfizz, and Quest loaded inside WorldFeatures")

	var box_east := world.get_node("Interactables/BoxEast") as MysteryBox
	_check(runner, "wunderwaffe" in box_east._all_weapon_ids, "MysteryBox spin previews include wunderwaffe")

	var player := world.get_node("Player") as PlayerController
	player.set_physics_process(false)
	GameManager.add_points(50000, "")

	# Verify Motorpool door unlocks north_yard + NavMesh path
	var map_rid: RID = (world as Node3D).get_world_3d().navigation_map
	for _i in range(30):
		await runner.get_tree().process_frame
		await runner.get_tree().physics_frame
		NavigationServer3D.map_force_update(map_rid)
		var it1 := NavigationServer3D.map_get_iteration_id(map_rid)
		if it1 >= 1:
			await runner.get_tree().process_frame
			await runner.get_tree().physics_frame
			if NavigationServer3D.map_get_iteration_id(map_rid) == it1:
				break
	var pre_nav_iter := NavigationServer3D.map_get_iteration_id(map_rid)
	var door_ny := world.get_node("Interactables/DoorReactorNorth") as BuyableDoor
	door_ny.interact(player)
	for _i in range(40):
		await runner.get_tree().physics_frame
		await runner.get_tree().process_frame
		NavigationServer3D.map_force_update(map_rid)
		if NavigationServer3D.map_get_iteration_id(map_rid) > pre_nav_iter:
			break
	var ny_path := NavigationServer3D.map_get_path(map_rid, Vector3(16.5, 0.0, -16.0), Vector3(16.5, 0.0, -34.0), true)
	var reached_ny := ny_path.size() >= 2 and ny_path[ny_path.size() - 1].z < -28.0
	_check(runner, GameManager.unlocked_zones["north_yard"] and reached_ny, "DoorReactorNorth unlocks north_yard & NavMesh bridge")

	# Verify Pre-Power prompts & Quest Step 0 -> Step 1 -> Step 2 automatic power transition
	_check(runner, wunderfizz.get_interact_prompt(player).contains("Power"), "Wunderfizz requires power before Power On")
	_check(runner, fire_trap.get_interact_prompt(player).contains("Power"), "FireTrap requires power before Power On")
	_check(runner, deadshot_mach.get_interact_prompt(player).contains("Power"), "New PerkMachines require power before Power On")

	quest.interact(player)
	_check(runner, quest.step == 1 and GameManager.quest_step == 1, "Interacting with QuestTerminal initiates Step 1 (Activate Power)")
	var pwr := world.get_node("Interactables/PowerSwitch") as PowerSwitch
	pwr.interact(player)
	_check(runner, GameManager.power_on and quest.step == 2 and GameManager.quest_step == 2, "PowerSwitch advances Quest cleanly from Step 1 -> Step 2")

	# 4. PerkMachine 4-Perk Limit + Der Wunderfizz enforcement
	(world.get_node("Interactables/PerkQuickRevive") as PerkMachine).interact(player)
	(world.get_node("Interactables/PerkJuggernog") as PerkMachine).interact(player)
	mule_mach.interact(player)
	deadshot_mach.interact(player)
	_check(runner, GameManager.perks.size() == 4 and GameManager.has_perk("mulekick") and GameManager.has_perk("deadshot"), "Purchased 4 perks including Mule Kick & Deadshot Daiquiri")
	_check(runner, cherry_mach.get_interact_prompt(player) == "Perk Limit Reached (4/4)", "5th PerkMachine displays Perk Limit Reached (4/4)")
	cherry_mach.interact(player)
	_check(runner, not GameManager.has_perk("electriccherry") and GameManager.perks.size() == 4, "5th PerkMachine blocks purchase at 4/4 perk cap")
	_check(runner, wunderfizz.get_interact_prompt(player) == "Perk Limit Reached (4/4)", "Der Wunderfizz displays Perk Limit Reached (4/4) when full")
	wunderfizz.interact(player)
	_check(runner, wunderfizz.state == WunderfizzMachine.FizzState.IDLE, "Der Wunderfizz blocks spin when player is at 4/4 perk cap")

	GameManager.lose_all_perks()
	var pts_before_fizz := GameManager.points
	wunderfizz.interact(player)
	_check(runner, wunderfizz.state == WunderfizzMachine.FizzState.SPINNING and GameManager.points == pts_before_fizz - WunderfizzMachine.COST, "Der Wunderfizz starts spinning and debits 1500 points")
	wunderfizz._process(0.16)
	wunderfizz._finish_spin()
	var rolled_perk := wunderfizz._chosen_perk
	_check(runner, wunderfizz.state == WunderfizzMachine.FizzState.READY_TAKE and rolled_perk != "" and wunderfizz.get_interact_prompt(player).contains("Drink"), "Der Wunderfizz lands on unowned perk and offers [E] Drink")
	wunderfizz.interact(player)
	_check(runner, GameManager.has_perk(rolled_perk) and wunderfizz.state == WunderfizzMachine.FizzState.IDLE, "Drinking from Der Wunderfizz grants rolled perk (%s)" % rolled_perk)

	# 5. Fire Trap Mechanics (Zombie Instakill, Panzer DoT, Player Burn vs PhD Flopper)
	GameManager.lose_all_perks()
	var pts_before_trap := GameManager.points
	fire_trap.interact(player)
	_check(runner, fire_trap.is_running and fire_trap.flame_wall.visible and fire_trap.flame_particles.emitting and GameManager.points == pts_before_trap - FireTrap.COST, "FireTrap activates flames, particles, and debits 1000 points")
	fire_trap.set_process(false)

	var z_burn := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_burn.setup("soldier", 200.0, 2.0, null)
	world.add_child(z_burn)
	z_burn.set_physics_process(false)
	z_burn.global_position = Vector3(18.0, 0.0, -26.2)
	await _await_body_in_area(runner, fire_trap.kill_area, z_burn)
	fire_trap._apply_fire_damage(0.05)
	_check(runner, z_burn.state == ZombieAI.State.DEAD, "FireTrap instakills regular zombie inside flame trench")
	z_burn.queue_free()

	var p_burn_boss := rd.spawn_panzer_boss(8, Vector3(18.0, 0.0, -26.2))
	p_burn_boss.set_physics_process(false)
	await _await_body_in_area(runner, fire_trap.kill_area, p_burn_boss)
	var boss_hp_before := p_burn_boss.hp
	fire_trap._apply_fire_damage(0.05)
	_check(runner, not p_burn_boss.is_dead and p_burn_boss.hp < boss_hp_before, "FireTrap deals DoT to Panzersoldat without 1-shotting boss (%.1f -> %.1f)" % [boss_hp_before, p_burn_boss.hp])
	for _tick in range(40):
		if p_burn_boss.is_dead:
			break
		fire_trap._apply_fire_damage(FireTrap.PANZER_TICK_INTERVAL + 0.02)
	_check(runner, p_burn_boss.is_dead, "Sustained FireTrap DoT defeats Panzersoldat boss")
	if is_instance_valid(p_burn_boss):
		p_burn_boss.queue_free()

	player.global_position = Vector3(18.0, 0.05, -26.2)
	await _await_body_in_area(runner, fire_trap.kill_area, player)
	player.hp = player.max_hp
	fire_trap._player_tick_cd = 0.0
	fire_trap._apply_fire_damage(0.05)
	_check(runner, player.hp < player.max_hp, "FireTrap burns unprotected player walking into flames")

	GameManager.grant_perk("phdflopper")
	player.hp = player.max_hp
	fire_trap._player_tick_cd = 0.0
	fire_trap._apply_fire_damage(0.05)
	_check(runner, is_equal_approx(player.hp, player.max_hp), "PhD Flopper grants full FireTrap burn immunity")
	player.global_position = Vector3(0.0, 0.05, -2.5)
	fire_trap.set_trap_active(false, true)
	fire_trap.set_process(true)

	# 6. Operation Element 115 Multi-Step Quest End-to-End (Steps 2 -> 3 -> 4 -> 5)
	GameManager.lose_all_perks()
	player.weapon_ctrl.weapons = [WeaponDB.create_weapon_state("m1911", false)]
	player.weapon_ctrl._equip_weapon(0)
	player.give_weapon("m14")
	var r0 := wf.get_node("QuestResonator0") as QuestResonator
	var r1 := wf.get_node("QuestResonator1") as QuestResonator
	var r2 := wf.get_node("QuestResonator2") as QuestResonator
	var r3 := wf.get_node("QuestResonator3") as QuestResonator
	_aim_player_at(player, r0.global_position + Vector3(0.0, 0.08, 0.0))
	player.weapon_ctrl._fire_cooldown = 0.0
	player.weapon_ctrl._try_fire()
	_check(runner, r0.is_attuned, "Live bullet ray from WeaponController attunes QuestResonator0")
	r1.trigger_quest_hit()
	r2.trigger_quest_hit()
	r3.trigger_quest_hit()
	_check(runner, quest.step == 3 and GameManager.quest_step == 3, "Attuning all 4 Resonators advances Operation Element 115 to Step 3 (Soul Canisters)")

	var canisters := [
		wf.get_node("QuestCanister0") as QuestCanister,
		wf.get_node("QuestCanister1") as QuestCanister,
		wf.get_node("QuestCanister2") as QuestCanister,
	]
	for c_idx in range(canisters.size()):
		var c := canisters[c_idx] as QuestCanister
		for s_i in range(QuestCanister.REQUIRED_SOULS):
			var sz := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
			sz.setup("soldier", 50.0, 1.8, null)
			world.add_child(sz)
			sz.set_physics_process(false)
			sz.global_position = c.global_position + Vector3(1.2, 0.0, 0.0)
			sz.take_damage(999.0, false, sz.global_position, Vector3.UP)
			sz.queue_free()
		_check(runner, c.is_filled and is_equal_approx(c._fill_core.scale.y, 1.0), "QuestCanister%d filled (5/5 souls) and FillCore scaled to 1.0" % c_idx)

	_check(runner, quest.step == 4 and GameManager.quest_step == 4 and quest._quest_boss != null and is_instance_valid(quest._quest_boss), "Filling all 3 canisters advances to Step 4 & spawns Containment Panzersoldat")
	var qboss := quest._quest_boss
	qboss.take_damage(99999.0, false, qboss.global_position, Vector3.UP)
	_check(runner, quest._boss_defeated and quest.get_interact_prompt(player).contains("Override"), "Defeating Containment Panzersoldat unlocks Final Extraction Override on QuestTerminal")

	var pts_before_ee := GameManager.points
	quest.interact(player)
	var cur_w := player.get_current_weapon_state()
	_check(runner, quest.completed and GameManager.quest_completed and GameManager.quest_step == 5, "Final Override completes Operation Element 115")
	_check(runner, GameManager.max_perks == 9 and GameManager.perks.size() == 9, "Quest reward unlocks all 9 perk slots & grants all 9 perks")
	_check(runner, player.has_weapon("wunderwaffe") and WeaponDB.get_display_name(cur_w) == "Wunderwaffe DG-3 JZ" and bool(cur_w.get("packed", false)), "Quest reward equips Pack-a-Punched Wunderwaffe DG-3 JZ")
	_check(runner, GameManager.points >= pts_before_ee + 5000, "Quest reward grants +5000 points")

	# 7. Song Teddies & UI Status Telemetry
	var t0 := wf.get_node("SongTeddy0") as SongTeddy
	var t1 := wf.get_node("SongTeddy1") as SongTeddy
	var t2 := wf.get_node("SongTeddy2") as SongTeddy
	t0.interact(player)
	t1.interact(player)
	_check(runner, t0.activated and t1.activated and not t2.song_player.playing, "Activating 2/3 Song Teddies records progress without prematurely playing song")
	var pts_before_song := GameManager.points
	t2.interact(player)
	_check(runner, t2.activated and t2.song_player.playing and GameManager.points == pts_before_song + 1150, "Activating 3/3 Song Teddies plays ee_song_115.wav & grants +1150 points")

	var pause_menu := world.get_node("PauseMenu")
	pause_menu.toggle_pause()
	var pause_status := str(pause_menu.status_label.text)
	_check(runner, pause_status.contains("9 / 9") and pause_status.contains("COMPLETE"), "PauseMenu displays 9/9 perks & Operation Element 115 COMPLETE")
	pause_menu.toggle_pause()

	GameManager.lose_all_perks()
	player.take_damage(9999.0)
	await runner.get_tree().process_frame
	var go_screen := world.get_node("GameOverScreen")
	_check(runner, go_screen.visible and str(go_screen.stats_lbl.text).contains("Easter Egg: COMPLETED"), "GameOverScreen reports Easter Egg: COMPLETED")

	# Clean up
	if t2.song_player:
		t2.song_player.stop()
		t2.song_player.stream = null
	for ch in fx_root.get_children():
		if not (ch in pre_children):
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
	await runner.get_tree().create_timer(0.06).timeout
	await runner.get_tree().process_frame
	await runner.get_tree().process_frame
	GameManager.reset_match()

extends Node

var _passed: int = 0
var _failed: int = 0


func _check(cond: bool, msg: String) -> void:
	if cond:
		_passed += 1
		print("  [PASS] ", msg)
	else:
		_failed += 1
		printerr("  [FAIL] ", msg)


func _ready() -> void:
	get_tree().create_timer(180.0).timeout.connect(func():
		printerr("TIMEOUT in test_runner.gd (exceeded 180s)!")
		get_tree().quit(1)
	)
	print("=== BUNKER 115 FULL HEADLESS VERIFICATION SUITE ===")
	await get_tree().process_frame

	await _test_game_manager_and_weapon_db()
	await _cleanup_between_suites()

	await _test_main_menu()
	await _cleanup_between_suites()

	await _test_game_world_and_mechanics()
	await _cleanup_between_suites()

	print("[4/8] Running weapon/camera jitter & smoothing regression checks...")
	TestsJitter.run_checks(self)
	await _cleanup_between_suites()

	print("[5/8] Running Stream A Environment & Zone 5 verification checks...")
	await load("res://tools/verify/tests_env.gd").run_checks(self)
	await _cleanup_between_suites()

	print("[6/8] Running Stream B Zombie, Dismemberment, Hellhound & Panzer Boss checks...")
	await TestsChars.run_checks(self)
	await _cleanup_between_suites()

	print("[7/8] Running Stream C Weapons, Viewmodel, Wunderwaffe, Perks, HUD & Audio checks...")
	await TestsWpn.run_checks(self)
	await _cleanup_between_suites()

	print("[8/8] Running Stream D Perks, Wunderfizz, Fire Trap, Easter Egg & Song Teddies checks...")
	await TestsMach.run_checks(self)
	await _cleanup_between_suites()
	await get_tree().create_timer(0.15).timeout
	await get_tree().process_frame

	print("==============================================")
	print("RESULTS: %d passed, %d failed" % [_passed, _failed])
	get_tree().quit(1 if _failed > 0 else 0)


func _cleanup_between_suites() -> void:
	get_tree().paused = false
	for tw in get_tree().get_processed_tweens():
		if tw and tw.is_valid():
			tw.kill()
	for ch in get_children():
		remove_child(ch)
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
	GameManager.reset_match()
	await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().process_frame


func _test_game_manager_and_weapon_db() -> void:
	print("[1/8] Testing GameManager & WeaponDB formulas...")
	GameManager.reset_match()
	_check(is_equal_approx(GameManager.get_zombie_health_for_round(1), 150.0), "Round 1 HP == 150")
	_check(is_equal_approx(GameManager.get_zombie_health_for_round(5), 550.0), "Round 5 HP == 550")
	_check(is_equal_approx(GameManager.get_zombie_health_for_round(9), 950.0), "Round 9 HP == 950")
	_check(is_equal_approx(GameManager.get_zombie_health_for_round(10), 1045.0), "Round 10 HP == 1045")
	_check(GameManager.get_zombie_count_for_round(1) == 6, "Round 1 zombie count == 6")
	_check(GameManager.get_zombie_count_for_round(4) == 18, "Round 4 zombie count == 18")
	_check(GameManager.is_dog_round(5) and GameManager.is_dog_round(10) and not GameManager.is_dog_round(6), "Dog rounds every 5th round")

	GameManager.add_points(60)
	_check(GameManager.points == 560, "Base points add correctly (+60 -> 560)")
	GameManager.activate_powerup("double_points")
	GameManager.add_points(100)
	_check(GameManager.points == 760, "Double points multiplier active (+200 -> 760)")
	_check(not GameManager.spend_points(9999), "Insufficient points purchase rejected")

	for wid in WeaponDB.WEAPON_DATA.keys():
		var mpath := str(WeaponDB.WEAPON_DATA[wid]["model"])
		_check(ResourceLoader.exists(mpath), "Weapon model exists: " + mpath)
	var pap_m1911 := WeaponDB.create_weapon_state("m1911", true)
	_check(WeaponDB.get_display_name(pap_m1911) == "Mustang & Sally", "M1911 PaP name == Mustang & Sally")
	_check(bool(WeaponDB.get_stat(pap_m1911, "is_explosive")), "Mustang & Sally becomes explosive")
	var pap_ray := WeaponDB.create_weapon_state("raygun", true)
	_check(WeaponDB.get_display_name(pap_ray) == "Porter's X2 Ray Gun", "Ray Gun PaP name == Porter's X2 Ray Gun")
	_check(is_equal_approx(float(WeaponDB.get_stat(pap_ray, "damage")), 1650.0), "Ray Gun PaP damage == 1650")


func _test_main_menu() -> void:
	print("[2/8] Testing MainMenu 3D scene & diorama...")
	var menu := (load("res://scenes/main_menu.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(menu)
	await get_tree().process_frame
	for slot_name in ["TankSlot", "Crystal1", "Crystal2", "Zombie1", "Perk1", "Box1"]:
		var slot := menu.get_node_or_null("Backdrop3D/Props/" + slot_name)
		_check(slot != null and slot.get_child_count() > 0, "Menu diorama loaded " + slot_name)
	var zap := menu.get_node("Backdrop3D/Props/Zombie1").find_child("AnimationPlayer", true, false) as AnimationPlayer
	_check(zap != null and zap.is_playing(), "Menu zombie Idle animation playing")
	menu.queue_free()
	await get_tree().process_frame


func _test_game_world_and_mechanics() -> void:
	print("[3/8] Testing GameWorld navigation, doors, barricades, perks, mystery box, PaP & AI...")
	GameManager.reset_match()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(world)
	await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame

	# 1. Check all 4 NavRegions baked cleanly
	for rname in ["NavRegionSpawn", "NavRegionLab", "NavRegionEast", "NavRegionReactor"]:
		var reg := world.get_node_or_null("Navigation/" + rname) as NavigationRegion3D
		var pcount := reg.navigation_mesh.get_polygon_count() if (reg and reg.navigation_mesh) else 0
		_check(pcount > 0, "%s baked (%d polys)" % [rname, pcount])

	# 2. Check Navigation path respects locked door, then opens cleanly
	var map_rid: RID = world.get_world_3d().navigation_map
	NavigationServer3D.map_force_update(map_rid)
	var locked_path := NavigationServer3D.map_get_path(map_rid, Vector3(0, 0, 4), Vector3(-16, 0, 0), true)
	var crossed_before := false
	for pt in locked_path:
		if pt.x < -10.5:
			crossed_before = true
	_check(not crossed_before, "Locked DoorSpawnWest blocks NavMesh pathing to Lab")

	GameManager.add_points(20000)
	var door_west := world.get_node("Interactables/DoorSpawnWest") as BuyableDoor
	var player := world.get_node("Player") as PlayerController
	_check(door_west != null and player != null, "DoorSpawnWest & Player loaded")
	door_west.interact(player)
	await get_tree().process_frame
	await get_tree().physics_frame
	NavigationServer3D.map_force_update(map_rid)
	var unlocked_path := NavigationServer3D.map_get_path(map_rid, Vector3(0, 0, 4), Vector3(-16, 0, 0), true)
	var reached_lab := unlocked_path.size() >= 2 and unlocked_path[unlocked_path.size() - 1].x < -14.0
	_check(reached_lab, "Opened DoorSpawnWest enables NavMesh path into Lab (pts=%d)" % unlocked_path.size())

	# 3. Open East Courtyard + Power Switch -> opens remote DoorPowerShortcut & enables path into Reactor!
	var door_east := world.get_node("Interactables/DoorSpawnEast") as BuyableDoor
	door_east.interact(player)
	_check(door_east.is_opened and GameManager.unlocked_zones["east_courtyard"], "DoorSpawnEast unlocks east_courtyard")

	var jugg := world.get_node("Interactables/PerkJuggernog") as PerkMachine
	jugg.interact(player)
	_check(not GameManager.has_perk("juggernog"), "Juggernog blocked before Power On")

	var pwr := world.get_node("Interactables/PowerSwitch") as PowerSwitch
	var teleporter := world.get_node("EmergencyTeleporter") as EmergencyTeleporter
	var console_ray := PhysicsRayQueryParameters3D.create(Vector3(-13.2, 1.2, -13.6), Vector3(-13.2, 1.2, -15.8))
	console_ray.collision_mask = 16
	console_ray.collide_with_areas = true
	console_ray.collide_with_bodies = false
	var console_hit: Dictionary = world.get_world_3d().direct_space_state.intersect_ray(console_ray)
	_check(not console_hit.is_empty() and console_hit["collider"].get_parent() == teleporter, "Transfer console is reachable by the player's interaction ray")
	var transfer_start := player.global_position
	var transfer_points := GameManager.points
	teleporter.interact(player)
	_check(player.global_position == transfer_start and GameManager.points == transfer_points, "Emergency transfer cannot bypass power requirement or spend points before power")
	_check(teleporter.get_interact_prompt(player).contains("Power"), "Emergency transfer explains missing power")
	pwr.interact(player)
	_check(GameManager.power_on, "PowerSwitch activates facility power")
	await get_tree().process_frame
	await get_tree().physics_frame
	NavigationServer3D.map_force_update(map_rid)
	var shortcut := world.get_node("Interactables/DoorPowerShortcut") as BuyableDoor
	_check(shortcut.is_opened, "Emergency Vault Shortcut opens automatically on Power On")
	var reactor_path := NavigationServer3D.map_get_path(map_rid, Vector3(0, 0, 4), Vector3(0, 0, -16), true)
	var reached_reactor := reactor_path.size() >= 2 and reactor_path[reactor_path.size() - 1].z < -12.0
	_check(reached_reactor, "Power Shortcut enables NavMesh path from Spawn to Reactor (pts=%d)" % reactor_path.size())

	# Emergency transfer: successful escape, cooldown, insufficient points and downed state.
	player.global_position = Vector3(-15, 0.1, -15.5)
	player.velocity = Vector3(3, -2, 1)
	teleporter.interact(player)
	_check(player.global_position == EmergencyTeleporter.EXIT_POSITION and player.velocity == Vector3.ZERO, "Emergency transfer moves player safely to Courtyard and clears momentum")
	_check(GameManager.points == transfer_points - EmergencyTeleporter.COST, "Emergency transfer debits exactly 500 points")
	_check(teleporter.cooldown_remaining > 0.0 and teleporter.get_interact_prompt(player).contains("Recharging"), "Transfer console reports cooldown")
	transfer_points = GameManager.points
	teleporter.interact(player)
	_check(GameManager.points == transfer_points, "Repeated interaction during cooldown cannot spend points")
	teleporter._process(EmergencyTeleporter.COOLDOWN)
	_check(is_zero_approx(teleporter.cooldown_remaining), "Emergency transfer recharges after 45 seconds")
	GameManager.points = 0
	player.global_position = Vector3(-15, 0.1, -15.5)
	teleporter.interact(player)
	_check(player.global_position != EmergencyTeleporter.EXIT_POSITION and is_zero_approx(teleporter.cooldown_remaining), "Unaffordable transfer does not teleport or start cooldown")
	GameManager.points = transfer_points
	player.is_downed = true
	teleporter.interact(player)
	_check(GameManager.points == transfer_points and teleporter.get_interact_prompt(player).is_empty(), "Downed player cannot use emergency transfer")
	player.is_downed = false
	teleporter.interact(player)
	_check(player.global_position == EmergencyTeleporter.EXIT_POSITION, "Recharged transfer is usable again")
	player.global_position = transfer_start

	jugg.interact(player)
	_check(GameManager.has_perk("juggernog") and is_equal_approx(player.max_hp, 250.0), "Juggernog grants 250 Max HP after Power On")

	# 4. Quick Revive + Last Stand + Self-Revive shockwave
	var qr := world.get_node("Interactables/PerkQuickRevive") as PerkMachine
	qr.interact(player)
	_check(GameManager.has_perk("quickrevive"), "Quick Revive purchased")
	player.take_damage(999.0)
	_check(player.is_downed and GameManager.quick_revive_uses_left == 2 and not GameManager.has_perk("juggernog"), "Lethal hit triggers Quick Revive Last Stand & clears perks")
	player._complete_self_revive()
	_check(not player.is_downed and is_equal_approx(player.hp, 100.0), "Self-revive restores standing state with 100 HP")

	# 5. WindowBarricade planks & Carpenter & ballistic gap
	var win := world.get_node("Interactables/WinSpawnW") as WindowBarricade
	_check(win.planks.size() == 6 and win.has_planks(), "WindowBarricade loaded 6 Blender planks")
	win.tear_plank()
	win.tear_plank()
	_check(win.intact_count == 4, "Tearing 2 planks leaves 4 intact")
	GameManager.activate_powerup("carpenter")
	_check(win.intact_count == 6, "Carpenter repairs all window planks back to 6")

	# Check bullet ray passes cleanly through window opening (y=1.4)
	var space: PhysicsDirectSpaceState3D = (world as Node3D).get_world_3d().direct_space_state
	var w_ray := PhysicsRayQueryParameters3D.create(Vector3(-5.2, 1.4, 8.8), Vector3(-5.2, 1.4, 11.2))
	w_ray.collision_mask = 1
	var w_hit: Dictionary = space.intersect_ray(w_ray)
	_check(w_hit.is_empty(), "Bullets shoot cleanly through open WindowBarricade gap")

	# 6. WallBuy + MysteryBox + Teddy Bear Relocation + FireSale + Pack-a-Punch
	var wall_mp40 := world.get_node("Interactables/WallMP40") as WallBuy
	wall_mp40.interact(player)
	_check(player.has_weapon("mp40"), "WallBuy equips MP40")
	var pap := world.get_node("Interactables/PackAPunch") as PackAPunch
	pap.interact(player)
	_check(bool(player.get_current_weapon_state().get("packed", false)) and WeaponDB.get_display_name(player.get_current_weapon_state()) == "The Afterburner", "Pack-a-Punch upgrades MP40 to The Afterburner")

	# Weapon 2-slot cap & 3rd weapon replacement
	_check(player.weapon_ctrl.weapons.size() == 2, "Player has 2 weapons (M1911 + MP40 PaP)")
	player.give_weapon("stg44")
	_check(player.weapon_ctrl.weapons.size() == 2 and player.weapon_ctrl.get_current_state().get("id", "") == "stg44" and not player.has_weapon("mp40"), "3rd weapon replaces active weapon slot cleanly")

	var box_east := world.get_node("Interactables/BoxEast") as MysteryBox
	var box_lab := world.get_node("Interactables/BoxLab") as MysteryBox
	var box_reactor := world.get_node("Interactables/BoxReactor") as MysteryBox
	_check(box_east.is_active and not box_lab.is_active and not box_reactor.is_active, "Mystery Box starts active only in East Courtyard")

	# Mystery Box Teddy Bear refund + relocation
	var pts_before_teddy := GameManager.points
	box_east._last_paid_cost = 950
	box_east._chosen_weapon = "teddy_bear"
	box_east.uses_here = 4
	box_east._finish_spin()
	_check(box_east.state == MysteryBox.BoxState.MOVING and GameManager.points == pts_before_teddy + 950, "Teddy Bear sets MOVING state & refunds 950 points")
	box_east._relocate_box()
	_check(not box_east.is_active and box_east.uses_here == 0 and (box_lab.is_active != box_reactor.is_active), "Mystery Box Teddy Bear relocates active box to BoxLab or BoxReactor")
	# Restore BoxEast as active for subsequent checks
	box_lab.set_box_active(false)
	box_reactor.set_box_active(false)
	box_east.set_box_active(true)

	GameManager.activate_powerup("fire_sale")
	_check(box_lab.is_active and box_reactor.is_active and box_east._current_cost() == 10, "Fire Sale activates all 3 Mystery Boxes for $10")

	# 7. Enemy Rigging, Variant Selection (before & after add_child), Headshots, Nuke & FragGrenade
	var zombie := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	zombie.setup("soldier", 200.0, 2.5, null)
	world.add_child(zombie)
	await get_tree().process_frame
	_check(zombie._skeleton != null and zombie._head_bone_idx >= 0 and zombie._anim_player != null and zombie._anim_player.is_playing(), "Zombie rigged skeleton + Head bone + AnimationPlayer loaded & playing")
	var killed := zombie.take_damage(100.0, true, zombie.global_position, Vector3.FORWARD)
	_check(not killed and is_equal_approx(zombie.hp, 100.0), "Zombie takes precise damage before dying")
	killed = zombie.take_damage(150.0, true, zombie.global_position, Vector3.FORWARD)
	_check(killed and zombie.state == ZombieAI.State.DEAD, "Zombie dies properly & transitions to DEAD")

	# Scientist (setup AFTER add_child) & Brute (setup BEFORE add_child)
	var z_sci := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	world.add_child(z_sci)
	z_sci.setup("scientist", 150.0, 2.0, null)
	await get_tree().process_frame
	_check(z_sci.variant == "scientist" and is_equal_approx(z_sci.max_hp, 150.0) and z_sci.model_root.find_child("Zombie_scientist_Armature", true, false) != null, "Scientist variant reloads cleanly even when setup() called after add_child")

	var z_brute := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_brute.setup("brute", 150.0, 2.0, null)
	world.add_child(z_brute)
	await get_tree().process_frame
	_check(z_brute.is_brute and is_equal_approx(z_brute.max_hp, 390.0) and z_brute.head_area.position.y >= 1.85 and z_brute.model_root.find_child("Zombie_brute_Armature", true, false) != null, "Brute variant loads Zombie_brute_Armature, 2.6x HP (390), and >=1.85m head height")

	var rd := world.get_node("RoundDirector") as RoundDirector
	_check(rd != null and (rd.zombies_remaining_to_spawn + rd.active_zombies) == 6, "RoundDirector starts Round 1 quota (6)")

	var hound := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	world.add_child(hound)
	hound.setup(150.0)
	await get_tree().process_frame
	_check(hound._anim_player != null, "Hellhound AnimationPlayer loaded")
	GameManager.activate_powerup("nuke")
	_check(hound.is_dead, "Nuke kills active Hellhound")

	# 8. Electro-Trap + RayBolt + FragGrenade explosion splash damage
	var trap := world.get_node("Interactables/ElectroTrap") as ElectroTrap
	trap.interact(player)
	_check(trap.is_running and trap.arc_wall.visible, "ElectroTrap activates electrical arc barrier")

	var bolt := (load("res://scenes/fx/ray_bolt.tscn") as PackedScene).instantiate()
	_check(bolt != null, "RayBolt projectile instantiates cleanly")
	bolt.free()

	var z_frag_target := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_frag_target.setup("soldier", 200.0, 2.0, null)
	world.add_child(z_frag_target)
	z_frag_target.set_physics_process(false)
	z_frag_target.global_position = Vector3(2.0, 0.0, 2.0)
	var frag := (load("res://scenes/fx/frag_grenade_proj.tscn") as PackedScene).instantiate()
	world.add_child(frag)
	frag.global_position = Vector3(2.2, 0.2, 2.0)
	frag._detonate()
	await get_tree().process_frame
	_check(z_frag_target.state == ZombieAI.State.DEAD, "FragGrenade _detonate() deals splash damage and kills nearby zombie")

	# 9. SettingsManager FOV & Graphics Quality
	var orig_fov := SettingsManager.fov
	var orig_gfx := SettingsManager.graphics_quality
	SettingsManager.set_fov(96.0)
	SettingsManager.set_graphics_quality("Low")
	await get_tree().process_frame
	_check(is_equal_approx(SettingsManager.fov, 96.0) and is_equal_approx(player.camera.fov, 96.0) and SettingsManager.graphics_quality == "Low", "SettingsManager updates FOV on Player camera & graphics quality")
	SettingsManager.set_fov(orig_fov)
	SettingsManager.set_graphics_quality(orig_gfx)

	# 10. PauseMenu toggle & Lethal hit WITHOUT Quick Revive -> GameOverScreen
	var pause_menu := world.get_node("PauseMenu")
	_check(pause_menu != null and not pause_menu.visible, "PauseMenu starts hidden")
	pause_menu.toggle_pause()
	_check(get_tree().paused and pause_menu.visible, "PauseMenu toggles pause cleanly")
	pause_menu.toggle_pause()
	_check(not get_tree().paused and not pause_menu.visible, "PauseMenu unpauses cleanly")

	GameManager.lose_all_perks()
	player.take_damage(999.0)
	await get_tree().process_frame
	var go_screen := world.get_node("GameOverScreen")
	_check(GameManager.is_game_over and go_screen != null and go_screen.visible, "Lethal hit without Quick Revive triggers GameManager.is_game_over & displays GameOverScreen")
	transfer_points = GameManager.points
	teleporter.cooldown_remaining = 0.0
	transfer_start = player.global_position
	teleporter.interact(player)
	_check(player.global_position == transfer_start and GameManager.points == transfer_points and teleporter.get_interact_prompt(player).is_empty(), "Game Over blocks transfer without changing position or spending points")

	for ch in get_children():
		ch.queue_free()
	world.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame

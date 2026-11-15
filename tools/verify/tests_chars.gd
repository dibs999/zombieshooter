extends RefCounted
class_name TestsChars


static func run_checks(runner: Node) -> void:
	print("[Chars] Running Stream B Zombie, Dismemberment, Hellhound & Panzer Boss verification checks...")
	GameManager.reset_match()

	var world_scene := load("res://scenes/game_world.tscn") as PackedScene
	_check(runner, world_scene != null, "Chars: game_world.tscn loads cleanly")
	if world_scene == null:
		return

	var world := world_scene.instantiate()
	runner.add_child(world)
	await runner.get_tree().process_frame
	await runner.get_tree().physics_frame

	var rd := world.get_node_or_null("RoundDirector") as RoundDirector
	_check(runner, rd != null, "Chars: RoundDirector exists in GameWorld")
	if rd != null:
		rd.set_process(false)

	# 1. Verify all 5 Zombie GLB variants, armatures, Head bone, animations & dismemberment meshes
	for v in ["soldier", "scientist", "brute", "worker", "crawler"]:
		var z := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
		z.setup(v, 200.0, 2.2, null)
		world.add_child(z)
		await runner.get_tree().process_frame
		z.set_physics_process(false)

		var expected_arm := "Zombie_%s_Armature" % v
		var arm := z.model_root.find_child(expected_arm, true, false)
		_check(runner, arm != null, "Chars: %s loads %s" % [v, expected_arm])
		_check(runner, z._skeleton != null and z._head_bone_idx >= 0, "Chars: %s has Skeleton3D + Head bone" % v)
		_check(runner, z._anim_player != null and z._anim_player.is_playing(), "Chars: %s AnimationPlayer loaded & playing (%s)" % [v, z._current_anim])

		var has_core_parts := (z._mesh_head != null and z._mesh_arm_l != null and z._mesh_arm_r != null and z._mesh_torso != null)
		var has_stumps := (z._stump_head != null and z._stump_arm_l != null and z._stump_arm_r != null and z._stump_legs != null)
		_check(runner, has_core_parts and has_stumps, "Chars: %s contains Mesh_* and Stump_* dismemberment parts" % v)

		if v == "crawler":
			_check(runner, z.is_crawler and z._current_anim == "Crawl" and z._stump_legs != null and z._stump_legs.visible, "Chars: crawler spawns in Crawl anim with Stump_Legs visible")
			_check(runner, z.head_area.position.y < 0.7, "Chars: crawler lowers HeadArea cleanly (y=%.2f)" % z.head_area.position.y)
		else:
			_check(runner, z._mesh_legs != null and z._stump_head != null and not z._stump_head.visible and not z._stump_legs.visible, "Chars: %s hides stumps until dismembered" % v)
		if v == "brute":
			_check(runner, z.is_brute and is_equal_approx(z.max_hp, 520.0) and z.head_area.position.y >= 1.85, "Chars: brute scales 2.6x HP (520) and >=1.85m HeadArea")

		for req_anim in ["Idle", "Walk", "Run", "Attack", "Tear", "Vault", "Hit", "Crawl", "DeathBack", "DeathFwd", "Death"]:
			_check(runner, z._anim_player != null and z._anim_player.has_animation(req_anim), "Chars: %s has animation '%s'" % [v, req_anim])

		z.queue_free()

	await runner.get_tree().process_frame

	# 2. Headshot Decapitation + BloodDecal + GibChunks
	var z_hs := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_hs.setup("soldier", 180.0, 2.0, null)
	world.add_child(z_hs)
	z_hs.global_position = Vector3(1.5, 0.0, 1.5)
	await runner.get_tree().process_frame
	z_hs.set_physics_process(false)
	var pre_pts := GameManager.points
	var died_hs := z_hs.take_damage(400.0, true, z_hs.head_area.global_position, Vector3.FORWARD)
	await runner.get_tree().process_frame
	_check(runner, died_hs and z_hs.is_head_popped, "Chars: headshot kill triggers is_head_popped")
	_check(runner, z_hs._mesh_head != null and not z_hs._mesh_head.visible and z_hs._stump_head != null and z_hs._stump_head.visible, "Chars: head-pop hides Mesh_Head and exposes Stump_Head")
	_check(runner, GameManager.points == pre_pts + 100, "Chars: headshot kill awards +100 points")

	var gib_count := 0
	var decal_count := 0
	for c in world.get_children():
		if c is GibChunk:
			gib_count += 1
		elif c is BloodDecal:
			decal_count += 1
	_check(runner, gib_count >= 3 and decal_count >= 1, "Chars: decapitation spawns GibChunks (%d) & BloodDecal (%d)" % [gib_count, decal_count])
	z_hs.queue_free()

	# 3. Heavy Arm Sever + Leg Hit Crawler Transition
	var z_dism := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z_dism.setup("worker", 400.0, 2.6, null)
	world.add_child(z_dism)
	z_dism.global_position = Vector3(-1.5, 0.0, 1.5)
	await runner.get_tree().process_frame
	z_dism.set_physics_process(false)

	var arm_l_world := z_dism._skeleton.to_global(z_dism._skeleton.get_bone_global_pose(z_dism._arm_l_bone_idx).origin)
	var killed_arm := z_dism.take_damage(65.0, false, arm_l_world, Vector3.RIGHT)
	_check(runner, not killed_arm and z_dism.is_arm_l_severed, "Chars: heavy left-arm hit severs Mesh_Arm_L")
	_check(runner, z_dism._mesh_arm_l != null and not z_dism._mesh_arm_l.visible and z_dism._stump_arm_l != null and z_dism._stump_arm_l.visible, "Chars: severed arm exposes Stump_Arm_L")

	var leg_world := z_dism.global_position + Vector3(0.1, 0.42, 0.0)
	var killed_leg := z_dism.take_damage(80.0, false, leg_world, Vector3.BACK)
	await runner.get_tree().process_frame
	_check(runner, not killed_leg and z_dism.is_crawler and z_dism._current_anim == "Crawl", "Chars: heavy leg hit converts upright zombie into Crawler")
	_check(runner, z_dism._mesh_legs != null and not z_dism._mesh_legs.visible and z_dism._stump_legs != null and z_dism._stump_legs.visible, "Chars: crawler transition hides Mesh_Legs & exposes Stump_Legs")
	z_dism.queue_free()

	# 4. Overhauled Hellhound Verification
	var hound := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	world.add_child(hound)
	hound.setup(180.0)
	hound.global_position = Vector3(2.5, 0.0, -2.0)
	await runner.get_tree().process_frame
	hound.set_physics_process(false)
	_check(runner, hound.model_root.find_child("Hellhound_Armature", true, false) != null, "Chars: Hellhound loads Hellhound_Armature")
	_check(runner, hound._anim_player != null and hound._anim_player.has_animation("Run") and hound._anim_player.has_animation("Attack") and hound._anim_player.has_animation("Death"), "Chars: Hellhound has Run/Attack/Death animations")
	_check(runner, hound.ember_trail != null and hound.ember_trail.emitting, "Chars: Hellhound EmberTrail emits on spawn")
	var hound_died_sig := [false]
	hound.died.connect(func(_e, _hs, _p, _fd): hound_died_sig[0] = true)
	hound.kill_by_nuke()
	_check(runner, hound.is_dead and hound_died_sig[0], "Chars: Hellhound nuke emits died and disables cleanly")
	hound.queue_free()

	# 5. RoundDirector Panzer Boss Cadence & Boss Armor/Flamethrower/Drops
	if rd != null:
		_check(runner, rd.is_panzer_round(8) and rd.is_panzer_round(16) and not rd.is_panzer_round(5) and not rd.is_panzer_round(40), "Chars: Panzer Boss spawns every 8th non-dog round (R8/R16 yes, R5/R40 no)")

	var boss := rd.spawn_panzer_boss(8, Vector3(0.0, 0.0, -3.5))
	await runner.get_tree().process_frame
	_check(runner, boss != null and is_equal_approx(boss.max_hp, 1400.0), "Chars: RoundDirector spawns PanzerBossAI with 1400 HP at Round 8")
	_check(runner, boss.model_root.find_child("Panzer_boss_Armature", true, false) != null and boss._head_bone_idx >= 0, "Chars: Panzer Boss loads Panzer_boss_Armature & Head bone")
	_check(runner, boss.get_intact_plates().size() == 4, "Chars: Panzer Boss starts with 4 breakable armor plates")
	for panim in ["Idle", "Walk", "Run", "Attack", "FlameAttack", "Hit", "Death"]:
		_check(runner, boss._anim_player != null and boss._anim_player.has_animation(panim), "Chars: Panzer Boss has animation '%s'" % panim)

	# Test visor plate armor mitigation then shatter -> critical weakpoint damage
	var hp_before := boss.hp
	boss.take_damage(200.0, true, boss.head_area.global_position, Vector3.FORWARD)
	var dmg_armored := hp_before - boss.hp
	_check(runner, dmg_armored < 100.0 and boss.is_plate_intact("visor"), "Chars: intact visor plate absorbs majority of headshot damage (%.1f < 100)" % dmg_armored)

	# Break visor plate cleanly
	boss.take_damage(120.0, true, boss.head_area.global_position, Vector3.FORWARD)
	await runner.get_tree().process_frame
	var visor_node := boss._plate_nodes.get("visor", null) as Node3D
	_check(runner, not boss.is_plate_intact("visor") and visor_node != null and not visor_node.visible, "Chars: shattering visor hides Helmet_VisorPlate")

	var hp_exposed_before := boss.hp
	boss.take_damage(100.0, true, boss.head_area.global_position, Vector3.FORWARD)
	var dmg_exposed := hp_exposed_before - boss.hp
	_check(runner, dmg_exposed > 150.0, "Chars: exposed visor weakpoint deals critical bonus damage (%.1f > 150)" % dmg_exposed)

	# Break chest plate cleanly
	boss.take_damage(400.0, false, boss.global_position + Vector3(0, 1.4, 0.2), Vector3.FORWARD)
	var chest_node := boss._plate_nodes.get("chest", null) as Node3D
	_check(runner, not boss.is_plate_intact("chest") and chest_node != null and not chest_node.visible, "Chars: shattering chest armor hides ArmorPlate_Chest")

	# Verify Flamethrower particles & light toggle cleanly
	boss._set_flamethrower_active(true)
	_check(runner, boss.flame_particles.emitting and boss.flame_light.light_energy > 0.5, "Chars: Panzer Flamethrower activates particles & flame light")
	boss._set_flamethrower_active(false)

	# Kill Panzer Boss -> awards +1500 pts & drops guaranteed Max Ammo!
	var pts_pre_boss := GameManager.points
	var boss_killed := boss.take_damage(5000.0, true, boss.head_area.global_position, Vector3.FORWARD)
	await runner.get_tree().process_frame
	_check(runner, boss_killed and boss.is_dead, "Chars: Panzer Boss dies cleanly on lethal damage")
	_check(runner, GameManager.points == pts_pre_boss + 1500, "Chars: Panzer Boss kill awards +1500 bonus points")

	var dropped_max_ammo := false
	for ch in world.get_children():
		if ch is PowerUpDrop and ch.kind == "max_ammo":
			dropped_max_ammo = true
			break
	_check(runner, dropped_max_ammo, "Chars: Panzer Boss death guarantees Max Ammo PowerUpDrop")

	world.queue_free()
	await runner.get_tree().process_frame
	await runner.get_tree().process_frame
	GameManager.reset_match()


static func _check(runner: Node, cond: bool, msg: String) -> void:
	runner.call("_check", cond, msg)

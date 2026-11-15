extends Node

var out_dir: String = OS.get_environment("BUNKER_SHOT_DIR") if OS.has_environment("BUNKER_SHOT_DIR") else "/tmp/bunker_shots_mach"


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
	rd.set_process(false)
	player.set_physics_process(false)
	await _wait_frames(3)

	# Activate Power & open all doors so interior lights and machines shine cleanly
	GameManager.add_points(50000, "")
	(world.get_node("Interactables/PowerSwitch") as PowerSwitch).interact(player)
	(world.get_node("Interactables/DoorSpawnEast") as BuyableDoor).interact(player)
	(world.get_node("Interactables/DoorSpawnWest") as BuyableDoor).interact(player)
	(world.get_node("Interactables/DoorEastReactor") as BuyableDoor).interact(player)
	(world.get_node("Interactables/DoorReactorNorth") as BuyableDoor).interact(player)
	for pl in world._power_lights:
		pl.light_energy = float(pl.get_meta("target_energy", 2.6))

	var wf := world.get_node("WorldFeatures")
	var wunderfizz := wf.get_node("WunderfizzMachine") as WunderfizzMachine
	var deadshot := wf.get_node("PerkDeadshot") as PerkMachine
	var phd := wf.get_node("PerkPhDFlopper") as PerkMachine
	var mule := wf.get_node("PerkMuleKick") as PerkMachine
	var cherry := wf.get_node("PerkElectricCherry") as PerkMachine
	var fire_trap := wf.get_node("FireTrap") as FireTrap
	var quest := wf.get_node("EasterEggQuest") as EasterEggQuest
	var canister2 := wf.get_node("QuestCanister2") as QuestCanister
	var resonator3 := wf.get_node("QuestResonator3") as QuestResonator
	var resonator1 := wf.get_node("QuestResonator1") as QuestResonator
	var teddy2 := wf.get_node("SongTeddy2") as SongTeddy

	# Give Wunderwaffe DG-2 and grant all 9 perks for HUD verification
	player.give_weapon("wunderwaffe")
	for pid in ["quickrevive", "juggernog", "speedcola", "doubletap", "staminup", "mulekick", "deadshot", "phdflopper", "electriccherry"]:
		GameManager.grant_perk(pid)

	# 1. Shot 1: Der Wunderfizz spinning/dispensing glowing perk bottle in Reactor Hall
	wunderfizz._chosen_perk = "electriccherry"
	wunderfizz._finish_spin()
	_place_and_aim(player, Vector3(9.2, 0.05, -13.0), Vector3(9.2, 1.32, -9.0))
	_clear_hud_deltas(world)
	await _wait_frames(4)
	await _save_shot("shot_1_wunderfizz.png")

	# 2. Shot 2: Deadshot Daiquiri close-up (scope topper, marquee, all 9 perk icons on HUD)
	_place_and_aim(player, Vector3(-19.5, 0.05, -12.6), Vector3(-20.2, 1.38, -9.0))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_2_deadshot_9perks.png")

	# 3. Shot 3: PhD Flopper close-up in North Yard West (mushroom cloud + orbital atom rings)
	_place_and_aim(player, Vector3(-7.4, 0.05, -30.5), Vector3(-10.9, 1.45, -30.2))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_3_phd_flopper.png")

	# 4. Shot 4: Mule Kick (North Yard East) & Electric Cherry (Shot 5)
	_place_and_aim(player, Vector3(19.2, 0.05, -31.0), Vector3(22.9, 1.38, -30.5))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_4_mule_kick.png")

	_place_and_aim(player, Vector3(5.6, 0.05, -32.6), Vector3(5.2, 1.38, -29.0))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_5_electric_cherry.png")

	# 6. Shot 6: Fire Trap Active (Console w/ CC0 Propane Tank + pulled lever + 6.2m Flame Curtain & Grate)
	fire_trap.set_trap_active(true, true)
	fire_trap.flame_particles.preprocess = 0.8
	_place_and_aim(player, Vector3(16.6, 0.05, -20.6), Vector3(17.1, 1.05, -26.2))
	_clear_hud_deltas(world)
	await _wait_frames(4)
	await _save_shot("shot_6_fire_trap_active.png")
	fire_trap.set_trap_active(false, true)

	# 7. Shot 7: Quest Terminal (CRT oscilloscope, CC0 Retro Multimeter, StatusBeacon)
	quest.interact(player) # auto advances 0->1->2 because power is already on
	_place_and_aim(player, Vector3(13.6, 0.05, -37.2), Vector3(14.5, 1.15, -40.2))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_7_quest_terminal.png")

	# 8. Shot 8: Quest Canister filling + Quest Resonator pylon glowing
	canister2.set_active(true)
	canister2.add_soul()
	canister2.add_soul()
	canister2.add_soul()
	resonator3.set_active(true)
	resonator3.trigger_quest_hit()
	_place_and_aim(player, Vector3(1.5, 0.05, -35.6), Vector3(2.8, 1.55, -39.9))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_8_canister_resonator.png")

	# 9. Shot 9: West Lab Song Teddy on Desk + Lab Pod Resonator
	resonator1.set_active(true)
	_place_and_aim(player, Vector3(-14.6, 0.05, -3.9), Vector3(-12.2, 0.96, -5.35))
	_clear_hud_deltas(world)
	await _wait_frames(3)
	await _save_shot("shot_9_west_lab_teddy.png")

	print("CAPTURED 9 STREAM D VERIFICATION SCREENSHOTS IN ", out_dir)
	world.queue_free()
	await _wait_frames(2)
	get_tree().quit(0)


func _place_and_aim(player: PlayerController, pos: Vector3, target_pos: Vector3) -> void:
	player.global_position = pos
	var eye := pos + Vector3(0.0, player.head.position.y, 0.0)
	var diff := target_pos - eye
	var horiz_len := maxf(0.001, Vector2(diff.x, diff.z).length())
	player.rotation = Vector3(0.0, atan2(-diff.x, -diff.z), 0.0)
	player.head.rotation = Vector3(atan2(diff.y, horiz_len), 0.0, 0.0)
	player.camera.rotation = Vector3.ZERO
	player.weapon_ctrl.snap_viewmodel()


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

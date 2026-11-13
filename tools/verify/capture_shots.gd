extends Node

const OUT_DIR := "/tmp/zombieshooter_shots"


func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(1280, 720)
	DirAccess.make_dir_recursive_absolute(OUT_DIR)
	await _wait_frames(2)

	# 1. Capture Main Menu 3D scene
	GameManager.reset_match()
	var menu := (load("res://scenes/main_menu.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(menu)
	await _wait_frames(3)
	await _save_shot("shot_1_main_menu.png")
	menu.queue_free()
	await _wait_frames(2)

	# 2. Load Bunker 115 GameWorld
	GameManager.reset_match()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(world)
	await _wait_frames(3)

	var player := world.get_node("Player") as PlayerController
	var rd := world.get_node("RoundDirector") as RoundDirector
	rd.set_process(false)

	# Shot 2: Spawn Courtyard default first-person view (looking at Tank + Crystals + Quick Revive + M1911)
	player.global_position = Vector3(1.2, 0.05, 6.2)
	player.rotation_degrees = Vector3(0, 12, 0)
	player.head.rotation_degrees = Vector3(-4, 0, 0)
	player.weapon_ctrl.snap_viewmodel()
	await _wait_frames(3)
	await _save_shot("shot_2_spawn_courtyard.png")

	# Shot 3: Combat view with Soldier, Scientist, Brute, Hellhound & PowerUp Drop + Ray Gun!
	GameManager.add_points(25000, "")
	player.give_weapon("raygun")
	player.weapon_ctrl.snap_viewmodel()
	_clear_hud_deltas(world)
	player.global_position = Vector3(4.5, 0.05, 6.0)
	player.rotation_degrees = Vector3(0, 26, 0)
	player.head.rotation_degrees = Vector3(-3, 0, 0)

	var zs := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	zs.setup("soldier", 150.0, 2.0, null)
	world.add_child(zs)
	zs.global_position = Vector3(1.8, 0.0, 1.6)
	zs.set_physics_process(false)
	zs.rotation_degrees.y = -150.0

	var zsc := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	zsc.setup("scientist", 150.0, 2.0, null)
	world.add_child(zsc)
	zsc.global_position = Vector3(3.7, 0.0, 2.2)
	zsc.set_physics_process(false)
	zsc.rotation_degrees.y = -160.0

	var zb := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	zb.setup("brute", 450.0, 1.8, null)
	world.add_child(zb)
	zb.global_position = Vector3(0.0, 0.0, 1.2)
	zb.set_physics_process(false)
	zb.rotation_degrees.y = -135.0

	var hh := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	world.add_child(hh)
	hh.global_position = Vector3(3.15, 0.0, 3.35)
	hh.setup(180.0)
	hh.set_physics_process(false)
	hh.rotation_degrees.y = -112.0

	var pu := (load("res://scenes/interactables/power_up.tscn") as PackedScene).instantiate() as PowerUpDrop
	world.add_child(pu)
	pu.global_position = Vector3(2.3, 0.0, 3.6)
	pu.setup("insta_kill")
	pu.model_holder.rotation.y = 0.0

	for znode in [zs, zsc, zb, hh]:
		var zap := znode.get("_anim_player") as AnimationPlayer
		if zap:
			zap.advance(0.25)

	await _wait_frames(3)
	await _save_shot("shot_3_combat_zombies.png")

	for n in [zs, zsc, zb, hh, pu]:
		n.queue_free()
	await _wait_frames(2)

	# Turn Power On + unlock doors for interior showcase
	(world.get_node("Interactables/PowerSwitch") as PowerSwitch).interact(player)
	(world.get_node("Interactables/DoorSpawnEast") as BuyableDoor).interact(player)
	(world.get_node("Interactables/DoorSpawnWest") as BuyableDoor).interact(player)
	(world.get_node("Interactables/PerkJuggernog") as PerkMachine).interact(player)
	(world.get_node("Interactables/PerkDoubleTap") as PerkMachine).interact(player)
	# Immediately complete power light tweens
	for pl in world._power_lights:
		pl.light_energy = float(pl.get_meta("target_energy", 2.6))

	# Shot 4: East Courtyard (Mystery Box + Electro Trap + Double Tap sightline + STG-44)
	(world.get_node("Interactables/ElectroTrap") as ElectroTrap).interact(player)
	player.give_weapon("stg44")
	player.weapon_ctrl.snap_viewmodel()
	_clear_hud_deltas(world)
	player.global_position = Vector3(19.2, 0.05, 0.6)
	player.rotation_degrees = Vector3(0, 44, 0)
	player.head.rotation_degrees = Vector3(-4, 0, 0)
	await _wait_frames(3)
	await _save_shot("shot_4_east_electro_box.png")

	# Shot 5: West Research Lab (Lab Pods + Element 115 + Speed Cola + MP40)
	(world.get_node("Interactables/PerkSpeedCola") as PerkMachine).interact(player)
	player.give_weapon("mp40")
	player.weapon_ctrl.snap_viewmodel()
	_clear_hud_deltas(world)
	player.global_position = Vector3(-11.5, 0.05, 4.2)
	player.rotation_degrees = Vector3(0, 48, 0)
	player.head.rotation_degrees = Vector3(-2, 0, 0)
	await _wait_frames(3)
	await _save_shot("shot_5_west_lab.png")

	# Shot 6: Reactor Hall (Pack-a-Punch Machine + PaP Runic Camo M14 + Power Switch + Teleporter)
	player.give_weapon("m14")
	(world.get_node("Interactables/PackAPunch") as PackAPunch).interact(player)
	player.weapon_ctrl.snap_viewmodel()
	_clear_hud_deltas(world)
	player.global_position = Vector3(1.5, 0.05, -14.0)
	player.rotation_degrees = Vector3(0, 14, 0)
	player.head.rotation_degrees = Vector3(-2, 0, 0)
	await _wait_frames(3)
	await _save_shot("shot_6_reactor_pap.png")

	print("CAPTURED 6 VERIFICATION SCREENSHOTS IN ", OUT_DIR)
	world.queue_free()
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
	img.save_png(OUT_DIR.path_join(filename))
	print("Saved: ", OUT_DIR.path_join(filename))

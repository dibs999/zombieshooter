extends Node

var out_dir: String = OS.get_environment("BUNKER_ENV_SHOT_DIR") if OS.has_environment("BUNKER_ENV_SHOT_DIR") else "/tmp/bunker_shots_env_extra"


func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(1280, 720)
	DirAccess.make_dir_recursive_absolute(out_dir)
	await _wait_frames(2)

	GameManager.reset_match()
	var packed := load("res://scenes/game_world.tscn") as PackedScene
	if packed == null:
		push_error("Failed to load res://scenes/game_world.tscn")
		get_tree().quit(1)
		return
	var world := packed.instantiate() as GameWorld
	if world == null:
		push_error("Failed to instantiate GameWorld")
		get_tree().quit(1)
		return
	get_tree().root.add_child(world)
	await _wait_frames(3)

	var player := world.get_node_or_null("Player") as PlayerController
	var rd := world.get_node_or_null("RoundDirector") as RoundDirector
	if rd:
		rd.set_process(false)
	if player:
		player.set_physics_process(false)
		player.visible = false
	var hud := world.get_node_or_null("HUD") as Control
	if hud:
		hud.visible = false

	# Power on & unlock doors for inspection
	GameManager.add_points(50000, "")
	if player:
		(world.get_node("Interactables/PowerSwitch") as PowerSwitch).interact(player)
		(world.get_node("Interactables/DoorSpawnWest") as BuyableDoor).interact(player)
		(world.get_node("Interactables/DoorSpawnEast") as BuyableDoor).interact(player)
		(world.get_node("Interactables/DoorReactorNorth") as BuyableDoor).interact(player)
	for pl in world._power_lights:
		pl.light_energy = float(pl.get_meta("target_energy", 2.8))

	var cam := Camera3D.new()
	cam.fov = 68.0
	world.add_child(cam)
	cam.make_current()

	# 1. Zone 5 North Yard Wide Overview (looking SW across covered car, street lamps, barriers, garage & sky)
	cam.look_at_from_position(Vector3(16.5, 3.6, -26.5), Vector3(0.5, 0.9, -36.5), Vector3.UP)
	await _wait_frames(3)
	await _save_shot("env_1_north_yard_overview.png")

	# 2. DoorReactorNorth Bulkhead & Garage Bay + FeatureSlots
	cam.look_at_from_position(Vector3(10.5, 2.2, -37.5), Vector3(17.5, 1.4, -24.0), Vector3.UP)
	await _wait_frames(3)
	await _save_shot("env_2_north_yard_garage.png")

	# 3. West Lab Desk, Chemistry Set, Bunsen Burner & Radio Detail
	cam.look_at_from_position(Vector3(-18.2, 2.1, -1.5), Vector3(-22.2, 0.9, 2.2), Vector3.UP)
	await _wait_frames(3)
	await _save_shot("env_3_lab_bench_detail.png")

	# 4. Reactor Hall Power Switch, PaP, Sparking Power Boxes & Lab Pods
	cam.look_at_from_position(Vector3(3.5, 2.4, -12.2), Vector3(-2.5, 1.4, -21.2), Vector3.UP)
	await _wait_frames(3)
	await _save_shot("env_4_reactor_power_wall.png")

	# 5. Spawn Courtyard High Angle (Tank, Embers, Cobbles, Barriers, Moonlit Ruined Story)
	cam.look_at_from_position(Vector3(7.2, 3.5, 7.6), Vector3(-2.8, 1.2, -3.5), Vector3.UP)
	await _wait_frames(3)
	await _save_shot("env_5_spawn_courtyard_detail.png")

	# 6. East Foundry Welding Cart, Tool Cabinet, Metal Floor & Vent Fan
	cam.look_at_from_position(Vector3(14.5, 2.3, 4.8), Vector3(22.2, 1.2, -2.5), Vector3.UP)
	await _wait_frames(3)
	await _save_shot("env_6_east_foundry_detail.png")

	print("CAPTURED 6 EXTRA ENVIRONMENT SHOTS IN ", out_dir)
	world.queue_free()
	await _wait_frames(2)
	get_tree().quit(0)


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

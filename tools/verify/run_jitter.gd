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
	get_tree().create_timer(30.0).timeout.connect(func():
		printerr("TIMEOUT in run_jitter.gd!")
		get_tree().quit(1)
	)
	print("=== BUNKER 115 JITTER VERIFICATION SUITE ===")
	await get_tree().process_frame

	TestsJitter.run_checks(self)
	await _test_live_game_world()

	print("==============================================")
	print("JITTER SUITE RESULTS: %d passed, %d failed" % [_passed, _failed])
	get_tree().quit(1 if _failed > 0 else 0)


func _test_live_game_world() -> void:
	print("[Jitter Live] Testing Player + WeaponController inside GameWorld...")
	GameManager.reset_match()
	var world_scene := load("res://scenes/game_world.tscn") as PackedScene
	_check(world_scene != null, "Live GameWorld: scene loaded")
	if world_scene == null:
		return
	var world := world_scene.instantiate()
	get_tree().root.add_child(world)
	var rd := world.get_node_or_null("RoundDirector") as RoundDirector
	if rd:
		rd.set_process(false)
	await get_tree().process_frame
	for _p in range(4):
		await get_tree().physics_frame

	var player := world.get_node_or_null("Player") as PlayerController
	_check(player != null and player.weapon_ctrl != null, "Live GameWorld: Player & WeaponController loaded")
	if player == null or player.weapon_ctrl == null:
		world.queue_free()
		return

	var wc := player.weapon_ctrl
	_check(player.is_on_floor(), "Live GameWorld: Player rests on floor cleanly")
	var hip_pos: Vector3 = WeaponDB.get_stat(wc.get_current_state(), "hip_pos")
	_check(wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001, "Live GameWorld: Viewmodel starts snapped at hip_pos")

	# Simulate real forward walking + noisy mouse look in GameWorld
	Input.action_press("move_forward")
	var max_live_vm_step := 0.0
	var max_live_cam_step := 0.0
	var prev_vm := wc.viewmodel_pivot.position
	var prev_cam := player.camera.position
	for i in range(25):
		var mm := InputEventMouseMotion.new()
		mm.relative = Vector2(8.0 if i % 2 == 0 else 2.0, -3.0)
		player._unhandled_input(mm)
		await get_tree().process_frame
		max_live_vm_step = maxf(max_live_vm_step, wc.viewmodel_pivot.position.distance_to(prev_vm))
		max_live_cam_step = maxf(max_live_cam_step, player.camera.position.distance_to(prev_cam))
		prev_vm = wc.viewmodel_pivot.position
		prev_cam = player.camera.position
	Input.action_release("move_forward")
	_check(player.velocity.length() > 1.0, "Live GameWorld: Player accelerates smoothly")
	_check(max_live_vm_step < 0.025 and max_live_cam_step < 0.015, "Live GameWorld: Walk + mouse sway motion stays bounded/smooth (vm=%.5f, cam=%.5f)" % [max_live_vm_step, max_live_cam_step])

	# Wait for settle back to idle
	for _i in range(60):
		await get_tree().physics_frame
		await get_tree().process_frame
	_check(wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.002 and player.camera.position.length() < 0.002, "Live GameWorld: Weapon & camera settle back to idle smoothly (vm_err=%.5f, cam_err=%.5f)" % [wc.viewmodel_pivot.position.distance_to(hip_pos), player.camera.position.length()])

	world.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame

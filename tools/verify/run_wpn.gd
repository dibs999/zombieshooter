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
	get_tree().create_timer(45.0).timeout.connect(func():
		printerr("TIMEOUT in run_wpn.gd!")
		get_tree().quit(1)
	)
	print("=== BUNKER 115 STREAM C WEAPONS & HUD VERIFICATION ===")
	await get_tree().process_frame
	await TestsWpn.run_checks(self)
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
	await get_tree().create_timer(0.08).timeout
	await get_tree().process_frame
	print("==============================================")
	print("WPN SUITE RESULTS: %d passed, %d failed" % [_passed, _failed])
	get_tree().quit(1 if _failed > 0 else 0)

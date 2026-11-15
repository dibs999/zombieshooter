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
	print("=== BUNKER 115 STREAM D (MACHINES/QUEST) VERIFICATION ===")
	await get_tree().process_frame
	await TestsMach.run_checks(self)
	print("=========================================================")
	print("MACH RESULTS: %d passed, %d failed" % [_passed, _failed])
	get_tree().quit(1 if _failed > 0 else 0)

extends Node

# Verify CoD-styled game-over & pause menu visuals
func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(1280, 720)
	await _wait(3)
	GameManager.reset_match()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(world)
	await _wait(6)

	# Shot A: game over screen over the frozen world
	GameManager.trigger_game_over()
	await _wait(6)
	get_viewport().get_texture().get_image().save_png("/tmp/ui_gameover.png")
	print("saved gameover")

	# Shot B: pause menu instead
	var go := get_tree().root.find_child("GameOverScreen", true, false)
	if go:
		go.visible = false
	GameManager.is_game_over = false
	get_tree().paused = true
	var pm := get_tree().root.find_child("PauseMenu", true, false)
	if pm:
		pm.visible = true
	await _wait(5)
	get_viewport().get_texture().get_image().save_png("/tmp/ui_pause.png")
	print("saved pause")
	get_tree().quit()

func _wait(n: int) -> void:
	for i in n:
		await get_tree().process_frame

extends Node

func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(960, 540)
	await _wait(2)
	var menu := (load("res://scenes/main_menu.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(menu)
	await _wait(6)
	_save("/tmp/menu_shot.png")
	get_tree().quit()

func _wait(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _save(path: String) -> void:
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("saved ", path)

extends CanvasLayer

@onready var title_lbl: Label = $Panel/VBox/TitleLabel
@onready var stats_lbl: Label = $Panel/VBox/StatsLabel


func _ready() -> void:
	visible = false
	GameManager.game_over_triggered.connect(_on_game_over)


func _on_game_over(stats: Dictionary) -> void:
	visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var rounds := int(stats.get("rounds_survived", 1))
	title_lbl.text = "GAME OVER\nYOU SURVIVED %d ROUND%s" % [rounds, "" if rounds == 1 else "S"]
	stats_lbl.text = (
		"Kills: %d   |   Headshots: %d\n" % [int(stats.get("kills", 0)), int(stats.get("headshots", 0))] +
		"Total Points Earned: %d\n" % int(stats.get("total_points", 0)) +
		"Doors Opened: %d   |   Pack-a-Punch Upgrades: %d\n" % [int(stats.get("doors_opened", 0)), int(stats.get("pap_upgrades", 0))] +
		"Barriers Repaired: %d" % int(stats.get("barriers_repaired", 0))
	)


func _on_restart_pressed() -> void:
	GameManager.reset_match()
	get_tree().reload_current_scene()


func _on_menu_pressed() -> void:
	GameManager.reset_match()
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

extends CanvasLayer

@onready var title_lbl: Label = $Panel/VBox/TitleLabel
@onready var stats_lbl: Label = $Panel/VBox/StatsLabel


func _ready() -> void:
	visible = false
	GameManager.game_over_triggered.connect(_on_game_over)
	_apply_cod_style()


func _apply_cod_style() -> void:
	CodUiStyle.dark_panel(get_node_or_null("Panel") as PanelContainer, 0.55)
	CodUiStyle.style_title(title_lbl, 40, Color(0.80, 0.15, 0.11))
	var tw := CodUiStyle.typewriter_font()
	if tw:
		stats_lbl.add_theme_font_override("font", tw)
	stats_lbl.add_theme_color_override("font_color", CodUiStyle.BONE)
	CodUiStyle.style_buttons(get_node("Panel") as Control)


func _on_game_over(stats: Dictionary) -> void:
	visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var rounds := int(stats.get("rounds_survived", 1))
	title_lbl.text = "GAME OVER\nYOU SURVIVED %d ROUND%s" % [rounds, "" if rounds == 1 else "S"]
	var ee_done := bool(stats.get("easter_egg_completed", false))
	var ee_step := int(stats.get("quest_step", 0))
	var ee_str := "COMPLETED" if ee_done else ("Step %d/5" % ee_step if ee_step > 0 else "Incomplete")
	stats_lbl.text = (
		"Kills: %d   |   Headshots: %d\n" % [int(stats.get("kills", 0)), int(stats.get("headshots", 0))] +
		"Total Points Earned: %d\n" % int(stats.get("total_points", 0)) +
		"Doors Opened: %d   |   Pack-a-Punch Upgrades: %d\n" % [int(stats.get("doors_opened", 0)), int(stats.get("pap_upgrades", 0))] +
		"Barriers Repaired: %d\n" % int(stats.get("barriers_repaired", 0)) +
		"Perks: %d / %d   |   Easter Egg: %s" % [GameManager.perks.size(), GameManager.max_perks, ee_str]
	)


func _on_restart_pressed() -> void:
	GameManager.reset_match()
	get_tree().reload_current_scene()


func _on_menu_pressed() -> void:
	GameManager.reset_match()
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

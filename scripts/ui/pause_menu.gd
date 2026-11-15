extends CanvasLayer

@onready var root: Control = $Root
@onready var main_panel: VBoxContainer = $Root/Panel/VBox/MainButtons
@onready var settings_panel: VBoxContainer = $Root/Panel/VBox/SettingsBox
@onready var status_label: Label = $Root/Panel/VBox/StatusLabel
@onready var sens_slider: HSlider = $Root/Panel/VBox/SettingsBox/SensSlider
@onready var fov_slider: HSlider = $Root/Panel/VBox/SettingsBox/FOVSlider
@onready var vol_slider: HSlider = $Root/Panel/VBox/SettingsBox/VolSlider
@onready var gfx_btn: OptionButton = $Root/Panel/VBox/SettingsBox/GfxOption
@onready var invert_chk: CheckBox = $Root/Panel/VBox/SettingsBox/InvertCheck


func _ready() -> void:
	visible = false
	settings_panel.visible = false
	gfx_btn.clear()
	gfx_btn.add_item("High")
	gfx_btn.add_item("Medium")
	gfx_btn.add_item("Low")
	_sync_ui()


func _sync_ui() -> void:
	sens_slider.value = SettingsManager.mouse_sensitivity * 1000.0
	fov_slider.value = SettingsManager.fov
	vol_slider.value = SettingsManager.master_volume * 100.0
	invert_chk.button_pressed = SettingsManager.invert_y
	var idx := ["High", "Medium", "Low"].find(SettingsManager.graphics_quality)
	gfx_btn.selected = maxi(0, idx)
	_refresh_status()


func _refresh_status() -> void:
	if status_label == null:
		return
	var q_text := "Inactive (Motorpool Terminal)"
	if GameManager.quest_completed:
		q_text = "Operation Element 115 COMPLETE"
	elif GameManager.quest_step > 0:
		q_text = "Step %d: %s" % [GameManager.quest_step, GameManager.quest_description]
	status_label.text = "Perks: %d / %d\nEaster Egg: %s" % [
		GameManager.perks.size(),
		GameManager.max_perks,
		q_text,
	]


func _unhandled_input(event: InputEvent) -> void:
	if GameManager.is_game_over:
		return
	if event.is_action_pressed("pause"):
		toggle_pause()


func toggle_pause() -> void:
	var next_paused := not get_tree().paused
	get_tree().paused = next_paused
	visible = next_paused
	main_panel.visible = true
	settings_panel.visible = false
	if next_paused:
		_refresh_status()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if next_paused else Input.MOUSE_MODE_CAPTURED


func _on_resume_pressed() -> void:
	toggle_pause()


func _on_restart_pressed() -> void:
	get_tree().paused = false
	GameManager.reset_match()
	get_tree().reload_current_scene()


func _on_settings_pressed() -> void:
	_sync_ui()
	main_panel.visible = false
	settings_panel.visible = true


func _on_back_settings_pressed() -> void:
	settings_panel.visible = false
	main_panel.visible = true


func _on_quit_menu_pressed() -> void:
	get_tree().paused = false
	AudioManager.stop_ambience()
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")


func _on_sens_changed(val: float) -> void:
	SettingsManager.set_mouse_sensitivity(val / 1000.0)


func _on_fov_changed(val: float) -> void:
	SettingsManager.set_fov(val)


func _on_vol_changed(val: float) -> void:
	SettingsManager.set_master_volume(val / 100.0)


func _on_gfx_selected(idx: int) -> void:
	SettingsManager.set_graphics_quality(["High", "Medium", "Low"][idx])


func _on_invert_toggled(on: bool) -> void:
	SettingsManager.set_invert_y(on)

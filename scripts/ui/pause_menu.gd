extends CanvasLayer

@onready var root: Control = $Root
@onready var main_panel: VBoxContainer = $Root/Panel/VBox/MainButtons
@onready var settings_panel: VBoxContainer = $Root/Panel/VBox/SettingsBox
@onready var status_label: Label = $Root/Panel/VBox/StatusLabel
@onready var sens_slider: HSlider = $Root/Panel/VBox/SettingsBox/SensSlider
@onready var fov_slider: HSlider = $Root/Panel/VBox/SettingsBox/FOVSlider
@onready var vol_slider: HSlider = $Root/Panel/VBox/SettingsBox/VolSlider
@onready var gfx_btn: OptionButton = $Root/Panel/VBox/SettingsBox/GfxOption
@onready var scale_label: Label = $Root/Panel/VBox/SettingsBox/ScaleLabel
@onready var scale_slider: HSlider = $Root/Panel/VBox/SettingsBox/ScaleSlider
@onready var msaa_btn: OptionButton = $Root/Panel/VBox/SettingsBox/MSAAOption
@onready var invert_chk: CheckBox = $Root/Panel/VBox/SettingsBox/InvertCheck
@onready var vsync_chk: CheckBox = $Root/Panel/VBox/SettingsBox/VSyncCheck


func _ready() -> void:
	visible = false
	settings_panel.visible = false
	gfx_btn.clear()
	gfx_btn.add_item("High")
	gfx_btn.add_item("Medium")
	gfx_btn.add_item("Low")
	msaa_btn.clear()
	msaa_btn.add_item("Off")
	msaa_btn.add_item("2x")
	msaa_btn.add_item("4x")
	_sync_ui()
	_apply_cod_style()


func _apply_cod_style() -> void:
	CodUiStyle.dark_panel(get_node_or_null("Root/Panel") as PanelContainer, 0.55)
	CodUiStyle.style_title(get_node_or_null("Root/Panel/VBox/Title") as Label, 34)
	CodUiStyle.style_buttons(root)
	CodUiStyle.style_labels(root, [get_node_or_null("Root/Panel/VBox/Title") as Label])


func _sync_ui() -> void:
	sens_slider.set_value_no_signal(SettingsManager.mouse_sensitivity * 1000.0)
	fov_slider.set_value_no_signal(SettingsManager.fov)
	vol_slider.set_value_no_signal(SettingsManager.master_volume * 100.0)
	scale_slider.set_value_no_signal(SettingsManager.render_scale)
	scale_label.text = "Render Scale (FSR): %d%%" % int(round(SettingsManager.render_scale * 100.0))
	invert_chk.set_pressed_no_signal(SettingsManager.invert_y)
	vsync_chk.set_pressed_no_signal(SettingsManager.vsync_enabled)
	var idx := ["High", "Medium", "Low"].find(SettingsManager.graphics_quality)
	gfx_btn.selected = maxi(0, idx)
	var msaa_idx := ["Off", "2x", "4x"].find(SettingsManager.msaa_mode)
	msaa_btn.selected = maxi(0, msaa_idx)
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


func _on_scale_changed(val: float) -> void:
	SettingsManager.set_render_scale(val)
	scale_label.text = "Render Scale (FSR): %d%%" % int(round(SettingsManager.render_scale * 100.0))


func _on_msaa_selected(idx: int) -> void:
	SettingsManager.set_msaa_mode(["Off", "2x", "4x"][idx])


func _on_invert_toggled(on: bool) -> void:
	SettingsManager.set_invert_y(on)


func _on_vsync_toggled(on: bool) -> void:
	SettingsManager.set_vsync_enabled(on)

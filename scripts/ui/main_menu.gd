extends Control

@onready var cam_pivot: Node3D = $Backdrop3D/CamPivot
@onready var menu_box: VBoxContainer = $UI/Card/VBox/MenuButtons
@onready var guide_box: VBoxContainer = $UI/Card/VBox/GuideBox
@onready var settings_box: VBoxContainer = $UI/Card/VBox/SettingsBox
@onready var sens_slider: HSlider = $UI/Card/VBox/SettingsBox/SensSlider
@onready var fov_slider: HSlider = $UI/Card/VBox/SettingsBox/FOVSlider
@onready var vol_slider: HSlider = $UI/Card/VBox/SettingsBox/VolSlider
@onready var gfx_btn: OptionButton = $UI/Card/VBox/SettingsBox/GfxOption


func _ready() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	guide_box.visible = false
	settings_box.visible = false
	gfx_btn.clear()
	gfx_btn.add_item("High")
	gfx_btn.add_item("Medium")
	gfx_btn.add_item("Low")
	_sync_settings()

	# Load real Blender models into the 3D menu diorama!
	_spawn_model("Backdrop3D/Props/TankSlot", "res://assets/models/env/ruined_tank.glb")
	_spawn_model("Backdrop3D/Props/Crystal1", "res://assets/models/env/element115_crystal.glb")
	_spawn_model("Backdrop3D/Props/Crystal2", "res://assets/models/env/element115_crystal.glb")
	_spawn_model("Backdrop3D/Props/Zombie1", "res://assets/models/characters/zombie_soldier.glb")
	_spawn_model("Backdrop3D/Props/Perk1", "res://assets/models/props/perk_juggernog.glb")
	_spawn_model("Backdrop3D/Props/Box1", "res://assets/models/props/mystery_box.glb")
	_spawn_model("Backdrop3D/Props/Sandbag1", "res://assets/models/env/sandbag_wall.glb")
	_spawn_model("Backdrop3D/Props/Crate1", "res://assets/models/env/crate_military.glb")
	_spawn_model("Backdrop3D/Props/Barrel1", "res://assets/models/env/barrel_rusted.glb")


var _t: float = 0.0


func _spawn_model(node_path: String, res_path: String) -> void:
	var holder := get_node_or_null(node_path)
	if holder and ResourceLoader.exists(res_path):
		var inst := (load(res_path) as PackedScene).instantiate()
		holder.add_child(inst)
		var ap := inst.find_child("AnimationPlayer", true, false) as AnimationPlayer
		if ap and ap.has_animation("Idle"):
			ap.get_animation("Idle").loop_mode = Animation.LOOP_LINEAR
			ap.play("Idle")


func _process(delta: float) -> void:
	_t += delta
	if cam_pivot:
		cam_pivot.rotation.y = sin(_t * 0.22) * 0.26


func _sync_settings() -> void:
	sens_slider.value = SettingsManager.mouse_sensitivity * 1000.0
	fov_slider.value = SettingsManager.fov
	vol_slider.value = SettingsManager.master_volume * 100.0
	var idx := ["High", "Medium", "Low"].find(SettingsManager.graphics_quality)
	gfx_btn.selected = maxi(0, idx)


func _on_play_pressed() -> void:
	GameManager.reset_match()
	get_tree().change_scene_to_file("res://scenes/game_world.tscn")


func _on_guide_pressed() -> void:
	menu_box.visible = false
	guide_box.visible = true


func _on_settings_pressed() -> void:
	_sync_settings()
	menu_box.visible = false
	settings_box.visible = true


func _on_back_pressed() -> void:
	guide_box.visible = false
	settings_box.visible = false
	menu_box.visible = true


func _on_quit_pressed() -> void:
	get_tree().quit()


func _on_sens_changed(val: float) -> void:
	SettingsManager.set_mouse_sensitivity(val / 1000.0)


func _on_fov_changed(val: float) -> void:
	SettingsManager.set_fov(val)


func _on_vol_changed(val: float) -> void:
	SettingsManager.set_master_volume(val / 100.0)


func _on_gfx_selected(idx: int) -> void:
	SettingsManager.set_graphics_quality(["High", "Medium", "Low"][idx])

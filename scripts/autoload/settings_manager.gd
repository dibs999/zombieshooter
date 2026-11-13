extends Node

signal settings_changed

var mouse_sensitivity: float = 0.0024
var fov: float = 82.0
var master_volume: float = 0.85
var sfx_volume: float = 0.90
var graphics_quality: String = "High" # High, Medium, Low
var invert_y: bool = false

const SAVE_PATH := "user://bunker115_settings.cfg"


func _ready() -> void:
	load_settings()
	apply_audio()


func apply_audio() -> void:
	var master_idx := AudioServer.get_bus_index("Master")
	if master_idx >= 0:
		AudioServer.set_bus_volume_db(master_idx, linear_to_db(clampf(master_volume, 0.0001, 1.0)))
		AudioServer.set_bus_mute(master_idx, master_volume <= 0.01)


func set_mouse_sensitivity(val: float) -> void:
	mouse_sensitivity = clampf(val, 0.0005, 0.01)
	emit_signal("settings_changed")
	save_settings()


func set_fov(val: float) -> void:
	fov = clampf(val, 65.0, 110.0)
	emit_signal("settings_changed")
	save_settings()


func set_master_volume(val: float) -> void:
	master_volume = clampf(val, 0.0, 1.0)
	apply_audio()
	emit_signal("settings_changed")
	save_settings()


func set_sfx_volume(val: float) -> void:
	sfx_volume = clampf(val, 0.0, 1.0)
	emit_signal("settings_changed")
	save_settings()


func set_graphics_quality(q: String) -> void:
	if q in ["High", "Medium", "Low"]:
		graphics_quality = q
		emit_signal("settings_changed")
		save_settings()


func set_invert_y(val: bool) -> void:
	invert_y = val
	emit_signal("settings_changed")
	save_settings()


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("controls", "mouse_sensitivity", mouse_sensitivity)
	cfg.set_value("controls", "invert_y", invert_y)
	cfg.set_value("video", "fov", fov)
	cfg.set_value("video", "graphics_quality", graphics_quality)
	cfg.set_value("audio", "master_volume", master_volume)
	cfg.set_value("audio", "sfx_volume", sfx_volume)
	cfg.save(SAVE_PATH)


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) == OK:
		mouse_sensitivity = float(cfg.get_value("controls", "mouse_sensitivity", mouse_sensitivity))
		invert_y = bool(cfg.get_value("controls", "invert_y", invert_y))
		fov = float(cfg.get_value("video", "fov", fov))
		graphics_quality = str(cfg.get_value("video", "graphics_quality", graphics_quality))
		master_volume = float(cfg.get_value("audio", "master_volume", master_volume))
		sfx_volume = float(cfg.get_value("audio", "sfx_volume", sfx_volume))

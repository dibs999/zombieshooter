extends Node

signal settings_changed

var mouse_sensitivity: float = 0.0024
var fov: float = 82.0
var master_volume: float = 0.85
var sfx_volume: float = 0.90
var graphics_quality: String = "Medium" # High, Medium, Low
var render_scale: float = 0.85
var msaa_mode: String = "2x" # Off, 2x, 4x
var vsync_enabled: bool = true
var invert_y: bool = false

const SAVE_PATH := "user://bunker115_settings.cfg"


func _ready() -> void:
	load_settings()
	apply_audio()
	apply_vsync()
	if get_tree() != null:
		apply_viewport_settings(get_tree().root)


func apply_audio() -> void:
	var master_idx := AudioServer.get_bus_index("Master")
	if master_idx >= 0:
		AudioServer.set_bus_volume_db(master_idx, linear_to_db(clampf(master_volume, 0.0001, 1.0)))
		AudioServer.set_bus_mute(master_idx, master_volume <= 0.01)


func apply_vsync() -> void:
	if DisplayServer.get_name() == "headless":
		return
	DisplayServer.window_set_vsync_mode(
		DisplayServer.VSYNC_ENABLED if vsync_enabled else DisplayServer.VSYNC_DISABLED
	)


func apply_viewport_settings(vp: Viewport) -> void:
	if vp == null:
		return
	vp.use_occlusion_culling = true
	vp.scaling_3d_scale = clampf(render_scale, 0.5, 1.0)
	if render_scale < 0.99:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR
		vp.fsr_sharpness = 0.25
	else:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	match msaa_mode:
		"Off":
			vp.msaa_3d = Viewport.MSAA_DISABLED
		"4x":
			vp.msaa_3d = Viewport.MSAA_4X
		_:
			vp.msaa_3d = Viewport.MSAA_2X
	if RenderingServer.get_rendering_device() != null:
		var sq := RenderingServer.SHADOW_QUALITY_SOFT_LOW
		if graphics_quality == "High":
			sq = RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM
		elif graphics_quality == "Low":
			sq = RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW
		RenderingServer.directional_soft_shadow_filter_set_quality(sq)
		RenderingServer.positional_soft_shadow_filter_set_quality(sq)


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
		if get_tree() != null:
			apply_viewport_settings(get_tree().root)
		emit_signal("settings_changed")
		save_settings()


func set_render_scale(val: float) -> void:
	render_scale = snappedf(clampf(val, 0.5, 1.0), 0.05)
	if get_tree() != null:
		apply_viewport_settings(get_tree().root)
	emit_signal("settings_changed")
	save_settings()


func set_msaa_mode(mode: String) -> void:
	if mode in ["Off", "2x", "4x"]:
		msaa_mode = mode
		if get_tree() != null:
			apply_viewport_settings(get_tree().root)
		emit_signal("settings_changed")
		save_settings()


func set_vsync_enabled(on: bool) -> void:
	vsync_enabled = on
	apply_vsync()
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
	cfg.set_value("video", "render_scale", render_scale)
	cfg.set_value("video", "msaa_mode", msaa_mode)
	cfg.set_value("video", "vsync_enabled", vsync_enabled)
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
		render_scale = snappedf(clampf(float(cfg.get_value("video", "render_scale", render_scale)), 0.5, 1.0), 0.05)
		var loaded_msaa := str(cfg.get_value("video", "msaa_mode", msaa_mode))
		if loaded_msaa in ["Off", "2x", "4x"]:
			msaa_mode = loaded_msaa
		vsync_enabled = bool(cfg.get_value("video", "vsync_enabled", vsync_enabled))
		master_volume = float(cfg.get_value("audio", "master_volume", master_volume))
		sfx_volume = float(cfg.get_value("audio", "sfx_volume", sfx_volume))

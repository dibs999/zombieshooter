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

	_build_menu_ruins()


var _t: float = 0.0


func _build_menu_ruins() -> void:
	var backdrop := $Backdrop3D as Node3D
	if not backdrop:
		return

	# Weathered PBR materials for ruined brick upper story & timber boards
	var brick_mat := StandardMaterial3D.new()
	brick_mat.albedo_color = Color(0.72, 0.64, 0.60)
	if ResourceLoader.exists("res://assets/textures/env/ruin_brick_albedo.png"):
		brick_mat.albedo_texture = load("res://assets/textures/env/ruin_brick_albedo.png")
	if ResourceLoader.exists("res://assets/textures/env/ruin_brick_normal.png"):
		brick_mat.normal_enabled = true
		brick_mat.normal_texture = load("res://assets/textures/env/ruin_brick_normal.png")
	brick_mat.roughness = 0.90
	brick_mat.uv1_scale = Vector3(0.32, 0.32, 0.32)
	brick_mat.uv1_triplanar = true
	brick_mat.uv1_world_triplanar = true

	var conc_mat := StandardMaterial3D.new()
	conc_mat.albedo_color = Color(0.62, 0.66, 0.72)
	if ResourceLoader.exists("res://assets/textures/env/bunker_concrete_albedo.png"):
		conc_mat.albedo_texture = load("res://assets/textures/env/bunker_concrete_albedo.png")
	conc_mat.roughness = 0.88
	conc_mat.uv1_scale = Vector3(0.28, 0.28, 0.28)
	conc_mat.uv1_triplanar = true
	conc_mat.uv1_world_triplanar = true

	var steel_mat := StandardMaterial3D.new()
	steel_mat.albedo_color = Color(0.22, 0.24, 0.26)
	steel_mat.metallic = 0.72
	steel_mat.roughness = 0.48

	var wood_mat := StandardMaterial3D.new()
	wood_mat.albedo_color = Color(0.42, 0.28, 0.18)
	if ResourceLoader.exists("res://assets/textures/env/charred_wood_albedo.png"):
		wood_mat.albedo_texture = load("res://assets/textures/env/charred_wood_albedo.png")
	wood_mat.roughness = 0.85

	var add_box := func(sz: Vector3, pos: Vector3, mat: Material, rot_deg: Vector3 = Vector3.ZERO) -> void:
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = sz
		bm.material = mat
		mi.mesh = bm
		mi.position = pos
		mi.rotation_degrees = rot_deg
		backdrop.add_child(mi)

	# Concrete cornice belt at Y=3.2m + broken brick piers & upper boarded windows along BackWall & SideWallR
	add_box.call(Vector3(28.4, 0.24, 1.04), Vector3(0, 3.22, -9.2), conc_mat)
	add_box.call(Vector3(1.04, 0.24, 28.4), Vector3(11.5, 3.22, -1.0), conc_mat)

	# Ruined brick piers & boarded upper window bays along BackWall (Y=3.3..5.9, moon sky breach over X=2.2..8.2)
	for spec in [
		[Vector3(1.5, 2.5, 0.76), Vector3(-7.9, 4.55, -9.2)],
		[Vector3(1.8, 0.75, 0.76), Vector3(-6.2, 3.68, -9.2)],
		[Vector3(1.2, 2.3, 0.76), Vector3(-4.7, 4.45, -9.2)],
		[Vector3(1.8, 0.75, 0.76), Vector3(-3.2, 3.68, -9.2)],
		[Vector3(1.5, 2.2, 0.76), Vector3(-1.5, 4.40, -9.2)],
		[Vector3(1.6, 1.1, 0.76), Vector3(0.4, 3.85, -9.2)],
		[Vector3(1.4, 0.9, 0.76), Vector3(8.1, 3.75, -9.2)],
		[Vector3(2.6, 2.1, 0.76), Vector3(10.3, 4.35, -9.2)],
	]:
		add_box.call(spec[0], spec[1], brick_mat)
	# Window lintels & crooked wooden planks across left upper ruined windows
	for wx in [-6.2, -3.2]:
		add_box.call(Vector3(2.0, 0.16, 0.84), Vector3(wx, 5.45, -9.2), conc_mat)
		add_box.call(Vector3(2.0, 0.16, 0.08), Vector3(wx, 4.45, -8.85), wood_mat, Vector3(0, 0, -10))
		add_box.call(Vector3(2.0, 0.16, 0.08), Vector3(wx, 4.95, -8.88), wood_mat, Vector3(0, 0, 14))
	# Protruding twisted rebar rods along top of brick stubs
	for rx in [-7.6, -4.7, -1.5, 0.5, 8.2, 10.2]:
		add_box.call(Vector3(0.04, 0.75, 0.04), Vector3(rx, 5.0 if absf(rx) > 3.0 else 4.4, -9.2), steel_mat, Vector3(12, 0, -16))

	# SideWallR bombed 2nd-story facade with boarded upper window bay
	add_box.call(Vector3(0.76, 2.2, 4.2), Vector3(11.5, 4.40, -6.2), brick_mat)
	add_box.call(Vector3(0.76, 1.8, 3.8), Vector3(11.5, 4.20, 2.8), brick_mat)
	add_box.call(Vector3(0.08, 0.16, 2.4), Vector3(11.45, 4.25, -2.0), wood_mat, Vector3(14, 0, 0))
	add_box.call(Vector3(0.08, 0.16, 2.4), Vector3(11.45, 4.75, -2.0), wood_mat, Vector3(-12, 0, 0))

	# Full Moon + Atmospheric Halo in upper-right sky framed cleanly above the gantry truss
	var moon_pos := Vector3(5.8, 7.6, -24.0)
	var moon := MeshInstance3D.new()
	moon.position = moon_pos
	moon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var sm := SphereMesh.new()
	sm.radius = 1.05
	sm.height = 2.10
	var mmat := ShaderMaterial.new()
	mmat.shader = preload("res://assets/shaders/moon_disc.gdshader")
	sm.material = mmat
	moon.mesh = sm
	backdrop.add_child(moon)

	var halo := MeshInstance3D.new()
	halo.position = moon_pos
	halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var hm := SphereMesh.new()
	hm.radius = 3.1
	hm.height = 6.2
	var hmat := ShaderMaterial.new()
	hmat.shader = preload("res://assets/shaders/moon_halo.gdshader")
	hm.material = hmat
	halo.mesh = hm
	backdrop.add_child(halo)

	# Spawn Blender Architectural Kit + Hellhound Cameo into Menu Diorama
	var place_extra := func(path: String, pos: Vector3, rot_y_deg: float, s: float = 1.0, play_idle: bool = false) -> void:
		if not ResourceLoader.exists(path):
			return
		var h := Node3D.new()
		h.position = pos
		h.rotation_degrees.y = rot_y_deg
		h.scale = Vector3.ONE * s
		var inst := (load(path) as PackedScene).instantiate()
		h.add_child(inst)
		backdrop.add_child(h)
		if play_idle:
			var ap := inst.find_child("AnimationPlayer", true, false) as AnimationPlayer
			if ap and ap.has_animation("Idle"):
				ap.get_animation("Idle").loop_mode = Animation.LOOP_LINEAR
				ap.play("Idle")

	place_extra.call("res://assets/models/env/steel_gantry.glb", Vector3(3.2, 4.95, -6.2), -8.0)
	place_extra.call("res://assets/models/env/wall_pipes.glb", Vector3(3.4, 2.25, -8.76), 0.0)
	place_extra.call("res://assets/models/env/wall_pipes.glb", Vector3(-5.8, 2.25, -8.76), 0.0)
	place_extra.call("res://assets/models/env/rubble_pile.glb", Vector3(-1.4, 0.0, -5.8), 18.0)
	place_extra.call("res://assets/models/env/rubble_pile.glb", Vector3(6.8, 0.0, -5.6), -26.0)
	place_extra.call("res://assets/models/env/barbed_wire.glb", Vector3(6.9, 0.0, -1.8), 32.0)
	place_extra.call("res://assets/models/env/light_cage.glb", Vector3(6.2, 2.85, -7.22), 0.0)
	place_extra.call("res://assets/models/characters/hellhound.glb", Vector3(1.75, 0.0, 2.35), -24.0, 1.0, true)

	# Practical warm wall sconce light by Pillar2 & BackWall
	var sconce := OmniLight3D.new()
	sconce.position = Vector3(6.2, 2.7, -6.9)
	sconce.light_color = Color(1.0, 0.62, 0.25)
	sconce.light_energy = 2.2
	sconce.omni_range = 8.0
	backdrop.add_child(sconce)


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

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

	var pbr_shader := preload("res://assets/shaders/env_world_pbr.gdshader")
	var make_menu_mat := func(alb: String, nrm: String, rgh: String, scale: float, tint: Color, is_floor: bool, puddle: float, damp: float, met: float = 0.0) -> ShaderMaterial:
		var m := ShaderMaterial.new()
		m.shader = pbr_shader
		m.set_shader_parameter("albedo_tint", tint)
		if ResourceLoader.exists(alb):
			m.set_shader_parameter("albedo_tex", load(alb))
		if ResourceLoader.exists(nrm):
			m.set_shader_parameter("normal_tex", load(nrm))
		if ResourceLoader.exists(rgh):
			m.set_shader_parameter("roughness_tex", load(rgh))
		m.set_shader_parameter("uv_scale", scale)
		m.set_shader_parameter("normal_strength", 1.18)
		m.set_shader_parameter("is_floor", is_floor)
		m.set_shader_parameter("puddle_amount", puddle)
		m.set_shader_parameter("wall_damp_strength", damp)
		m.set_shader_parameter("metallic_val", met)
		m.set_shader_parameter("specular_val", 0.38)
		m.set_shader_parameter("macro_variation", 0.24)
		return m

	var cobble_mat: ShaderMaterial = make_menu_mat.call(
		"res://assets/textures/env/cc0_cobble_albedo.jpg",
		"res://assets/textures/env/cc0_cobble_normal.jpg",
		"res://assets/textures/env/cc0_cobble_roughness.jpg",
		0.40, Color(0.54, 0.58, 0.65), true, 0.52, 0.0, 0.0
	)
	cobble_mat.set_shader_parameter("normal_strength", 1.35)
	cobble_mat.set_shader_parameter("use_alt_layer", true)
	cobble_mat.set_shader_parameter("alt_albedo_tex", load("res://assets/textures/env/cc0_mud_albedo.jpg"))
	cobble_mat.set_shader_parameter("alt_normal_tex", load("res://assets/textures/env/cc0_mud_normal.jpg"))
	cobble_mat.set_shader_parameter("alt_roughness_tex", load("res://assets/textures/env/cc0_mud_roughness.jpg"))
	cobble_mat.set_shader_parameter("alt_blend_amount", 0.24)
	cobble_mat.set_shader_parameter("alt_tint", Color(0.46, 0.43, 0.39))

	var brick_mat: ShaderMaterial = make_menu_mat.call(
		"res://assets/textures/env/cc0_brick_albedo.jpg",
		"res://assets/textures/env/cc0_brick_normal.jpg",
		"res://assets/textures/env/cc0_brick_roughness.jpg",
		0.36, Color(0.78, 0.72, 0.68), false, 0.0, 0.34, 0.0
	)
	var conc_mat: ShaderMaterial = make_menu_mat.call(
		"res://assets/textures/env/cc0_concrete_wall_albedo.jpg",
		"res://assets/textures/env/cc0_concrete_wall_normal.jpg",
		"res://assets/textures/env/cc0_concrete_wall_roughness.jpg",
		0.30, Color(0.62, 0.65, 0.70), false, 0.0, 0.52, 0.0
	)
	var steel_mat: ShaderMaterial = make_menu_mat.call(
		"res://assets/textures/env/cc0_rust_steel_albedo.jpg",
		"res://assets/textures/env/cc0_rust_steel_normal.jpg",
		"res://assets/textures/env/cc0_rust_steel_roughness.jpg",
		0.40, Color(0.76, 0.74, 0.72), false, 0.0, 0.25, 0.55
	)
	var wood_mat: ShaderMaterial = make_menu_mat.call(
		"res://assets/textures/env/cc0_planks_albedo.jpg",
		"res://assets/textures/env/cc0_planks_normal.jpg",
		"res://assets/textures/env/cc0_planks_roughness.jpg",
		0.48, Color(0.76, 0.68, 0.60), false, 0.0, 0.20, 0.0
	)

	# Upgrade Ground, BackWall, SideWallR & Pillars to world-space triplanar CC0 PBR shaders
	for gspec in [
		["Ground", cobble_mat],
		["BackWall", conc_mat],
		["SideWallR", conc_mat],
		["Pillar1", conc_mat],
		["Pillar2", conc_mat],
	]:
		var mi := backdrop.get_node_or_null(gspec[0]) as MeshInstance3D
		if mi:
			mi.material_override = gspec[1]

	# Reflection probe for menu diorama metallic & puddle reflections
	var rp := ReflectionProbe.new()
	rp.position = Vector3(1.5, 2.8, -1.5)
	rp.size = Vector3(24.0, 8.0, 20.0)
	rp.box_projection = true
	rp.intensity = 0.85
	rp.update_mode = ReflectionProbe.UPDATE_ONCE
	backdrop.add_child(rp)

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
	add_box.call(Vector3(0.45, 3.2, 0.56), Vector3(10.95, 1.6, -2.5), conc_mat)

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
	for wx in [-6.2, -3.2]:
		add_box.call(Vector3(2.0, 0.16, 0.84), Vector3(wx, 5.45, -9.2), conc_mat)
		add_box.call(Vector3(2.0, 0.16, 0.08), Vector3(wx, 4.45, -8.85), wood_mat, Vector3(0, 0, -10))
		add_box.call(Vector3(2.0, 0.16, 0.08), Vector3(wx, 4.95, -8.88), wood_mat, Vector3(0, 0, 14))
	for rx in [-7.6, -4.7, -1.5, 0.5, 8.2, 10.2]:
		add_box.call(Vector3(0.04, 0.75, 0.04), Vector3(rx, 5.0 if absf(rx) > 3.0 else 4.4, -9.2), steel_mat, Vector3(12, 0, -16))

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

	# Soft moonlight shaft illuminating the centerpiece tank & mystery box
	var shaft := MeshInstance3D.new()
	shaft.position = Vector3(1.8, 3.8, -1.8)
	shaft.rotation_degrees = Vector3(16, 0, -14)
	shaft.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var cyl := CylinderMesh.new()
	cyl.top_radius = 1.1
	cyl.bottom_radius = 2.6
	cyl.height = 8.5
	var smat := ShaderMaterial.new()
	smat.shader = preload("res://assets/shaders/light_shaft.gdshader")
	smat.set_shader_parameter("shaft_color", Color(0.56, 0.76, 0.98, 0.055))
	cyl.material = smat
	shaft.mesh = cyl
	backdrop.add_child(shaft)

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
	place_extra.call("res://assets/models/env/wall_pipes.glb", Vector3(11.05, 2.25, -5.2), -90.0)
	place_extra.call("res://assets/models/env/rubble_pile.glb", Vector3(-1.4, 0.0, -5.8), 18.0)
	place_extra.call("res://assets/models/env/rubble_pile.glb", Vector3(6.8, 0.0, -5.6), -26.0)
	place_extra.call("res://assets/models/env/barbed_wire.glb", Vector3(6.9, 0.0, -1.8), 32.0)
	place_extra.call("res://assets/models/env/light_cage.glb", Vector3(6.2, 2.85, -7.22), 0.0)
	place_extra.call("res://assets/models/characters/hellhound.glb", Vector3(1.75, 0.0, 2.35), -24.0, 1.0, true)

	# Upgraded CC0 Diorama Props (street lamp, barrel stove, concrete barriers, covered car, ammo boxes, power box)
	place_extra.call("res://assets/models/env_cc0/street_lamp_01.glb", Vector3(8.5, 0.0, -5.2), -125.0)
	place_extra.call("res://assets/models/env_cc0/covered_car.glb", Vector3(8.2, 0.0, -0.4), -22.0)
	place_extra.call("res://assets/models/env_cc0/concrete_road_barrier_02.glb", Vector3(0.45, 0.0, 3.65), 14.0)
	place_extra.call("res://assets/models/env_cc0/concrete_road_barrier.glb", Vector3(5.8, 0.0, 3.0), -34.0)
	place_extra.call("res://assets/models/env_cc0/barrel_stove.glb", Vector3(-1.85, 0.0, -2.35), 15.0)
	place_extra.call("res://assets/models/env_cc0/ammo_box.glb", Vector3(4.15, 0.0, 2.85), -18.0)
	place_extra.call("res://assets/models/env_cc0/industrial_wall_lamp.glb", Vector3(-2.5, 2.6, -7.25), 0.0)
	place_extra.call("res://assets/models/env_cc0/power_box_01.glb", Vector3(11.08, 1.60, 0.4), -90.0)

	# Glowing sodium bulb inside street_lamp_01 lantern housing
	var bulb := MeshInstance3D.new()
	bulb.position = Vector3(8.5, 3.36, -5.2)
	bulb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var bsm := SphereMesh.new()
	bsm.radius = 0.09
	bsm.height = 0.22
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(1.0, 0.78, 0.40)
	bmat.emission_enabled = true
	bmat.emission = Color(1.0, 0.68, 0.28)
	bmat.emission_energy_multiplier = 4.5
	bsm.material = bmat
	bulb.mesh = bsm
	backdrop.add_child(bulb)

	# Warm Street Lamp & Barrel Fire Lights
	var lamp_l := OmniLight3D.new()
	lamp_l.position = Vector3(8.5, 3.30, -5.2)
	lamp_l.light_color = Color(1.0, 0.68, 0.28)
	lamp_l.light_energy = 3.1
	lamp_l.omni_range = 14.0
	backdrop.add_child(lamp_l)

	var stove_l := OmniLight3D.new()
	stove_l.position = Vector3(-1.85, 0.95, -2.35)
	stove_l.light_color = Color(1.0, 0.45, 0.14)
	stove_l.light_energy = 1.65
	stove_l.omni_range = 7.5
	backdrop.add_child(stove_l)

	var sconce := OmniLight3D.new()
	sconce.position = Vector3(6.2, 2.7, -6.9)
	sconce.light_color = Color(1.0, 0.62, 0.25)
	sconce.light_energy = 2.2
	sconce.omni_range = 8.0
	backdrop.add_child(sconce)

	var wall_sconce := OmniLight3D.new()
	wall_sconce.position = Vector3(-2.5, 2.52, -7.02)
	wall_sconce.light_color = Color(1.0, 0.65, 0.28)
	wall_sconce.light_energy = 1.15
	wall_sconce.omni_range = 6.5
	backdrop.add_child(wall_sconce)

	# Decals on menu cobble ground & SideWallR (oil slicks, blood, puddles, wall crack)
	for dspec in [
		[Vector3(2.6, 0.0, -3.5), Vector3.ZERO, Vector3(3.6, 0.16, 4.4), "res://assets/decals/decal_oil_slick.png"],
		[Vector3(2.2, 0.0, 1.9), Vector3.ZERO, Vector3(2.2, 0.16, 2.2), "res://assets/decals/decal_blood_splatter.png"],
		[Vector3(-0.4, 0.0, 2.6), Vector3.ZERO, Vector3(3.2, 0.16, 2.8), "res://assets/decals/decal_puddle_albedo.png"],
		[Vector3(11.08, 1.9, -1.6), Vector3(0, 0, 90), Vector3(2.4, 0.22, 2.4), "res://assets/decals/decal_wall_crack.png"],
	]:
		if ResourceLoader.exists(dspec[3]):
			var dec := Decal.new()
			dec.position = dspec[0]
			dec.rotation_degrees = dspec[1]
			dec.size = dspec[2]
			dec.texture_albedo = load(dspec[3])
			dec.albedo_mix = 0.85
			backdrop.add_child(dec)

	# GPU Particles: Embers from barrel stove + low mist across cobbles
	if ResourceLoader.exists("res://scenes/fx/env_embers.tscn"):
		var emb := (load("res://scenes/fx/env_embers.tscn") as PackedScene).instantiate() as Node3D
		emb.position = Vector3(-1.85, 0.65, -2.35)
		backdrop.add_child(emb)
	if ResourceLoader.exists("res://scenes/fx/env_ground_fog.tscn"):
		var fog := (load("res://scenes/fx/env_ground_fog.tscn") as PackedScene).instantiate() as Node3D
		fog.position = Vector3(2.4, 0.25, 0.2)
		backdrop.add_child(fog)


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

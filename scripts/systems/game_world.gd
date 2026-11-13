extends Node3D
class_name GameWorld

@onready var world_env: WorldEnvironment = $WorldEnvironment
@onready var moon_light: DirectionalLight3D = $MoonLight
@onready var geo_root: Node3D = $LevelGeometry

var _power_lights: Array[OmniLight3D] = []
var _alarm_lights: Array[OmniLight3D] = []
var _fog_base_color := Color(0.05, 0.10, 0.16, 1.0)
var _fog_dog_color := Color(0.28, 0.09, 0.04, 1.0)
var _pulse_t: float = 0.0

var _mat_cobble: StandardMaterial3D
var _mat_concrete: StandardMaterial3D
var _mat_tile: StandardMaterial3D
var _mat_steel: StandardMaterial3D
var _mat_wood: StandardMaterial3D
var _mat_earth: StandardMaterial3D
var _light_shaft_mat: ShaderMaterial


func _ready() -> void:
	SettingsManager.settings_changed.connect(_apply_graphics_settings)
	GameManager.power_activated.connect(_on_power_activated)
	GameManager.round_changed.connect(_on_round_changed)

	_init_materials()
	_build_facility_architecture()
	_build_props_and_atmosphere()
	_bake_zone_navigation()
	_apply_graphics_settings()
	AudioManager.start_ambience()


func _process(delta: float) -> void:
	_pulse_t += delta
	if not GameManager.power_on:
		var pulse := 0.8 + 0.7 * sin(_pulse_t * 3.8)
		for l in _alarm_lights:
			l.light_energy = pulse


func _init_materials() -> void:
	_mat_cobble = _make_pbr(
		"res://assets/textures/env/cobblestone_albedo.png",
		"res://assets/textures/env/cobblestone_normal.png",
		"res://assets/textures/env/cobblestone_roughness.png",
		Vector3(0.45, 0.45, 0.45), Color(0.74, 0.78, 0.84), 0.72
	)
	_mat_concrete = _make_pbr(
		"res://assets/textures/env/bunker_concrete_albedo.png",
		"res://assets/textures/env/bunker_concrete_normal.png",
		"res://assets/textures/env/bunker_concrete_roughness.png",
		Vector3(0.28, 0.28, 0.28), Color(0.78, 0.80, 0.82), 0.86
	)
	_mat_tile = _make_pbr(
		"res://assets/textures/env/lab_tile_albedo.png",
		"res://assets/textures/env/lab_tile_normal.png",
		"res://assets/textures/env/lab_tile_roughness.png",
		Vector3(0.42, 0.42, 0.42), Color(0.84, 0.90, 0.92), 0.46
	)
	_mat_steel = _make_pbr(
		"res://assets/textures/env/rusted_steel_albedo.png",
		"res://assets/textures/env/rusted_steel_normal.png",
		"res://assets/textures/env/rusted_steel_roughness.png",
		Vector3(0.38, 0.38, 0.38), Color(0.76, 0.78, 0.82), 0.70, 0.26
	)
	_mat_wood = _make_pbr(
		"res://assets/textures/env/charred_wood_albedo.png",
		"res://assets/textures/env/charred_wood_normal.png",
		"res://assets/textures/env/charred_wood_roughness.png",
		Vector3(0.55, 0.55, 0.55), Color(0.78, 0.70, 0.62), 0.84
	)
	_mat_earth = StandardMaterial3D.new()
	_mat_earth.albedo_color = Color(0.05, 0.06, 0.055, 1.0)
	_mat_earth.roughness = 0.95

	_light_shaft_mat = ShaderMaterial.new()
	_light_shaft_mat.shader = preload("res://assets/shaders/light_shaft.gdshader")
	_light_shaft_mat.set_shader_parameter("shaft_color", Color(0.55, 0.78, 1.0, 0.09))


func _make_pbr(alb: String, nrm: String, rgh: String, uv_scale: Vector3, tint: Color, rough: float, met: float = 0.0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = tint
	if ResourceLoader.exists(alb):
		mat.albedo_texture = load(alb)
	if ResourceLoader.exists(nrm):
		mat.normal_enabled = true
		mat.normal_texture = load(nrm)
	if ResourceLoader.exists(rgh):
		mat.roughness_texture = load(rgh)
	mat.roughness = rough
	mat.metallic = met
	mat.uv1_scale = uv_scale
	mat.uv1_triplanar = true
	mat.uv1_world_triplanar = true
	return mat


func _build_facility_architecture() -> void:
	# Global smooth ground collider covering playable map + outside zombie window approach
	var foundation := StaticBody3D.new()
	foundation.name = "Foundation"
	foundation.collision_layer = 1
	foundation.collision_mask = 0
	foundation.add_to_group("nav_bake")
	var fcol := CollisionShape3D.new()
	var fbox := BoxShape3D.new()
	fbox.size = Vector3(84.0, 0.4, 64.0)
	fcol.shape = fbox
	fcol.position = Vector3(0.0, -0.2, -5.0)
	foundation.add_child(fcol)
	geo_root.add_child(foundation)

	# Outer dark terrain visual mesh slightly below floor level to avoid Z-fighting
	_add_visual_box("OuterEarth", Vector3(84, 0.1, 64), Vector3(0, -0.07, -5), _mat_earth)

	# Zone Visual Floors at Y = 0.0 (top face 0.002)
	_add_visual_box("Floor_Spawn", Vector3(20.0, 0.04, 18.0), Vector3(0.0, -0.018, 1.0), _mat_cobble)
	_add_visual_box("Floor_Lab", Vector3(14.0, 0.04, 16.0), Vector3(-17.0, -0.018, 0.0), _mat_tile)
	_add_visual_box("Floor_East", Vector3(14.0, 0.04, 16.0), Vector3(17.0, -0.018, 0.0), _mat_steel)
	_add_visual_box("Floor_Reactor", Vector3(48.0, 0.04, 14.0), Vector3(0.0, -0.018, -15.0), _mat_concrete)

	# Exterior West Lab Walls (X=-24, Z=-8..+8 with Window W at Z=0)
	_add_wall(Vector2(-24.0, -8.0), Vector2(-24.0, -1.15), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-24.0, 1.15), Vector2(-24.0, 8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-24.0, -1.15), Vector2(-24.0, 1.15), 2.82, 4.6, 0.5, _mat_concrete)

	# Exterior Lab South Wall (Z=+8, X=-24..-10 with Window S at X=-17)
	_add_wall(Vector2(-24.0, 8.0), Vector2(-18.15, 8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-15.85, 8.0), Vector2(-10.0, 8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-18.15, 8.0), Vector2(-15.85, 8.0), 2.82, 4.6, 0.5, _mat_concrete)

	# Corner connectors linking Lab/East Z=+8 to Spawn Z=+10
	_add_wall(Vector2(-10.0, 8.0), Vector2(-10.0, 10.25), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(10.0, 8.0), Vector2(10.0, 10.25), 4.6, 0.5, _mat_concrete)

	# Exterior Spawn South Wall (Z=+10, X=-10..+10 with Windows at X=-5.2 and X=+5.2)
	_add_wall(Vector2(-10.0, 10.0), Vector2(-6.35, 10.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-4.05, 10.0), Vector2(4.05, 10.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(6.35, 10.0), Vector2(10.0, 10.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-6.35, 10.0), Vector2(-4.05, 10.0), 2.82, 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(4.05, 10.0), Vector2(6.35, 10.0), 2.82, 4.6, 0.5, _mat_concrete)

	# Exterior East South Wall (Z=+8, X=+10..+24 with Window S at X=+17)
	_add_wall(Vector2(10.0, 8.0), Vector2(15.85, 8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(18.15, 8.0), Vector2(24.0, 8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(15.85, 8.0), Vector2(18.15, 8.0), 2.82, 4.6, 0.5, _mat_concrete)

	# Exterior East Wall (X=+24, Z=-8..+8 with Window E at Z=+1.5)
	_add_wall(Vector2(24.0, -8.0), Vector2(24.0, 0.35), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(24.0, 2.65), Vector2(24.0, 8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(24.0, 0.35), Vector2(24.0, 2.65), 2.82, 4.6, 0.5, _mat_concrete)

	# Interior Partition: Spawn <-> West Lab (X=-10, Door Z in [-1.7..+1.7])
	_add_wall(Vector2(-10.0, -8.0), Vector2(-10.0, -1.7), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-10.0, 1.7), Vector2(-10.0, 8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-10.0, -1.7), Vector2(-10.0, 1.7), 3.2, 4.6, 0.5, _mat_concrete)

	# Interior Partition: Spawn <-> East Courtyard (X=+10, Door Z in [-1.7..+1.7])
	_add_wall(Vector2(10.0, -8.0), Vector2(10.0, -1.7), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(10.0, 1.7), Vector2(10.0, 8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(10.0, -1.7), Vector2(10.0, 1.7), 3.2, 4.6, 0.5, _mat_concrete)

	# North Partition separating Zones 1/2/3 from Zone 4 Reactor (Z=-8)
	# Lab North Door: X in [-16.7..-13.3]
	_add_wall(Vector2(-24.0, -8.0), Vector2(-16.7, -8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-13.3, -8.0), Vector2(-10.0, -8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-16.7, -8.0), Vector2(-13.3, -8.0), 3.2, 4.6, 0.5, _mat_concrete)
	# Spawn North Power Shortcut Door: X in [+1.5..+4.9]
	_add_wall(Vector2(-10.0, -8.0), Vector2(1.5, -8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(4.9, -8.0), Vector2(10.0, -8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(1.5, -8.0), Vector2(4.9, -8.0), 3.2, 4.6, 0.5, _mat_concrete)
	# East North Door: X in [+15.3..+18.7]
	_add_wall(Vector2(10.0, -8.0), Vector2(15.3, -8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(18.7, -8.0), Vector2(24.0, -8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(15.3, -8.0), Vector2(18.7, -8.0), 3.2, 4.6, 0.5, _mat_concrete)

	# Electro-Trap Choke Archway inside East Courtyard (Z=-2.8, archway X in [15.2..18.8])
	_add_wall(Vector2(10.25, -2.8), Vector2(15.2, -2.8), 4.6, 0.5, _mat_steel)
	_add_wall(Vector2(18.8, -2.8), Vector2(23.75, -2.8), 4.6, 0.5, _mat_steel)
	_add_header(Vector2(15.2, -2.8), Vector2(18.8, -2.8), 2.8, 4.6, 0.5, _mat_steel)

	# Reactor Outer Walls (X=-24, X=+24, Z=-22 with 2 North Windows at X=-9.5 and X=+9.5)
	_add_wall(Vector2(-24.0, -22.0), Vector2(-24.0, -8.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(24.0, -22.0), Vector2(24.0, -8.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(-24.0, -22.0), Vector2(-10.65, -22.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(-8.35, -22.0), Vector2(8.35, -22.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(10.65, -22.0), Vector2(24.0, -22.0), 5.2, 0.5, _mat_concrete)
	_add_header(Vector2(-10.65, -22.0), Vector2(-8.35, -22.0), 2.82, 5.2, 0.5, _mat_concrete)
	_add_header(Vector2(8.35, -22.0), Vector2(10.65, -22.0), 2.82, 5.2, 0.5, _mat_concrete)

	# Roofs & Ruined Skylight Beams
	# West Lab closed roof (Y=4.6)
	_add_static_box("Roof_Lab", Vector3(14.5, 0.3, 16.5), Vector3(-17.0, 4.75, 0.0), _mat_concrete)
	# Reactor high roof (Y=5.2) with glowing skylight strips
	_add_static_box("Roof_Reactor", Vector3(48.5, 0.3, 14.5), Vector3(0.0, 5.35, -15.0), _mat_concrete)
	# Spawn partial bombed roof overhangs leaving central courtyard open to moonlight & Mystery Box beam
	_add_static_box("Roof_Spawn_S", Vector3(20.5, 0.3, 4.4), Vector3(0.0, 4.75, 8.0), _mat_concrete)
	_add_static_box("Roof_Spawn_N", Vector3(20.5, 0.3, 3.0), Vector3(0.0, 4.75, -6.5), _mat_concrete)
	# Ruined overhead wooden/steel rafters across open courtyard
	_add_visual_box("Rafter_1", Vector3(20.0, 0.25, 0.35), Vector3(0.0, 4.65, -1.2), _mat_steel)
	_add_visual_box("Rafter_2", Vector3(20.0, 0.25, 0.35), Vector3(0.0, 4.65, 3.2), _mat_wood)
	# East Courtyard roof with big open skylight over Box East
	_add_static_box("Roof_East_S", Vector3(14.5, 0.3, 9.0), Vector3(17.0, 4.75, 3.5), _mat_concrete)


func _build_props_and_atmosphere() -> void:
	# Ruined Panzer Tank Centerpiece in Spawn Courtyard
	_place_prop("res://assets/models/env/ruined_tank.glb", Vector3(-1.4, 0.0, -2.0), 24.0, Vector3(3.0, 2.2, 5.2), Vector3(0, 1.1, 0))
	# Courtyard Sandbags, Crates, Barrels & Element 115 Crystals
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(2.8, 0.0, 0.6), -25.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(-6.2, 0.0, 1.8), 42.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(6.8, 0.0, -5.2), 18.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/barrel_rusted.glb", Vector3(7.9, 0.0, -4.6), 0.0, Vector3(0.7, 0.95, 0.7), Vector3(0, 0.47, 0))
	_place_prop("res://assets/models/env/barrel_rusted.glb", Vector3(-8.4, 0.0, -6.2), 0.0, Vector3(0.7, 0.95, 0.7), Vector3(0, 0.47, 0))
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(4.2, 0.0, -4.2), 15.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.92, 1.0), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(-6.8, 0.0, -5.8), -40.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.92, 1.0), 1.5)

	# West Lab Bio-Pods + Crystal Island + Lab Crates
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-16.8, 0.0, -1.6), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-16.8, 0.0, 2.2), 180.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(-16.8, 0.0, 0.3), 25.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.95, 1.0), 1.7)
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(-22.2, 0.0, 5.8), 10.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))

	# East Courtyard Industrial Crates & Barrels
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(21.4, 0.0, 6.2), -22.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/barrel_rusted.glb", Vector3(22.4, 0.0, 5.4), 0.0, Vector3(0.7, 0.95, 0.7), Vector3(0, 0.47, 0))
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(21.0, 0.0, -6.2), 70.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.92, 1.0), 1.5)

	# Reactor Props: Teleporter Pad + Lab Pods + Crystals + Cover
	_place_prop("res://assets/models/env/teleporter_pad.glb", Vector3(-15.0, 0.0, -15.5), 0.0, Vector3.ZERO, Vector3.ZERO, Color(0.15, 0.92, 1.0), 2.2)
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-1.4, 0.0, -20.5), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(4.4, 0.0, -20.5), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(11.5, 0.0, -13.8), 30.0, Vector3(1.1, 1.2, 1.1), Vector3(0, 0.5, 0), Color(0.1, 0.95, 1.0), 1.8)
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(7.0, 0.0, -13.0), 15.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(-7.0, 0.0, -13.5), -14.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))

	# Moonlight Volumetric Cones streaming over Spawn Courtyard
	_add_light_shaft(Vector3(-1.5, 3.6, -1.0), Vector3(18, 0, -12), 2.4, 9.0)
	_add_light_shaft(Vector3(3.2, 3.6, 1.8), Vector3(18, 0, -12), 2.0, 9.0)

	# Practical Cage Lights & Facility Lighting
	_add_cage_light(Vector3(0.0, 3.3, 9.68), 180.0, Color(1.0, 0.62, 0.24), 2.5, false)
	_add_cage_light(Vector3(-9.68, 3.3, 4.5), 90.0, Color(1.0, 0.62, 0.24), 2.4, false)
	_add_cage_light(Vector3(-23.68, 3.3, -4.5), 90.0, Color(0.35, 0.88, 1.0), 1.6, false)
	_add_cage_light(Vector3(-16.8, 4.56, 0.3), 0.0, Color(0.35, 0.95, 1.0), 2.4, true, true)
	_add_cage_light(Vector3(17.0, 4.56, 3.5), 0.0, Color(1.0, 0.65, 0.28), 1.8, false, true)
	_add_cage_light(Vector3(17.0, 4.56, -5.5), 0.0, Color(1.0, 0.68, 0.32), 2.6, true, true)
	_add_cage_light(Vector3(23.68, 3.3, -5.2), -90.0, Color(1.0, 0.62, 0.25), 1.6, false)
	_add_cage_light(Vector3(-15.0, 5.16, -15.5), 0.0, Color(0.45, 0.9, 1.0), 2.8, true, true)
	_add_cage_light(Vector3(1.5, 5.16, -15.5), 0.0, Color(1.0, 0.85, 0.65), 3.2, true, true)
	_add_cage_light(Vector3(15.0, 5.16, -15.5), 0.0, Color(1.0, 0.65, 0.28), 2.8, true, true)

	# Alarm Red Lights active before Power Switch is pulled
	_add_alarm_light(Vector3(-3.5, 3.8, -19.5))
	_add_alarm_light(Vector3(-17.0, 3.8, -5.0))
	_add_alarm_light(Vector3(17.0, 3.8, -5.0))


func _add_visual_box(nname: String, size: Vector3, pos: Vector3, mat: Material) -> void:
	var mi := MeshInstance3D.new()
	mi.name = nname
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh.material = mat
	mi.mesh = mesh
	mi.position = pos
	geo_root.add_child(mi)


func _add_static_box(nname: String, size: Vector3, pos: Vector3, mat: Material, add_nav: bool = false) -> void:
	var sb := StaticBody3D.new()
	sb.name = nname
	sb.position = pos
	sb.collision_layer = 1
	sb.collision_mask = 0
	if add_nav:
		sb.add_to_group("nav_bake")
	var col := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	col.shape = bs
	sb.add_child(col)
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	bm.material = mat
	mi.mesh = bm
	sb.add_child(mi)
	geo_root.add_child(sb)


func _add_wall(p1: Vector2, p2: Vector2, height: float, thick: float, mat: Material) -> void:
	var delta := p2 - p1
	var length := delta.length()
	if length < 0.05:
		return
	var mid := (p1 + p2) * 0.5
	var angle := -delta.angle()
	var sb := StaticBody3D.new()
	sb.position = Vector3(mid.x, height * 0.5, mid.y)
	sb.rotation.y = angle
	sb.collision_layer = 1
	sb.collision_mask = 0
	sb.add_to_group("nav_bake")
	var col := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(length, height, thick)
	col.shape = bs
	sb.add_child(col)
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(length, height, thick)
	bm.material = mat
	mi.mesh = bm
	sb.add_child(mi)
	geo_root.add_child(sb)


func _add_header(p1: Vector2, p2: Vector2, bottom_y: float, top_y: float, thick: float, mat: Material) -> void:
	var h := top_y - bottom_y
	if h <= 0.05:
		return
	var delta := p2 - p1
	var mid := (p1 + p2) * 0.5
	var sb := StaticBody3D.new()
	sb.position = Vector3(mid.x, bottom_y + h * 0.5, mid.y)
	sb.rotation.y = -delta.angle()
	sb.collision_layer = 1
	sb.collision_mask = 0
	var col := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(delta.length(), h, thick)
	col.shape = bs
	sb.add_child(col)
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(delta.length(), h, thick)
	bm.material = mat
	mi.mesh = bm
	sb.add_child(mi)
	geo_root.add_child(sb)


func _place_prop(model_path: String, pos: Vector3, rot_y_deg: float, col_size: Vector3, col_offset: Vector3, glow_color: Color = Color.BLACK, glow_energy: float = 0.0) -> void:
	var holder := Node3D.new()
	holder.position = pos
	holder.rotation_degrees.y = rot_y_deg
	geo_root.add_child(holder)

	if ResourceLoader.exists(model_path):
		holder.add_child((load(model_path) as PackedScene).instantiate())

	if col_size.length_squared() > 0.01:
		var sb := StaticBody3D.new()
		sb.collision_layer = 1
		sb.collision_mask = 0
		sb.add_to_group("nav_bake")
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = col_size
		cs.shape = bs
		cs.position = col_offset
		sb.add_child(cs)
		holder.add_child(sb)

	if glow_energy > 0.0:
		var l := OmniLight3D.new()
		l.position = col_offset + Vector3(0, 0.5, 0)
		l.light_color = glow_color
		l.light_energy = glow_energy
		l.omni_range = 9.0
		holder.add_child(l)


func _add_light_shaft(pos: Vector3, rot_deg: Vector3, radius: float, height: float) -> void:
	var mi := MeshInstance3D.new()
	mi.position = pos
	mi.rotation_degrees = rot_deg
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var cyl := CylinderMesh.new()
	cyl.top_radius = radius * 0.45
	cyl.bottom_radius = radius
	cyl.height = height
	cyl.material = _light_shaft_mat
	mi.mesh = cyl
	geo_root.add_child(mi)


func _add_cage_light(pos: Vector3, rot_y_deg: float, col: Color, energy: float, power_controlled: bool, ceiling_mount: bool = false) -> void:
	var n := Node3D.new()
	n.position = pos
	n.rotation_degrees.y = rot_y_deg
	geo_root.add_child(n)
	if ResourceLoader.exists("res://assets/models/env/light_cage.glb"):
		var inst := (load("res://assets/models/env/light_cage.glb") as PackedScene).instantiate() as Node3D
		if ceiling_mount:
			inst.rotation_degrees.x = 90.0
		n.add_child(inst)
	var omni := OmniLight3D.new()
	omni.position = Vector3(0, -0.35, 0) if ceiling_mount else Vector3(0, -0.2, 0.25)
	omni.light_color = col
	omni.omni_range = 16.0
	omni.light_energy = 0.0 if (power_controlled and not GameManager.power_on) else energy
	omni.set_meta("target_energy", energy)
	n.add_child(omni)
	if power_controlled:
		_power_lights.append(omni)


func _add_alarm_light(pos: Vector3) -> void:
	var l := OmniLight3D.new()
	l.position = pos
	l.light_color = Color(1.0, 0.14, 0.08)
	l.omni_range = 12.0
	l.light_energy = 1.2
	geo_root.add_child(l)
	_alarm_lights.append(l)


func _bake_zone_navigation() -> void:
	# Add temporary seal colliders at doorways during NavMesh bake so zones stay sealed before purchase
	var seals := Node3D.new()
	geo_root.add_child(seals)
	for spec in [
		[Vector3(-10.0, 1.5, 0.0), Vector3(0.5, 3.0, 3.6)],
		[Vector3(10.0, 1.5, 0.0), Vector3(0.5, 3.0, 3.6)],
		[Vector3(-15.0, 1.5, -8.0), Vector3(3.6, 3.0, 0.5)],
		[Vector3(17.0, 1.5, -8.0), Vector3(3.6, 3.0, 0.5)],
		[Vector3(3.2, 1.5, -8.0), Vector3(3.6, 3.0, 0.5)],
	]:
		var sb := StaticBody3D.new()
		sb.position = spec[0]
		sb.collision_layer = 1
		sb.add_to_group("nav_bake")
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = spec[1]
		cs.shape = bs
		sb.add_child(cs)
		seals.add_child(sb)

	var zone_cfg := {
		"Navigation/NavRegionSpawn": AABB(Vector3(-9.9, -0.4, -7.9), Vector3(19.8, 3.6, 17.8)),
		"Navigation/NavRegionLab": AABB(Vector3(-23.9, -0.4, -7.9), Vector3(13.8, 3.6, 15.8)),
		"Navigation/NavRegionEast": AABB(Vector3(10.1, -0.4, -7.9), Vector3(13.8, 3.6, 15.8)),
		"Navigation/NavRegionReactor": AABB(Vector3(-23.9, -0.4, -21.9), Vector3(47.8, 3.6, 13.8)),
	}
	for npath in zone_cfg.keys():
		var reg := get_node_or_null(npath) as NavigationRegion3D
		if reg == null:
			continue
		var nm := NavigationMesh.new()
		nm.agent_radius = 0.50
		nm.agent_height = 1.75
		nm.agent_max_climb = 0.25
		nm.cell_size = 0.25
		nm.cell_height = 0.25
		nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
		nm.geometry_source_geometry_mode = NavigationMesh.SOURCE_GEOMETRY_GROUPS_EXPLICIT
		nm.geometry_source_group_name = &"nav_bake"
		nm.filter_baking_aabb = zone_cfg[npath]
		reg.navigation_mesh = nm
		reg.bake_navigation_mesh(false)

	geo_root.remove_child(seals)
	seals.free()


func _on_power_activated() -> void:
	for al in _alarm_lights:
		al.light_energy = 0.0
	for pl in _power_lights:
		var target := float(pl.get_meta("target_energy", 2.8))
		create_tween().tween_property(pl, "light_energy", target, 0.9)


func _on_round_changed(_r: int, is_dog: bool) -> void:
	if not world_env or not world_env.environment:
		return
	var env := world_env.environment
	var target_col := _fog_dog_color if is_dog else _fog_base_color
	var target_den := 0.044 if is_dog else 0.022
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(env, "fog_light_color", target_col, 1.4)
	tw.tween_property(env, "fog_density", target_den, 1.4)


func _apply_graphics_settings() -> void:
	if not world_env or not world_env.environment:
		return
	var env := world_env.environment
	var q := SettingsManager.graphics_quality
	env.ssao_enabled = (q == "High")
	env.glow_enabled = (q != "Low")
	env.volumetric_fog_enabled = (q == "High")
	if moon_light:
		moon_light.shadow_enabled = (q != "Low")

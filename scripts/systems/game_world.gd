extends Node3D
class_name GameWorld

@onready var world_env: WorldEnvironment = $WorldEnvironment
@onready var moon_light: DirectionalLight3D = $MoonLight
@onready var geo_root: Node3D = $LevelGeometry

var _power_lights: Array[OmniLight3D] = []
var _alarm_lights: Array[OmniLight3D] = []
var _fog_base_color := Color(0.07, 0.085, 0.10, 1.0)
var _fog_dog_color := Color(0.28, 0.09, 0.04, 1.0)
var _pulse_t: float = 0.0

var _mat_cobble: StandardMaterial3D
var _mat_concrete: StandardMaterial3D
var _mat_brick: StandardMaterial3D
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
	_build_facility_details()
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
		Vector3(0.45, 0.45, 0.45), Color(0.76, 0.80, 0.84), 0.78
	)
	_mat_concrete = _make_pbr(
		"res://assets/textures/env/bunker_concrete_albedo.png",
		"res://assets/textures/env/bunker_concrete_normal.png",
		"res://assets/textures/env/bunker_concrete_roughness.png",
		Vector3(0.28, 0.28, 0.28), Color(0.78, 0.80, 0.82), 0.86
	)
	_mat_brick = _make_pbr(
		"res://assets/textures/env/ruin_brick_albedo.png",
		"res://assets/textures/env/ruin_brick_normal.png",
		"res://assets/textures/env/ruin_brick_roughness.png",
		Vector3(0.32, 0.32, 0.32), Color(0.76, 0.68, 0.64), 0.90
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
	_light_shaft_mat.set_shader_parameter("shaft_color", Color(0.58, 0.76, 0.96, 0.065))


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

	# Roofs & Structural Ceiling Beams
	_add_static_box("Roof_Lab", Vector3(14.5, 0.3, 16.5), Vector3(-17.0, 4.75, 0.0), _mat_concrete)
	_add_static_box("Roof_Reactor", Vector3(48.5, 0.3, 14.5), Vector3(0.0, 5.35, -15.0), _mat_concrete)
	# Spawn partial bombed roof overhangs leaving central courtyard open to moonlight & Mystery Box beam
	_add_static_box("Roof_Spawn_S", Vector3(20.5, 0.3, 4.4), Vector3(0.0, 4.75, 8.0), _mat_concrete)
	_add_static_box("Roof_Spawn_N", Vector3(20.5, 0.3, 3.0), Vector3(0.0, 4.75, -6.5), _mat_concrete)
	# Broken timber/steel roof joists framing the bombed sky opening in Spawn Courtyard
	_add_visual_box("Rafter_StubL", Vector3(6.2, 0.24, 0.32), Vector3(-6.9, 4.62, 3.2), _mat_wood)
	_add_visual_box("Rafter_StubR", Vector3(5.6, 0.24, 0.32), Vector3(7.2, 4.62, 3.2), _mat_wood)
	# East Courtyard roof with big open skylight over Box East
	_add_static_box("Roof_East_S", Vector3(14.5, 0.3, 9.0), Vector3(17.0, 4.75, 3.5), _mat_concrete)

	# 2nd-Story Bombed Brick Courtyard Skyline around Spawn (Y = 4.6 .. 9.0m, moon gap along X=-4.4..+0.8)
	_build_ruined_story(Vector2(-10.0, -8.0), Vector2(10.0, -8.0), 4.6, 0.52, [0.16, 0.62, 0.84], 0.28, 0.54)
	_build_ruined_story(Vector2(-10.0, -8.0), Vector2(-10.0, 10.0), 4.6, 0.52, [0.22, 0.52, 0.80], -1.0, -1.0)
	_build_ruined_story(Vector2(10.0, -8.0), Vector2(10.0, 10.0), 4.6, 0.52, [0.22, 0.52, 0.80], -1.0, -1.0)
	_build_ruined_story(Vector2(-10.0, 10.0), Vector2(10.0, 10.0), 4.6, 0.52, [0.25, 0.75], -1.0, -1.0)

	# Interior Structural Wall Pilasters, Baseboards & Ceiling I-Beams to break up large flat concrete walls
	for rx in [-17.5, -13.0, -6.4, -0.1, 6.4, 12.6, 18.8]:
		_add_visual_box("Pilaster_Reactor_%d" % int(rx * 10), Vector3(0.54, 5.2, 0.32), Vector3(rx, 2.6, -21.74), _mat_concrete)
	for rx_b in [-16.0, -8.0, 0.0, 8.0, 16.0]:
		_add_visual_box("CeilingBeam_Reactor_%d" % int(rx_b), Vector3(0.36, 0.42, 13.8), Vector3(rx_b, 5.02, -15.0), _mat_steel)
	for lx_b in [-5.0, 0.0, 5.0]:
		_add_visual_box("CeilingBeam_Lab_%d" % int(lx_b), Vector3(13.6, 0.36, 0.34), Vector3(-17.0, 4.44, lx_b), _mat_steel)
	for lz_p in [-5.2, 5.2]:
		_add_visual_box("Pilaster_LabW_%d" % int(lz_p * 10), Vector3(0.30, 4.6, 0.50), Vector3(-23.74, 2.3, lz_p), _mat_concrete)
		_add_visual_box("Pilaster_EastE_%d" % int(lz_p * 10), Vector3(0.30, 4.6, 0.50), Vector3(23.74, 2.3, lz_p), _mat_concrete)
	# Continuous Concrete Baseboard Plinths (visual skirt along base of interior walls)
	_add_visual_box("Skirt_ReactorN1", Vector3(13.0, 0.22, 0.14), Vector3(-17.3, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_ReactorN2", Vector3(16.4, 0.22, 0.14), Vector3(0.0, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_ReactorN3", Vector3(13.0, 0.22, 0.14), Vector3(17.3, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_SpawnN1", Vector3(11.2, 0.22, 0.14), Vector3(-4.2, 0.11, -7.72), _mat_concrete)
	_add_visual_box("Skirt_SpawnN2", Vector3(4.8, 0.22, 0.14), Vector3(7.4, 0.11, -7.72), _mat_concrete)


func _build_props_and_atmosphere() -> void:
	# Glowing Full Moon & Atmospheric Halo in Night Sky above Spawn North-West bombed skyline
	_add_full_moon(Vector3(-15.0, 34.0, -56.0), 2.35)

	# Overhead Perforated Steel Gantry Bridge spanning Spawn Courtyard across sky
	_place_visual_model("res://assets/models/env/steel_gantry.glb", Vector3(-5.0, 4.56, -0.8), 0.0)
	_place_visual_model("res://assets/models/env/steel_gantry.glb", Vector3(5.0, 4.56, -0.8), 0.0)

	# Mounted Industrial Pipe Manifolds, Valves & Pressure Gauges along concrete walls
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-6.0, 2.45, -21.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(0.0, 3.65, -21.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(6.5, 3.25, -21.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-23.74, 2.45, -1.8), 90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-19.5, 2.45, -7.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(23.74, 2.45, -1.5), -90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(19.5, 2.45, -7.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-3.8, 2.60, -7.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-9.74, 2.60, -4.4), 90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(9.74, 2.60, -4.4), -90.0)

	# Perimeter Bombed Rubble Piles & Barbed Wire Entanglements (kept clear of NavMesh center & doorways!)
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(7.4, 0.0, -6.7), -28.0, Vector3(1.8, 0.7, 1.1), Vector3(0, 0.35, 0))
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(-3.5, 0.0, -7.0), 14.0, Vector3(1.8, 0.7, 1.1), Vector3(0, 0.35, 0))
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(-22.2, 0.0, -6.6), 36.0, Vector3(1.6, 0.65, 1.0), Vector3(0, 0.32, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(-8.85, 0.0, -4.4), 90.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(8.85, 0.0, -2.9), 90.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(8.4, 0.0, 8.4), -42.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))

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
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-1.4, 0.0, -20.5), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(4.4, 0.0, -20.5), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(11.5, 0.0, -13.8), 30.0, Vector3(1.1, 1.2, 1.1), Vector3(0, 0.5, 0), Color(0.1, 0.95, 1.0), 1.8)
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(7.0, 0.0, -13.0), 15.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(-7.0, 0.0, -13.5), -14.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))

	# Moonlight Volumetric Cones streaming over Spawn Courtyard through broken upper windows
	_add_light_shaft(Vector3(-1.5, 3.6, -1.0), Vector3(18, 0, -12), 2.4, 9.0)
	_add_light_shaft(Vector3(3.2, 3.6, 1.8), Vector3(18, 0, -12), 2.0, 9.0)
	_add_light_shaft(Vector3(-4.8, 5.0, -5.2), Vector3(-22, 0, 10), 1.5, 8.0)
	_add_light_shaft(Vector3(4.2, 5.0, -5.2), Vector3(-22, 0, 10), 1.5, 8.0)

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


func _build_facility_details() -> void:
	# On-wall art does not change the playable floor or navigation geometry.
	var details := Node3D.new()
	details.name = "FacilityDetails"
	geo_root.add_child(details)
	var arch := preload("res://assets/models/env/containment_arch.glb")
	for spec in [
		[Vector3(-10, 0, 0), 90.0, "01 / BIO-LAB", Color(0.35, 0.85, 0.78)],
		[Vector3(10, 0, 0), -90.0, "02 / FOUNDRY", Color(1.0, 0.65, 0.27)],
		[Vector3(-15, 0, -8), 0.0, "03 / REACTOR", Color(1.0, 0.65, 0.27)],
		[Vector3(17, 0, -8), 0.0, "03 / REACTOR", Color(1.0, 0.65, 0.27)],
		[Vector3(3.2, 0, -8), 0.0, "EMERGENCY / POWER LOCK", Color(0.75, 0.85, 0.9)],
	]:
		var doorway := Node3D.new()
		doorway.position = spec[0]
		doorway.rotation_degrees.y = spec[1]
		details.add_child(doorway)
		doorway.add_child(arch.instantiate())
		var sign := Label3D.new()
		sign.text = spec[2]
		sign.position = Vector3(0, 3.92, 0.39)
		sign.font_size = 48
		sign.pixel_size = 0.0018
		sign.modulate = spec[3]
		sign.outline_size = 8
		doorway.add_child(sign)
	var pipe := preload("res://assets/models/env/service_pipes.glb")
	for x in [-20.5, -15.5, 13.0, 18.0]:
		var inst := pipe.instantiate() as Node3D
		inst.position = Vector3(x, 3.85, -21.55)
		details.add_child(inst)
	for x in [-9.55, 9.55]:
		var inst := pipe.instantiate() as Node3D
		inst.position = Vector3(x, 3.35, 3.8)
		inst.rotation_degrees.y = 90.0 if x < 0.0 else -90.0
		details.add_child(inst)


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


func _place_visual_model(model_path: String, pos: Vector3, rot_y_deg: float, s: float = 1.0) -> void:
	if not ResourceLoader.exists(model_path):
		return
	var holder := Node3D.new()
	holder.position = pos
	holder.rotation_degrees.y = rot_y_deg
	holder.scale = Vector3.ONE * s
	holder.add_child((load(model_path) as PackedScene).instantiate())
	geo_root.add_child(holder)


func _add_full_moon(pos: Vector3, radius: float) -> void:
	var disc := MeshInstance3D.new()
	disc.name = "FullMoonDisc"
	disc.position = pos
	disc.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://assets/shaders/moon_disc.gdshader")
	sm.material = mat
	disc.mesh = sm
	geo_root.add_child(disc)

	var halo := MeshInstance3D.new()
	halo.name = "MoonHalo"
	halo.position = pos
	halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var hm := SphereMesh.new()
	hm.radius = radius * 3.0
	hm.height = radius * 6.0
	var hmat := ShaderMaterial.new()
	hmat.shader = preload("res://assets/shaders/moon_halo.gdshader")
	hm.material = hmat
	halo.mesh = hm
	geo_root.add_child(halo)


func _build_ruined_story(p1: Vector2, p2: Vector2, base_y: float, thick: float, win_fracs: Array, gap_t0: float, gap_t1: float) -> void:
	var delta := p2 - p1
	var total_len := delta.length()
	if total_len < 1.0:
		return
	var root := Node3D.new()
	var mid := (p1 + p2) * 0.5
	root.position = Vector3(mid.x, base_y, mid.y)
	root.rotation.y = -delta.angle()
	geo_root.add_child(root)

	var add_local := func(sz: Vector3, lpos: Vector3, mat: Material, rot_deg: Vector3 = Vector3.ZERO) -> void:
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = sz
		bm.material = mat
		mi.mesh = bm
		mi.position = lpos
		mi.rotation_degrees = rot_deg
		root.add_child(mi)

	# Continuous weathered concrete cornice belt dividing 1st floor concrete from 2nd floor brick
	add_local.call(Vector3(total_len + 0.35, 0.24, thick + 0.24), Vector3(0, 0.12, 0), _mat_concrete)

	# Build segmented spans along local X in [-total_len/2 .. +total_len/2]
	var win_half_w := 0.88
	var x_start := -total_len * 0.5
	var x_end := total_len * 0.5
	var win_xs: Array[float] = []
	for wf in win_fracs:
		var wx := x_start + float(wf) * total_len
		if gap_t0 >= 0.0 and float(wf) >= gap_t0 and float(wf) <= gap_t1:
			continue
		win_xs.append(wx)

	var cur_x := x_start
	var seg_idx := 0
	for wx in win_xs:
		var pier_end := wx - win_half_w
		if pier_end > cur_x + 0.15:
			_add_ruined_pier_span(add_local, cur_x, pier_end, total_len, thick, gap_t0, gap_t1, seg_idx)
			seg_idx += 1
		# Window sill, boarded planks, header & rugged top masonry
		var ww := win_half_w * 2.0
		add_local.call(Vector3(ww + 0.08, 0.86, thick), Vector3(wx, 0.67, 0), _mat_brick)
		add_local.call(Vector3(ww + 0.24, 0.12, thick + 0.12), Vector3(wx, 1.12, 0), _mat_concrete)
		add_local.call(Vector3(ww + 0.22, 0.22, thick + 0.10), Vector3(wx, 3.24, 0), _mat_concrete)
		var par_h := 0.45 + 0.30 * fmod(absf(wx * 0.37), 1.0)
		add_local.call(Vector3(ww + 0.08, par_h, thick), Vector3(wx, 3.35 + par_h * 0.5, 0), _mat_brick)
		# Crooked nailed planks across upper window opening
		add_local.call(Vector3(ww + 0.16, 0.15, 0.05), Vector3(wx, 1.56, 0.02), _mat_wood, Vector3(0, 0, -9.0 + (seg_idx % 3) * 6.0))
		add_local.call(Vector3(ww + 0.16, 0.15, 0.05), Vector3(wx, 2.38, -0.02), _mat_wood, Vector3(0, 0, 11.0 - (seg_idx % 2) * 8.0))
		cur_x = wx + win_half_w

	if x_end > cur_x + 0.15:
		_add_ruined_pier_span(add_local, cur_x, x_end, total_len, thick, gap_t0, gap_t1, seg_idx)


func _add_ruined_pier_span(add_local: Callable, x0: float, x1: float, total_len: float, thick: float, gap_t0: float, gap_t1: float, seed_idx: int) -> void:
	# Split pier span into 1.4m jagged brick battlements, dipping sharply inside any moon skylight gap
	var pos_x := x0
	var chunk_i := 0
	while pos_x < x1 - 0.1:
		var nxt := minf(x1, pos_x + 1.5)
		var cx := (pos_x + nxt) * 0.5
		var cw := nxt - pos_x
		var frac := (cx + total_len * 0.5) / total_len
		var in_gap := (gap_t0 >= 0.0 and frac >= gap_t0 and frac <= gap_t1)
		var top_y := 1.45 + 0.45 * sin(cx * 1.1) if in_gap else 3.65 + 0.55 * sin(cx * 0.75 + seed_idx)
		var bh := top_y - 0.24
		if bh > 0.15:
			add_local.call(Vector3(cw + 0.02, bh, thick), Vector3(cx, 0.24 + bh * 0.5, 0), _mat_brick)
		# Protruding twisted dark rebar spikes along ragged roofline
		if (chunk_i + seed_idx) % 2 == 0:
			add_local.call(Vector3(0.035, 0.72, 0.035), Vector3(cx - 0.15, top_y + 0.28, 0.04), _mat_steel, Vector3(12, 0, -18))
			add_local.call(Vector3(0.035, 0.58, 0.035), Vector3(cx + 0.18, top_y + 0.22, -0.05), _mat_steel, Vector3(-14, 0, 22))
		pos_x = nxt
		chunk_i += 1


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

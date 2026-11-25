extends Node3D
class_name GameWorld

@onready var world_env: WorldEnvironment = $WorldEnvironment
@onready var moon_light: DirectionalLight3D = $MoonLight
@onready var geo_root: Node3D = $LevelGeometry

var _power_lights: Array[OmniLight3D] = []
var _alarm_lights: Array[OmniLight3D] = []
var _flicker_lights: Array[Dictionary] = []
var _vent_fans: Array[Node3D] = []
var _probes: Array[ReflectionProbe] = []
var _decals: Array[Decal] = []

var _fog_base_color := Color(0.08, 0.10, 0.14, 1.0)
var _fog_dog_color := Color(0.28, 0.09, 0.04, 1.0)
var _pulse_t: float = 0.0

var _env_pbr_shader: Shader = preload("res://assets/shaders/env_world_pbr.gdshader")
var _mat_cobble: ShaderMaterial
var _mat_concrete: ShaderMaterial
var _mat_roof_concrete: ShaderMaterial
var _mat_concrete_floor: ShaderMaterial
var _mat_brick: ShaderMaterial
var _mat_tile: ShaderMaterial
var _mat_steel: ShaderMaterial
var _mat_metal_floor: ShaderMaterial
var _mat_corrugated: ShaderMaterial
var _mat_roof_corrugated: ShaderMaterial
var _mat_wood: ShaderMaterial
var _mat_asphalt: ShaderMaterial
var _mat_earth: ShaderMaterial
var _light_shaft_mat: ShaderMaterial
var _street_bulb_mat: StandardMaterial3D
var _street_bulb_mesh: SphereMesh
var _env_fx_particles: Array[GPUParticles3D] = []
var _arch_batching: bool = false
var _arch_batches: Dictionary = {}
var _unit_box_mesh: BoxMesh
var _shaft_sts: Dictionary = {}
var _prewarmed_resources: Array[Resource] = []


func _enter_tree() -> void:
	# Ensure Zone 5 starts locked even before GameManager pre-populates its map
	if not GameManager.unlocked_zones.has("north_yard"):
		GameManager.unlocked_zones["north_yard"] = false


func _ready() -> void:
	SettingsManager.settings_changed.connect(_apply_graphics_settings)
	GameManager.power_activated.connect(_on_power_activated)
	GameManager.round_changed.connect(_on_round_changed)

	_prewarm_resources()
	_init_materials()
	_build_facility_architecture()
	_build_props_and_atmosphere()
	_build_facility_details()
	_build_reflection_probes_and_decals()
	_build_env_fx()
	_bake_zone_navigation()
	_apply_graphics_settings()
	AudioManager.start_ambience()


func _process(delta: float) -> void:
	_pulse_t += delta
	if not GameManager.power_on:
		var pulse := 0.8 + 0.7 * sin(_pulse_t * 3.8)
		for l in _alarm_lights:
			l.light_energy = pulse

	for entry in _flicker_lights:
		var light := entry["light"] as Light3D
		if not is_instance_valid(light):
			continue
		var base_e := float(entry["base"])
		var spd := float(entry["speed"])
		var ph := float(entry["phase"])
		var n := 0.5 + 0.35 * sin(_pulse_t * spd + ph) + 0.15 * sin(_pulse_t * (spd * 2.7) + ph * 1.9)
		var dip := 0.58 if sin(_pulse_t * 1.9 + ph) > 0.86 else 1.0
		light.light_energy = base_e * lerpf(0.76, 1.08, n) * dip

	for fan in _vent_fans:
		if is_instance_valid(fan):
			fan.rotate_z(delta * 5.4)


func _init_materials() -> void:
	_mat_cobble = _make_world_mat(
		"res://assets/textures/env/cc0_cobble_albedo.jpg",
		"res://assets/textures/env/cc0_cobble_normal.jpg",
		"res://assets/textures/env/cc0_cobble_roughness.jpg",
		0.40, Color(0.50, 0.54, 0.62), true, 0.46, 0.0, 0.0, 0.28,
		"res://assets/textures/env/cc0_mud_albedo.jpg",
		"res://assets/textures/env/cc0_mud_normal.jpg",
		"res://assets/textures/env/cc0_mud_roughness.jpg",
		0.18, Color(0.42, 0.39, 0.36)
	)
	_mat_cobble.set_shader_parameter("normal_strength", 1.35)

	_mat_tile = _make_world_mat(
		"res://assets/textures/env/cc0_lab_tile_albedo.jpg",
		"res://assets/textures/env/cc0_lab_tile_normal.jpg",
		"res://assets/textures/env/cc0_lab_tile_roughness.jpg",
		0.34, Color(0.76, 0.80, 0.84), true, 0.22, 0.0, 0.0, 0.50
	)
	_mat_tile.set_shader_parameter("roughness_scale", 0.80)

	_mat_metal_floor = _make_world_mat(
		"res://assets/textures/env/cc0_metal_plate_albedo.jpg",
		"res://assets/textures/env/cc0_metal_plate_normal.jpg",
		"res://assets/textures/env/cc0_metal_plate_roughness.jpg",
		0.48, Color(0.78, 0.80, 0.82), true, 0.24, 0.0, 0.38, 0.58
	)
	_mat_metal_floor.set_shader_parameter("roughness_scale", 0.86)

	_mat_concrete_floor = _make_world_mat(
		"res://assets/textures/env/cc0_concrete_floor_albedo.jpg",
		"res://assets/textures/env/cc0_concrete_floor_normal.jpg",
		"res://assets/textures/env/cc0_concrete_floor_roughness.jpg",
		0.32, Color(0.64, 0.67, 0.71), true, 0.30, 0.0, 0.0, 0.40
	)

	_mat_asphalt = _make_world_mat(
		"res://assets/textures/env/cc0_asphalt_albedo.jpg",
		"res://assets/textures/env/cc0_asphalt_normal.jpg",
		"res://assets/textures/env/cc0_asphalt_roughness.jpg",
		0.34, Color(0.54, 0.58, 0.64), true, 0.54, 0.0, 0.0, 0.34,
		"res://assets/textures/env/cc0_mud_albedo.jpg",
		"res://assets/textures/env/cc0_mud_normal.jpg",
		"res://assets/textures/env/cc0_mud_roughness.jpg",
		0.36, Color(0.46, 0.42, 0.38)
	)
	_mat_asphalt.set_shader_parameter("normal_strength", 1.25)

	_mat_concrete = _make_world_mat(
		"res://assets/textures/env/cc0_concrete_wall_albedo.jpg",
		"res://assets/textures/env/cc0_concrete_wall_normal.jpg",
		"res://assets/textures/env/cc0_concrete_wall_roughness.jpg",
		0.28, Color(0.62, 0.65, 0.69), false, 0.0, 0.52, 0.0, 0.38
	)
	_mat_concrete.set_shader_parameter("wall_damp_height", 1.25)
	_mat_concrete.set_shader_parameter("wall_top_grime_y", 4.8)

	_mat_roof_concrete = _make_world_mat(
		"res://assets/textures/env/cc0_concrete_wall_albedo.jpg",
		"res://assets/textures/env/cc0_concrete_wall_normal.jpg",
		"res://assets/textures/env/cc0_concrete_wall_roughness.jpg",
		0.18, Color(0.56, 0.59, 0.63), false, 0.0, 0.0, 0.0, 0.32
	)
	_mat_roof_concrete.set_shader_parameter("normal_strength", 0.35)
	_mat_roof_concrete.set_shader_parameter("macro_variation", 0.24)

	_mat_brick = _make_world_mat(
		"res://assets/textures/env/cc0_brick_albedo.jpg",
		"res://assets/textures/env/cc0_brick_normal.jpg",
		"res://assets/textures/env/cc0_brick_roughness.jpg",
		0.36, Color(0.80, 0.74, 0.70), false, 0.0, 0.34, 0.0, 0.38
	)
	_mat_brick.set_shader_parameter("wall_damp_height", 0.45)
	_mat_brick.set_shader_parameter("wall_top_grime_y", 8.6)

	_mat_steel = _make_world_mat(
		"res://assets/textures/env/cc0_rust_steel_albedo.jpg",
		"res://assets/textures/env/cc0_rust_steel_normal.jpg",
		"res://assets/textures/env/cc0_rust_steel_roughness.jpg",
		0.40, Color(0.78, 0.76, 0.74), false, 0.0, 0.32, 0.55, 0.52
	)
	_mat_steel.set_shader_parameter("roughness_scale", 0.86)

	_mat_corrugated = _make_world_mat(
		"res://assets/textures/env/cc0_corrugated_albedo.jpg",
		"res://assets/textures/env/cc0_corrugated_normal.jpg",
		"res://assets/textures/env/cc0_corrugated_roughness.jpg",
		0.22, Color(0.74, 0.71, 0.68), false, 0.0, 0.24, 0.45, 0.48
	)
	_mat_corrugated.set_shader_parameter("normal_strength", 0.55)
	_mat_corrugated.set_shader_parameter("roughness_scale", 0.85)

	_mat_roof_corrugated = _make_world_mat(
		"res://assets/textures/env/cc0_corrugated_albedo.jpg",
		"res://assets/textures/env/cc0_corrugated_normal.jpg",
		"res://assets/textures/env/cc0_corrugated_roughness.jpg",
		0.14, Color(0.58, 0.58, 0.60), false, 0.0, 0.0, 0.38, 0.34
	)
	_mat_roof_corrugated.set_shader_parameter("normal_strength", 0.30)
	_mat_roof_corrugated.set_shader_parameter("roughness_scale", 0.90)

	_mat_wood = _make_world_mat(
		"res://assets/textures/env/cc0_planks_albedo.jpg",
		"res://assets/textures/env/cc0_planks_normal.jpg",
		"res://assets/textures/env/cc0_planks_roughness.jpg",
		0.48, Color(0.58, 0.50, 0.44), false, 0.0, 0.22, 0.0, 0.32
	)

	_mat_earth = _make_world_mat(
		"res://assets/textures/env/cc0_mud_albedo.jpg",
		"res://assets/textures/env/cc0_mud_normal.jpg",
		"res://assets/textures/env/cc0_mud_roughness.jpg",
		0.26, Color(0.40, 0.38, 0.35), true, 0.26, 0.0, 0.0, 0.35
	)

	_light_shaft_mat = ShaderMaterial.new()
	_light_shaft_mat.shader = preload("res://assets/shaders/light_shaft.gdshader")
	_light_shaft_mat.set_shader_parameter("shaft_color", Color(0.58, 0.76, 0.96, 0.058))


func _make_world_mat(
	alb: String,
	nrm: String,
	rgh: String,
	uv_scale: float,
	tint: Color,
	is_floor: bool,
	puddle: float,
	damp: float,
	met: float = 0.0,
	spec: float = 0.45,
	alt_alb: String = "",
	alt_nrm: String = "",
	alt_rgh: String = "",
	alt_blend: float = 0.0,
	alt_tint: Color = Color.WHITE
) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = _env_pbr_shader
	mat.set_shader_parameter("albedo_tint", tint)
	if ResourceLoader.exists(alb):
		mat.set_shader_parameter("albedo_tex", load(alb))
	if ResourceLoader.exists(nrm):
		mat.set_shader_parameter("normal_tex", load(nrm))
	if ResourceLoader.exists(rgh):
		mat.set_shader_parameter("roughness_tex", load(rgh))
	mat.set_shader_parameter("uv_scale", uv_scale)
	mat.set_shader_parameter("normal_strength", 0.95)
	mat.set_shader_parameter("metallic_val", met)
	mat.set_shader_parameter("specular_val", spec)
	mat.set_shader_parameter("is_floor", is_floor)
	mat.set_shader_parameter("puddle_amount", puddle)
	mat.set_shader_parameter("wall_damp_strength", damp)
	mat.set_shader_parameter("macro_variation", 0.34)
	if alt_blend > 0.001 and ResourceLoader.exists(alt_alb):
		mat.set_shader_parameter("use_alt_layer", true)
		mat.set_shader_parameter("alt_albedo_tex", load(alt_alb))
		if ResourceLoader.exists(alt_nrm):
			mat.set_shader_parameter("alt_normal_tex", load(alt_nrm))
		if ResourceLoader.exists(alt_rgh):
			mat.set_shader_parameter("alt_roughness_tex", load(alt_rgh))
		mat.set_shader_parameter("alt_blend_amount", alt_blend)
		mat.set_shader_parameter("alt_tint", alt_tint)
	return mat


func _build_facility_architecture() -> void:
	# Global smooth ground collider covering Zones 1-5 + outside zombie window approach (X:-42..42, Z:-56..27)
	var foundation := StaticBody3D.new()
	foundation.name = "Foundation"
	foundation.collision_layer = 1
	foundation.collision_mask = 0
	foundation.add_to_group("nav_bake")
	var fcol := CollisionShape3D.new()
	var fbox := BoxShape3D.new()
	fbox.size = Vector3(84.0, 0.4, 83.0)
	fcol.shape = fbox
	fcol.position = Vector3(0.0, -0.2, -14.5)
	foundation.add_child(fcol)
	geo_root.add_child(foundation)

	# Outer dark mud terrain slightly below floor level to avoid Z-fighting
	_add_visual_box("OuterEarth", Vector3(84.0, 0.1, 83.0), Vector3(0.0, -0.07, -14.5), _mat_earth)

	# Zone Visual Floors at Y = 0.0 (top face 0.002)
	_add_visual_box("Floor_Spawn", Vector3(20.0, 0.04, 18.0), Vector3(0.0, -0.018, 1.0), _mat_cobble)
	_add_visual_box("Floor_Lab", Vector3(14.0, 0.04, 16.0), Vector3(-17.0, -0.018, 0.0), _mat_tile)
	_add_visual_box("Floor_East", Vector3(14.0, 0.04, 16.0), Vector3(17.0, -0.018, 0.0), _mat_metal_floor)
	_add_visual_box("Floor_Reactor", Vector3(48.0, 0.04, 14.0), Vector3(0.0, -0.018, -15.0), _mat_concrete_floor)
	_add_visual_box("Floor_NorthYard_Bay", Vector3(12.0, 0.04, 6.0), Vector3(18.0, -0.018, -25.0), _mat_concrete_floor)
	_add_visual_box("Floor_NorthYard", Vector3(36.0, 0.04, 14.0), Vector3(6.0, -0.018, -35.0), _mat_asphalt)

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
	_add_wall(Vector2(-24.0, -8.0), Vector2(-16.7, -8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-13.3, -8.0), Vector2(-10.0, -8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-16.7, -8.0), Vector2(-13.3, -8.0), 3.2, 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-10.0, -8.0), Vector2(1.5, -8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(4.9, -8.0), Vector2(10.0, -8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(1.5, -8.0), Vector2(4.9, -8.0), 3.2, 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(10.0, -8.0), Vector2(15.3, -8.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(18.7, -8.0), Vector2(24.0, -8.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(15.3, -8.0), Vector2(18.7, -8.0), 3.2, 4.6, 0.5, _mat_concrete)

	# Electro-Trap Choke Archway inside East Courtyard (Z=-2.8, archway X in [15.2..18.8])
	_add_wall(Vector2(10.25, -2.8), Vector2(15.2, -2.8), 4.6, 0.5, _mat_steel)
	_add_wall(Vector2(18.8, -2.8), Vector2(23.75, -2.8), 4.6, 0.5, _mat_steel)
	_add_header(Vector2(15.2, -2.8), Vector2(18.8, -2.8), 2.8, 4.6, 0.5, _mat_steel)

	# Reactor Outer Walls (X=-24, X=+24, Z=-22 with 2 North Windows at X=-9.5, X=+9.5 and DoorReactorNorth at X=16.5)
	_add_wall(Vector2(-24.0, -22.0), Vector2(-24.0, -8.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(24.0, -22.0), Vector2(24.0, -8.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(-24.0, -22.0), Vector2(-10.65, -22.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(-8.35, -22.0), Vector2(8.35, -22.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(10.65, -22.0), Vector2(14.8, -22.0), 5.2, 0.5, _mat_concrete)
	_add_wall(Vector2(18.2, -22.0), Vector2(24.0, -22.0), 5.2, 0.5, _mat_concrete)
	_add_header(Vector2(-10.65, -22.0), Vector2(-8.35, -22.0), 2.82, 5.2, 0.5, _mat_concrete)
	_add_header(Vector2(8.35, -22.0), Vector2(10.65, -22.0), 2.82, 5.2, 0.5, _mat_concrete)
	_add_header(Vector2(14.8, -22.0), Vector2(18.2, -22.0), 3.2, 5.2, 0.5, _mat_concrete)

	# Zone 5: Ruined Motorpool / Research Courtyard (north_yard)
	# Entry Bay X:12..24, Z:-22..-28 (leaves X:-12..+12, Z:-22..-28 outside alley unobstructed for WinReactorW/E!)
	_add_wall(Vector2(24.0, -22.0), Vector2(24.0, -42.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(12.0, -22.0), Vector2(12.0, -28.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-12.0, -28.0), Vector2(12.0, -28.0), 4.6, 0.5, _mat_concrete)
	# North Yard West Wall (X=-12, Z=-28..-42 with WinNorthYardW at Z=-35)
	_add_wall(Vector2(-12.0, -28.0), Vector2(-12.0, -33.85), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(-12.0, -36.15), Vector2(-12.0, -42.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(-12.0, -33.85), Vector2(-12.0, -36.15), 2.82, 4.6, 0.5, _mat_concrete)
	# North Yard North Wall (Z=-42, X=-12..24 with WinNorthYardN at X=4)
	_add_wall(Vector2(-12.0, -42.0), Vector2(2.85, -42.0), 4.6, 0.5, _mat_concrete)
	_add_wall(Vector2(5.15, -42.0), Vector2(24.0, -42.0), 4.6, 0.5, _mat_concrete)
	_add_header(Vector2(2.85, -42.0), Vector2(5.15, -42.0), 2.82, 4.6, 0.5, _mat_concrete)

	# Roofs & Structural Ceiling Beams (dedicated low-grain roof shaders)
	_add_static_box("Roof_Lab", Vector3(14.5, 0.3, 16.5), Vector3(-17.0, 4.75, 0.0), _mat_roof_concrete)
	_add_static_box("Roof_Reactor", Vector3(48.5, 0.3, 14.5), Vector3(0.0, 5.35, -15.0), _mat_roof_concrete)
	_add_static_box("Roof_Spawn_S", Vector3(20.5, 0.3, 4.4), Vector3(0.0, 4.75, 8.0), _mat_roof_concrete)
	_add_static_box("Roof_Spawn_N", Vector3(20.5, 0.3, 3.0), Vector3(0.0, 4.75, -6.5), _mat_roof_concrete)
	_arch_batching = true
	_add_visual_box("Rafter_StubL", Vector3(6.2, 0.24, 0.32), Vector3(-6.9, 4.62, 3.2), _mat_wood)
	_add_visual_box("Rafter_StubR", Vector3(5.6, 0.24, 0.32), Vector3(7.2, 4.62, 3.2), _mat_wood)
	_add_static_box("Roof_East_S", Vector3(14.5, 0.3, 9.0), Vector3(17.0, 4.75, 3.5), _mat_roof_corrugated)
	# Zone 5 Covered Garage Bay + Corrugated Overhang Roof (west yard remains open to HDRI sky)
	_add_static_box("Roof_NorthYard_Bay", Vector3(12.5, 0.3, 6.5), Vector3(18.0, 4.75, -25.0), _mat_roof_corrugated)
	_add_static_box("Roof_NorthYard_Garage", Vector3(12.3, 0.3, 14.5), Vector3(18.15, 4.75, -35.0), _mat_roof_corrugated)
	for ny_z in [-31.0, -35.0, -39.0]:
		_add_visual_box("Rafter_NorthYard_%d" % int(absf(ny_z)), Vector3(5.4, 0.24, 0.26), Vector3(10.6, 4.62, ny_z), _mat_wood)
	_add_visual_box("GarageEdgeBeam", Vector3(0.38, 0.48, 14.2), Vector3(12.15, 4.55, -35.0), _mat_steel)
	_add_visual_box("Threshold_NorthGarage", Vector3(11.8, 0.02, 0.24), Vector3(18.0, 0.008, -28.0), _mat_steel)

	# 2nd-Story Bombed Brick Courtyard Skyline around Spawn & North Yard
	_build_ruined_story(Vector2(-10.0, -8.0), Vector2(10.0, -8.0), 4.6, 0.52, [0.16, 0.62, 0.84], 0.28, 0.54)
	_build_ruined_story(Vector2(-10.0, -8.0), Vector2(-10.0, 10.0), 4.6, 0.52, [0.22, 0.52, 0.80], -1.0, -1.0)
	_build_ruined_story(Vector2(10.0, -8.0), Vector2(10.0, 10.0), 4.6, 0.52, [0.22, 0.52, 0.80], -1.0, -1.0)
	_build_ruined_story(Vector2(-10.0, 10.0), Vector2(10.0, 10.0), 4.6, 0.52, [0.25, 0.75], -1.0, -1.0)

	_build_ruined_story(Vector2(-12.0, -42.0), Vector2(24.0, -42.0), 4.6, 0.52, [0.18, 0.48, 0.78], -1.0, -1.0)
	_build_ruined_story(Vector2(-12.0, -28.0), Vector2(-12.0, -42.0), 4.6, 0.52, [0.25, 0.72], -1.0, -1.0)
	_build_ruined_story(Vector2(-12.0, -28.0), Vector2(12.0, -28.0), 4.6, 0.52, [0.22, 0.68], -1.0, -1.0)

	# Interior Structural Wall Pilasters, Baseboards & Ceiling I-Beams
	for rx in [-17.5, -13.0, -6.4, -0.1, 6.4, 12.6, 20.5]:
		_add_visual_box("Pilaster_Reactor_%d" % int(rx * 10), Vector3(0.54, 5.2, 0.32), Vector3(rx, 2.6, -21.74), _mat_concrete)
	for rx_b in [-16.0, -8.0, 0.0, 8.0, 16.0]:
		_add_visual_box("CeilingBeam_Reactor_%d" % int(rx_b), Vector3(0.36, 0.42, 13.8), Vector3(rx_b, 5.02, -15.0), _mat_steel)
	for lx_b in [-5.0, 0.0, 5.0]:
		_add_visual_box("CeilingBeam_Lab_%d" % int(lx_b), Vector3(13.6, 0.36, 0.34), Vector3(-17.0, 4.44, lx_b), _mat_steel)
	for lz_p in [-5.2, 5.2]:
		_add_visual_box("Pilaster_LabW_%d" % int(lz_p * 10), Vector3(0.30, 4.6, 0.50), Vector3(-23.74, 2.3, lz_p), _mat_concrete)
		_add_visual_box("Pilaster_EastE_%d" % int(lz_p * 10), Vector3(0.30, 4.6, 0.50), Vector3(23.74, 2.3, lz_p), _mat_concrete)
	for ny_p in [-2.0, 8.8, 17.5]:
		_add_visual_box("Pilaster_NorthYardN_%d" % int(ny_p * 10), Vector3(0.52, 4.6, 0.30), Vector3(ny_p, 2.3, -41.74), _mat_concrete)
	_add_visual_box("Pilaster_NorthYard_Corner", Vector3(0.42, 4.6, 0.42), Vector3(12.0, 2.3, -28.0), _mat_steel)

	# Continuous Concrete / Steel Baseboard Plinths
	_add_visual_box("Skirt_ReactorN1", Vector3(13.0, 0.22, 0.14), Vector3(-17.3, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_ReactorN2", Vector3(16.4, 0.22, 0.14), Vector3(0.0, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_ReactorN3a", Vector3(4.0, 0.22, 0.14), Vector3(12.75, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_ReactorN3b", Vector3(5.4, 0.22, 0.14), Vector3(21.0, 0.11, -21.72), _mat_steel)
	_add_visual_box("Skirt_SpawnN1", Vector3(11.2, 0.22, 0.14), Vector3(-4.2, 0.11, -7.72), _mat_concrete)
	_add_visual_box("Skirt_SpawnN2", Vector3(4.8, 0.22, 0.14), Vector3(7.4, 0.11, -7.72), _mat_concrete)
	_add_visual_box("Skirt_NorthYardS", Vector3(23.6, 0.22, 0.14), Vector3(0.0, 0.11, -28.28), _mat_concrete)
	_add_visual_box("Skirt_NorthYardE", Vector3(0.14, 0.22, 19.6), Vector3(23.72, 0.11, -32.0), _mat_steel)
	_arch_batching = false
	_flush_arch_batches()


func _build_props_and_atmosphere() -> void:
	# Glowing Full Moon & Atmospheric Halo visible through bombed roof skylights
	_add_full_moon(Vector3(-15.0, 34.0, -56.0), 2.35)

	# Overhead Perforated Steel Gantry Bridge spanning Spawn Courtyard
	_place_visual_model("res://assets/models/env/steel_gantry.glb", Vector3(-5.0, 4.56, -0.8), 0.0)
	_place_visual_model("res://assets/models/env/steel_gantry.glb", Vector3(5.0, 4.56, -0.8), 0.0)

	# Mounted Industrial Pipe Manifolds, Valves & Pressure Gauges along concrete walls (clear of all windows)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-6.0, 2.45, -21.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(0.0, 3.65, -21.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(6.5, 3.25, -21.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-23.74, 2.45, -4.8), 90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-19.5, 2.45, -7.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(23.74, 2.45, -5.2), -90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(19.5, 2.45, -7.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-3.8, 2.60, -7.74), 0.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-9.74, 2.60, -4.4), 90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(9.74, 2.60, -4.4), -90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(23.74, 2.55, -25.0), -90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(12.26, 2.55, -25.0), 90.0)

	# Perimeter Rubble & Barbed Wire
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(7.4, 0.0, -6.7), -28.0, Vector3(1.8, 0.7, 1.1), Vector3(0, 0.35, 0))
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(-3.5, 0.0, -7.0), 14.0, Vector3(1.8, 0.7, 1.1), Vector3(0, 0.35, 0))
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(-22.2, 0.0, -6.6), 36.0, Vector3(1.6, 0.65, 1.0), Vector3(0, 0.32, 0))
	_place_prop("res://assets/models/env/rubble_pile.glb", Vector3(-8.4, 0.0, -29.2), 22.0, Vector3(1.8, 0.7, 1.1), Vector3(0, 0.35, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(-8.85, 0.0, -4.4), 90.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(8.85, 0.0, -2.9), 90.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(8.4, 0.0, 8.4), -42.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))
	_place_prop("res://assets/models/env/barbed_wire.glb", Vector3(-5.8, 0.0, -40.8), 12.0, Vector3(2.0, 0.8, 0.7), Vector3(0, 0.4, 0))

	# === ZONE 1: SPAWN COURTYARD ===
	_place_prop("res://assets/models/env/ruined_tank.glb", Vector3(-1.4, 0.0, -2.0), 24.0, Vector3(3.0, 2.2, 5.2), Vector3(0, 1.1, 0))
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(2.8, 0.0, 0.6), -25.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(-6.2, 0.0, 1.8), 42.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env_cc0/concrete_road_barrier.glb", Vector3(-7.6, 0.0, 6.8), 28.0, Vector3(1.55, 0.85, 0.65), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env_cc0/concrete_road_barrier.glb", Vector3(7.4, 0.0, 7.2), -34.0, Vector3(1.55, 0.85, 0.65), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env_cc0/barrel_stove.glb", Vector3(-7.6, 0.0, -5.8), 15.0, Vector3(0.6, 0.88, 0.6), Vector3(0, 0.44, 0), Color(1.0, 0.48, 0.14), 1.45)
	_place_prop("res://assets/models/env_cc0/barrel_stove.glb", Vector3(8.0, 0.0, -4.6), -40.0, Vector3(0.6, 0.88, 0.6), Vector3(0, 0.44, 0), Color(1.0, 0.48, 0.14), 1.45)
	_place_prop("res://assets/models/env_cc0/ammo_box.glb", Vector3(3.2, 0.0, -0.2), -20.0, Vector3.ZERO, Vector3.ZERO)
	_place_prop("res://assets/models/env_cc0/ammo_box.glb", Vector3(-5.8, 0.0, 2.5), 38.0, Vector3.ZERO, Vector3.ZERO)
	_place_prop("res://assets/models/env_cc0/old_military_crate.glb", Vector3(6.6, 0.0, -5.2), 18.0, Vector3(1.8, 0.35, 0.96), Vector3(0, 0.17, 0))
	_place_prop("res://assets/models/env_cc0/barrel_01.glb", Vector3(-8.6, 0.0, -6.2), 0.0, Vector3(0.6, 0.9, 0.6), Vector3(0, 0.45, 0))
	_place_visual_model("res://assets/models/env_cc0/cement_bag.glb", Vector3(5.6, 0.0, -6.2), 26.0)
	_place_visual_model("res://assets/models/env_cc0/crowbar_01.glb", Vector3(3.75, 0.0, 0.92), 45.0)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(4.2, 0.0, -4.2), 15.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.92, 1.0), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(-6.8, 0.0, -5.8), -40.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.92, 1.0), 1.5)

	# === ZONE 2: WEST RESEARCH LAB ===
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-16.8, 0.0, -1.6), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-16.8, 0.0, 2.2), 180.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(-16.8, 0.0, 0.3), 25.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.95, 1.0), 1.7)
	_place_prop("res://assets/models/env_cc0/metal_office_desk.glb", Vector3(-22.2, 0.0, 2.4), 90.0, Vector3(2.0, 0.80, 0.95), Vector3(0, 0.40, 0))
	_place_visual_model("res://assets/models/env_cc0/chemistry_set.glb", Vector3(-22.15, 0.788, 2.1), 90.0)
	_place_visual_model("res://assets/models/env_cc0/bunsen_burner.glb", Vector3(-22.05, 0.788, 3.0), 25.0)
	_place_prop("res://assets/models/env_cc0/metal_office_desk.glb", Vector3(-11.8, 0.0, -5.4), -90.0, Vector3(2.0, 0.80, 0.95), Vector3(0, 0.40, 0))
	_place_visual_model("res://assets/models/env_cc0/vintage_radio_transceiver.glb", Vector3(-11.85, 0.788, -4.95), -90.0)
	_place_visual_model("res://assets/models/env_cc0/medical_box.glb", Vector3(-11.9, 0.788, -5.85), -70.0)
	_place_prop("res://assets/models/env_cc0/steel_frame_shelves_01.glb", Vector3(-10.8, 0.0, 5.8), -90.0, Vector3(1.1, 2.14, 0.52), Vector3(0, 1.07, 0))
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(-22.2, 0.0, 5.8), 10.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))
	_place_visual_model("res://assets/models/env_cc0/power_box_01.glb", Vector3(-10.26, 1.55, 3.8), -90.0)
	_place_visual_model("res://assets/models/env_cc0/hanging_industrial_lamp.glb", Vector3(-19.5, 4.6, -2.5), 0.0)
	_place_visual_model("res://assets/models/env_cc0/hanging_industrial_lamp.glb", Vector3(-14.5, 4.6, 3.5), 0.0)

	# === ZONE 3: EAST FOUNDRY COURTYARD ===
	_place_prop("res://assets/models/env_cc0/portable_welding_cart.glb", Vector3(22.4, 0.0, -1.2), -125.0, Vector3(0.84, 1.56, 0.66), Vector3(0, 0.78, 0))
	_place_prop("res://assets/models/env_cc0/drawer_cabinet.glb", Vector3(10.6, 0.0, 4.9), 90.0, Vector3(1.13, 1.88, 0.50), Vector3(0, 0.94, 0))
	_place_visual_model("res://assets/models/env_cc0/metal_toolbox.glb", Vector3(10.6, 1.88, 4.9), 75.0)
	_place_prop("res://assets/models/env_cc0/old_military_crate.glb", Vector3(21.4, 0.0, 6.4), -18.0, Vector3(1.8, 0.35, 0.96), Vector3(0, 0.17, 0))
	_place_prop("res://assets/models/env_cc0/barrel_02.glb", Vector3(22.6, 0.0, 5.2), 0.0, Vector3(0.54, 0.88, 0.54), Vector3(0, 0.44, 0))
	_place_prop("res://assets/models/env_cc0/barrel_01.glb", Vector3(11.3, 0.0, -1.3), 25.0, Vector3(0.58, 0.88, 0.58), Vector3(0, 0.44, 0))
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(21.0, 0.0, -6.2), 70.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.92, 1.0), 1.5)
	_place_visual_model("res://assets/models/env_cc0/caged_hanging_light.glb", Vector3(17.0, 4.6, 3.8), 90.0)

	# === ZONE 4: REACTOR HALL ===
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(-1.4, 0.0, -20.5), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/lab_pod.glb", Vector3(4.4, 0.0, -20.5), 0.0, Vector3(1.3, 2.5, 1.3), Vector3(0, 1.25, 0), Color(0.15, 0.95, 0.78), 1.6)
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(11.5, 0.0, -13.8), 30.0, Vector3(1.1, 1.2, 1.1), Vector3(0, 0.5, 0), Color(0.1, 0.95, 1.0), 1.8)
	_place_prop("res://assets/models/env/sandbag_wall.glb", Vector3(7.0, 0.0, -13.0), 15.0, Vector3(2.4, 0.85, 0.7), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/crate_military.glb", Vector3(-7.0, 0.0, -13.5), -14.0, Vector3(1.2, 0.85, 0.85), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env_cc0/metal_office_desk.glb", Vector3(-20.4, 0.0, -20.0), 18.0, Vector3(2.0, 0.80, 0.95), Vector3(0, 0.40, 0))
	_place_visual_model("res://assets/models/env_cc0/vintage_radio_transceiver.glb", Vector3(-20.4, 0.788, -20.0), 22.0)
	_place_visual_model("res://assets/models/env_cc0/ammo_box.glb", Vector3(-19.6, 0.788, -19.8), -15.0)
	_place_prop("res://assets/models/env_cc0/drawer_cabinet.glb", Vector3(-23.2, 0.0, -18.5), 90.0, Vector3(1.13, 1.88, 0.50), Vector3(0, 0.94, 0))
	_place_prop("res://assets/models/env_cc0/steel_frame_shelves_01.glb", Vector3(-23.2, 0.0, -9.8), 90.0, Vector3(1.1, 2.14, 0.52), Vector3(0, 1.07, 0))
	_place_prop("res://assets/models/env_cc0/steel_frame_shelves_01.glb", Vector3(23.2, 0.0, -19.8), -90.0, Vector3(1.1, 2.14, 0.52), Vector3(0, 1.07, 0))
	_place_prop("res://assets/models/env_cc0/portable_welding_cart.glb", Vector3(20.6, 0.0, -9.8), -145.0, Vector3(0.84, 1.56, 0.66), Vector3(0, 0.78, 0))
	_place_visual_model("res://assets/models/env_cc0/power_box_01.glb", Vector3(-5.3, 1.65, -21.74), 0.0)
	_place_visual_model("res://assets/models/env_cc0/power_box_01.glb", Vector3(6.2, 1.65, -21.74), 0.0)
	_place_visual_model("res://assets/models/env_cc0/hanging_industrial_lamp.glb", Vector3(-15.0, 5.2, -15.5), 0.0)
	_place_visual_model("res://assets/models/env_cc0/hanging_industrial_lamp.glb", Vector3(1.5, 5.2, -15.5), 0.0)
	_place_visual_model("res://assets/models/env_cc0/hanging_industrial_lamp.glb", Vector3(15.0, 5.2, -15.5), 0.0)

	# West reactor/teleporter corner: fill the bare walls with lab clutter & piping
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-23.74, 2.55, -14.8), 90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-23.74, 3.45, -17.6), 90.0)
	_place_visual_model("res://assets/models/env/wall_pipes.glb", Vector3(-14.0, 2.75, -21.74), 0.0)
	_place_prop("res://assets/models/env_cc0/metal_office_desk.glb", Vector3(-21.8, 0.0, -13.2), 90.0, Vector3(2.0, 0.80, 0.95), Vector3(0, 0.40, 0))
	_place_visual_model("res://assets/models/env_cc0/chemistry_set.glb", Vector3(-21.9, 0.788, -13.6), 115.0)
	_place_visual_model("res://assets/models/env_cc0/bunsen_burner.glb", Vector3(-21.7, 0.788, -12.7), -30.0)
	_place_prop("res://assets/models/env_cc0/drawer_cabinet.glb", Vector3(-23.2, 0.0, -11.0), 90.0, Vector3(1.13, 1.88, 0.50), Vector3(0, 0.94, 0))
	_place_prop("res://assets/models/env_cc0/steel_frame_shelves_01.glb", Vector3(-12.5, 0.0, -21.3), 0.0, Vector3(1.1, 2.14, 0.52), Vector3(0, 1.07, 0))
	_place_visual_model("res://assets/models/env_cc0/medical_box.glb", Vector3(-12.6, 1.1, -21.2), 12.0)
	_place_visual_model("res://assets/models/env_cc0/power_box_01.glb", Vector3(-17.8, 1.65, -21.74), 0.0)
	_place_visual_model("res://assets/models/env_cc0/hanging_industrial_lamp.glb", Vector3(-15.0, 5.2, -13.0), 0.0)

	# === ZONE 5: RUINED MOTORPOOL COURTYARD (north_yard) ===
	_place_prop("res://assets/models/env_cc0/covered_car.glb", Vector3(2.2, 0.0, -34.4), 24.0, Vector3(1.82, 1.42, 4.35), Vector3(0, 0.71, 0))
	_place_prop("res://assets/models/env_cc0/concrete_road_barrier_02.glb", Vector3(-4.6, 0.0, -31.8), 16.0, Vector3(1.56, 1.12, 0.45), Vector3(0, 0.56, 0))
	_place_prop("res://assets/models/env_cc0/concrete_road_barrier.glb", Vector3(9.4, 0.0, -35.8), -32.0, Vector3(1.55, 0.85, 0.65), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env_cc0/concrete_road_barrier_02.glb", Vector3(20.6, 0.0, -29.0), -16.0, Vector3(1.56, 1.12, 0.45), Vector3(0, 0.56, 0))
	_place_prop("res://assets/models/env_cc0/barrel_stove.glb", Vector3(-9.8, 0.0, -40.2), 20.0, Vector3(0.6, 0.88, 0.6), Vector3(0, 0.44, 0), Color(1.0, 0.50, 0.16), 1.55)
	_place_prop("res://assets/models/env_cc0/barrel_stove.glb", Vector3(22.2, 0.0, -39.2), -28.0, Vector3(0.6, 0.88, 0.6), Vector3(0, 0.44, 0), Color(1.0, 0.48, 0.14), 1.45)
	_place_prop("res://assets/models/env_cc0/industrial_storage_cart.glb", Vector3(22.3, 0.0, -35.0), -90.0, Vector3(1.48, 1.28, 1.02), Vector3(0, 0.64, 0))
	_place_visual_model("res://assets/models/env_cc0/metal_toolbox.glb", Vector3(22.2, 1.27, -34.6), -70.0)
	_place_prop("res://assets/models/env_cc0/steel_frame_shelves_01.glb", Vector3(22.6, 0.0, -25.4), -90.0, Vector3(1.1, 2.14, 0.52), Vector3(0, 1.07, 0))
	_place_prop("res://assets/models/env_cc0/barrel_01.glb", Vector3(13.0, 0.0, -25.6), 12.0, Vector3(0.58, 0.88, 0.58), Vector3(0, 0.44, 0))
	_place_prop("res://assets/models/env_cc0/barrel_02.glb", Vector3(13.2, 0.0, -24.7), -30.0, Vector3(0.54, 0.88, 0.54), Vector3(0, 0.44, 0))
	_place_prop("res://assets/models/env_cc0/old_military_crate.glb", Vector3(-6.2, 0.0, -39.6), -8.0, Vector3(1.8, 0.35, 0.96), Vector3(0, 0.17, 0))
	_place_visual_model("res://assets/models/env_cc0/cement_bag.glb", Vector3(-6.4, 0.30, -39.6), 14.0)
	_place_prop("res://assets/models/env_cc0/flood_lights.glb", Vector3(9.4, 0.0, -40.2), -48.0, Vector3(1.9, 0.85, 0.9), Vector3(0, 0.42, 0))
	_place_prop("res://assets/models/env/element115_crystal.glb", Vector3(-2.5, 0.0, -40.4), 35.0, Vector3(1.0, 1.1, 1.0), Vector3(0, 0.5, 0), Color(0.1, 0.95, 1.0), 1.65)
	_place_visual_model("res://assets/models/env_cc0/caged_hanging_light.glb", Vector3(18.0, 4.6, -25.0), 0.0)
	_place_visual_model("res://assets/models/env_cc0/caged_hanging_light.glb", Vector3(18.5, 4.6, -34.5), 90.0)

	# Street Lamps in North Yard (positioned cleanly along perimeter edges away from doorway sightline)
	for sl_pos in [Vector3(-10.8, 0.0, -39.2), Vector3(8.2, 0.0, -28.7)]:
		_add_street_lamp(sl_pos, 40.0 if sl_pos.x < 0.0 else 180.0)

	# Outside Silhouette Props visible through WindowBarricades & bombed walls (clear of window approach lanes)
	for out_tree in [
		[Vector3(-10.5, 0.0, 16.5), 25.0],
		[Vector3(10.5, 0.0, 16.8), -40.0],
		[Vector3(-29.2, 0.0, -5.8), 65.0],
		[Vector3(29.2, 0.0, -4.8), -75.0],
		[Vector3(-17.8, 0.0, -30.2), 18.0],
		[Vector3(-6.2, 0.0, -47.8), 12.0],
		[Vector3(17.5, 0.0, -47.2), -32.0],
	]:
		_place_visual_model("res://assets/models/env_cc0/dead_tree_trunk.glb", out_tree[0], out_tree[1], 1.15)
	for out_rock in [
		[Vector3(0.0, 0.0, 17.5), 14.0, 1.2],
		[Vector3(-29.5, 0.0, 5.5), 48.0, 1.1],
		[Vector3(29.0, 0.0, 6.8), -30.0, 1.05],
		[Vector3(-17.5, 0.0, -40.2), 20.0, 1.15],
		[Vector3(10.8, 0.0, -48.2), -55.0, 1.25],
	]:
		_place_visual_model("res://assets/models/env_cc0/boulder_01.glb", out_rock[0], out_rock[1], out_rock[2])

	# Moonlight Volumetric Cones streaming over Spawn Courtyard & North Yard
	_add_light_shaft(Vector3(-1.5, 3.6, -1.0), Vector3(18, 0, -12), 2.4, 9.0)
	_add_light_shaft(Vector3(3.2, 3.6, 1.8), Vector3(18, 0, -12), 2.0, 9.0)
	_add_light_shaft(Vector3(-4.8, 5.0, -5.2), Vector3(-22, 0, 10), 1.5, 8.0)
	_add_light_shaft(Vector3(4.2, 5.0, -5.2), Vector3(-22, 0, 10), 1.5, 8.0)
	_add_light_shaft(Vector3(1.5, 3.8, -34.5), Vector3(16, 0, -10), 2.5, 9.5)
	_add_light_shaft(Vector3(-6.2, 4.0, -34.8), Vector3(18, 0, 8), 1.9, 8.5)
	_flush_light_shafts()

	# Practical Cage/Industrial Wall & Ceiling Lights (omit light_cage mesh where CC0 hanging lamp sits)
	_add_cage_light(Vector3(0.0, 3.3, 9.68), 180.0, Color(1.0, 0.62, 0.24), 2.3, false, false, false, true)
	_add_cage_light(Vector3(-9.68, 3.3, 4.5), 90.0, Color(1.0, 0.62, 0.24), 2.2, false, false, true, true)
	_add_cage_light(Vector3(-23.68, 3.3, -4.5), 90.0, Color(0.35, 0.88, 1.0), 1.6, false, false, false, true)
	_add_cage_light(Vector3(-19.5, 4.6, -2.5), 0.0, Color(0.95, 0.90, 0.78), 1.6, true, true, false, false, -1.25)
	_add_cage_light(Vector3(-14.5, 4.6, 3.5), 0.0, Color(0.45, 0.92, 0.88), 1.8, true, true, false, false, -1.25)
	_add_cage_light(Vector3(-16.8, 4.56, 0.3), 0.0, Color(0.35, 0.92, 0.96), 1.9, true, true, false, false, -0.45)
	_add_cage_light(Vector3(17.0, 4.6, 3.8), 0.0, Color(1.0, 0.68, 0.32), 2.0, false, true, false, false, -0.78)
	_place_visual_model("res://assets/models/env_cc0/caged_hanging_light.glb", Vector3(17.0, 4.6, -5.5), 0.0)
	_add_cage_light(Vector3(17.0, 4.6, -5.5), 0.0, Color(1.0, 0.68, 0.32), 2.5, true, true, false, false, -0.78)
	_add_cage_light(Vector3(23.68, 3.3, -5.2), -90.0, Color(1.0, 0.62, 0.25), 1.7, false, false, true, true)
	_add_cage_light(Vector3(-15.0, 5.2, -15.5), 0.0, Color(0.45, 0.9, 1.0), 2.7, true, true, false, false, -1.32)
	_add_cage_light(Vector3(1.5, 5.2, -15.5), 0.0, Color(1.0, 0.85, 0.65), 3.0, true, true, false, false, -1.32)
	_add_cage_light(Vector3(15.0, 5.2, -15.5), 0.0, Color(1.0, 0.65, 0.28), 2.7, true, true, false, false, -1.32)
	_add_cage_light(Vector3(18.0, 4.6, -25.0), 0.0, Color(1.0, 0.68, 0.30), 2.2, false, true, true, false, -0.78)
	_add_cage_light(Vector3(18.5, 4.6, -34.5), 0.0, Color(1.0, 0.72, 0.35), 2.5, true, true, false, false, -0.78)

	# Warm Lab Task Light & Cool Moonlit Sky Bounce Fill in Open Spawn Courtyard
	var lab_task := OmniLight3D.new()
	lab_task.position = Vector3(-21.2, 2.55, 2.4)
	lab_task.light_color = Color(0.96, 0.90, 0.78)
	lab_task.light_energy = 1.45
	lab_task.omni_range = 6.5
	_setup_light_fade(lab_task, 22.0, 8.0)
	geo_root.add_child(lab_task)

	var spawn_sky_fill := OmniLight3D.new()
	spawn_sky_fill.position = Vector3(0.0, 4.4, 2.2)
	spawn_sky_fill.light_color = Color(0.44, 0.62, 0.90)
	spawn_sky_fill.light_energy = 0.72
	spawn_sky_fill.omni_range = 16.0
	_setup_light_fade(spawn_sky_fill, 28.0, 8.0)
	geo_root.add_child(spawn_sky_fill)

	# CC0 Industrial Wall Sconces framing main courtyard, foundry & north yard (each with warm downward bulb glow)
	for wlamp in [
		[Vector3(9.74, 3.1, 4.8), -90.0, Vector3(-0.28, -0.08, 0.0)],
		[Vector3(10.26, 3.1, -5.6), 90.0, Vector3(0.28, -0.08, 0.0)],
		[Vector3(-11.74, 3.1, -35.0), 90.0, Vector3(0.28, -0.08, 0.0)],
		[Vector3(4.0, 3.1, -28.26), 180.0, Vector3(0.0, -0.08, -0.28)],
	]:
		_place_visual_model("res://assets/models/env_cc0/industrial_wall_lamp.glb", wlamp[0], wlamp[1])
		var wl := OmniLight3D.new()
		wl.position = wlamp[0] + wlamp[2]
		wl.light_color = Color(1.0, 0.66, 0.28)
		wl.light_energy = 1.35
		wl.omni_range = 7.5
		_setup_light_fade(wl, 22.0, 8.0)
		geo_root.add_child(wl)

	# North Yard Floodlight SpotLight illuminating the Covered Car & crater
	var flood := SpotLight3D.new()
	flood.name = "MotorpoolFloodSpot"
	flood.position = Vector3(9.1, 0.65, -39.8)
	flood.look_at_from_position(flood.position, Vector3(2.2, 0.5, -34.4), Vector3.UP)
	flood.light_color = Color(0.82, 0.90, 1.0)
	flood.light_energy = 4.2
	flood.spot_range = 16.0
	flood.spot_angle = 36.0
	flood.spot_attenuation = 1.2
	_setup_light_fade(flood, 28.0, 8.0)
	geo_root.add_child(flood)

	# Alarm Red Lights active before Power Switch is pulled
	_add_alarm_light(Vector3(-3.5, 3.8, -19.5))
	_add_alarm_light(Vector3(-17.0, 3.8, -5.0))
	_add_alarm_light(Vector3(17.0, 3.8, -5.0))
	_add_alarm_light(Vector3(18.0, 3.6, -25.0))

	# Trashed window entries: broken planks & debris scattered inside every barricaded window
	for wspec in [
		[Vector3(-5.2, 0.02, 9.1), 0.0],
		[Vector3(5.2, 0.02, 9.1), 0.0],
		[Vector3(-23.1, 0.02, 0.0), 90.0],
		[Vector3(-17.0, 0.02, 7.1), 0.0],
		[Vector3(17.0, 0.02, 7.1), 0.0],
		[Vector3(23.1, 0.02, 1.5), 90.0],
		[Vector3(-9.5, 0.02, -21.1), 180.0],
		[Vector3(9.5, 0.02, -21.1), 180.0],
		[Vector3(-11.1, 0.02, -35.0), 90.0],
		[Vector3(4.0, 0.02, -41.1), 180.0],
	]:
		_scatter_plank_debris(wspec[0], wspec[1])

	# Interior corner rubble: collapsed ceiling plaster & brick inside Lab, East & Reactor corners
	for rspec in [
		[Vector3(-23.2, 0.0, -6.9), 58.0, 1.0],
		[Vector3(-10.9, 0.0, 7.0), -24.0, 0.8],
		[Vector3(23.0, 0.0, 7.0), 41.0, 0.9],
		[Vector3(10.9, 0.0, -6.8), 12.0, 0.75],
		[Vector3(-23.0, 0.0, -20.9), 77.0, 1.15],
		[Vector3(23.0, 0.0, -12.5), -33.0, 0.9],
		[Vector3(15.9, 0.0, -21.0), 20.0, 0.85],
	]:
		_place_prop("res://assets/models/env/rubble_pile.glb", rspec[0], rspec[1], Vector3(1.5, 0.62, 1.0) * rspec[2], Vector3(0, 0.30, 0))
	_scatter_floor_debris()
	_scatter_grime_decals()



func _scatter_grime_decals() -> void:
	# Grit layer: blood at the kill zones, grime bleeding down walls, oil & scorch.
	# Decals cost nearly nothing in Forward+ but do most of the "lived-in bunker" work.
	var blood := "res://assets/decals/decal_blood_splatter.png"
	var grime := "res://assets/decals/decal_grime_leak.png"
	var oil := "res://assets/decals/decal_oil_slick.png"
	var scorch := "res://assets/decals/decal_scorch_mark.png"
	var crack := "res://assets/decals/decal_wall_crack.png"
	var geo_root := get_node_or_null("Geometry")
	if geo_root == null:
		geo_root = self

	var place := func(tex_path: String, pos: Vector3, rot_deg: Vector3, size: Vector3, mix: float = 0.85) -> void:
		if not ResourceLoader.exists(tex_path):
			return
		var dec := Decal.new()
		dec.position = pos
		dec.rotation_degrees = rot_deg
		dec.size = size
		dec.texture_albedo = load(tex_path)
		dec.albedo_mix = mix
		dec.distance_fade_enabled = true
		dec.distance_fade_begin = 20.0
		dec.distance_fade_length = 7.0
		geo_root.add_child(dec)

	# Blood pools & sprays inside every barricaded window — the zombies bleed here
	for wpos in [
		Vector3(-5.2, 0.03, 8.3), Vector3(5.2, 0.03, 8.3),
		Vector3(-22.3, 0.03, 0.0), Vector3(-17.0, 0.03, 6.4),
		Vector3(17.0, 0.03, 6.4), Vector3(22.3, 0.03, 1.5),
		Vector3(-9.5, 0.03, -20.4), Vector3(9.5, 0.03, -20.4),
		Vector3(-10.5, 0.03, -35.0), Vector3(4.0, 0.03, -40.4),
	]:
		place.call(blood, wpos, Vector3.ZERO, Vector3(2.0, 0.2, 2.0), 0.8)

	# Dried blood trails through the main corridors — the outbreak happened here
	for bspec in [
		[Vector3(0.8, 0.03, 2.0), Vector3(1.6, 0.2, 2.6)],
		[Vector3(-3.2, 0.03, -8.5), Vector3(2.2, 0.2, 1.8)],
		[Vector3(2.5, 0.03, -14.8), Vector3(1.8, 0.2, 2.4)],
		[Vector3(-14.5, 0.03, -3.5), Vector3(2.4, 0.2, 2.0)],
		[Vector3(14.8, 0.03, -2.8), Vector3(2.0, 0.2, 2.2)],
		[Vector3(0.5, 0.03, -26.5), Vector3(2.6, 0.2, 2.2)],
	]:
		place.call(blood, bspec[0], Vector3.ZERO, bspec[1], 0.62)

	# Grime leaks bleeding down walls (east/west walls: rot z ±90, north/south: rot x ∓90)
	for gspec in [
		[Vector3(-10.9, 1.7, 4.5), Vector3(0, 0, 90), 2.6],
		[Vector3(10.9, 1.9, -3.0), Vector3(0, 0, -90), 3.2],
		[Vector3(-3.5, 1.6, -20.9), Vector3(-90, 0, 0), 2.8],
		[Vector3(6.5, 1.8, -20.9), Vector3(-90, 0, 0), 2.4],
		[Vector3(-22.9, 1.7, -4.2), Vector3(0, 0, 90), 3.0],
		[Vector3(22.9, 1.5, 4.0), Vector3(0, 0, -90), 2.6],
		[Vector3(-6.0, 1.8, 8.9), Vector3(90, 0, 0), 2.2],
		[Vector3(4.2, 1.6, 8.9), Vector3(90, 0, 0), 2.8],
		[Vector3(0.5, 1.9, -40.9), Vector3(-90, 0, 0), 3.4],
		[Vector3(-11.9, 1.6, -30.0), Vector3(0, 0, 90), 2.6],
	]:
		place.call(grime, gspec[0], gspec[1], Vector3(1.6, 0.3, gspec[2]), 0.7)

	# Wall cracks near the reactor & east wing — structural damage
	for cspec in [
		[Vector3(11.9, 2.0, -28.0), Vector3(0, 0, -90), 2.8],
		[Vector3(-18.0, 2.2, -21.0), Vector3(-90, 0, 0), 3.2],
		[Vector3(22.9, 2.1, -8.5), Vector3(0, 0, -90), 2.4],
	]:
		place.call(crack, cspec[0], cspec[1], Vector3(cspec[2], 0.3, cspec[2]), 0.75)

	# Oil slicks in motorpool / north yard, scorch marks near reactor & furnace areas
	for ospec in [
		[Vector3(3.0, 0.03, -34.5), Vector3(3.2, 0.2, 3.8)],
		[Vector3(-2.5, 0.03, -37.8), Vector3(2.6, 0.2, 3.0)],
		[Vector3(15.5, 0.03, -16.5), Vector3(2.2, 0.2, 2.6)],
	]:
		place.call(oil, ospec[0], Vector3.ZERO, ospec[1], 0.8)
	for sspec in [
		[Vector3(16.0, 0.03, -27.5), Vector3(2.8, 0.2, 2.8)],
		[Vector3(-15.5, 0.03, -26.0), Vector3(2.2, 0.2, 2.2)],
	]:
		place.call(scorch, sspec[0], Vector3.ZERO, sspec[1], 0.7)


func _scatter_floor_debris() -> void:
	# One draw call of rubble chunks/pebbles across all rooms: breaks up the bare-floor look
	var areas := [
		[Vector2(-9.4, -7.4), Vector2(9.4, 9.4), 60],
		[Vector2(-23.4, -7.4), Vector2(-10.6, 7.4), 55],
		[Vector2(10.6, -7.4), Vector2(23.4, 7.4), 55],
		[Vector2(-23.4, -21.4), Vector2(23.4, -8.6), 110],
		[Vector2(-11.4, -41.4), Vector2(23.4, -28.6), 90],
	]
	var total := 0
	for a in areas:
		total += a[2]
	var rock := SphereMesh.new()
	rock.radial_segments = 6
	rock.rings = 3
	rock.radius = 0.5
	rock.height = 1.0
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.42, 0.40, 0.37)
	mat.roughness = 0.95
	mat.vertex_color_use_as_albedo = true
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = rock
	mm.instance_count = total
	var idx := 0
	var rng := RandomNumberGenerator.new()
	rng.seed = 115115
	for a in areas:
		var mn: Vector2 = a[0]
		var mx: Vector2 = a[1]
		for i in range(a[2]):
			var pos := Vector3(rng.randf_range(mn.x, mx.x), 0.015, rng.randf_range(mn.y, mx.y))
			var s := rng.randf_range(0.05, 0.22)
			var sy := s * rng.randf_range(0.35, 0.7)
			var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, sy, s * rng.randf_range(0.7, 1.3)))
			mm.set_instance_transform(idx, Transform3D(basis, pos))
			var g := rng.randf_range(0.55, 1.15)
			mm.set_instance_color(idx, Color(g, g * rng.randf_range(0.92, 1.0), g * rng.randf_range(0.85, 0.98)))
			idx += 1
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.name = "FloorDebris"
	geo_root.add_child(mmi)


func _scatter_plank_debris(center: Vector3, facing_deg: float) -> void:
	# Deterministic per-window plank scatter: broken barricade boards lying trashed on the floor
	var seed_i := int(absf(center.x * 7.31 + center.z * 3.97) * 100.0)
	for i in range(5):
		var frac := float((seed_i + i * 37) % 100) / 100.0
		var frac2 := float((seed_i + i * 53 + 11) % 100) / 100.0
		var ang := facing_deg + (frac - 0.5) * 130.0
		var off := Vector3((frac - 0.5) * 1.9, 0.0, 0.35 + frac2 * 1.3)
		var fwd := Vector3(sin(deg_to_rad(facing_deg)), 0.0, cos(deg_to_rad(facing_deg)))
		var side := Vector3(fwd.z, 0.0, -fwd.x)
		var pos: Vector3 = center + side * off.x + fwd * off.z
		var length := 0.55 + frac2 * 0.7
		var plank := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.14, 0.035, length)
		plank.mesh = bm
		plank.material_override = _mat_wood
		plank.position = pos + Vector3(0.0, 0.02, 0.0)
		plank.rotation_degrees = Vector3(0.0, ang, (frac - 0.5) * 6.0)
		geo_root.add_child(plank)



func _build_facility_details() -> void:
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
		[Vector3(16.5, 0, -22), 0.0, "04 / MOTORPOOL", Color(0.98, 0.72, 0.30)],
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
	for x in [-20.5, -15.5, 13.0, 21.0]:
		var inst := pipe.instantiate() as Node3D
		inst.position = Vector3(x, 3.85, -21.55)
		details.add_child(inst)
	for x in [-9.55, 9.55]:
		var inst := pipe.instantiate() as Node3D
		inst.position = Vector3(x, 3.35, 3.8)
		inst.rotation_degrees.y = 90.0 if x < 0.0 else -90.0
		details.add_child(inst)

	# Rotating Industrial Ventilation Fans (with dusty volumetric air beams)
	if ResourceLoader.exists("res://scenes/fx/env_vent_fan.tscn"):
		var fan_scene := load("res://scenes/fx/env_vent_fan.tscn") as PackedScene
		for fspec in [
			[Vector3(-23.62, 3.55, -11.4), 90.0],
			[Vector3(23.62, 3.55, -11.4), -90.0],
			[Vector3(23.62, 3.45, -5.5), -90.0],
			[Vector3(23.62, 3.45, -35.5), -90.0],
		]:
			var fan := fan_scene.instantiate() as Node3D
			fan.position = fspec[0]
			fan.rotation_degrees.y = fspec[1]
			details.add_child(fan)
			var blades := fan.get_node_or_null("FanBlades") as Node3D
			if blades:
				_vent_fans.append(blades)


func _build_reflection_probes_and_decals() -> void:
	var probe_root := Node3D.new()
	probe_root.name = "ReflectionProbes"
	geo_root.add_child(probe_root)
	for pspec in [
		["Probe_Spawn", Vector3(0.0, 2.6, 1.0), Vector3(22.0, 7.0, 20.0), false, 0.85],
		["Probe_Lab", Vector3(-17.0, 2.4, 0.0), Vector3(16.0, 6.0, 18.0), true, 0.90],
		["Probe_East", Vector3(17.0, 2.4, 0.0), Vector3(16.0, 6.0, 18.0), false, 0.90],
		["Probe_Reactor", Vector3(0.0, 2.7, -15.0), Vector3(50.0, 6.8, 16.0), true, 0.92],
		["Probe_NorthYard", Vector3(6.0, 2.8, -33.0), Vector3(38.0, 8.0, 22.0), false, 0.85],
	]:
		var rp := ReflectionProbe.new()
		rp.name = pspec[0]
		rp.position = pspec[1]
		rp.size = pspec[2]
		rp.interior = pspec[3]
		rp.intensity = pspec[4]
		rp.box_projection = true
		rp.max_distance = 42.0
		rp.mesh_lod_threshold = 2.0
		rp.update_mode = ReflectionProbe.UPDATE_ONCE
		probe_root.add_child(rp)
		_probes.append(rp)

	var decals_root := Node3D.new()
	decals_root.name = "EnvDecals"
	geo_root.add_child(decals_root)

	var t_warn := load("res://assets/decals/decal_warning_stripe.png") as Texture2D
	var t_puddle := load("res://assets/decals/decal_puddle_albedo.png") as Texture2D
	var t_puddle_orm := load("res://assets/decals/decal_puddle_orm.png") as Texture2D
	var t_oil := load("res://assets/decals/decal_oil_slick.png") as Texture2D
	var t_scorch := load("res://assets/decals/decal_scorch_mark.png") as Texture2D
	var t_blood := load("res://assets/decals/decal_blood_splatter.png") as Texture2D
	var t_grate := load("res://assets/decals/decal_floor_grate.png") as Texture2D
	var t_grate_n := load("res://assets/decals/decal_floor_grate_normal.png") as Texture2D
	var t_crack := load("res://assets/decals/decal_wall_crack.png") as Texture2D
	var t_crack_n := load("res://assets/decals/decal_wall_crack_normal.png") as Texture2D
	var t_leak := load("res://assets/decals/decal_grime_leak.png") as Texture2D

	# Threshold warning stripes at doorways, ElectroTrap & Pack-a-Punch
	for wspec in [
		[Vector3(-9.1, 0.0, 0.0), 90.0, Vector3(3.4, 0.16, 0.9)],
		[Vector3(9.1, 0.0, 0.0), 90.0, Vector3(3.4, 0.16, 0.9)],
		[Vector3(-15.0, 0.0, -7.1), 0.0, Vector3(3.4, 0.16, 0.9)],
		[Vector3(17.0, 0.0, -7.1), 0.0, Vector3(3.4, 0.16, 0.9)],
		[Vector3(3.2, 0.0, -7.1), 0.0, Vector3(3.4, 0.16, 0.9)],
		[Vector3(16.5, 0.0, -21.1), 0.0, Vector3(3.4, 0.16, 0.9)],
		[Vector3(17.0, 0.0, -2.8), 0.0, Vector3(3.6, 0.16, 1.1)],
		[Vector3(1.5, 0.0, -18.9), 0.0, Vector3(2.8, 0.16, 0.9)],
	]:
		_add_decal(decals_root, "Decal_Warn", wspec[0], Vector3(0, wspec[1], 0), wspec[2], t_warn, null, null, 0.85)

	# Rainwater puddles across courtyards
	for ppos in [Vector3(2.5, 0.0, 4.2), Vector3(-4.2, 0.0, -1.2), Vector3(16.2, 0.0, 1.5), Vector3(-2.8, 0.0, -34.2), Vector3(8.5, 0.0, -33.6)]:
		_add_decal(decals_root, "Decal_Puddle", ppos, Vector3(0, randf_range(0, 180), 0), Vector3(3.4, 0.16, 2.8), t_puddle, null, t_puddle_orm, 0.78)

	# Oil slicks under Panzer tank, Covered Car & Welding Cart
	_add_decal(decals_root, "Decal_Oil_Tank", Vector3(-1.4, 0.0, -2.0), Vector3(0, 24, 0), Vector3(3.4, 0.16, 4.2), t_oil, null, t_puddle_orm, 0.85)
	_add_decal(decals_root, "Decal_Oil_Car", Vector3(2.2, 0.0, -34.4), Vector3(0, 24, 0), Vector3(2.8, 0.16, 4.4), t_oil, null, t_puddle_orm, 0.88)
	_add_decal(decals_root, "Decal_Oil_Weld", Vector3(22.0, 0.0, -1.6), Vector3(0, 0, 0), Vector3(1.8, 0.16, 1.8), t_oil, null, null, 0.82)

	# Blast scorch marks
	for sc in [Vector3(-1.2, 0.0, -4.4), Vector3(6.8, 0.0, -37.2), Vector3(-7.6, 0.0, -5.8), Vector3(-9.8, 0.0, -40.2)]:
		_add_decal(decals_root, "Decal_Scorch", sc, Vector3(0, 18, 0), Vector3(2.6, 0.16, 2.6), t_scorch, null, null, 0.82)

	# Blood splatters near barricaded windows & bio-pods
	for bl in [
		[Vector3(-5.2, 0.0, 8.7), 18.0, Vector3(2.0, 0.16, 2.0)],
		[Vector3(5.2, 0.0, 8.7), -42.0, Vector3(1.9, 0.16, 1.9)],
		[Vector3(-16.8, 0.0, 0.4), 55.0, Vector3(2.4, 0.16, 2.2)],
		[Vector3(-10.8, 0.0, -35.0), 75.0, Vector3(2.1, 0.16, 2.1)],
		[Vector3(4.0, 0.0, -40.6), -15.0, Vector3(2.2, 0.16, 2.0)],
	]:
		_add_decal(decals_root, "Decal_Blood", bl[0], Vector3(0, bl[1], 0), bl[2], t_blood, null, null, 0.82)

	# Industrial floor drain grates
	for gr in [Vector3(-19.5, 0.0, 0.2), Vector3(-14.2, 0.0, 0.2), Vector3(16.8, 0.0, -0.5), Vector3(-6.0, 0.0, -15.0), Vector3(6.0, 0.0, -15.0), Vector3(16.5, 0.0, -25.2)]:
		_add_decal(decals_root, "Decal_Grate", gr, Vector3.ZERO, Vector3(1.4, 0.16, 1.4), t_grate, t_grate_n, null, 0.90)

	# Wall cracks & water-stain grime streaks projected vertically onto interior walls
	for wc in [
		[Vector3(0.8, 1.9, 9.74), Vector3(-90, 0, 0), Vector3(2.8, 0.22, 2.6), t_crack, t_crack_n],
		[Vector3(-6.8, 2.4, -7.74), Vector3(90, 0, 0), Vector3(2.6, 0.22, 2.8), t_leak, null],
		[Vector3(7.4, 2.4, -7.74), Vector3(90, 0, 0), Vector3(2.6, 0.22, 2.8), t_leak, null],
		[Vector3(-23.74, 2.2, 4.8), Vector3(0, 0, -90), Vector3(2.4, 0.22, 2.8), t_leak, null],
		[Vector3(23.74, 2.2, -18.2), Vector3(0, 0, 90), Vector3(2.8, 0.22, 2.8), t_crack, t_crack_n],
		[Vector3(9.8, 2.2, -41.74), Vector3(90, 0, 0), Vector3(2.8, 0.22, 2.8), t_crack, t_crack_n],
	]:
		_add_decal(decals_root, "Decal_Wall", wc[0], wc[1], wc[2], wc[3], wc[4], null, 0.85)


func _build_env_fx() -> void:
	var fx_root := Node3D.new()
	fx_root.name = "EnvFX"
	geo_root.add_child(fx_root)
	_env_fx_particles.clear()

	if ResourceLoader.exists("res://scenes/fx/env_embers.tscn"):
		var s_emb := load("res://scenes/fx/env_embers.tscn") as PackedScene
		for ep in [Vector3(-7.6, 0.65, -5.8), Vector3(8.0, 0.65, -4.6), Vector3(-9.8, 0.65, -40.2), Vector3(22.2, 0.65, -39.2)]:
			var inst := s_emb.instantiate() as Node3D
			inst.position = ep
			fx_root.add_child(inst)
			_register_fx_particles(inst)

	if ResourceLoader.exists("res://scenes/fx/env_dust_motes.tscn"):
		var s_dust := load("res://scenes/fx/env_dust_motes.tscn") as PackedScene
		for dp in [Vector3(-1.2, 2.75, -0.5), Vector3(2.8, 2.75, 1.5), Vector3(1.8, 2.85, -34.2), Vector3(-16.8, 2.65, 0.2)]:
			var inst := s_dust.instantiate() as Node3D
			inst.position = dp
			fx_root.add_child(inst)
			_register_fx_particles(inst)

	if ResourceLoader.exists("res://scenes/fx/env_electric_sparks.tscn"):
		var s_spk := load("res://scenes/fx/env_electric_sparks.tscn") as PackedScene
		for sp in [Vector3(-5.3, 1.65, -21.45), Vector3(6.2, 1.65, -21.45), Vector3(-10.45, 1.55, 3.8)]:
			var inst := s_spk.instantiate() as Node3D
			inst.position = sp
			fx_root.add_child(inst)
			_register_fx_particles(inst)

	if ResourceLoader.exists("res://scenes/fx/env_ground_fog.tscn"):
		var s_fog := load("res://scenes/fx/env_ground_fog.tscn") as PackedScene
		for fp in [Vector3(0.0, 0.25, 1.5), Vector3(2.2, 0.25, -34.0)]:
			var inst := s_fog.instantiate() as Node3D
			inst.position = fp
			fx_root.add_child(inst)
			_register_fx_particles(inst)


func _register_fx_particles(node: Node) -> void:
	if node is GPUParticles3D:
		_env_fx_particles.append(node as GPUParticles3D)
	for gp in node.find_children("", "GPUParticles3D", true, false):
		if gp is GPUParticles3D and not _env_fx_particles.has(gp):
			_env_fx_particles.append(gp as GPUParticles3D)


func _setup_light_fade(light: Light3D, begin: float = 26.0, length: float = 8.0) -> void:
	light.distance_fade_enabled = true
	light.distance_fade_begin = begin
	light.distance_fade_shadow = begin
	light.distance_fade_length = length


func _add_decal(
	parent: Node3D,
	nname: String,
	pos: Vector3,
	rot_deg: Vector3,
	sz: Vector3,
	alb: Texture2D,
	nrm: Texture2D,
	orm: Texture2D,
	mix: float
) -> void:
	if alb == null:
		return
	var d := Decal.new()
	d.name = nname
	d.position = pos
	d.rotation_degrees = rot_deg
	d.size = sz
	d.texture_albedo = alb
	if nrm != null:
		d.texture_normal = nrm
	if orm != null:
		d.texture_orm = orm
	d.albedo_mix = mix
	d.normal_fade = 0.55
	d.upper_fade = 0.25
	d.lower_fade = 0.25
	d.distance_fade_enabled = true
	d.distance_fade_begin = 24.0
	d.distance_fade_length = 8.0
	parent.add_child(d)
	_decals.append(d)


func _add_street_lamp(pos: Vector3, rot_y_deg: float) -> void:
	_place_prop("res://assets/models/env_cc0/street_lamp_01.glb", pos, rot_y_deg, Vector3(0.45, 3.85, 0.45), Vector3(0, 1.92, 0))
	if _street_bulb_mat == null:
		_street_bulb_mat = StandardMaterial3D.new()
		_street_bulb_mat.albedo_color = Color(1.0, 0.78, 0.40)
		_street_bulb_mat.emission_enabled = true
		_street_bulb_mat.emission = Color(1.0, 0.68, 0.28)
		_street_bulb_mat.emission_energy_multiplier = 4.2
	if _street_bulb_mesh == null:
		_street_bulb_mesh = SphereMesh.new()
		_street_bulb_mesh.radius = 0.085
		_street_bulb_mesh.height = 0.22
		_street_bulb_mesh.radial_segments = 12
		_street_bulb_mesh.rings = 6
		_street_bulb_mesh.material = _street_bulb_mat
	var bulb := MeshInstance3D.new()
	bulb.position = pos + Vector3(0, 3.36, 0)
	bulb.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	bulb.mesh = _street_bulb_mesh
	geo_root.add_child(bulb)

	var l := OmniLight3D.new()
	l.position = pos + Vector3(0, 3.30, 0)
	l.light_color = Color(1.0, 0.68, 0.30)
	l.light_energy = 3.0
	l.omni_range = 15.0
	l.omni_attenuation = 1.25
	_setup_light_fade(l, 28.0, 8.0)
	geo_root.add_child(l)


func _zone_bucket(pos: Vector3) -> String:
	if pos.z > -8.2:
		if pos.x < -9.8:
			return "lab"
		if pos.x > 9.8:
			return "east"
		return "spawn"
	if pos.z > -22.2:
		return "reactor_w" if pos.x < 0.0 else "reactor_e"
	return "north_w" if pos.x < 6.0 else "north_e"


func _queue_batch_box(size: Vector3, xform: Transform3D, mat: Material, bucket_override: String = "") -> void:
	if _unit_box_mesh == null:
		_unit_box_mesh = BoxMesh.new()
		_unit_box_mesh.size = Vector3.ONE
	var bucket := bucket_override if bucket_override != "" else _zone_bucket(xform.origin)
	var key := "%s_%d" % [bucket, mat.get_instance_id()]
	var batch: Dictionary = _arch_batches.get(key, {})
	var st: SurfaceTool
	if batch.is_empty():
		st = SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		_arch_batches[key] = {"mat": mat, "st": st}
	else:
		st = batch["st"] as SurfaceTool
	var scaled_xf := Transform3D(xform.basis * Basis.from_scale(size), xform.origin)
	st.append_from(_unit_box_mesh, 0, scaled_xf)


func _flush_arch_batches() -> void:
	for key in _arch_batches.keys():
		var batch: Dictionary = _arch_batches[key]
		var st := batch["st"] as SurfaceTool
		var am := st.commit()
		if am == null or am.get_surface_count() == 0:
			continue
		var mi := MeshInstance3D.new()
		mi.name = "ArchBatch_" + str(key)
		mi.mesh = am
		mi.material_override = batch["mat"] as Material
		geo_root.add_child(mi)
	_arch_batches.clear()


func _add_visual_box(nname: String, size: Vector3, pos: Vector3, mat: Material) -> void:
	if _arch_batching and mat != null:
		_queue_batch_box(size, Transform3D(Basis.IDENTITY, pos), mat)
		return
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
	if nname.begins_with("Roof_") and size.x > 1.2 and size.z > 1.2:
		var occ := OccluderInstance3D.new()
		var bo := BoxOccluder3D.new()
		bo.size = Vector3(size.x - 0.6, 0.22, size.z - 0.6)
		occ.occluder = bo
		sb.add_child(occ)
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
	if length >= 2.2 and height >= 3.5:
		var occ := OccluderInstance3D.new()
		var bo := BoxOccluder3D.new()
		bo.size = Vector3(length - 0.70, height - 0.30, clampf(thick - 0.12, 0.14, 0.40))
		occ.occluder = bo
		sb.add_child(occ)
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
		l.omni_range = 9.5
		_setup_light_fade(l, 22.0, 8.0)
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
	var mid := (p1 + p2) * 0.5
	var wall_yaw := -delta.angle()
	var root_xf := Transform3D(Basis.from_euler(Vector3(0.0, wall_yaw, 0.0)), Vector3(mid.x, base_y, mid.y))
	var wall_bucket := "ruin_spawn" if mid.y > -15.0 else "ruin_north"
	var root: Node3D = null
	if not _arch_batching:
		root = Node3D.new()
		root.position = Vector3(mid.x, base_y, mid.y)
		root.rotation.y = wall_yaw
		geo_root.add_child(root)

	var add_local := func(sz: Vector3, lpos: Vector3, mat: Material, rot_deg: Vector3 = Vector3.ZERO) -> void:
		if _arch_batching and mat != null:
			var local_xf := Transform3D(Basis.from_euler(Vector3(deg_to_rad(rot_deg.x), deg_to_rad(rot_deg.y), deg_to_rad(rot_deg.z))), lpos)
			_queue_batch_box(sz, root_xf * local_xf, mat, wall_bucket)
			return
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
		var ww := win_half_w * 2.0
		add_local.call(Vector3(ww + 0.08, 0.86, thick), Vector3(wx, 0.67, 0), _mat_brick)
		add_local.call(Vector3(ww + 0.24, 0.12, thick + 0.12), Vector3(wx, 1.12, 0), _mat_concrete)
		add_local.call(Vector3(ww + 0.22, 0.22, thick + 0.10), Vector3(wx, 3.24, 0), _mat_concrete)
		var par_h := 0.45 + 0.30 * fmod(absf(wx * 0.37), 1.0)
		add_local.call(Vector3(ww + 0.08, par_h, thick), Vector3(wx, 3.35 + par_h * 0.5, 0), _mat_brick)
		add_local.call(Vector3(ww + 0.16, 0.15, 0.05), Vector3(wx, 1.56, 0.02), _mat_wood, Vector3(0, 0, -9.0 + (seg_idx % 3) * 6.0))
		add_local.call(Vector3(ww + 0.16, 0.15, 0.05), Vector3(wx, 2.38, -0.02), _mat_wood, Vector3(0, 0, 11.0 - (seg_idx % 2) * 8.0))
		cur_x = wx + win_half_w

	if x_end > cur_x + 0.15:
		_add_ruined_pier_span(add_local, cur_x, x_end, total_len, thick, gap_t0, gap_t1, seg_idx)


func _add_ruined_pier_span(add_local: Callable, x0: float, x1: float, total_len: float, thick: float, gap_t0: float, gap_t1: float, seed_idx: int) -> void:
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
		if (chunk_i + seed_idx) % 2 == 0:
			add_local.call(Vector3(0.035, 0.72, 0.035), Vector3(cx - 0.15, top_y + 0.28, 0.04), _mat_steel, Vector3(12, 0, -18))
			add_local.call(Vector3(0.035, 0.58, 0.035), Vector3(cx + 0.18, top_y + 0.22, -0.05), _mat_steel, Vector3(-14, 0, 22))
		pos_x = nxt
		chunk_i += 1


func _add_light_shaft(pos: Vector3, rot_deg: Vector3, radius: float, height: float) -> void:
	var bucket := "spawn" if pos.z > -15.0 else "north"
	var st := _shaft_sts.get(bucket, null) as SurfaceTool
	if st == null:
		st = SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		_shaft_sts[bucket] = st
	var cyl := CylinderMesh.new()
	cyl.top_radius = radius * 0.45
	cyl.bottom_radius = radius
	cyl.height = height
	cyl.radial_segments = 16
	cyl.rings = 1
	var xf := Transform3D(Basis.from_euler(Vector3(deg_to_rad(rot_deg.x), deg_to_rad(rot_deg.y), deg_to_rad(rot_deg.z))), pos)
	st.append_from(cyl, 0, xf)


func _flush_light_shafts() -> void:
	for bucket in _shaft_sts.keys():
		var st := _shaft_sts[bucket] as SurfaceTool
		var am := st.commit()
		if am == null or am.get_surface_count() == 0:
			continue
		var mi := MeshInstance3D.new()
		mi.name = "MoonLightShafts_" + str(bucket)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.mesh = am
		mi.material_override = _light_shaft_mat
		geo_root.add_child(mi)
	_shaft_sts.clear()


func _add_cage_light(pos: Vector3, rot_y_deg: float, col: Color, energy: float, power_controlled: bool, ceiling_mount: bool = false, flicker: bool = false, spawn_mesh: bool = true, drop_y: float = -0.35) -> void:
	var n := Node3D.new()
	n.position = pos
	n.rotation_degrees.y = rot_y_deg
	geo_root.add_child(n)
	if spawn_mesh and ResourceLoader.exists("res://assets/models/env/light_cage.glb"):
		var inst := (load("res://assets/models/env/light_cage.glb") as PackedScene).instantiate() as Node3D
		if ceiling_mount:
			inst.rotation_degrees.x = 90.0
		n.add_child(inst)
	var omni := OmniLight3D.new()
	omni.position = Vector3(0, drop_y, 0) if ceiling_mount else Vector3(0, -0.2, 0.25)
	omni.light_color = col
	omni.omni_range = 8.5
	omni.omni_attenuation = 1.9
	omni.light_energy = 0.0 if (power_controlled and not GameManager.power_on) else energy
	omni.set_meta("target_energy", energy)
	_setup_light_fade(omni, 28.0, 8.0)
	n.add_child(omni)
	if power_controlled:
		_power_lights.append(omni)
	elif flicker:
		_flicker_lights.append({
			"light": omni,
			"base": energy,
			"speed": 9.5 + fmod(absf(pos.x + pos.z), 5.0),
			"phase": pos.x * 0.7 + pos.z * 0.4,
		})


func _add_alarm_light(pos: Vector3) -> void:
	var l := OmniLight3D.new()
	l.position = pos
	l.light_color = Color(1.0, 0.14, 0.08)
	l.omni_range = 12.0
	l.light_energy = 1.2
	_setup_light_fade(l, 22.0, 8.0)
	geo_root.add_child(l)
	_alarm_lights.append(l)


func _bake_zone_navigation() -> void:
	# Add temporary seal colliders at doorways + north exterior alley during NavMesh bake
	var seals := Node3D.new()
	geo_root.add_child(seals)
	for spec in [
		[Vector3(-10.0, 1.5, 0.0), Vector3(0.5, 3.0, 3.6)],
		[Vector3(10.0, 1.5, 0.0), Vector3(0.5, 3.0, 3.6)],
		[Vector3(-15.0, 1.5, -8.0), Vector3(3.6, 3.0, 0.5)],
		[Vector3(17.0, 1.5, -8.0), Vector3(3.6, 3.0, 0.5)],
		[Vector3(3.2, 1.5, -8.0), Vector3(3.6, 3.0, 0.5)],
		[Vector3(16.5, 1.5, -22.0), Vector3(3.6, 3.0, 0.5)],
		[Vector3(0.0, 1.5, -25.0), Vector3(24.0, 3.0, 6.0)],
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
		"Navigation/NavRegionNorthYard": AABB(Vector3(-11.9, -0.4, -41.9), Vector3(35.8, 3.6, 19.8)),
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
	var target_den := 0.038 if is_dog else 0.015
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(env, "fog_light_color", target_col, 1.4)
	tw.tween_property(env, "fog_density", target_den, 1.4)


func _apply_graphics_settings() -> void:
	SettingsManager.apply_viewport_settings(get_viewport())
	if not world_env or not world_env.environment:
		return
	var env := world_env.environment
	var q := SettingsManager.graphics_quality
	env.ssao_enabled = (q == "High")
	env.ssil_enabled = (q == "High")
	env.glow_enabled = (q != "Low")
	env.volumetric_fog_enabled = (q == "High")
	var fx_ratio := 1.0 if q == "High" else (0.55 if q == "Medium" else 0.25)
	for gp in _env_fx_particles:
		if is_instance_valid(gp):
			gp.amount_ratio = fx_ratio
	if moon_light:
		moon_light.shadow_enabled = (q != "Low")
		moon_light.directional_shadow_mode = (
			DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS if q == "High"
			else (DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if q == "Medium" else DirectionalLight3D.SHADOW_ORTHOGONAL)
		)
		moon_light.directional_shadow_max_distance = 65.0 if q == "High" else (45.0 if q == "Medium" else 32.0)


func _prewarm_resources() -> void:
	var paths := [
		"res://scenes/enemies/zombie.tscn",
		"res://scenes/enemies/hellhound.tscn",
		"res://scenes/enemies/panzer_boss.tscn",
		"res://scenes/interactables/power_up.tscn",
		"res://scenes/fx/blood_burst.tscn",
		"res://scenes/fx/impact_sparks.tscn",
		"res://scenes/fx/gib_chunk.tscn",
		"res://scenes/fx/blood_decal.tscn",
		"res://scenes/fx/wpn_shell_casing.tscn",
		"res://scenes/fx/wpn_bullet_decal.tscn",
		"res://assets/models/characters/zombie_soldier.glb",
		"res://assets/models/characters/zombie_scientist.glb",
		"res://assets/models/characters/zombie_worker.glb",
		"res://assets/models/characters/zombie_brute.glb",
		"res://assets/models/characters/zombie_crawler.glb",
		"res://assets/models/characters/hellhound.glb",
		"res://assets/models/characters/panzer_boss.glb",
	]
	for p in paths:
		if ResourceLoader.exists(p):
			var r := load(p)
			if r != null:
				_prewarmed_resources.append(r)
	GibChunk._ensure_shared_assets()
	BloodDecal._get_shared_mat()
	WeaponController._ensure_tracer_assets()


func _exit_tree() -> void:
	_prewarmed_resources.clear()
	_power_lights.clear()
	_alarm_lights.clear()
	_flicker_lights.clear()
	_vent_fans.clear()
	_probes.clear()
	_decals.clear()
	_env_fx_particles.clear()
	_arch_batches.clear()
	_shaft_sts.clear()
	_mat_cobble = null
	_mat_concrete = null
	_mat_roof_concrete = null
	_mat_concrete_floor = null
	_mat_brick = null
	_mat_tile = null
	_mat_steel = null
	_mat_metal_floor = null
	_mat_corrugated = null
	_mat_roof_corrugated = null
	_mat_wood = null
	_mat_asphalt = null
	_mat_earth = null
	_light_shaft_mat = null
	_street_bulb_mat = null
	_street_bulb_mesh = null
	_unit_box_mesh = null
	_env_pbr_shader = null

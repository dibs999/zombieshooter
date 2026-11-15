extends Node

var _passed: int = 0
var _failed: int = 0


func _check(cond: bool, msg: String) -> void:
	if cond:
		_passed += 1
		print("  [ENV PASS] ", msg)
	else:
		_failed += 1
		printerr("  [ENV FAIL] ", msg)


static func run_checks(runner: Node) -> void:
	var checker := Node.new()
	checker.set_script(load("res://tools/verify/tests_env.gd"))
	runner.add_child(checker)
	await checker._execute()
	if runner.has_method("_check"):
		runner._check(checker._failed == 0, "Environment Stream A suite (%d passed, %d failed)" % [checker._passed, checker._failed])
	checker.queue_free()


func _ready() -> void:
	if get_parent() == get_tree().root:
		await get_tree().process_frame
		await _execute()
		print("==============================================")
		print("ENV RESULTS: %d passed, %d failed" % [_passed, _failed])
		get_tree().quit(1 if _failed > 0 else 0)


func _execute() -> void:
	print("=== BUNKER 115 STREAM A ENVIRONMENT VERIFICATION ===")
	GameManager.reset_match()

	# 1. Verify MainMenu HDRI, shaders, ReflectionProbe, CC0 diorama
	var menu := (load("res://scenes/main_menu.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(menu)
	await get_tree().process_frame
	var menu_we := menu.get_node_or_null("Backdrop3D/WorldEnvironment") as WorldEnvironment
	_check(menu_we != null and menu_we.environment != null, "MainMenu WorldEnvironment present")
	var menu_sky := menu_we.environment.sky if menu_we and menu_we.environment else null
	_check(menu_sky != null and menu_sky.sky_material is PanoramaSkyMaterial, "MainMenu uses PanoramaSkyMaterial HDRI")
	_check(menu_we.environment.tonemap_mode == Environment.TONE_MAPPER_AGX, "MainMenu uses AgX tonemapping")
	_check(menu.get_node("Backdrop3D").find_children("", "ReflectionProbe", true, false).size() >= 1, "MainMenu includes ReflectionProbe")
	_check(menu.get_node("Backdrop3D").find_children("", "GPUParticles3D", true, false).size() >= 2, "MainMenu includes GPU particle FX")
	menu.queue_free()
	await get_tree().process_frame

	# 2. Load GameWorld
	GameManager.reset_match()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate() as GameWorld
	get_tree().root.add_child(world)
	await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame

	var env := world.world_env.environment
	_check(env != null and env.sky != null and env.sky.sky_material is PanoramaSkyMaterial, "GameWorld uses PanoramaSkyMaterial HDRI")
	_check(env.tonemap_mode == Environment.TONE_MAPPER_AGX, "GameWorld uses AgX tonemapping")
	_check(not GameManager.unlocked_zones.get("north_yard", true), "Zone north_yard starts locked")

	# 3. Zone 5 NavMesh & DoorReactorNorth sealing + unlocking
	var reg_ny := world.get_node_or_null("Navigation/NavRegionNorthYard") as NavigationRegion3D
	var ny_polys := reg_ny.navigation_mesh.get_polygon_count() if (reg_ny and reg_ny.navigation_mesh) else 0
	_check(ny_polys > 0, "NavRegionNorthYard baked (%d polys)" % ny_polys)

	var map_rid: RID = world.get_world_3d().navigation_map
	NavigationServer3D.map_force_update(map_rid)
	var locked_ny := NavigationServer3D.map_get_path(map_rid, Vector3(16.5, 0, -16.0), Vector3(6.0, 0, -35.0), true)
	var crossed_ny := false
	for pt in locked_ny:
		if pt.z < -22.5:
			crossed_ny = true
	_check(not crossed_ny, "Locked DoorReactorNorth blocks NavMesh pathing into north_yard")

	var player := world.get_node("Player") as PlayerController
	GameManager.add_points(20000)
	var door_ny := world.get_node_or_null("Interactables/DoorReactorNorth") as BuyableDoor
	_check(door_ny != null and door_ny.cost == 1500 and door_ny.unlock_zone_id == "north_yard", "DoorReactorNorth configured ($1500 -> north_yard)")
	door_ny.interact(player)
	await get_tree().process_frame
	await get_tree().physics_frame
	NavigationServer3D.map_force_update(map_rid)
	_check(door_ny.is_opened and GameManager.unlocked_zones.get("north_yard", false), "DoorReactorNorth opens and unlocks north_yard")

	# Unlock path from Spawn -> Reactor -> North Yard
	(world.get_node("Interactables/PowerSwitch") as PowerSwitch).interact(player)
	await get_tree().process_frame
	await get_tree().physics_frame
	NavigationServer3D.map_force_update(map_rid)
	var full_path := NavigationServer3D.map_get_path(map_rid, Vector3(0.0, 0, 4.0), Vector3(6.0, 0, -35.0), true)
	var reached_ny := full_path.size() >= 2 and full_path[full_path.size() - 1].z < -30.0
	_check(reached_ny, "Full NavMesh path reaches north_yard from Spawn (pts=%d, end_z=%.1f)" % [full_path.size(), full_path[full_path.size() - 1].z if full_path.size() > 0 else 0.0])

	# 4. Windows, DogSpawns & FeatureSlots in north_yard
	for wname in ["WinNorthYardW", "WinNorthYardN"]:
		var w := world.get_node_or_null("Interactables/" + wname) as WindowBarricade
		_check(w != null and w.zone_id == "north_yard" and w.planks.size() == 6, "%s configured for north_yard with 6 planks" % wname)

	var space: PhysicsDirectSpaceState3D = world.get_world_3d().direct_space_state
	var ny_ray := PhysicsRayQueryParameters3D.create(Vector3(4.0, 1.4, -40.8), Vector3(4.0, 1.4, -43.2))
	ny_ray.collision_mask = 1
	_check(space.intersect_ray(ny_ray).is_empty(), "WinNorthYardN bullet gap unobstructed")

	for dname in ["DogSpawn7", "DogSpawn8"]:
		var ds := world.get_node_or_null("DogSpawns/" + dname) as Marker3D
		_check(ds != null and ds.is_in_group("dog_spawns") and str(ds.get_meta("zone_id", "")) == "north_yard", "%s registered for north_yard" % dname)

	for sname in ["FeatureSlot_Perk1", "FeatureSlot_Perk2", "FeatureSlot_Quest"]:
		var slot := world.get_node_or_null("FeatureSlots/" + sname) as Marker3D
		var in_ny := slot != null and slot.global_position.x >= -12.0 and slot.global_position.x <= 24.0 and slot.global_position.z >= -42.0 and slot.global_position.z <= -22.0
		_check(in_ny, "FeatureSlots/%s Marker3D inside north_yard" % sname)

	# 5. Visual systems: ReflectionProbes, Decals, FX, VentFans, all CC0 meshes
	var probes := world.geo_root.find_children("", "ReflectionProbe", true, false)
	var decals := world.geo_root.find_children("", "Decal", true, false)
	var particles := world.geo_root.find_children("", "GPUParticles3D", true, false)
	_check(probes.size() == 5, "All 5 zone ReflectionProbes present (%d)" % probes.size())
	_check(decals.size() >= 20, "Environment Decals placed (%d)" % decals.size())
	_check(particles.size() >= 10, "Environment GPUParticles3D FX active (%d)" % particles.size())
	_check(world._vent_fans.size() >= 4, "Rotating ventilation fans registered (%d)" % world._vent_fans.size())
	var cc0_names := [
		"ammo_box", "barrel_01", "barrel_02", "barrel_stove", "boulder_01",
		"bunsen_burner", "caged_hanging_light", "cement_bag", "chemistry_set",
		"concrete_road_barrier", "concrete_road_barrier_02", "covered_car", "crowbar_01",
		"dead_tree_trunk", "drawer_cabinet", "flood_lights", "hanging_industrial_lamp",
		"industrial_storage_cart", "industrial_wall_lamp", "medical_box", "metal_office_desk",
		"metal_toolbox", "old_military_crate", "portable_welding_cart", "power_box_01",
		"steel_frame_shelves_01", "street_lamp_01", "vintage_radio_transceiver",
	]
	var missing_cc0 := 0
	for cname in cc0_names:
		if not ResourceLoader.exists("res://assets/models/env_cc0/%s.glb" % cname):
			missing_cc0 += 1
	_check(missing_cc0 == 0, "All %d CC0 GLB assets load cleanly (missing=%d)" % [cc0_names.size(), missing_cc0])

	world.queue_free()
	await get_tree().process_frame
	await get_tree().process_frame

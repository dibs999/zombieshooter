extends Node

var out_dir: String = OS.get_environment("BUNKER_CHAR_SHOT_DIR") if OS.has_environment("BUNKER_CHAR_SHOT_DIR") else "/tmp/bunker_shots_chars"


func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(1280, 720)
	DirAccess.make_dir_recursive_absolute(out_dir)
	await _wait_frames(2)

	await _capture_studio_shots()
	await _capture_ingame_combat_shot()

	print("CAPTURED 5 CHARACTER VERIFICATION SCREENSHOTS IN ", out_dir)
	get_tree().quit(0)


func _build_studio_stage() -> Node3D:
	var stage := Node3D.new()
	stage.name = "CharStudioStage"

	var sky_mat := PanoramaSkyMaterial.new()
	if ResourceLoader.exists("res://assets/hdri/moonlit_golf_2k.hdr"):
		sky_mat.panorama = load("res://assets/hdri/moonlit_golf_2k.hdr")
	sky_mat.energy_multiplier = 0.88
	var sky := Sky.new()
	sky.sky_material = sky_mat

	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color(0.28, 0.34, 0.42)
	env.ambient_light_energy = 0.85
	env.ambient_light_sky_contribution = 0.65
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.16
	env.ssao_enabled = true
	env.ssao_radius = 1.0
	env.ssao_intensity = 1.35
	env.glow_enabled = true
	env.glow_intensity = 0.65
	env.glow_bloom = 0.14

	var we := WorldEnvironment.new()
	we.environment = env
	stage.add_child(we)

	# Moon key light matching GameWorld + warm/cool fill lights so textures & normals read cleanly
	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-42.0, 28.0, 0.0)
	moon.light_color = Color(0.76, 0.85, 0.98)
	moon.light_energy = 1.45
	moon.shadow_enabled = true
	stage.add_child(moon)

	var warm_fill := OmniLight3D.new()
	warm_fill.position = Vector3(-2.6, 2.5, 3.2)
	warm_fill.light_color = Color(1.0, 0.84, 0.66)
	warm_fill.light_energy = 2.8
	warm_fill.omni_range = 14.0
	stage.add_child(warm_fill)

	var cool_fill := OmniLight3D.new()
	cool_fill.position = Vector3(2.8, 2.4, 3.0)
	cool_fill.light_color = Color(0.68, 0.86, 1.0)
	cool_fill.light_energy = 2.4
	cool_fill.omni_range = 14.0
	stage.add_child(cool_fill)

	var rim_light := OmniLight3D.new()
	rim_light.position = Vector3(0.0, 3.1, -3.5)
	rim_light.light_color = Color(0.75, 0.88, 1.0)
	rim_light.light_energy = 2.2
	rim_light.omni_range = 14.0
	stage.add_child(rim_light)

	# Textured concrete courtyard slab + dark bunker backdrop wall
	var floor_mesh := PlaneMesh.new()
	floor_mesh.size = Vector2(22.0, 18.0)
	var floor_mat := StandardMaterial3D.new()
	floor_mat.roughness = 0.85
	floor_mat.uv1_scale = Vector3(6.0, 6.0, 1.0)
	if ResourceLoader.exists("res://assets/textures/env/cc0_asphalt_albedo.jpg"):
		floor_mat.albedo_texture = load("res://assets/textures/env/cc0_asphalt_albedo.jpg")
		floor_mat.normal_enabled = true
		floor_mat.normal_texture = load("res://assets/textures/env/cc0_asphalt_normal.jpg")
		floor_mat.roughness_texture = load("res://assets/textures/env/cc0_asphalt_roughness.jpg")
	else:
		floor_mat.albedo_color = Color(0.18, 0.19, 0.21)
	var floor_mi := MeshInstance3D.new()
	floor_mi.mesh = floor_mesh
	floor_mi.material_override = floor_mat
	stage.add_child(floor_mi)

	var wall_mesh := BoxMesh.new()
	wall_mesh.size = Vector3(22.0, 6.0, 0.4)
	var wall_mat := StandardMaterial3D.new()
	wall_mat.roughness = 0.88
	wall_mat.uv1_scale = Vector3(6.0, 2.0, 1.0)
	if ResourceLoader.exists("res://assets/textures/env/cc0_concrete_wall_albedo.jpg"):
		wall_mat.albedo_texture = load("res://assets/textures/env/cc0_concrete_wall_albedo.jpg")
		wall_mat.normal_enabled = true
		wall_mat.normal_texture = load("res://assets/textures/env/cc0_concrete_wall_normal.jpg")
	else:
		wall_mat.albedo_color = Color(0.16, 0.17, 0.18)
	var wall_mi := MeshInstance3D.new()
	wall_mi.mesh = wall_mesh
	wall_mi.material_override = wall_mat
	wall_mi.position = Vector3(0.0, 3.0, -4.8)
	stage.add_child(wall_mi)

	return stage


func _spawn_zombie(stage: Node3D, variant: String, pos: Vector3, yaw_deg: float, anim: String, anim_time: float) -> ZombieAI:
	var z := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z.setup(variant, 250.0, 2.2, null)
	stage.add_child(z)
	z.set_physics_process(false)
	z.global_position = pos
	z.rotation_degrees.y = yaw_deg
	if z._anim_player != null and z._anim_player.has_animation(anim):
		z._anim_player.play(anim, 0.0)
		z._anim_player.advance(anim_time)
	return z


func _capture_studio_shots() -> void:
	GameManager.reset_match()
	var stage := _build_studio_stage()
	get_tree().root.add_child(stage)

	var cam := Camera3D.new()
	cam.fov = 44.0
	cam.near = 0.05
	cam.current = true
	stage.add_child(cam)

	# --- Shot 1: All 5 Zombie Variants Lineup ---
	var z_sol := _spawn_zombie(stage, "soldier", Vector3(-2.05, 0.0, -0.1), 165.0, "Walk", 0.28)
	var z_sci := _spawn_zombie(stage, "scientist", Vector3(-0.72, 0.0, 0.05), 174.0, "Idle", 0.45)
	var z_bru := _spawn_zombie(stage, "brute", Vector3(0.75, 0.0, -0.2), -174.0, "Walk", 0.52)
	var z_wrk := _spawn_zombie(stage, "worker", Vector3(2.12, 0.0, 0.05), -162.0, "Run", 0.18)
	var z_crw := _spawn_zombie(stage, "crawler", Vector3(0.05, 0.0, 1.35), 178.0, "Crawl", 0.30)

	cam.position = Vector3(0.0, 1.32, 4.45)
	cam.look_at(Vector3(0.0, 0.96, 0.15), Vector3.UP)
	await _wait_frames(4)
	await _save_shot("chars_1_zombies_lineup.png")

	for n in [z_sol, z_sci, z_bru, z_wrk, z_crw]:
		n.queue_free()
	await _wait_frames(2)

	# --- Shot 2: Close-up Faces, Eyes, Ribs & Dismemberment/Gore ---
	var f_sol := _spawn_zombie(stage, "soldier", Vector3(-0.78, 0.0, 0.1), 158.0, "Attack", 0.28)
	var f_sci := _spawn_zombie(stage, "scientist", Vector3(-0.08, 0.0, 0.22), 178.0, "Walk", 0.18)
	var f_gor := _spawn_zombie(stage, "worker", Vector3(0.72, 0.0, 0.12), 148.0, "Idle", 0.22)
	await _wait_frames(2)
	f_gor._dismember_arm("L", Vector3(1.0, 0.6, 0.5))
	f_gor._dismember_head(Vector3(0.2, 0.8, 0.9))
	f_gor._spawn_blood_decal(f_gor.global_position + Vector3(0.0, 0.0, 0.28), 1.35)
	# Also show a crawler in foreground for leg stump + flat crawl posture inspection
	var f_crw := _spawn_zombie(stage, "soldier", Vector3(-0.18, 0.0, 1.12), -118.0, "Crawl", 0.25)
	await _wait_frames(1)
	f_crw.become_crawler(Vector3(0.0, 0.5, 1.0))
	f_crw._anim_player.advance(0.28)

	cam.position = Vector3(0.0, 1.18, 3.12)
	cam.look_at(Vector3(0.0, 0.78, 0.32), Vector3.UP)
	await _wait_frames(5)
	await _save_shot("chars_2_face_gore_closeup.png")

	for ch in stage.get_children():
		if ch is ZombieAI or ch is GibChunk or ch is BloodDecal or ch.name.begins_with("Blood"):
			ch.queue_free()
	await _wait_frames(2)

	# --- Shot 3: Overhauled Hellhound Close-up ---
	var hh1 := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	stage.add_child(hh1)
	hh1.setup(180.0)
	hh1.set_physics_process(false)
	hh1.global_position = Vector3(-0.62, 0.0, 0.20)
	hh1.rotation_degrees.y = 135.0
	if hh1._anim_player:
		hh1._anim_player.play("Attack", 0.0)
		hh1._anim_player.advance(0.20)

	var hh2 := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	stage.add_child(hh2)
	hh2.setup(180.0)
	hh2.set_physics_process(false)
	hh2.global_position = Vector3(0.74, 0.0, 0.12)
	hh2.rotation_degrees.y = -132.0
	if hh2._anim_player:
		hh2._anim_player.play("Run", 0.0)
		hh2._anim_player.advance(0.16)

	cam.position = Vector3(0.0, 0.86, 2.25)
	cam.look_at(Vector3(0.04, 0.54, 0.15), Vector3.UP)
	await _wait_frames(8)
	await _save_shot("chars_3_hellhound_closeup.png")

	for ch in stage.get_children():
		if ch is HellhoundAI or ch is GibChunk or ch is BloodDecal or ch.name.begins_with("Impact"):
			ch.queue_free()
	await _wait_frames(2)

	# --- Shot 4: Panzersoldat Boss Front (Flamethrower) + Armor Shattered + Rear Jetpack ---
	var pb_intact := (load("res://scenes/enemies/panzer_boss.tscn") as PackedScene).instantiate() as PanzerBossAI
	pb_intact.setup(8)
	stage.add_child(pb_intact)
	pb_intact.set_physics_process(false)
	pb_intact.global_position = Vector3(-1.72, 0.0, 0.15)
	pb_intact.rotation_degrees.y = 158.0
	if pb_intact._anim_player:
		pb_intact._anim_player.play("FlameAttack", 0.0)
		pb_intact._anim_player.advance(0.26)
	await _wait_frames(1)
	pb_intact._set_flamethrower_active(true)

	var pb_broken := (load("res://scenes/enemies/panzer_boss.tscn") as PackedScene).instantiate() as PanzerBossAI
	pb_broken.setup(8)
	stage.add_child(pb_broken)
	pb_broken.set_physics_process(false)
	pb_broken.global_position = Vector3(0.08, 0.0, 0.40)
	pb_broken.rotation_degrees.y = -172.0
	if pb_broken._anim_player:
		pb_broken._anim_player.play("Attack", 0.0)
		pb_broken._anim_player.advance(0.28)
	# Shatter visor, chest, and left shoulder armor plates to inspect exposed core + visor glow + gibs!
	pb_broken.take_damage(350.0, true, pb_broken.head_area.global_position, Vector3.FORWARD)
	pb_broken.take_damage(420.0, false, pb_broken.global_position + Vector3(0.0, 1.35, 0.25), Vector3.FORWARD)
	pb_broken.take_damage(320.0, false, pb_broken.global_position + Vector3(-0.45, 1.75, 0.05), Vector3.RIGHT)

	var pb_rear := (load("res://scenes/enemies/panzer_boss.tscn") as PackedScene).instantiate() as PanzerBossAI
	pb_rear.setup(8)
	stage.add_child(pb_rear)
	pb_rear.set_physics_process(false)
	pb_rear.global_position = Vector3(1.70, 0.0, 0.15)
	pb_rear.rotation_degrees.y = -28.0
	if pb_rear._anim_player:
		pb_rear._anim_player.play("Walk", 0.0)
		pb_rear._anim_player.advance(0.22)

	cam.position = Vector3(0.0, 1.52, 5.18)
	cam.look_at(Vector3(0.02, 1.24, 0.22), Vector3.UP)
	await _wait_frames(14)
	await _save_shot("chars_4_panzer_front_back.png")

	stage.queue_free()
	await _wait_frames(3)


func _capture_ingame_combat_shot() -> void:
	GameManager.reset_match()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(world)

	var player := world.get_node("Player") as PlayerController
	var rd := world.get_node("RoundDirector") as RoundDirector
	rd.set_process(false)
	player.set_physics_process(false)
	await _wait_frames(3)

	GameManager.add_points(15000, "")
	player.give_weapon("stg44")
	player.weapon_ctrl.snap_viewmodel()
	var db := world.get_node_or_null("HUD/BottomLeft/PointsRow/DeltaBox")
	if db:
		for ch in db.get_children():
			ch.queue_free()

	player.global_position = Vector3(3.8, 0.05, 6.2)
	player.rotation_degrees = Vector3(0, 22, 0)
	player.head.rotation_degrees = Vector3(-4, 0, 0)

	var boss := rd.spawn_panzer_boss(8, Vector3(0.5, 0.0, 0.8))
	boss.set_physics_process(false)
	boss.rotation_degrees.y = -152.0
	if boss._anim_player:
		boss._anim_player.play("FlameAttack", 0.0)
		boss._anim_player.advance(0.24)
	await _wait_frames(1)
	boss._set_flamethrower_active(true)

	var z1 := _spawn_zombie(world, "soldier", Vector3(2.4, 0.0, 2.3), -160.0, "Run", 0.20)
	var z2 := _spawn_zombie(world, "brute", Vector3(-1.0, 0.0, 1.6), -138.0, "Walk", 0.40)
	var z3 := _spawn_zombie(world, "crawler", Vector3(1.85, 0.0, 3.2), -152.0, "Crawl", 0.25)

	var hh := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	world.add_child(hh)
	hh.setup(180.0)
	hh.set_physics_process(false)
	hh.global_position = Vector3(3.2, 0.0, 3.1)
	hh.rotation_degrees.y = -140.0
	if hh._anim_player:
		hh._anim_player.play("Attack", 0.0)
		hh._anim_player.advance(0.18)

	await _wait_frames(8)
	await _save_shot("chars_5_combat_action.png")

	for n in [boss, z1, z2, z3, hh]:
		if is_instance_valid(n):
			n.queue_free()
	world.queue_free()
	await _wait_frames(2)


func _wait_frames(n: int) -> void:
	for _i in range(n):
		await get_tree().process_frame


func _save_shot(filename: String) -> void:
	await RenderingServer.frame_post_draw
	var img: Image = get_viewport().get_texture().get_image()
	var output := out_dir.path_join(filename)
	var result := img.save_png(output)
	if result != OK:
		push_error("Screenshot save failed: %s (%d)" % [output, result])
		get_tree().quit(1)
	print("Saved: ", output)

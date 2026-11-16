extends Node

var out_path: String = OS.get_environment("PERF_OUT_PATH") if OS.has_environment("PERF_OUT_PATH") else "/tmp/perf_report.json"
var _orig_quality: String = ""
var _orig_scale: float = 0.85
var _orig_msaa: String = "2x"
var _orig_vsync: bool = true
var _had_saved_cfg: bool = false


func _ready() -> void:
	print("[PERF] Starting benchmark...")
	await get_tree().process_frame
	var vp := get_viewport()
	get_window().size = Vector2i(1280, 720)
	_had_saved_cfg = FileAccess.file_exists(SettingsManager.SAVE_PATH)
	_orig_quality = SettingsManager.graphics_quality
	_orig_scale = SettingsManager.render_scale
	_orig_msaa = SettingsManager.msaa_mode
	_orig_vsync = SettingsManager.vsync_enabled

	var req_quality := OS.get_environment("PERF_QUALITY")
	if req_quality != "" and SettingsManager.has_method("set_graphics_quality"):
		SettingsManager.set_graphics_quality(req_quality)
	if OS.has_environment("PERF_RENDER_SCALE") and SettingsManager.has_method("set_render_scale"):
		SettingsManager.set_render_scale(float(OS.get_environment("PERF_RENDER_SCALE")))
	if OS.has_environment("PERF_MSAA") and SettingsManager.has_method("set_msaa_mode"):
		SettingsManager.set_msaa_mode(OS.get_environment("PERF_MSAA"))
	if OS.has_environment("PERF_VSYNC") and SettingsManager.has_method("set_vsync_enabled"):
		SettingsManager.set_vsync_enabled(OS.get_environment("PERF_VSYNC") == "1")
	elif DisplayServer.get_name() != "headless":
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)

	await _wait_frames(2)
	var pre_run_children := get_children().duplicate()

	var report := {
		"quality": SettingsManager.graphics_quality,
		"render_scale": float(SettingsManager.get("render_scale")) if SettingsManager.get("render_scale") != null else vp.scaling_3d_scale,
		"msaa_mode": str(SettingsManager.get("msaa_mode")) if SettingsManager.get("msaa_mode") != null else "4x",
		"viewport_size": [vp.size.x, vp.size.y],
		"scaling_3d_scale": vp.scaling_3d_scale,
		"scaling_3d_mode": vp.scaling_3d_mode,
		"msaa_3d": vp.msaa_3d,
		"occlusion_culling": vp.use_occlusion_culling,
	}

	# Stage 1: MainMenu
	print("[PERF] Stage 1: MainMenu...")
	GameManager.reset_match()
	var t_menu0 := Time.get_ticks_usec()
	var menu := (load("res://scenes/main_menu.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(menu)
	await RenderingServer.frame_post_draw
	var menu_load_ms := (Time.get_ticks_usec() - t_menu0) / 1000.0
	var menu_stats := await _measure_stage(1, 3)
	menu_stats["load_ms"] = snappedf(menu_load_ms, 0.1)
	report["menu"] = menu_stats
	_write_report(report)
	print("  [PERF] Stage 1 done: load=%.1fms frame=%.1fms dc=%d prim=%d tex=%.1fMB" % [menu_stats["load_ms"], menu_stats["avg_frame_ms"], menu_stats["draw_calls"], menu_stats["primitives"], menu_stats["tex_mb"]])
	menu.queue_free()
	await _wait_frames(2)

	# Stage 2: GameWorld load + initial settle
	print("[PERF] Stage 2: GameWorld load...")
	GameManager.reset_match()
	var t_w0 := Time.get_ticks_usec()
	var world := (load("res://scenes/game_world.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(world)
	await _wait_frames(1)
	await RenderingServer.frame_post_draw
	var world_load_ms := (Time.get_ticks_usec() - t_w0) / 1000.0
	report["world_load_ms"] = snappedf(world_load_ms, 0.1)
	_write_report(report)
	print("  [PERF] Stage 2 done: world_load=%.1fms" % report["world_load_ms"])

	var player := world.get_node("Player") as PlayerController
	var rd := world.get_node("RoundDirector") as RoundDirector
	rd.set_process(false)
	player.set_physics_process(false)

	# Stage 3: Spawn Courtyard (Power Off)
	print("[PERF] Stage 3: Courtyard...")
	player.global_position = Vector3(1.2, 0.05, 6.2)
	player.rotation_degrees = Vector3(0, 12, 0)
	player.head.rotation_degrees = Vector3(-4, 0, 0)
	player.weapon_ctrl.snap_viewmodel()
	report["courtyard"] = await _measure_stage(1, 3)
	_write_report(report)
	print("  [PERF] Stage 3 done: frame=%.1fms dc=%d prim=%d tex=%.1fMB" % [report["courtyard"]["avg_frame_ms"], report["courtyard"]["draw_calls"], report["courtyard"]["primitives"], report["courtyard"]["tex_mb"]])
	if OS.get_environment("PERF_STOP_AFTER") == "courtyard":
		await _cleanup_and_quit(pre_run_children, [], world)
		return

	# Stage 4: Reactor Hall Vista (Doors Unlocked + Power On)
	print("[PERF] Stage 4: Reactor...")
	GameManager.add_points(30000, "")
	(world.get_node("Interactables/PowerSwitch") as PowerSwitch).interact(player)
	(world.get_node("Interactables/DoorSpawnEast") as BuyableDoor).interact(player)
	(world.get_node("Interactables/DoorSpawnWest") as BuyableDoor).interact(player)
	for pl in world._power_lights:
		pl.light_energy = float(pl.get_meta("target_energy", 2.6))
	player.global_position = Vector3(1.5, 0.05, -14.0)
	player.rotation_degrees = Vector3(0, 14, 0)
	player.head.rotation_degrees = Vector3(-2, 0, 0)
	player.weapon_ctrl.snap_viewmodel()
	report["reactor"] = await _measure_stage(1, 3)
	_write_report(report)
	print("  [PERF] Stage 4 done: frame=%.1fms dc=%d prim=%d" % [report["reactor"]["avg_frame_ms"], report["reactor"]["draw_calls"], report["reactor"]["primitives"]])

	# Stage 5: Heavy Combat Stress (24 zombies + 1 Hellhound + 1 Panzer Boss + gunfire)
	print("[PERF] Stage 5: Combat Stress...")
	player.give_weapon("stg44")
	player.global_position = Vector3(4.5, 0.05, 6.0)
	player.rotation_degrees = Vector3(0, 26, 0)
	player.head.rotation_degrees = Vector3(-3, 0, 0)
	player.weapon_ctrl.snap_viewmodel()

	var t_sp0 := Time.get_ticks_usec()
	var z_scene := load("res://scenes/enemies/zombie.tscn") as PackedScene
	var h_scene := load("res://scenes/enemies/hellhound.tscn") as PackedScene
	var p_scene := load("res://scenes/enemies/panzer_boss.tscn") as PackedScene

	var spawned: Array[Node] = []
	var variants: Array[String] = []
	for _i in range(8):
		variants.append("soldier")
	for _i in range(6):
		variants.append("scientist")
	for _i in range(6):
		variants.append("worker")
	for _i in range(2):
		variants.append("brute")
	for _i in range(2):
		variants.append("crawler")

	for idx in range(variants.size()):
		var z := z_scene.instantiate() as ZombieAI
		z.setup(variants[idx], 350.0, 2.6, null)
		world.add_child(z)
		var col := idx % 6
		var row := idx / 6
		z.global_position = Vector3(-5.0 + float(col) * 2.1, 0.0, -3.5 + float(row) * 1.9)
		z.rotation_degrees.y = -155.0
		spawned.append(z)

	var hh := h_scene.instantiate() as HellhoundAI
	world.add_child(hh)
	hh.setup(180.0)
	hh.global_position = Vector3(3.15, 0.0, 3.35)
	hh.rotation_degrees.y = -112.0
	spawned.append(hh)

	var pb := p_scene.instantiate() as PanzerBossAI
	world.add_child(pb)
	pb.setup(8, 1400.0)
	pb.global_position = Vector3(-1.5, 0.0, -0.5)
	pb.rotation_degrees.y = -135.0
	spawned.append(pb)

	await RenderingServer.frame_post_draw
	var enemy_spawn_ms := (Time.get_ticks_usec() - t_sp0) / 1000.0

	# Fire 3 shots during warmup to include tracers/casings/decals/blood cost
	for _s in range(3):
		player.weapon_ctrl._fire_cooldown = 0.0
		player.weapon_ctrl._try_fire()
		await get_tree().process_frame

	var combat_stats := await _measure_stage(1, 3)
	combat_stats["enemy_spawn_ms"] = snappedf(enemy_spawn_ms, 0.1)
	report["combat_stress"] = combat_stats
	_write_report(report)

	print("=== PERF BENCH REPORT (%s | scale=%.2f | msaa=%s | occ=%s) ===" % [
		report["quality"],
		float(report["scaling_3d_scale"]),
		report["msaa_mode"],
		str(report["occlusion_culling"]),
	])
	print("  Menu: load=%.1fms | frame=%.1fms (p95=%.1fms) | dc=%d | prim=%d | vram=%.1fMB (tex=%.1fMB)" % [
		menu_stats["load_ms"], menu_stats["avg_frame_ms"], menu_stats["p95_frame_ms"],
		menu_stats["draw_calls"], menu_stats["primitives"], menu_stats["vram_mb"], menu_stats["tex_mb"],
	])
	print("  World Load: %.1fms" % report["world_load_ms"])
	print("  Courtyard: frame=%.1fms (p95=%.1fms) | dc=%d | prim=%d | obj=%d | vram=%.1fMB (tex=%.1fMB)" % [
		report["courtyard"]["avg_frame_ms"], report["courtyard"]["p95_frame_ms"],
		report["courtyard"]["draw_calls"], report["courtyard"]["primitives"], report["courtyard"]["objects"],
		report["courtyard"]["vram_mb"], report["courtyard"]["tex_mb"],
	])
	print("  Reactor:   frame=%.1fms (p95=%.1fms) | dc=%d | prim=%d | obj=%d" % [
		report["reactor"]["avg_frame_ms"], report["reactor"]["p95_frame_ms"],
		report["reactor"]["draw_calls"], report["reactor"]["primitives"], report["reactor"]["objects"],
	])
	print("  Combat(26): spawn=%.1fms | frame=%.1fms (p95=%.1fms) | proc=%.2fms phys=%.2fms | dc=%d | prim=%d | vram=%.1fMB (tex=%.1fMB)" % [
		combat_stats["enemy_spawn_ms"], combat_stats["avg_frame_ms"], combat_stats["p95_frame_ms"],
		combat_stats["process_ms"], combat_stats["physics_ms"],
		combat_stats["draw_calls"], combat_stats["primitives"],
		combat_stats["vram_mb"], combat_stats["tex_mb"],
	])
	print("WROTE: ", out_path)

	await _cleanup_and_quit(pre_run_children, spawned, world)


func _cleanup_and_quit(pre_run_children: Array, spawned: Array[Node], world: Node) -> void:
	for tw in get_tree().get_processed_tweens():
		if tw and tw.is_valid():
			tw.kill()
	for ch in get_children():
		if not pre_run_children.has(ch) and is_instance_valid(ch):
			remove_child(ch)
			ch.queue_free()
	for s in spawned:
		if is_instance_valid(s):
			s.queue_free()
	if is_instance_valid(world):
		world.queue_free()
	AudioManager.stop_ambience()
	if AudioManager._ambience_player:
		AudioManager._ambience_player.stream = null
	for p2 in AudioManager._pool_2d:
		if p2:
			p2.stop()
			p2.stream = null
	for p3 in AudioManager._pool_3d:
		if p3:
			p3.stop()
			p3.stream = null
	await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().process_frame
	WeaponController.clear_shared_caches()
	WpnShellCasing.clear_shared_caches()
	WpnBulletDecal.clear_shared_caches()
	GibChunk.clear_shared_caches()
	BloodDecal.clear_shared_caches()
	if _orig_quality != "":
		SettingsManager.set_graphics_quality(_orig_quality)
		SettingsManager.set_render_scale(_orig_scale)
		SettingsManager.set_msaa_mode(_orig_msaa)
		SettingsManager.set_vsync_enabled(_orig_vsync)
	if not _had_saved_cfg and FileAccess.file_exists(SettingsManager.SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SettingsManager.SAVE_PATH))
	get_tree().quit(0)


func _write_report(report: Dictionary) -> void:
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(report, "\t"))
		f.close()


func _wait_frames(n: int) -> void:
	for _i in range(n):
		await get_tree().process_frame


func _measure_stage(warmup_frames: int, sample_frames: int) -> Dictionary:
	for _i in range(warmup_frames):
		await RenderingServer.frame_post_draw

	var frame_times: Array[float] = []
	var proc_sum: float = 0.0
	var phys_sum: float = 0.0
	var dc_sum: float = 0.0
	var prim_sum: float = 0.0
	var obj_sum: float = 0.0

	var prev_us := Time.get_ticks_usec()
	for _i in range(sample_frames):
		await RenderingServer.frame_post_draw
		var now_us := Time.get_ticks_usec()
		frame_times.append((now_us - prev_us) / 1000.0)
		prev_us = now_us
		proc_sum += Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
		phys_sum += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		dc_sum += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		prim_sum += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
		obj_sum += Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)

	frame_times.sort()
	var sum_ms := 0.0
	for ft in frame_times:
		sum_ms += ft
	var p95_idx := clampi(int(ceil(frame_times.size() * 0.95)) - 1, 0, frame_times.size() - 1)
	var vram_mb := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / (1024.0 * 1024.0)
	var tex_mb := Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / (1024.0 * 1024.0)
	var static_mb := Performance.get_monitor(Performance.MEMORY_STATIC) / (1024.0 * 1024.0)

	return {
		"avg_frame_ms": snappedf(sum_ms / maxf(1, sample_frames), 0.1),
		"p95_frame_ms": snappedf(frame_times[p95_idx], 0.1),
		"min_frame_ms": snappedf(frame_times[0], 0.1),
		"max_frame_ms": snappedf(frame_times[frame_times.size() - 1], 0.1),
		"process_ms": snappedf(proc_sum / maxf(1, sample_frames), 0.01),
		"physics_ms": snappedf(phys_sum / maxf(1, sample_frames), 0.01),
		"draw_calls": int(round(dc_sum / maxf(1, sample_frames))),
		"primitives": int(round(prim_sum / maxf(1, sample_frames))),
		"objects": int(round(obj_sum / maxf(1, sample_frames))),
		"vram_mb": snappedf(vram_mb, 0.1),
		"tex_mb": snappedf(tex_mb, 0.1),
		"static_mb": snappedf(static_mb, 0.1),
		"node_count": int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),
		"object_count": int(Performance.get_monitor(Performance.OBJECT_COUNT)),
	}

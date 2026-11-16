extends RefCounted
class_name TestsPerf


static func run_checks(runner: Node) -> void:
	print("[Perf] Running performance, quality preset, asset dedup & cache regression checks...")
	GameManager.reset_match()

	var had_saved_cfg := FileAccess.file_exists(SettingsManager.SAVE_PATH)
	var orig_gfx := SettingsManager.graphics_quality
	var orig_scale := SettingsManager.render_scale
	var orig_msaa := SettingsManager.msaa_mode
	var orig_vsync := SettingsManager.vsync_enabled

	# 1. SettingsManager laptop-friendly defaults (fresh instance, independent of user://) & preset/FSR/MSAA controls
	var sm_script := load("res://scripts/autoload/settings_manager.gd") as GDScript
	var fresh_sm = sm_script.new()
	_check(runner, fresh_sm != null and fresh_sm.graphics_quality == "Medium", "Perf: default graphics_quality == Medium")
	_check(runner, fresh_sm != null and is_equal_approx(fresh_sm.render_scale, 0.85), "Perf: default render_scale == 0.85")
	_check(runner, fresh_sm != null and fresh_sm.msaa_mode == "2x", "Perf: default msaa_mode == 2x")
	_check(runner, fresh_sm != null and fresh_sm.vsync_enabled == true, "Perf: default vsync_enabled == true")
	if fresh_sm != null:
		fresh_sm.free()

	SettingsManager.set_graphics_quality("Medium")
	SettingsManager.set_render_scale(0.85)
	SettingsManager.set_msaa_mode("2x")
	SettingsManager.set_vsync_enabled(true)

	var vp := runner.get_viewport()
	if vp:
		_check(runner, vp.use_occlusion_culling, "Perf: Viewport occlusion culling enabled")
		_check(runner, vp.scaling_3d_mode == Viewport.SCALING_3D_MODE_FSR, "Perf: FSR scaling active when render_scale < 1.0")
		_check(runner, is_equal_approx(vp.scaling_3d_scale, 0.85), "Perf: Viewport scaling_3d_scale == 0.85")
		_check(runner, vp.msaa_3d == Viewport.MSAA_2X, "Perf: Viewport MSAA_3D == MSAA_2X")

	SettingsManager.set_render_scale(0.1)
	_check(runner, is_equal_approx(SettingsManager.render_scale, 0.5), "Perf: render_scale clamps low to 0.50")
	SettingsManager.set_render_scale(1.8)
	_check(runner, is_equal_approx(SettingsManager.render_scale, 1.0), "Perf: render_scale clamps high to 1.00")
	if vp:
		_check(runner, vp.scaling_3d_mode == Viewport.SCALING_3D_MODE_BILINEAR, "Perf: render_scale == 1.0 switches to BILINEAR")
	SettingsManager.set_msaa_mode("Off")
	_check(runner, vp == null or vp.msaa_3d == Viewport.MSAA_DISABLED, "Perf: msaa_mode Off disables MSAA_3D")
	SettingsManager.set_msaa_mode("4x")
	_check(runner, vp == null or vp.msaa_3d == Viewport.MSAA_4X, "Perf: msaa_mode 4x enables MSAA_4X")
	SettingsManager.set_graphics_quality("InvalidPreset")
	_check(runner, SettingsManager.graphics_quality == "Medium", "Perf: invalid graphics quality preset rejected")

	SettingsManager.set_graphics_quality("Medium")
	SettingsManager.set_render_scale(0.85)
	SettingsManager.set_msaa_mode("2x")
	SettingsManager.set_vsync_enabled(true)

	# 2. Deduplicated texture map + .glb.import + _shared_tex import compression checks
	var map_path := "res://tools/import/shared_tex_map.json"
	_check(runner, FileAccess.file_exists(map_path), "Perf: shared_tex_map.json exists")
	var mf := FileAccess.open(map_path, FileAccess.READ)
	var smap_var = JSON.parse_string(mf.get_as_text()) if mf else null
	if mf:
		mf.close()
	_check(runner, smap_var is Dictionary and (smap_var as Dictionary).size() >= 90, "Perf: shared_tex_map covers >= 90 models")

	if smap_var is Dictionary:
		var smap: Dictionary = smap_var
		var bad_glb_imports := 0
		var missing_shared := 0
		var bad_tex_imports := 0
		var checked_tex := {}
		for model_path_v in smap.keys():
			var model_path := str(model_path_v)
			var gi := ConfigFile.new()
			if gi.load(model_path + ".import") != OK:
				bad_glb_imports += 1
			else:
				var emb := int(gi.get_value("params", "gltf/embedded_image_handling", -1))
				var ipath := str(gi.get_value("params", "import_script/path", ""))
				if emb != 0 or ipath != "res://tools/import/dedup_model_textures.gd":
					bad_glb_imports += 1
			var mat_table: Dictionary = smap[model_path_v]
			for mat_name in mat_table.keys():
				var spec: Dictionary = mat_table[mat_name]
				for slot in ["albedo", "normal", "orm", "emissive"]:
					if not spec.has(slot):
						continue
					var tpath := str(spec[slot])
					if checked_tex.has(tpath):
						continue
					checked_tex[tpath] = true
					if not tpath.begins_with("res://assets/models/_shared_tex/") or not FileAccess.file_exists(tpath):
						missing_shared += 1
						continue
					var ti := ConfigFile.new()
					if ti.load(tpath + ".import") != OK:
						bad_tex_imports += 1
					else:
						var cm := int(ti.get_value("params", "compress/mode", -1))
						var slim := int(ti.get_value("params", "process/size_limit", 0))
						if cm != 2 or slim <= 0 or slim > 768:
							bad_tex_imports += 1
		_check(runner, bad_glb_imports == 0, "Perf: all mapped .glb.import files disable embedded images and wire dedup_model_textures.gd")
		_check(runner, missing_shared == 0, "Perf: all deduplicated shared textures exist under res://assets/models/_shared_tex/ (%d checked)" % checked_tex.size())
		_check(runner, bad_tex_imports == 0, "Perf: all _shared_tex/*.import files use VRAM compression (mode=2) and size_limit <= 768")

	var sample_glb := load("res://assets/models/characters/zombie_soldier.glb") as PackedScene
	var sample_inst := sample_glb.instantiate() if sample_glb else null
	var shared_mat_bound := false
	if sample_inst:
		for mi in sample_inst.find_children("", "MeshInstance3D", true, false):
			var m3 := mi as MeshInstance3D
			if m3 and m3.mesh and m3.mesh.get_surface_count() > 0:
				var mat := m3.mesh.surface_get_material(0)
				if mat is StandardMaterial3D and (mat as StandardMaterial3D).albedo_texture != null:
					if (mat as StandardMaterial3D).albedo_texture.resource_path.begins_with("res://assets/models/_shared_tex/"):
						shared_mat_bound = true
						break
		sample_inst.free()
	_check(runner, shared_mat_bound, "Perf: imported zombie_soldier.glb resolves albedo_texture from _shared_tex/")

	# 3. Runtime optimizations in GameWorld
	var world_scene := load("res://scenes/game_world.tscn") as PackedScene
	_check(runner, world_scene != null, "Perf: game_world.tscn loads cleanly")
	if world_scene == null:
		return

	var world := world_scene.instantiate() as GameWorld
	runner.add_child(world)
	await runner.get_tree().process_frame
	await runner.get_tree().physics_frame

	var rd := world.get_node_or_null("RoundDirector") as RoundDirector
	var player := world.get_node_or_null("Player") as PlayerController
	_check(runner, rd != null and player != null, "Perf: GameWorld RoundDirector and Player present")
	if rd == null or player == null:
		world.queue_free()
		return
	rd.set_process(false)
	player.set_physics_process(false)

	var arch_batches := 0
	var light_shaft_batches := 0
	for c in world.geo_root.get_children():
		if c.name.begins_with("ArchBatch_"):
			arch_batches += 1
		elif c.name.begins_with("MoonLightShafts_"):
			light_shaft_batches += 1
	_check(runner, arch_batches >= 4, "Perf: SurfaceTool architecture batching merged props into %d ArchBatch nodes" % arch_batches)
	_check(runner, light_shaft_batches >= 2, "Perf: volumetric light shafts batched into %d MoonLightShafts nodes" % light_shaft_batches)

	var occluders := world.geo_root.find_children("", "OccluderInstance3D", true, false)
	var box_occs := 0
	for o in occluders:
		if (o as OccluderInstance3D).occluder is BoxOccluder3D:
			box_occs += 1
	_check(runner, box_occs >= 10, "Perf: %d BoxOccluder3D occlusion instances built in GameWorld" % box_occs)

	var faded_decals := 0
	for d in world._decals:
		if is_instance_valid(d) and d.distance_fade_enabled:
			faded_decals += 1
	_check(runner, world._decals.size() >= 15 and faded_decals == world._decals.size(), "Perf: all %d static env decals enable distance fade" % world._decals.size())

	var lights := world.geo_root.find_children("", "Light3D", true, false)
	var unfaded_lights := 0
	for l in lights:
		var l3 := l as Light3D
		if not (l3 is DirectionalLight3D) and not l3.distance_fade_enabled:
			unfaded_lights += 1
	_check(runner, lights.size() >= 15 and unfaded_lights == 0, "Perf: all %d non-directional lights in geo_root enable distance fade" % lights.size())

	_check(runner, world._prewarmed_resources.size() >= 15, "Perf: GameWorld prewarmed %d enemy/FX resources" % world._prewarmed_resources.size())

	# Quality scaling checks on MoonLight & WorldEnvironment
	var env := world.world_env.environment
	_check(runner, world.moon_light.shadow_enabled and world.moon_light.directional_shadow_mode == DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS, "Perf: Medium quality uses 2-split directional shadows")
	_check(runner, is_equal_approx(world.moon_light.directional_shadow_max_distance, 45.0), "Perf: Medium shadow distance == 45.0m")
	_check(runner, env != null and not env.ssao_enabled and not env.ssil_enabled and not env.volumetric_fog_enabled, "Perf: Medium disables heavy SSAO/SSIL/volumetric fog")

	SettingsManager.set_graphics_quality("High")
	_check(runner, world.moon_light.directional_shadow_mode == DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS and is_equal_approx(world.moon_light.directional_shadow_max_distance, 65.0), "Perf: High switches to 4-split shadows @ 65.0m")
	_check(runner, env.ssao_enabled and env.ssil_enabled and env.volumetric_fog_enabled, "Perf: High enables SSAO/SSIL/volumetric fog")

	SettingsManager.set_graphics_quality("Low")
	_check(runner, not world.moon_light.shadow_enabled and not env.glow_enabled, "Perf: Low disables MoonLight shadows and glow")
	SettingsManager.set_graphics_quality("Medium")

	# 4. RoundDirector spawn caching & zone invalidation
	rd.invalidate_spawn_caches()
	_check(runner, rd._windows_cache_dirty and rd._dog_spawns_cache_dirty, "Perf: invalidate_spawn_caches marks both caches dirty")
	var w_base: Array[Node] = rd._get_unlocked_windows()
	var d_base: Array[Node3D] = rd._get_unlocked_dog_spawns()
	_check(runner, not rd._windows_cache_dirty and not rd._dog_spawns_cache_dirty and w_base.size() >= 2, "Perf: RoundDirector populates spawn caches cleanly")
	var w_cached: Array[Node] = rd._get_unlocked_windows()
	_check(runner, w_cached.size() == w_base.size(), "Perf: cached unlocked windows lookup matches cleanly")

	GameManager.unlocked_zones["east_courtyard"] = true
	GameManager.zone_unlocked.emit("east_courtyard")
	_check(runner, rd._windows_cache_dirty and rd._dog_spawns_cache_dirty, "Perf: zone_unlocked signal invalidates RoundDirector caches")
	var w_unlocked: Array[Node] = rd._get_unlocked_windows()
	_check(runner, not rd._windows_cache_dirty and w_unlocked.size() >= w_base.size(), "Perf: RoundDirector rebuilds window cache after zone unlock")

	# 5. Enemy AI caching + Hellhound flash distance fade + Staggered bone sync
	var z := (load("res://scenes/enemies/zombie.tscn") as PackedScene).instantiate() as ZombieAI
	z.setup("soldier", 200.0, 2.2, null)
	world.add_child(z)
	await runner.get_tree().process_frame
	z.set_physics_process(false)
	_check(runner, z._get_player() == player and z._player == player, "Perf: ZombieAI _get_player() caches Player")

	z.global_position = player.global_position + Vector3(26.0, 0.0, 0.0)
	z._head_synced_once = false
	z._head_sync_tick = 1
	z.head_area.position = Vector3(0.0, 9.9, 0.0)
	z._physics_process(0.016) # tick -> 2, first sync forced
	_check(runner, z._head_synced_once and z.head_area.position.y < 5.0, "Perf: ZombieAI syncs head bone on first physics tick even > 14m")

	z.head_area.position = Vector3(0.0, 9.9, 0.0)
	z._physics_process(0.016) # tick -> 3 != 0 (> 14m skips)
	_check(runner, z.head_area.position.y > 9.0, "Perf: ZombieAI skips off-phase head bone sync > 14m")

	z._physics_process(0.016) # tick -> 0 (> 14m syncs every 4th tick)
	_check(runner, z.head_area.position.y < 5.0, "Perf: ZombieAI updates head bone on 4th tick > 14m")

	z.global_position = player.global_position + Vector3(5.0, 0.0, 0.0)
	z._head_sync_tick = 1
	z.head_area.position = Vector3(0.0, 9.9, 0.0)
	z._physics_process(0.016) # tick -> 2, within 14m always syncs
	_check(runner, z.head_area.position.y < 5.0, "Perf: ZombieAI syncs head bone every tick within 14m")
	z.queue_free()

	var pb := (load("res://scenes/enemies/panzer_boss.tscn") as PackedScene).instantiate() as PanzerBossAI
	pb.setup(8, 1400.0)
	world.add_child(pb)
	await runner.get_tree().process_frame
	pb.set_physics_process(false)
	_check(runner, pb._get_player() == player and pb._player == player, "Perf: PanzerBossAI _get_player() caches Player")

	pb.global_position = player.global_position + Vector3(25.0, 0.0, 0.0)
	pb._head_synced_once = false
	pb._head_sync_tick = 1
	pb.head_area.position = Vector3(0.0, 9.9, 0.0)
	pb._physics_process(0.016) # tick -> 2, first sync forced
	_check(runner, pb._head_synced_once and pb.head_area.position.y < 5.0, "Perf: PanzerBossAI syncs head bone on first physics tick even > 14m")

	pb.head_area.position = Vector3(0.0, 9.9, 0.0)
	pb._physics_process(0.016) # tick -> 3 (> 14m skips)
	_check(runner, pb.head_area.position.y > 9.0, "Perf: PanzerBossAI skips off-phase head bone sync > 14m")
	pb.global_position = player.global_position + Vector3(5.0, 0.0, 0.0)
	pb._physics_process(0.016) # within 14m always syncs
	_check(runner, pb.head_area.position.y < 5.0, "Perf: PanzerBossAI syncs head bone every tick within 14m")
	pb.queue_free()

	var hh := (load("res://scenes/enemies/hellhound.tscn") as PackedScene).instantiate() as HellhoundAI
	world.add_child(hh)
	await runner.get_tree().process_frame
	hh.set_physics_process(false)
	_check(runner, hh._get_player() == player and hh._player == player, "Perf: HellhoundAI _get_player() caches Player")
	var flash_faded := false
	for ch in hh.get_children():
		if ch is OmniLight3D and ch != hh.ember_light and (ch as OmniLight3D).distance_fade_enabled:
			flash_faded = true
			break
	_check(runner, flash_faded, "Perf: HellhoundAI spawn flash light enables distance fade")
	hh.queue_free()

	# 6. WeaponController HUD cache & Static FX clear_shared_caches() cleanup
	var hud := world.get_node_or_null("HUD")
	_check(runner, player.weapon_ctrl._get_hud() == hud and player.weapon_ctrl._hud == hud, "Perf: WeaponController _get_hud() caches HUD node")

	WeaponController._ensure_tracer_assets()
	WpnShellCasing._get_shotgun_hull_mesh()
	WpnBulletDecal._get_decal_texture(false)
	WpnBulletDecal._get_decal_texture(true)
	GibChunk._ensure_shared_assets()
	BloodDecal._get_shared_mat()

	for tw in runner.get_tree().get_processed_tweens():
		if tw and tw.is_valid():
			tw.kill()
	world.queue_free()
	await runner.get_tree().process_frame
	await runner.get_tree().physics_frame
	await runner.get_tree().process_frame

	WeaponController.clear_shared_caches()
	WpnShellCasing.clear_shared_caches()
	WpnBulletDecal.clear_shared_caches()
	GibChunk.clear_shared_caches()
	BloodDecal.clear_shared_caches()

	var caches_cleared := (
		WeaponController._active_tracers.is_empty()
		and WeaponController._tracer_mesh == null
		and WeaponController._tracer_mat_std == null
		and WeaponController._tracer_mat_pap == null
		and WpnShellCasing._active_shells.is_empty()
		and WpnShellCasing._shotgun_hull_mesh == null
		and WpnBulletDecal._active_decals.is_empty()
		and WpnBulletDecal._tex_concrete == null
		and WpnBulletDecal._tex_metal == null
		and GibChunk._active_gibs.is_empty()
		and GibChunk._mesh_armor == null
		and GibChunk._mat_flesh == null
		and BloodDecal._active_decals.is_empty()
		and BloodDecal._shared_mat == null
	)
	_check(runner, caches_cleared, "Perf: clear_shared_caches resets all static FX arrays, meshes, materials & textures cleanly")
	SettingsManager.set_graphics_quality(orig_gfx)
	SettingsManager.set_render_scale(orig_scale)
	SettingsManager.set_msaa_mode(orig_msaa)
	SettingsManager.set_vsync_enabled(orig_vsync)
	if not had_saved_cfg and FileAccess.file_exists(SettingsManager.SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SettingsManager.SAVE_PATH))


static func _check(runner: Node, cond: bool, msg: String) -> void:
	if runner.has_method("_check"):
		runner._check(cond, msg)
	else:
		assert(cond, msg)

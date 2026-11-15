extends RefCounted
class_name TestsJitter


static func run_checks(runner: Node) -> void:
	print("[Jitter] Running weapon/camera jitter & smoothing verification checks...")
	GameManager.reset_match()

	var player_scene := load("res://scenes/player/player.tscn") as PackedScene
	_check(runner, player_scene != null, "Jitter: player.tscn loads cleanly")
	if player_scene == null:
		return

	# 1. Exponential smoothing math invariants
	_check(runner, is_zero_approx(WeaponController._exp_alpha(18.0, 0.0)), "Jitter: _exp_alpha(18, 0.0) == 0.0")
	_check(runner, is_zero_approx(WeaponController._exp_alpha(18.0, -0.05)), "Jitter: _exp_alpha clamps negative delta to 0.0")
	var spike_alpha := WeaponController._exp_alpha(18.0, 0.12)
	_check(runner, spike_alpha > 0.8 and spike_alpha < 1.0, "Jitter: _exp_alpha(18, 0.12) stays strictly < 1.0 (%.4f)" % spike_alpha)
	var two_step := (1.0 - WeaponController._exp_alpha(14.0, 0.06)) * (1.0 - WeaponController._exp_alpha(14.0, 0.06))
	var one_step := 1.0 - WeaponController._exp_alpha(14.0, 0.12)
	_check(runner, absf(two_step - one_step) < 0.00001, "Jitter: exponential decay is frame-rate independent (2x60ms == 120ms)")

	var player := player_scene.instantiate() as PlayerController
	runner.add_child(player)
	var wc := player.weapon_ctrl
	_check(runner, player != null and wc != null, "Jitter: PlayerController and WeaponController initialized")
	if player == null or wc == null:
		return

	# Head node must opt out of SceneTree physics interpolation so _process camera/viewmodel stay synced
	_check(runner, player.head.physics_interpolation_mode == Node.PHYSICS_INTERPOLATION_MODE_OFF, "Jitter: Head subtree disables physics interpolation")
	_check(runner, player.camera.near <= 0.05, "Jitter: Camera3D near plane <= 0.05 (%.3f)" % player.camera.near)

	var cur_w: Dictionary = wc.get_current_state()
	var hip_pos: Vector3 = WeaponDB.get_stat(cur_w, "hip_pos")
	var ads_pos: Vector3 = WeaponDB.get_stat(cur_w, "ads_pos")
	var base_fov := SettingsManager.fov
	var ads_fov := base_fov * float(WeaponDB.get_stat(cur_w, "ads_fov_mult"))

	# 2. Idle zero-velocity invariance across 144Hz, 60Hz, and 0.12s spike frames
	wc.snap_viewmodel()
	var max_idle_pos_err := 0.0
	var max_idle_rot_err := 0.0
	var max_idle_cam_err := 0.0
	var max_idle_head_err := 0.0
	var mixed_deltas := [1.0 / 144.0, 1.0 / 60.0, 0.033, 0.12, 0.008]
	for i in range(120):
		var dt: float = mixed_deltas[i % mixed_deltas.size()]
		player._process(dt)
		wc._animate_viewmodel(dt)
		max_idle_pos_err = maxf(max_idle_pos_err, wc.viewmodel_pivot.position.distance_to(hip_pos))
		max_idle_rot_err = maxf(max_idle_rot_err, wc.viewmodel_pivot.rotation.length())
		max_idle_cam_err = maxf(max_idle_cam_err, player.camera.position.length() + player.camera.rotation.length())
		max_idle_head_err = maxf(max_idle_head_err, absf(player.head.position.y - 1.62))
	_check(runner, max_idle_pos_err < 0.00001 and max_idle_rot_err < 0.00001, "Jitter: idle viewmodel invariant across mixed FPS + 0.12s spikes")
	_check(runner, max_idle_cam_err < 0.00001 and max_idle_head_err < 0.00001, "Jitter: idle camera & head height invariant across mixed FPS")

	# 3a-1. Low-FPS spike (delta=0.12) pure viewmodel displacement converges monotonically on all 6 DOF with zero sign-flip oscillation
	wc.snap_viewmodel()
	wc.viewmodel_pivot.position = hip_pos + Vector3(0.08, -0.06, 0.09)
	wc.viewmodel_pivot.rotation = Vector3(0.35, -0.25, 0.20)
	var prev_pos := wc.viewmodel_pivot.position - hip_pos
	var prev_rot := wc.viewmodel_pivot.rotation
	var pure_monotonic := true
	var pure_no_flip := true
	for _i in range(25):
		wc._animate_viewmodel(0.12)
		var dp := wc.viewmodel_pivot.position - hip_pos
		var dr := wc.viewmodel_pivot.rotation
		if dp.x < -0.00001 or dp.y > 0.00001 or dp.z < -0.00001:
			pure_no_flip = false
		if dr.x < -0.00001 or dr.y > 0.00001 or dr.z < -0.00001:
			pure_no_flip = false
		if dp.x > prev_pos.x + 0.00001 or dp.y < prev_pos.y - 0.00001 or dp.z > prev_pos.z + 0.00001:
			pure_monotonic = false
		if dr.x > prev_rot.x + 0.00001 or dr.y < prev_rot.y - 0.00001 or dr.z > prev_rot.z + 0.00001:
			pure_monotonic = false
		prev_pos = dp
		prev_rot = dr
	_check(runner, pure_no_flip and pure_monotonic, "Jitter: delta=0.12 viewmodel 6-DOF displacement decays monotonically without sign-flip")

	# 3a-2. Low-FPS spike (delta=0.12) active recoil kick + displacement converges without sign-flip oscillation
	wc.snap_viewmodel()
	wc.viewmodel_pivot.position = hip_pos + Vector3(0.08, 0.06, 0.09)
	wc.viewmodel_pivot.rotation = Vector3(0.35, -0.25, 0.20)
	wc._kick_pos = Vector3(0.0, 0.02, 0.08)
	wc._kick_rot = Vector3(0.20, -0.05, 0.0)
	var prev_err_x := wc.viewmodel_pivot.position.x - hip_pos.x
	var prev_rot_x := wc.viewmodel_pivot.rotation.x
	var prev_rot_y := wc.viewmodel_pivot.rotation.y
	var prev_kick_z := wc._kick_pos.z
	var monotonic_spike := true
	var no_sign_flip := true
	for _i in range(25):
		wc._animate_viewmodel(0.12)
		var err_x := wc.viewmodel_pivot.position.x - hip_pos.x
		var rot_x := wc.viewmodel_pivot.rotation.x
		var rot_y := wc.viewmodel_pivot.rotation.y
		var kick_z := wc._kick_pos.z
		if err_x < -0.00001 or rot_x < -0.00001 or rot_y > 0.00001 or kick_z < -0.00001:
			no_sign_flip = false
		if err_x > prev_err_x + 0.00001 or rot_x > prev_rot_x + 0.00001 or rot_y < prev_rot_y - 0.00001 or kick_z > prev_kick_z + 0.00001:
			monotonic_spike = false
		prev_err_x = err_x
		prev_rot_x = rot_x
		prev_rot_y = rot_y
		prev_kick_z = kick_z
	_check(runner, no_sign_flip and monotonic_spike, "Jitter: delta=0.12 viewmodel & kick convergence is monotonic with zero sign-flip oscillation")
	_check(runner, wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001 and wc.viewmodel_pivot.rotation.length() < 0.0001, "Jitter: delta=0.12 viewmodel converges cleanly to hip rest")

	# 3b. Camera recoil recovery at delta=0.12
	player.add_camera_recoil(0.18, 0.0)
	var prev_cam_pitch := player._recoil_pitch
	var cam_recoil_ok := true
	for _i in range(25):
		player._process(0.12)
		var p := player.camera.rotation.x
		if p < -0.00001 or p > prev_cam_pitch + 0.00001:
			cam_recoil_ok = false
		prev_cam_pitch = p
	_check(runner, cam_recoil_ok and absf(player.camera.rotation.x) < 0.0001, "Jitter: delta=0.12 camera recoil recovers monotonically without sign-flip")

	# 3c. ADS position, cant & FOV monotonic convergence at delta=0.12
	wc.snap_viewmodel()
	wc.is_aiming = true
	var ads_ok := true
	var prev_fov := player.camera.fov
	var prev_cant := wc.model_holder.rotation.y
	for _i in range(25):
		wc._animate_viewmodel(0.12)
		if player.camera.fov < ads_fov - 0.001 or player.camera.fov > prev_fov + 0.001:
			ads_ok = false
		if wc.model_holder.rotation.y < -0.0001 or wc.model_holder.rotation.y > prev_cant + 0.0001:
			ads_ok = false
		if wc.viewmodel_pivot.position.x < ads_pos.x - 0.0001 or wc.viewmodel_pivot.position.x > hip_pos.x + 0.0001:
			ads_ok = false
		prev_fov = player.camera.fov
		prev_cant = wc.model_holder.rotation.y
	_check(runner, ads_ok and wc.viewmodel_pivot.position.distance_to(ads_pos) < 0.0001 and absf(player.camera.fov - ads_fov) < 0.001, "Jitter: ADS position/cant/FOV converge monotonically at delta=0.12")
	wc.is_aiming = false
	for _i in range(25):
		wc._animate_viewmodel(0.12)
	_check(runner, wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001 and absf(player.camera.fov - base_fov) < 0.001, "Jitter: exiting ADS returns monotonically to hip pose & base FOV")

	# 4. Look sway two-stage exponential follower (pos + rot, bounded, smooth on noisy mouse polling)
	wc.snap_viewmodel()
	wc.add_look_sway(Vector2(35.0, -25.0))
	wc._animate_viewmodel(0.016)
	var sway_pos_moved := wc.viewmodel_pivot.position.distance_to(hip_pos) > 0.0005
	var sway_rot_moved := wc.viewmodel_pivot.rotation.length() > 0.0005
	var sway_bounded := wc._sway_offset.length() < 0.04 and absf(wc.viewmodel_pivot.position.x - hip_pos.x) < 0.04
	var sway_no_flip := true
	for _i in range(50):
		wc._animate_viewmodel(0.016)
		if wc._sway_offset.x > 0.00001 or wc._sway_offset.y > 0.00001:
			sway_no_flip = false
	_check(runner, sway_pos_moved and sway_rot_moved and sway_bounded and sway_no_flip, "Jitter: look sway drives smooth pos+rot without overshoot or sign flip")
	_check(runner, wc._sway_offset.length() < 0.0001 and wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001, "Jitter: look sway converges back to exact idle pose")

	# Uneven 144Hz mouse packets should produce smooth viewmodel steps (no micro-twitch jumps)
	wc.snap_viewmodel()
	var max_mouse_step := 0.0
	var last_vm_pos := wc.viewmodel_pivot.position
	for i in range(60):
		if i % 2 == 0:
			wc.add_look_sway(Vector2(18.0, -8.0))
		wc._animate_viewmodel(1.0 / 144.0)
		max_mouse_step = maxf(max_mouse_step, wc.viewmodel_pivot.position.distance_to(last_vm_pos))
		last_vm_pos = wc.viewmodel_pivot.position
	_check(runner, max_mouse_step < 0.0035, "Jitter: uneven mouse polling packets smoothed cleanly (max_step=%.5fm)" % max_mouse_step)

	# ADS clamps look sway tighter for steady aiming
	wc.snap_viewmodel()
	wc.is_aiming = true
	wc.add_look_sway(Vector2(500.0, 500.0))
	_check(runner, absf(wc._sway_target.x) <= 0.0101 and absf(wc._sway_target.y) <= 0.0101, "Jitter: ADS sway tightly clamped (<= 0.010)")
	wc.is_aiming = false
	wc.snap_viewmodel()

	# 5. Camera + Viewmodel bob smoothness & zero 0.4 m/s binary threshold snap
	player._grounded_override = true
	var thresh_speeds := [0.20, 0.35, 0.45, 0.35, 0.45, 0.60, 0.38, 0.42, 0.30, 0.0]
	var max_thresh_cam_step := 0.0
	var max_thresh_vm_step := 0.0
	var prev_cam_pos := player.camera.position
	var prev_vm_pos := wc.viewmodel_pivot.position
	for s in thresh_speeds:
		for _sub in range(4):
			player.velocity = Vector3(0.0, 0.0, -s)
			player._process(0.016)
			wc._animate_viewmodel(0.016)
			max_thresh_cam_step = maxf(max_thresh_cam_step, player.camera.position.distance_to(prev_cam_pos))
			max_thresh_vm_step = maxf(max_thresh_vm_step, wc.viewmodel_pivot.position.distance_to(prev_vm_pos))
			prev_cam_pos = player.camera.position
			prev_vm_pos = wc.viewmodel_pivot.position
	_check(runner, max_thresh_cam_step < 0.002 and max_thresh_vm_step < 0.003, "Jitter: crossing 0.4 m/s speed threshold has zero snap (cam=%.5f, vm=%.5f)" % [max_thresh_cam_step, max_thresh_vm_step])

	# High-FPS (144Hz) walk -> sprint -> grounded flicker -> stop convergence
	wc.snap_viewmodel()
	player.camera.position = Vector3.ZERO
	player._bob_weight = 0.0
	player._sprint_blend = 0.0
	var max_walk_cam_step := 0.0
	var max_walk_vm_step := 0.0
	prev_cam_pos = player.camera.position
	prev_vm_pos = wc.viewmodel_pivot.position
	for f in range(360):
		if f < 120:
			player.velocity = Vector3(0.0, 0.0, -PlayerController.BASE_WALK_SPEED)
			player.is_sprinting = false
			player._grounded_override = (f != 60) # 1-frame floor flicker test
		elif f < 220:
			player.velocity = Vector3(0.0, 0.0, -PlayerController.BASE_SPRINT_SPEED)
			player.is_sprinting = true
			player._grounded_override = true
		else:
			player.velocity = Vector3.ZERO
			player.is_sprinting = false
			player._grounded_override = true
		player._process(1.0 / 144.0)
		wc._animate_viewmodel(1.0 / 144.0)
		max_walk_cam_step = maxf(max_walk_cam_step, player.camera.position.distance_to(prev_cam_pos))
		max_walk_vm_step = maxf(max_walk_vm_step, wc.viewmodel_pivot.position.distance_to(prev_vm_pos))
		prev_cam_pos = player.camera.position
		prev_vm_pos = wc.viewmodel_pivot.position
	_check(runner, max_walk_cam_step < 0.0035 and max_walk_vm_step < 0.0035, "Jitter: 144Hz walk/sprint/stop bob transitions smooth (cam=%.5f, vm=%.5f)" % [max_walk_cam_step, max_walk_vm_step])
	# Finish idle convergence check with a few extra steps
	for _i in range(60):
		player._process(0.016)
		wc._animate_viewmodel(0.016)
	_check(runner, player.camera.position.length() < 0.0001 and wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001 and wc.viewmodel_pivot.rotation.length() < 0.0001, "Jitter: walk/sprint bob converges cleanly back to idle zero")

	# 6. Crouch head height, Reload, Melee, Equip & MG42 recoil bounds
	player.is_crouching = true
	var prev_h := player.head.position.y
	var crouch_ok := true
	for _i in range(20):
		player._process(0.12)
		var h := player.head.position.y
		if h < 0.85 - 0.0001 or h > prev_h + 0.0001:
			crouch_ok = false
		prev_h = h
	_check(runner, crouch_ok and absf(player.head.position.y - 0.85) < 0.0001, "Jitter: crouch head.position.y converges monotonically to 0.85 at delta=0.12")
	player.is_crouching = false
	for _i in range(20):
		player._process(0.12)
	_check(runner, absf(player.head.position.y - 1.62) < 0.0001, "Jitter: uncrouch head.position.y converges cleanly back to 1.62")

	# Reload transition & recovery
	wc.snap_viewmodel()
	wc.weapons[wc.active_idx]["mag"] = 2
	wc.start_reload()
	_check(runner, wc.is_reloading, "Jitter: reload starts cleanly")
	for _i in range(20):
		wc._animate_viewmodel(0.016)
	_check(runner, wc.viewmodel_pivot.position.y < hip_pos.y - 0.05 and wc.viewmodel_pivot.rotation.x < -0.15, "Jitter: reload dips & tilts viewmodel smoothly")
	wc._finish_reload()
	for _i in range(60):
		wc._animate_viewmodel(0.016)
	_check(runner, wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001 and wc.viewmodel_pivot.rotation.length() < 0.0001, "Jitter: post-reload returns smoothly to idle hip pose")

	# Melee transition: no 13cm 1-frame snap on start, clean return on end
	wc.snap_viewmodel()
	var pre_melee_pos := wc.viewmodel_pivot.position
	wc._perform_melee()
	wc._process(0.016)
	var first_melee_step := wc.viewmodel_pivot.position.distance_to(pre_melee_pos)
	_check(runner, wc.is_meleeing and wc.knife_holder.visible and not wc.model_holder.visible, "Jitter: melee toggles knife/gun visibility cleanly")
	_check(runner, first_melee_step < 0.04, "Jitter: melee start does not 1-frame snap across screen (step=%.4fm)" % first_melee_step)
	for _i in range(30):
		wc._process(0.016)
	_check(runner, not wc.is_meleeing and not wc.knife_holder.visible and wc.model_holder.visible, "Jitter: melee completes cleanly & restores weapon visibility")
	for _i in range(60):
		wc._process(0.016)
	_check(runner, wc.viewmodel_pivot.position.distance_to(hip_pos) < 0.0001 and wc.viewmodel_pivot.rotation.length() < 0.0001, "Jitter: post-melee gun draw converges smoothly to idle pose")

	# Equip mid-melee clears melee & immediately detaches old weapon (no 1-frame double-model overlap)
	wc._perform_melee()
	wc.weapons[wc.active_idx]["mag"] = 2
	wc.start_reload()
	_check(runner, not wc.is_reloading and wc.is_meleeing, "Jitter: reload blocked cleanly during active melee swing")
	wc.give_or_replace_weapon("mp40")
	_check(runner, not wc.is_meleeing and wc.model_holder.visible and not wc.knife_holder.visible, "Jitter: equipping weapon mid-melee cleanly resets melee state")
	_check(runner, wc.model_holder.get_child_count() == 2, "Jitter: ModelHolder contains exactly 1 weapon + FirstPersonHands immediately on equip (count=%d)" % wc.model_holder.get_child_count())

	# MG42 rapid fire recoil kick stays bounded well clear of Camera3D near plane
	wc.give_or_replace_weapon("mg42")
	wc.snap_viewmodel()
	var target_parent: Node = runner.get_tree().current_scene if runner.get_tree().current_scene != null else runner.get_tree().root
	var pre_children := target_parent.get_children()
	var cur_z := -999.0
	var max_z := -999.0
	for _i in range(25):
		wc._fire_cooldown = 0.0
		wc._try_fire()
		wc._animate_viewmodel(0.05)
		cur_z = wc.viewmodel_pivot.position.z
		max_z = maxf(max_z, cur_z)
	for ch in target_parent.get_children():
		if not (ch in pre_children):
			target_parent.remove_child(ch)
			ch.free()
	_check(runner, wc._kick_pos.z <= 0.0851 and max_z < -0.10, "Jitter: high-RPM MG42 recoil kick bounded safely clear of camera near plane (max_z=%.4f)" % max_z)

	runner.remove_child(player)
	player.free()
	GameManager.reset_match()


static func _check(runner: Node, cond: bool, msg: String) -> void:
	runner.call("_check", cond, msg)

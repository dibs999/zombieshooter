extends Node

# Fast isolated viewmodel-hand preview: instance the fp hand GLBs in front of a
# camera with a warm key light, screenshot, quit. Much faster than full-world smoke.
func _ready() -> void:
	await get_tree().process_frame
	get_window().size = Vector2i(960, 540)
	var root3d := Node3D.new()
	get_tree().root.add_child.call_deferred(root3d)
	await _wait(2)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.03, 0.04, 0.06)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.35, 0.38, 0.45)
	e.ambient_light_energy = 0.6
	env.environment = e
	root3d.add_child(env)

	var cam := Camera3D.new()
	cam.position = Vector3(0.15, 0.05, 0.55)
	cam.rotation_degrees = Vector3(-5, 8, 0)
	cam.fov = 55.0
	cam.current = true
	root3d.add_child(cam)

	var key := OmniLight3D.new()
	key.position = Vector3(0.5, 0.6, 0.5)
	key.light_color = Color(1.0, 0.85, 0.7)
	key.light_energy = 2.2
	key.omni_range = 6.0
	root3d.add_child(key)

	# mimic weapon_controller runtime grading
	var wc_script := load("res://scripts/player/weapon_controller.gd")
	for spec in [["res://assets/models/weapons/fp_right_hand.glb", Vector3(-0.12, -0.15, 0.0), 25.0], ["res://assets/models/weapons/fp_left_hand.glb", Vector3(0.15, -0.15, -0.05), -20.0]]:
		if not ResourceLoader.exists(spec[0]):
			continue
		var inst := (load(spec[0]) as PackedScene).instantiate()
		var h := Node3D.new()
		h.position = spec[1]
		h.rotation_degrees.y = spec[2]
		h.add_child(inst)
		root3d.add_child(h)
		WeaponController.grade_hand_materials(h)
		pass

	await _wait(10)
	get_viewport().get_texture().get_image().save_png("/tmp/hands_shot.png")
	print("saved hands")
	get_tree().quit()

func _grade(root: Node) -> void:
	var tints := {
		"FPSkin": Color(0.66, 0.55, 0.47),
		"TacticalLeather": Color(0.72, 0.68, 0.62),
		"GloveReinforceLeather": Color(0.8, 0.76, 0.72),
		"SleeveWool": Color(0.62, 0.66, 0.55),
		"KnitCuff": Color(0.48, 0.72, 0.58),
	}
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is MeshInstance3D:
			var mi := n as MeshInstance3D
			for surf in mi.get_surface_override_material_count():
				var mat: Material = mi.get_active_material(surf)
				if mat is StandardMaterial3D and tints.has(mat.resource_name):
					print("grading mat: ", mat.resource_name)
					var sm := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
					var tint: Color = tints[mat.resource_name]
					sm.albedo_color = sm.albedo_color * tint
					mi.set_surface_override_material(surf, sm)
		for c in n.get_children():
			stack.append(c)

func _wait(n: int) -> void:
	for i in n:
		await get_tree().process_frame

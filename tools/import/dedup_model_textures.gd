@tool
extends EditorScenePostImport

const MAP_PATH := "res://tools/import/shared_tex_map.json"

static var _shared_map: Dictionary = {}
static var _map_loaded: bool = false


static func _get_shared_map() -> Dictionary:
	if _map_loaded:
		return _shared_map
	_map_loaded = true
	if FileAccess.file_exists(MAP_PATH):
		var f := FileAccess.open(MAP_PATH, FileAccess.READ)
		if f:
			var parsed = JSON.parse_string(f.get_as_text())
			f.close()
			if parsed is Dictionary:
				_shared_map = parsed
	else:
		push_error("dedup_model_textures: missing " + MAP_PATH)
	return _shared_map


func _post_import(scene: Node) -> Object:
	var src := get_source_file()
	var smap := _get_shared_map()
	var mat_table: Dictionary = smap.get(src, {})
	if mat_table.is_empty():
		return scene

	var visited_mats: Dictionary = {}
	_apply_recursive(scene, mat_table, visited_mats)
	return scene


func _apply_recursive(node: Node, mat_table: Dictionary, visited_mats: Dictionary) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh:
			for si in range(mi.mesh.get_surface_count()):
				var mat := mi.mesh.surface_get_material(si)
				if mat:
					_patch_material(mat, mat_table, visited_mats)
		for si in range(mi.get_surface_override_material_count()):
			var omat := mi.get_surface_override_material(si)
			if omat:
				_patch_material(omat, mat_table, visited_mats)
		if mi.material_override:
			_patch_material(mi.material_override, mat_table, visited_mats)

	for child in node.get_children():
		_apply_recursive(child, mat_table, visited_mats)


func _patch_material(mat: Material, mat_table: Dictionary, visited_mats: Dictionary) -> void:
	var id := mat.get_instance_id()
	if visited_mats.has(id):
		return
	visited_mats[id] = true

	if not (mat is StandardMaterial3D):
		return
	var sm := mat as StandardMaterial3D
	var spec_var = mat_table.get(sm.resource_name, null)
	if not (spec_var is Dictionary):
		return
	var spec: Dictionary = spec_var

	if spec.has("albedo"):
		var tex := _load_tex(str(spec["albedo"]))
		if tex:
			sm.albedo_texture = tex

	if spec.has("normal"):
		var ntex := _load_tex(str(spec["normal"]))
		if ntex:
			sm.normal_enabled = true
			sm.normal_texture = ntex
			if spec.has("normal_scale"):
				sm.normal_scale = float(spec["normal_scale"])

	if spec.has("orm"):
		var otex := _load_tex(str(spec["orm"]))
		if otex:
			sm.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
			sm.roughness_texture = otex
			sm.metallic_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_BLUE
			sm.metallic_texture = otex

	if spec.has("emissive"):
		var etex := _load_tex(str(spec["emissive"]))
		if etex:
			sm.emission_enabled = true
			sm.emission_texture = etex


func _load_tex(path: String) -> Texture2D:
	var res := ResourceLoader.load(path, "Texture2D")
	if res is Texture2D:
		return res
	push_warning("dedup_model_textures: failed to load Texture2D " + path)
	return null

extends Node3D
class_name WallBuy

@export var weapon_id: String = "mp40"
@export var chalk_texture: Texture2D
@onready var chalk_mesh: MeshInstance3D = $ChalkPlane
@onready var preview_holder: Node3D = $PreviewHolder


func _ready() -> void:
	if chalk_texture and chalk_mesh:
		var mat := StandardMaterial3D.new()
		mat.albedo_texture = chalk_texture
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		chalk_mesh.material_override = mat

	var data: Dictionary = WeaponDB.WEAPON_DATA.get(weapon_id, WeaponDB.WEAPON_DATA["mp40"])
	var mpath := str(data["model"])
	if ResourceLoader.exists(mpath):
		var inst := (load(mpath) as PackedScene).instantiate()
		preview_holder.add_child(inst)
		inst.rotation_degrees = Vector3(0, 90, 0)


func get_interact_prompt(player: Node) -> String:
	var data: Dictionary = WeaponDB.WEAPON_DATA.get(weapon_id, WeaponDB.WEAPON_DATA["mp40"])
	var wname := str(data["name"])
	var price := int(data["wall_cost"])
	if player.has_method("has_weapon") and player.has_weapon(weapon_id):
		var cur: Dictionary = player.get_current_weapon_state()
		var ammo_cost := 4500 if (cur.get("id") == weapon_id and bool(cur.get("packed", false))) else int(price / 2)
		return "[E] Buy %s Ammo [Cost: %d]" % [wname, ammo_cost]
	return "[E] Buy %s [Cost: %d]" % [wname, price]


func interact(player: Node) -> void:
	var data: Dictionary = WeaponDB.WEAPON_DATA.get(weapon_id, WeaponDB.WEAPON_DATA["mp40"])
	var price := int(data["wall_cost"])
	if player.has_method("has_weapon") and player.has_weapon(weapon_id):
		var cur: Dictionary = player.get_current_weapon_state()
		var ammo_cost := 4500 if (cur.get("id") == weapon_id and bool(cur.get("packed", false))) else int(price / 2)
		if GameManager.spend_points(ammo_cost):
			player.weapon_ctrl.refill_all_ammo() if player.get("weapon_ctrl") else player.refill_all_ammo()
	else:
		if GameManager.spend_points(price):
			player.give_weapon(weapon_id)

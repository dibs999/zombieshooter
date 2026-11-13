extends Node3D
class_name PackAPunch

const COST := 5000

@onready var model_holder: Node3D = $ModelHolder
@onready var forge_light: OmniLight3D = $OmniLight3D


func _ready() -> void:
	GameManager.power_activated.connect(_refresh_lights)
	if ResourceLoader.exists("res://assets/models/props/pack_a_punch.glb"):
		var inst := (load("res://assets/models/props/pack_a_punch.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
	_refresh_lights()


func _refresh_lights() -> void:
	forge_light.light_energy = 4.2 if GameManager.power_on else 0.3


func get_interact_prompt(player: Node) -> String:
	if not GameManager.power_on:
		return "Pack-a-Punch — Power Must Be Turned On!"
	var cur: Dictionary = player.get_current_weapon_state() if player.has_method("get_current_weapon_state") else {}
	if cur.is_empty():
		return ""
	if bool(cur.get("packed", false)):
		return "%s is already Pack-a-Punched!" % WeaponDB.get_display_name(cur)
	return "[E] Pack-a-Punch %s [Cost: %d]" % [WeaponDB.get_display_name(cur), COST]


func interact(player: Node) -> void:
	if not GameManager.power_on:
		return
	var cur: Dictionary = player.get_current_weapon_state() if player.has_method("get_current_weapon_state") else {}
	if cur.is_empty() or bool(cur.get("packed", false)):
		return
	if GameManager.spend_points(COST):
		if player.has_method("pack_current_weapon") and player.pack_current_weapon():
			AudioManager.play_3d("perk_drink", global_position, 0.15, 2.0)
			var upgraded: Dictionary = player.get_current_weapon_state()
			GameManager.powerup_banner.emit("UPGRADED: %s!" % WeaponDB.get_display_name(upgraded).to_upper(), Color(0.2, 0.95, 1.0))
			var tw := create_tween()
			forge_light.light_energy = 12.0
			tw.tween_property(forge_light, "light_energy", 4.2, 0.8)

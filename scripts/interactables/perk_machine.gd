extends Node3D
class_name PerkMachine

@export var perk_id: String = "juggernog"
@onready var model_holder: Node3D = $ModelHolder
@onready var light: OmniLight3D = $OmniLight3D
@onready var interact_col: CollisionShape3D = $InteractArea/CollisionShape3D


func _ready() -> void:
	GameManager.power_activated.connect(_refresh_power_visuals)
	GameManager.perks_changed.connect(_on_perks_changed)

	var mpath := "res://assets/models/props/perk_%s.glb" % perk_id
	if ResourceLoader.exists(mpath):
		var inst := (load(mpath) as PackedScene).instantiate()
		model_holder.add_child(inst)

	var info: Dictionary = GameManager.PERK_INFO.get(perk_id, {})
	if info.has("color"):
		light.light_color = info["color"]
	_refresh_power_visuals()


func _is_powered() -> bool:
	return GameManager.power_on or perk_id == "quickrevive"


func _refresh_power_visuals() -> void:
	light.light_energy = 1.8 if _is_powered() else 0.12


func _on_perks_changed(_p: Array[String]) -> void:
	if perk_id == "quickrevive" and GameManager.quick_revive_uses_left <= 0:
		visible = false
		interact_col.set_deferred("disabled", true)


func get_interact_prompt(_player: Node) -> String:
	if not visible:
		return ""
	var info: Dictionary = GameManager.PERK_INFO.get(perk_id, {})
	if not _is_powered():
		return "%s — Power Must Be Turned On!" % str(info.get("name", perk_id))
	if GameManager.has_perk(perk_id):
		return "%s (Already Active)" % str(info.get("name", perk_id))
	if GameManager.perks.size() >= GameManager.max_perks:
		return "Perk Limit Reached (%d/%d)" % [GameManager.perks.size(), GameManager.max_perks]
	return "[E] Buy %s [Cost: %d]" % [str(info.get("name", perk_id)), int(info.get("cost", 2000))]


func interact(_player: Node) -> void:
	if not visible or not _is_powered() or not GameManager.can_buy_perk(perk_id):
		return
	var info: Dictionary = GameManager.PERK_INFO.get(perk_id, {})
	var cost := int(info.get("cost", 2000))
	if GameManager.spend_points(cost):
		GameManager.grant_perk(perk_id, true)
		GameManager.powerup_banner.emit("%s ACQUIRED!" % str(info.get("name", perk_id)).to_upper(), info.get("color", Color.WHITE))

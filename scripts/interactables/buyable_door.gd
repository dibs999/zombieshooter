extends Node3D
class_name BuyableDoor

@export var door_name: String = "Blast Door"
@export var cost: int = 750
@export var unlock_zone_id: String = "east_courtyard"
@export var also_unlock_zone_id: String = ""
@export var requires_power: bool = false
@export var nav_bridge_path: NodePath

@onready var door_mesh: Node3D = $DoorMesh
@onready var blocker_col: CollisionShape3D = $StaticBody3D/CollisionShape3D
@onready var interact_col: CollisionShape3D = $InteractArea/CollisionShape3D
@onready var label_3d: Label3D = $Label3D

var is_opened: bool = false


func _ready() -> void:
	if requires_power:
		GameManager.power_activated.connect(_on_power_activated)
		if label_3d:
			label_3d.text = "LOCKED\n[REQUIRES POWER]"
	else:
		if label_3d:
			label_3d.text = "%s\n[%d PTS]" % [door_name.to_upper(), cost]


func _on_power_activated() -> void:
	if requires_power and not is_opened:
		_open_door()


func get_interact_prompt(_player: Node) -> String:
	if is_opened:
		return ""
	if requires_power:
		return "Door Powered Remotely — Turn On Power!"
	return "[E] Open %s [Cost: %d]" % [door_name, cost]


func interact(_player: Node) -> void:
	if is_opened or requires_power:
		return
	if GameManager.spend_points(cost):
		_open_door()


func _open_door() -> void:
	is_opened = true
	if unlock_zone_id != "":
		GameManager.unlock_zone(unlock_zone_id)
	if also_unlock_zone_id != "":
		GameManager.unlock_zone(also_unlock_zone_id)
	blocker_col.set_deferred("disabled", true)
	interact_col.set_deferred("disabled", true)
	if not nav_bridge_path.is_empty():
		var bridge := get_node_or_null(nav_bridge_path)
		if bridge is NavigationRegion3D:
			(bridge as NavigationRegion3D).enabled = true
		elif bridge is NavigationLink3D:
			(bridge as NavigationLink3D).enabled = true
	if label_3d:
		label_3d.visible = false
	var tw := create_tween()
	tw.tween_property(door_mesh, "position:y", door_mesh.position.y + 3.4, 0.85).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func(): door_mesh.visible = false)

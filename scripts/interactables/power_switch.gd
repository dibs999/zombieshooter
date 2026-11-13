extends Node3D
class_name PowerSwitch

@onready var model_holder: Node3D = $ModelHolder
@onready var status_light: OmniLight3D = $OmniLight3D
@onready var interact_col: CollisionShape3D = $InteractArea/CollisionShape3D

var _lever: Node3D = null
var _activated: bool = false


func _ready() -> void:
	if ResourceLoader.exists("res://assets/models/props/power_switch.glb"):
		var inst := (load("res://assets/models/props/power_switch.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		_lever = inst.find_child("SwitchLever", true, false) as Node3D
		if _lever:
			_lever.rotation_degrees.x = -38.0
	status_light.light_color = Color(1.0, 0.15, 0.1)
	status_light.light_energy = 2.2


func get_interact_prompt(_player: Node) -> String:
	return "" if _activated else "[E] Turn On Power"


func interact(_player: Node) -> void:
	if _activated:
		return
	_activated = true
	interact_col.set_deferred("disabled", true)
	status_light.light_color = Color(0.15, 1.0, 0.45)
	status_light.light_energy = 4.5
	if _lever:
		create_tween().tween_property(_lever, "rotation_degrees:x", 45.0, 0.3)
	GameManager.activate_power()

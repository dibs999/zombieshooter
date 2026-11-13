extends Node3D
class_name WindowBarricade

@export var zone_id: String = "spawn"
@onready var model_holder: Node3D = $ModelHolder
@onready var spawn_marker: Marker3D = $SpawnMarker
@onready var outside_marker: Marker3D = $OutsideMarker
@onready var sill_marker: Marker3D = $SillMarker
@onready var inside_marker: Marker3D = $InsideMarker

var planks: Array[Node3D] = []
var intact_count: int = 6


func _ready() -> void:
	add_to_group("window_barricades")
	GameManager.carpenter_triggered.connect(repair_all)
	if ResourceLoader.exists("res://assets/models/env/barricade_window.glb"):
		var inst := (load("res://assets/models/env/barricade_window.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		for i in range(6):
			var p := inst.find_child("Plank_%d" % i, true, false)
			if p is Node3D:
				planks.append(p as Node3D)
	intact_count = planks.size() if not planks.is_empty() else 6


func has_planks() -> bool:
	return intact_count > 0


func tear_plank() -> void:
	if intact_count <= 0:
		return
	intact_count -= 1
	if intact_count < planks.size():
		planks[intact_count].visible = false
	AudioManager.play_3d("plank_break", global_position, 0.1, -2.0)


func repair_all() -> void:
	intact_count = planks.size() if not planks.is_empty() else 6
	for p in planks:
		p.visible = true


func get_interact_prompt(_player: Node) -> String:
	if intact_count >= 6:
		return ""
	return "[Hold E] Rebuild Barrier (+10)"


func interact_hold(_player: Node) -> void:
	if intact_count >= 6:
		return
	if intact_count < planks.size():
		planks[intact_count].visible = true
	intact_count += 1
	AudioManager.play_3d("plank_repair", global_position, 0.08, -1.0)
	GameManager.add_barrier_repair_points()


func get_spawn_pos() -> Vector3:
	return spawn_marker.global_position


func get_outside_pos() -> Vector3:
	return outside_marker.global_position


func get_sill_pos() -> Vector3:
	return sill_marker.global_position


func get_inside_pos() -> Vector3:
	return inside_marker.global_position

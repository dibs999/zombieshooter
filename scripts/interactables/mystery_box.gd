extends Node3D
class_name MysteryBox

enum BoxState { IDLE, SPINNING, READY_TAKE, MOVING }

@export var start_active: bool = false
@export var zone_id: String = "spawn"

@onready var model_holder: Node3D = $ModelHolder
@onready var item_holder: Node3D = $ItemHolder
@onready var sky_beam: MeshInstance3D = $SkyBeam
@onready var box_light: OmniLight3D = $OmniLight3D

var is_active: bool = false
var state: BoxState = BoxState.IDLE
var uses_here: int = 0
var _lid_node: Node3D = null
var _spin_timer: float = 0.0
var _cycle_timer: float = 0.0
var _take_timer: float = 0.0
var _chosen_weapon: String = ""
var _last_paid_cost: int = 950
var _all_weapon_ids: Array[String] = ["m14", "trench_shotgun", "mp40", "stg44", "kar98k", "mg42", "raygun"]


func _ready() -> void:
	add_to_group("mystery_boxes")
	GameManager.fire_sale_changed.connect(_on_fire_sale_changed)

	if ResourceLoader.exists("res://assets/models/props/mystery_box.glb"):
		var inst := (load("res://assets/models/props/mystery_box.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		_lid_node = inst.find_child("BoxLid", true, false) as Node3D

	set_box_active(start_active)


func set_box_active(active: bool) -> void:
	is_active = active
	state = BoxState.IDLE
	_clear_item()
	if _lid_node:
		_lid_node.rotation_degrees.x = 0.0
	model_holder.visible = active
	sky_beam.visible = active
	box_light.light_energy = 3.2 if active else 0.0


func _on_fire_sale_changed(fs_active: bool) -> void:
	if fs_active:
		if not is_active:
			set_box_active(true)
	else:
		# Keep only primary active box if not chosen
		if not start_active and state == BoxState.IDLE:
			set_box_active(false)


func _current_cost() -> int:
	return 10 if GameManager.active_powerups.get("fire_sale", 0.0) > 0.0 else 950


func get_interact_prompt(_player: Node) -> String:
	if not is_active:
		return ""
	match state:
		BoxState.IDLE:
			return "[E] Mystery Box [Cost: %d]" % _current_cost()
		BoxState.SPINNING:
			return "Mystery Box Spinning..."
		BoxState.READY_TAKE:
			var wname := str(WeaponDB.WEAPON_DATA.get(_chosen_weapon, {}).get("name", _chosen_weapon))
			return "[E] Take %s" % wname
		_:
			return "Box Moving!"


func interact(player: Node) -> void:
	if not is_active:
		return
	if state == BoxState.IDLE:
		var cost := _current_cost()
		if GameManager.spend_points(cost):
			_last_paid_cost = cost
			_start_spin(player)
	elif state == BoxState.READY_TAKE:
		if player.has_method("give_weapon"):
			player.give_weapon(_chosen_weapon)
		AudioManager.play_2d("buy_confirm", 0.04, 0.0)
		_reset_to_idle()


func _start_spin(player: Node) -> void:
	state = BoxState.SPINNING
	uses_here += 1
	_spin_timer = 2.6
	_cycle_timer = 0.0
	AudioManager.play_3d("mystery_box_jingle", global_position, 0.0, 1.0)
	if _lid_node:
		create_tween().tween_property(_lid_node, "rotation_degrees:x", 82.0, 0.35)

	# Decide final weapon or Teddy Bear relocation!
	var fs_left: float = float(GameManager.active_powerups.get("fire_sale", 0.0))
	var should_move: bool = (uses_here >= 4 and fs_left <= 0.0 and randf() < 0.32)
	if should_move:
		_chosen_weapon = "teddy_bear"
	else:
		var exclude: Array[String] = []
		if player and player.get("weapon_ctrl"):
			for w in player.weapon_ctrl.weapons:
				exclude.append(str(w["id"]))
		_chosen_weapon = WeaponDB.pick_random_box_weapon(exclude)


func _process(delta: float) -> void:
	if not is_active:
		return
	if state == BoxState.SPINNING:
		_spin_timer -= delta
		_cycle_timer -= delta
		item_holder.position.y = 0.95 + (1.0 - (_spin_timer / 2.6)) * 0.35
		item_holder.rotation.y += delta * 5.0
		if _cycle_timer <= 0.0:
			_cycle_timer = 0.14
			var wid: String = _all_weapon_ids[randi() % _all_weapon_ids.size()]
			_show_preview_model("res://assets/models/weapons/%s.glb" % wid)
		if _spin_timer <= 0.0:
			_finish_spin()
	elif state == BoxState.READY_TAKE:
		_take_timer -= delta
		item_holder.rotation.y += delta * 1.4
		item_holder.position.y = 1.25 - (1.0 - clampf(_take_timer / 7.5, 0.0, 1.0)) * 0.45
		if _take_timer <= 0.0:
			_reset_to_idle()


func _finish_spin() -> void:
	if _chosen_weapon == "teddy_bear":
		state = BoxState.MOVING
		_show_preview_model("res://assets/models/props/teddy_bear.glb")
		GameManager.add_points(_last_paid_cost, "Box Refund")
		GameManager.powerup_banner.emit("TEDDY BEAR — BOX RELOCATING!", Color(1.0, 0.45, 0.25))
		AudioManager.play_2d("buy_denied", 0.15, 2.0)
		get_tree().create_timer(2.2).timeout.connect(_relocate_box)
		return

	state = BoxState.READY_TAKE
	_take_timer = 7.5
	var mpath := str(WeaponDB.WEAPON_DATA.get(_chosen_weapon, {}).get("model", ""))
	_show_preview_model(mpath)


func _relocate_box() -> void:
	uses_here = 0
	var boxes := get_tree().get_nodes_in_group("mystery_boxes")
	var candidates: Array[MysteryBox] = []
	for b in boxes:
		if b != self and b is MysteryBox:
			candidates.append(b as MysteryBox)
	set_box_active(false)
	if not candidates.is_empty():
		var next_box: MysteryBox = candidates[randi() % candidates.size()]
		next_box.set_box_active(true)
	else:
		set_box_active(true)


func _reset_to_idle() -> void:
	state = BoxState.IDLE
	_clear_item()
	if _lid_node:
		create_tween().tween_property(_lid_node, "rotation_degrees:x", 0.0, 0.35)


func _show_preview_model(path: String) -> void:
	_clear_item()
	if ResourceLoader.exists(path):
		var inst := (load(path) as PackedScene).instantiate()
		item_holder.add_child(inst)
		inst.scale = Vector3.ONE * 1.45


func _clear_item() -> void:
	for c in item_holder.get_children():
		c.queue_free()

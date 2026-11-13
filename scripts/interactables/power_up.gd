extends Node3D
class_name PowerUpDrop

@export var kind: String = "max_ammo"

@onready var model_holder: Node3D = $ModelHolder
@onready var pickup_light: OmniLight3D = $OmniLight3D

var lifetime: float = 28.0
var _time: float = 0.0


func setup(p_kind: String) -> void:
	kind = p_kind
	_load_mesh()


func _ready() -> void:
	if model_holder.get_child_count() == 0:
		_load_mesh()


func _load_mesh() -> void:
	for c in model_holder.get_children():
		c.queue_free()
	var mpath := "res://assets/models/pickups/powerup_%s.glb" % kind
	if ResourceLoader.exists(mpath):
		var inst := (load(mpath) as PackedScene).instantiate()
		model_holder.add_child(inst)
		inst.scale = Vector3.ONE * 1.05


func _process(delta: float) -> void:
	_time += delta
	lifetime -= delta
	model_holder.rotation.y += delta * 2.4
	model_holder.position.y = 0.35 + sin(_time * 3.5) * 0.14

	if lifetime <= 6.0:
		model_holder.visible = fmod(_time * 12.0, 1.0) > 0.45
	if lifetime <= 0.0:
		queue_free()


func _on_area_3d_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		GameManager.activate_powerup(kind)
		queue_free()

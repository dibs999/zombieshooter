extends CharacterBody3D
class_name HellhoundAI

@onready var nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var body_area: Area3D = $BodyArea
@onready var model_root: Node3D = $ModelRoot
@onready var ember_light: OmniLight3D = $EmberLight
@onready var ember_trail: CPUParticles3D = $EmberTrail

var max_hp: float = 180.0
var hp: float = 180.0
var move_speed: float = 6.3
var attack_damage: float = 35.0
var is_dead: bool = false
var _attack_cd: float = 0.0
var _repath_cd: float = 0.0
var _anim_player: AnimationPlayer = null
var _current_anim: String = ""

var _blood_decal_scene: PackedScene = preload("res://scenes/fx/blood_decal.tscn")
var _impact_sparks_scene: PackedScene = preload("res://scenes/fx/impact_sparks.tscn")

signal died(hound: HellhoundAI, was_headshot: bool, death_pos: Vector3, force_drop: bool)


func setup(p_hp: float) -> void:
	max_hp = p_hp
	hp = max_hp


func _ready() -> void:
	add_to_group("zombies")
	body_area.set_meta("zombie_owner", self)
	if ResourceLoader.exists("res://assets/models/characters/hellhound.glb"):
		var inst := (load("res://assets/models/characters/hellhound.glb") as PackedScene).instantiate()
		model_root.add_child(inst)
		_find_anim(inst)
	if ember_trail != null:
		ember_trail.emitting = true
	_trigger_spawn_lightning()
	AudioManager.play_3d("hellhound_howl", global_position, 0.1, 0.0)
	_play_anim("Run")


func _fx_parent() -> Node:
	var p := get_parent()
	if p != null and p != get_tree().root:
		return p
	return get_tree().current_scene if get_tree().current_scene != null else p


func _trigger_spawn_lightning() -> void:
	var flash := OmniLight3D.new()
	flash.light_color = Color(0.55, 0.80, 1.0)
	flash.light_energy = 7.5
	flash.omni_range = 11.0
	add_child(flash)
	flash.position = Vector3(0, 1.6, 0)
	var tw := flash.create_tween()
	tw.tween_property(flash, "light_energy", 0.0, 0.36).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	tw.tween_callback(flash.queue_free)

	if is_inside_tree():
		var parent_node := _fx_parent()
		if parent_node != null:
			var spk := _impact_sparks_scene.instantiate() as Node3D
			parent_node.add_child(spk)
			spk.global_position = global_position + Vector3(0, 0.7, 0)


func _find_anim(n: Node) -> void:
	if n is AnimationPlayer and _anim_player == null:
		_anim_player = n as AnimationPlayer
		for aname in ["Idle", "Run"]:
			if _anim_player.has_animation(aname):
				_anim_player.get_animation(aname).loop_mode = Animation.LOOP_LINEAR
	for c in n.get_children():
		_find_anim(c)


func _play_anim(a: String, force_restart: bool = false) -> void:
	if _anim_player and (force_restart or _current_anim != a) and _anim_player.has_animation(a):
		var blend := 0.0 if _current_anim == "" else 0.12
		_current_anim = a
		_anim_player.play(a, blend)


func _physics_process(delta: float) -> void:
	if is_dead or GameManager.is_game_over:
		return
	_attack_cd = maxf(0.0, _attack_cd - delta)
	if ember_light != null:
		ember_light.light_energy = 2.1 + sin(Time.get_ticks_msec() * 0.015) * 0.45

	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return

	var dist := global_position.distance_to(player.global_position)
	if dist <= 1.75:
		velocity.x = 0.0
		velocity.z = 0.0
		_face_direction((player.global_position - global_position).normalized(), delta)
		if _attack_cd <= 0.0:
			_attack_cd = 1.0
			_play_anim("Attack", true)
			if player.has_method("take_damage"):
				player.take_damage(attack_damage)
		return

	_repath_cd -= delta
	if _repath_cd <= 0.0:
		_repath_cd = 0.2
		nav_agent.target_position = player.global_position

	var dir := Vector3.ZERO
	if not nav_agent.is_navigation_finished():
		dir = nav_agent.get_next_path_position() - global_position
		dir.y = 0.0
	if dir.length_squared() < 0.01:
		dir = player.global_position - global_position
		dir.y = 0.0
	if dir.length_squared() > 0.001:
		dir = dir.normalized()

	velocity.x = dir.x * move_speed
	velocity.z = dir.z * move_speed
	velocity.y = -15.0 * delta if not is_on_floor() else 0.0
	move_and_slide()
	_face_direction(dir, delta)
	if _attack_cd <= 0.45:
		_play_anim("Run")


func _face_direction(dir: Vector3, delta: float) -> void:
	if dir.length_squared() < 0.001:
		return
	rotation.y = lerp_angle(rotation.y, atan2(-dir.x, -dir.z), delta * 12.0)


func take_damage(amount: float, is_headshot: bool, _hit_pos: Vector3, _hit_dir: Vector3, is_melee: bool = false) -> bool:
	if is_dead:
		return false
	var insta: bool = float(GameManager.active_powerups.get("insta_kill", 0.0)) > 0.0
	hp = 0.0 if insta else (hp - amount)
	if hp <= 0.0:
		_die(is_headshot, is_melee, false)
		return true
	GameManager.add_points(10, "Hit")
	return false


func kill_by_nuke() -> void:
	if not is_dead:
		_die(false, false, true)


func _die(_hs: bool, is_melee: bool, from_nuke: bool) -> void:
	is_dead = true
	remove_from_group("zombies")
	set_physics_process(false)
	body_area.set_deferred("monitoring", false)
	body_area.set_deferred("monitorable", false)
	($CollisionShape3D as CollisionShape3D).set_deferred("disabled", true)
	if ember_trail != null:
		ember_trail.emitting = false
	if ember_light != null:
		var tw := ember_light.create_tween()
		tw.tween_property(ember_light, "light_energy", 0.0, 1.1)

	if not from_nuke:
		GameManager.stats["kills"] += 1
		GameManager.add_points(130 if is_melee else 60, "Hellhound")
		if is_inside_tree():
			var parent_node := _fx_parent()
			if parent_node != null:
				var spk := _impact_sparks_scene.instantiate() as Node3D
				parent_node.add_child(spk)
				spk.global_position = global_position + Vector3(0, 0.55, 0)
				var dec := _blood_decal_scene.instantiate() as BloodDecal
				dec.setup(0.90)
				parent_node.add_child(dec)
				dec.global_position = Vector3(global_position.x, 0.0, global_position.z)

	_play_anim("Death", true)
	emit_signal("died", self, false, global_position, false)
	get_tree().create_timer(1.5).timeout.connect(queue_free)

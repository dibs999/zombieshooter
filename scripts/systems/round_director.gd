extends Node
class_name RoundDirector

const MAX_ACTIVE_ZOMBIES := 24
const POWERUP_TYPES := ["max_ammo", "insta_kill", "double_points", "nuke", "carpenter", "fire_sale"]

var zombie_scene: PackedScene = preload("res://scenes/enemies/zombie.tscn")
var hellhound_scene: PackedScene = preload("res://scenes/enemies/hellhound.tscn")
var powerup_scene: PackedScene = preload("res://scenes/interactables/power_up.tscn")

var zombies_remaining_to_spawn: int = 0
var active_zombies: int = 0
var spawn_timer: float = 0.0
var spawn_interval: float = 1.8
var round_transition_timer: float = 0.0
var in_transition: bool = false
var _kills_since_drop: int = 0
var _drops_this_round: int = 0
var _brute_spawned_this_round: bool = false
var _is_dog_round: bool = false


func _ready() -> void:
	GameManager.nuke_triggered.connect(_on_nuke)
	start_round(1)


func start_round(r: int) -> void:
	GameManager.current_round = r
	GameManager.round_barrier_points_earned = 0
	_drops_this_round = 0
	_brute_spawned_this_round = false
	_is_dog_round = GameManager.is_dog_round(r)
	zombies_remaining_to_spawn = GameManager.get_zombie_count_for_round(r)
	spawn_interval = maxf(0.75, 2.0 * pow(0.95, float(r - 1)))
	spawn_timer = 1.6
	in_transition = false

	AudioManager.play_2d("hellhound_howl" if _is_dog_round else "round_start", 0.02, 0.0)
	GameManager.round_changed.emit(r, _is_dog_round)


func _process(delta: float) -> void:
	if GameManager.is_game_over:
		return

	if in_transition:
		round_transition_timer -= delta
		if round_transition_timer <= 0.0:
			start_round(GameManager.current_round + 1)
		return

	if zombies_remaining_to_spawn > 0 and active_zombies < MAX_ACTIVE_ZOMBIES:
		spawn_timer -= delta
		if spawn_timer <= 0.0:
			spawn_timer = spawn_interval * randf_range(0.8, 1.2)
			_spawn_next_enemy()
	elif zombies_remaining_to_spawn <= 0 and active_zombies <= 0:
		in_transition = true
		round_transition_timer = 5.0
		AudioManager.play_2d("round_end", 0.0, 0.0)


func _spawn_next_enemy() -> void:
	var r := GameManager.current_round
	var hp := GameManager.get_zombie_health_for_round(r)

	if _is_dog_round:
		var dog_spawns := _get_unlocked_dog_spawns()
		if dog_spawns.is_empty():
			return
		var sp: Node3D = dog_spawns[randi() % dog_spawns.size()]
		var hound := hellhound_scene.instantiate() as HellhoundAI
		get_tree().current_scene.add_child(hound)
		hound.global_position = sp.global_position
		hound.setup(maxf(150.0, hp * 0.55))
		hound.died.connect(_on_enemy_died)
		zombies_remaining_to_spawn -= 1
		active_zombies += 1
		return

	var windows := _get_unlocked_windows()
	if windows.is_empty():
		return
	var win := windows[randi() % windows.size()]

	var variant := "soldier"
	if not _brute_spawned_this_round and r >= 8 and (r - 8) % 5 == 0 and zombies_remaining_to_spawn <= 3:
		variant = "brute"
		_brute_spawned_this_round = true
	elif randf() < 0.38:
		variant = "scientist"

	# CoD Zombies speed escalation: slow early, sprinters starting Round 4+
	var speed := 1.85
	if r == 2:
		speed = randf_range(1.9, 2.35)
	elif r == 3:
		speed = randf_range(2.2, 3.0)
	elif r >= 4:
		var sprinter_chance := clampf(0.18 + float(r - 4) * 0.12, 0.18, 0.88)
		speed = randf_range(4.1, 4.95) if randf() < sprinter_chance else randf_range(2.4, 3.3)

	var z := zombie_scene.instantiate() as ZombieAI
	z.setup(variant, hp, speed, win)
	z.died.connect(_on_enemy_died)
	get_tree().current_scene.add_child(z)
	z.global_position = win.get_spawn_pos()

	zombies_remaining_to_spawn -= 1
	active_zombies += 1


func _get_unlocked_windows() -> Array[Node]:
	var out: Array[Node] = []
	for w in get_tree().get_nodes_in_group("window_barricades"):
		if GameManager.unlocked_zones.get(str(w.get("zone_id")), true):
			out.append(w)
	return out


func _get_unlocked_dog_spawns() -> Array[Node3D]:
	var out: Array[Node3D] = []
	for s in get_tree().get_nodes_in_group("dog_spawns"):
		var zid := str(s.get_meta("zone_id", "spawn"))
		if GameManager.unlocked_zones.get(zid, true):
			out.append(s as Node3D)
	return out


func _on_enemy_died(_enemy: Node, _hs: bool, pos: Vector3, force_drop: bool) -> void:
	active_zombies = maxi(0, active_zombies - 1)
	_kills_since_drop += 1

	# Dog round finale ALWAYS drops Max Ammo!
	if _is_dog_round and zombies_remaining_to_spawn <= 0 and active_zombies <= 0:
		_spawn_powerup("max_ammo", pos + Vector3.UP * 0.6)
		return

	if force_drop or (_drops_this_round < 4 and (_kills_since_drop >= 14 or randf() < 0.085)):
		_kills_since_drop = 0
		_drops_this_round += 1
		var kind: String = POWERUP_TYPES[randi() % POWERUP_TYPES.size()]
		_spawn_powerup(kind, pos + Vector3.UP * 0.6)


func _spawn_powerup(kind: String, pos: Vector3) -> void:
	var pu := powerup_scene.instantiate() as Node3D
	get_tree().current_scene.add_child(pu)
	pu.global_position = pos
	if pu.has_method("setup"):
		pu.setup(kind)


func _on_nuke() -> void:
	for z in get_tree().get_nodes_in_group("zombies"):
		if z.has_method("kill_by_nuke"):
			z.kill_by_nuke()

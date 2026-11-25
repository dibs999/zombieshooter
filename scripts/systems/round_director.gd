extends Node
class_name RoundDirector

const MAX_ACTIVE_ZOMBIES := 24
const POWERUP_TYPES := ["max_ammo", "insta_kill", "double_points", "nuke", "carpenter", "fire_sale"]

var zombie_scene: PackedScene = preload("res://scenes/enemies/zombie.tscn")
var hellhound_scene: PackedScene = preload("res://scenes/enemies/hellhound.tscn")
var panzer_scene: PackedScene = preload("res://scenes/enemies/panzer_boss.tscn")
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
var _panzer_spawned_this_round: bool = false
var _is_dog_round: bool = false
var _is_panzer_round: bool = false
var _cached_windows: Array[Node] = []
var _cached_dog_spawns: Array[Node3D] = []
var _windows_cache_dirty: bool = true
var _dog_spawns_cache_dirty: bool = true
var _windows_zones_snapshot: Dictionary = {}
var _dog_spawns_zones_snapshot: Dictionary = {}
var _awaiting_first_input := true


func _ready() -> void:
	GameManager.nuke_triggered.connect(_on_nuke)
	if not GameManager.zone_unlocked.is_connected(_on_zone_unlocked):
		GameManager.zone_unlocked.connect(_on_zone_unlocked)
	if not GameManager.power_activated.is_connected(invalidate_spawn_caches):
		GameManager.power_activated.connect(invalidate_spawn_caches)
	invalidate_spawn_caches()
	start_round(1)


func _exit_tree() -> void:
	invalidate_spawn_caches()


func invalidate_spawn_caches() -> void:
	_windows_cache_dirty = true
	_dog_spawns_cache_dirty = true
	_cached_windows.clear()
	_cached_dog_spawns.clear()
	_windows_zones_snapshot.clear()
	_dog_spawns_zones_snapshot.clear()


func _on_zone_unlocked(_zone_id: String) -> void:
	invalidate_spawn_caches()


func is_panzer_round(r: int) -> bool:
	return r >= 8 and r % 8 == 0 and not GameManager.is_dog_round(r)


func start_round(r: int) -> void:
	GameManager.current_round = r
	GameManager.round_barrier_points_earned = 0
	_drops_this_round = 0
	_brute_spawned_this_round = false
	_panzer_spawned_this_round = false
	_is_dog_round = GameManager.is_dog_round(r)
	_is_panzer_round = is_panzer_round(r)
	zombies_remaining_to_spawn = GameManager.get_zombie_count_for_round(r)
	spawn_interval = maxf(0.7, 2.6 * pow(0.90, float(r - 1)))
	spawn_timer = 1.6
	in_transition = false

	AudioManager.play_2d("hellhound_howl" if _is_dog_round else "round_start", 0.02, 0.0)
	GameManager.round_changed.emit(r, _is_dog_round)


func _world_root() -> Node:
	var p := get_parent()
	if p != null and p != get_tree().root:
		return p
	return get_tree().current_scene if get_tree().current_scene != null else p


func spawn_panzer_boss(r: int = -1, spawn_pos: Variant = null) -> PanzerBossAI:
	var use_round := r if r > 0 else GameManager.current_round
	var boss := panzer_scene.instantiate() as PanzerBossAI
	boss.setup(use_round)
	boss.died.connect(_on_enemy_died)
	_world_root().add_child(boss)
	if spawn_pos is Vector3:
		boss.global_position = spawn_pos as Vector3
	else:
		var dog_spawns := _get_unlocked_dog_spawns()
		if not dog_spawns.is_empty():
			var sp := dog_spawns[randi() % dog_spawns.size()]
			boss.global_position = sp.global_position
		else:
			var windows := _get_unlocked_windows()
			if not windows.is_empty():
				boss.global_position = windows[randi() % windows.size()].get_inside_pos()
	boss.reset_physics_interpolation()
	active_zombies += 1
	return boss


func _player_gave_input() -> bool:
	# Only count real gameplay input: mouse must be captured (not in a menu)
	# and the player must act — menu clicks/loading mouse movements must not open the gate
	if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		return false
	for action in ["move_forward", "move_back", "move_left", "move_right", "jump", "shoot", "sprint"]:
		if Input.is_action_pressed(action):
			return true
	return false


func _process(delta: float) -> void:
	if _awaiting_first_input:
		if GameManager.current_round > 1 or _player_gave_input():
			_awaiting_first_input = false
			spawn_timer = 4.0  # grace period: read the room before the horde moves
		else:
			return
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
		_world_root().add_child(hound)
		hound.global_position = sp.global_position
		hound.reset_physics_interpolation()
		hound.setup(maxf(150.0, hp * 0.55))
		hound.died.connect(_on_enemy_died)
		zombies_remaining_to_spawn -= 1
		active_zombies += 1
		return

	# Spawn Panzersoldat Boss midway through every 8th non-dog round (Rounds 8, 16, 24, ...)
	if _is_panzer_round and not _panzer_spawned_this_round and zombies_remaining_to_spawn <= maxi(2, GameManager.get_zombie_count_for_round(r) / 2):
		_panzer_spawned_this_round = true
		zombies_remaining_to_spawn -= 1
		spawn_panzer_boss(r)
		return

	var windows := _get_unlocked_windows()
	if windows.is_empty():
		return
	var win := windows[randi() % windows.size()]

	var variant := "soldier"
	if not _brute_spawned_this_round and not _is_panzer_round and r >= 6 and (r - 6) % 5 == 0 and zombies_remaining_to_spawn <= 3:
		variant = "brute"
		_brute_spawned_this_round = true
	else:
		var roll := randf()
		if r >= 3 and roll < 0.12:
			variant = "crawler"
		elif roll < 0.36:
			variant = "worker"
		elif roll < 0.64:
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
	_world_root().add_child(z)
	z.global_position = win.get_spawn_pos()
	z.reset_physics_interpolation()

	zombies_remaining_to_spawn -= 1
	active_zombies += 1


func _get_unlocked_windows() -> Array[Node]:
	var zones := GameManager.unlocked_zones
	if not _windows_cache_dirty and _windows_zones_snapshot == zones and not _cached_windows.is_empty():
		var all_valid := true
		for w in _cached_windows:
			if not is_instance_valid(w) or not w.is_inside_tree():
				all_valid = false
				break
		if all_valid:
			return _cached_windows
	var out: Array[Node] = []
	for w in get_tree().get_nodes_in_group("window_barricades"):
		if zones.get(str(w.get("zone_id")), true):
			out.append(w)
	_cached_windows = out
	_windows_zones_snapshot = zones.duplicate()
	_windows_cache_dirty = false
	return _cached_windows


func _get_unlocked_dog_spawns() -> Array[Node3D]:
	var zones := GameManager.unlocked_zones
	if not _dog_spawns_cache_dirty and _dog_spawns_zones_snapshot == zones and not _cached_dog_spawns.is_empty():
		var all_valid := true
		for s in _cached_dog_spawns:
			if not is_instance_valid(s) or not s.is_inside_tree():
				all_valid = false
				break
		if all_valid:
			return _cached_dog_spawns
	var out: Array[Node3D] = []
	for s in get_tree().get_nodes_in_group("dog_spawns"):
		var zid := str(s.get_meta("zone_id", "spawn"))
		if zones.get(zid, true):
			out.append(s as Node3D)
	_cached_dog_spawns = out
	_dog_spawns_zones_snapshot = zones.duplicate()
	_dog_spawns_cache_dirty = false
	return _cached_dog_spawns


func _on_enemy_died(enemy: Node, _hs: bool, pos: Vector3, force_drop: bool) -> void:
	active_zombies = maxi(0, active_zombies - 1)
	_kills_since_drop += 1

	# Panzersoldat Boss & Dog round finale ALWAYS drop Max Ammo!
	if enemy is PanzerBossAI:
		_spawn_powerup("max_ammo", pos + Vector3.UP * 0.6)
		return

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
	_world_root().add_child(pu)
	pu.global_position = pos
	pu.reset_physics_interpolation()
	if pu.has_method("setup"):
		pu.setup(kind)


func _on_nuke() -> void:
	for z in get_tree().get_nodes_in_group("zombies"):
		if z.has_method("kill_by_nuke"):
			z.kill_by_nuke()

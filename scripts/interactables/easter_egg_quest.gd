extends Node3D
class_name EasterEggQuest

@onready var model_holder: Node3D = $ModelHolder
@onready var terminal_light: OmniLight3D = $OmniLight3D

var step: int = 0
var completed: bool = false

var _beacon_mat: StandardMaterial3D = null
var _resonators: Array[QuestResonator] = []
var _canisters: Array[QuestCanister] = []
var _world_root: Node = null
var _round_director: RoundDirector = null
var _quest_boss: PanzerBossAI = null
var _boss_defeated: bool = false
var _connected_zombie_ids: Dictionary = {}
var _watching_spawns: bool = false


func _ready() -> void:
	add_to_group("easter_egg_quests")
	GameManager.power_activated.connect(_on_power_activated)

	if ResourceLoader.exists("res://assets/models/props/quest_terminal.glb"):
		var inst := (load("res://assets/models/props/quest_terminal.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
		var beacon := inst.find_child("StatusBeacon", true, false) as Node3D
		_beacon_mat = _extract_beacon_mat(beacon)

	call_deferred("_bind_world_nodes")
	_refresh_terminal_visuals()


func _exit_tree() -> void:
	_set_watching_spawns(false)
	_connected_zombie_ids.clear()


func _extract_beacon_mat(node: Node) -> StandardMaterial3D:
	if node == null:
		return null
	var stack: Array[Node] = [node]
	while not stack.is_empty():
		var cur: Node = stack.pop_back()
		if cur is MeshInstance3D:
			var mi := cur as MeshInstance3D
			var mat := mi.get_active_material(0)
			if mat is StandardMaterial3D and (mat as StandardMaterial3D).emission_enabled:
				var dup := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
				mi.set_surface_override_material(0, dup)
				return dup
		for ch in cur.get_children():
			stack.append(ch)
	return null


func _resolve_world_root() -> Node:
	if _world_root != null and is_instance_valid(_world_root):
		return _world_root
	var cur: Node = get_parent()
	while cur != null and cur != get_tree().root:
		if cur.find_child("RoundDirector", false, false) != null or cur is GameWorld:
			_world_root = cur
			return _world_root
		cur = cur.get_parent()
	_world_root = get_parent()
	return _world_root


func _bind_world_nodes() -> void:
	var wroot := _resolve_world_root()
	if wroot != null:
		_round_director = wroot.find_child("RoundDirector", true, false) as RoundDirector

	_resonators.clear()
	for r in get_tree().get_nodes_in_group("quest_resonators"):
		if r is QuestResonator and (wroot == null or wroot.is_ancestor_of(r)):
			var qr := r as QuestResonator
			_resonators.append(qr)
			if not qr.attuned.is_connected(_on_resonator_attuned):
				qr.attuned.connect(_on_resonator_attuned)
	_resonators.sort_custom(func(a: QuestResonator, b: QuestResonator) -> bool: return a.resonator_index < b.resonator_index)

	_canisters.clear()
	for c in get_tree().get_nodes_in_group("quest_canisters"):
		if c is QuestCanister and (wroot == null or wroot.is_ancestor_of(c)):
			var qc := c as QuestCanister
			_canisters.append(qc)
			if not qc.filled.is_connected(_on_canister_filled):
				qc.filled.connect(_on_canister_filled)
	_canisters.sort_custom(func(a: QuestCanister, b: QuestCanister) -> bool: return a.canister_index < b.canister_index)


func _ensure_bound() -> void:
	if _resonators.is_empty() or _canisters.is_empty() or _round_director == null:
		_bind_world_nodes()


func get_interact_prompt(_player: Node) -> String:
	if completed:
		return "Operation Element 115 Complete!"
	match step:
		0:
			return "[E] Initiate Operation Element 115"
		1:
			return "Quest Step 1: Activate Facility Power"
		2:
			return "Quest Step 2: Shoot 4 Resonators (%d/%d)" % [_count_attuned_resonators(), _resonators.size()]
		3:
			return "Quest Step 3: Fill 3 Soul Canisters (%d/%d Full)" % [_count_filled_canisters(), _canisters.size()]
		4:
			if _boss_defeated:
				return "[E] Execute Final Extraction Override"
			return "Quest Step 4: Defeat Containment Panzersoldat!"
		_:
			return ""


func interact(player: Node) -> void:
	if completed:
		return
	_ensure_bound()
	if step == 0:
		_start_quest()
	elif step == 4 and _boss_defeated:
		_complete_easter_egg(player)


func _start_quest() -> void:
	step = 1
	GameManager.set_quest_state(1, "Activate Facility Power", false)
	GameManager.powerup_banner.emit("OPERATION ELEMENT 115 INITIATED", Color(0.25, 0.92, 1.0))
	AudioManager.play_3d("power_on", global_position, 0.05, 0.0)
	_refresh_terminal_visuals()
	if GameManager.power_on:
		_advance_to_step_2()


func _on_power_activated() -> void:
	if step == 1:
		_advance_to_step_2()


func _advance_to_step_2() -> void:
	_ensure_bound()
	step = 2
	for r in _resonators:
		r.set_active(true)
	var total := _resonators.size()
	var cnt := _count_attuned_resonators()
	GameManager.set_quest_state(2, "Shoot %d Element-115 Resonators (%d/%d)" % [total, cnt, total], false)
	GameManager.powerup_banner.emit("STEP 2: ATTUNE ELEMENT-115 RESONATORS (%d/%d)" % [cnt, total], Color(1.0, 0.62, 0.16))
	_refresh_terminal_visuals()
	if total > 0 and cnt >= total:
		_advance_to_step_3()


func _on_resonator_attuned(_res: QuestResonator) -> void:
	if step != 2:
		return
	var total := _resonators.size()
	var cnt := _count_attuned_resonators()
	GameManager.set_quest_state(2, "Shoot %d Element-115 Resonators (%d/%d)" % [total, cnt, total], false)
	GameManager.powerup_banner.emit("RESONATOR ATTUNED (%d/%d)" % [cnt, total], Color(0.25, 0.94, 1.0))
	if total > 0 and cnt >= total:
		_advance_to_step_3()


func _advance_to_step_3() -> void:
	_ensure_bound()
	step = 3
	for c in _canisters:
		c.set_active(true)
	_set_watching_spawns(true)
	_connect_existing_zombies()
	var total := _canisters.size()
	var full := _count_filled_canisters()
	GameManager.set_quest_state(3, "Fill %d Soul Canisters (%d/%d Full)" % [total, full, total], false)
	GameManager.powerup_banner.emit("STEP 3: FILL 3 SOUL CANISTERS NEARBY", Color(0.24, 0.90, 1.0))
	_refresh_terminal_visuals()
	if total > 0 and full >= total:
		_advance_to_step_4()


func _set_watching_spawns(enable: bool) -> void:
	if not is_inside_tree():
		_watching_spawns = false
		return
	var tree := get_tree()
	if enable and not _watching_spawns:
		if not tree.node_added.is_connected(_on_tree_node_added):
			tree.node_added.connect(_on_tree_node_added)
		_watching_spawns = true
	elif not enable and _watching_spawns:
		if tree.node_added.is_connected(_on_tree_node_added):
			tree.node_added.disconnect(_on_tree_node_added)
		_watching_spawns = false


func _connect_existing_zombies() -> void:
	if not is_inside_tree():
		return
	var wroot := _resolve_world_root()
	for z in get_tree().get_nodes_in_group("zombies"):
		if wroot == null or wroot.is_ancestor_of(z):
			_track_enemy(z)


func _on_tree_node_added(node: Node) -> void:
	if step != 3:
		return
	var wroot := _resolve_world_root()
	if wroot != null and not wroot.is_ancestor_of(node):
		return
	if node is ZombieAI or node is HellhoundAI or node is PanzerBossAI:
		_track_enemy(node)


func _track_enemy(enemy: Node) -> void:
	if enemy == null or not is_instance_valid(enemy) or not enemy.has_signal("died"):
		return
	var eid := enemy.get_instance_id()
	if _connected_zombie_ids.has(eid):
		return
	_connected_zombie_ids[eid] = true
	if not enemy.died.is_connected(_on_tracked_enemy_died):
		enemy.died.connect(_on_tracked_enemy_died)


func _on_tracked_enemy_died(_enemy: Node, _hs: bool, death_pos: Vector3, _force_drop: bool) -> void:
	if step != 3:
		return
	register_soul_near(death_pos)


func register_soul_near(pos: Vector3) -> bool:
	if step != 3:
		return false
	_ensure_bound()
	var best_canister: QuestCanister = null
	var best_dist := INF
	for c in _canisters:
		if c.can_absorb_soul_at(pos):
			var d := c.global_position.distance_to(pos)
			if d < best_dist:
				best_dist = d
				best_canister = c
	if best_canister == null:
		return false
	if best_canister.add_soul():
		var full := _count_filled_canisters()
		var total := _canisters.size()
		GameManager.set_quest_state(3, "Fill %d Soul Canisters (%d/%d Full)" % [total, full, total], false)
		if full >= total:
			_advance_to_step_4()
		return true
	return false


func _on_canister_filled(_canister: QuestCanister) -> void:
	if step != 3:
		return
	var full := _count_filled_canisters()
	var total := _canisters.size()
	GameManager.powerup_banner.emit("SOUL CANISTER CHARGED (%d/%d)" % [full, total], Color(0.24, 1.0, 0.56))
	if total > 0 and full >= total:
		_advance_to_step_4()


func _advance_to_step_4() -> void:
	_ensure_bound()
	step = 4
	_boss_defeated = false
	_set_watching_spawns(false)
	var spawn_pos := Vector3(15.0, 0.05, -33.0)
	if _round_director != null and _round_director.has_method("spawn_panzer_boss"):
		_quest_boss = _round_director.spawn_panzer_boss(maxi(8, GameManager.current_round), spawn_pos)
		if _quest_boss != null and not _quest_boss.died.is_connected(_on_quest_boss_died):
			_quest_boss.died.connect(_on_quest_boss_died)
	GameManager.set_quest_state(4, "Defeat the Containment Panzersoldat!", false)
	GameManager.powerup_banner.emit("STEP 4: CONTAINMENT BREACH — DEFEAT PANZERSOLDAT!", Color(1.0, 0.28, 0.16))
	_refresh_terminal_visuals()


func _on_quest_boss_died(_boss: PanzerBossAI, _hs: bool, _pos: Vector3, _drop: bool) -> void:
	if step != 4 or _boss_defeated:
		return
	_boss_defeated = true
	GameManager.set_quest_state(4, "Return to Quest Terminal for Final Override", false)
	GameManager.powerup_banner.emit("PANZERSOLDAT DESTROYED — INTERACT WITH QUEST TERMINAL!", Color(0.25, 1.0, 0.65))
	_refresh_terminal_visuals()


func _complete_easter_egg(player: Node) -> void:
	completed = true
	step = 5
	GameManager.unlock_all_perk_slots()
	for pid in GameManager.PERK_INFO.keys():
		GameManager.grant_perk(str(pid), false)

	var p: Node = player if player != null else get_tree().get_first_node_in_group("player")
	if p != null:
		if p.has_method("give_weapon"):
			p.give_weapon("wunderwaffe")
		if p.has_method("pack_current_weapon"):
			p.pack_current_weapon()

	GameManager.add_points(5000, "Operation Element 115")
	GameManager.set_quest_state(5, "Operation Element 115 Complete!", true)
	GameManager.powerup_banner.emit("OPERATION ELEMENT 115 COMPLETE! ALL 9 PERKS + DG-3 JZ!", Color(0.30, 1.0, 0.72))
	AudioManager.play_2d("powerup_collect", 0.0, 2.0)
	_refresh_terminal_visuals()


func _count_attuned_resonators() -> int:
	var n := 0
	for r in _resonators:
		if r.is_attuned:
			n += 1
	return n


func _count_filled_canisters() -> int:
	var n := 0
	for c in _canisters:
		if c.is_filled:
			n += 1
	return n


func _refresh_terminal_visuals() -> void:
	var col := Color(0.20, 0.88, 1.0)
	var em := 1.6
	var le := 1.5
	if completed:
		col = Color(0.25, 1.0, 0.56)
		em = 3.0
		le = 3.2
	elif step == 4 and _boss_defeated:
		col = Color(0.25, 1.0, 0.56)
		em = 2.8
		le = 2.8
	elif step == 4:
		col = Color(1.0, 0.24, 0.16)
		em = 2.8
		le = 2.6
	elif step > 0:
		col = Color(1.0, 0.64, 0.16)
		em = 2.2
		le = 2.1

	if _beacon_mat:
		_beacon_mat.albedo_color = col
		_beacon_mat.emission_enabled = true
		_beacon_mat.emission = col
		_beacon_mat.emission_energy_multiplier = em
	if terminal_light:
		terminal_light.light_color = col
		terminal_light.light_energy = le

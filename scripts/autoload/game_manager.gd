extends Node

signal points_changed(new_points: int, delta: int, reason: String)
signal round_changed(new_round: int, is_dog_round: bool)
signal power_activated
signal perks_changed(perks: Array[String])
signal powerup_updated(active_timers: Dictionary)
signal powerup_banner(label_text: String, color: Color)
signal zone_unlocked(zone_id: String)
signal game_over_triggered(stats: Dictionary)
signal carpenter_triggered
signal nuke_triggered
signal fire_sale_changed(active: bool)
signal player_health_changed(hp: float, max_hp: float)
signal player_stamina_changed(stamina: float, max_stamina: float)
signal player_downed_changed(is_downed: bool, revive_progress: float)
signal weapon_hud_updated(weapon_name: String, packed: bool, mag: int, reserve: int, grenades: int, secondary_name: String)
signal prompt_changed(text: String)
signal hitmarker_triggered(is_kill: bool, is_headshot: bool)
signal quest_updated(step: int, description: String, completed: bool)

const PERK_INFO := {
	"quickrevive": {"name": "Quick Revive", "cost": 500, "icon": "res://assets/textures/ui/perk_quickrevive.png", "color": Color(0.2, 0.65, 1.0)},
	"juggernog": {"name": "Juggernog", "cost": 2500, "icon": "res://assets/textures/ui/perk_juggernog.png", "color": Color(0.95, 0.2, 0.22)},
	"speedcola": {"name": "Speed Cola", "cost": 3000, "icon": "res://assets/textures/ui/perk_speedcola.png", "color": Color(0.2, 0.9, 0.35)},
	"doubletap": {"name": "Double Tap II", "cost": 2000, "icon": "res://assets/textures/ui/perk_doubletap.png", "color": Color(0.98, 0.72, 0.15)},
	"staminup": {"name": "Stamin-Up", "cost": 2000, "icon": "res://assets/textures/ui/perk_staminup.png", "color": Color(0.98, 0.45, 0.12)},
	"mulekick": {"name": "Mule Kick", "cost": 4000, "icon": "res://assets/textures/ui/perk_mulekick.png", "color": Color(0.22, 0.86, 0.38)},
	"deadshot": {"name": "Deadshot Daiquiri", "cost": 1500, "icon": "res://assets/textures/ui/perk_deadshot.png", "color": Color(0.96, 0.76, 0.18)},
	"phdflopper": {"name": "PhD Flopper", "cost": 2000, "icon": "res://assets/textures/ui/perk_phdflopper.png", "color": Color(0.72, 0.28, 0.96)},
	"electriccherry": {"name": "Electric Cherry", "cost": 2000, "icon": "res://assets/textures/ui/perk_electriccherry.png", "color": Color(0.22, 0.88, 1.0)},
}

var points: int = 500
var current_round: int = 1
var power_on: bool = false
var perks: Array[String] = []
var max_perks: int = 4
var quick_revive_uses_left: int = 3
var quest_step: int = 0
var quest_description: String = ""
var quest_completed: bool = false
var unlocked_zones: Dictionary = {
	"spawn": true,
	"west_lab": false,
	"east_courtyard": false,
	"reactor": false,
	"north_yard": false,
}
var active_powerups: Dictionary = {
	"insta_kill": 0.0,
	"double_points": 0.0,
	"fire_sale": 0.0,
}
var is_game_over: bool = false
var round_barrier_points_earned: int = 0

var stats: Dictionary = {
	"rounds_survived": 1,
	"kills": 0,
	"headshots": 0,
	"doors_opened": 0,
	"total_points": 500,
	"pap_upgrades": 0,
	"barriers_repaired": 0,
	"easter_egg_completed": false,
	"quest_step": 0,
}


func _process(delta: float) -> void:
	if is_game_over:
		return
	var changed := false
	var was_fire_sale: bool = active_powerups["fire_sale"] > 0.0
	for k in active_powerups.keys():
		if active_powerups[k] > 0.0:
			active_powerups[k] = maxf(0.0, active_powerups[k] - delta)
			changed = true
	if changed:
		emit_signal("powerup_updated", active_powerups.duplicate())
		var is_fire_sale_now: bool = active_powerups["fire_sale"] > 0.0
		if was_fire_sale != is_fire_sale_now:
			emit_signal("fire_sale_changed", is_fire_sale_now)


func reset_match() -> void:
	points = 500
	current_round = 1
	power_on = false
	perks.clear()
	max_perks = 4
	quick_revive_uses_left = 3
	quest_step = 0
	quest_description = ""
	quest_completed = false
	unlocked_zones = {
		"spawn": true,
		"west_lab": false,
		"east_courtyard": false,
		"reactor": false,
		"north_yard": false,
	}
	active_powerups = {
		"insta_kill": 0.0,
		"double_points": 0.0,
		"fire_sale": 0.0,
	}
	is_game_over = false
	round_barrier_points_earned = 0
	stats = {
		"rounds_survived": 1,
		"kills": 0,
		"headshots": 0,
		"doors_opened": 0,
		"total_points": 500,
		"pap_upgrades": 0,
		"barriers_repaired": 0,
		"easter_egg_completed": false,
		"quest_step": 0,
	}
	emit_signal("points_changed", points, 0, "")
	emit_signal("perks_changed", perks)
	emit_signal("powerup_updated", active_powerups.duplicate())
	emit_signal("quest_updated", quest_step, quest_description, quest_completed)


func add_points(amount: int, reason: String = "") -> void:
	if amount <= 0:
		return
	var mult := 2 if active_powerups.get("double_points", 0.0) > 0.0 else 1
	var total := amount * mult
	points += total
	stats["total_points"] += total
	emit_signal("points_changed", points, total, reason)


func add_barrier_repair_points() -> bool:
	var cap := mini(490, 40 + (current_round - 1) * 50)
	if round_barrier_points_earned >= cap:
		return false
	round_barrier_points_earned += 10
	stats["barriers_repaired"] += 1
	add_points(10, "Barrier Repaired")
	return true


func spend_points(cost: int) -> bool:
	if points < cost:
		AudioManager.play_2d("buy_denied", 0.02, -2.0)
		return false
	points -= cost
	AudioManager.play_2d("buy_confirm", 0.03, 0.0)
	emit_signal("points_changed", points, -cost, "")
	return true


func has_perk(perk_id: String) -> bool:
	return perk_id in perks


func can_buy_perk(perk_id: String) -> bool:
	return not has_perk(perk_id) and perks.size() < max_perks


func get_unowned_perks() -> Array[String]:
	var out: Array[String] = []
	for pid in PERK_INFO.keys():
		if not has_perk(str(pid)):
			out.append(str(pid))
	return out


func unlock_all_perk_slots() -> void:
	max_perks = PERK_INFO.size()


func set_quest_state(step: int, desc: String, completed: bool) -> void:
	quest_step = step
	quest_description = desc
	quest_completed = completed
	stats["quest_step"] = step
	stats["easter_egg_completed"] = completed
	emit_signal("quest_updated", step, desc, completed)


func grant_perk(perk_id: String, respect_limit: bool = false) -> bool:
	if has_perk(perk_id):
		return false
	if respect_limit and perks.size() >= max_perks:
		return false
	perks.append(perk_id)
	AudioManager.play_2d("perk_drink", 0.02, 0.0)
	emit_signal("perks_changed", perks.duplicate())
	return true


func lose_all_perks() -> void:
	if perks.is_empty():
		return
	perks.clear()
	emit_signal("perks_changed", perks.duplicate())


func activate_power() -> void:
	if power_on:
		return
	power_on = true
	AudioManager.play_2d("power_on", 0.0, 2.0)
	emit_signal("power_activated")
	emit_signal("powerup_banner", "POWER ACTIVATED", Color(0.25, 0.92, 1.0))


func unlock_zone(zone_id: String) -> void:
	if unlocked_zones.get(zone_id, false):
		return
	unlocked_zones[zone_id] = true
	stats["doors_opened"] += 1
	emit_signal("zone_unlocked", zone_id)


func activate_powerup(kind: String) -> void:
	AudioManager.play_2d("powerup_collect", 0.03, 1.0)
	match kind:
		"max_ammo":
			emit_signal("powerup_banner", "MAX AMMO!", Color(0.35, 1.0, 0.45))
			get_tree().call_group("player", "refill_all_ammo")
		"insta_kill":
			active_powerups["insta_kill"] = 30.0
			emit_signal("powerup_banner", "INSTA-KILL (30s)", Color(1.0, 0.25, 0.25))
			emit_signal("powerup_updated", active_powerups.duplicate())
		"double_points":
			active_powerups["double_points"] = 30.0
			emit_signal("powerup_banner", "DOUBLE POINTS (30s)", Color(1.0, 0.85, 0.2))
			emit_signal("powerup_updated", active_powerups.duplicate())
		"nuke":
			AudioManager.play_2d("explosion", 0.04, 1.0)
			add_points(400, "Kaboom!")
			emit_signal("powerup_banner", "KA-BOOM! (+400)", Color(1.0, 0.65, 0.15))
			emit_signal("nuke_triggered")
		"carpenter":
			add_points(200, "Carpenter")
			emit_signal("powerup_banner", "CARPENTER! (+200)", Color(0.75, 0.9, 1.0))
			emit_signal("carpenter_triggered")
		"fire_sale":
			active_powerups["fire_sale"] = 30.0
			emit_signal("powerup_banner", "FIRE SALE! ($10 BOX)", Color(1.0, 0.55, 0.9))
			emit_signal("fire_sale_changed", true)
			emit_signal("powerup_updated", active_powerups.duplicate())


func trigger_game_over() -> void:
	if is_game_over:
		return
	is_game_over = true
	stats["rounds_survived"] = current_round
	AudioManager.stop_ambience()
	emit_signal("game_over_triggered", stats.duplicate())


func is_dog_round(r: int) -> bool:
	return r >= 5 and r % 5 == 0


func get_zombie_health_for_round(r: int) -> float:
	if r <= 1:
		return 150.0
	if r <= 9:
		return 150.0 + float(r - 1) * 100.0
	var hp := 950.0
	for _i in range(10, r + 1):
		hp = roundf(hp * 1.1)
	return hp


func get_zombie_count_for_round(r: int) -> int:
	if is_dog_round(r):
		return mini(14, 5 + (r / 5) * 3)
	match r:
		1:
			return 6
		2:
			return 8
		3:
			return 13
		4:
			return 18
		_:
			return mini(120, int(roundf(24.0 + 0.15 * float(r * r))))

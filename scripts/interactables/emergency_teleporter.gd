extends Node3D
class_name EmergencyTeleporter

const COST := 500
const COOLDOWN := 45.0
const EXIT_POSITION := Vector3(0.0, 0.1, 6.0)

var cooldown_remaining: float = 0.0
var _last_power: int = -1
var _last_ready: int = -1
var _last_secs: int = -2
@onready var status_light: OmniLight3D = $StatusLight
@onready var display: Label3D = $Display


func _ready() -> void:
	GameManager.power_activated.connect(_refresh_status)
	_refresh_status()


func _process(delta: float) -> void:
	if cooldown_remaining > 0.0:
		cooldown_remaining = maxf(0.0, cooldown_remaining - delta)
	var cur_power := 1 if GameManager.power_on else 0
	var cur_ready := 1 if (GameManager.power_on and cooldown_remaining <= 0.0) else 0
	var cur_secs := ceili(cooldown_remaining) if (GameManager.power_on and cooldown_remaining > 0.0) else -1
	if cur_power != _last_power or cur_ready != _last_ready or cur_secs != _last_secs:
		_refresh_status()


func _refresh_status() -> void:
	var cur_power := 1 if GameManager.power_on else 0
	var ready := GameManager.power_on and cooldown_remaining <= 0.0
	var cur_ready := 1 if ready else 0
	var cur_secs := ceili(cooldown_remaining) if (GameManager.power_on and cooldown_remaining > 0.0) else -1
	_last_power = cur_power
	_last_ready = cur_ready
	_last_secs = cur_secs
	status_light.light_color = Color(0.15, 0.95, 0.75) if ready else Color(1.0, 0.22, 0.06)
	status_light.light_energy = 1.8 if ready else 0.35
	var txt := "RETURN TO COURTYARD\n500 POINTS" if ready else (
		"RECHARGING %ds" % cur_secs if GameManager.power_on else "AUXILIARY LINK\nNO POWER")
	if display.text != txt:
		display.text = txt
	display.modulate = status_light.light_color


func get_interact_prompt(player: Node) -> String:
	if GameManager.is_game_over or bool(player.get("is_downed")):
		return ""
	if not GameManager.power_on:
		return "Emergency Teleporter — Power Must Be Turned On!"
	if cooldown_remaining > 0.0:
		return "Emergency Teleporter — Recharging (%ds)" % ceili(cooldown_remaining)
	return "[E] Teleport to Courtyard [Cost: %d]" % COST


func interact(player: Node) -> void:
	if not player is PlayerController or GameManager.is_game_over or player.is_downed:
		return
	if not GameManager.power_on or cooldown_remaining > 0.0:
		return
	if not GameManager.spend_points(COST):
		return
	cooldown_remaining = COOLDOWN
	player.global_position = EXIT_POSITION
	player.velocity = Vector3.ZERO
	player.reset_physics_interpolation()
	AudioManager.play_3d("power_on", global_position, 0.0, 0.0)
	GameManager.powerup_banner.emit("EMERGENCY TRANSFER — COURTYARD", Color(0.2, 0.95, 0.85))
	_refresh_status()

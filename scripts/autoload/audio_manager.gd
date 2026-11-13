extends Node

const SFX_PATHS := {
	"shot_pistol": "res://assets/audio/weapons/shot_pistol.wav",
	"shot_pistol_pap": "res://assets/audio/weapons/shot_pistol_pap.wav",
	"shot_shotgun": "res://assets/audio/weapons/shot_shotgun.wav",
	"shot_shotgun_pap": "res://assets/audio/weapons/shot_shotgun_pap.wav",
	"shot_smg": "res://assets/audio/weapons/shot_smg.wav",
	"shot_smg_pap": "res://assets/audio/weapons/shot_smg_pap.wav",
	"shot_rifle": "res://assets/audio/weapons/shot_rifle.wav",
	"shot_rifle_pap": "res://assets/audio/weapons/shot_rifle_pap.wav",
	"shot_sniper": "res://assets/audio/weapons/shot_sniper.wav",
	"shot_sniper_pap": "res://assets/audio/weapons/shot_sniper_pap.wav",
	"shot_raygun": "res://assets/audio/weapons/shot_raygun.wav",
	"reload_click": "res://assets/audio/weapons/reload_click.wav",
	"empty_click": "res://assets/audio/weapons/empty_click.wav",
	"knife_slash": "res://assets/audio/weapons/knife_slash.wav",
	"headshot_crunch": "res://assets/audio/weapons/headshot_crunch.wav",
	"explosion": "res://assets/audio/weapons/explosion.wav",
	"zombie_groan_1": "res://assets/audio/zombies/zombie_groan_1.wav",
	"zombie_groan_2": "res://assets/audio/zombies/zombie_groan_2.wav",
	"hellhound_howl": "res://assets/audio/zombies/hellhound_howl.wav",
	"plank_break": "res://assets/audio/zombies/plank_break.wav",
	"plank_repair": "res://assets/audio/zombies/plank_repair.wav",
	"round_start": "res://assets/audio/ui/round_start.wav",
	"round_end": "res://assets/audio/ui/round_end.wav",
	"buy_confirm": "res://assets/audio/ui/buy_confirm.wav",
	"buy_denied": "res://assets/audio/ui/buy_denied.wav",
	"mystery_box_jingle": "res://assets/audio/ui/mystery_box_jingle.wav",
	"power_on": "res://assets/audio/ui/power_on.wav",
	"powerup_collect": "res://assets/audio/ui/powerup_collect.wav",
	"perk_drink": "res://assets/audio/ui/perk_drink.wav",
	"hitmarker": "res://assets/audio/ui/hitmarker.wav",
	"player_hurt": "res://assets/audio/ui/player_hurt.wav",
	"bunker_ambience": "res://assets/audio/ambience/bunker_ambience.wav",
}

var _streams: Dictionary = {}
var _pool_2d: Array[AudioStreamPlayer] = []
var _pool_3d: Array[AudioStreamPlayer3D] = []
var _idx_2d: int = 0
var _idx_3d: int = 0
var _ambience_player: AudioStreamPlayer


func _ready() -> void:
	for key in SFX_PATHS.keys():
		var path: String = SFX_PATHS[key]
		if ResourceLoader.exists(path):
			_streams[key] = load(path)
	for i in range(16):
		var p2 := AudioStreamPlayer.new()
		add_child(p2)
		_pool_2d.append(p2)
	for i in range(16):
		var p3 := AudioStreamPlayer3D.new()
		p3.max_distance = 38.0
		p3.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		add_child(p3)
		_pool_3d.append(p3)

	_ambience_player = AudioStreamPlayer.new()
	add_child(_ambience_player)


func play_2d(key: String, pitch_jitter: float = 0.04, volume_db: float = 0.0) -> void:
	var stream: AudioStream = _streams.get(key, null)
	if stream == null:
		return
	var p := _pool_2d[_idx_2d]
	_idx_2d = (_idx_2d + 1) % _pool_2d.size()
	p.stream = stream
	p.pitch_scale = randf_range(1.0 - pitch_jitter, 1.0 + pitch_jitter)
	p.volume_db = volume_db + linear_to_db(maxf(0.001, SettingsManager.sfx_volume))
	p.play()


func play_3d(key: String, pos: Vector3, pitch_jitter: float = 0.06, volume_db: float = 0.0, max_dist: float = 36.0) -> void:
	var stream: AudioStream = _streams.get(key, null)
	if stream == null:
		return
	var p := _pool_3d[_idx_3d]
	_idx_3d = (_idx_3d + 1) % _pool_3d.size()
	p.global_position = pos
	p.max_distance = max_dist
	p.stream = stream
	p.pitch_scale = randf_range(1.0 - pitch_jitter, 1.0 + pitch_jitter)
	p.volume_db = volume_db + linear_to_db(maxf(0.001, SettingsManager.sfx_volume))
	p.play()


func start_ambience() -> void:
	var stream: AudioStream = _streams.get("bunker_ambience", null)
	if stream == null:
		return
	if stream is AudioStreamWAV:
		(stream as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_FORWARD
	_ambience_player.stream = stream
	_ambience_player.volume_db = -12.0 + linear_to_db(maxf(0.001, SettingsManager.sfx_volume))
	if not _ambience_player.playing:
		_ambience_player.play()


func stop_ambience() -> void:
	if _ambience_player and _ambience_player.playing:
		_ambience_player.stop()


func _exit_tree() -> void:
	stop_ambience()
	if _ambience_player:
		_ambience_player.stream = null
	for p2 in _pool_2d:
		if p2:
			p2.stop()
			p2.stream = null
	for p3 in _pool_3d:
		if p3:
			p3.stop()
			p3.stream = null
	_streams.clear()

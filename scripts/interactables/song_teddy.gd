extends Node3D
class_name SongTeddy

@export var teddy_index: int = 0

@onready var model_holder: Node3D = $ModelHolder
@onready var interact_area: Area3D = $InteractArea
@onready var glow_light: OmniLight3D = $OmniLight3D
@onready var song_player: AudioStreamPlayer = $SongPlayer

var activated: bool = false
var _song_playing: bool = false


func _ready() -> void:
	add_to_group("song_teddies")
	if ResourceLoader.exists("res://assets/models/props/teddy_bear.glb"):
		var inst := (load("res://assets/models/props/teddy_bear.glb") as PackedScene).instantiate()
		model_holder.add_child(inst)
	glow_light.light_color = Color(1.0, 0.18, 0.12)
	glow_light.light_energy = 0.45


func _exit_tree() -> void:
	if song_player:
		song_player.stop()
		song_player.stream = null


func _sibling_teddies() -> Array[SongTeddy]:
	var out: Array[SongTeddy] = []
	var wroot: Node = get_parent()
	while wroot != null and wroot != get_tree().root:
		if wroot.find_child("RoundDirector", false, false) != null or wroot is GameWorld:
			break
		wroot = wroot.get_parent()
	for node in get_tree().get_nodes_in_group("song_teddies"):
		if node is SongTeddy:
			if wroot == null or wroot == get_tree().root or wroot.is_ancestor_of(node):
				out.append(node as SongTeddy)
	return out


func get_interact_prompt(_player: Node) -> String:
	if activated:
		return ""
	return "[E] Activate Element 115 Teddy"


func interact(_player: Node) -> void:
	if activated:
		return
	activated = true
	if interact_area:
		interact_area.collision_layer = 0
	glow_light.light_color = Color(0.22, 0.92, 1.0)
	glow_light.light_energy = 1.6
	AudioManager.play_3d("perk_drink", global_position, 0.15, 2.0, 26.0)

	var siblings := _sibling_teddies()
	var active_count := 0
	for t in siblings:
		if t.activated:
			active_count += 1
	var total := maxi(siblings.size(), 3)

	if active_count >= total:
		_trigger_easter_egg_song(siblings)
	else:
		GameManager.powerup_banner.emit("ELEMENT 115 RECORDING (%d/%d)" % [active_count, total], Color(0.28, 0.92, 1.0))


func _trigger_easter_egg_song(siblings: Array[SongTeddy]) -> void:
	for t in siblings:
		if t.glow_light:
			t.glow_light.light_color = Color(1.0, 0.28, 0.30)
			t.glow_light.light_energy = 2.4
	GameManager.add_points(1150, "115 Song Easter Egg")
	GameManager.powerup_banner.emit("NOW PLAYING: 115 (EASTER EGG SONG!) +1150", Color(1.0, 0.35, 0.35))
	if song_player and ResourceLoader.exists("res://assets/audio/ui/ee_song_115.wav"):
		song_player.stream = load("res://assets/audio/ui/ee_song_115.wav")
		song_player.volume_db = -3.0
		song_player.play()
		_song_playing = true

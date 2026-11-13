extends CanvasLayer

@onready var blood_vignette: TextureRect = $BloodVignette
@onready var nuke_flash: ColorRect = $NukeFlash
@onready var hitmarker: TextureRect = $Center/Hitmarker
@onready var prompt_panel: PanelContainer = $Center/PromptPanel
@onready var prompt_label: Label = $Center/PromptPanel/PromptLabel
@onready var banner_label: Label = $Top/BannerLabel
@onready var timers_box: HBoxContainer = $Top/ActiveTimers
@onready var round_label: Label = $BottomLeft/RoundLabel
@onready var points_label: Label = $BottomLeft/PointsRow/PointsLabel
@onready var delta_box: VBoxContainer = $BottomLeft/PointsRow/DeltaBox
@onready var perks_box: HBoxContainer = $BottomLeft/PerksBox
@onready var hp_bar: ProgressBar = $BottomLeft/Bars/HPBar
@onready var stam_bar: ProgressBar = $BottomLeft/Bars/StamBar
@onready var weapon_name_label: Label = $BottomRight/WeaponName
@onready var ammo_label: Label = $BottomRight/AmmoLabel
@onready var reload_hint: Label = $BottomRight/ReloadHint
@onready var secondary_label: Label = $BottomRight/SecondaryLabel
@onready var revive_panel: PanelContainer = $Center/RevivePanel
@onready var revive_bar: ProgressBar = $Center/RevivePanel/VBox/ReviveBar

var _hitmarker_timer: float = 0.0
var _banner_timer: float = 0.0
var _pulse_t: float = 0.0
var _hp_ratio: float = 1.0


func _ready() -> void:
	blood_vignette.modulate.a = 0.0
	nuke_flash.modulate.a = 0.0
	hitmarker.visible = false
	prompt_panel.visible = false
	banner_label.visible = false
	revive_panel.visible = false
	reload_hint.visible = false

	GameManager.points_changed.connect(_on_points_changed)
	GameManager.round_changed.connect(_on_round_changed)
	GameManager.perks_changed.connect(_on_perks_changed)
	GameManager.powerup_updated.connect(_on_powerup_updated)
	GameManager.powerup_banner.connect(_on_powerup_banner)
	GameManager.nuke_triggered.connect(_on_nuke)
	GameManager.player_health_changed.connect(_on_health_changed)
	GameManager.player_stamina_changed.connect(_on_stamina_changed)
	GameManager.player_downed_changed.connect(_on_downed_changed)
	GameManager.weapon_hud_updated.connect(_on_weapon_updated)
	GameManager.prompt_changed.connect(_on_prompt_changed)
	GameManager.hitmarker_triggered.connect(_on_hitmarker)

	_on_points_changed(GameManager.points, 0, "")
	_on_round_changed(GameManager.current_round, false)


func _process(delta: float) -> void:
	_pulse_t += delta
	if _hitmarker_timer > 0.0:
		_hitmarker_timer -= delta
		if _hitmarker_timer <= 0.0:
			hitmarker.visible = false
	if _banner_timer > 0.0:
		_banner_timer -= delta
		if _banner_timer <= 0.6:
			banner_label.modulate.a = maxf(0.0, _banner_timer / 0.6)
		if _banner_timer <= 0.0:
			banner_label.visible = false

	var base_blood := clampf((1.0 - _hp_ratio) * 1.15, 0.0, 0.92)
	if _hp_ratio < 0.45:
		base_blood += 0.14 * (0.5 + 0.5 * sin(_pulse_t * 7.5))
	blood_vignette.modulate.a = lerpf(blood_vignette.modulate.a, clampf(base_blood, 0.0, 0.95), delta * 8.0)


func _to_roman_or_num(r: int) -> String:
	match r:
		1: return "I"
		2: return "II"
		3: return "III"
		4: return "IV"
		5: return "V"
		_: return str(r)


func _on_round_changed(new_round: int, is_dog: bool) -> void:
	round_label.text = _to_roman_or_num(new_round)
	round_label.modulate = Color(1.0, 0.85, 0.45)
	var tw := create_tween()
	tw.tween_property(round_label, "modulate", Color(0.88, 0.14, 0.14), 1.6)
	if is_dog:
		_on_powerup_banner("FETCH ME THEIR SOULS! (HELLHOUND ROUND)", Color(1.0, 0.45, 0.12))
	elif new_round > 1:
		_on_powerup_banner("ROUND %d" % new_round, Color(0.95, 0.25, 0.22))


func _on_points_changed(new_pts: int, delta_pts: int, _reason: String) -> void:
	points_label.text = "%d" % new_pts
	if delta_pts == 0:
		return
	var lbl := Label.new()
	lbl.text = ("+%d" % delta_pts) if delta_pts > 0 else str(delta_pts)
	lbl.add_theme_font_size_override("font_size", 20)
	lbl.modulate = Color(1.0, 0.86, 0.28) if delta_pts > 0 else Color(1.0, 0.35, 0.35)
	delta_box.add_child(lbl)
	var tw := lbl.create_tween()
	tw.tween_property(lbl, "modulate:a", 0.0, 0.95)
	tw.tween_callback(lbl.queue_free)


func _on_perks_changed(perks: Array[String]) -> void:
	for c in perks_box.get_children():
		c.queue_free()
	for pid in perks:
		var info: Dictionary = GameManager.PERK_INFO.get(pid, {})
		var ipath := str(info.get("icon", ""))
		if ResourceLoader.exists(ipath):
			var tr := TextureRect.new()
			tr.texture = load(ipath)
			tr.custom_minimum_size = Vector2(44, 44)
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			perks_box.add_child(tr)


func _on_powerup_updated(timers: Dictionary) -> void:
	for c in timers_box.get_children():
		c.queue_free()
	var labels := {
		"insta_kill": ["INSTA-KILL", Color(1.0, 0.32, 0.32)],
		"double_points": ["2X POINTS", Color(1.0, 0.86, 0.24)],
		"fire_sale": ["FIRE SALE", Color(1.0, 0.55, 0.92)],
	}
	for k in timers.keys():
		var t: float = float(timers[k])
		if t > 0.0 and labels.has(k):
			var lbl := Label.new()
			lbl.text = "%s: %ds" % [labels[k][0], int(ceilf(t))]
			lbl.add_theme_font_size_override("font_size", 18)
			lbl.modulate = labels[k][1]
			timers_box.add_child(lbl)


func _on_powerup_banner(text: String, color: Color) -> void:
	banner_label.text = text
	banner_label.modulate = color
	banner_label.visible = true
	_banner_timer = 3.2


func _on_nuke() -> void:
	nuke_flash.modulate.a = 0.92
	create_tween().tween_property(nuke_flash, "modulate:a", 0.0, 1.3)


func _on_health_changed(hp: float, max_hp: float) -> void:
	_hp_ratio = clampf(hp / maxf(1.0, max_hp), 0.0, 1.0)
	hp_bar.max_value = max_hp
	hp_bar.value = hp


func _on_stamina_changed(stam: float, max_stam: float) -> void:
	stam_bar.max_value = max_stam
	stam_bar.value = stam


func _on_downed_changed(downed: bool, progress: float) -> void:
	revive_panel.visible = downed
	revive_bar.value = progress * 100.0


func _on_weapon_updated(wname: String, packed: bool, mag: int, reserve: int, grenades: int, sec: String) -> void:
	weapon_name_label.text = ("★ " + wname) if packed else wname
	weapon_name_label.modulate = Color(0.28, 0.95, 1.0) if packed else Color(0.95, 0.95, 0.95)
	ammo_label.text = "%d / %d   [G: %d]" % [mag, reserve, grenades]
	ammo_label.modulate = Color(1.0, 0.28, 0.28) if mag <= 2 else Color(1.0, 1.0, 1.0)
	reload_hint.visible = (mag <= 2 and reserve > 0)
	secondary_label.text = ("ALT [Q]: " + sec) if sec != "" else ""


func _on_prompt_changed(text: String) -> void:
	prompt_panel.visible = text != ""
	prompt_label.text = text


func _on_hitmarker(is_kill: bool, is_headshot: bool) -> void:
	hitmarker.visible = true
	_hitmarker_timer = 0.14
	if is_headshot:
		hitmarker.modulate = Color(1.0, 0.22, 0.22)
	elif is_kill:
		hitmarker.modulate = Color(1.0, 0.55, 0.2)
	else:
		hitmarker.modulate = Color(1.0, 1.0, 1.0)

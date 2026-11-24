extends CanvasLayer

@onready var blood_vignette: TextureRect = $BloodVignette
@onready var nuke_flash: ColorRect = $NukeFlash
@onready var damage_arc: HudDamageArc = $DamageArc
@onready var crosshair: Control = $Center/Crosshair
@onready var top_tick: ColorRect = $Center/Crosshair/TopTick
@onready var bot_tick: ColorRect = $Center/Crosshair/BotTick
@onready var left_tick: ColorRect = $Center/Crosshair/LeftTick
@onready var right_tick: ColorRect = $Center/Crosshair/RightTick
@onready var hitmarker: TextureRect = $Center/Hitmarker
@onready var prompt_panel: PanelContainer = $Center/PromptPanel
@onready var prompt_label: Label = $Center/PromptPanel/PromptLabel
@onready var banner_label: Label = $Top/BannerLabel
@onready var timers_box: HBoxContainer = $Top/ActiveTimers
@onready var chalk_counter: HudChalkCounter = $BottomLeft/ChalkRow/ChalkCounter
@onready var round_label: Label = $BottomLeft/RoundLabel
@onready var points_label: Label = $BottomLeft/PointsRow/PointsLabel
@onready var delta_box: VBoxContainer = $BottomLeft/PointsRow/DeltaBox
@onready var perks_box: HBoxContainer = $BottomLeft/PerksBox
@onready var hp_bar: ProgressBar = $BottomLeft/Bars/HPBar
@onready var stam_bar: ProgressBar = $BottomLeft/Bars/StamBar
@onready var pap_badge: TextureRect = $BottomRight/AmmoCard/VBox/WeaponTopRow/PaPBadge
@onready var weapon_name_label: Label = $BottomRight/AmmoCard/VBox/WeaponTopRow/WeaponName
@onready var ammo_label: Label = $BottomRight/AmmoCard/VBox/AmmoMainRow/AmmoLabel
@onready var grenade_count_label: Label = $BottomRight/AmmoCard/VBox/AmmoMainRow/GrenadeRow/GrenadeCount
@onready var reload_hint: Label = $BottomRight/AmmoCard/VBox/ReloadHint
@onready var secondary_label: Label = $BottomRight/AmmoCard/VBox/SecondaryLabel
@onready var revive_panel: PanelContainer = $Center/RevivePanel
@onready var revive_bar: ProgressBar = $Center/RevivePanel/VBox/ReviveBar

var _hitmarker_timer: float = 0.0
var _banner_timer: float = 0.0
var _pulse_t: float = 0.0
var _hp_ratio: float = 1.0
var _cur_spread_px: float = 10.0
var _target_spread_px: float = 10.0
var _hide_crosshair: bool = false
var _last_round_seen: int = -1
var _last_blood_a: float = -1.0
var _last_ch_a: float = -1.0
var _last_gap: float = -1.0

const FALLBACK_PERK_COLORS := {
	"quickrevive": Color(0.2, 0.65, 1.0),
	"juggernog": Color(0.95, 0.2, 0.22),
	"speedcola": Color(0.2, 0.9, 0.35),
	"doubletap": Color(0.98, 0.72, 0.15),
	"staminup": Color(0.98, 0.45, 0.12),
	"mulekick": Color(0.22, 0.86, 0.38),
	"deadshot": Color(0.96, 0.76, 0.18),
	"phdflopper": Color(0.72, 0.28, 0.96),
	"electriccherry": Color(0.22, 0.88, 1.0),
}


func _apply_cod_style() -> void:
	# Authentic WaW/BO1 zombies HUD: no health bar (blood vignette carries damage),
	# no boxed panels — bare typewriter-style numbers floating over the game
	var bars := get_node_or_null("BottomLeft/Bars") as Control
	if bars != null:
		bars.visible = false
	points_label.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	points_label.add_theme_font_size_override("font_size", 30)
	points_label.add_theme_color_override("font_color", Color(0.98, 0.95, 0.86))
	var ammo_card := get_node_or_null("BottomRight/AmmoCard") as PanelContainer
	if ammo_card != null:
		ammo_card.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	ammo_label.add_theme_font_size_override("font_size", 34)
	weapon_name_label.add_theme_font_size_override("font_size", 15)
	weapon_name_label.modulate = Color(0.85, 0.82, 0.72, 0.85)
	secondary_label.add_theme_font_size_override("font_size", 13)
	var tw := load("res://assets/fonts/SpecialElite.ttf") as Font
	if tw:
		for lb in [points_label, ammo_label, weapon_name_label, secondary_label, grenade_count_label]:
			if lb:
				lb.add_theme_font_override("font", tw)
	if tw:
		prompt_label.add_theme_font_override("font", tw)
	prompt_label.add_theme_font_size_override("font_size", 27)
	prompt_label.add_theme_constant_override("outline_size", 6)
	prompt_panel.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	grenade_count_label.add_theme_font_size_override("font_size", 20)


func _ready() -> void:
	add_to_group("hud")
	_add_film_grade()
	_apply_cod_style()
	blood_vignette.modulate.a = 0.0
	nuke_flash.modulate.a = 0.0
	hitmarker.visible = false
	hitmarker.pivot_offset = Vector2(24.0, 24.0)
	prompt_panel.visible = false
	banner_label.visible = false
	revive_panel.visible = false
	reload_hint.visible = false
	pap_badge.visible = false

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
	_on_perks_changed(GameManager.perks)


func _add_film_grade() -> void:
	var rect := ColorRect.new()
	rect.name = "FilmGrade"
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://assets/shaders/film_grade.gdshader") as Shader
	rect.material = sm
	add_child(rect)
	move_child(rect, 0)


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

	if reload_hint.visible:
		reload_hint.modulate.a = 0.55 + 0.45 * sin(_pulse_t * 8.0)

	var target_blood := clampf((1.0 - _hp_ratio) * 1.15, 0.0, 0.92)
	if _hp_ratio < 0.45:
		target_blood = clampf(target_blood + 0.14 * (0.5 + 0.5 * sin(_pulse_t * 7.5)), 0.0, 0.95)
	var dt := maxf(delta, 0.0)
	var cur_blood := blood_vignette.modulate.a
	if absf(cur_blood - target_blood) > 0.002 or _last_blood_a < 0.0:
		var blood_alpha := clampf(1.0 - exp(-8.0 * dt), 0.0, 1.0)
		var next_blood := lerpf(cur_blood, target_blood, blood_alpha)
		if absf(next_blood - target_blood) <= 0.002:
			next_blood = target_blood
		if absf(next_blood - _last_blood_a) > 0.001:
			_last_blood_a = next_blood
			blood_vignette.modulate.a = next_blood

	# Smooth reactive crosshair tick spacing & ADS fade
	var ch_lerp := clampf(1.0 - exp(-18.0 * dt), 0.0, 1.0)
	if absf(_cur_spread_px - _target_spread_px) > 0.02 or _last_gap < 0.0:
		_cur_spread_px = lerpf(_cur_spread_px, _target_spread_px, ch_lerp)
		if absf(_cur_spread_px - _target_spread_px) <= 0.02:
			_cur_spread_px = _target_spread_px
		var gap := clampf(_cur_spread_px, 4.0, 56.0)
		if absf(gap - _last_gap) > 0.02:
			_last_gap = gap
			var tick_len := 8.0
			top_tick.offset_top = 20.0 - gap - tick_len
			top_tick.offset_bottom = 20.0 - gap
			bot_tick.offset_top = 20.0 + gap
			bot_tick.offset_bottom = 20.0 + gap + tick_len
			left_tick.offset_left = 20.0 - gap - tick_len
			left_tick.offset_right = 20.0 - gap
			right_tick.offset_left = 20.0 + gap
			right_tick.offset_right = 20.0 + gap + tick_len

	var ch_alpha := 0.0 if _hide_crosshair else 1.0
	var cur_ch_a := crosshair.modulate.a
	if absf(cur_ch_a - ch_alpha) > 0.002 or _last_ch_a < 0.0:
		var next_ch_a := lerpf(cur_ch_a, ch_alpha, ch_lerp)
		if absf(next_ch_a - ch_alpha) <= 0.002:
			next_ch_a = ch_alpha
		if absf(next_ch_a - _last_ch_a) > 0.001:
			_last_ch_a = next_ch_a
			crosshair.modulate.a = next_ch_a


func set_crosshair_spread(spread_px: float, hide_crosshair: bool) -> void:
	_target_spread_px = spread_px
	_hide_crosshair = hide_crosshair


func on_player_damaged(amount: float, source_pos: Vector3, player_pos: Vector3, player_basis: Basis) -> void:
	if damage_arc:
		damage_arc.add_damage(source_pos, player_pos, player_basis, amount)


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
	if chalk_counter:
		chalk_counter.set_round(new_round, is_dog)
	var is_transition := _last_round_seen != -1 and new_round != _last_round_seen
	_last_round_seen = new_round
	if is_dog:
		_on_powerup_banner("FETCH ME THEIR SOULS! (HELLHOUND ROUND)", Color(1.0, 0.45, 0.12))
	elif new_round > 1 and is_transition:
		_on_powerup_banner("ROUND %d" % new_round, Color(0.95, 0.25, 0.22))


func _on_points_changed(new_pts: int, delta_pts: int, _reason: String) -> void:
	points_label.text = "%d" % new_pts
	if delta_pts == 0:
		return
	var lbl := Label.new()
	lbl.text = ("+%d" % delta_pts) if delta_pts > 0 else str(delta_pts)
	lbl.add_theme_font_size_override("font_size", 21)
	lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	lbl.add_theme_constant_override("outline_size", 4)
	lbl.modulate = Color(1.0, 0.88, 0.30) if delta_pts > 0 else Color(1.0, 0.35, 0.35)
	delta_box.add_child(lbl)
	if delta_box.get_child_count() > 5:
		var old := delta_box.get_child(0)
		delta_box.remove_child(old)
		old.queue_free()
	var tw := lbl.create_tween()
	tw.tween_property(lbl, "modulate:a", 0.0, 0.95)
	tw.tween_callback(lbl.queue_free)


func _resolve_perk_icon(pid: String) -> String:
	var info: Dictionary = GameManager.PERK_INFO.get(pid, {})
	var ipath := str(info.get("icon", ""))
	if ipath != "" and ResourceLoader.exists(ipath):
		return ipath
	var alt_hud := "res://assets/textures/ui/hud_perk_%s.png" % pid
	if ResourceLoader.exists(alt_hud):
		return alt_hud
	var alt_base := "res://assets/textures/ui/perk_%s.png" % pid
	if ResourceLoader.exists(alt_base):
		return alt_base
	return ""


func _on_perks_changed(perks: Array[String]) -> void:
	for c in perks_box.get_children():
		perks_box.remove_child(c)
		c.queue_free()
	for pid in perks:
		var ipath := _resolve_perk_icon(pid)
		if ipath != "":
			var tr := TextureRect.new()
			tr.name = "PerkIcon_" + pid
			tr.texture = load(ipath)
			tr.custom_minimum_size = Vector2(38, 38)
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			perks_box.add_child(tr)
		else:
			# Clean fallback badge if no PNG icon exists
			var p := PanelContainer.new()
			p.name = "PerkIcon_" + pid
			p.custom_minimum_size = Vector2(38, 38)
			var sb := StyleBoxFlat.new()
			sb.bg_color = FALLBACK_PERK_COLORS.get(pid, Color(0.5, 0.5, 0.5))
			sb.set_corner_radius_all(6)
			sb.set_border_width_all(2)
			sb.border_color = Color(0.96, 0.94, 0.88)
			p.add_theme_stylebox_override("panel", sb)
			var lbl := Label.new()
			lbl.text = pid.left(2).to_upper()
			lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			lbl.add_theme_font_size_override("font_size", 14)
			p.add_child(lbl)
			perks_box.add_child(p)


func _on_powerup_updated(timers: Dictionary) -> void:
	for c in timers_box.get_children():
		timers_box.remove_child(c)
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
			lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
			lbl.add_theme_constant_override("outline_size", 4)
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
	var is_wonder := wname.contains("Wunderwaffe") or wname.contains("Ray Gun")
	pap_badge.visible = packed
	weapon_name_label.text = wname
	if packed:
		weapon_name_label.modulate = Color(0.32, 0.96, 1.0)
	elif is_wonder:
		weapon_name_label.modulate = Color(0.55, 0.95, 1.0)
	else:
		weapon_name_label.modulate = Color(0.95, 0.92, 0.84)

	ammo_label.text = "%d | %d" % [mag, reserve]
	if mag == 0 and reserve == 0:
		ammo_label.modulate = Color(1.0, 0.24, 0.22)
		reload_hint.text = "NO AMMO"
		reload_hint.visible = true
	elif mag <= 2:
		ammo_label.modulate = Color(1.0, 0.34, 0.26)
		reload_hint.text = "[R] RELOAD"
		reload_hint.visible = reserve > 0
	else:
		ammo_label.modulate = Color(0.98, 0.97, 0.92)
		reload_hint.visible = false

	grenade_count_label.text = "x%d" % grenades
	secondary_label.text = ("ALT [Q]: " + sec) if sec != "" else ""


func _on_prompt_changed(text: String) -> void:
	prompt_panel.visible = text != ""
	prompt_label.text = text


func _on_hitmarker(is_kill: bool, is_headshot: bool) -> void:
	hitmarker.visible = true
	hitmarker.scale = Vector2(1.36, 1.36)
	create_tween().tween_property(hitmarker, "scale", Vector2.ONE, 0.10)
	_hitmarker_timer = 0.14
	if is_headshot:
		hitmarker.modulate = Color(1.0, 0.22, 0.22)
	elif is_kill:
		hitmarker.modulate = Color(1.0, 0.55, 0.2)
	else:
		hitmarker.modulate = Color(1.0, 1.0, 1.0)

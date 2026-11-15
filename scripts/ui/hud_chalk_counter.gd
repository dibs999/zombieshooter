extends Control
class_name HudChalkCounter

var round_num: int = 1
var flash_amount: float = 0.0
var _initial_set: bool = false

const CHALK_RED := Color(0.86, 0.13, 0.11, 0.96)
const CHALK_FLASH := Color(1.0, 0.88, 0.48, 1.0)
const CHALK_SHADOW := Color(0.04, 0.01, 0.01, 0.88)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	pivot_offset = Vector2(56.0, 38.0)


func set_round(r: int, is_dog: bool = false) -> void:
	var changed := _initial_set and r != round_num
	round_num = maxi(1, r)
	_initial_set = true
	if changed or r > 1:
		flash_amount = 1.0
		var tw := create_tween()
		tw.set_parallel(true)
		tw.tween_property(self, "flash_amount", 0.0, 1.8)
		scale = Vector2(1.18, 1.18)
		tw.tween_property(self, "scale", Vector2.ONE, 0.42).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		if changed and not is_dog:
			AudioManager.play_2d("round_chalk", 0.04, -3.5)
	queue_redraw()


func _process(_delta: float) -> void:
	if flash_amount > 0.005:
		queue_redraw()


func _draw() -> void:
	var col := CHALK_RED.lerp(CHALK_FLASH, flash_amount)
	if round_num <= 10:
		var groups := (round_num - 1) / 5
		var cur_x := 14.0
		for g in range(groups + 1):
			var count := mini(5, round_num - g * 5)
			if count <= 0:
				continue
			_draw_tally_group(Vector2(cur_x, 12.0), count, col)
			cur_x += 92.0
	else:
		var font := ThemeDB.fallback_font
		var txt := str(round_num)
		var fsize := 56
		var pos := Vector2(12.0, 56.0)
		for dx in [-3.0, 3.0, 0.0]:
			for dy in [-3.0, 3.0, 0.0]:
				if dx == 0.0 and dy == 0.0:
					continue
				draw_string(font, pos + Vector2(dx, dy), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, CHALK_SHADOW)
		draw_string(font, pos, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, col)
		# Chalk scratch underline beneath double-digit stencil
		var w := maxf(54.0, font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize).x)
		_draw_chalk_stroke(Vector2(10.0, 64.0), Vector2(14.0 + w, 61.0), col, 4.0)
		_draw_chalk_stroke(Vector2(16.0, 70.0), Vector2(10.0 + w * 0.72, 68.0), col * Color(1, 1, 1, 0.7), 2.5)


func _draw_tally_group(origin: Vector2, count: int, col: Color) -> void:
	var vertical_count := mini(4, count)
	var tilts := [-2.5, 1.8, -1.2, 2.8]
	var tops := [-2.0, 1.5, -1.0, 2.0]
	for i in range(vertical_count):
		var x := origin.x + float(i) * 16.0
		var p0 := Vector2(x + tilts[i], origin.y + tops[i])
		var p1 := Vector2(x - tilts[i] * 0.7, origin.y + 48.0 + tops[(i + 1) % 4])
		_draw_chalk_stroke(p0, p1, col, 6.0)

	if count == 5:
		var s0 := Vector2(origin.x - 8.0, origin.y + 44.0)
		var s1 := Vector2(origin.x + 58.0, origin.y + 6.0)
		_draw_chalk_stroke(s0, s1, col, 6.5)


func _draw_chalk_stroke(a: Vector2, b: Vector2, col: Color, width: float) -> void:
	draw_line(a + Vector2(2.0, 2.5), b + Vector2(2.0, 2.5), CHALK_SHADOW, width + 3.5, true)
	draw_line(a, b, col, width, true)
	var inner := col.lightened(0.28)
	inner.a = col.a * 0.65
	draw_line(a + Vector2(-0.8, 0.6), b + Vector2(0.8, -0.6), inner, maxf(1.5, width * 0.38), true)
	draw_circle(a, width * 0.42, col)
	draw_circle(b, width * 0.36, col)

extends Control
class_name HudDamageArc

const TEX_ARC: Texture2D = preload("res://assets/textures/ui/hud_dmg_arc.png")
const ARC_DURATION := 1.15

var _pings: Array[Dictionary] = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func add_damage(source_pos: Vector3, player_pos: Vector3, player_basis: Basis, amount: float = 30.0) -> void:
	var to_src := source_pos - player_pos
	to_src.y = 0.0
	if to_src.length_squared() < 0.001:
		return
	to_src = to_src.normalized()
	var fwd := -player_basis.z
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length_squared() > 0.001 else Vector3.FORWARD
	var right := player_basis.x
	right.y = 0.0
	right = right.normalized() if right.length_squared() > 0.001 else Vector3.RIGHT

	var ang := atan2(to_src.dot(right), to_src.dot(fwd))
	_pings.append({
		"angle": ang,
		"age": 0.0,
		"duration": ARC_DURATION,
		"strength": clampf(amount / 45.0, 0.65, 1.0),
	})
	if _pings.size() > 6:
		_pings.pop_front()
	queue_redraw()


func _process(delta: float) -> void:
	if _pings.is_empty():
		return
	for i in range(_pings.size() - 1, -1, -1):
		_pings[i]["age"] = float(_pings[i]["age"]) + delta
		if float(_pings[i]["age"]) >= float(_pings[i]["duration"]):
			_pings.remove_at(i)
	queue_redraw()


func _draw() -> void:
	if _pings.is_empty():
		return
	var sz := size
	if sz.x < 10.0 or sz.y < 10.0:
		sz = Vector2(1280.0, 720.0)
	var center := sz * 0.5
	var arc_size := clampf(minf(sz.x, sz.y) * 0.58, 300.0, 520.0)
	var half := arc_size * 0.5
	for p in _pings:
		var t := clampf(float(p["age"]) / float(p["duration"]), 0.0, 1.0)
		var alpha := (1.0 - t * t) * float(p["strength"]) * 0.92
		if alpha <= 0.01:
			continue
		draw_set_transform(center, float(p["angle"]), Vector2.ONE)
		draw_texture_rect(TEX_ARC, Rect2(-half, -half, arc_size, arc_size), false, Color(1.0, 0.22, 0.18, alpha))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

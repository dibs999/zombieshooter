class_name CodUiStyle
extends RefCounted

# Shared WaW/BO1 zombies UI treatment: distressed stencil titles,
# typewriter body text, flat bone-white buttons with amber hover.

const BONE := Color(0.93, 0.90, 0.82)
const DIM := Color(0.66, 0.62, 0.54)
const AMBER := Color(1.0, 0.72, 0.32)
const BLOOD := Color(0.72, 0.16, 0.12)


static func stencil_font() -> Font:
	return load("res://assets/fonts/BlackOpsOne.ttf") as Font


static func typewriter_font() -> Font:
	return load("res://assets/fonts/SpecialElite.ttf") as Font


static func style_buttons(root: Control) -> void:
	var typewriter := typewriter_font()
	var empty := StyleBoxEmpty.new()
	var hover_box := StyleBoxFlat.new()
	hover_box.bg_color = Color(0.55, 0.42, 0.16, 0.22)
	hover_box.border_width_left = 3
	hover_box.border_color = AMBER
	hover_box.content_margin_left = 8.0
	for node in root.find_children("", "Button", true, false):
		var btn := node as Button
		if btn == null:
			continue
		for state in ["normal", "pressed", "disabled", "focus"]:
			btn.add_theme_stylebox_override(state, empty)
		btn.add_theme_stylebox_override("hover", hover_box)
		if typewriter:
			btn.add_theme_font_override("font", typewriter)
		btn.add_theme_color_override("font_color", BONE)
		btn.add_theme_color_override("font_hover_color", AMBER)
		btn.add_theme_color_override("font_pressed_color", BLOOD)
		btn.add_theme_color_override("font_focus_color", BONE)
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT


static func style_labels(root: Control, skip: Array = []) -> void:
	var typewriter := typewriter_font()
	for node in root.find_children("", "Label", true, false):
		var lb := node as Label
		if lb == null or lb in skip:
			continue
		if typewriter:
			lb.add_theme_font_override("font", typewriter)
		if not lb.has_theme_color_override("font_color"):
			lb.add_theme_color_override("font_color", DIM)


static func style_title(lb: Label, size: int = 48, color: Color = BONE) -> void:
	var stencil := stencil_font()
	if lb == null or stencil == null:
		return
	lb.add_theme_font_override("font", stencil)
	lb.add_theme_font_size_override("font_size", size)
	lb.add_theme_color_override("font_color", color)
	lb.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	lb.add_theme_constant_override("outline_size", 9)


static func dark_panel(panel: PanelContainer, alpha: float = 0.42) -> void:
	if panel == null:
		return
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.0, 0.0, 0.0, alpha)
	bg.corner_radius_top_left = 2
	bg.corner_radius_top_right = 2
	bg.corner_radius_bottom_right = 2
	bg.corner_radius_bottom_left = 2
	bg.content_margin_left = 30.0
	bg.content_margin_top = 22.0
	bg.content_margin_right = 30.0
	bg.content_margin_bottom = 22.0
	panel.add_theme_stylebox_override("panel", bg)

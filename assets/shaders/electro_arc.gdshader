shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

uniform vec4 arc_color : source_color = vec4(0.35, 0.85, 1.0, 0.85);

void fragment() {
	float wave1 = sin(UV.y * 28.0 - TIME * 24.0 + sin(UV.x * 16.0 + TIME * 12.0) * 2.5);
	float wave2 = sin(UV.y * 42.0 + TIME * 19.0 - cos(UV.x * 22.0) * 3.0);
	float bolt = smoothstep(0.86, 0.99, abs(wave1 * 0.55 + wave2 * 0.45));
	float edge_fade = sin(UV.x * 3.14159);
	ALBEDO = arc_color.rgb * (1.2 + bolt * 2.5);
	ALPHA = (0.12 + bolt * 0.85) * edge_fade * arc_color.a;
}

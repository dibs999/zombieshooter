shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

uniform vec4 shaft_color : source_color = vec4(0.55, 0.72, 0.95, 0.10);

void fragment() {
	float v_fade = (1.0 - UV.y) * smoothstep(0.0, 0.15, UV.y);
	float dust = 0.85 + 0.15 * sin(UV.y * 12.0 - TIME * 0.6 + UV.x * 6.283);
	float fres = pow(abs(dot(NORMAL, VIEW)), 1.6);
	ALBEDO = shaft_color.rgb;
	ALPHA = shaft_color.a * v_fade * dust * fres;
}

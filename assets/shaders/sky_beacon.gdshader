shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

uniform vec4 beam_color : source_color = vec4(0.20, 0.85, 1.0, 0.45);
uniform float pulse_speed = 2.4;

void fragment() {
	float v_fade = smoothstep(0.0, 0.12, UV.y) * (1.0 - smoothstep(0.25, 1.0, UV.y));
	float swirl = 0.75 + 0.25 * sin(UV.x * 18.8495 + TIME * pulse_speed + UV.y * 8.0);
	float rim = pow(abs(dot(NORMAL, VIEW)), 1.5);
	ALBEDO = beam_color.rgb;
	ALPHA = beam_color.a * v_fade * swirl * rim;
}

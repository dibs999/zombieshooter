shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

uniform vec4 beam_color : source_color = vec4(0.22, 0.88, 1.0, 0.48);
uniform float pulse_speed = 2.4;

void fragment() {
	float v_fade = smoothstep(0.0, 0.08, UV.y) * (1.0 - smoothstep(0.28, 1.0, UV.y));
	float swirl = 0.74 + 0.26 * sin(UV.x * 18.8495 + TIME * pulse_speed + UV.y * 9.0);
	float core = 0.85 + 0.15 * cos(TIME * (pulse_speed * 1.7) - UV.y * 14.0);
	vec3 n = length(NORMAL) > 1e-5 ? normalize(NORMAL) : vec3(0.0, 1.0, 0.0);
	vec3 v = length(VIEW) > 1e-5 ? normalize(VIEW) : vec3(0.0, 0.0, 1.0);
	float ndv = clamp(abs(dot(n, v)), 0.0001, 1.0);
	float rim = pow(ndv, 1.55);
	ALBEDO = beam_color.rgb * core;
	ALPHA = clamp(beam_color.a * v_fade * swirl * rim, 0.0, 1.0);
}

shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

uniform vec4 shaft_color : source_color = vec4(0.58, 0.76, 0.98, 0.09);

void fragment() {
	float v_inv = clamp(1.0 - UV.y, 0.0001, 1.0);
	float v_fade = pow(v_inv, 1.35) * smoothstep(0.0, 0.18, clamp(UV.y, 0.0, 1.0)) * smoothstep(1.0, 0.96, UV.y);
	float streak1 = 0.80 + 0.20 * sin(UV.x * 18.8495 + TIME * 0.35 + UV.y * 4.0);
	float streak2 = 0.88 + 0.12 * cos(UV.x * 31.4159 - TIME * 0.22 + UV.y * 9.0);
	vec3 n = length(NORMAL) > 1e-5 ? normalize(NORMAL) : vec3(0.0, 1.0, 0.0);
	vec3 v = length(VIEW) > 1e-5 ? normalize(VIEW) : vec3(0.0, 0.0, 1.0);
	float ndv = clamp(abs(dot(n, v)), 0.0001, 1.0);
	float fres = pow(ndv, 1.75);
	ALBEDO = shaft_color.rgb;
	ALPHA = clamp(shaft_color.a * v_fade * streak1 * streak2 * fres, 0.0, 1.0);
}

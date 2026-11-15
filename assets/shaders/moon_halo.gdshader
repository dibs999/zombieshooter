shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_front, fog_disabled;

uniform vec3 halo_color : source_color = vec3(0.40, 0.64, 1.0);
uniform float intensity : hint_range(0.0, 2.0) = 0.68;
uniform float power_falloff : hint_range(1.0, 8.0) = 3.2;

void fragment() {
	vec3 n = length(NORMAL) > 1e-5 ? normalize(NORMAL) : vec3(0.0, 1.0, 0.0);
	vec3 v = length(VIEW) > 1e-5 ? normalize(VIEW) : vec3(0.0, 0.0, 1.0);
	float ndv = clamp(abs(dot(n, v)), 0.0001, 1.0);
	float inner = pow(ndv, power_falloff) * intensity;
	float outer = pow(ndv, 1.45) * intensity * 0.22;
	float glow = inner + outer;
	ALBEDO = halo_color * glow;
	ALPHA = clamp(glow, 0.0, 1.0);
}

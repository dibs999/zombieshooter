shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_front, fog_disabled;

uniform vec3 halo_color : source_color = vec3(0.35, 0.60, 1.0);
uniform float intensity : hint_range(0.0, 2.0) = 0.55;
uniform float power_falloff : hint_range(1.0, 8.0) = 3.8;

void fragment() {
	float ndv = clamp(abs(dot(normalize(NORMAL), normalize(VIEW))), 0.0, 1.0);
	float glow = pow(ndv, power_falloff) * intensity;
	ALBEDO = halo_color * glow;
	ALPHA = glow;
}

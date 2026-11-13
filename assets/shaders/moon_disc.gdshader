shader_type spatial;
render_mode unshaded, fog_disabled;

uniform vec3 moon_color : source_color = vec3(0.95, 0.97, 1.0);
uniform vec3 mare_color : source_color = vec3(0.72, 0.79, 0.88);
uniform float emission_boost : hint_range(0.5, 3.0) = 1.15;

void fragment() {
	float ndv = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);
	float limb = smoothstep(0.05, 0.55, ndv);
	// Subtle organic lunar mare dark patches across the facing hemisphere
	vec3 p = normalize(NORMAL);
	float mare = sin(p.x * 4.5 + p.y * 2.2) * cos(p.y * 3.8 - p.z * 2.6);
	float patch_mix = smoothstep(-0.15, 0.45, mare) * 0.55;
	vec3 col = mix(moon_color, mare_color, patch_mix) * mix(0.68, 1.0, limb);
	ALBEDO = col;
	EMISSION = col * emission_boost;
}

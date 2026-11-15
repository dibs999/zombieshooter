shader_type spatial;
render_mode unshaded, fog_disabled;

uniform vec3 moon_color : source_color = vec3(0.96, 0.98, 1.0);
uniform vec3 mare_color : source_color = vec3(0.60, 0.68, 0.78);
uniform vec3 crater_rim_color : source_color = vec3(0.99, 0.99, 1.0);
uniform float emission_boost : hint_range(0.5, 4.0) = 1.65;

float hash31(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

float noise3(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	float n000 = hash31(i + vec3(0.0, 0.0, 0.0));
	float n100 = hash31(i + vec3(1.0, 0.0, 0.0));
	float n010 = hash31(i + vec3(0.0, 1.0, 0.0));
	float n110 = hash31(i + vec3(1.0, 1.0, 0.0));
	float n001 = hash31(i + vec3(0.0, 0.0, 1.0));
	float n101 = hash31(i + vec3(1.0, 0.0, 1.0));
	float n011 = hash31(i + vec3(0.0, 1.0, 1.0));
	float n111 = hash31(i + vec3(1.0, 1.0, 1.0));
	return mix(
		mix(mix(n000, n100, f.x), mix(n010, n110, f.x), f.y),
		mix(mix(n001, n101, f.x), mix(n011, n111, f.x), f.y),
		f.z
	);
}

void fragment() {
	vec3 n = normalize(NORMAL);
	vec3 v = normalize(VIEW);
	float ndv = clamp(dot(n, v), 0.0, 1.0);
	float limb = smoothstep(0.04, 0.62, ndv);

	// Multi-octave lunar maria & crater ridges
	float mare = noise3(n * 3.4) * 0.6 + noise3(n * 7.8) * 0.4;
	float ridge = noise3(n * 18.0 + vec3(4.2, -1.7, 2.3));
	float patch_mix = smoothstep(0.32, 0.72, mare) * 0.78;
	float crater = smoothstep(0.66, 0.85, ridge) * 0.25;

	vec3 col = mix(moon_color, mare_color, patch_mix);
	col = mix(col, crater_rim_color, crater);
	col *= mix(0.62, 1.05, limb);
	ALBEDO = col;
	EMISSION = col * emission_boost;
}

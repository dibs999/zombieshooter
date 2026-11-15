shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

uniform vec4 core_color : source_color = vec4(1.0, 0.88, 0.36, 1.0);
uniform vec4 outer_color : source_color = vec4(1.0, 0.30, 0.05, 0.92);

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float noise2d(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void fragment() {
	float h = clamp(1.0 - UV.y, 0.0, 1.0);
	float edge_x = smoothstep(0.0, 0.14, UV.x) * smoothstep(1.0, 0.86, UV.x);
	float base_fade = smoothstep(0.0, 0.08, h);

	float t = TIME * 4.8;
	float n1 = noise2d(vec2(UV.x * 18.0, h * 5.2 - t));
	float n2 = noise2d(vec2(UV.x * 34.0 + 3.1, h * 9.5 - t * 1.45));
	float wave = n1 * 0.62 + n2 * 0.38;

	float jets = 0.72 + 0.28 * sin(UV.x * 25.1327);
	float tongue = smoothstep(h * 0.88 + 0.06, h * 0.88 + 0.58, wave * 0.92 + (1.0 - h) * 0.55) * jets;
	float core = smoothstep(0.45, 0.92, tongue * (1.0 - h * 0.68));

	vec3 col = mix(outer_color.rgb * 1.5, core_color.rgb * 2.4, core);
	float h_pow = pow(max(0.0001, h), 2.2);
	float alpha = clamp(tongue * edge_x * base_fade * (1.0 - h_pow) * outer_color.a, 0.0, 1.0);

	ALBEDO = col;
	ALPHA = alpha;
}

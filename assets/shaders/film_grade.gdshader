shader_type canvas_item;

// Cinematic CoD-Zombies grade: soft vignette, animated film grain,
// slight cool-green desaturation — subtle enough to leave gameplay readable.

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.46;
uniform float vignette_softness : hint_range(0.1, 1.0) = 0.62;
uniform float grain_strength : hint_range(0.0, 0.25) = 0.055;
uniform float desat_amount : hint_range(0.0, 0.6) = 0.10;
uniform vec3 tint_color : source_color = vec3(0.93, 1.02, 0.97);
uniform float tint_amount : hint_range(0.0, 0.5) = 0.10;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

void fragment() {
	vec3 col = texture(screen_tex, SCREEN_UV).rgb;

	// Cool desaturated military-facility tone
	float luma = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(col, vec3(luma), desat_amount);
	col = mix(col, col * tint_color, tint_amount);

	// Soft edge falloff
	vec2 d = SCREEN_UV - vec2(0.5);
	float vig = smoothstep(0.9, 0.9 - vignette_softness * 0.55, length(d) * (1.0 + vignette_strength));
	col *= mix(1.0, vig, vignette_strength);

	// Animated 35mm grain
	float g = hash12(SCREEN_UV * vec2(1920.0, 1080.0) + vec2(TIME * 61.7, TIME * 83.3)) - 0.5;
	col += g * grain_strength * (1.0 - luma * 0.55);

	COLOR.rgb = col;
	COLOR.a = 1.0;
}

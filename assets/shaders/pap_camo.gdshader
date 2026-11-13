shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color;
uniform sampler2D emission_tex : source_color;
uniform float scroll_speed = 0.08;
uniform float uv_scale = 0.45;
uniform float emission_boost = 1.85;

void fragment() {
	vec2 base_uv = UV * uv_scale;
	vec3 base = texture(albedo_tex, base_uv).rgb;
	vec3 glow = texture(emission_tex, base_uv).rgb;
	float pulse = 0.80 + 0.25 * sin(TIME * 3.2 + base_uv.x * 4.0 + base_uv.y * 3.0);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.4);
	ALBEDO = mix(vec3(0.56, 0.60, 0.66), base, 0.78);
	METALLIC = 0.92;
	ROUGHNESS = 0.20;
	EMISSION = glow * (emission_boost * pulse) + vec3(0.06, 0.68, 0.96) * fres * 0.24;
}

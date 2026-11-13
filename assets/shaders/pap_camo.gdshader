shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color;
uniform sampler2D emission_tex : source_color;
uniform float scroll_speed = 0.22;
uniform float uv_scale = 3.5;
uniform float emission_boost = 3.2;

void fragment() {
	vec2 uv = UV * uv_scale + vec2(TIME * scroll_speed, TIME * scroll_speed * 0.65);
	vec3 base = texture(albedo_tex, uv).rgb;
	vec3 glow = texture(emission_tex, uv).rgb;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.5);
	ALBEDO = mix(vec3(0.45, 0.50, 0.58), base, 0.72);
	METALLIC = 0.92;
	ROUGHNESS = 0.16;
	EMISSION = glow * emission_boost + vec3(0.08, 0.75, 1.0) * fres * 1.4;
}

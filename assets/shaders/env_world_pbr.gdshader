shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 albedo_tint : source_color = vec4(1.0);
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D roughness_tex : hint_default_white, filter_linear_mipmap, repeat_enable;

uniform bool use_alt_layer = false;
uniform sampler2D alt_albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D alt_normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D alt_roughness_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 alt_tint : source_color = vec4(1.0);
uniform float alt_blend_amount : hint_range(0.0, 1.0) = 0.0;
uniform float alt_noise_scale : hint_range(0.01, 1.0) = 0.14;

uniform float uv_scale : hint_range(0.05, 4.0) = 0.35;
uniform float normal_strength : hint_range(0.0, 2.0) = 0.85;
uniform float roughness_scale : hint_range(0.1, 1.5) = 1.0;
uniform float metallic_val : hint_range(0.0, 1.0) = 0.0;
uniform float specular_val : hint_range(0.0, 1.0) = 0.45;

// Anti-tiling world-space macro variation
uniform float macro_variation : hint_range(0.0, 0.5) = 0.22;
uniform float macro_scale : hint_range(0.01, 0.5) = 0.09;
uniform vec3 grime_tint : source_color = vec3(0.12, 0.13, 0.12);

// Floor wetness / puddles & Wall-base damp/soot
uniform bool is_floor = false;
uniform float puddle_amount : hint_range(0.0, 1.0) = 0.0;
uniform float puddle_scale : hint_range(0.02, 0.5) = 0.12;
uniform float wall_damp_height : hint_range(0.0, 3.0) = 1.15;
uniform float wall_damp_strength : hint_range(0.0, 1.0) = 0.48;
uniform float wall_top_grime_y : hint_range(1.0, 12.0) = 4.6;

varying vec3 v_world_pos;
varying vec3 v_world_nrm;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise2(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm2(vec2 p) {
	float v = 0.0;
	float amp = 0.62;
	mat2 rot = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8));
	for (int i = 0; i < 2; i++) {
		v += amp * vnoise2(p);
		p = rot * p * 2.07 + vec2(17.1, 31.7);
		amp *= 0.613;
	}
	return clamp(v, 0.0, 1.0);
}

void compute_planar_axis(vec3 wp, vec3 wn, vec3 dpdx, vec3 dpdy, float scale, out int axis, out vec2 uv, out vec2 duvx, out vec2 duvy, out float axis_sign) {
	vec3 an = abs(wn);
	if (an.y >= an.x && an.y >= an.z) {
		axis = 1;
		uv = vec2(wp.x, -wp.z) * scale;
		duvx = vec2(dpdx.x, -dpdx.z) * scale;
		duvy = vec2(dpdy.x, -dpdy.z) * scale;
		axis_sign = (wn.y >= 0.0) ? 1.0 : -1.0;
	} else if (an.x >= an.z) {
		axis = 0;
		uv = vec2(wp.z, -wp.y) * scale;
		duvx = vec2(dpdx.z, -dpdx.y) * scale;
		duvy = vec2(dpdy.z, -dpdy.y) * scale;
		axis_sign = (wn.x >= 0.0) ? 1.0 : -1.0;
	} else {
		axis = 2;
		uv = vec2(wp.x, -wp.y) * scale;
		duvx = vec2(dpdx.x, -dpdx.y) * scale;
		duvy = vec2(dpdy.x, -dpdy.y) * scale;
		axis_sign = (wn.z >= 0.0) ? 1.0 : -1.0;
	}
}

vec3 decode_planar_normal(vec3 sample_rgb, vec3 wn, int axis, float axis_sign, float strength) {
	vec2 t = (sample_rgb.xy * 2.0 - 1.0) * strength;
	t.x *= axis_sign;
	if (axis == 1) {
		return normalize(vec3(t.x + wn.x, wn.y, t.y + wn.z));
	} else if (axis == 0) {
		return normalize(vec3(wn.x, t.y + wn.y, t.x + wn.z));
	}
	return normalize(vec3(t.x + wn.x, t.y + wn.y, wn.z));
}

void vertex() {
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 wn = normalize(v_world_nrm);
	vec3 dpdx = dFdx(v_world_pos);
	vec3 dpdy = dFdy(v_world_pos);

	int p_axis;
	vec2 p_uv;
	vec2 p_duvx;
	vec2 p_duvy;
	float p_sign;
	compute_planar_axis(v_world_pos, wn, dpdx, dpdy, uv_scale, p_axis, p_uv, p_duvx, p_duvy, p_sign);

	vec3 alb = textureGrad(albedo_tex, p_uv, p_duvx, p_duvy).rgb * albedo_tint.rgb;
	float rgh = textureGrad(roughness_tex, p_uv, p_duvx, p_duvy).r * roughness_scale;
	vec3 world_n = decode_planar_normal(textureGrad(normal_tex, p_uv, p_duvx, p_duvy).rgb, wn, p_axis, p_sign, normal_strength);

	if (use_alt_layer && alt_blend_amount > 0.001) {
		float n_alt = fbm2(v_world_pos.xz * alt_noise_scale + vec2(3.7, -8.2));
		float mask = smoothstep(0.55 - alt_blend_amount * 0.45, 0.85 - alt_blend_amount * 0.35, n_alt);
		if (mask > 0.001) {
			vec2 alt_uv = p_uv * 0.95;
			vec2 alt_duvx = p_duvx * 0.95;
			vec2 alt_duvy = p_duvy * 0.95;
			vec3 alb2 = textureGrad(alt_albedo_tex, alt_uv, alt_duvx, alt_duvy).rgb * alt_tint.rgb;
			float rgh2 = textureGrad(alt_roughness_tex, alt_uv, alt_duvx, alt_duvy).r * roughness_scale;
			vec3 world_n2 = decode_planar_normal(textureGrad(alt_normal_tex, alt_uv, alt_duvx, alt_duvy).rgb, wn, p_axis, p_sign, normal_strength);
			alb = mix(alb, alb2, mask);
			rgh = mix(rgh, rgh2, mask);
			world_n = normalize(mix(world_n, world_n2, mask));
		}
	}

	// Macro non-repeating breakup across meters
	float m_noise = fbm2(v_world_pos.xz * macro_scale + v_world_pos.xy * (macro_scale * 0.65));
	float grime_patch = smoothstep(0.35, 0.82, m_noise);
	alb *= mix(1.0 + macro_variation * 0.55, 1.0 - macro_variation * 0.85, grime_patch);
	alb = mix(alb, grime_tint, grime_patch * macro_variation * 0.55);
	rgh = clamp(rgh + (m_noise - 0.5) * 0.16, 0.06, 0.98);

	float spec = specular_val;
	float met = metallic_val;

	if (is_floor && puddle_amount > 0.001 && wn.y > 0.5) {
		float p_noise = fbm2(v_world_pos.xz * puddle_scale + vec2(11.4, -4.9));
		float p_thresh = 0.78 - puddle_amount * 0.36;
		float puddle = smoothstep(p_thresh, p_thresh + 0.08, p_noise);
		if (puddle > 0.001) {
			alb = mix(alb, alb * 0.42 + vec3(0.015, 0.02, 0.025), puddle * 0.72);
			rgh = mix(rgh, 0.07, puddle);
			spec = mix(spec, 0.78, puddle);
			met = mix(met, 0.04, puddle);
			world_n = normalize(mix(world_n, wn, puddle * 0.92));
		}
	} else if (!is_floor && wall_damp_strength > 0.001) {
		// Base damp rising from floor + top cornice leakage streaks (height-gated)
		float wall_coord = v_world_pos.x + v_world_pos.z;
		float base_mask = 0.0;
		if (v_world_pos.y < wall_damp_height * 1.35) {
			float streak = fbm2(vec2(wall_coord * 0.65, v_world_pos.y * 0.25));
			float base_h = wall_damp_height * (0.55 + 0.75 * streak);
			base_mask = clamp(1.0 - v_world_pos.y / max(0.1, base_h), 0.0, 1.0);
		}
		float top_mask = 0.0;
		if (v_world_pos.y > wall_top_grime_y - 1.45) {
			float top_streak = fbm2(vec2(wall_coord * 1.15, v_world_pos.y * 0.12));
			top_mask = smoothstep(wall_top_grime_y - 1.4, wall_top_grime_y, v_world_pos.y) * smoothstep(0.35, 0.78, top_streak);
		}
		// Mid-wall water streaks running down at random columns (derelict bunker seepage)
		float col = fbm2(vec2(wall_coord * 0.9, 3.7));
		float streak_col = smoothstep(0.62, 0.86, col);
		float vert_fade = smoothstep(4.6, 2.6, v_world_pos.y) * smoothstep(0.2, 1.3, v_world_pos.y);
		float drip = fbm2(vec2(wall_coord * 3.4, v_world_pos.y * 0.35)) * 0.5 + 0.5;
		float mid_mask = streak_col * vert_fade * drip * 0.55;
		float damp = clamp(base_mask * 0.85 + top_mask * 0.55 + mid_mask, 0.0, 1.0) * wall_damp_strength;
		if (damp > 0.001) {
			alb = mix(alb, alb * 0.45 + grime_tint * 0.35, damp);
			rgh = mix(rgh, 0.38, base_mask * wall_damp_strength * 0.65);
		}
	}

	ALBEDO = alb;
	ROUGHNESS = clamp(rgh, 0.05, 0.98);
	METALLIC = met;
	SPECULAR = spec;
	NORMAL = normalize((VIEW_MATRIX * vec4(world_n, 0.0)).xyz);
}

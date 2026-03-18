/**
 * WebGPU Particle Engine for cosmological visualization.
 *
 * Renders millions of particles representing dark matter / baryon density
 * using compute shaders for physics + render pipeline for display.
 *
 * Compute shader handles:
 * - Gravitational N-body interaction (simplified)
 * - Hubble expansion
 * - Position/velocity integration
 *
 * Render pipeline:
 * - Point sprites with additive blending
 * - Color by velocity magnitude (cool = slow, hot = fast)
 */

// WGSL compute shader: update particle positions
export const COMPUTE_SHADER = /* wgsl */ `
struct Particle {
  pos: vec4<f32>,   // xyz = position, w = mass
  vel: vec4<f32>,   // xyz = velocity, w = padding
};

struct SimParams {
  dt: f32,
  gravity: f32,
  hubble: f32,
  damping: f32,
  num_particles: u32,
  softening: f32,
  box_size: f32,
  _pad: f32,
};

@group(0) @binding(0) var<storage, read_write> particles: array<Particle>;
@group(0) @binding(1) var<uniform> params: SimParams;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let idx = gid.x;
  if (idx >= params.num_particles) { return; }

  var p = particles[idx];
  var acc = vec3<f32>(0.0, 0.0, 0.0);

  // Simplified gravity: interact with subset (Barnes-Hut approximation)
  let stride = max(params.num_particles / 256u, 1u);
  for (var j = 0u; j < params.num_particles; j += stride) {
    if (j == idx) { continue; }
    let other = particles[j];
    var diff = other.pos.xyz - p.pos.xyz;

    // Periodic boundary conditions
    diff = diff - params.box_size * round(diff / params.box_size);

    let dist2 = dot(diff, diff) + params.softening * params.softening;
    let inv_dist = inverseSqrt(dist2);
    let force = params.gravity * other.pos.w * inv_dist * inv_dist * inv_dist;
    acc += diff * force * f32(stride);
  }

  // Hubble expansion: v += H * r * dt
  acc -= params.hubble * p.pos.xyz;

  // Integrate velocity
  p.vel = vec4<f32>(
    (p.vel.xyz + acc * params.dt) * params.damping,
    0.0
  );

  // Integrate position
  p.pos = vec4<f32>(p.pos.xyz + p.vel.xyz * params.dt, p.pos.w);

  // Periodic wrap
  let half = params.box_size * 0.5;
  p.pos.x = ((p.pos.x + half) % params.box_size + params.box_size) % params.box_size - half;
  p.pos.y = ((p.pos.y + half) % params.box_size + params.box_size) % params.box_size - half;
  p.pos.z = ((p.pos.z + half) % params.box_size + params.box_size) % params.box_size - half;

  particles[idx] = p;
}
`;

// WGSL vertex + fragment shader: render particles as point sprites
export const RENDER_SHADER = /* wgsl */ `
struct Particle {
  pos: vec4<f32>,
  vel: vec4<f32>,
};

struct Uniforms {
  mvp: mat4x4<f32>,
  point_size: f32,
  brightness: f32,
  _pad: vec2<f32>,
};

@group(0) @binding(0) var<storage, read> particles: array<Particle>;
@group(0) @binding(1) var<uniform> uniforms: Uniforms;

struct VertexOutput {
  @builtin(position) position: vec4<f32>,
  @location(0) color: vec4<f32>,
  @builtin(point_size) point_size: f32,
};

@vertex
fn vs_main(@builtin(vertex_index) idx: u32) -> VertexOutput {
  let p = particles[idx];
  var out: VertexOutput;
  out.position = uniforms.mvp * vec4<f32>(p.pos.xyz, 1.0);
  out.point_size = uniforms.point_size;

  // Color by velocity: blue (slow) -> white -> red (fast)
  let speed = length(p.vel.xyz);
  let t = clamp(speed * 5.0, 0.0, 1.0);
  if (t < 0.5) {
    let s = t * 2.0;
    out.color = vec4<f32>(0.2 * s, 0.3 + 0.5 * s, 0.8 + 0.2 * s, uniforms.brightness);
  } else {
    let s = (t - 0.5) * 2.0;
    out.color = vec4<f32>(0.2 + 0.8 * s, 0.8 - 0.4 * s, 1.0 - 0.8 * s, uniforms.brightness);
  }

  return out;
}

@fragment
fn fs_main(@location(0) color: vec4<f32>) -> @location(0) vec4<f32> {
  return color;
}
`;

export interface ParticleEngineConfig {
  numParticles: number;
  boxSize: number;
  gravity: number;
  hubble: number;
  damping: number;
  softening: number;
  dt: number;
  pointSize: number;
  brightness: number;
}

export const DEFAULT_CONFIG: ParticleEngineConfig = {
  numParticles: 4096,
  boxSize: 10.0,
  gravity: 0.001,
  hubble: 0.0,
  damping: 0.999,
  softening: 0.1,
  dt: 0.02,
  pointSize: 2.0,
  brightness: 0.6,
};

/**
 * Initialize particle positions from a density field or random.
 * Returns Float32Array of Particle structs (pos.xyzw, vel.xyzw).
 */
export function initParticles(n: number, boxSize: number): Float32Array {
  const data = new Float32Array(n * 8); // 4 floats pos + 4 floats vel
  for (let i = 0; i < n; i++) {
    const off = i * 8;
    // Positions: uniform random in box
    data[off + 0] = (Math.random() - 0.5) * boxSize;
    data[off + 1] = (Math.random() - 0.5) * boxSize;
    data[off + 2] = (Math.random() - 0.5) * boxSize;
    data[off + 3] = 1.0; // mass

    // Small initial velocity perturbation
    data[off + 4] = (Math.random() - 0.5) * 0.01;
    data[off + 5] = (Math.random() - 0.5) * 0.01;
    data[off + 6] = (Math.random() - 0.5) * 0.01;
    data[off + 7] = 0.0;
  }
  return data;
}

/**
 * Simple perspective MVP matrix for rotating view.
 */
export function createMVP(
  time: number,
  aspect: number,
  distance: number = 15,
): Float32Array {
  const angle = time * 0.2;
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);

  const fov = Math.PI / 4;
  const near = 0.1;
  const far = 100.0;
  const f = 1.0 / Math.tan(fov / 2);

  // View: rotation around Y + translate back
  const view = new Float32Array(16);
  view[0] = cos; view[2] = sin;
  view[5] = 1;
  view[8] = -sin; view[10] = cos;
  view[14] = -distance;
  view[15] = 1;

  // Projection
  const proj = new Float32Array(16);
  proj[0] = f / aspect;
  proj[5] = f;
  proj[10] = (far + near) / (near - far);
  proj[11] = -1;
  proj[14] = (2 * far * near) / (near - far);

  // Multiply proj * view
  const mvp = new Float32Array(16);
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      let sum = 0;
      for (let k = 0; k < 4; k++) {
        sum += proj[r + k * 4] * view[k + c * 4];
      }
      mvp[r + c * 4] = sum;
    }
  }
  return mvp;
}

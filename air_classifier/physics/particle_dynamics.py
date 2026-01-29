"""
Particle Dynamics - FUNDAMENTAL PHYSICS ONLY

Computes forces on particles and updates their motion using ONLY fundamental laws:
1. Newton's second law: F = ma
2. Stokes drag law: F_drag = 6πμr·v_rel (for Re < 1)
3. Schiller-Naumann correlation: Extended drag for higher Re
4. Gravity: F_g = mg

PHILOSOPHY:
===========
This module contains ONLY the physics - the unchanging laws of mechanics.
All material properties (density) and physical constants (air viscosity, gravity)
come from control_parameters.py

FUNDAMENTAL FORCES:
===================
1. DRAG: F = 6πμr·(v_air - v_particle) [Stokes law]
   - THE primary force on microparticles
   - Couples particle motion to air flow
   - Centrifugal effect EMERGES from tangential drag component!

2. GRAVITY: F = m·g
   - Always downward
   - Opposes upward flow
   - Helps large particles settle

NO EXPLICIT CENTRIFUGAL FORCE!
===============================
The centrifugal "force" is NOT added explicitly because:
1. Air swirls tangentially (v_θ from Rankine vortex)
2. Drag accelerates particle tangentially
3. Particle follows curved path → centrifugal acceleration emerges
4. This is THE CORRECT PHYSICS! Not F_cent = m·ω²·r

If we added explicit centrifugal force ON TOP of drag from swirling air,
we would DOUBLE-COUNT the centrifugal effect!
"""

import numpy as np
import warp as wp

# Mathematical constant (not a tuning parameter!)
PI = 3.14159265359


@wp.func
def compute_stokes_drag(
    v_rel: wp.vec3,
    diameter: float,
    air_viscosity: float
) -> wp.vec3:
    """
    Compute Stokes drag force for small particles (Re < 1)

    FUNDAMENTAL LAW: Stokes drag (textbook equation!)
        F_drag = 6·π·μ·r·v_rel = 3·π·μ·d·v_rel

    Valid for: Reynolds number Re = ρ·v·d/μ < 1
    Typical for: Microparticles in air (d < 100 μm)

    Physical meaning:
    1. Force opposes relative motion (toward air velocity)
    2. Linear in velocity (low Re → no turbulence)
    3. Stronger for larger particles (∝ d)
    4. Stronger in more viscous fluids (∝ μ)

    This drag force is THE mechanism that:
    - Pulls particles with air flow
    - Creates centrifugal motion (from tangential air component)
    - Drags fine particles inward (from radial air inflow)

    Args:
        v_rel: Relative velocity (particle - air) [m/s]
        diameter: Particle diameter [m]
        air_viscosity: Air dynamic viscosity [Pa·s] (PHYSICAL CONSTANT!)

    Returns:
        Drag force vector [N]
    """
    # Stokes drag coefficient: 3πμd
    # (Factor of 3 comes from: 6πμr = 6πμ(d/2) = 3πμd)
    drag_coeff = 3.0 * PI * air_viscosity * diameter

    # Force direction: opposite to relative velocity
    # Negative sign: pulls particle toward air velocity
    return -v_rel * drag_coeff


@wp.func
def compute_drag_force_extended(
    v_rel: wp.vec3,
    diameter: float,
    particle_density: float,
    air_density: float,
    air_viscosity: float
) -> wp.vec3:
    """
    Compute drag force with Stokes-to-turbulent transition
    
    For larger particles or higher velocities, use Schiller-Naumann correlation.
    
    Args:
        v_rel: Relative velocity (particle - air)
        diameter: Particle diameter (m)
        particle_density: Particle density (kg/m³)
        air_density: Air density (kg/m³)
        air_viscosity: Air dynamic viscosity (Pa·s)
        
    Returns:
        Drag force vector (N)
    """
    vel_mag = wp.length(v_rel)
    
    if vel_mag < 1e-8:
        return wp.vec3(0.0, 0.0, 0.0)
    
    # Reynolds number
    Re = air_density * vel_mag * diameter / air_viscosity
    
    # Drag coefficient
    if Re < 0.1:
        # Stokes regime (most microparticles)
        Cd = 24.0 / wp.max(Re, 0.001)
    elif Re < 1000.0:
        # Intermediate regime (Schiller-Naumann)
        Cd = 24.0 / Re * (1.0 + 0.15 * wp.pow(Re, 0.687))
    else:
        # Turbulent regime (rare for microparticles)
        Cd = 0.44
    
    # Drag force: F = 0.5·ρ·v²·A·Cd
    radius = diameter / 2.0
    area = PI * radius * radius
    F_drag_mag = 0.5 * air_density * vel_mag * vel_mag * area * Cd
    
    # Direction: opposite to relative velocity
    F_drag = -v_rel / vel_mag * F_drag_mag
    
    return F_drag


@wp.func
def compute_particle_mass(diameter: float, density: float) -> float:
    """Compute particle mass from diameter and density"""
    radius = diameter / 2.0
    volume = (4.0 / 3.0) * PI * radius * radius * radius
    return density * volume


@wp.kernel
def compute_particle_forces_corrected(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=wp.float32),
    densities: wp.array(dtype=wp.float32),
    active: wp.array(dtype=wp.int32),
    forces: wp.array(dtype=wp.vec3),
    masses: wp.array(dtype=wp.float32),
    # Air properties
    air_velocities: wp.array(dtype=wp.vec3),
    air_density: float,          # PHYSICAL CONSTANT from control_parameters
    air_viscosity: float,        # PHYSICAL CONSTANT from control_parameters
    # Gravity
    gravity: float               # PHYSICAL CONSTANT from control_parameters
):
    """
    Compute forces on particles using FUNDAMENTAL PHYSICS ONLY

    FORCES INCLUDED:
    ================
    1. DRAG: F = 6πμr·(v_air - v_particle)
       - Stokes law for Re < 1
       - Schiller-Naumann for higher Re
       - THE primary force on microparticles

    2. GRAVITY: F = m·g
       - Always downward
       - Constant acceleration

    FORCES EXCLUDED (and why):
    ===========================
    - CENTRIFUGAL: Emerges from drag + swirling air (already included!)
    - BUOYANCY: Negligible (ρ_particle/ρ_air ≈ 1000)
    - BASSET HISTORY: Negligible for steady-state
    - ADDED MASS: Negligible (ρ_particle >> ρ_air)
    - MAGNUS: Negligible (no particle rotation)
    - SAFFMAN LIFT: Negligible (low shear)

    KEY INSIGHT:
    ============
    Centrifugal "force" is NOT added explicitly!
    - Air swirls tangentially (v_θ from Rankine vortex)
    - Drag accelerates particle tangentially
    - Particle follows curved path
    - Centrifugal acceleration emerges naturally from Newton's laws!

    Adding explicit F_cent = m·ω²·r would DOUBLE-COUNT the effect!
    """
    i = wp.tid()
    
    if active[i] == 0:
        forces[i] = wp.vec3(0.0, 0.0, 0.0)
        return
    
    pos = positions[i]
    vel = velocities[i]
    d = diameters[i]
    rho = densities[i]
    
    # Particle mass
    mass = compute_particle_mass(d, rho)
    masses[i] = mass
    
    # Air velocity at particle position
    v_air = air_velocities[i]
    
    # Relative velocity (particle relative to air)
    v_rel = vel - v_air
    
    # === DRAG FORCE (PRIMARY FORCE!) ===
    # Choose appropriate drag model based on particle size
    # For microparticles (d < 50 μm): Stokes drag (Re < 1)
    # For larger particles: Extended drag with Re dependence
    if d < 50e-6:
        F_drag = compute_stokes_drag(v_rel, d, air_viscosity)
    else:
        F_drag = compute_drag_force_extended(v_rel, d, rho, air_density, air_viscosity)

    # === GRAVITY (CONSTANT FORCE) ===
    # Always acts downward (negative z direction)
    # F_g = m·g where g = 9.81 m/s² (PHYSICAL CONSTANT!)
    F_gravity = wp.vec3(0.0, 0.0, -gravity * mass)

    # === TOTAL FORCE (FUNDAMENTAL PHYSICS!) ===
    # Only drag + gravity!
    # NO explicit centrifugal force - it emerges from swirling air!
    #
    # Centrifugal effect comes from:
    #   1. Air has tangential velocity v_θ (from Rankine vortex)
    #   2. Drag pulls particle tangentially → particle gains v_θ
    #   3. Particle moves in circular path → a_cent = v_θ²/r
    #   4. This IS the centrifugal acceleration!
    #
    # Adding F_cent = m·ω²·r would be DOUBLE-COUNTING!
    forces[i] = F_gravity + F_drag


@wp.kernel
def update_particle_motion_corrected(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    forces: wp.array(dtype=wp.vec3),
    masses: wp.array(dtype=wp.float32),
    active: wp.array(dtype=wp.int32),
    dt: float,
    velocity_damping: float = 0.999  # Slight damping for stability
):
    """
    Update particle positions and velocities using semi-implicit Euler
    
    Semi-implicit Euler is more stable than explicit Euler:
    1. Update velocity: v_new = v + a·dt
    2. Update position: x_new = x + v_new·dt  (use NEW velocity)
    """
    i = wp.tid()
    
    if active[i] == 0:
        return
    
    mass = masses[i]
    if mass < 1e-20:
        return
    
    # Acceleration
    accel = forces[i] / mass
    
    # Update velocity (with optional damping for stability)
    new_vel = (velocities[i] + accel * dt) * velocity_damping
    
    # Limit maximum velocity (for stability)
    vel_mag = wp.length(new_vel)
    if vel_mag > 50.0:  # Max 50 m/s
        new_vel = new_vel * (50.0 / vel_mag)
    
    velocities[i] = new_vel
    
    # Update position using NEW velocity (semi-implicit)
    positions[i] = positions[i] + new_vel * dt


# =============================================================================
# DIAGNOSTIC FUNCTIONS
# =============================================================================

def analyze_force_balance(
    diameter: float,
    density: float,
    r_position: float,
    air_flow_m3s: float,
    rotor_omega: float,
    selector_radius: float,
    selector_height: float,
    air_viscosity: float = 1.81e-5
) -> dict:
    """
    Analyze force balance for a particle at given position
    
    This helps verify that the physics is correct by checking that
    forces balance at the cut size.
    
    Returns dict with force magnitudes and predicted behavior.
    """
    # Particle properties
    radius = diameter / 2.0
    volume = (4.0/3.0) * PI * radius**3
    mass = density * volume
    
    # Air velocities at this position (approximate)
    # Radial inflow
    v_r = air_flow_m3s / (2.0 * PI * r_position * selector_height)
    
    # Tangential (at selector edge, solid body rotation)
    if r_position < selector_radius:
        v_theta = rotor_omega * r_position
    else:
        v_theta = rotor_omega * selector_radius**2 / r_position
    
    # Drag force from radial inflow (pulls particle INWARD)
    F_drag_r = 6.0 * PI * air_viscosity * radius * v_r
    
    # Centrifugal acceleration from circular motion
    # If particle moves with air tangentially: a_cent = v_θ²/r
    a_cent = v_theta**2 / r_position
    F_cent = mass * a_cent
    
    # Gravity
    F_gravity = mass * 9.81
    
    # Determine behavior
    if F_drag_r > F_cent:
        behavior = "FINES (drag > centrifugal)"
    else:
        behavior = "COARSE (centrifugal > drag)"
    
    return {
        'diameter_um': diameter * 1e6,
        'mass_kg': mass,
        'v_r_ms': v_r,
        'v_theta_ms': v_theta,
        'F_drag_r_N': F_drag_r,
        'F_centrifugal_N': F_cent,
        'F_gravity_N': F_gravity,
        'drag_to_cent_ratio': F_drag_r / F_cent if F_cent > 0 else float('inf'),
        'predicted_behavior': behavior
    }


def compute_theoretical_d50(
    air_flow_m3s: float,
    rotor_omega: float,
    selector_radius: float,
    selector_height: float,
    particle_density: float = 1400.0,
    air_viscosity: float = 1.81e-5
) -> float:
    """
    Compute theoretical cut size (d50) from operating parameters
    
    At d50, drag force = centrifugal force:
    
    6πμr·v_r = m·ω²·R
    
    Solving for d:
    d50 = √(9·μ·Q / (π·ρ_p·ω²·R²·h))
    
    Returns d50 in meters.
    """
    Q = air_flow_m3s
    omega = rotor_omega
    R = selector_radius
    h = selector_height
    rho_p = particle_density
    mu = air_viscosity
    
    d50_squared = 9.0 * mu * Q / (PI * rho_p * omega**2 * R**2 * h)
    d50 = np.sqrt(d50_squared)
    
    return d50


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# Keep old function names for compatibility
compute_particle_forces = compute_particle_forces_corrected
update_particle_motion = update_particle_motion_corrected


if __name__ == "__main__":
    """Test particle dynamics"""
    print("=" * 70)
    print("PARTICLE DYNAMICS TEST (CORRECTED)")
    print("=" * 70)
    
    # Test parameters
    air_flow_m3s = 2000 / 3600  # 2000 m³/hr
    rotor_rpm = 3000
    rotor_omega = rotor_rpm * 2 * PI / 60
    selector_radius = 0.1  # m
    selector_height = 0.1  # m
    particle_density = 1400  # kg/m³
    
    # Compute theoretical d50
    d50 = compute_theoretical_d50(
        air_flow_m3s, rotor_omega, 
        selector_radius, selector_height,
        particle_density
    )
    
    print(f"\nOperating conditions:")
    print(f"  Air flow: {air_flow_m3s * 3600:.0f} m³/hr")
    print(f"  Rotor: {rotor_rpm:.0f} RPM ({rotor_omega:.1f} rad/s)")
    print(f"  Selector: r={selector_radius*1000:.0f}mm, h={selector_height*1000:.0f}mm")
    
    print(f"\nTheoretical d50: {d50*1e6:.1f} μm")
    
    print(f"\nForce balance at r = {selector_radius}m:")
    print("-" * 70)
    print(f"{'Diameter':>10} {'F_drag':>12} {'F_cent':>12} {'Ratio':>10} {'Prediction'}")
    print(f"{'(μm)':>10} {'(N)':>12} {'(N)':>12} {'':>10} {''}")
    print("-" * 70)
    
    for d_um in [5, 10, 15, 20, 25, 30, 40]:
        d = d_um * 1e-6
        result = analyze_force_balance(
            d, particle_density, selector_radius,
            air_flow_m3s, rotor_omega, selector_radius, selector_height
        )
        print(f"{d_um:>10} {result['F_drag_r_N']:>12.2e} {result['F_centrifugal_N']:>12.2e} "
              f"{result['drag_to_cent_ratio']:>10.2f} {result['predicted_behavior']}")
    
    print("-" * 70)
    print(f"\nParticles < {d50*1e6:.1f} μm → FINES (drag dominates)")
    print(f"Particles > {d50*1e6:.1f} μm → COARSE (centrifugal dominates)")
    
    print("\n" + "=" * 70)
    print("✓ Particle dynamics test complete")
    print("=" * 70)
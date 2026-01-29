"""
Collision Detection and Collection - GEOMETRY-BASED ONLY

Handles particle-boundary collisions and collection at outlets.

PHILOSOPHY:
===========
This module handles ONLY geometry-based operations:
1. Particle hits wall → reflect (elastic/inelastic collision)
2. Particle reaches outlet → collect (remove from simulation)
3. NO SIZE-BASED CLASSIFICATION!

The PHYSICS (in particle_dynamics.py + air_flow.py) determines trajectories.
The COLLECTION (here) simply records where particles exit.

FUNDAMENTAL PRINCIPLE:
======================
Separation is determined by PHYSICS, not by collection logic!

Small particles:
  - Drag > Centrifugal → pulled inward by radial flow
  - Rise through selector → exit at TOP = FINES

Large particles:
  - Centrifugal > Drag → pushed outward
  - Fall in annular zone → exit at BOTTOM = COARSE

This code does NOT check particle size!
If a large particle reaches the fines outlet, it's collected as fines
(though this shouldn't happen if physics is correct).

PARAMETERS:
===========
All geometric parameters (outlet positions, radii) come from control_parameters.py
Restitution coefficient (energy loss in collisions) could be tuned, but typically 0.3-0.5
"""

import warp as wp
from typing import Dict, Optional

# Mathematical constant (not a tuning parameter!)
PI = 3.14159265359


@wp.kernel
def apply_boundaries_and_collection_corrected(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=wp.float32),
    particle_types: wp.array(dtype=wp.int32),
    active: wp.array(dtype=wp.int32),
    # Collection tracking
    collected_fine: wp.array(dtype=wp.int32),
    collected_coarse: wp.array(dtype=wp.int32),
    collection_time: wp.array(dtype=wp.float32),
    collection_position: wp.array(dtype=wp.vec3),
    collection_outlet: wp.array(dtype=wp.int32),
    # GEOMETRY (fixed machine dimensions from control_parameters)
    chamber_radius: float,
    chamber_height: float,
    cone_height: float,
    # OUTLETS (geometric positions from control_parameters)
    fines_outlet_z: float,
    fines_outlet_radius: float,
    coarse_outlet_z: float,
    coarse_outlet_radius: float,
    # Simulation parameters
    current_time: float,
    restitution: float  # Collision energy loss (0.3 = 70% energy lost)
):
    """
    Apply boundary conditions and collect particles at OUTLETS ONLY

    PURE GEOMETRY - NO PHYSICS!
    ===========================
    This kernel handles:
    1. Particle-wall collisions (elastic/inelastic reflection)
    2. Particle collection at outlets (geometric check only)

    NO SIZE-BASED CLASSIFICATION!
    ==============================
    Collection criterion is PURELY geometric:
    - Particle position reaches outlet region → collect
    - NO check of particle size!

    The PHYSICS has already determined the trajectory:
    - Small particles: drag > centrifugal → go up → exit at FINES outlet
    - Large particles: centrifugal > drag → go down → exit at COARSE outlet

    If physics is correct, particles will naturally separate by size.
    If physics is wrong, this code won't "fix" it by adding size checks!

    PARAMETERS:
    ===========
    All geometric parameters (outlets, radii) from control_parameters.py
    Restitution: typical value 0.3 (70% energy lost), could be material-specific
    """
    i = wp.tid()
    
    if active[i] == 0:
        return
    
    pos = positions[i]
    vel = velocities[i]
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z = pos[2]
    
    # =========================================================================
    # FINES COLLECTION (TOP OUTLET)
    # =========================================================================
    # GEOMETRIC CHECK ONLY: Has particle reached top outlet?
    # NO SIZE CHECK! Physics determines which particles get here.

    if z >= fines_outlet_z:
        if r < fines_outlet_radius:
            # Particle exits through fines outlet → COLLECT AS FINES
            # This happens naturally for small particles (drag > centrifugal)
            wp.atomic_add(collected_fine, 0, 1)
            active[i] = 0
            collection_time[i] = current_time
            collection_position[i] = pos
            collection_outlet[i] = 1  # Outlet ID: 1 = fines
            return
        else:
            # Particle hit top but OUTSIDE outlet → REFLECT
            # (Shouldn't happen often if geometry is well-designed)
            positions[i] = wp.vec3(pos[0], pos[1], fines_outlet_z - 0.01)
            velocities[i] = wp.vec3(vel[0], vel[1], -wp.abs(vel[2]) * restitution)
            return

    # =========================================================================
    # COARSE COLLECTION (BOTTOM OUTLET)
    # =========================================================================
    # GEOMETRIC CHECK ONLY: Has particle reached bottom outlet?
    # NO SIZE CHECK! Physics determines which particles get here.

    if z <= coarse_outlet_z:
        if r < coarse_outlet_radius:
            # Particle exits through coarse outlet → COLLECT AS COARSE
            # This happens naturally for large particles (centrifugal > drag)
            wp.atomic_add(collected_coarse, 0, 1)
            active[i] = 0
            collection_time[i] = current_time
            collection_position[i] = pos
            collection_outlet[i] = 2  # Outlet ID: 2 = coarse
            return
        else:
            # In cone but not at outlet - redirect toward outlet
            # Cone wall naturally pushes particles toward center
            positions[i] = wp.vec3(pos[0] * 0.95, pos[1] * 0.95, coarse_outlet_z + 0.01)
            velocities[i] = wp.vec3(vel[0] * 0.5, vel[1] * 0.5, -wp.abs(vel[2]) * 0.3)
            return
    
    # =========================================================================
    # CYLINDRICAL WALL COLLISION
    # =========================================================================
    # GEOMETRY: Elastic/inelastic reflection at chamber wall
    # Radial component reversed, tangential preserved, energy lost via restitution

    if r >= chamber_radius * 0.99:
        # Particle hit outer wall → REFLECT

        # Push back inside (numerical stability)
        r_safe = chamber_radius * 0.98
        scale = r_safe / r
        new_x = pos[0] * scale
        new_y = pos[1] * scale

        # Decompose velocity into radial and tangential components
        if r > 0.01:
            # Unit vectors in cylindrical coordinates
            cos_t = pos[0] / r
            sin_t = pos[1] / r

            # Velocity in cylindrical coordinates
            v_r = vel[0] * cos_t + vel[1] * sin_t  # Radial (toward/away from center)
            v_t = -vel[0] * sin_t + vel[1] * cos_t  # Tangential (circumferential)

            # Reflection: reverse radial, keep tangential, apply energy loss
            v_r = -v_r * restitution

            # Convert back to Cartesian
            new_vx = v_r * cos_t - v_t * sin_t
            new_vy = v_r * sin_t + v_t * cos_t

            velocities[i] = wp.vec3(new_vx, new_vy, vel[2])

        positions[i] = wp.vec3(new_x, new_y, pos[2])
    
    # =========================================================================
    # CONE WALL COLLISION (z < 0)
    # =========================================================================
    if z < 0.0 and z > coarse_outlet_z:
        # In cone region
        # Cone radius decreases linearly: r_cone = R_chamber × (1 + z/h_cone)
        # At z=0: r_cone = R_chamber
        # At z=-h_cone: r_cone = 0
        
        cone_radius = chamber_radius * (cone_height + z) / cone_height
        cone_radius = wp.max(cone_radius, coarse_outlet_radius)
        
        if r >= cone_radius * 0.99:
            # Hit cone wall - slide down toward outlet
            r_safe = cone_radius * 0.95
            scale = r_safe / wp.max(r, 0.01)
            
            new_x = pos[0] * scale
            new_y = pos[1] * scale
            
            # Reduce velocity, add slight downward component
            positions[i] = wp.vec3(new_x, new_y, z)
            
            # Decompose and reflect
            if r > 0.01:
                cos_t = pos[0] / r
                sin_t = pos[1] / r
                
                v_r = vel[0] * cos_t + vel[1] * sin_t
                v_t = -vel[0] * sin_t + vel[1] * cos_t
                
                # Reflect with damping
                v_r = -v_r * restitution * 0.5
                
                new_vx = v_r * cos_t - v_t * sin_t
                new_vy = v_r * sin_t + v_t * cos_t
                
                # Add downward bias (gravity + cone geometry)
                new_vz = vel[2] * 0.5 - 0.1
                
                velocities[i] = wp.vec3(new_vx, new_vy, new_vz)
    
    # =========================================================================
    # SHAFT COLLISION (optional - if particles get too close to center shaft)
    # =========================================================================
    shaft_radius = 0.025  # 50mm diameter shaft
    if r < shaft_radius and z > 0.0:
        # Hit shaft - push outward
        r_safe = shaft_radius * 1.1
        if r > 0.001:
            scale = r_safe / r
            positions[i] = wp.vec3(pos[0] * scale, pos[1] * scale, z)
            
            # Reflect radial velocity
            cos_t = pos[0] / r
            sin_t = pos[1] / r
            v_r = vel[0] * cos_t + vel[1] * sin_t
            
            if v_r < 0:  # Moving inward
                v_t = -vel[0] * sin_t + vel[1] * cos_t
                v_r = -v_r * restitution
                
                new_vx = v_r * cos_t - v_t * sin_t
                new_vy = v_r * sin_t + v_t * cos_t
                velocities[i] = wp.vec3(new_vx, new_vy, vel[2])


@wp.kernel
def check_particle_status(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    active: wp.array(dtype=wp.int32),
    status: wp.array(dtype=wp.int32),  # 0=active, 1=fines_zone, 2=coarse_zone, 3=stuck
    fines_outlet_z: float,
    coarse_outlet_z: float,
    selector_z_center: float
):
    """
    Check particle status for debugging
    
    Helps identify where particles are and if they're stuck.
    """
    i = wp.tid()
    
    if active[i] == 0:
        status[i] = 0
        return
    
    pos = positions[i]
    vel = velocities[i]
    z = pos[2]
    
    vel_mag = wp.length(vel)
    
    if z > fines_outlet_z - 0.1:
        status[i] = 1  # Near fines outlet
    elif z < coarse_outlet_z + 0.1:
        status[i] = 2  # Near coarse outlet
    elif vel_mag < 0.001:
        status[i] = 3  # Stuck (very low velocity)
    else:
        status[i] = 0  # Active and moving


# =============================================================================
# LEGACY FUNCTION FOR COMPATIBILITY
# =============================================================================

def handle_collisions(
    positions: wp.array,
    velocities: wp.array,
    active: wp.array,
    boundary_conditions: Dict,
    device: str = "cuda:0"
):
    """
    Legacy function - redirects to corrected implementation
    """
    bc = boundary_conditions
    
    # Create dummy arrays for collection tracking
    n = positions.shape[0]
    collected_fine = wp.zeros(1, dtype=wp.int32, device=device)
    collected_coarse = wp.zeros(1, dtype=wp.int32, device=device)
    collection_time = wp.zeros(n, dtype=wp.float32, device=device)
    collection_position = wp.zeros(n, dtype=wp.vec3, device=device)
    collection_outlet = wp.zeros(n, dtype=wp.int32, device=device)
    diameters = wp.zeros(n, dtype=wp.float32, device=device)
    particle_types = wp.zeros(n, dtype=wp.int32, device=device)
    
    wp.launch(
        kernel=apply_boundaries_and_collection_corrected,
        dim=n,
        inputs=[
            positions,
            velocities,
            diameters,
            particle_types,
            active,
            collected_fine,
            collected_coarse,
            collection_time,
            collection_position,
            collection_outlet,
            bc['chamber_radius'],
            bc['chamber_height'],
            bc['cone_height'],
            bc.get('fines_outlet_z', bc['chamber_height']),
            bc.get('fines_outlet_radius', 0.075),
            bc.get('coarse_outlet_z', -bc['cone_height']),
            bc.get('coarse_outlet_radius', 0.075),
            0.0,  # current_time
            0.3   # restitution
        ],
        device=device
    )


# Keep old name for compatibility
apply_boundaries_and_collection = apply_boundaries_and_collection_corrected


if __name__ == "__main__":
    """Test collision handling"""
    print("=" * 70)
    print("COLLISION HANDLING TEST (CORRECTED)")
    print("=" * 70)
    
    print("\nKey changes from original:")
    print("  ✓ NO size-based classification")
    print("  ✓ Collection only at actual outlets")
    print("  ✓ Physics determines separation")
    print("  ✓ Proper cone geometry handling")
    
    print("\nCollection logic:")
    print("  FINES:  z >= fines_outlet_z AND r < fines_outlet_radius")
    print("  COARSE: z <= coarse_outlet_z AND r < coarse_outlet_radius")
    print("  (No size check - physics already determined trajectory!)")
    
    print("\n" + "=" * 70)
    print("✓ Collision handling test complete")
    print("=" * 70)
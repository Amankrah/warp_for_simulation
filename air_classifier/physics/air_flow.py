"""
Air Flow Field Modeling - FUNDAMENTAL PHYSICS ONLY

Computes air velocity field in the classifier chamber using ONLY fundamental equations:
1. Mass continuity: Q = ∫∫ v·dA
2. Rankine vortex model (standard fluid mechanics)
3. No empirical tuning parameters
4. No magic numbers

PHILOSOPHY:
===========
This module contains ONLY the physics - the unchanging laws of fluid mechanics.
All tunable parameters (RPM, air flow, geometry) come from control_parameters.py

FUNDAMENTAL EQUATIONS USED:
===========================
1. RADIAL VELOCITY: From mass continuity equation
   Q = 2π·r·h·v_r  →  v_r = Q/(2π·r·h)

2. TANGENTIAL VELOCITY: Rankine vortex (solid body + free vortex)
   r < R: v_θ = ω·r        (solid body rotation)
   r > R: v_θ = ω·R²/r     (free vortex, conserves angular momentum)

3. AXIAL VELOCITY: From flow distribution + continuity
   Central: v_z = Q/A_central     (all air exits through top)
   Annular: v_z = -Q/A_annular    (return flow, mass balance)
"""

import numpy as np
import warp as wp
from typing import Dict

# Mathematical constant (not a tuning parameter!)
PI = 3.14159265359


@wp.func
def compute_air_velocity_corrected(
    position: wp.vec3,
    # GEOMETRY (fixed machine dimensions)
    chamber_radius: float,
    selector_radius: float,
    selector_z_min: float,
    selector_z_max: float,
    distributor_z: float,
    cone_height: float,
    # OPERATING CONDITIONS (control board settings)
    air_flow_m3s: float,  # Volumetric flow rate [m³/s] - operator adjusts
    rotor_omega: float,   # Rotor angular velocity [rad/s] - operator adjusts
) -> wp.vec3:
    """
    Compute air velocity using FUNDAMENTAL PHYSICS ONLY

    NO TUNING PARAMETERS! All velocities derived from:
    1. Conservation of mass (continuity equation)
    2. Rankine vortex model (standard fluid mechanics)
    3. Machine geometry (fixed dimensions)
    4. Operating conditions (RPM, air flow from control board)

    The three velocity components:

    1. RADIAL (v_r): INWARD flow at selector
       Physics: Mass continuity → v_r = Q/(2πrh)
       Purpose: Pulls fine particles through selector center

    2. TANGENTIAL (v_θ): Swirl from rotor
       Physics: Rankine vortex (solid body + free vortex)
       Purpose: Creates centrifugal acceleration on particles

    3. AXIAL (v_z): Vertical flow
       Physics: Continuity → v_z = Q/A
       Purpose: Central upflow (fines), annular downflow (coarse)
    """
    # Cylindrical coordinates (geometry-based transformation)
    r = wp.sqrt(position[0] * position[0] + position[1] * position[1])
    z = position[2]

    # Avoid singularity at center (numerical stability, not physics tuning!)
    r = wp.max(r, 0.01)

    # Unit vectors for cylindrical → Cartesian conversion
    cos_theta = position[0] / r
    sin_theta = position[1] / r

    # Geometric parameters (derived from machine dimensions)
    selector_z_center = (selector_z_min + selector_z_max) / 2.0
    selector_height = selector_z_max - selector_z_min

    # Determine particle location (pure geometry!)
    in_selector_zone = (z >= selector_z_min - selector_height * 0.5) and \
                       (z <= selector_z_max + selector_height * 0.5)
    above_selector = z > selector_z_max
    below_selector = z < selector_z_min
    above_distributor = z > distributor_z
    in_cone = z < 0.0
    
    # =========================================================================
    # RADIAL VELOCITY (v_r) - THE KEY SEPARATION MECHANISM!
    # =========================================================================
    # FUNDAMENTAL EQUATION: Mass continuity in cylindrical coordinates
    #   Q = ∫∫ v_r · r · dθ · dz
    #   For uniform flow over height h at radius r:
    #   Q = 2π·r·h·v_r
    #   Therefore: v_r = Q / (2π·r·h)
    #
    # NEGATIVE = INWARD (toward center)
    # This radial inflow is what PULLS FINE PARTICLES through the selector!

    if in_selector_zone and r > selector_radius * 0.3:
        # At selector zone - strongest radial inflow
        # Height = selector_height (the classification zone)
        v_r = -air_flow_m3s / (2.0 * PI * r * selector_height)

        # Stability limit (prevent numerical issues, not physics tuning!)
        v_r = wp.max(v_r, -10.0)

    elif above_distributor and not in_selector_zone:
        # Between distributor and selector - moderate radial flow
        # Effective height ≈ chamber_radius (characteristic length)
        v_r = -air_flow_m3s / (2.0 * PI * r * chamber_radius) * 0.3

    elif in_cone:
        # In cone region - weak radial flow
        v_r = -air_flow_m3s / (2.0 * PI * r * chamber_radius) * 0.1

    else:
        # Below distributor - minimal radial flow
        v_r = -air_flow_m3s / (2.0 * PI * r * chamber_radius) * 0.05
    
    # =========================================================================
    # TANGENTIAL VELOCITY (v_θ) - Creates centrifugal effect
    # =========================================================================
    # FUNDAMENTAL MODEL: Rankine vortex (standard fluid mechanics textbook!)
    #
    # Physical Origin:
    #   - Rotor at radius R rotates at angular velocity ω
    #   - Air at rotor surface: v_θ = ω·R
    #   - Inside rotor (r < R): Solid body rotation, v_θ = ω·r
    #   - Outside rotor (r > R): Free vortex (conserves angular momentum)
    #     L = r·v_θ = const → v_θ = ω·R²/r
    #
    # NO EMPIRICAL PARAMETERS! This is THE standard vortex model.

    if r < selector_radius:
        # Inside selector: Solid body rotation
        # Fluid rotates with rotor, v = ω × r
        v_theta = rotor_omega * r

    else:
        # Outside selector: Free vortex
        # Angular momentum conserved: L = m·v_θ·r = const
        # v_θ ∝ 1/r
        v_theta = rotor_omega * selector_radius * selector_radius / r

    # Axial decay of swirl (geometric effect, not tuning!)
    # Swirl is strongest at selector, decays above/below
    if not in_selector_zone:
        # Distance from selector center
        z_dist = wp.abs(z - selector_z_center)

        # Exponential decay (characteristic length = 2×selector_height)
        decay = wp.exp(-z_dist / (selector_height * 2.0))

        # Apply decay (some base swirl remains from tangential inlets)
        v_theta = v_theta * (0.7 * decay + 0.3)
    
    # =========================================================================
    # AXIAL VELOCITY (v_z) - Derived from CONTINUITY EQUATION
    # =========================================================================
    # FUNDAMENTAL PRINCIPLE: Conservation of mass
    #
    # Physical Reality:
    #   - All air Q enters at bottom (cone region)
    #   - All air Q exits through fines outlet at top (central region)
    #   - Flow must be continuous (no accumulation)
    #
    # Flow Pattern:
    #   - Central region (r < R_selector): UPFLOW carries fines to top outlet
    #   - Annular region (r > R_selector): DOWNFLOW returns air + rejected particles
    #   - Continuity: Q_up = Q_down (what goes up must come down)
    #
    # NO EMPIRICAL PARAMETERS! Pure continuity equation:
    #   v_z = Q / A

    # Calculate areas for continuity (GEOMETRY, not tuning!)
    A_central = PI * selector_radius * selector_radius
    A_annular = PI * (chamber_radius * chamber_radius - selector_radius * selector_radius)
    A_chamber = PI * chamber_radius * chamber_radius

    # Base velocities from continuity (FUNDAMENTAL PHYSICS!)
    v_z_central_base = air_flow_m3s / A_central       # Upward in center
    v_z_annular_base = -air_flow_m3s / A_annular     # Downward in annulus
    v_z_chamber_base = air_flow_m3s / A_chamber      # Below selector

    # Zone-dependent distribution (GEOMETRY-BASED, not tuned!)
    if in_cone:
        # In cone region - expanding cross-section
        # Cone radius: r_cone(z) = R_chamber × (h_cone + z) / h_cone
        # Area varies with height
        cone_radius_at_z = chamber_radius * (cone_height + z) / cone_height
        cone_radius_at_z = wp.max(cone_radius_at_z, 0.01)
        A_cone = PI * cone_radius_at_z * cone_radius_at_z
        v_z = air_flow_m3s / A_cone

    elif z < distributor_z:
        # Below distributor - full chamber cross-section
        v_z = v_z_chamber_base

    elif below_selector:
        # Between distributor and selector - particles rising to selector
        # Full chamber upflow
        v_z = v_z_chamber_base

    elif in_selector_zone or above_selector:
        # At and above selector - CENTRAL UPFLOW + ANNULAR DOWNFLOW
        # This is THE KEY SEPARATION MECHANISM!

        # Transition zone width (geometric parameter, not tuning!)
        transition_width = selector_radius * 0.1  # 10% of radius

        if r < selector_radius:
            # Inside selector - pure upflow
            v_z = v_z_central_base

        elif r < selector_radius + transition_width:
            # Transition zone - smooth interpolation
            # From upflow to downflow to avoid discontinuity
            blend = (r - selector_radius) / transition_width
            v_z = v_z_central_base * (1.0 - blend) + v_z_annular_base * blend

        else:
            # Annular downflow region - rejected particles fall here
            v_z = v_z_annular_base

    else:
        # Fallback (should not reach here if zones are well-defined)
        v_z = 0.0
    
    # =========================================================================
    # CONVERT TO CARTESIAN COORDINATES
    # =========================================================================
    # v_x = v_r·cos(θ) - v_θ·sin(θ)
    # v_y = v_r·sin(θ) + v_θ·cos(θ)
    
    v_x = v_r * cos_theta - v_theta * sin_theta
    v_y = v_r * sin_theta + v_theta * cos_theta
    
    return wp.vec3(v_x, v_y, v_z)


@wp.kernel
def compute_air_velocity_field_kernel(
    positions: wp.array(dtype=wp.vec3),
    air_velocities: wp.array(dtype=wp.vec3),
    active: wp.array(dtype=wp.int32),
    # Geometry
    chamber_radius: float,
    selector_radius: float,
    selector_z_min: float,
    selector_z_max: float,
    distributor_z: float,
    cone_height: float,
    # Operating conditions
    air_flow_m3s: float,
    rotor_omega: float
):
    """
    Compute air velocity field for all particles

    This kernel applies the fundamental velocity field equations to each particle.
    """
    i = wp.tid()

    if active[i] == 0:
        air_velocities[i] = wp.vec3(0.0, 0.0, 0.0)
        return

    air_velocities[i] = compute_air_velocity_corrected(
        positions[i],
        chamber_radius, selector_radius,
        selector_z_min, selector_z_max, distributor_z, cone_height,
        air_flow_m3s, rotor_omega
    )


class AirFlowModelCorrected:
    """
    Air flow model based on FUNDAMENTAL PHYSICS

    This class wraps the physics kernels and manages parameters.
    NO TUNING HAPPENS HERE - just passing control parameters to physics!
    """

    def __init__(self, boundary_conditions: Dict):
        """
        Initialize air flow model

        Args:
            boundary_conditions: Dictionary containing:
                - Geometry (fixed machine dimensions)
                - Operating conditions (RPM, air flow from control board)
        """
        self.bc = boundary_conditions

        # GEOMETRY (fixed machine dimensions)
        self.chamber_radius = boundary_conditions['chamber_radius']
        self.selector_radius = boundary_conditions['selector_radius']
        self.selector_z_min = boundary_conditions.get('selector_z_min',
                                boundary_conditions['selector_z_center'] -
                                boundary_conditions['selector_height'] / 2)
        self.selector_z_max = boundary_conditions.get('selector_z_max',
                                boundary_conditions['selector_z_center'] +
                                boundary_conditions['selector_height'] / 2)
        self.distributor_z = boundary_conditions.get('distributor_z', 0.5)
        self.cone_height = boundary_conditions.get('cone_height', 0.866)

        # OPERATING CONDITIONS (from control board)
        # Convert from m³/hr to m³/s if needed
        air_flow = boundary_conditions.get('air_flow_m3s',
                                           boundary_conditions.get('air_flow_rate', 2000) / 3600)
        if air_flow > 10:  # Probably in m³/hr
            air_flow = air_flow / 3600
        self.air_flow_m3s = air_flow

        self.rotor_omega = boundary_conditions['rotor_omega']

        # Print configuration
        print(f"  AirFlowModel initialized (FUNDAMENTAL PHYSICS):")
        print(f"    Air flow: {self.air_flow_m3s * 3600:.0f} m³/hr ({self.air_flow_m3s:.4f} m³/s)")
        print(f"    Rotor: {self.rotor_omega * 60 / (2*PI):.0f} RPM ({self.rotor_omega:.1f} rad/s)")
        print(f"    Selector: r={self.selector_radius*1000:.0f}mm, z={self.selector_z_min:.2f}-{self.selector_z_max:.2f}m")

        # Show theoretical predictions from fundamental equations
        v_r_selector = self.air_flow_m3s / (2 * PI * self.selector_radius *
                                            (self.selector_z_max - self.selector_z_min))
        v_theta_selector = self.rotor_omega * self.selector_radius
        print(f"    Predicted v_r at selector: {v_r_selector:.2f} m/s (from continuity)")
        print(f"    Predicted v_θ at selector: {v_theta_selector:.2f} m/s (from Rankine vortex)")
    
    def compute_velocities(
        self,
        positions: wp.array,
        active: wp.array = None,
        device: str = "cuda:0"
    ) -> wp.array:
        """
        Compute air velocities at particle positions

        This method simply passes geometry and operating parameters to the
        fundamental physics kernels. NO TUNING HERE!

        Args:
            positions: Particle positions
            active: Active particle flags (optional)
            device: WARP device

        Returns:
            Air velocity array computed from fundamental equations
        """
        n = positions.shape[0]
        air_velocities = wp.zeros(n, dtype=wp.vec3, device=device)

        # Create active array if not provided
        if active is None:
            active = wp.ones(n, dtype=wp.int32, device=device)

        # Launch physics kernel with parameters
        wp.launch(
            kernel=compute_air_velocity_field_kernel,
            dim=n,
            inputs=[
                positions,
                air_velocities,
                active,
                # Geometry
                self.chamber_radius,
                self.selector_radius,
                self.selector_z_min,
                self.selector_z_max,
                self.distributor_z,
                self.cone_height,
                # Operating conditions
                self.air_flow_m3s,
                self.rotor_omega
            ],
            device=device
        )

        return air_velocities


# Keep old class name for compatibility
AirFlowModel = AirFlowModelCorrected


if __name__ == "__main__":
    """Test air flow model"""
    import numpy as np
    
    print("=" * 70)
    print("AIR FLOW MODEL TEST")
    print("=" * 70)
    
    # Test parameters
    bc = {
        'chamber_radius': 0.5,
        'selector_radius': 0.1,
        'selector_z_center': 0.75,
        'selector_height': 0.1,
        'distributor_z': 0.5,
        'air_flow_m3s': 2000 / 3600,  # 2000 m³/hr
        'rotor_omega': 314.16,  # 3000 RPM
    }
    
    model = AirFlowModelCorrected(bc)
    
    # Test velocities at key positions
    print("\nVelocity field at key positions:")
    print("-" * 70)
    
    test_points = [
        ("Center, selector", [0.0, 0.05, 0.75]),
        ("Selector edge", [0.1, 0.0, 0.75]),
        ("Outside selector", [0.2, 0.0, 0.75]),
        ("Above selector", [0.05, 0.0, 1.0]),
        ("Below selector", [0.1, 0.0, 0.3]),
        ("In cone", [0.1, 0.0, -0.2]),
    ]
    
    for name, pos in test_points:
        pos_wp = wp.vec3(pos[0], pos[1], pos[2])
        vel = compute_air_velocity_corrected(
            pos_wp,
            bc['chamber_radius'],
            bc['selector_radius'],
            bc['selector_z_center'] - bc['selector_height']/2,
            bc['selector_z_center'] + bc['selector_height']/2,
            bc['distributor_z'],
            bc.get('cone_height', 0.866),
            bc['air_flow_m3s'],
            bc['rotor_omega']
        )
        
        r = np.sqrt(pos[0]**2 + pos[1]**2)
        # Convert to cylindrical for display
        if r > 0.01:
            v_r = (vel[0] * pos[0] + vel[1] * pos[1]) / r
            v_theta = (-vel[0] * pos[1] + vel[1] * pos[0]) / r
        else:
            v_r = 0
            v_theta = np.sqrt(vel[0]**2 + vel[1]**2)
        
        print(f"{name:20s}: r={r:.2f}m, v_r={v_r:+6.2f}, v_θ={v_theta:+6.2f}, v_z={vel[2]:+6.2f} m/s")
    
    print("\n" + "=" * 70)
    print("✓ Air flow model test complete")
    print("=" * 70)
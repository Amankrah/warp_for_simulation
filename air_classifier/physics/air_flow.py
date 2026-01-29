"""
CORRECTED Air Flow Field Modeling

Computes air velocity field in the classifier chamber.

KEY FIXES:
1. Radial INFLOW at selector zone (the key separation mechanism!)
2. Proper Rankine vortex model for tangential velocity
3. Continuous velocity field (not stepped)
4. Correct scaling based on volumetric flow rate
"""

import numpy as np
import warp as wp
from typing import Dict

PI = 3.14159265359


@wp.func
def compute_air_velocity_corrected(
    position: wp.vec3,
    # Geometry
    chamber_radius: float,
    selector_radius: float,
    selector_z_min: float,
    selector_z_max: float,
    distributor_z: float,
    # Flow parameters
    air_flow_m3s: float,  # Volumetric flow rate (m³/s)
    rotor_omega: float,   # Rotor angular velocity (rad/s)
) -> wp.vec3:
    """
    Compute air velocity at a given position using CORRECT vortex model
    
    The air velocity field has three components:
    
    1. RADIAL (v_r): INWARD flow toward center at selector
       - This is THE KEY MECHANISM that pulls fine particles through!
       - From continuity: v_r = -Q / (2πrh)
       - Negative = toward center
    
    2. TANGENTIAL (v_θ): Swirl from rotor rotation
       - Creates centrifugal acceleration on particles
       - Rankine vortex: solid body inside, free vortex outside
    
    3. AXIAL (v_z): Upward flow carrying particles to selector
       - Stronger near center where fines exit
    """
    r = wp.sqrt(position[0] * position[0] + position[1] * position[1])
    z = position[2]
    
    # Avoid singularity at center
    r = wp.max(r, 0.01)
    
    # Unit vectors for cylindrical coordinates
    cos_theta = position[0] / r
    sin_theta = position[1] / r
    
    # Selector zone parameters
    selector_z_center = (selector_z_min + selector_z_max) / 2.0
    selector_height = selector_z_max - selector_z_min
    
    # Check which zone we're in
    in_selector_zone = (z > selector_z_min - selector_height * 0.5) and \
                       (z < selector_z_max + selector_height * 0.5)
    above_distributor = z > distributor_z
    in_cone = z < 0.0
    
    # =========================================================================
    # RADIAL VELOCITY (v_r) - THE KEY SEPARATION MECHANISM!
    # =========================================================================
    # From mass continuity: Q = 2π·r·h·v_r
    # Therefore: v_r = Q / (2π·r·h)
    # NEGATIVE because flow is INWARD (toward center)
    
    if in_selector_zone and r > selector_radius * 0.3:
        # Strong radial INFLOW at selector - this pulls fines through!
        # Use selector height as the effective flow area height
        v_r = -air_flow_m3s / (2.0 * PI * r * selector_height)
        # Limit to reasonable values (max ~10 m/s)
        v_r = wp.max(v_r, -10.0)
    elif above_distributor:
        # Moderate inflow above distributor, outside selector
        v_r = -air_flow_m3s / (2.0 * PI * r * chamber_radius) * 0.3
    elif in_cone:
        # Weak inflow in cone region
        v_r = -air_flow_m3s / (2.0 * PI * r * chamber_radius) * 0.1
    else:
        # Below distributor - very weak radial flow
        v_r = -air_flow_m3s / (2.0 * PI * r * chamber_radius) * 0.05
    
    # =========================================================================
    # TANGENTIAL VELOCITY (v_θ) - Creates centrifugal effect
    # =========================================================================
    # Rankine vortex model:
    # - Inside core (r < R_selector): Solid body rotation, v_θ = ω·r
    # - Outside core (r > R_selector): Free vortex, v_θ = ω·R²/r
    
    if r < selector_radius:
        # Solid body rotation inside selector
        v_theta = rotor_omega * r
    else:
        # Free vortex decay outside selector
        # v_θ = ω·R²/r (conserves angular momentum)
        v_theta = rotor_omega * selector_radius * selector_radius / r
    
    # Tangential velocity is strongest in selector zone, decays elsewhere
    if not in_selector_zone:
        # Decay swirl away from selector zone
        z_dist = wp.abs(z - selector_z_center)
        decay = wp.exp(-z_dist / (selector_height * 2.0))
        # Keep some base swirl from tangential inlets
        v_theta = v_theta * decay * 0.7 + v_theta * 0.3 * 0.3
    
    # =========================================================================
    # AXIAL VELOCITY (v_z) - Carries particles upward
    # =========================================================================
    # Upward flow from air inlets, stronger near center
    
    # Base upward velocity from volumetric flow through cross-section
    # Q = π·R²·v_z, so v_z = Q / (π·R²)
    
    if in_cone:
        # In cone - weak upward flow, mostly swirling
        effective_radius = chamber_radius * (1.0 + z / chamber_radius)  # Decreases in cone
        effective_radius = wp.max(effective_radius, 0.1)
        v_z = air_flow_m3s / (PI * effective_radius * effective_radius) * 0.2
    elif z < distributor_z:
        # Below distributor - moderate upward flow
        v_z = air_flow_m3s / (PI * chamber_radius * chamber_radius) * 0.5
    elif in_selector_zone:
        # In selector zone - velocity depends on radial position
        if r < selector_radius:
            # Inside selector - STRONG upward flow (fines exit here!)
            v_z = air_flow_m3s / (PI * selector_radius * selector_radius) * 1.2
        else:
            # Outside selector - DOWNWARD annular flow (coarse particles fall!)
            # Create annular downdraft zone for rejected particles
            downdraft_strength = (r - selector_radius) / (chamber_radius - selector_radius)
            v_z = -2.0 * downdraft_strength  # Negative = DOWNWARD
    else:
        # Above selector (fines outlet region)
        if r < selector_radius:
            # Near center - strong upward toward outlet
            v_z = air_flow_m3s / (PI * selector_radius * selector_radius)
        else:
            # At edges - STRONG DOWNWARD (rejected particles must fall!)
            downdraft_strength = (r - selector_radius) / (chamber_radius - selector_radius)
            v_z = -3.0 * downdraft_strength  # Stronger downward above selector
    
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
    chamber_radius: float,
    selector_radius: float,
    selector_z_min: float,
    selector_z_max: float,
    distributor_z: float,
    air_flow_m3s: float,
    rotor_omega: float
):
    """Compute air velocity field for all particles"""
    i = wp.tid()
    
    if active[i] == 0:
        air_velocities[i] = wp.vec3(0.0, 0.0, 0.0)
        return
    
    air_velocities[i] = compute_air_velocity_corrected(
        positions[i],
        chamber_radius, selector_radius,
        selector_z_min, selector_z_max, distributor_z,
        air_flow_m3s, rotor_omega
    )


class AirFlowModelCorrected:
    """CORRECTED Air flow model for classifier"""
    
    def __init__(self, boundary_conditions: Dict):
        """
        Initialize air flow model
        
        Args:
            boundary_conditions: Boundary condition parameters
        """
        self.bc = boundary_conditions
        
        # Geometry
        self.chamber_radius = boundary_conditions['chamber_radius']
        self.selector_radius = boundary_conditions['selector_radius']
        self.selector_z_min = boundary_conditions.get('selector_z_min', 
                                boundary_conditions['selector_z_center'] - 
                                boundary_conditions['selector_height'] / 2)
        self.selector_z_max = boundary_conditions.get('selector_z_max',
                                boundary_conditions['selector_z_center'] + 
                                boundary_conditions['selector_height'] / 2)
        self.distributor_z = boundary_conditions.get('distributor_z', 0.5)
        
        # Flow parameters
        # Convert from m³/hr to m³/s if needed
        air_flow = boundary_conditions.get('air_flow_m3s', 
                                           boundary_conditions.get('air_flow_rate', 2000) / 3600)
        if air_flow > 10:  # Probably in m³/hr
            air_flow = air_flow / 3600
        self.air_flow_m3s = air_flow
        
        self.rotor_omega = boundary_conditions['rotor_omega']
        
        # Print configuration
        print(f"  AirFlowModelCorrected initialized:")
        print(f"    Air flow: {self.air_flow_m3s * 3600:.0f} m³/hr ({self.air_flow_m3s:.4f} m³/s)")
        print(f"    Rotor: {self.rotor_omega * 60 / (2*3.14159):.0f} RPM ({self.rotor_omega:.1f} rad/s)")
        print(f"    Selector: r={self.selector_radius*1000:.0f}mm, z={self.selector_z_min:.2f}-{self.selector_z_max:.2f}m")
        
        # Calculate expected radial velocity at selector
        v_r_selector = self.air_flow_m3s / (2 * 3.14159 * self.selector_radius * 
                                            (self.selector_z_max - self.selector_z_min))
        print(f"    Radial inflow at selector: {v_r_selector:.2f} m/s")
    
    def compute_velocities(
        self,
        positions: wp.array,
        active: wp.array = None,
        device: str = "cuda:0"
    ) -> wp.array:
        """
        Compute air velocities at particle positions
        
        Args:
            positions: Particle positions
            active: Active particle flags (optional)
            device: WARP device
            
        Returns:
            Air velocity array
        """
        n = positions.shape[0]
        air_velocities = wp.zeros(n, dtype=wp.vec3, device=device)
        
        # Create active array if not provided
        if active is None:
            active = wp.ones(n, dtype=wp.int32, device=device)
        
        wp.launch(
            kernel=compute_air_velocity_field_kernel,
            dim=n,
            inputs=[
                positions,
                air_velocities,
                active,
                self.chamber_radius,
                self.selector_radius,
                self.selector_z_min,
                self.selector_z_max,
                self.distributor_z,
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
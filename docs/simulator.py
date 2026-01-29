"""
GPU-Accelerated Air Classifier Simulation using NVIDIA Warp
For Yellow Pea Protein Separation

Based on comprehensive engineering design guide
"""

import warp as wp
import numpy as np
from typing import Optional, Dict, Tuple
import time

from .config import ClassifierConfig, ParticleProperties, SimulationConfig

# Initialize Warp
wp.init()


@wp.func
def compute_drag_force(
    velocity_rel: wp.vec3,
    diameter: float,
    particle_density: float,
    air_density: float,
    air_viscosity: float
) -> wp.vec3:
    """
    Compute drag force on a spherical particle
    Using Schiller-Naumann correlation for intermediate Reynolds numbers
    """
    vel_mag = wp.length(velocity_rel)

    if vel_mag < 1e-10:
        return wp.vec3(0.0, 0.0, 0.0)

    # Reynolds number
    Re = air_density * vel_mag * diameter / air_viscosity

    # Drag coefficient (Schiller-Naumann)
    if Re < 0.1:
        Cd = 24.0 / (Re + 1e-10)
    elif Re < 1000.0:
        Cd = 24.0 / Re * (1.0 + 0.15 * wp.pow(Re, 0.687))
    else:
        Cd = 0.44

    # Drag force magnitude
    area = 0.25 * 3.14159265359 * diameter * diameter
    F_mag = 0.5 * Cd * air_density * vel_mag * vel_mag * area

    # Direction opposite to relative velocity
    return -velocity_rel * (F_mag / vel_mag)


@wp.func
def compute_air_velocity_field(
    pos: wp.vec3,
    wheel_radius: float,
    wheel_z: float,
    wheel_width: float,
    air_vel_radial: float,
    wheel_omega: float,
    collection_threshold_fine: float,
    collection_threshold_coarse: float
) -> wp.vec3:
    """
    Compute air velocity at a given position
    Model includes:
    - Radial inflow toward classifier wheel
    - Tangential component from wheel rotation
    - Axial flow through wheel for fine particles
    """
    # Cylindrical coordinates
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    theta = wp.atan2(pos[1], pos[0])
    z = pos[2]

    # Radial unit vector (pointing inward)
    er = wp.vec3(-pos[0] / (r + 1e-10), -pos[1] / (r + 1e-10), 0.0)

    # Tangential unit vector
    et = wp.vec3(-wp.sin(theta), wp.cos(theta), 0.0)

    # Distance from wheel plane
    z_dist = wp.abs(z - wheel_z)
    # Wider vertical extent for air flow influence
    radial_factor = wp.exp(-z_dist / (wheel_width * 4.0))

    # Radial velocity (inward flow, stronger near wheel)
    # Velocity scales as 1/r to conserve mass
    # VERY strong radial flow to draw particles inward from feed zone
    # ENHANCED: Even stronger to pull particles from outer regions
    radial_strength = 3.5  # Increased from 2.5
    if r > wheel_radius:
        v_radial = air_vel_radial * radial_strength * radial_factor * (wheel_radius / r)
    else:
        v_radial = air_vel_radial * radial_strength * radial_factor

    # Tangential velocity (from wheel rotation)
    # Decays exponentially with distance from wheel
    if r < wheel_radius * 2.5 and z_dist < wheel_width * 3.0:
        # Inside wheel: solid body rotation
        if r < wheel_radius:
            v_tangential = wheel_omega * r * radial_factor
        # Outside wheel: decaying rotation
        else:
            decay = wp.exp(-(r - wheel_radius) / wheel_radius)
            v_tangential = wheel_omega * wheel_radius * decay * radial_factor
    else:
        v_tangential = 0.0

    # Axial velocity (upward through wheel for fines, downward elsewhere for coarse)
    # Based on air classifier design: strong upward axial flow through wheel center
    # ENHANCED: Much stronger flow to push particles toward collection zones and break circulation
    if r < wheel_radius * 0.93:
        # Strong upward axial flow through wheel for fine particles
        # This carries small particles up to the fine outlet
        # Flow is strong across full height range to pull particles from feed zone
        radial_position_factor = 1.0 - (r / (wheel_radius * 0.93))

        # Height-dependent factor: MUCH stronger to push particles to extremes
        # EXTRA STRONG near collection threshold to ensure particles reach it
        if z > collection_threshold_fine * 0.9:
            # Very close to fine collection zone - extra strong upward push
            height_factor = 2.2  # Increased from 2.0
        elif z > wheel_z + wheel_width * 0.5:
            height_factor = 2.0  # Increased from 1.8 - even stronger above wheel
        elif z > wheel_z - wheel_width * 0.5:
            height_factor = 1.7  # Increased from 1.5 - stronger at wheel level
        elif z > collection_threshold_coarse * 2.0:
            # Middle zone - push upward VERY strongly to break circulation
            height_factor = 1.5 + 0.4 * wp.exp(-(wheel_z - z) / (wheel_width * 2.0))
        else:
            # Below wheel but above coarse threshold - strong upward flow
            height_factor = 1.0 + 0.5 * wp.exp(-(wheel_z - z) / (wheel_width * 3.0))

        v_axial = 35.0 * radial_position_factor * height_factor  # Increased from 32.0
    elif r > wheel_radius * 1.15:
        # Strong downward flow in outer annular region for coarse particles
        # These particles are rejected by centrifugal force and must settle
        # EXTRA STRONG near bottom to ensure collection
        if z < collection_threshold_coarse * 2.0:
            # Close to coarse collection zone - extra strong downward push
            v_axial = -14.0  # Increased from -12.0
        elif z < wheel_z - wheel_width:
            # Below wheel in outer region - strong downward
            v_axial = -12.0  # Increased from -10.0
        else:
            # Outer region above wheel - still push down to break circulation
            v_axial = -10.0  # Increased from -8.0
    else:
        # Transition zone between wheel and outer region (r = 0.93*R to 1.15*R)
        # Make this zone push particles more decisively
        transition_factor = (r - wheel_radius * 0.93) / (wheel_radius * 0.22)
        # Interpolate: upward at inner edge, strong downward at outer edge
        if z > wheel_z:
            # Above wheel in transition - push upward if close to center, down if far
            v_axial = 2.0 - transition_factor * 10.0
        else:
            # Below wheel in transition - push downward
            v_axial = -2.0 - transition_factor * 8.0

    return er * v_radial + et * v_tangential + wp.vec3(0.0, 0.0, v_axial)


@wp.kernel
def initialize_particles_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    densities: wp.array(dtype=float),
    particle_types: wp.array(dtype=int),  # 0=protein, 1=starch
    active: wp.array(dtype=int),
    feed_height: float,
    feed_radius_min: float,
    feed_radius_max: float,
    seed: int
):
    """Initialize particles at feed location with random positions"""
    i = wp.tid()

    # Random position in annular feed zone
    state = wp.rand_init(seed, i)

    r = feed_radius_min + wp.randf(state) * (feed_radius_max - feed_radius_min)
    theta = wp.randf(state) * 2.0 * 3.14159265359
    z = feed_height + (wp.randf(state) - 0.5) * 0.05  # Small vertical spread

    positions[i] = wp.vec3(r * wp.cos(theta), r * wp.sin(theta), z)

    # Initial velocity - small downward and inward
    velocities[i] = wp.vec3(
        -wp.cos(theta) * 0.5,
        -wp.sin(theta) * 0.5,
        -0.5
    )

    # All particles start active
    active[i] = 1


@wp.kernel
def update_particles_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    densities: wp.array(dtype=float),
    active: wp.array(dtype=int),
    forces: wp.array(dtype=wp.vec3),
    wheel_radius: float,
    wheel_z: float,
    wheel_width: float,
    wheel_omega: float,
    air_vel_radial: float,
    air_density: float,
    air_viscosity: float,
    dt: float,
    collection_threshold_fine: float,
    collection_threshold_coarse: float
):
    """Update particle positions and velocities"""
    i = wp.tid()

    # Skip inactive particles
    if active[i] == 0:
        return

    pos = positions[i]
    vel = velocities[i]
    d = diameters[i]
    rho = densities[i]

    # Particle mass
    volume = (4.0 / 3.0) * 3.14159265359 * wp.pow(d / 2.0, 3.0)
    mass = rho * volume

    # Air velocity at particle position
    air_vel = compute_air_velocity_field(
        pos, wheel_radius, wheel_z, wheel_width,
        air_vel_radial, wheel_omega,
        collection_threshold_fine, collection_threshold_coarse
    )

    # Relative velocity
    vel_rel = vel - air_vel

    # Drag force
    F_drag = compute_drag_force(vel_rel, d, rho, air_density, air_viscosity)

    # Gravity
    F_gravity = wp.vec3(0.0, 0.0, -9.81 * mass)

    # Centrifugal force (in rotating frame near wheel)
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z_dist = wp.abs(pos[2] - wheel_z)

    # Apply centrifugal force if near wheel
    # This is the KEY separation mechanism: pushes large/heavy particles outward
    if r < wheel_radius * 2.5 and z_dist < wheel_width * 4.0:
        # Local angular velocity decreases with distance from wheel
        z_factor = wp.exp(-z_dist / (wheel_width * 2.0))

        if r < wheel_radius * 0.95:
            # Inside wheel: solid body rotation at full speed
            omega_local = wheel_omega * z_factor
        else:
            # Outside wheel: decaying rotation but still significant
            decay = wp.exp(-(r - wheel_radius) / (wheel_radius * 0.6))
            omega_local = wheel_omega * decay * z_factor

        # Centrifugal acceleration: ω²r (this separates particles by mass/size)
        # Larger particles experience stronger outward push
        centrifugal_accel = omega_local * omega_local
        F_centrifugal = wp.vec3(pos[0], pos[1], 0.0) * (mass * centrifugal_accel / (r + 1e-10))
    else:
        F_centrifugal = wp.vec3(0.0, 0.0, 0.0)

    # Total force
    F_total = F_drag + F_gravity + F_centrifugal
    forces[i] = F_total

    # Update velocity (semi-implicit Euler)
    acc = F_total / mass
    vel_new = vel + acc * dt
    
    # DAMPING: Break circulation patterns for particles stuck in middle zone
    # If particle is in middle zone (between thresholds) and has high tangential velocity,
    # apply damping to help it move toward collection zones
    z = pos[2]
    if z > collection_threshold_coarse * 1.5 and z < collection_threshold_fine * 0.9:
        # Middle zone - apply damping to tangential velocity to break circulation
        # Calculate tangential velocity component
        v_tangential_mag = wp.sqrt(vel_new[0] * vel_new[0] + vel_new[1] * vel_new[1])
        if v_tangential_mag > 2.0:  # Only damp if tangential velocity is high
            # Damp tangential velocity by 5% per step to gradually break circulation
            damping_factor = 0.95
            vel_new = wp.vec3(
                vel_new[0] * damping_factor,
                vel_new[1] * damping_factor,
                vel_new[2]  # Don't damp axial velocity - we want particles to move vertically
            )
    
    velocities[i] = vel_new

    # Update position
    positions[i] = pos + vel_new * dt


@wp.kernel
def apply_boundaries_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    particle_types: wp.array(dtype=int),
    active: wp.array(dtype=int),
    collected_fine: wp.array(dtype=int),
    collected_coarse: wp.array(dtype=int),
    collection_time: wp.array(dtype=float),
    collection_position: wp.array(dtype=wp.vec3),
    collection_outlet: wp.array(dtype=int),  # 0=not collected, 1=fine, 2=coarse
    chamber_radius: float,
    chamber_height: float,
    wheel_radius: float,
    wheel_z: float,
    wheel_width: float,
    collection_threshold_fine: float,
    collection_threshold_coarse: float,
    current_time: float
):
    """Apply boundary conditions and track particle collection"""
    i = wp.tid()

    # Skip inactive particles
    if active[i] == 0:
        return

    pos = positions[i]
    vel = velocities[i]

    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z = pos[2]

    # PRIMARY COLLECTION ZONES (based on air classifier engineering design)

    # FINE FRACTION: Particles that pass through wheel and exit at top
    # According to design guide: fine particles follow axial flow upward through wheel
    # EXPANDED: Collect particles that reach high z OR are near center at moderate height
    # This prevents particles from bouncing back down when they reach the top
    fine_collected = False
    if z > collection_threshold_fine:
        # High altitude: collect if near center OR anywhere above threshold
        if r < wheel_radius * 1.3:  # Expanded radius for high-altitude collection
            wp.atomic_add(collected_fine, 0, 1)
            active[i] = 0
            collection_time[i] = current_time
            collection_position[i] = pos
            collection_outlet[i] = 1
            fine_collected = True
    elif z > collection_threshold_fine * 0.95 and r < wheel_radius * 0.9:
        # Very close to top threshold and very close to center (excludes feed zone)
        # Feed zone is at z≈0.88m, so z>0.95m ensures we're well above feed zone
        wp.atomic_add(collected_fine, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 1
        fine_collected = True
    elif z > collection_threshold_fine * 0.92 and r < wheel_radius * 0.7 and vel[2] > 1.0:
        # Close to threshold, very close to center, AND moving upward strongly
        # This helps collect particles that are clearly moving toward fine zone
        wp.atomic_add(collected_fine, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 1
        fine_collected = True
    
    if fine_collected:
        return

    # COARSE FRACTION: Particles rejected by centrifugal force, fall to bottom
    # According to design guide: coarse particles settle to bottom cone
    # EXPANDED: Collect particles that reach low z OR are in outer region at low height
    if z < collection_threshold_coarse:
        # Particle reaches bottom -> coarse fraction
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return
    elif z < collection_threshold_coarse * 1.5 and r > wheel_radius * 1.2:
        # Low altitude and far from center: likely coarse particle
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return
    elif z < collection_threshold_coarse * 1.8 and r > wheel_radius * 1.3 and vel[2] < -1.0:
        # Close to coarse threshold, far from center, AND moving downward strongly
        # This helps collect particles that are clearly moving toward coarse zone
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return

    # FALLBACK: Collect particles stuck in middle region - CONSERVATIVE for fine to preserve purity
    # Fine: only very close to threshold or size-based (avoid pulling starch into fine)
    if z > collection_threshold_fine * 0.98 and r < wheel_radius * 0.6:
        # Almost at fine threshold (z > 0.98m), very close to center -> fine
        wp.atomic_add(collected_fine, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 1
        return
    
    # Coarse particles: below wheel, far from center (position-only is OK for coarse)
    if z < collection_threshold_coarse * 1.2 and r > wheel_radius * 1.4:
        # Almost at coarse threshold (z < 0.12m), far from center -> coarse
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return
    elif z < wheel_z - wheel_width * 1.5 and r > wheel_radius * 1.25:
        # Well below wheel (z < 0.81m), far from center -> coarse
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return
    elif z < collection_threshold_coarse * 2.5 and r > wheel_radius * 1.35:
        # Low altitude (z < 0.25m), far from center -> coarse
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return
    
    # SIZE-BASED COLLECTION: For particles truly stuck, use size and position
    # Small particles (likely fine/protein) near center -> fine
    # Large particles (likely coarse/starch) far from center -> coarse
    # Target cut size is ~20 micrometers, so use that as threshold
    d = diameters[i]
    target_cut_size = 20e-6  # 20 micrometers
    
    # Fine: small particles above wheel and close to center (size-based preserves purity)
    if d < target_cut_size * 1.5 and z > wheel_z and r < wheel_radius * 0.9:
        # Small particle, above wheel, close to center -> fine
        wp.atomic_add(collected_fine, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 1
        return
    
    # Coarse: large particles below wheel and far from center
    if d > target_cut_size * 0.8 and z < wheel_z and r > wheel_radius * 1.2:
        # Large particle, below wheel, far from center -> coarse
        wp.atomic_add(collected_coarse, 0, 1)
        active[i] = 0
        collection_time[i] = current_time
        collection_position[i] = pos
        collection_outlet[i] = 2
        return

    # BOUNDARY CONDITIONS

    # Cylindrical wall boundary
    if r > chamber_radius * 0.98:
        # Reflect with damping
        normal = wp.vec3(pos[0] / r, pos[1] / r, 0.0)
        v_normal = wp.dot(vel, normal)
        if v_normal > 0.0:
            velocities[i] = vel - 1.8 * v_normal * normal  # Slight damping

        # Push inside
        scale = chamber_radius * 0.96 / r
        positions[i] = wp.vec3(pos[0] * scale, pos[1] * scale, pos[2])

    # Top boundary (above collection zone)
    # Only redirect particles that are clearly outside fine collection zone
    # Particles near center at top should be collected, not redirected
    if z > chamber_height * 0.99:
        if r >= wheel_radius * 1.4:  # Only redirect if well outside collection zone
            positions[i] = wp.vec3(pos[0], pos[1], chamber_height * 0.98)
            if vel[2] > 0.0:
                velocities[i] = wp.vec3(vel[0], vel[1], -vel[2] * 0.5)


class AirClassifierSimulator:
    """
    Main simulator class for air classifier
    Simulates particle separation in turbine-type air classifier
    """

    def __init__(
        self,
        classifier_config: ClassifierConfig,
        particle_props: ParticleProperties,
        sim_config: SimulationConfig
    ):
        self.classifier_config = classifier_config
        self.particle_props = particle_props
        self.sim_config = sim_config
        self.device = sim_config.device

        # Simulation state
        self.current_time = 0.0
        self.step_count = 0

        # Angular velocity
        self.wheel_omega = classifier_config.wheel_rpm * 2.0 * np.pi / 60.0

        # Allocate arrays
        n = classifier_config.num_particles
        self.positions = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.velocities = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.forces = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.diameters = wp.zeros(n, dtype=float, device=self.device)
        self.densities = wp.zeros(n, dtype=float, device=self.device)
        self.particle_types = wp.zeros(n, dtype=int, device=self.device)
        self.active = wp.ones(n, dtype=int, device=self.device)

        # Collection tracking
        self.collected_fine = wp.zeros(1, dtype=int, device=self.device)
        self.collected_coarse = wp.zeros(1, dtype=int, device=self.device)
        self.collection_time = wp.zeros(n, dtype=float, device=self.device)
        self.collection_position = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.collection_outlet = wp.zeros(n, dtype=int, device=self.device)  # 0=not collected, 1=fine, 2=coarse

        # Initialize particles
        self._initialize_particles()

        print(f"Air Classifier Simulator initialized")
        print(f"  Particles: {n}")
        print(f"  Wheel RPM: {classifier_config.wheel_rpm}")
        print(f"  Target cut size: {particle_props.target_cut_size*1e6:.1f} μm")
        print(f"  Device: {self.device}")

    def _initialize_particles(self):
        """Initialize particle properties and positions"""
        n = self.classifier_config.num_particles
        n_protein = int(n * self.particle_props.protein_fraction)
        n_starch = n - n_protein

        # Generate particle sizes (log-normal distribution)
        np.random.seed(42)

        # Protein particles
        protein_diameters = np.random.lognormal(
            np.log(self.particle_props.protein_diameter_mean),
            0.4, n_protein
        ).astype(np.float32)
        protein_diameters = np.clip(protein_diameters, 1e-6, 15e-6)

        # Starch particles
        starch_diameters = np.random.lognormal(
            np.log(self.particle_props.starch_diameter_mean),
            0.3, n_starch
        ).astype(np.float32)
        starch_diameters = np.clip(starch_diameters, 10e-6, 60e-6)

        # Combine
        all_diameters = np.concatenate([protein_diameters, starch_diameters])
        all_densities = np.concatenate([
            np.full(n_protein, self.particle_props.protein_density, dtype=np.float32),
            np.full(n_starch, self.particle_props.starch_density, dtype=np.float32)
        ])
        all_types = np.concatenate([
            np.zeros(n_protein, dtype=np.int32),
            np.ones(n_starch, dtype=np.int32)
        ])

        # Shuffle
        indices = np.random.permutation(n)
        all_diameters = all_diameters[indices]
        all_densities = all_densities[indices]
        all_types = all_types[indices]

        # Copy to device
        self.diameters.assign(all_diameters)
        self.densities.assign(all_densities)
        self.particle_types.assign(all_types)

        # Initialize positions
        wp.launch(
            initialize_particles_kernel,
            dim=n,
            inputs=[
                self.positions, self.velocities,
                self.diameters, self.densities, self.particle_types,
                self.active,
                self.sim_config.feed_height,
                self.sim_config.feed_radius_min,
                self.sim_config.feed_radius_max,
                42
            ],
            device=self.device
        )

    def step(self):
        """Perform one simulation time step"""
        # Update particles
        wp.launch(
            update_particles_kernel,
            dim=self.classifier_config.num_particles,
            inputs=[
                self.positions, self.velocities,
                self.diameters, self.densities,
                self.active, self.forces,
                self.classifier_config.wheel_radius,
                self.classifier_config.wheel_position_z,
                self.classifier_config.wheel_width,
                self.wheel_omega,
                self.classifier_config.air_velocity,
                self.sim_config.air_density,
                self.sim_config.air_viscosity,
                self.classifier_config.dt,
                self.sim_config.collection_threshold_fine,
                self.sim_config.collection_threshold_coarse
            ],
            device=self.device
        )

        # Apply boundaries
        wp.launch(
            apply_boundaries_kernel,
            dim=self.classifier_config.num_particles,
            inputs=[
                self.positions, self.velocities,
                self.diameters, self.particle_types,
                self.active,
                self.collected_fine, self.collected_coarse,
                self.collection_time, self.collection_position,
                self.collection_outlet,
                self.classifier_config.chamber_radius,
                self.classifier_config.chamber_height,
                self.classifier_config.wheel_radius,
                self.classifier_config.wheel_position_z,
                self.classifier_config.wheel_width,
                self.sim_config.collection_threshold_fine,
                self.sim_config.collection_threshold_coarse,
                self.current_time
            ],
            device=self.device
        )

        self.current_time += self.classifier_config.dt
        self.step_count += 1

    def get_state(self) -> Dict:
        """Get current simulation state"""
        return {
            'time': self.current_time,
            'step': self.step_count,
            'positions': self.positions.numpy(),
            'velocities': self.velocities.numpy(),
            'diameters': self.diameters.numpy(),
            'densities': self.densities.numpy(),
            'particle_types': self.particle_types.numpy(),
            'active': self.active.numpy(),
            'collected_fine': self.collected_fine.numpy()[0],
            'collected_coarse': self.collected_coarse.numpy()[0],
            'collection_time': self.collection_time.numpy(),
            'collection_position': self.collection_position.numpy(),
            'collection_outlet': self.collection_outlet.numpy()  # 0=not collected, 1=fine, 2=coarse
        }

    def run(self, duration: Optional[float] = None,
            output_interval: Optional[float] = None) -> Dict:
        """
        Run simulation for specified duration

        Args:
            duration: Simulation time (uses config if None)
            output_interval: Time between outputs (uses config if None)

        Returns:
            Dictionary with simulation results
        """
        if duration is None:
            duration = self.sim_config.total_time
        if output_interval is None:
            output_interval = self.sim_config.output_interval

        steps = int(duration / self.classifier_config.dt)
        output_steps = int(output_interval / self.classifier_config.dt)

        results = {
            'time': [],
            'fine_collected': [],
            'coarse_collected': [],
            'active_count': []
        }

        print(f"\nRunning simulation for {duration}s ({steps} steps)...")
        start_time = time.time()

        for step in range(steps):
            self.step()

            if step % output_steps == 0 or step == steps - 1:
                state = self.get_state()
                n_active = np.sum(state['active'])

                results['time'].append(state['time'])
                results['fine_collected'].append(state['collected_fine'])
                results['coarse_collected'].append(state['collected_coarse'])
                results['active_count'].append(n_active)

                if step % (output_steps * 5) == 0:
                    print(f"  t={state['time']:.3f}s: "
                          f"Active={n_active}, "
                          f"Fine={state['collected_fine']}, "
                          f"Coarse={state['collected_coarse']}")

                # Early termination if all particles collected
                if n_active == 0:
                    print(f"  All particles collected at t={state['time']:.3f}s")
                    break

        # Final state
        results['final_state'] = self.get_state()

        elapsed = time.time() - start_time
        print(f"\nSimulation complete in {elapsed:.2f}s")
        print(f"  Steps per second: {steps/elapsed:.0f}")

        return results

"""
Core physics module with Warp kernels for droplet dynamics

Implements:
- Gravity
- Aerodynamic drag (Stokes and turbulent regimes)
- Wind forcing
- Evaporation
- Deposition detection
"""

import warp as wp
import numpy as np
from typing import Optional, Dict
from .config import SprayConfig, WindConfig, SimulationConfig


# Initialize Warp
wp.init()


@wp.func
def compute_drag_coefficient(reynolds: float) -> float:
    """
    Compute drag coefficient based on Reynolds number
    Uses Schiller-Naumann correlation for spheres
    """
    if reynolds < 0.01:
        # Stokes regime
        return 24.0 / wp.max(reynolds, 0.001)
    elif reynolds < 1000.0:
        # Intermediate regime (Schiller-Naumann)
        return 24.0 / reynolds * (1.0 + 0.15 * wp.pow(reynolds, 0.687))
    else:
        # Turbulent regime
        return 0.44


@wp.func
def wind_velocity_profile(z: float, wind_speed_ref: float, z_ref: float, roughness: float, exponent: float) -> float:
    """
    Compute wind speed at height z using power law
    u(z) = u_ref * (z / z_ref)^exponent
    """
    if z <= roughness:
        return 0.0

    return wind_speed_ref * wp.pow(z / z_ref, exponent)


@wp.kernel
def initialize_droplets_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    masses: wp.array(dtype=float),
    active: wp.array(dtype=int),
    nozzle_x: float,
    nozzle_y: float,
    nozzle_z: float,
    initial_velocity: float,
    spray_angle_rad: float,
    liquid_density: float,
    seed: int
):
    """
    Initialize droplet positions, velocities, and properties
    """
    i = wp.tid()

    # Random state for this droplet
    state = wp.rand_init(seed + i)

    # Start at nozzle position
    positions[i] = wp.vec3(nozzle_x, nozzle_y, nozzle_z)

    # Random direction within spray cone
    # Spherical coordinates
    theta = wp.randf(state, 0.0, spray_angle_rad)  # Angle from vertical
    phi = wp.randf(state, 0.0, 2.0 * 3.14159265)   # Azimuthal angle

    # Convert to Cartesian (downward spray = negative z)
    sin_theta = wp.sin(theta)
    vx = initial_velocity * sin_theta * wp.cos(phi)
    vy = initial_velocity * sin_theta * wp.sin(phi)
    vz = -initial_velocity * wp.cos(theta)

    velocities[i] = wp.vec3(vx, vy, vz)

    # Diameter already set externally (from distribution)
    d = diameters[i]

    # Compute droplet mass (sphere)
    volume = 3.14159265 / 6.0 * d * d * d
    masses[i] = liquid_density * volume

    # Mark as active
    active[i] = 1


@wp.kernel
def compute_forces_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    masses: wp.array(dtype=float),
    forces: wp.array(dtype=wp.vec3),
    active: wp.array(dtype=int),
    # Wind parameters
    wind_speed_ref: float,
    wind_direction_x: float,
    wind_direction_y: float,
    z_ref: float,
    roughness: float,
    power_exponent: float,
    turbulence_intensity: float,
    # Physical properties
    air_density: float,
    air_viscosity: float,
    gravity: float,
    time: float,
    gust_amplitude: float,
    gust_period: float,
    seed: int
):
    """
    Compute forces on each droplet:
    - Gravity
    - Aerodynamic drag
    - Wind forcing
    """
    i = wp.tid()

    if active[i] == 0:
        forces[i] = wp.vec3(0.0, 0.0, 0.0)
        return

    pos = positions[i]
    vel = velocities[i]
    d = diameters[i]
    m = masses[i]

    # Gravity force
    f_gravity = wp.vec3(0.0, 0.0, -gravity * m)

    # Wind velocity at droplet height
    wind_speed = wind_velocity_profile(pos[2], wind_speed_ref, z_ref, roughness, power_exponent)

    # Add gust
    gust = gust_amplitude * wp.sin(2.0 * 3.14159265 * time / gust_period)
    wind_speed += gust

    # Add turbulence (random component)
    state = wp.rand_init(seed + i * 1000 + int(time * 100.0))
    turb_x = wp.randf(state, -1.0, 1.0) * turbulence_intensity * wind_speed
    turb_y = wp.randf(state, -1.0, 1.0) * turbulence_intensity * wind_speed
    turb_z = wp.randf(state, -1.0, 1.0) * turbulence_intensity * wind_speed * 0.3  # Reduced vertical

    wind_vel = wp.vec3(
        wind_speed * wind_direction_x + turb_x,
        wind_speed * wind_direction_y + turb_y,
        turb_z
    )

    # Relative velocity (air relative to droplet)
    v_rel = wind_vel - vel
    v_rel_mag = wp.length(v_rel)

    # Drag force
    if v_rel_mag > 0.001:
        # Reynolds number
        Re = air_density * v_rel_mag * d / air_viscosity

        # Drag coefficient
        Cd = compute_drag_coefficient(Re)

        # Cross-sectional area
        A = 3.14159265 * d * d / 4.0

        # Drag force magnitude
        f_drag_mag = 0.5 * Cd * air_density * A * v_rel_mag * v_rel_mag

        # Drag force vector (direction of relative velocity)
        f_drag = v_rel * (f_drag_mag / v_rel_mag)
    else:
        f_drag = wp.vec3(0.0, 0.0, 0.0)

    # Total force
    forces[i] = f_gravity + f_drag


@wp.kernel
def integrate_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    forces: wp.array(dtype=wp.vec3),
    masses: wp.array(dtype=float),
    active: wp.array(dtype=int),
    dt: float
):
    """
    Time integration using semi-implicit Euler
    """
    i = wp.tid()

    if active[i] == 0:
        return

    m = masses[i]
    acc = forces[i] / m

    # Update velocity
    vel_new = velocities[i] + acc * dt
    velocities[i] = vel_new

    # Update position
    positions[i] = positions[i] + vel_new * dt


@wp.kernel
def check_deposition_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    active: wp.array(dtype=int),
    deposition_time: wp.array(dtype=float),
    deposition_position: wp.array(dtype=wp.vec3),
    ground_level: float,
    canopy_height: float,
    capture_distance: float,
    domain_x_min: float,
    domain_x_max: float,
    domain_y_min: float,
    domain_y_max: float,
    current_time: float
):
    """
    Check for droplet deposition or domain exit
    """
    i = wp.tid()

    if active[i] == 0:
        return

    pos = positions[i]

    # Check ground deposition
    deposition_height = ground_level + canopy_height

    if pos[2] <= deposition_height + capture_distance:
        active[i] = 0
        deposition_time[i] = current_time
        deposition_position[i] = wp.vec3(pos[0], pos[1], deposition_height)
        return

    # Check domain boundaries (lost to drift)
    if pos[0] < domain_x_min or pos[0] > domain_x_max:
        active[i] = 0
        deposition_time[i] = -1.0  # Mark as lost
        return

    if pos[1] < domain_y_min or pos[1] > domain_y_max:
        active[i] = 0
        deposition_time[i] = -1.0
        return


@wp.kernel
def evaporation_kernel(
    diameters: wp.array(dtype=float),
    masses: wp.array(dtype=float),
    positions: wp.array(dtype=wp.vec3),
    active: wp.array(dtype=int),
    liquid_density: float,
    temperature: float,
    relative_humidity: float,
    vapor_pressure_sat: float,
    diffusion_coeff: float,
    dt: float
):
    """
    Evaporation using simplified Maxwell equation
    dm/dt = 2πD·d·Mw·(Psat·(1-RH))/(R·T)
    """
    i = wp.tid()

    if active[i] == 0:
        return

    d = diameters[i]
    m = masses[i]

    # Evaporation rate constant
    # Simplified: k = 2π·D·d where D is diffusion coefficient
    R_gas = 8.314  # J/(mol·K)
    Mw = 0.018     # kg/mol (water)

    # Vapor pressure deficit
    P_deficit = vapor_pressure_sat * (1.0 - relative_humidity)

    # Mass loss rate (kg/s)
    dm_dt = 2.0 * 3.14159265 * diffusion_coeff * d * Mw * P_deficit / (R_gas * temperature)

    # Update mass
    m_new = m - dm_dt * dt

    # Ensure non-negative
    if m_new <= 0.0:
        # Droplet completely evaporated
        active[i] = 0
        return

    masses[i] = m_new

    # Update diameter (maintain density)
    volume_new = m_new / liquid_density
    d_new = wp.pow(6.0 * volume_new / 3.14159265, 1.0/3.0)
    diameters[i] = d_new


class DropletSimulator:
    """
    Main simulator class for spray drift dynamics
    """

    def __init__(
        self,
        spray_config: SprayConfig,
        wind_config: WindConfig,
        sim_config: SimulationConfig
    ):
        self.spray = spray_config
        self.wind = wind_config
        self.sim = sim_config

        self.num_droplets = spray_config.num_droplets
        self.device = sim_config.device

        # Allocate arrays
        self.positions = wp.zeros(self.num_droplets, dtype=wp.vec3, device=self.device)
        self.velocities = wp.zeros(self.num_droplets, dtype=wp.vec3, device=self.device)
        self.forces = wp.zeros(self.num_droplets, dtype=wp.vec3, device=self.device)
        self.diameters = wp.zeros(self.num_droplets, dtype=float, device=self.device)
        self.masses = wp.zeros(self.num_droplets, dtype=float, device=self.device)
        self.active = wp.zeros(self.num_droplets, dtype=int, device=self.device)

        # Deposition tracking
        self.deposition_time = wp.zeros(self.num_droplets, dtype=float, device=self.device)
        self.deposition_position = wp.zeros(self.num_droplets, dtype=wp.vec3, device=self.device)

        # Time
        self.current_time = 0.0
        self.step_count = 0

        # Random seed
        self.seed = np.random.randint(0, 1000000)

        # Wind direction unit vector
        wind_dir_rad = np.deg2rad(wind_config.wind_direction)
        self.wind_dir_x = np.sin(wind_dir_rad)  # East component
        self.wind_dir_y = np.cos(wind_dir_rad)  # North component

        self._initialize()

    def _initialize(self):
        """Initialize droplet properties and positions"""
        # Generate droplet diameter distribution (log-normal)
        diameters_np = np.random.normal(
            self.spray.droplet_diameter_mean,
            self.spray.droplet_diameter_std,
            self.num_droplets
        )

        # Clip to physical range
        diameters_np = np.clip(
            diameters_np,
            self.spray.droplet_diameter_min,
            self.spray.droplet_diameter_max
        )

        # Copy to device
        wp.copy(self.diameters, wp.array(diameters_np, dtype=float, device=self.device))

        # Initialize positions and velocities
        spray_angle_rad = np.deg2rad(self.spray.spray_angle)

        wp.launch(
            kernel=initialize_droplets_kernel,
            dim=self.num_droplets,
            inputs=[
                self.positions,
                self.velocities,
                self.diameters,
                self.masses,
                self.active,
                self.spray.nozzle_position[0],
                self.spray.nozzle_position[1],
                self.spray.nozzle_height,
                self.spray.initial_velocity,
                spray_angle_rad,
                self.spray.liquid_density,
                self.seed
            ],
            device=self.device
        )

        wp.synchronize()

    def step(self, dt: Optional[float] = None):
        """
        Perform one simulation time step
        """
        if dt is None:
            dt = self.sim.dt

        # 1. Compute forces
        wp.launch(
            kernel=compute_forces_kernel,
            dim=self.num_droplets,
            inputs=[
                self.positions,
                self.velocities,
                self.diameters,
                self.masses,
                self.forces,
                self.active,
                self.wind.wind_speed,
                self.wind_dir_x,
                self.wind_dir_y,
                self.wind.reference_height,
                self.wind.surface_roughness,
                self.wind.power_law_exponent,
                self.wind.turbulence_intensity,
                self.sim.air_density,
                self.sim.air_viscosity,
                self.sim.gravity,
                self.current_time,
                self.wind.gust_amplitude,
                self.wind.gust_period,
                self.seed
            ],
            device=self.device
        )

        # 2. Integrate motion
        wp.launch(
            kernel=integrate_kernel,
            dim=self.num_droplets,
            inputs=[
                self.positions,
                self.velocities,
                self.forces,
                self.masses,
                self.active,
                dt
            ],
            device=self.device
        )

        # 3. Apply evaporation
        if self.sim.enable_evaporation:
            wp.launch(
                kernel=evaporation_kernel,
                dim=self.num_droplets,
                inputs=[
                    self.diameters,
                    self.masses,
                    self.positions,
                    self.active,
                    self.spray.liquid_density,
                    self.sim.temperature,
                    self.sim.relative_humidity,
                    self.sim.vapor_pressure_sat,
                    self.sim.diffusion_coefficient,
                    dt
                ],
                device=self.device
            )

        # 4. Check deposition
        wp.launch(
            kernel=check_deposition_kernel,
            dim=self.num_droplets,
            inputs=[
                self.positions,
                self.velocities,
                self.active,
                self.deposition_time,
                self.deposition_position,
                self.sim.ground_level,
                self.sim.canopy_height,
                self.sim.capture_distance,
                self.sim.domain_x[0],
                self.sim.domain_x[1],
                self.sim.domain_y[0],
                self.sim.domain_y[1],
                self.current_time
            ],
            device=self.device
        )

        # Update time
        self.current_time += dt
        self.step_count += 1

    def get_state(self) -> Dict[str, np.ndarray]:
        """Return current state as numpy arrays"""
        return {
            'positions': self.positions.numpy(),
            'velocities': self.velocities.numpy(),
            'diameters': self.diameters.numpy(),
            'masses': self.masses.numpy(),
            'active': self.active.numpy(),
            'deposition_time': self.deposition_time.numpy(),
            'deposition_position': self.deposition_position.numpy(),
            'time': self.current_time,
            'step': self.step_count
        }

    def get_active_count(self) -> int:
        """Return number of active (airborne) droplets"""
        return int(np.sum(self.active.numpy()))

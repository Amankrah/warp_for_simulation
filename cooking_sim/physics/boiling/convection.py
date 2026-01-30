"""
Convection model for boiling water
"""

import warp as wp
import numpy as np


@wp.kernel
def compute_buoyancy_force(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    temperature: wp.array(dtype=float),
    forces: wp.array(dtype=wp.vec3),
    T_ref: float,
    beta: float,  # Thermal expansion coefficient
    rho: float,   # Density
    g: float,     # Gravity magnitude
    num_points: int
):
    """
    Compute buoyancy forces due to temperature differences
    F_buoyancy = ρ * β * (T - T_ref) * g

    Args:
        positions: Particle positions
        velocities: Particle velocities
        temperature: Temperature at each point
        forces: Output forces
        T_ref: Reference temperature
        beta: Thermal expansion coefficient (1/K)
        rho: Fluid density (kg/m³)
        g: Gravitational acceleration (m/s²)
        num_points: Number of points
    """
    tid = wp.tid()

    if tid >= num_points:
        return

    T = temperature[tid]
    delta_T = T - T_ref

    # Buoyancy force (upward for hot fluid)
    F_buoyancy = rho * beta * delta_T * g

    # Apply in z-direction (upward)
    forces[tid] = wp.vec3(0.0, 0.0, F_buoyancy)


class ConvectionModel:
    """Natural convection model for boiling water"""

    def __init__(
        self,
        density: float = 958.4,              # kg/m³ at 100°C
        thermal_expansion: float = 0.00075,   # 1/K for water near 100°C
        gravity: float = 9.81                 # m/s²
    ):
        """
        Initialize convection model

        Args:
            density: Fluid density
            thermal_expansion: Thermal expansion coefficient β
            gravity: Gravitational acceleration
        """
        self.density = density
        self.beta = thermal_expansion
        self.g = gravity

    def compute_rayleigh_number(
        self,
        delta_T: float,
        characteristic_length: float,
        thermal_diffusivity: float,
        kinematic_viscosity: float
    ) -> float:
        """
        Compute Rayleigh number for natural convection
        Ra = g·β·ΔT·L³/(α·ν)

        Args:
            delta_T: Temperature difference (K)
            characteristic_length: Characteristic length scale (m)
            thermal_diffusivity: α (m²/s)
            kinematic_viscosity: ν (m²/s)

        Returns:
            Rayleigh number (dimensionless)
        """
        Ra = (self.g * self.beta * delta_T * characteristic_length**3) / \
             (thermal_diffusivity * kinematic_viscosity)
        return Ra

    def estimate_convection_coefficient(
        self,
        delta_T: float,
        characteristic_length: float,
        thermal_conductivity: float
    ) -> float:
        """
        Estimate convection heat transfer coefficient

        For natural convection: h = C·(ΔT/L)^n·k
        where C and n depend on flow regime

        Args:
            delta_T: Temperature difference (K)
            characteristic_length: L (m)
            thermal_conductivity: k (W/(m·K))

        Returns:
            Convection coefficient h (W/(m²·K))
        """
        # For boiling water, use high convection coefficient
        # Typical range: 500-10000 W/(m²·K)

        # Simple correlation for nucleate boiling
        if delta_T < 5:
            # Free convection
            h = 100 + 25 * delta_T
        else:
            # Nucleate boiling regime
            h = 500 + 500 * (delta_T / 10)**0.33

        return min(h, 10000)  # Cap at typical maximum

    def apply_buoyancy(
        self,
        positions: wp.array,
        velocities: wp.array,
        temperature: wp.array,
        forces: wp.array,
        T_ref: float,
        num_points: int
    ):
        """
        Apply buoyancy forces to fluid particles

        Args:
            positions: Particle positions
            velocities: Particle velocities
            temperature: Temperature field
            forces: Output forces
            T_ref: Reference temperature
            num_points: Number of points
        """
        wp.launch(
            kernel=compute_buoyancy_force,
            dim=num_points,
            inputs=[
                positions,
                velocities,
                temperature,
                forces,
                T_ref,
                self.beta,
                self.density,
                self.g,
                num_points
            ]
        )

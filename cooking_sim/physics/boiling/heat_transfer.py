"""
Heat transfer model for boiling process
"""

import warp as wp
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class ThermalProperties:
    """Thermal properties of materials"""
    thermal_conductivity: float  # W/(m·K)
    specific_heat: float         # J/(kg·K)
    density: float               # kg/m³

    @property
    def thermal_diffusivity(self) -> float:
        """Calculate thermal diffusivity α = k/(ρ·cp)"""
        return self.thermal_conductivity / (self.density * self.specific_heat)


class MaterialDatabase:
    """Database of thermal properties for common materials"""

    WATER = ThermalProperties(
        thermal_conductivity=0.6,    # W/(m·K) at 100°C
        specific_heat=4186,           # J/(kg·K)
        density=958.4                 # kg/m³ at 100°C
    )

    CARROT = ThermalProperties(
        thermal_conductivity=0.55,    # W/(m·K)
        specific_heat=3850,           # J/(kg·K)
        density=1030                  # kg/m³
    )

    STAINLESS_STEEL = ThermalProperties(
        thermal_conductivity=16.0,    # W/(m·K)
        specific_heat=500,            # J/(kg·K)
        density=8000                  # kg/m³
    )


@wp.kernel
def compute_heat_diffusion_3d(
    temperature: wp.array(dtype=float),
    temperature_new: wp.array(dtype=float),
    grid_indices: wp.array(dtype=wp.vec3i),
    thermal_diffusivity: float,
    dx: float,
    dy: float,
    dz: float,
    dt: float,
    num_points: int
):
    """
    Compute 3D heat diffusion using finite difference method

    Args:
        temperature: Current temperature field
        temperature_new: Updated temperature field
        grid_indices: Grid indices for each point
        thermal_diffusivity: α = k/(ρ·cp)
        dx, dy, dz: Grid spacing
        dt: Time step
        num_points: Number of grid points
    """
    tid = wp.tid()

    if tid >= num_points:
        return

    # Get current point index
    idx = grid_indices[tid]
    i = idx[0]
    j = idx[1]
    k = idx[2]

    # Current temperature
    T_curr = temperature[tid]

    # Find neighbors and compute Laplacian
    # For simplicity, using 6-point stencil (face neighbors only)
    # ∇²T ≈ (T_i+1 - 2T_i + T_i-1)/dx²

    laplacian = 0.0

    # TODO: Implement neighbor finding and Laplacian computation
    # This requires a proper grid neighbor lookup structure

    # For now, use a simple approximation
    # In practice, you'd need to implement proper neighbor detection

    # Update temperature using explicit Euler method
    # T_new = T_old + α·dt·∇²T
    temperature_new[tid] = T_curr + thermal_diffusivity * dt * laplacian


class HeatTransferModel:
    """Heat transfer model for boiling simulation"""

    def __init__(
        self,
        water_properties: ThermalProperties = MaterialDatabase.WATER,
        food_properties: ThermalProperties = MaterialDatabase.CARROT,
        boiling_temperature: float = 100.0,
        ambient_temperature: float = 20.0
    ):
        """
        Initialize heat transfer model

        Args:
            water_properties: Thermal properties of water
            food_properties: Thermal properties of food
            boiling_temperature: Boiling point (°C)
            ambient_temperature: Initial temperature (°C)
        """
        self.water_props = water_properties
        self.food_props = food_properties
        self.T_boiling = boiling_temperature
        self.T_ambient = ambient_temperature

        # Warp arrays for simulation
        self.water_temperature = None
        self.food_temperature = None

    def initialize_temperatures(
        self,
        num_water_points: int,
        num_food_points: int
    ):
        """
        Initialize temperature fields

        Args:
            num_water_points: Number of water grid points
            num_food_points: Number of food grid points
        """
        # Initialize water at boiling temperature
        water_temp = np.full(num_water_points, self.T_boiling, dtype=np.float32)
        self.water_temperature = wp.array(water_temp, dtype=float)
        self.water_temperature_new = wp.array(water_temp, dtype=float)

        # Initialize food at ambient temperature
        food_temp = np.full(num_food_points, self.T_ambient, dtype=np.float32)
        self.food_temperature = wp.array(food_temp, dtype=float)
        self.food_temperature_new = wp.array(food_temp, dtype=float)

    def compute_convective_boundary_condition(
        self,
        surface_temperature: float,
        water_temperature: float,
        convection_coefficient: float = 500.0
    ) -> float:
        """
        Compute heat flux at food-water interface using Newton's law of cooling

        q = h(T_water - T_surface)

        Args:
            surface_temperature: Temperature at food surface (°C)
            water_temperature: Water temperature (°C)
            convection_coefficient: h in W/(m²·K), typical for boiling water: 500-10000

        Returns:
            Heat flux in W/m²
        """
        return convection_coefficient * (water_temperature - surface_temperature)

    def step(self, dt: float, dx: float = 0.001):
        """
        Advance heat transfer simulation by one time step

        Args:
            dt: Time step (s)
            dx: Grid spacing (m)
        """
        # For stable explicit scheme: dt < dx²/(2α) in 3D
        # where α is thermal diffusivity

        # Check stability criterion
        alpha_max = max(self.water_props.thermal_diffusivity,
                       self.food_props.thermal_diffusivity)
        dt_max = dx * dx / (6 * alpha_max)  # 3D stability

        if dt > dt_max:
            print(f"Warning: dt={dt:.6f}s exceeds stability limit {dt_max:.6f}s")

        # Update water temperature (maintained at boiling point)
        # In reality, you'd solve the full heat equation here

        # Update food temperature
        if self.food_temperature is not None:
            # TODO: Launch kernel to compute heat diffusion
            # For now, this is a placeholder
            pass

    def get_temperature_stats(self) -> dict:
        """Get statistics of temperature field"""
        stats = {}

        if self.food_temperature is not None:
            food_temps = self.food_temperature.numpy()
            stats['food_min'] = float(np.min(food_temps))
            stats['food_max'] = float(np.max(food_temps))
            stats['food_mean'] = float(np.mean(food_temps))

        if self.water_temperature is not None:
            water_temps = self.water_temperature.numpy()
            stats['water_min'] = float(np.min(water_temps))
            stats['water_max'] = float(np.max(water_temps))
            stats['water_mean'] = float(np.mean(water_temps))

        return stats

"""
Vitamin A degradation kinetics during boiling
"""

import warp as wp
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class VitaminAProperties:
    """Properties of Vitamin A (β-carotene) in carrots"""

    # Initial concentration in carrots (μg/g fresh weight)
    # Carrots contain ~8000-10000 μg β-carotene per 100g
    initial_concentration: float = 83.35  # μg/g

    # Diffusion coefficient in carrot tissue (m²/s)
    # Estimated based on literature for similar compounds
    diffusion_coefficient: float = 1e-10  # m²/s

    # Partition coefficient (carrot/water)
    # β-carotene is fat-soluble, low partition to water
    partition_coefficient: float = 0.01  # dimensionless

    # Thermal degradation kinetics parameters
    # Based on first-order kinetics: dC/dt = -k·C
    # Arrhenius equation: k = A·exp(-Ea/(R·T))

    # Pre-exponential factor (1/s)
    frequency_factor: float = 1e8  # 1/s

    # Activation energy (J/mol)
    # Literature values for carotenoid degradation: 50-120 kJ/mol
    activation_energy: float = 80000  # J/mol

    # Gas constant
    R: float = 8.314  # J/(mol·K)

    def get_degradation_rate(self, temperature_celsius: float) -> float:
        """
        Calculate degradation rate constant at given temperature
        k = A·exp(-Ea/(R·T))

        Args:
            temperature_celsius: Temperature in °C

        Returns:
            Rate constant k in 1/s
        """
        T_kelvin = temperature_celsius + 273.15
        k = self.frequency_factor * np.exp(-self.activation_energy / (self.R * T_kelvin))
        return k


@wp.kernel
def compute_vitamin_degradation(
    concentration: wp.array(dtype=float),
    concentration_new: wp.array(dtype=float),
    rate_constants: wp.array(dtype=float),
    dt: float,
    num_points: int
):
    """
    Compute first-order degradation of Vitamin A
    dC/dt = -k(T)·C

    Args:
        concentration: Current concentration (μg/g)
        concentration_new: Updated concentration (μg/g)
        rate_constants: Pre-computed rate constants at each temperature
        dt: Time step (s)
        num_points: Number of grid points
    """
    tid = wp.tid()

    if tid >= num_points:
        return

    C = concentration[tid]
    k = rate_constants[tid]

    # First-order degradation using explicit Euler
    # C_new = C_old - k·C_old·dt
    # Or more accurately: C_new = C_old·exp(-k·dt)

    C_new = C * wp.exp(-k * dt)

    concentration_new[tid] = C_new


@wp.kernel
def compute_leaching_to_water(
    food_concentration: wp.array(dtype=float),
    water_concentration: wp.array(dtype=float),
    food_positions: wp.array(dtype=wp.vec3),
    water_positions: wp.array(dtype=wp.vec3),
    partition_coefficient: float,
    mass_transfer_coefficient: float,
    dt: float,
    num_food_points: int,
    num_water_points: int,
    search_radius: float
):
    """
    Compute leaching of nutrients from food to water at interface

    Args:
        food_concentration: Concentration in food (μg/g)
        water_concentration: Concentration in water (μg/mL)
        food_positions: Positions of food grid points
        water_positions: Positions of water grid points
        partition_coefficient: K = C_food_eq/C_water_eq
        mass_transfer_coefficient: k_m (m/s)
        dt: Time step (s)
        num_food_points: Number of food grid points
        num_water_points: Number of water grid points
        search_radius: Radius to search for nearby water points (m)
    """
    tid = wp.tid()

    if tid >= num_food_points:
        return

    pos_food = food_positions[tid]
    C_food = food_concentration[tid]

    # Find nearest water point (simplified - in practice use spatial hash)
    min_dist = 1e10
    nearest_water_idx = -1

    for i in range(num_water_points):
        pos_water = water_positions[i]
        dist = wp.length(pos_food - pos_water)

        if dist < min_dist and dist < search_radius:
            min_dist = dist
            nearest_water_idx = i

    # If near water surface, compute mass transfer
    if nearest_water_idx >= 0:
        C_water = water_concentration[nearest_water_idx]

        # Equilibrium concentration in food
        C_food_eq = partition_coefficient * C_water

        # Driving force for mass transfer
        driving_force = C_food - C_food_eq

        # Mass flux: J = k_m·(C_food - C_food_eq)
        # Change in concentration: dC = -J·A·dt/V
        # Simplified: dC = -k_m·(C_food - C_food_eq)·dt

        dC = mass_transfer_coefficient * driving_force * dt

        # Update concentrations
        food_concentration[tid] = C_food - dC

        # Transfer to water (with conversion factors)
        # Note: Need to account for volume/mass ratios
        # Simplified for now
        # water_concentration[nearest_water_idx] = C_water + dC / partition_coefficient


class VitaminAKinetics:
    """Vitamin A degradation and leaching kinetics"""

    def __init__(
        self,
        properties: VitaminAProperties = VitaminAProperties()
    ):
        """
        Initialize Vitamin A kinetics model

        Args:
            properties: Vitamin A properties
        """
        self.props = properties

        # Warp arrays
        self.food_concentration = None
        self.water_concentration = None
        self.rate_constants = None

    def initialize_concentrations(
        self,
        num_food_points: int,
        num_water_points: int
    ):
        """
        Initialize nutrient concentration fields

        Args:
            num_food_points: Number of grid points in food
            num_water_points: Number of grid points in water
        """
        # Initialize food with uniform Vitamin A concentration
        food_conc = np.full(num_food_points, self.props.initial_concentration, dtype=np.float32)
        self.food_concentration = wp.array(food_conc, dtype=float)
        self.food_concentration_new = wp.array(food_conc, dtype=float)

        # Initialize water with zero concentration
        water_conc = np.zeros(num_water_points, dtype=np.float32)
        self.water_concentration = wp.array(water_conc, dtype=float)

    def update_rate_constants(self, temperature: wp.array):
        """
        Update degradation rate constants based on temperature field

        Args:
            temperature: Temperature array (°C)
        """
        temps = temperature.numpy()
        num_points = len(temps)

        rates = np.zeros(num_points, dtype=np.float32)
        for i in range(num_points):
            rates[i] = self.props.get_degradation_rate(temps[i])

        self.rate_constants = wp.array(rates, dtype=float)

    def step_degradation(self, dt: float, num_points: int):
        """
        Advance degradation simulation by one time step

        Args:
            dt: Time step (s)
            num_points: Number of food grid points
        """
        if self.rate_constants is None:
            raise ValueError("Rate constants not initialized. Call update_rate_constants first.")

        wp.launch(
            kernel=compute_vitamin_degradation,
            dim=num_points,
            inputs=[
                self.food_concentration,
                self.food_concentration_new,
                self.rate_constants,
                dt,
                num_points
            ]
        )

        # Swap buffers
        self.food_concentration, self.food_concentration_new = \
            self.food_concentration_new, self.food_concentration

    def get_retention_percentage(self) -> float:
        """
        Calculate percentage of Vitamin A retained

        Returns:
            Retention percentage (0-100)
        """
        if self.food_concentration is None:
            return 100.0

        current_conc = self.food_concentration.numpy()
        current_total = np.sum(current_conc)

        initial_total = self.props.initial_concentration * len(current_conc)

        retention = (current_total / initial_total) * 100
        return retention

    def get_statistics(self) -> dict:
        """Get statistics of Vitamin A concentration"""
        stats = {}

        if self.food_concentration is not None:
            conc = self.food_concentration.numpy()
            stats['food_min'] = float(np.min(conc))
            stats['food_max'] = float(np.max(conc))
            stats['food_mean'] = float(np.mean(conc))
            stats['retention_%'] = float(self.get_retention_percentage())

        if self.water_concentration is not None:
            conc = self.water_concentration.numpy()
            stats['water_mean'] = float(np.mean(conc))

        return stats

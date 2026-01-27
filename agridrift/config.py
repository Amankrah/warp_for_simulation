"""
Configuration classes for AgriDrift simulation parameters
"""

import dataclasses
from typing import Tuple
import numpy as np


@dataclasses.dataclass
class SprayConfig:
    """Spray equipment and droplet parameters"""

    # Spray location and pattern
    nozzle_height: float = 2.0              # Height above ground (m)
    nozzle_position: Tuple[float, float] = (0.0, 0.0)  # (x, y) position (m)
    spray_angle: float = 30.0               # Spray cone half-angle (degrees)

    # Droplet properties
    num_droplets: int = 10000               # Number of droplets to simulate
    droplet_diameter_mean: float = 200e-6   # Mean diameter (m) - 200 microns
    droplet_diameter_std: float = 50e-6     # Std deviation (m)
    droplet_diameter_min: float = 50e-6     # Minimum diameter (m)
    droplet_diameter_max: float = 500e-6    # Maximum diameter (m)

    # Initial velocity
    initial_velocity: float = 5.0           # Initial spray velocity (m/s)
    velocity_variation: float = 0.5         # Velocity std deviation (m/s)

    # Liquid properties
    liquid_density: float = 1000.0          # Density of spray liquid (kg/m³)
    liquid_surface_tension: float = 0.072   # Surface tension (N/m)

    # Active ingredient
    concentration: float = 1.0              # Active ingredient concentration (g/L)


@dataclasses.dataclass
class WindConfig:
    """Wind field parameters"""

    # Mean wind
    wind_speed: float = 3.0                 # Mean wind speed at reference height (m/s)
    wind_direction: float = 90.0            # Wind direction (degrees, 0=North, 90=East)
    reference_height: float = 10.0          # Reference height for wind speed (m)

    # Wind profile (power law)
    surface_roughness: float = 0.1          # Roughness length (m) - cropland ~0.1m
    power_law_exponent: float = 0.16        # Typical for cropland

    # Turbulence
    turbulence_intensity: float = 0.2       # Turbulence intensity (fraction of mean)
    turbulence_length_scale: float = 1.0    # Length scale for turbulent eddies (m)

    # Gusts (simple sinusoidal model)
    gust_amplitude: float = 1.0             # Gust amplitude (m/s)
    gust_period: float = 10.0               # Gust period (s)


@dataclasses.dataclass
class SimulationConfig:
    """Simulation control parameters"""

    # Time stepping
    dt: float = 0.01                        # Time step (s)
    total_time: float = 60.0                # Total simulation time (s)
    output_interval: float = 0.5            # Output interval (s)

    # Domain
    domain_x: Tuple[float, float] = (-20.0, 20.0)  # X extent (m)
    domain_y: Tuple[float, float] = (-20.0, 20.0)  # Y extent (m)
    domain_z: Tuple[float, float] = (0.0, 10.0)    # Z extent (m)

    # Ground/canopy
    ground_level: float = 0.0               # Ground height (m)
    canopy_height: float = 0.0              # Crop canopy height (m, 0=bare soil)
    canopy_density: float = 0.0             # Leaf area density (m²/m³, 0=no canopy)

    # Physical constants
    air_density: float = 1.225              # Air density (kg/m³) at sea level, 15°C
    air_viscosity: float = 1.81e-5          # Dynamic viscosity of air (Pa·s)
    gravity: float = 9.81                   # Gravitational acceleration (m/s²)
    temperature: float = 293.15             # Temperature (K) - 20°C
    relative_humidity: float = 0.6          # Relative humidity (0-1)

    # Evaporation
    enable_evaporation: bool = True         # Enable droplet evaporation
    vapor_pressure_sat: float = 2339.0      # Saturation vapor pressure at 20°C (Pa)
    diffusion_coefficient: float = 2.5e-5   # Water vapor diffusion in air (m²/s)

    # Deposition
    capture_distance: float = 0.05          # Distance for ground capture (m)

    # Device
    device: str = "cuda:0"                  # Compute device


@dataclasses.dataclass
class EnvironmentalConditions:
    """Combined environmental conditions for easy scenario setup"""

    # Quick presets
    wind_calm: bool = False                 # Calm conditions (< 1 m/s wind)
    wind_moderate: bool = False             # Moderate wind (3-5 m/s)
    wind_strong: bool = False               # Strong wind (> 6 m/s)

    temperature_hot: bool = False           # Hot day (30°C+)
    temperature_moderate: bool = True       # Moderate (20°C)
    temperature_cool: bool = False          # Cool (10°C)

    humidity_low: bool = False              # Low humidity (< 40%)
    humidity_moderate: bool = True          # Moderate (40-70%)
    humidity_high: bool = False             # High (> 70%)

    def to_configs(self) -> Tuple[WindConfig, SimulationConfig]:
        """Convert preset to actual configuration objects"""
        wind_cfg = WindConfig()
        sim_cfg = SimulationConfig()

        # Set wind
        if self.wind_calm:
            wind_cfg.wind_speed = 0.5
        elif self.wind_moderate:
            wind_cfg.wind_speed = 4.0
        elif self.wind_strong:
            wind_cfg.wind_speed = 7.0

        # Set temperature
        if self.temperature_hot:
            sim_cfg.temperature = 303.15  # 30°C
            sim_cfg.vapor_pressure_sat = 4245.0
        elif self.temperature_moderate:
            sim_cfg.temperature = 293.15  # 20°C
            sim_cfg.vapor_pressure_sat = 2339.0
        elif self.temperature_cool:
            sim_cfg.temperature = 283.15  # 10°C
            sim_cfg.vapor_pressure_sat = 1228.0

        # Set humidity
        if self.humidity_low:
            sim_cfg.relative_humidity = 0.3
        elif self.humidity_moderate:
            sim_cfg.relative_humidity = 0.6
        elif self.humidity_high:
            sim_cfg.relative_humidity = 0.85

        return wind_cfg, sim_cfg

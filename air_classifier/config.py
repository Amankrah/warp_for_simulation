"""
Configuration classes for air classifier simulation

Based on the comprehensive engineering guide for yellow pea protein separation
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClassifierConfig:
    """Air classifier geometry and operating configuration"""

    # Geometry (meters)
    chamber_radius: float = 0.5           # Classification chamber radius
    chamber_height: float = 1.2           # Chamber height
    wheel_radius: float = 0.2             # Classifier wheel radius
    wheel_width: float = 0.06             # Wheel width (height)
    wheel_position_z: float = 0.9         # Height of wheel center above bottom

    # Operating conditions
    wheel_rpm: float = 3500.0             # Wheel rotation speed (rpm)
    air_velocity: float = 8.0             # Radial air velocity (m/s)

    # Blade configuration
    blade_count: int = 24                 # Number of classifier blades
    blade_thickness: float = 0.003        # Blade thickness (m)

    # Simulation parameters
    num_particles: int = 50000            # Number of particles to simulate
    dt: float = 1e-5                      # Time step (seconds)
    device: str = "cuda"                  # Compute device


@dataclass
class ParticleProperties:
    """Properties for pea flour particles"""

    # Protein particles (fine fraction)
    protein_diameter_mean: float = 5e-6       # 5 μm
    protein_diameter_std: float = 2e-6        # Standard deviation
    protein_density: float = 1350.0           # kg/m³
    protein_fraction: float = 0.25            # 25% of particles by count

    # Starch particles (coarse fraction)
    starch_diameter_mean: float = 28e-6       # 28 μm
    starch_diameter_std: float = 8e-6         # Standard deviation
    starch_density: float = 1520.0            # kg/m³

    # Physical properties
    moisture_content: float = 0.10            # 10% moisture
    temperature: float = 298.15               # K (25°C)

    # Target separation parameters
    target_cut_size: float = 20e-6            # d50 target (20 μm)
    target_protein_purity: float = 0.58       # 58% protein in fine fraction
    target_starch_purity: float = 0.88        # 88% starch in coarse fraction


@dataclass
class SimulationConfig:
    """Simulation control parameters"""

    # Time control
    total_time: float = 3.0               # Total simulation time (seconds)
    output_interval: float = 0.05         # Time between outputs (seconds)

    # Feed conditions
    feed_rate: float = 200.0              # kg/hr
    feed_height: float = 0.88             # Height where particles enter (m) - just below wheel
    feed_radius_min: float = 0.10         # Inner radius of feed zone (m) - MOVED CLOSER to center
    feed_radius_max: float = 0.18         # Outer radius of feed zone (m) - just inside upward zone (0.186m)

    # Air properties (at 25°C, 1 atm)
    air_density: float = 1.184            # kg/m³
    air_viscosity: float = 1.85e-5        # Pa·s
    air_temperature: float = 298.15       # K
    relative_humidity: float = 0.50       # 50% RH

    # Computational
    device: str = "cuda:0"                # Computation device
    enable_visualization: bool = True      # Enable real-time visualization
    save_trajectory: bool = False         # Save particle trajectories

    # Analysis
    collection_threshold_fine: float = 1.0     # Z threshold for fine collection (m)
    collection_threshold_coarse: float = 0.10  # Z threshold for coarse collection (m)


@dataclass
class ProcessParameters:
    """Process-level parameters for operation and optimization"""

    # Target performance
    target_throughput: float = 200.0      # kg/hr
    target_protein_recovery: float = 0.70  # 70% of protein to fine fraction
    target_separation_efficiency: float = 0.85  # Overall efficiency

    # Operating ranges
    rpm_min: float = 2000.0
    rpm_max: float = 5000.0
    air_flow_min: float = 1500.0          # m³/hr
    air_flow_max: float = 2200.0          # m³/hr

    # Control parameters
    control_mode: str = "manual"          # "manual", "auto", "optimize"
    optimization_target: str = "purity"    # "purity", "yield", "recovery"

    # Economic parameters
    flour_cost_per_kg: float = 0.80
    protein_price_per_kg: float = 3.50
    starch_price_per_kg: float = 0.60
    electricity_cost_per_kwh: float = 0.10


# Default configurations for common scenarios

def get_default_config() -> tuple[ClassifierConfig, ParticleProperties, SimulationConfig]:
    """Get default configuration for standard operation"""
    return (
        ClassifierConfig(),
        ParticleProperties(),
        SimulationConfig()
    )


def get_high_purity_config() -> tuple[ClassifierConfig, ParticleProperties, SimulationConfig]:
    """Configuration optimized for maximum protein purity"""
    classifier = ClassifierConfig(
        wheel_rpm=4500.0,
        air_velocity=7.0
    )
    particles = ParticleProperties(
        target_protein_purity=0.65
    )
    simulation = SimulationConfig(
        feed_rate=150.0
    )
    return classifier, particles, simulation


def get_high_yield_config() -> tuple[ClassifierConfig, ParticleProperties, SimulationConfig]:
    """Configuration optimized for maximum protein recovery"""
    classifier = ClassifierConfig(
        wheel_rpm=3000.0,
        air_velocity=9.0
    )
    particles = ParticleProperties(
        target_protein_purity=0.52
    )
    simulation = SimulationConfig(
        feed_rate=250.0
    )
    return classifier, particles, simulation


def get_pilot_scale_config() -> tuple[ClassifierConfig, ParticleProperties, SimulationConfig]:
    """Configuration for pilot-scale testing (smaller system)"""
    classifier = ClassifierConfig(
        chamber_radius=0.25,
        chamber_height=0.6,
        wheel_radius=0.1,
        wheel_width=0.03,
        wheel_position_z=0.45,
        wheel_rpm=4000.0,
        num_particles=20000
    )
    particles = ParticleProperties()
    simulation = SimulationConfig(
        feed_rate=50.0,
        total_time=1.5,
        feed_radius_min=0.18,
        feed_radius_max=0.22
    )
    return classifier, particles, simulation

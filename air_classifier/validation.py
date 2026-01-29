"""
Design Validation and Industry Standard Calculations

Implements theoretical calculations from the engineering guide to validate
simulation results against established correlations and industry standards.

Reference: Comprehensive Engineering Guide §2, §5
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from .config import ClassifierConfig, ParticleProperties, SimulationConfig


# Physical constants
GRAVITY = 9.81  # m/s²
PI = np.pi


@dataclass
class ValidationResults:
    """Results from design validation calculations"""
    # Cut size calculations
    theoretical_d50: float  # μm
    theoretical_rpm_for_target: float
    tip_speed: float  # m/s

    # Air system
    required_air_flow: float  # m³/hr
    required_air_velocity: float  # m/s
    reynolds_number_wheel: float

    # Mass balance
    expected_fine_fraction: float
    expected_coarse_fraction: float
    expected_protein_recovery: float

    # Performance metrics
    blade_gap: float  # mm
    residence_time: float  # seconds
    stokes_number_protein: float
    stokes_number_starch: float

    # Compliance flags
    tip_speed_ok: bool
    rpm_in_range: bool
    separation_feasible: bool


def calculate_theoretical_cut_size(
    config: ClassifierConfig,
    particle_props: ParticleProperties,
    sim_config: SimulationConfig
) -> float:
    """
    Calculate theoretical cut size from operating parameters

    Based on Guide §2.2.3:
    d₅₀ = √(9μQ / (2π × ρₚ × ω² × rc² × h))

    Args:
        config: Classifier geometry and operating conditions
        particle_props: Particle properties
        sim_config: Simulation configuration

    Returns:
        Theoretical cut size in meters
    """
    # Angular velocity
    omega = config.wheel_rpm * 2 * PI / 60  # rad/s

    # Volumetric air flow (approximate from radial velocity)
    # Q ≈ 2π × rc × h × v_radial
    Q = 2 * PI * config.wheel_radius * config.wheel_width * config.air_velocity  # m³/s

    # Average particle density (weighted by fraction)
    rho_p = (particle_props.protein_fraction * particle_props.protein_density +
             (1 - particle_props.protein_fraction) * particle_props.starch_density)

    # Cut size formula
    numerator = 9 * sim_config.air_viscosity * Q
    denominator = 2 * PI * rho_p * omega**2 * config.wheel_radius**2 * config.wheel_width

    d50 = np.sqrt(numerator / denominator)

    return d50


def calculate_required_rpm_for_target_d50(
    target_d50: float,
    config: ClassifierConfig,
    particle_props: ParticleProperties,
    sim_config: SimulationConfig
) -> float:
    """
    Calculate wheel RPM needed to achieve target cut size

    Inverts the cut size formula:
    ω = √(9μQ / (2π × ρₚ × d₅₀² × rc² × h))

    Args:
        target_d50: Target cut size in meters
        config: Classifier configuration
        particle_props: Particle properties
        sim_config: Simulation configuration

    Returns:
        Required wheel speed in RPM
    """
    # Volumetric air flow
    Q = 2 * PI * config.wheel_radius * config.wheel_width * config.air_velocity

    # Average particle density
    rho_p = (particle_props.protein_fraction * particle_props.protein_density +
             (1 - particle_props.protein_fraction) * particle_props.starch_density)

    # Calculate required angular velocity
    numerator = 9 * sim_config.air_viscosity * Q
    denominator = 2 * PI * rho_p * target_d50**2 * config.wheel_radius**2 * config.wheel_width

    omega = np.sqrt(numerator / denominator)  # rad/s
    rpm = omega * 60 / (2 * PI)

    return rpm


def calculate_terminal_velocity(
    diameter: float,
    density: float,
    air_density: float,
    air_viscosity: float
) -> float:
    """
    Calculate terminal settling velocity of a particle

    Guide §2.1.1 - Uses iterative solution for intermediate Re

    Args:
        diameter: Particle diameter (m)
        density: Particle density (kg/m³)
        air_density: Air density (kg/m³)
        air_viscosity: Air dynamic viscosity (Pa·s)

    Returns:
        Terminal velocity in m/s
    """
    # Initial guess using Stokes law
    vt = diameter**2 * (density - air_density) * GRAVITY / (18 * air_viscosity)

    # Iterate to account for drag coefficient
    for _ in range(10):
        Re = air_density * vt * diameter / air_viscosity

        # Drag coefficient (Schiller-Naumann)
        if Re < 0.1:
            Cd = 24.0 / (Re + 1e-10)
        elif Re < 1000:
            Cd = 24.0 / Re * (1.0 + 0.15 * Re**0.687)
        else:
            Cd = 0.44

        # Update velocity
        vt_new = np.sqrt(4 * diameter * (density - air_density) * GRAVITY /
                        (3 * Cd * air_density))

        # Check convergence
        if abs(vt_new - vt) / vt < 0.01:
            break
        vt = vt_new

    return vt


def calculate_stokes_number(
    diameter: float,
    density: float,
    characteristic_velocity: float,
    characteristic_length: float,
    air_viscosity: float
) -> float:
    """
    Calculate Stokes number for particle

    Guide §2.1.3:
    St = (ρₚ × d² × U) / (18 × μ × L)

    Args:
        diameter: Particle diameter (m)
        density: Particle density (kg/m³)
        characteristic_velocity: Characteristic fluid velocity (m/s)
        characteristic_length: Characteristic length scale (m)
        air_viscosity: Air dynamic viscosity (Pa·s)

    Returns:
        Stokes number (dimensionless)
    """
    St = (density * diameter**2 * characteristic_velocity) / \
         (18 * air_viscosity * characteristic_length)
    return St


def calculate_blade_gap(
    wheel_diameter: float,
    blade_count: int,
    blade_thickness: float
) -> float:
    """
    Calculate gap between classifier blades

    Guide §6.1.3

    Args:
        wheel_diameter: Classifier wheel diameter (m)
        blade_count: Number of blades
        blade_thickness: Thickness of each blade (m)

    Returns:
        Gap between blades in meters
    """
    circumference = PI * wheel_diameter
    total_blade_width = blade_count * blade_thickness
    total_gap = circumference - total_blade_width
    gap_per_blade = total_gap / blade_count
    return gap_per_blade


def calculate_mass_balance(
    feed_protein_content: float,
    fine_protein_content: float,
    coarse_protein_content: float,
    separation_efficiency: float = 0.85
) -> Dict[str, float]:
    """
    Calculate mass balance for protein separation

    Guide §5.2.1

    Args:
        feed_protein_content: Protein content in feed (fraction)
        fine_protein_content: Target protein in fine fraction
        coarse_protein_content: Expected protein in coarse fraction
        separation_efficiency: Separation efficiency factor

    Returns:
        Dictionary with mass balance results
    """
    # Solve for fine fraction split
    # x_F = f × x_fine + (1-f) × x_coarse
    # f = (x_F - x_coarse) / (x_fine - x_coarse)

    fine_fraction = (feed_protein_content - coarse_protein_content) / \
                   (fine_protein_content - coarse_protein_content)

    # Apply separation efficiency
    fine_fraction *= separation_efficiency
    coarse_fraction = 1.0 - fine_fraction

    # Protein recovery
    protein_recovery = (fine_fraction * fine_protein_content) / feed_protein_content

    return {
        'fine_fraction': fine_fraction,
        'coarse_fraction': coarse_fraction,
        'protein_recovery': protein_recovery,
        'fine_rate_kg_per_hr': fine_fraction * 200,  # Assuming 200 kg/hr feed
        'coarse_rate_kg_per_hr': coarse_fraction * 200,
        'protein_enrichment_ratio': fine_protein_content / feed_protein_content
    }


def calculate_air_system_requirements(
    feed_rate: float,
    solids_loading: float,
    air_temperature: float,
    pressure_drop: float,
    fan_efficiency: float = 0.60
) -> Dict[str, float]:
    """
    Calculate air flow and fan power requirements

    Guide §5.4.1

    Args:
        feed_rate: Feed rate (kg/hr)
        solids_loading: Solids loading (kg solids / kg air)
        air_temperature: Air temperature (°C)
        pressure_drop: System pressure drop (Pa)
        fan_efficiency: Fan efficiency (fraction)

    Returns:
        Dictionary with air system calculations
    """
    # Air properties
    R = 287  # J/(kg·K)
    T = air_temperature + 273.15  # K
    P = 101325  # Pa (atmospheric)
    rho_air = P / (R * T)  # kg/m³

    # Air mass flow
    air_mass_flow = feed_rate / solids_loading  # kg/hr
    air_volume_flow = air_mass_flow / rho_air   # m³/hr

    # Fan power
    fan_power = (air_volume_flow / 3600) * pressure_drop / fan_efficiency  # W

    # Add safety factor
    fan_power *= 1.2

    return {
        'air_mass_flow_kg_hr': air_mass_flow,
        'air_volume_flow_m3_hr': air_volume_flow,
        'air_volume_flow_m3_s': air_volume_flow / 3600,
        'fan_power_kw': fan_power / 1000,
        'air_density_kg_m3': rho_air,
        'specific_power_kwh_per_tonne': fan_power / 1000 / (feed_rate / 1000)
    }


def validate_classifier_design(
    config: ClassifierConfig,
    particle_props: ParticleProperties,
    sim_config: SimulationConfig
) -> ValidationResults:
    """
    Perform comprehensive design validation

    Checks all critical parameters against industry standards
    and engineering guide specifications

    Args:
        config: Classifier configuration
        particle_props: Particle properties
        sim_config: Simulation configuration

    Returns:
        ValidationResults with all calculated parameters and compliance flags
    """
    # Cut size calculations
    theoretical_d50 = calculate_theoretical_cut_size(config, particle_props, sim_config)
    theoretical_rpm = calculate_required_rpm_for_target_d50(
        particle_props.target_cut_size, config, particle_props, sim_config
    )

    # Tip speed
    omega = config.wheel_rpm * 2 * PI / 60
    tip_speed = omega * config.wheel_radius

    # Blade gap
    blade_gap = calculate_blade_gap(
        config.wheel_radius * 2, config.blade_count, config.blade_thickness
    )

    # Air system
    air_system = calculate_air_system_requirements(
        sim_config.feed_rate,
        solids_loading=0.3,  # kg/kg - typical for classifiers
        air_temperature=sim_config.air_temperature - 273.15,
        pressure_drop=3500  # Pa - from guide §5.4.2
    )

    # Mass balance
    mass_balance = calculate_mass_balance(
        feed_protein_content=0.23,  # 23% protein in feed
        fine_protein_content=particle_props.target_protein_purity,
        coarse_protein_content=0.12  # 12% protein in coarse
    )

    # Terminal velocities
    vt_protein = calculate_terminal_velocity(
        particle_props.protein_diameter_mean,
        particle_props.protein_density,
        sim_config.air_density,
        sim_config.air_viscosity
    )

    vt_starch = calculate_terminal_velocity(
        particle_props.starch_diameter_mean,
        particle_props.starch_density,
        sim_config.air_density,
        sim_config.air_viscosity
    )

    # Stokes numbers
    St_protein = calculate_stokes_number(
        particle_props.protein_diameter_mean,
        particle_props.protein_density,
        config.air_velocity,
        config.wheel_radius,
        sim_config.air_viscosity
    )

    St_starch = calculate_stokes_number(
        particle_props.starch_diameter_mean,
        particle_props.starch_density,
        config.air_velocity,
        config.wheel_radius,
        sim_config.air_viscosity
    )

    # Residence time (approximate)
    chamber_volume = PI * config.chamber_radius**2 * config.chamber_height
    residence_time = chamber_volume / air_system['air_volume_flow_m3_s']

    # Reynolds number at wheel
    Re_wheel = sim_config.air_density * tip_speed * config.wheel_width / sim_config.air_viscosity

    # Compliance checks
    tip_speed_ok = 40 <= tip_speed <= 100  # Guide §5.3.1: safe range
    rpm_in_range = 2000 <= config.wheel_rpm <= 5000  # Guide §5.5

    # Check if separation is feasible (Stokes numbers should differ significantly)
    separation_feasible = (St_starch / St_protein) > 5.0

    return ValidationResults(
        theoretical_d50=theoretical_d50 * 1e6,  # Convert to μm
        theoretical_rpm_for_target=theoretical_rpm,
        tip_speed=tip_speed,
        required_air_flow=air_system['air_volume_flow_m3_hr'],
        required_air_velocity=config.air_velocity,
        reynolds_number_wheel=Re_wheel,
        expected_fine_fraction=mass_balance['fine_fraction'],
        expected_coarse_fraction=mass_balance['coarse_fraction'],
        expected_protein_recovery=mass_balance['protein_recovery'],
        blade_gap=blade_gap * 1000,  # Convert to mm
        residence_time=residence_time,
        stokes_number_protein=St_protein,
        stokes_number_starch=St_starch,
        tip_speed_ok=tip_speed_ok,
        rpm_in_range=rpm_in_range,
        separation_feasible=separation_feasible
    )


def print_validation_report(
    validation: ValidationResults,
    config: ClassifierConfig,
    particle_props: ParticleProperties
):
    """
    Print comprehensive validation report

    Args:
        validation: Validation results
        config: Classifier configuration
        particle_props: Particle properties
    """
    print("\n" + "="*70)
    print(" AIR CLASSIFIER DESIGN VALIDATION REPORT")
    print("="*70)

    print("\n1. CUT SIZE ANALYSIS")
    print("-" * 70)
    print(f"  Target cut size (d₅₀):        {particle_props.target_cut_size*1e6:.1f} μm")
    print(f"  Theoretical cut size:         {validation.theoretical_d50:.1f} μm")
    print(f"  Current wheel speed:          {config.wheel_rpm:.0f} RPM")
    print(f"  Required RPM for target:      {validation.theoretical_rpm_for_target:.0f} RPM")

    delta_d50 = abs(validation.theoretical_d50 - particle_props.target_cut_size*1e6)
    if delta_d50 < 2:
        status = "✓ EXCELLENT"
    elif delta_d50 < 5:
        status = "✓ ACCEPTABLE"
    else:
        status = "⚠ NEEDS ADJUSTMENT"
    print(f"  Cut size match:               {status}")

    print("\n2. WHEEL PERFORMANCE")
    print("-" * 70)
    print(f"  Wheel radius:                 {config.wheel_radius*1000:.0f} mm")
    print(f"  Wheel width:                  {config.wheel_width*1000:.0f} mm")
    print(f"  Number of blades:             {config.blade_count}")
    print(f"  Blade gap:                    {validation.blade_gap:.1f} mm")
    print(f"  Tip speed:                    {validation.tip_speed:.1f} m/s")
    print(f"  Tip speed check:              {'✓ OK' if validation.tip_speed_ok else '⚠ OUT OF RANGE'}")
    print(f"  RPM range check:              {'✓ OK' if validation.rpm_in_range else '⚠ OUT OF RANGE'}")
    print(f"  Reynolds number (wheel):      {validation.reynolds_number_wheel:.0f}")

    print("\n3. AIR SYSTEM")
    print("-" * 70)
    print(f"  Required air flow:            {validation.required_air_flow:.0f} m³/hr")
    print(f"  Radial air velocity:          {validation.required_air_velocity:.1f} m/s")
    print(f"  Residence time:               {validation.residence_time:.2f} s")

    print("\n4. SEPARATION FEASIBILITY")
    print("-" * 70)
    print(f"  Stokes number (protein):      {validation.stokes_number_protein:.4f}")
    print(f"  Stokes number (starch):       {validation.stokes_number_starch:.4f}")
    print(f"  Ratio (starch/protein):       {validation.stokes_number_starch/validation.stokes_number_protein:.1f}")
    print(f"  Separation feasibility:       {'✓ FEASIBLE' if validation.separation_feasible else '⚠ CHALLENGING'}")

    if validation.stokes_number_protein < 0.1:
        print(f"  → Protein particles follow streamlines (St << 1)")
    if validation.stokes_number_starch > 1:
        print(f"  → Starch particles deviate from streamlines (St >> 1)")

    print("\n5. MASS BALANCE PREDICTIONS")
    print("-" * 70)
    print(f"  Expected fine fraction:       {validation.expected_fine_fraction*100:.1f}%")
    print(f"  Expected coarse fraction:     {validation.expected_coarse_fraction*100:.1f}%")
    print(f"  Expected protein recovery:    {validation.expected_protein_recovery*100:.1f}%")
    print(f"  Fine rate (at 200 kg/hr):     {validation.expected_fine_fraction*200:.1f} kg/hr")
    print(f"  Coarse rate (at 200 kg/hr):   {validation.expected_coarse_fraction*200:.1f} kg/hr")

    print("\n6. OVERALL COMPLIANCE")
    print("-" * 70)

    checks_passed = sum([
        validation.tip_speed_ok,
        validation.rpm_in_range,
        validation.separation_feasible,
        delta_d50 < 5
    ])

    total_checks = 4
    compliance_pct = (checks_passed / total_checks) * 100

    print(f"  Checks passed:                {checks_passed}/{total_checks}")
    print(f"  Compliance level:             {compliance_pct:.0f}%")

    if compliance_pct == 100:
        print(f"  Status:                       ✓ FULLY COMPLIANT")
    elif compliance_pct >= 75:
        print(f"  Status:                       ✓ ACCEPTABLE - Minor adjustments recommended")
    else:
        print(f"  Status:                       ⚠ REQUIRES ADJUSTMENT")

    print("\n" + "="*70)
    print(" Reference: Comprehensive Engineering Guide §2, §5")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Example validation
    from .config import get_default_config

    config, particle_props, sim_config = get_default_config()

    validation = validate_classifier_design(config, particle_props, sim_config)
    print_validation_report(validation, config, particle_props)

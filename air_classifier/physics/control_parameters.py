"""
Control Parameters for Air Classifier

This module defines the TUNABLE parameters that operators adjust via the control board,
as well as PHYSICAL CONSTANTS that never change.

PHILOSOPHY:
===========
- FUNDAMENTAL PHYSICS (in air_flow.py, particle_dynamics.py) = Laws of nature
- CONTROL PARAMETERS (here) = Machine settings adjustable by operators
- GEOMETRY (here) = Fixed machine dimensions (different per machine model)
- PHYSICAL CONSTANTS (here) = Properties of air, gravity, etc.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# PHYSICAL CONSTANTS (Never change)
# =============================================================================

class PhysicalConstants:
    """Universal physical constants"""

    # Air properties (at 20°C, 1 atm)
    AIR_DENSITY = 1.204  # kg/m³
    AIR_VISCOSITY = 1.81e-5  # Pa·s (dynamic viscosity)

    # Gravity
    GRAVITY = 9.81  # m/s²

    # Mathematical constants
    PI = 3.14159265359


# =============================================================================
# CONTROL BOARD PARAMETERS (Operator adjustable)
# =============================================================================

@dataclass
class OperatingConditions:
    """
    Parameters that operators adjust on the control board to tune separation

    These determine the cut size (d50) according to fundamental physics:
        d50 = √(9·μ·Q / (π·ρ_p·ω²·R²·h))

    Adjusting these parameters shifts the separation curve.
    """

    # PRIMARY CONTROLS
    rotor_rpm: float = 3000.0  # Rotor speed [RPM]
    air_flow_m3hr: float = 2000.0  # Volumetric air flow [m³/hr]

    # SECONDARY CONTROLS (less frequently adjusted)
    feed_rate_kg_hr: float = 100.0  # Material feed rate [kg/hr]

    @property
    def rotor_omega(self) -> float:
        """Rotor angular velocity [rad/s]"""
        return self.rotor_rpm * 2.0 * PhysicalConstants.PI / 60.0

    @property
    def air_flow_m3s(self) -> float:
        """Volumetric air flow [m³/s]"""
        return self.air_flow_m3hr / 3600.0

    @property
    def feed_rate_kg_s(self) -> float:
        """Material feed rate [kg/s]"""
        return self.feed_rate_kg_hr / 3600.0

    def __str__(self) -> str:
        return f"Operating: {self.rotor_rpm:.0f} RPM, {self.air_flow_m3hr:.0f} m³/hr"


# =============================================================================
# MACHINE GEOMETRY (Fixed per machine model)
# =============================================================================

@dataclass
class ClassifierGeometry:
    """
    Fixed dimensions of the air classifier machine

    These are determined by mechanical design and rarely changed.
    Different machine models (lab-scale, pilot, industrial) have different geometries.
    """

    # MAIN CHAMBER
    chamber_radius: float = 0.5  # [m] Inner radius of cylindrical chamber
    chamber_height: float = 1.2  # [m] Height from distributor to top

    # SELECTOR (CLASSIFICATION ZONE)
    selector_radius: float = 0.1  # [m] Radius of rotating selector
    selector_z_center: float = 0.75  # [m] Vertical position of selector center
    selector_height: float = 0.1  # [m] Height of classification zone

    # FEED SYSTEM
    distributor_z: float = 0.5  # [m] Height of feed distributor plate

    # CONE SECTION
    cone_height: float = 0.866  # [m] Height of conical bottom section

    # OUTLETS
    fines_outlet_z: float = 1.2  # [m] Top outlet for fine particles
    fines_outlet_radius: float = 0.075  # [m] Fines outlet radius

    coarse_outlet_z: float = -0.866  # [m] Bottom outlet for coarse particles
    coarse_outlet_radius: float = 0.075  # [m] Coarse outlet radius

    # Derived properties
    @property
    def selector_z_min(self) -> float:
        """Bottom of selector zone [m]"""
        return self.selector_z_center - self.selector_height / 2.0

    @property
    def selector_z_max(self) -> float:
        """Top of selector zone [m]"""
        return self.selector_z_center + self.selector_height / 2.0

    @property
    def central_area(self) -> float:
        """Cross-sectional area of central upflow region [m²]"""
        return PhysicalConstants.PI * self.selector_radius**2

    @property
    def annular_area(self) -> float:
        """Cross-sectional area of annular downflow region [m²]"""
        return PhysicalConstants.PI * (self.chamber_radius**2 - self.selector_radius**2)

    @property
    def chamber_volume(self) -> float:
        """Total chamber volume [m³]"""
        cylinder_vol = PhysicalConstants.PI * self.chamber_radius**2 * self.chamber_height
        cone_vol = PhysicalConstants.PI * self.chamber_radius**2 * self.cone_height / 3.0
        return cylinder_vol + cone_vol

    def __str__(self) -> str:
        return f"Geometry: Chamber R={self.chamber_radius*1000:.0f}mm, Selector R={self.selector_radius*1000:.0f}mm"


# =============================================================================
# MATERIAL PROPERTIES (Feed-specific)
# =============================================================================

@dataclass
class MaterialProperties:
    """
    Properties of the material being classified

    These vary depending on the feed material (minerals, food powders, chemicals, etc.)
    """

    # Average particle density
    particle_density: float = 1400.0  # [kg/m³] typical for food powders

    # Size distribution of feed
    d10_um: float = 5.0  # [μm] 10th percentile
    d50_um: float = 25.0  # [μm] median size
    d90_um: float = 50.0  # [μm] 90th percentile

    # Composition (for validation)
    component_names: list = None

    def __post_init__(self):
        if self.component_names is None:
            self.component_names = ["Material"]

    @property
    def d50_m(self) -> float:
        """Median particle size [m]"""
        return self.d50_um * 1e-6

    def __str__(self) -> str:
        return f"Material: ρ={self.particle_density:.0f} kg/m³, d50={self.d50_um:.1f} μm"


# =============================================================================
# COMPLETE CONFIGURATION
# =============================================================================

@dataclass
class AirClassifierConfig:
    """
    Complete configuration for air classifier simulation

    Combines:
    - Operating conditions (tunable by operator)
    - Machine geometry (fixed per machine)
    - Material properties (feed-specific)
    - Physical constants (universal)
    """

    operating: OperatingConditions
    geometry: ClassifierGeometry
    material: MaterialProperties
    constants: PhysicalConstants = PhysicalConstants()

    def predict_d50(self) -> float:
        """
        Predict theoretical cut size from force balance

        At d50, drag force = centrifugal force:
            6πμr·v_r = m·ω²·R

        Solving for diameter:
            d50 = √(9·μ·Q / (π·ρ_p·ω²·R²·h))

        Returns:
            Predicted d50 [μm]
        """
        mu = self.constants.AIR_VISCOSITY
        Q = self.operating.air_flow_m3s
        omega = self.operating.rotor_omega
        R = self.geometry.selector_radius
        h = self.geometry.selector_height
        rho_p = self.material.particle_density

        d50_m_squared = (9.0 * mu * Q) / (
            self.constants.PI * rho_p * omega**2 * R**2 * h
        )
        d50_m = np.sqrt(d50_m_squared)

        return d50_m * 1e6  # Convert to μm

    def predict_radial_velocity_at_selector(self) -> float:
        """
        Predict radial inflow velocity at selector from continuity

        From: Q = 2π·r·h·v_r

        Returns:
            Radial velocity at selector edge [m/s] (negative = inward)
        """
        Q = self.operating.air_flow_m3s
        r = self.geometry.selector_radius
        h = self.geometry.selector_height

        v_r = -Q / (2.0 * self.constants.PI * r * h)
        return v_r

    def predict_tangential_velocity_at_selector(self) -> float:
        """
        Predict tangential velocity at selector edge

        From: v_θ = ω·r (solid body rotation at selector)

        Returns:
            Tangential velocity [m/s]
        """
        return self.operating.rotor_omega * self.geometry.selector_radius

    def predict_axial_upflow_velocity(self) -> float:
        """
        Predict axial upflow velocity in central region

        From: v_z = Q / A_central

        Returns:
            Axial velocity [m/s] (positive = upward)
        """
        return self.operating.air_flow_m3s / self.geometry.central_area

    def predict_residence_time(self) -> float:
        """
        Estimate particle residence time in chamber

        Returns:
            Typical residence time [s]
        """
        volume = self.geometry.chamber_volume
        flow = self.operating.air_flow_m3s
        return volume / flow

    def to_dict(self) -> dict:
        """
        Convert to dictionary for passing to WARP kernels

        Returns flat dictionary with all parameters needed by physics kernels.
        """
        return {
            # Geometry
            'chamber_radius': self.geometry.chamber_radius,
            'chamber_height': self.geometry.chamber_height,
            'selector_radius': self.geometry.selector_radius,
            'selector_z_center': self.geometry.selector_z_center,
            'selector_height': self.geometry.selector_height,
            'selector_z_min': self.geometry.selector_z_min,
            'selector_z_max': self.geometry.selector_z_max,
            'distributor_z': self.geometry.distributor_z,
            'cone_height': self.geometry.cone_height,
            'fines_outlet_z': self.geometry.fines_outlet_z,
            'fines_outlet_radius': self.geometry.fines_outlet_radius,
            'coarse_outlet_z': self.geometry.coarse_outlet_z,
            'coarse_outlet_radius': self.geometry.coarse_outlet_radius,

            # Operating conditions
            'rotor_omega': self.operating.rotor_omega,
            'air_flow_m3s': self.operating.air_flow_m3s,
            'air_flow_rate': self.operating.air_flow_m3hr,  # Legacy compatibility

            # Material
            'particle_density': self.material.particle_density,

            # Physical constants
            'air_density': self.constants.AIR_DENSITY,
            'air_viscosity': self.constants.AIR_VISCOSITY,
            'gravity': self.constants.GRAVITY,
        }

    def print_summary(self):
        """Print configuration summary with theoretical predictions"""
        print("=" * 70)
        print("AIR CLASSIFIER CONFIGURATION")
        print("=" * 70)
        print(f"\n{self.operating}")
        print(f"{self.geometry}")
        print(f"{self.material}")

        print("\n" + "-" * 70)
        print("THEORETICAL PREDICTIONS (from fundamental physics)")
        print("-" * 70)
        print(f"  Cut size (d50):            {self.predict_d50():.1f} μm")
        print(f"  Radial inflow at selector: {self.predict_radial_velocity_at_selector():.2f} m/s")
        print(f"  Tangential at selector:    {self.predict_tangential_velocity_at_selector():.2f} m/s")
        print(f"  Central upflow:            {self.predict_axial_upflow_velocity():.2f} m/s")
        print(f"  Residence time:            {self.predict_residence_time():.1f} s")
        print("=" * 70)


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

def create_default_config() -> AirClassifierConfig:
    """Create default configuration for protein/starch separation"""
    operating = OperatingConditions(
        rotor_rpm=3000.0,
        air_flow_m3hr=2000.0,
        feed_rate_kg_hr=100.0
    )

    geometry = ClassifierGeometry(
        chamber_radius=0.5,
        selector_radius=0.1,
        selector_z_center=0.75,
        selector_height=0.1,
        distributor_z=0.5,
        cone_height=0.866,
        fines_outlet_z=1.2,
        coarse_outlet_z=-0.866
    )

    material = MaterialProperties(
        particle_density=1400.0,
        d10_um=5.0,
        d50_um=25.0,
        d90_um=50.0,
        component_names=["Protein", "Starch"]
    )

    return AirClassifierConfig(operating, geometry, material)


def create_lab_scale_config() -> AirClassifierConfig:
    """Create lab-scale classifier configuration"""
    operating = OperatingConditions(
        rotor_rpm=5000.0,
        air_flow_m3hr=500.0,
        feed_rate_kg_hr=10.0
    )

    geometry = ClassifierGeometry(
        chamber_radius=0.2,
        selector_radius=0.05,
        selector_z_center=0.4,
        selector_height=0.05,
        distributor_z=0.25,
        cone_height=0.3,
        fines_outlet_z=0.6,
        coarse_outlet_z=-0.3
    )

    material = MaterialProperties(
        particle_density=1400.0,
        d50_um=20.0
    )

    return AirClassifierConfig(operating, geometry, material)


# =============================================================================
# OPERATING POINT CALCULATOR
# =============================================================================

class OperatingPointCalculator:
    """
    Calculate required operating conditions to achieve target d50

    Based on fundamental force balance equation:
        d50 = √(9·μ·Q / (π·ρ_p·ω²·R²·h))
    """

    @staticmethod
    def rpm_for_target_d50(
        target_d50_um: float,
        air_flow_m3hr: float,
        geometry: ClassifierGeometry,
        material: MaterialProperties,
        constants: PhysicalConstants = PhysicalConstants()
    ) -> float:
        """
        Calculate required rotor RPM to achieve target d50

        Args:
            target_d50_um: Desired cut size [μm]
            air_flow_m3hr: Air flow rate [m³/hr]
            geometry: Machine geometry
            material: Material properties
            constants: Physical constants

        Returns:
            Required rotor RPM
        """
        d50_m = target_d50_um * 1e-6
        Q = air_flow_m3hr / 3600.0
        mu = constants.AIR_VISCOSITY
        rho_p = material.particle_density
        R = geometry.selector_radius
        h = geometry.selector_height
        PI = constants.PI

        omega_squared = (9.0 * mu * Q) / (d50_m**2 * PI * rho_p * R**2 * h)
        omega = np.sqrt(omega_squared)
        rpm = omega * 60.0 / (2.0 * PI)

        return rpm

    @staticmethod
    def airflow_for_target_d50(
        target_d50_um: float,
        rotor_rpm: float,
        geometry: ClassifierGeometry,
        material: MaterialProperties,
        constants: PhysicalConstants = PhysicalConstants()
    ) -> float:
        """
        Calculate required air flow to achieve target d50

        Args:
            target_d50_um: Desired cut size [μm]
            rotor_rpm: Rotor speed [RPM]
            geometry: Machine geometry
            material: Material properties
            constants: Physical constants

        Returns:
            Required air flow [m³/hr]
        """
        d50_m = target_d50_um * 1e-6
        omega = rotor_rpm * 2.0 * constants.PI / 60.0
        mu = constants.AIR_VISCOSITY
        rho_p = material.particle_density
        R = geometry.selector_radius
        h = geometry.selector_height
        PI = constants.PI

        Q_m3s = (d50_m**2 * PI * rho_p * omega**2 * R**2 * h) / (9.0 * mu)
        Q_m3hr = Q_m3s * 3600.0

        return Q_m3hr


if __name__ == "__main__":
    """Test configuration and predictions"""

    print("\n" + "=" * 70)
    print("CONTROL PARAMETERS TEST")
    print("=" * 70)

    # Create default config
    config = create_default_config()
    config.print_summary()

    # Test operating point calculator
    print("\n" + "=" * 70)
    print("OPERATING POINT CALCULATOR")
    print("=" * 70)

    target_d50 = 20.0  # μm
    print(f"\nTarget d50: {target_d50:.1f} μm")
    print("-" * 70)

    # Option 1: Adjust RPM
    rpm_needed = OperatingPointCalculator.rpm_for_target_d50(
        target_d50, 2000.0, config.geometry, config.material
    )
    print(f"Option 1: At Q=2000 m³/hr, need RPM = {rpm_needed:.0f}")

    # Option 2: Adjust air flow
    flow_needed = OperatingPointCalculator.airflow_for_target_d50(
        target_d50, 3000.0, config.geometry, config.material
    )
    print(f"Option 2: At RPM=3000, need Q = {flow_needed:.0f} m³/hr")

    print("\n" + "=" * 70)
    print("✓ Control parameters module ready")
    print("=" * 70)

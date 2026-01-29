"""
Corrected Air Classifier Configuration

Based on: docs/corrected_classifier_geometry.md
Configuration for Cyclone Air Classifier (Humboldt Wedag type)
Optimized for yellow pea protein/starch separation at d50 = 20 μm
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class CorrectedClassifierConfig:
    """
    CORRECTED geometry configuration for Cyclone Air Classifier

    Based on Klumpar et al. (1986) Figure 11 - Cyclone Air Classifier
    with external fines collection system.

    All dimensions follow the corrected specifications from
    corrected_classifier_geometry.md Section 4.
    """

    # === CLASSIFICATION CHAMBER ===
    chamber_diameter: float = 1.0        # m (1000 mm)
    chamber_height: float = 1.2          # m (cylindrical section)
    chamber_wall_thickness: float = 0.004  # m (4mm SS304)

    # === CONICAL SECTION ===
    cone_angle: float = 60.0             # degrees (included angle)
    cone_wall_thickness: float = 0.004   # m (4mm SS304)

    # === SELECTOR ROTOR (CORRECTED) ===
    selector_diameter: float = 0.400     # m (400 mm)
    selector_blade_count: int = 24
    selector_blade_height: float = 0.500 # m (REDUCED from 0.6)
    selector_blade_thickness: float = 0.004  # m (REDUCED from 5mm)
    selector_zone_bottom: float = 0.45   # m (RAISED from 0.35)
    selector_zone_top: float = 0.95      # m
    selector_blade_lean_angle: float = 5.0  # degrees forward lean

    # === HUB ASSEMBLY (NEW - WAS INCOMPLETE) ===
    hub_outer_diameter: float = 0.300    # m (300 mm)
    hub_inner_diameter: float = 0.120    # m (120 mm)
    hub_height: float = 0.500            # m
    hub_port_count: int = 8
    hub_port_diameter: float = 0.040     # m (40 mm)
    hub_port_angle: float = 30.0         # degrees downward

    # === DISTRIBUTOR PLATE (CORRECTED) ===
    distributor_diameter: float = 0.450  # m (REDUCED from 0.5)
    distributor_position_z: float = 0.35 # m (RAISED from 0.25)
    distributor_thickness: float = 0.008 # m (8 mm)
    distributor_lip_height: float = 0.015  # m (15 mm)
    distributor_groove_count: int = 24
    distributor_groove_depth: float = 0.002  # m (2 mm)
    distributor_groove_width: float = 0.005  # m (5 mm)

    # === VERTICAL SHAFT (CORRECTED) ===
    shaft_diameter: float = 0.080        # m (REDUCED from 0.1)
    shaft_bottom_z: float = -0.90        # m (EXTENDED)
    shaft_top_z: float = 1.50            # m (EXTENDED)
    shaft_material: str = "SS316"

    # === AIR INLETS (CORRECTED) ===
    air_inlet_count: int = 4
    air_inlet_diameter: float = 0.150    # m (150 mm each)
    air_inlet_position_z: float = 0.15   # m (above cone junction)
    air_inlet_vane_count: int = 6        # guide vanes per inlet
    air_inlet_vane_angle: float = 45.0   # degrees from radial
    air_inlet_velocity_design: float = 17.5  # m/s (15-20 range)

    # === FINES OUTLET (TO EXTERNAL CYCLONE) ===
    fines_outlet_diameter: float = 0.200  # m (200 mm)
    fines_outlet_position_z: float = 1.20  # m (at chamber top)

    # === COARSE OUTLET ===
    coarse_outlet_diameter: float = 0.150  # m (150 mm)

    # === EXTERNAL CYCLONE (STAIRMAND HIGH-EFFICIENCY) ===
    cyclone_body_diameter: float = 0.500   # m (500 mm)
    cyclone_inlet_height: float = 0.250    # m (a = 0.5D)
    cyclone_inlet_width: float = 0.100     # m (b = 0.2D)
    cyclone_vortex_finder_diameter: float = 0.250  # m (Dx = 0.5D)
    cyclone_vortex_finder_length: float = 0.250    # m (S = 0.5D)
    cyclone_cylinder_height: float = 0.750  # m (h = 1.5D)
    cyclone_cone_height: float = 1.250     # m (Hc = 2.5D)
    cyclone_dust_outlet: float = 0.200     # m (B = 0.4D)
    cyclone_offset_x: float = 1.0          # m (horizontal offset from chamber)

    # === DAMPER (IRIS TYPE) ===
    damper_diameter: float = 0.200         # m (200 mm nominal)
    damper_position_z: float = 1.10        # m (below fines outlet)
    damper_opening_range: tuple = field(default_factory=lambda: (0.5, 1.0))  # 50-100% open

    # === OPERATING PARAMETERS ===
    rotor_rpm_min: float = 1500
    rotor_rpm_max: float = 4000
    rotor_rpm_design: float = 3000
    air_flow_design: float = 3000          # m³/hr
    feed_rate_design: float = 200          # kg/hr
    target_d50: float = 20.0               # μm

    # === MATERIAL SPECIFICATIONS ===
    chamber_material: str = "SS304"
    wear_liner_material: str = "Hardox 400"
    cone_liner_material: str = "Alumina ceramic"
    selector_blade_material: str = "SS304"
    distributor_coating: str = "WC-Co"     # Tungsten carbide coating

    @property
    def cone_height(self) -> float:
        """Calculate cone height from chamber radius and angle"""
        half_angle = np.radians(self.cone_angle / 2)
        return (self.chamber_diameter / 2) / np.tan(half_angle)

    @property
    def total_chamber_height(self) -> float:
        """Total classifier height (cylinder + cone)"""
        return self.chamber_height + self.cone_height

    @property
    def selector_blade_gap(self) -> float:
        """Gap between selector blades at outer radius"""
        circumference = np.pi * self.selector_diameter
        total_blade_width = self.selector_blade_count * self.selector_blade_thickness
        return (circumference - total_blade_width) / self.selector_blade_count

    @property
    def solidity_ratio(self) -> float:
        """Selector blade solidity ratio (blade area / total area)"""
        circumference = np.pi * self.selector_diameter
        total_blade_width = self.selector_blade_count * self.selector_blade_thickness
        return total_blade_width / circumference

    @property
    def tip_speed_design(self) -> float:
        """Rotor tip speed at design RPM (m/s)"""
        omega = self.rotor_rpm_design * 2 * np.pi / 60
        return omega * (self.selector_diameter / 2)

    @property
    def cyclone_total_height(self) -> float:
        """Total cyclone height (cylinder + cone)"""
        return self.cyclone_cylinder_height + self.cyclone_cone_height

    @property
    def chamber_volume(self) -> float:
        """Chamber volume (m³)"""
        vol_cylinder = np.pi * (self.chamber_diameter / 2)**2 * self.chamber_height
        vol_cone = (1/3) * np.pi * (self.chamber_diameter / 2)**2 * self.cone_height
        return vol_cylinder + vol_cone

    def calculate_cut_size(self, rotor_rpm: float, air_flow: float,
                          particle_density: float = 1400) -> float:
        """
        Calculate theoretical cut size (d50) for given operating conditions

        Based on Section 8.1.1 of corrected_classifier_geometry.md
        Uses simplified Stokes equilibrium for centrifugal classifiers

        Args:
            rotor_rpm: Rotor speed (rpm)
            air_flow: Air flow rate (m³/hr)
            particle_density: Particle density (kg/m³), default 1400 (avg protein/starch)

        Returns:
            Cut size d50 in micrometers
        """
        # Air viscosity at 20°C
        mu = 1.81e-5  # Pa·s
        rho_air = 1.2  # kg/m³

        # Convert air flow to m³/s
        Q = air_flow / 3600

        # Angular velocity
        omega = rotor_rpm * 2 * np.pi / 60  # rad/s

        # Selector rotor radius
        r = self.selector_diameter / 2

        # Blade height
        h = self.selector_blade_height

        # Radial air velocity through selector cage
        circumference = 2 * np.pi * r
        v_r = Q / (circumference * h)

        # Stokes regime cut size calculation
        # Balance: Drag force = Centrifugal force
        # 3*pi*mu*d*v_r = (pi/6)*d³*(rho_p - rho_air)*omega²*r
        # Simplified form accounting for radial velocity:
        d50_squared = (18 * mu * v_r) / ((particle_density - rho_air) * omega**2 * r)
        d50 = np.sqrt(d50_squared)

        return d50 * 1e6  # Convert to micrometers

    def calculate_required_rpm(self, target_d50_um: float, air_flow: float,
                               particle_density: float = 1400) -> float:
        """
        Calculate required RPM to achieve target cut size

        Args:
            target_d50_um: Target cut size (μm)
            air_flow: Air flow rate (m³/hr)
            particle_density: Particle density (kg/m³)

        Returns:
            Required rotor speed (rpm)
        """
        mu = 1.81e-5
        Q = air_flow / 3600
        r = self.selector_diameter / 2
        h = self.selector_blade_height
        d50 = target_d50_um * 1e-6  # Convert to meters

        # Solve for omega
        omega_squared = (9 * mu * Q) / (2 * np.pi * particle_density * d50**2 * r**2 * h)
        omega = np.sqrt(omega_squared)

        # Convert to RPM
        rpm = omega * 60 / (2 * np.pi)
        return rpm

    def print_specifications(self):
        """Print comprehensive corrected specifications"""
        print("=" * 80)
        print("CORRECTED AIR CLASSIFIER SPECIFICATIONS")
        print("Cyclone Air Classifier Configuration (Humboldt Wedag Type)")
        print("=" * 80)

        print("\n📐 CLASSIFICATION CHAMBER:")
        print(f"  Chamber Diameter:        {self.chamber_diameter:.3f} m ({self.chamber_diameter*1000:.0f} mm)")
        print(f"  Chamber Height:          {self.chamber_height:.3f} m ({self.chamber_height*1000:.0f} mm)")
        print(f"  Cone Height:             {self.cone_height:.3f} m ({self.cone_height*1000:.0f} mm)")
        print(f"  Cone Angle:              {self.cone_angle:.0f}° (included angle)")
        print(f"  Total Height:            {self.total_chamber_height:.3f} m")
        print(f"  Chamber Volume:          {self.chamber_volume:.3f} m³ ({self.chamber_volume*1000:.0f} L)")
        print(f"  Material:                {self.chamber_material} {self.chamber_wall_thickness*1000:.0f}mm")

        print("\n⚙️  SELECTOR ROTOR (CORRECTED):")
        print(f"  Selector Diameter:       {self.selector_diameter:.3f} m ({self.selector_diameter*1000:.0f} mm)")
        print(f"  Number of Blades:        {self.selector_blade_count}")
        print(f"  Blade Height:            {self.selector_blade_height:.3f} m ({self.selector_blade_height*1000:.0f} mm)")
        print(f"  Blade Thickness:         {self.selector_blade_thickness*1000:.1f} mm")
        print(f"  Blade Gap:               {self.selector_blade_gap*1000:.1f} mm")
        print(f"  Solidity Ratio:          {self.solidity_ratio:.3f}")
        print(f"  Blade Lean Angle:        {self.selector_blade_lean_angle:.1f}° forward")
        print(f"  Selector Zone:           Z = {self.selector_zone_bottom:.2f}m to {self.selector_zone_top:.2f}m")
        print(f"  Material:                {self.selector_blade_material}")

        print("\n🔧 HUB ASSEMBLY (CORRECTED):")
        print(f"  Hub Outer Diameter:      {self.hub_outer_diameter:.3f} m ({self.hub_outer_diameter*1000:.0f} mm)")
        print(f"  Hub Inner Diameter:      {self.hub_inner_diameter:.3f} m ({self.hub_inner_diameter*1000:.0f} mm)")
        print(f"  Hub Height:              {self.hub_height:.3f} m ({self.hub_height*1000:.0f} mm)")
        print(f"  Number of Feed Ports:    {self.hub_port_count}")
        print(f"  Port Diameter:           {self.hub_port_diameter*1000:.0f} mm")
        print(f"  Port Angle:              {self.hub_port_angle:.0f}° downward")

        print("\n🔄 DISTRIBUTOR PLATE (CORRECTED):")
        print(f"  Plate Diameter:          {self.distributor_diameter:.3f} m ({self.distributor_diameter*1000:.0f} mm)")
        print(f"  Position:                Z = {self.distributor_position_z:.2f} m")
        print(f"  Thickness:               {self.distributor_thickness*1000:.0f} mm")
        print(f"  Edge Lip Height:         {self.distributor_lip_height*1000:.0f} mm")
        print(f"  Radial Grooves:          {self.distributor_groove_count} grooves")
        print(f"  Surface Coating:         {self.distributor_coating} (wear resistant)")

        print("\n🌀 AIR DISTRIBUTION (CORRECTED):")
        print(f"  Number of Inlets:        {self.air_inlet_count}")
        print(f"  Inlet Diameter:          {self.air_inlet_diameter*1000:.0f} mm each")
        print(f"  Inlet Position:          Z = {self.air_inlet_position_z:.2f} m")
        print(f"  Guide Vanes per Inlet:   {self.air_inlet_vane_count}")
        print(f"  Vane Angle:              {self.air_inlet_vane_angle:.0f}° from radial")
        print(f"  Design Inlet Velocity:   {self.air_inlet_velocity_design:.1f} m/s")

        print("\n🌪️  EXTERNAL CYCLONE (STAIRMAND HIGH-EFFICIENCY):")
        print(f"  Body Diameter:           {self.cyclone_body_diameter:.3f} m ({self.cyclone_body_diameter*1000:.0f} mm)")
        print(f"  Inlet Dimensions:        {self.cyclone_inlet_width*1000:.0f} × {self.cyclone_inlet_height*1000:.0f} mm")
        print(f"  Vortex Finder:           Ø{self.cyclone_vortex_finder_diameter*1000:.0f} mm × {self.cyclone_vortex_finder_length*1000:.0f} mm")
        print(f"  Cylinder Height:         {self.cyclone_cylinder_height:.3f} m")
        print(f"  Cone Height:             {self.cyclone_cone_height:.3f} m")
        print(f"  Total Height:            {self.cyclone_total_height:.3f} m")
        print(f"  Dust Outlet:             Ø{self.cyclone_dust_outlet*1000:.0f} mm")
        print(f"  Expected Efficiency:     >95% for d > 5 μm")

        print("\n📊 OPERATING PARAMETERS:")
        print(f"  Rotor Speed Range:       {self.rotor_rpm_min:.0f} - {self.rotor_rpm_max:.0f} rpm")
        print(f"  Design Rotor Speed:      {self.rotor_rpm_design:.0f} rpm")
        print(f"  Design Air Flow:         {self.air_flow_design:.0f} m³/hr")
        print(f"  Design Feed Rate:        {self.feed_rate_design:.0f} kg/hr")
        print(f"  Target Cut Size:         {self.target_d50:.1f} μm")
        print(f"  Tip Speed at Design:     {self.tip_speed_design:.1f} m/s")

        # Calculate predicted cut size
        predicted_d50 = self.calculate_cut_size(self.rotor_rpm_design, self.air_flow_design)
        print(f"  Predicted d₅₀:           {predicted_d50:.1f} μm")

        print("\n🎯 DESIGN RATIOS:")
        print(f"  D_selector/D_chamber:    {self.selector_diameter/self.chamber_diameter:.2f}")
        print(f"  D_distributor/D_chamber: {self.distributor_diameter/self.chamber_diameter:.2f}")
        print(f"  H_chamber/D_chamber:     {self.chamber_height/self.chamber_diameter:.2f}")

        print("\n✅ KEY CORRECTIONS FROM ORIGINAL:")
        print("  • Selector blade height REDUCED: 600mm → 500mm (-17%)")
        print("  • Selector blade thickness REDUCED: 5mm → 4mm (-20%)")
        print("  • Blade gap INCREASED: 47.4mm → 48.5mm (+2%)")
        print("  • Selector zone RAISED: Z=0.35m → Z=0.45m (+0.10m)")
        print("  • Distributor diameter REDUCED: 500mm → 450mm (-10%)")
        print("  • Distributor position RAISED: Z=0.25m → Z=0.35m (+0.10m)")
        print("  • Shaft diameter REDUCED: 100mm → 80mm (-20%)")
        print("  • Hub assembly FULLY SPECIFIED (was incomplete)")
        print("  • External cyclone ADDED (critical component)")
        print("  • Air inlet guide vanes ADDED (6 per inlet @ 45°)")

        print("=" * 80)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'chamber_diameter': self.chamber_diameter,
            'chamber_height': self.chamber_height,
            'cone_angle': self.cone_angle,
            'selector_diameter': self.selector_diameter,
            'selector_blade_count': self.selector_blade_count,
            'selector_blade_height': self.selector_blade_height,
            'hub_outer_diameter': self.hub_outer_diameter,
            'distributor_diameter': self.distributor_diameter,
            'shaft_diameter': self.shaft_diameter,
            'cyclone_body_diameter': self.cyclone_body_diameter,
            'rotor_rpm_design': self.rotor_rpm_design,
            'air_flow_design': self.air_flow_design,
            'target_d50': self.target_d50
        }


def create_default_config() -> CorrectedClassifierConfig:
    """
    Create default corrected classifier configuration

    Returns:
        CorrectedClassifierConfig with default values
    """
    return CorrectedClassifierConfig()


def create_scaled_config(scale_factor: float) -> CorrectedClassifierConfig:
    """
    Create scaled classifier configuration

    Args:
        scale_factor: Scaling factor (1.0 = default, 0.5 = half size, etc.)

    Returns:
        Scaled CorrectedClassifierConfig
    """
    config = CorrectedClassifierConfig()

    # Scale geometric dimensions
    config.chamber_diameter *= scale_factor
    config.chamber_height *= scale_factor
    config.selector_diameter *= scale_factor
    config.selector_blade_height *= scale_factor
    config.hub_outer_diameter *= scale_factor
    config.hub_inner_diameter *= scale_factor
    config.distributor_diameter *= scale_factor
    config.shaft_diameter *= scale_factor
    config.cyclone_body_diameter *= scale_factor

    # Scale positions
    config.distributor_position_z *= scale_factor
    config.selector_zone_bottom *= scale_factor
    config.selector_zone_top *= scale_factor
    config.air_inlet_position_z *= scale_factor

    # Scale throughputs proportionally to area (scale^2)
    config.feed_rate_design *= scale_factor**2
    config.air_flow_design *= scale_factor**2

    return config


if __name__ == "__main__":
    # Example usage
    config = create_default_config()
    config.print_specifications()

    print("\n\n🔬 CUT SIZE ANALYSIS:")
    print("=" * 60)
    print(f"{'RPM':<10} {'Air Flow (m³/hr)':<18} {'d₅₀ (μm)':<12}")
    print("-" * 60)

    for rpm in range(1500, 4500, 500):
        for flow in [2500, 3000, 3500]:
            d50 = config.calculate_cut_size(rpm, flow)
            print(f"{rpm:<10} {flow:<18} {d50:<12.1f}")

    print("\n✓ Configuration module loaded successfully")

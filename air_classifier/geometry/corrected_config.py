"""
CORRECTED Air Classifier Configuration for d50 = 20 μm

IMPORTANT: This file supersedes the previous corrected_config.py
The previous version had geometry sized for COARSE cuts (50-150 μm).
This version has geometry correctly sized for FINE cuts (~20 μm).

For yellow pea protein/starch separation:
- Protein particles: 3-10 μm (mean ~5 μm)
- Starch granules: 15-40 μm (mean ~28 μm)
- Target cut: d50 = 20 μm

Key insight: Fine cuts require SMALLER rotor with SHORTER blades!
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple


@dataclass
class CorrectedClassifierConfig:
    """
    CORRECTED geometry configuration for Cyclone Air Classifier
    
    CRITICAL FIX: Selector rotor sized for d50 = 20 μm, not 4 μm!
    
    The cut size formula is:
        d50² = 9·μ·Q / (π·ρ_p·ω²·r²·h)
        
    For d50 = 20 μm at 3000 RPM with 2000 m³/hr:
        Need r²·h ≈ 0.001 m³
        → r = 0.1 m (200 mm diameter), h = 0.1 m (100 mm height)
    
    Previous WRONG values had r²·h = 0.02 m³ (20× too large!)
    """

    # === CLASSIFICATION CHAMBER ===
    # Chamber can stay large - it's the ROTOR that determines cut size
    chamber_diameter: float = 1.0        # m (1000 mm)
    chamber_height: float = 1.2          # m (cylindrical section)
    chamber_wall_thickness: float = 0.004  # m (4mm SS304)

    # === CONICAL SECTION ===
    cone_angle: float = 60.0             # degrees (included angle)
    cone_wall_thickness: float = 0.004   # m (4mm SS304)

    # === SELECTOR ROTOR (*** CRITICAL CORRECTION ***) ===
    # For d50 = 20 μm, need MUCH smaller rotor!
    selector_diameter: float = 0.200     # m (200 mm) *** WAS 400 mm ***
    selector_blade_count: int = 18       # *** WAS 24 ***
    selector_blade_height: float = 0.100 # m (100 mm) *** WAS 500 mm ***
    selector_blade_thickness: float = 0.003  # m (3 mm)
    selector_zone_bottom: float = 0.70   # m (raised to allow larger annular gap)
    selector_zone_top: float = 0.80      # m
    selector_blade_lean_angle: float = 5.0  # degrees forward lean

    # === HUB ASSEMBLY (*** SIZED FOR SMALLER ROTOR ***) ===
    hub_outer_diameter: float = 0.120    # m (120 mm) *** WAS 300 mm ***
    hub_inner_diameter: float = 0.060    # m (60 mm) *** WAS 120 mm ***
    hub_height: float = 0.100            # m (matches blade height)
    hub_port_count: int = 6              # *** WAS 8 ***
    hub_port_diameter: float = 0.025     # m (25 mm) *** WAS 40 mm ***
    hub_port_angle: float = 30.0         # degrees downward

    # === DISTRIBUTOR PLATE ===
    # Can be larger than rotor - spreads material into air stream
    distributor_diameter: float = 0.350  # m (350 mm)
    distributor_position_z: float = 0.50 # m (below selector)
    distributor_thickness: float = 0.008 # m (8 mm)
    distributor_lip_height: float = 0.015  # m (15 mm)
    distributor_groove_count: int = 16
    distributor_groove_depth: float = 0.002  # m (2 mm)
    distributor_groove_width: float = 0.005  # m (5 mm)

    # === VERTICAL SHAFT ===
    shaft_diameter: float = 0.050        # m (50 mm) *** WAS 80 mm ***
    shaft_bottom_z: float = -0.90        # m
    shaft_top_z: float = 1.50            # m
    shaft_material: str = "SS316"

    # === AIR INLETS ===
    air_inlet_count: int = 4
    air_inlet_diameter: float = 0.125    # m (125 mm) *** ADJUSTED ***
    air_inlet_position_z: float = 0.15   # m (above cone junction)
    air_inlet_vane_count: int = 6        # guide vanes per inlet
    air_inlet_vane_angle: float = 45.0   # degrees from radial
    air_inlet_velocity_design: float = 15.0  # m/s

    # === FINES OUTLET (TO EXTERNAL CYCLONE) ===
    fines_outlet_diameter: float = 0.150  # m (150 mm)
    fines_outlet_position_z: float = 1.20  # m (at chamber top)

    # === COARSE OUTLET ===
    coarse_outlet_diameter: float = 0.150  # m (150 mm)

    # === EXTERNAL CYCLONE (STAIRMAND HIGH-EFFICIENCY) ===
    # Sized for the reduced air flow
    cyclone_body_diameter: float = 0.400   # m (400 mm) *** WAS 500 mm ***
    cyclone_inlet_height: float = 0.200    # m (a = 0.5D)
    cyclone_inlet_width: float = 0.080     # m (b = 0.2D)
    cyclone_vortex_finder_diameter: float = 0.200  # m (Dx = 0.5D)
    cyclone_vortex_finder_length: float = 0.200    # m (S = 0.5D)
    cyclone_cylinder_height: float = 0.600  # m (h = 1.5D)
    cyclone_cone_height: float = 1.000     # m (Hc = 2.5D)
    cyclone_dust_outlet: float = 0.160     # m (B = 0.4D)
    cyclone_offset_x: float = 0.9          # m (horizontal offset from chamber)

    # === DAMPER (IRIS TYPE) ===
    damper_diameter: float = 0.150         # m (150 mm nominal)
    damper_position_z: float = 1.10        # m (below fines outlet)
    damper_opening_range: Tuple[float, float] = field(default_factory=lambda: (0.5, 1.0))

    # === OPERATING PARAMETERS (*** ADJUSTED FOR NEW GEOMETRY ***) ===
    rotor_rpm_min: float = 2000            # *** WAS 1500 ***
    rotor_rpm_max: float = 5000            # *** WAS 4000 ***
    rotor_rpm_design: float = 3000         # Design point
    air_flow_design: float = 2000          # m³/hr *** WAS 3000 ***
    feed_rate_design: float = 200          # kg/hr
    target_d50: float = 20.0               # μm

    # === MATERIAL SPECIFICATIONS ===
    chamber_material: str = "SS304"
    wear_liner_material: str = "Hardox 400"
    cone_liner_material: str = "Alumina ceramic"
    selector_blade_material: str = "SS304"
    distributor_coating: str = "WC-Co"     # Tungsten carbide coating

    # === PHYSICAL CONSTANTS ===
    air_viscosity: float = 1.81e-5         # Pa·s at 20°C
    air_density: float = 1.2               # kg/m³
    protein_density: float = 1350          # kg/m³
    starch_density: float = 1520           # kg/m³

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
    def selector_radius(self) -> float:
        """Selector rotor radius"""
        return self.selector_diameter / 2

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
        return omega * self.selector_radius

    @property
    def r_squared_h_product(self) -> float:
        """
        The r²·h product that determines cut size
        
        d50² ∝ 1/(r²·h)
        
        For fine cuts (20 μm), need small r²·h (~0.001 m³)
        For coarse cuts (100 μm), need large r²·h (~0.025 m³)
        """
        return self.selector_radius**2 * self.selector_blade_height

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

    @property
    def annular_gap(self) -> float:
        """Gap between selector rotor and chamber wall"""
        return (self.chamber_diameter - self.selector_diameter) / 2

    def calculate_cut_size(self, rotor_rpm: float, air_flow_m3hr: float,
                          particle_density: float = 1400) -> float:
        """
        Calculate theoretical cut size (d50) for given operating conditions
        
        Uses the equilibrium balance between drag and centrifugal forces:
        
            Drag force = Centrifugal force
            3·π·μ·d·v_r = (π/6)·d³·ρ_p·ω²·r
            
        Solving for d:
            d² = 18·μ·v_r / (ρ_p·ω²·r)
            
        Where v_r = Q / (2·π·r·h) is the radial air velocity at the rotor
        
        Substituting:
            d50² = 9·μ·Q / (π·ρ_p·ω²·r²·h)

        Args:
            rotor_rpm: Rotor speed (rpm)
            air_flow_m3hr: Air flow rate (m³/hr)
            particle_density: Particle density (kg/m³), default 1400 (avg protein/starch)

        Returns:
            Cut size d50 in micrometers
        """
        # Convert units
        Q = air_flow_m3hr / 3600  # m³/s
        omega = rotor_rpm * 2 * np.pi / 60  # rad/s
        
        # Rotor geometry
        r = self.selector_radius
        h = self.selector_blade_height
        
        # Use net density (particle - air) for buoyancy correction
        rho_net = particle_density - self.air_density
        
        # Cut size formula
        # d50² = 9·μ·Q / (π·ρ_p·ω²·r²·h)
        numerator = 9 * self.air_viscosity * Q
        denominator = np.pi * rho_net * omega**2 * r**2 * h
        
        d50_squared = numerator / denominator
        d50_m = np.sqrt(d50_squared)
        
        return d50_m * 1e6  # Convert to micrometers

    def calculate_required_rpm(self, target_d50_um: float, air_flow_m3hr: float,
                               particle_density: float = 1400) -> float:
        """
        Calculate required RPM to achieve target cut size
        
        Rearranging d50² = 9·μ·Q / (π·ρ_p·ω²·r²·h) for ω:
            ω² = 9·μ·Q / (π·ρ_p·d50²·r²·h)

        Args:
            target_d50_um: Target cut size (μm)
            air_flow_m3hr: Air flow rate (m³/hr)
            particle_density: Particle density (kg/m³)

        Returns:
            Required rotor speed (rpm)
        """
        Q = air_flow_m3hr / 3600  # m³/s
        d50 = target_d50_um * 1e-6  # m
        r = self.selector_radius
        h = self.selector_blade_height
        rho_net = particle_density - self.air_density
        
        # Solve for omega
        omega_squared = (9 * self.air_viscosity * Q) / (np.pi * rho_net * d50**2 * r**2 * h)
        omega = np.sqrt(omega_squared)
        
        # Convert to RPM
        return omega * 60 / (2 * np.pi)

    def calculate_required_airflow(self, target_d50_um: float, rotor_rpm: float,
                                    particle_density: float = 1400) -> float:
        """
        Calculate required air flow to achieve target cut size at given RPM
        
        Rearranging: Q = π·ρ_p·d50²·ω²·r²·h / (9·μ)

        Args:
            target_d50_um: Target cut size (μm)
            rotor_rpm: Rotor speed (rpm)
            particle_density: Particle density (kg/m³)

        Returns:
            Required air flow (m³/hr)
        """
        d50 = target_d50_um * 1e-6  # m
        omega = rotor_rpm * 2 * np.pi / 60  # rad/s
        r = self.selector_radius
        h = self.selector_blade_height
        rho_net = particle_density - self.air_density
        
        Q = (np.pi * rho_net * d50**2 * omega**2 * r**2 * h) / (9 * self.air_viscosity)
        
        return Q * 3600  # Convert to m³/hr

    def validate_geometry_for_target(self) -> Dict[str, Any]:
        """
        Validate that geometry can achieve target d50
        
        Returns dict with validation results
        """
        # Calculate d50 at design conditions
        d50_at_design = self.calculate_cut_size(self.rotor_rpm_design, self.air_flow_design)
        
        # Calculate d50 at min/max RPM
        d50_at_min_rpm = self.calculate_cut_size(self.rotor_rpm_min, self.air_flow_design)
        d50_at_max_rpm = self.calculate_cut_size(self.rotor_rpm_max, self.air_flow_design)
        
        # Calculate required RPM for target
        rpm_for_target = self.calculate_required_rpm(self.target_d50, self.air_flow_design)
        
        # Check if target is achievable
        target_achievable = self.rotor_rpm_min <= rpm_for_target <= self.rotor_rpm_max
        
        # Check tip speed at required RPM
        omega_at_target = rpm_for_target * 2 * np.pi / 60
        tip_speed_at_target = omega_at_target * self.selector_radius
        
        return {
            'd50_at_design_rpm': d50_at_design,
            'd50_at_min_rpm': d50_at_min_rpm,
            'd50_at_max_rpm': d50_at_max_rpm,
            'd50_range': (d50_at_max_rpm, d50_at_min_rpm),  # Note: higher RPM = smaller d50
            'rpm_for_target_d50': rpm_for_target,
            'target_achievable': target_achievable,
            'tip_speed_at_target': tip_speed_at_target,
            'tip_speed_safe': tip_speed_at_target < 100,  # m/s limit
            'r_squared_h': self.r_squared_h_product,
        }

    def print_specifications(self):
        """Print comprehensive corrected specifications"""
        print("=" * 80)
        print("CORRECTED AIR CLASSIFIER SPECIFICATIONS (v2.0)")
        print("Geometry Sized for d50 = 20 μm (Yellow Pea Protein Separation)")
        print("=" * 80)
        
        # Validate first
        validation = self.validate_geometry_for_target()
        
        print("\n" + "!" * 80)
        print("!!! CRITICAL GEOMETRY CHANGE FROM v1.0 !!!")
        print("!" * 80)
        print(f"  OLD: Selector Ø400mm × H500mm → d50 = 4 μm (TOO FINE!)")
        print(f"  NEW: Selector Ø{self.selector_diameter*1000:.0f}mm × H{self.selector_blade_height*1000:.0f}mm → d50 = {validation['d50_at_design_rpm']:.1f} μm")
        print(f"  r²·h product: {self.r_squared_h_product:.6f} m³ (was 0.020 m³)")
        print("!" * 80)

        print("\n📐 CLASSIFICATION CHAMBER:")
        print(f"  Chamber Diameter:        {self.chamber_diameter:.3f} m ({self.chamber_diameter*1000:.0f} mm)")
        print(f"  Chamber Height:          {self.chamber_height:.3f} m ({self.chamber_height*1000:.0f} mm)")
        print(f"  Cone Height:             {self.cone_height:.3f} m ({self.cone_height*1000:.0f} mm)")
        print(f"  Cone Angle:              {self.cone_angle:.0f}° (included angle)")
        print(f"  Total Height:            {self.total_chamber_height:.3f} m")
        print(f"  Annular Gap:             {self.annular_gap*1000:.0f} mm")

        print("\n⚙️  SELECTOR ROTOR (*** KEY CHANGE ***):")
        print(f"  Selector Diameter:       {self.selector_diameter:.3f} m ({self.selector_diameter*1000:.0f} mm)")
        print(f"  Number of Blades:        {self.selector_blade_count}")
        print(f"  Blade Height:            {self.selector_blade_height:.3f} m ({self.selector_blade_height*1000:.0f} mm)")
        print(f"  Blade Thickness:         {self.selector_blade_thickness*1000:.1f} mm")
        print(f"  Blade Gap:               {self.selector_blade_gap*1000:.1f} mm")
        print(f"  r²·h Product:            {self.r_squared_h_product:.6f} m³")

        print("\n🔧 HUB ASSEMBLY:")
        print(f"  Hub Outer Diameter:      {self.hub_outer_diameter:.3f} m ({self.hub_outer_diameter*1000:.0f} mm)")
        print(f"  Hub Inner Diameter:      {self.hub_inner_diameter:.3f} m ({self.hub_inner_diameter*1000:.0f} mm)")
        print(f"  Number of Feed Ports:    {self.hub_port_count}")
        print(f"  Port Diameter:           {self.hub_port_diameter*1000:.0f} mm")

        print("\n🔄 DISTRIBUTOR PLATE:")
        print(f"  Plate Diameter:          {self.distributor_diameter:.3f} m ({self.distributor_diameter*1000:.0f} mm)")
        print(f"  Position:                Z = {self.distributor_position_z:.2f} m")

        print("\n🌀 AIR SYSTEM:")
        print(f"  Number of Inlets:        {self.air_inlet_count}")
        print(f"  Inlet Diameter:          {self.air_inlet_diameter*1000:.0f} mm each")
        print(f"  Design Air Flow:         {self.air_flow_design:.0f} m³/hr")

        print("\n🌪️  EXTERNAL CYCLONE:")
        print(f"  Body Diameter:           {self.cyclone_body_diameter:.3f} m ({self.cyclone_body_diameter*1000:.0f} mm)")
        print(f"  Total Height:            {self.cyclone_total_height:.3f} m")

        print("\n📊 OPERATING PARAMETERS:")
        print(f"  Rotor Speed Range:       {self.rotor_rpm_min:.0f} - {self.rotor_rpm_max:.0f} rpm")
        print(f"  Design Rotor Speed:      {self.rotor_rpm_design:.0f} rpm")
        print(f"  Design Air Flow:         {self.air_flow_design:.0f} m³/hr")
        print(f"  Target Cut Size:         {self.target_d50:.1f} μm")
        print(f"  Tip Speed at Design:     {self.tip_speed_design:.1f} m/s")

        print("\n✅ CUT SIZE VALIDATION:")
        print(f"  d50 at design ({self.rotor_rpm_design:.0f} RPM):  {validation['d50_at_design_rpm']:.1f} μm")
        print(f"  d50 at min ({self.rotor_rpm_min:.0f} RPM):     {validation['d50_at_min_rpm']:.1f} μm")
        print(f"  d50 at max ({self.rotor_rpm_max:.0f} RPM):     {validation['d50_at_max_rpm']:.1f} μm")
        print(f"  d50 range achievable:    {validation['d50_range'][0]:.1f} - {validation['d50_range'][1]:.1f} μm")
        print(f"  RPM for target d50:      {validation['rpm_for_target_d50']:.0f} rpm")
        print(f"  Target achievable:       {'✓ YES' if validation['target_achievable'] else '✗ NO'}")
        print(f"  Tip speed at target:     {validation['tip_speed_at_target']:.1f} m/s {'(safe)' if validation['tip_speed_safe'] else '(TOO HIGH!)'}")

        print("\n🎯 DESIGN RATIOS:")
        print(f"  D_selector/D_chamber:    {self.selector_diameter/self.chamber_diameter:.2f}")
        print(f"  D_distributor/D_chamber: {self.distributor_diameter/self.chamber_diameter:.2f}")
        print(f"  H_chamber/D_chamber:     {self.chamber_height/self.chamber_diameter:.2f}")

        print("=" * 80)

    def print_cut_size_table(self):
        """Print cut size vs operating conditions table"""
        print("\n📊 CUT SIZE vs OPERATING CONDITIONS")
        print("=" * 70)
        print(f"Geometry: Selector Ø{self.selector_diameter*1000:.0f}mm × H{self.selector_blade_height*1000:.0f}mm")
        print(f"r²·h = {self.r_squared_h_product:.6f} m³")
        print("-" * 70)
        print(f"{'RPM':<10} {'Air Flow (m³/hr)':<18} {'d50 (μm)':<12} {'Notes'}")
        print("-" * 70)

        for rpm in range(2000, 5500, 500):
            for flow in [1500, 2000, 2500]:
                d50 = self.calculate_cut_size(rpm, flow)
                notes = ""
                if abs(d50 - self.target_d50) < 2:
                    notes = "← Near target"
                elif d50 < 10:
                    notes = "(protein loss risk)"
                elif d50 > 30:
                    notes = "(starch in fines risk)"
                print(f"{rpm:<10} {flow:<18} {d50:<12.1f} {notes}")
        
        print("-" * 70)
        print(f"Target d50: {self.target_d50:.1f} μm")
        print(f"Optimal: ~{self.rotor_rpm_design} RPM @ {self.air_flow_design} m³/hr")
        print("=" * 70)

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
            'target_d50': self.target_d50,
            'r_squared_h': self.r_squared_h_product,
        }


def create_default_config() -> CorrectedClassifierConfig:
    """
    Create default corrected classifier configuration
    
    Returns:
        CorrectedClassifierConfig with geometry sized for d50 = 20 μm
    """
    return CorrectedClassifierConfig()


def create_scaled_config(scale_factor: float) -> CorrectedClassifierConfig:
    """
    Create scaled classifier configuration
    
    Scaling preserves the cut size by maintaining r²·h proportionally.
    
    Args:
        scale_factor: Scaling factor (1.0 = default, 0.5 = half size, etc.)

    Returns:
        Scaled CorrectedClassifierConfig
    """
    config = CorrectedClassifierConfig()

    # Scale chamber dimensions
    config.chamber_diameter *= scale_factor
    config.chamber_height *= scale_factor
    
    # For selector, scale radius by scale_factor^(2/3) and height by scale_factor^(1/3)
    # This keeps r²·h ∝ scale_factor², which maintains d50 when Q also scales by scale_factor²
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


def create_config_for_cut_size(target_d50_um: float, 
                                design_rpm: float = 3000,
                                air_flow_m3hr: float = 2000) -> CorrectedClassifierConfig:
    """
    Create configuration optimized for a specific cut size
    
    Args:
        target_d50_um: Target cut size in micrometers
        design_rpm: Design rotor speed (rpm)
        air_flow_m3hr: Design air flow (m³/hr)
        
    Returns:
        Configuration with geometry sized for target d50
    """
    config = CorrectedClassifierConfig()
    
    # Constants
    mu = config.air_viscosity
    rho = 1400 - config.air_density  # Net density
    Q = air_flow_m3hr / 3600
    omega = design_rpm * 2 * np.pi / 60
    d50 = target_d50_um * 1e-6
    
    # Calculate required r²·h
    # d50² = 9·μ·Q / (π·ρ·ω²·r²·h)
    # r²·h = 9·μ·Q / (π·ρ·ω²·d50²)
    r_sq_h_required = (9 * mu * Q) / (np.pi * rho * omega**2 * d50**2)
    
    # Choose reasonable aspect ratio: h/r ≈ 1.0
    # r²·h = r³ when h = r
    # r = (r²·h)^(1/3)
    r = r_sq_h_required ** (1/3)
    h = r  # Equal to radius for h/r = 1
    
    # Apply constraints
    r = max(0.05, min(0.3, r))  # 50-300mm radius
    h = max(0.05, min(0.2, h))  # 50-200mm height
    
    # Update configuration
    config.selector_diameter = 2 * r
    config.selector_blade_height = h
    config.target_d50 = target_d50_um
    config.rotor_rpm_design = design_rpm
    config.air_flow_design = air_flow_m3hr
    
    # Scale hub to match
    config.hub_outer_diameter = r * 1.2
    config.hub_inner_diameter = r * 0.6
    config.hub_height = h
    
    return config


# =============================================================================
# MAIN - Test the corrected configuration
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CORRECTED CLASSIFIER CONFIGURATION - VERSION 2.0")
    print("Geometry properly sized for d50 = 20 μm")
    print("=" * 80)
    
    # Create and print configuration
    config = create_default_config()
    config.print_specifications()
    
    # Print cut size table
    config.print_cut_size_table()
    
    # Validation summary
    validation = config.validate_geometry_for_target()
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    if validation['target_achievable'] and abs(validation['d50_at_design_rpm'] - config.target_d50) < 5:
        print("✅ GEOMETRY CORRECTLY SIZED FOR TARGET d50")
        print(f"   Target: {config.target_d50:.1f} μm")
        print(f"   Achieved at design conditions: {validation['d50_at_design_rpm']:.1f} μm")
        print(f"   Error: {abs(validation['d50_at_design_rpm'] - config.target_d50):.1f} μm")
    else:
        print("⚠️  GEOMETRY MAY NEED ADJUSTMENT")
        print(f"   Target: {config.target_d50:.1f} μm")
        print(f"   At design conditions: {validation['d50_at_design_rpm']:.1f} μm")
        print(f"   Required RPM: {validation['rpm_for_target_d50']:.0f}")
    
    print("=" * 80)
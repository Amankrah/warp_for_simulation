"""
Selector Rotor Component Builder

Builds the corrected selector rotor assembly with:
- 24 vertical blades (4mm thick, corrected)
- 500mm height (reduced from 600mm)
- 5° forward lean angle
- Improved blade gap (48.5mm)

Based on Section 4.1.2 and Section 5.1 of corrected_classifier_geometry.md
"""

import numpy as np
import pyvista as pv
from typing import List, Tuple
from ..corrected_config import CorrectedClassifierConfig


def build_selector_blades(config: CorrectedClassifierConfig) -> List[pv.PolyData]:
    """
    Build selector blade array (rejector cage)

    CORRECTED specifications per Section 4.1.2:
    - 24 blades @ 4mm thickness (reduced from 5mm)
    - 500mm height (reduced from 600mm)
    - 5° forward lean (improves coarse rejection)
    - Blade gap: 48.5mm (increased from 47.4mm)

    Args:
        config: Corrected classifier configuration

    Returns:
        List of blade meshes
    """
    blades = []

    # Blade dimensions from corrected config
    blade_count = config.selector_blade_count
    blade_thickness = config.selector_blade_thickness
    blade_height = config.selector_blade_height
    selector_radius = config.selector_diameter / 2
    hub_radius = config.hub_outer_diameter / 2
    lean_angle = config.selector_blade_lean_angle  # 5° forward

    # Blade center Z position
    blade_center_z = (config.selector_zone_bottom + config.selector_zone_top) / 2

    # Create each blade
    for i in range(blade_count):
        # Angular position
        angle = 2 * np.pi * i / blade_count

        # Blade radial extent (from hub to selector radius)
        blade_radial_length = selector_radius - hub_radius

        # Create blade as thin box (radial orientation)
        # Blade extends from hub surface to selector cage radius
        blade = pv.Box(
            bounds=[
                -blade_thickness / 2,
                blade_thickness / 2,
                hub_radius,
                selector_radius,
                -blade_height / 2,
                blade_height / 2
            ]
        )

        # Apply forward lean (5° tilt)
        # Lean in direction of rotation to improve rejection
        if lean_angle != 0:
            blade.rotate_y(lean_angle, point=(0, 0, 0), inplace=True)

        # Rotate to angular position
        blade.rotate_z(np.degrees(angle), point=(0, 0, 0), inplace=True)

        # Translate to selector zone vertical position
        blade.translate((0, 0, blade_center_z), inplace=True)

        blades.append(blade)

    return blades


def build_selector_rotor(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build complete selector rotor assembly including top and bottom plates

    Args:
        config: Corrected classifier configuration

    Returns:
        Combined selector rotor mesh
    """
    # Build all blades
    blades = build_selector_blades(config)

    # Combine all blades into single mesh
    selector = blades[0]
    for blade in blades[1:]:
        selector = selector + blade

    # Add top mounting plate
    top_plate_z = config.selector_zone_top
    top_plate = pv.Cylinder(
        radius=config.selector_diameter / 2,
        height=0.008,  # 8mm thick
        center=(0, 0, top_plate_z + 0.004),
        direction=(0, 0, 1),
        resolution=48
    )

    # Add bottom mounting plate
    bottom_plate_z = config.selector_zone_bottom
    bottom_plate = pv.Cylinder(
        radius=config.selector_diameter / 2,
        height=0.008,  # 8mm thick
        center=(0, 0, bottom_plate_z - 0.004),
        direction=(0, 0, 1),
        resolution=48
    )

    # Combine everything
    selector = selector + top_plate + bottom_plate

    return selector


def build_selector_cage_outline(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build selector cage outline cylinder (for visualization)

    Args:
        config: Corrected classifier configuration

    Returns:
        Outline cylinder mesh
    """
    cage = pv.Cylinder(
        radius=config.selector_diameter / 2,
        height=config.selector_blade_height,
        center=(0, 0, (config.selector_zone_bottom + config.selector_zone_top) / 2),
        direction=(0, 0, 1),
        resolution=64
    )

    return cage


def calculate_blade_loading(
    config: CorrectedClassifierConfig,
    rotor_rpm: float,
    tip_velocity_limit: float = 100.0
) -> dict:
    """
    Calculate blade loading and stress parameters

    Args:
        config: Corrected classifier configuration
        rotor_rpm: Rotor speed (rpm)
        tip_velocity_limit: Maximum safe tip velocity (m/s)

    Returns:
        Dictionary with loading parameters
    """
    # Calculate tip speed
    omega = rotor_rpm * 2 * np.pi / 60  # rad/s
    tip_radius = config.selector_diameter / 2
    tip_speed = omega * tip_radius

    # Centrifugal force on blade
    # Approximate blade as rectangular plate
    blade_mass_per_unit = 7850 * config.selector_blade_thickness * config.selector_blade_height  # kg/m (SS304 density)
    blade_radial_length = tip_radius - config.hub_outer_diameter / 2
    avg_radius = (tip_radius + config.hub_outer_diameter / 2) / 2

    # Centrifugal force
    centrifugal_force = blade_mass_per_unit * blade_radial_length * omega**2 * avg_radius

    # Stress (approximate)
    blade_area = config.selector_blade_thickness * config.selector_blade_height
    stress_estimate = centrifugal_force / blade_area / 1e6  # MPa

    return {
        'tip_speed_ms': tip_speed,
        'angular_velocity_rad_s': omega,
        'centrifugal_force_N': centrifugal_force,
        'stress_estimate_MPa': stress_estimate,
        'safe': tip_speed < tip_velocity_limit,
        'tip_speed_limit_ms': tip_velocity_limit
    }


def print_selector_specifications(config: CorrectedClassifierConfig):
    """
    Print detailed selector rotor specifications

    Args:
        config: Corrected classifier configuration
    """
    print("\n" + "=" * 70)
    print("SELECTOR ROTOR SPECIFICATIONS (CORRECTED)")
    print("=" * 70)

    print(f"\n🔧 BLADE GEOMETRY:")
    print(f"  Number of Blades:        {config.selector_blade_count}")
    print(f"  Blade Thickness:         {config.selector_blade_thickness*1000:.1f} mm (REDUCED from 5mm)")
    print(f"  Blade Height:            {config.selector_blade_height*1000:.0f} mm (REDUCED from 600mm)")
    print(f"  Blade Gap:               {config.selector_blade_gap*1000:.1f} mm (INCREASED from 47.4mm)")
    print(f"  Forward Lean Angle:      {config.selector_blade_lean_angle:.1f}°")
    print(f"  Solidity Ratio:          {config.solidity_ratio:.3f}")

    print(f"\n📐 CAGE DIMENSIONS:")
    print(f"  Selector Diameter:       {config.selector_diameter*1000:.0f} mm")
    print(f"  Hub Outer Diameter:      {config.hub_outer_diameter*1000:.0f} mm")
    print(f"  Blade Radial Length:     {(config.selector_diameter - config.hub_outer_diameter)/2*1000:.0f} mm")
    print(f"  Selector Zone Bottom:    Z = {config.selector_zone_bottom:.2f} m (RAISED from 0.35m)")
    print(f"  Selector Zone Top:       Z = {config.selector_zone_top:.2f} m")
    print(f"  Active Zone Height:      {config.selector_zone_top - config.selector_zone_bottom:.2f} m")

    print(f"\n⚙️  OPERATING PARAMETERS:")
    print(f"  Design RPM:              {config.rotor_rpm_design:.0f} rpm")
    print(f"  RPM Range:               {config.rotor_rpm_min:.0f} - {config.rotor_rpm_max:.0f} rpm")
    print(f"  Tip Speed at Design:     {config.tip_speed_design:.1f} m/s")

    # Calculate loading at design speed
    loading = calculate_blade_loading(config, config.rotor_rpm_design)
    print(f"\n💪 BLADE LOADING (at {config.rotor_rpm_design:.0f} RPM):")
    print(f"  Tip Speed:               {loading['tip_speed_ms']:.1f} m/s")
    print(f"  Angular Velocity:        {loading['angular_velocity_rad_s']:.1f} rad/s")
    print(f"  Centrifugal Force:       {loading['centrifugal_force_N']:.1f} N per blade")
    print(f"  Estimated Stress:        {loading['stress_estimate_MPa']:.1f} MPa")
    print(f"  Safe Operation:          {'✓ Yes' if loading['safe'] else '✗ No - Exceeds limit'}")

    # Calculate at max speed
    loading_max = calculate_blade_loading(config, config.rotor_rpm_max)
    print(f"\n💪 BLADE LOADING (at MAX {config.rotor_rpm_max:.0f} RPM):")
    print(f"  Tip Speed:               {loading_max['tip_speed_ms']:.1f} m/s")
    print(f"  Estimated Stress:        {loading_max['stress_estimate_MPa']:.1f} MPa")
    print(f"  Safe Operation:          {'✓ Yes' if loading_max['safe'] else '✗ No - Exceeds limit'}")

    print(f"\n✅ KEY IMPROVEMENTS:")
    print("  • Thinner blades (4mm vs 5mm) = +2.3% open area")
    print("  • Reduced height (500mm vs 600mm) = better clearance")
    print("  • Raised zone (Z=0.45m vs 0.35m) = cleaner air flow")
    print("  • Forward lean (5°) = improved coarse rejection")

    print("=" * 70)


def visualize_selector_rotor(config: CorrectedClassifierConfig):
    """
    Visualize selector rotor assembly

    Args:
        config: Corrected classifier configuration
    """
    plotter = pv.Plotter(window_size=(1200, 900))
    plotter.set_background('white')

    # Build blades
    blades = build_selector_blades(config)

    # Add each blade
    for i, blade in enumerate(blades):
        plotter.add_mesh(
            blade,
            color='steelblue',
            opacity=0.8,
            show_edges=True,
            line_width=0.5,
            label='Selector Blades' if i == 0 else None
        )

    # Add cage outline (transparent)
    cage = build_selector_cage_outline(config)
    plotter.add_mesh(
        cage,
        color='lightblue',
        opacity=0.15,
        show_edges=True,
        line_width=2,
        label=f'Selector Cage (Ø{config.selector_diameter*1000:.0f}mm)'
    )

    # Add hub outline
    hub = pv.Cylinder(
        radius=config.hub_outer_diameter / 2,
        height=config.hub_height,
        center=(0, 0, (config.selector_zone_bottom + config.selector_zone_top) / 2),
        direction=(0, 0, 1),
        resolution=32
    )
    plotter.add_mesh(
        hub,
        color='goldenrod',
        opacity=0.6,
        show_edges=True,
        label=f'Hub (Ø{config.hub_outer_diameter*1000:.0f}mm)'
    )

    # Add axes
    plotter.add_axes(
        xlabel='X (m)',
        ylabel='Y (m)',
        zlabel='Z (m)',
        line_width=3
    )

    # Add legend
    plotter.add_legend(bcolor='white', size=(0.3, 0.2))

    # Set camera
    plotter.camera_position = 'iso'

    # Add title
    plotter.add_text(
        f'Selector Rotor - {config.selector_blade_count} Blades (Corrected Design)',
        position='upper_edge',
        font_size=12,
        color='black'
    )

    plotter.show()


if __name__ == "__main__":
    # Test selector rotor builder
    from ..corrected_config import create_default_config

    print("Testing Selector Rotor Component Builder")
    print("=" * 70)

    config = create_default_config()

    # Print specifications
    print_selector_specifications(config)

    # Build blades
    blades = build_selector_blades(config)
    print(f"\n✓ Created {len(blades)} selector blades")
    print(f"  Each blade: {blades[0].n_points} points, {blades[0].n_cells} cells")

    # Visualize
    print("\nLaunching visualization...")
    visualize_selector_rotor(config)

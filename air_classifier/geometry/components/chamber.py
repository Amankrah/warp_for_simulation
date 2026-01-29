"""
Classification Chamber Component Builder

Builds the main classification chamber consisting of:
- Cylindrical section (main classification zone)
- Conical bottom section (60° included angle)

Based on Section 4.1.1 and Section 5.4 of corrected_classifier_geometry.md
"""

import numpy as np
import pyvista as pv
from typing import Tuple
from ..corrected_config import CorrectedClassifierConfig


def build_chamber(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build cylindrical classification chamber

    Args:
        config: Corrected classifier configuration

    Returns:
        PyVista mesh of cylindrical chamber section
    """
    # Cylindrical section - main classification zone
    chamber = pv.Cylinder(
        radius=config.chamber_diameter / 2,
        height=config.chamber_height,
        center=(0, 0, config.chamber_height / 2),
        direction=(0, 0, 1),
        resolution=64
    )

    return chamber


def build_cone(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build conical bottom section (coarse collection)

    60° included angle cone as specified in Section 4.1.1

    Args:
        config: Corrected classifier configuration

    Returns:
        PyVista mesh of conical section
    """
    # Calculate cone height from angle
    cone_height = config.cone_height

    # Conical bottom - coarse particle collection
    cone = pv.Cone(
        center=(0, 0, -cone_height / 2),
        direction=(0, 0, 1),
        height=cone_height,
        radius=config.chamber_diameter / 2,
        resolution=64
    )

    return cone


def build_chamber_with_wear_liner(
    config: CorrectedClassifierConfig,
    include_liner: bool = True
) -> Tuple[pv.PolyData, pv.PolyData]:
    """
    Build chamber with optional wear liner

    Per Section 5.4.2:
    - Cylinder: Hardox 400 liner (6mm)
    - Cone: Alumina ceramic tiles (10mm)

    Args:
        config: Corrected classifier configuration
        include_liner: Whether to include wear liner

    Returns:
        Tuple of (chamber shell, liner) if include_liner=True
        Tuple of (chamber shell, None) if include_liner=False
    """
    # Main chamber shell
    chamber = build_chamber(config)

    if not include_liner:
        return chamber, None

    # Inner liner (slightly smaller radius)
    liner_thickness = 0.006  # 6mm Hardox liner
    inner_radius = config.chamber_diameter / 2 - liner_thickness

    liner = pv.Cylinder(
        radius=inner_radius,
        height=config.chamber_height,
        center=(0, 0, config.chamber_height / 2),
        direction=(0, 0, 1),
        resolution=64
    )

    return chamber, liner


def build_cone_with_ceramic_liner(
    config: CorrectedClassifierConfig,
    include_liner: bool = True
) -> Tuple[pv.PolyData, pv.PolyData]:
    """
    Build cone with optional ceramic wear liner

    Args:
        config: Corrected classifier configuration
        include_liner: Whether to include ceramic liner

    Returns:
        Tuple of (cone shell, ceramic liner)
    """
    # Main cone shell
    cone = build_cone(config)

    if not include_liner:
        return cone, None

    # Ceramic liner (slightly smaller)
    liner_thickness = 0.010  # 10mm alumina ceramic
    inner_radius = config.chamber_diameter / 2 - liner_thickness
    cone_height = config.cone_height

    ceramic_liner = pv.Cone(
        center=(0, 0, -cone_height / 2),
        direction=(0, 0, 1),
        height=cone_height,
        radius=inner_radius,
        resolution=64
    )

    return cone, ceramic_liner


def visualize_chamber_section(config: CorrectedClassifierConfig):
    """
    Visualize chamber and cone sections with dimensions

    Args:
        config: Corrected classifier configuration
    """
    plotter = pv.Plotter(window_size=(1000, 800))
    plotter.set_background('white')

    # Build components
    chamber = build_chamber(config)
    cone = build_cone(config)

    # Add chamber (transparent)
    plotter.add_mesh(
        chamber,
        color='lightblue',
        opacity=0.3,
        show_edges=True,
        line_width=2,
        label=f'Chamber (Ø{config.chamber_diameter*1000:.0f}mm × H{config.chamber_height*1000:.0f}mm)'
    )

    # Add cone (transparent)
    plotter.add_mesh(
        cone,
        color='lightcoral',
        opacity=0.3,
        show_edges=True,
        line_width=2,
        label=f'Cone (H={config.cone_height*1000:.0f}mm, {config.cone_angle:.0f}°)'
    )

    # Add axes
    plotter.add_axes(
        xlabel='X (m)',
        ylabel='Y (m)',
        zlabel='Z (m)',
        line_width=3
    )

    # Add legend
    plotter.add_legend(bcolor='white', size=(0.3, 0.15))

    # Set camera
    plotter.camera_position = 'iso'

    # Add title
    plotter.add_text(
        'Classification Chamber - Chamber + Cone',
        position='upper_edge',
        font_size=12,
        color='black'
    )

    plotter.show()


if __name__ == "__main__":
    # Test chamber builder
    from ..corrected_config import create_default_config

    print("Testing Chamber Component Builder")
    print("=" * 60)

    config = create_default_config()

    print(f"\nChamber Dimensions:")
    print(f"  Diameter: {config.chamber_diameter*1000:.0f} mm")
    print(f"  Height: {config.chamber_height*1000:.0f} mm")
    print(f"  Cone Height: {config.cone_height*1000:.0f} mm")
    print(f"  Cone Angle: {config.cone_angle:.0f}°")

    # Build components
    chamber = build_chamber(config)
    cone = build_cone(config)

    print(f"\n✓ Chamber mesh created: {chamber.n_points} points, {chamber.n_cells} cells")
    print(f"✓ Cone mesh created: {cone.n_points} points, {cone.n_cells} cells")

    # Visualize
    print("\nLaunching visualization...")
    visualize_chamber_section(config)

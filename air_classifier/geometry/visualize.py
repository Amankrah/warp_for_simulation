"""
Visualization Module for Corrected Classifier Geometry

3D visualization using PyVista with proper colors and labels
"""

import pyvista as pv
import numpy as np
from typing import Optional, Tuple
from .assembly import GeometryAssembly
from .corrected_config import CorrectedClassifierConfig


def visualize_complete_assembly(
    assembly: GeometryAssembly,
    window_size: Tuple[int, int] = (1600, 1200),
    screenshot_path: Optional[str] = None,
    show_axes: bool = True,
    camera_position: str = 'iso'
):
    """
    Visualize complete classifier assembly in 3D

    Args:
        assembly: Geometry assembly to visualize
        window_size: Window size (width, height)
        screenshot_path: Path to save screenshot
        show_axes: Show coordinate axes
        camera_position: Camera position ('iso', 'xy', 'xz', 'yz')
    """
    plotter = pv.Plotter(window_size=window_size)
    plotter.set_background('white')

    # Add chamber (transparent)
    plotter.add_mesh(
        assembly.chamber,
        color='lightblue',
        opacity=0.2,
        show_edges=True,
        line_width=1,
        label='Chamber'
    )

    # Add cone (transparent)
    plotter.add_mesh(
        assembly.cone,
        color='lightblue',
        opacity=0.2,
        show_edges=True,
        line_width=1,
        label='Cone'
    )

    # Add shaft
    plotter.add_mesh(
        assembly.shaft,
        color='darkgray',
        show_edges=True,
        line_width=0.5,
        label='Shaft'
    )

    # Add distributor
    plotter.add_mesh(
        assembly.distributor,
        color='chocolate',
        opacity=0.9,
        show_edges=True,
        label='Distributor Plate'
    )

    # Add selector blades
    for i, blade in enumerate(assembly.selector_blades):
        plotter.add_mesh(
            blade,
            color='steelblue',
            opacity=0.7,
            show_edges=True,
            line_width=0.3,
            label='Selector Blades' if i == 0 else None
        )

    # Add hub
    plotter.add_mesh(
        assembly.hub,
        color='goldenrod',
        opacity=0.8,
        show_edges=True,
        label='Hub Assembly'
    )

    # Add feed ports
    for i, port in enumerate(assembly.feed_ports):
        plotter.add_mesh(
            port,
            color='orange',
            opacity=0.6,
            label='Feed Ports' if i == 0 else None
        )

    # Add air inlets
    for i, inlet in enumerate(assembly.air_inlets):
        plotter.add_mesh(
            inlet,
            color='cyan',
            opacity=0.6,
            show_edges=True,
            label='Air Inlets' if i == 0 else None
        )

    # Add outlets
    plotter.add_mesh(
        assembly.fines_outlet,
        color='green',
        opacity=0.7,
        show_edges=True,
        label='Fines Outlet'
    )

    plotter.add_mesh(
        assembly.coarse_outlet,
        color='brown',
        opacity=0.7,
        show_edges=True,
        label='Coarse Outlet'
    )

    # Add external cyclone if present
    if assembly.cyclone_cylinder is not None:
        plotter.add_mesh(
            assembly.cyclone_cylinder,
            color='lightcoral',
            opacity=0.3,
            show_edges=True,
            line_width=1,
            label='Cyclone'
        )

        plotter.add_mesh(
            assembly.cyclone_cone,
            color='lightcoral',
            opacity=0.3,
            show_edges=True,
            line_width=1
        )

        plotter.add_mesh(
            assembly.cyclone_vortex_finder,
            color='pink',
            opacity=0.5,
            show_edges=True,
            label='Vortex Finder'
        )

    # Add axes
    if show_axes:
        plotter.add_axes(
            xlabel='X (m)',
            ylabel='Y (m)',
            zlabel='Z (m)',
            line_width=3,
            color='black'
        )

    # Add legend
    plotter.add_legend(
        bcolor='white',
        size=(0.25, 0.35),
        face='rectangle',
        loc='upper right'
    )

    # Set title
    plotter.add_text(
        'Corrected Air Classifier - Cyclone Configuration',
        position='upper_edge',
        font_size=14,
        color='black',
        font='arial'
    )

    # Set camera
    if camera_position == 'iso':
        plotter.camera_position = 'iso'
    elif camera_position == 'xy':
        plotter.view_xy()
    elif camera_position == 'xz':
        plotter.view_xz()
    elif camera_position == 'yz':
        plotter.view_yz()

    # Show or save
    if screenshot_path:
        plotter.show(screenshot=screenshot_path)
        print(f"\n✓ Screenshot saved to: {screenshot_path}")
    else:
        plotter.show()


def visualize_cross_section(
    assembly: GeometryAssembly,
    plane: str = 'xz',
    window_size: Tuple[int, int] = (1200, 900)
):
    """
    Visualize cross-section through classifier

    Args:
        assembly: Geometry assembly
        plane: Cut plane ('xz', 'yz', 'xy')
        window_size: Window size
    """
    plotter = pv.Plotter(window_size=window_size)
    plotter.set_background('white')

    # Define cutting plane
    if plane == 'xz':
        normal = (0, 1, 0)
        origin = (0, 0, 0)
    elif plane == 'yz':
        normal = (1, 0, 0)
        origin = (0, 0, 0)
    else:  # xy
        normal = (0, 0, 1)
        origin = (0, 0, assembly.config.chamber_height / 2)

    # Slice and display major components
    chamber_slice = assembly.chamber.slice(normal=normal, origin=origin)
    plotter.add_mesh(chamber_slice, color='lightblue', opacity=0.5, label='Chamber')

    cone_slice = assembly.cone.slice(normal=normal, origin=origin)
    plotter.add_mesh(cone_slice, color='lightcoral', opacity=0.5, label='Cone')

    shaft_slice = assembly.shaft.slice(normal=normal, origin=origin)
    plotter.add_mesh(shaft_slice, color='darkgray', label='Shaft')

    # Add blade slices
    for i, blade in enumerate(assembly.selector_blades[:8]):  # Show subset
        try:
            blade_slice = blade.slice(normal=normal, origin=origin)
            plotter.add_mesh(
                blade_slice,
                color='steelblue',
                opacity=0.7,
                label='Selector Blades' if i == 0 else None
            )
        except:
            pass

    plotter.add_legend(bcolor='white')
    plotter.add_text(
        f'Cross-Section View ({plane.upper()} plane)',
        position='upper_edge',
        font_size=12,
        color='black'
    )

    if plane == 'xz':
        plotter.view_xz()
    elif plane == 'yz':
        plotter.view_yz()
    else:
        plotter.view_xy()

    plotter.show()


def compare_configurations(
    config1: CorrectedClassifierConfig,
    config2: CorrectedClassifierConfig,
    labels: Tuple[str, str] = ("Config 1", "Config 2")
):
    """
    Compare two configurations side-by-side

    Args:
        config1: First configuration
        config2: Second configuration
        labels: Labels for configurations
    """
    from .assembly import build_complete_classifier

    print(f"\nBuilding geometry for {labels[0]}...")
    assembly1 = build_complete_classifier(config1, include_cyclone=False)

    print(f"\nBuilding geometry for {labels[1]}...")
    assembly2 = build_complete_classifier(config2, include_cyclone=False)

    # Create side-by-side comparison
    plotter = pv.Plotter(shape=(1, 2), window_size=(1800, 900))
    plotter.set_background('white')

    # Left subplot - Config 1
    plotter.subplot(0, 0)
    plotter.add_text(labels[0], position='upper_edge', font_size=12)

    plotter.add_mesh(assembly1.chamber, color='lightblue', opacity=0.2, show_edges=True)
    plotter.add_mesh(assembly1.cone, color='lightblue', opacity=0.2, show_edges=True)
    plotter.add_mesh(assembly1.shaft, color='darkgray')
    plotter.add_mesh(assembly1.distributor, color='chocolate', opacity=0.8)

    for blade in assembly1.selector_blades:
        plotter.add_mesh(blade, color='steelblue', opacity=0.7, show_edges=True)

    plotter.camera_position = 'iso'

    # Right subplot - Config 2
    plotter.subplot(0, 1)
    plotter.add_text(labels[1], position='upper_edge', font_size=12)

    plotter.add_mesh(assembly2.chamber, color='lightblue', opacity=0.2, show_edges=True)
    plotter.add_mesh(assembly2.cone, color='lightblue', opacity=0.2, show_edges=True)
    plotter.add_mesh(assembly2.shaft, color='darkgray')
    plotter.add_mesh(assembly2.distributor, color='chocolate', opacity=0.8)

    for blade in assembly2.selector_blades:
        plotter.add_mesh(blade, color='steelblue', opacity=0.7, show_edges=True)

    plotter.camera_position = 'iso'

    plotter.show()


if __name__ == "__main__":
    from .corrected_config import create_default_config
    from .assembly import build_complete_classifier

    print("Building geometry for visualization...")
    config = create_default_config()
    assembly = build_complete_classifier(config, include_cyclone=True)

    print("\nLaunching 3D visualization...")
    visualize_complete_assembly(assembly)

"""
PyVista-based 3D visualization for cooking simulation geometry
"""

import pyvista as pv
import numpy as np
import warp as wp
from typing import Optional, List, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from geometry.boiling.assembly import BoilingAssembly


def warp_mesh_to_pyvista(warp_mesh: wp.Mesh) -> pv.PolyData:
    """
    Convert Warp mesh to PyVista PolyData

    Args:
        warp_mesh: Warp mesh object

    Returns:
        PyVista PolyData
    """
    # Get points and indices
    points = warp_mesh.points.numpy()
    indices = warp_mesh.indices.numpy().reshape(-1, 3)

    # Create faces array for PyVista (prepend 3 to each triangle)
    faces = []
    for tri in indices:
        faces.append(3)
        faces.extend(tri)

    faces = np.array(faces, dtype=np.int32)

    # Create PyVista mesh
    pv_mesh = pv.PolyData(points, faces)

    return pv_mesh


def create_point_cloud(grid_points: wp.array) -> pv.PolyData:
    """
    Convert Warp grid points to PyVista point cloud

    Args:
        grid_points: Warp array of grid points

    Returns:
        PyVista PolyData point cloud
    """
    points = grid_points.numpy()
    return pv.PolyData(points)


class GeometryVisualizer:
    """PyVista-based visualizer for cooking simulation geometries"""

    def __init__(self, window_size: Tuple[int, int] = (1600, 1200)):
        """
        Initialize the visualizer

        Args:
            window_size: Window size (width, height)
        """
        self.window_size = window_size

    def visualize_assembly(
        self,
        assembly: BoilingAssembly,
        show_components: Optional[List[str]] = None,
        show_grid_points: bool = True,
        save_path: Optional[str] = None,
        camera_position: str = 'iso'
    ):
        """
        Visualize a BoilingAssembly in 3D

        Args:
            assembly: The assembly to visualize
            show_components: List of component names to show (None = all)
            show_grid_points: Whether to show liquid domain grid points
            save_path: Path to save the figure (None = display only)
            camera_position: Camera position ('iso', 'xy', 'xz', 'yz')
        """
        plotter = pv.Plotter(window_size=self.window_size)
        plotter.set_background('white')

        # Filter components
        if show_components is None:
            components_to_show = list(assembly.components.items())
        else:
            components_to_show = [
                (name, assembly.get_component(name))
                for name in show_components
                if assembly.get_component(name) is not None
            ]

        # Plot each component
        for comp_name, component in components_to_show:
            if component.mesh is not None:
                # Convert Warp mesh to PyVista
                pv_mesh = warp_mesh_to_pyvista(component.mesh)

                # Get visualization style
                color, opacity, show_edges = self._get_component_style(comp_name)

                plotter.add_mesh(
                    pv_mesh,
                    color=color,
                    opacity=opacity,
                    show_edges=show_edges,
                    line_width=0.5,
                    label=comp_name
                )

            # Show computational grid points for liquid domain (subtle visualization)
            if show_grid_points and hasattr(component, 'grid_points') and 'water' in comp_name.lower():
                grid_cloud = create_point_cloud(component.grid_points)
                plotter.add_mesh(
                    grid_cloud,
                    color='darkblue',
                    point_size=1,
                    render_points_as_spheres=False,
                    opacity=0.15,
                    label=f'{comp_name} grid'
                )

            # Show internal grid for food objects
            if show_grid_points and hasattr(component, 'internal_grid_points'):
                internal_cloud = create_point_cloud(component.internal_grid_points)
                plotter.add_mesh(
                    internal_cloud,
                    color='darkorange',
                    point_size=3,
                    render_points_as_spheres=True,
                    opacity=0.6,
                    label=f'{comp_name} internal grid'
                )

        # Add axes
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
            size=(0.10, 0.15),
            face='rectangle',
            loc='lower right'
        )

        # Set title
        plotter.add_text(
            f'Assembly: {assembly.name}',
            position='upper_edge',
            font_size=14,
            color='black',
            font='arial'
        )

        # Set camera position
        if camera_position == 'iso':
            plotter.camera_position = 'iso'
        elif camera_position == 'xy':
            plotter.view_xy()
        elif camera_position == 'xz':
            plotter.view_xz()
        elif camera_position == 'yz':
            plotter.view_yz()

        # Show or save
        if save_path:
            plotter.show(screenshot=save_path)
            print(f"Figure saved to {save_path}")
        else:
            plotter.show()

    def visualize_cross_section(
        self,
        assembly: BoilingAssembly,
        plane: str = 'xz',
        position: float = 0.0,
        save_path: Optional[str] = None
    ):
        """
        Visualize a cross-section of the assembly

        Args:
            assembly: The assembly to visualize
            plane: Cross-section plane ('xy', 'xz', 'yz')
            position: Position along the perpendicular axis
            save_path: Path to save the figure
        """
        plotter = pv.Plotter(window_size=self.window_size)
        plotter.set_background('white')

        # Define cutting plane
        if plane == 'xz':
            normal = (0, 1, 0)
            origin = (0, position, 0)
        elif plane == 'yz':
            normal = (1, 0, 0)
            origin = (position, 0, 0)
        else:  # xy
            normal = (0, 0, 1)
            origin = (0, 0, position)

        # Slice and display components
        for comp_name, component in assembly.components.items():
            if component.mesh is not None:
                pv_mesh = warp_mesh_to_pyvista(component.mesh)

                try:
                    sliced_mesh = pv_mesh.slice(normal=normal, origin=origin)

                    if sliced_mesh.n_points > 0:
                        color, opacity, show_edges = self._get_component_style(comp_name)

                        plotter.add_mesh(
                            sliced_mesh,
                            color=color,
                            opacity=opacity,
                            show_edges=show_edges,
                            line_width=1,
                            label=comp_name
                        )
                except:
                    pass  # Skip if slicing fails

        # Add axes
        plotter.add_axes(
            xlabel='X (m)' if plane != 'yz' else '',
            ylabel='Y (m)' if plane != 'xz' else '',
            zlabel='Z (m)' if plane != 'xy' else '',
            line_width=3
        )

        # Add legend
        plotter.add_legend(bcolor='white', loc='upper right')

        # Add title
        plotter.add_text(
            f'Cross-Section: {plane.upper()} plane at {position:.3f}m',
            position='upper_edge',
            font_size=12,
            color='black'
        )

        # Set view
        if plane == 'xz':
            plotter.view_xz()
        elif plane == 'yz':
            plotter.view_yz()
        else:
            plotter.view_xy()

        # Show or save
        if save_path:
            plotter.show(screenshot=save_path)
            print(f"Figure saved to {save_path}")
        else:
            plotter.show()

    def visualize_temperature_field(
        self,
        assembly: BoilingAssembly,
        food_temperature: np.ndarray,
        save_path: Optional[str] = None
    ):
        """
        Visualize temperature distribution in food

        Args:
            assembly: BoilingAssembly
            food_temperature: Temperature array for food grid points
            save_path: Path to save screenshot
        """
        plotter = pv.Plotter(window_size=self.window_size)
        plotter.set_background('white')

        # Find food components and plot with temperature coloring
        food_components = [
            name for name in assembly.components.keys()
            if 'carrot' in name or 'potato' in name
        ]

        point_offset = 0
        for comp_name in food_components:
            component = assembly.get_component(comp_name)

            if hasattr(component, 'internal_grid_points'):
                num_points = component.num_internal_points
                temps = food_temperature[point_offset:point_offset + num_points]

                # Create point cloud with temperature data
                grid_cloud = create_point_cloud(component.internal_grid_points)
                grid_cloud['temperature'] = temps

                plotter.add_mesh(
                    grid_cloud,
                    scalars='temperature',
                    cmap='coolwarm',
                    point_size=5,
                    render_points_as_spheres=True,
                    opacity=0.8,
                    show_scalar_bar=True,
                    scalar_bar_args={'title': 'Temperature (°C)', 'vertical': True}
                )

                point_offset += num_points

        # Add saucepan for context (transparent)
        saucepan = assembly.get_component('saucepan_body')
        if saucepan and saucepan.mesh:
            pv_mesh = warp_mesh_to_pyvista(saucepan.mesh)
            plotter.add_mesh(pv_mesh, color='silver', opacity=0.1, show_edges=True)

        plotter.add_axes(xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)')
        plotter.add_text('Temperature Distribution', position='upper_edge', font_size=14)
        plotter.camera_position = 'iso'

        if save_path:
            plotter.show(screenshot=save_path)
            print(f"Figure saved to {save_path}")
        else:
            plotter.show()

    def visualize_nutrient_concentration(
        self,
        assembly: BoilingAssembly,
        nutrient_concentration: np.ndarray,
        nutrient_name: str = "Vitamin A",
        save_path: Optional[str] = None
    ):
        """
        Visualize nutrient concentration distribution in food

        Args:
            assembly: BoilingAssembly
            nutrient_concentration: Concentration array for food grid points
            nutrient_name: Name of the nutrient
            save_path: Path to save screenshot
        """
        plotter = pv.Plotter(window_size=self.window_size)
        plotter.set_background('white')

        # Find food components
        food_components = [
            name for name in assembly.components.keys()
            if 'carrot' in name or 'potato' in name
        ]

        point_offset = 0
        for comp_name in food_components:
            component = assembly.get_component(comp_name)

            if hasattr(component, 'internal_grid_points'):
                num_points = component.num_internal_points
                conc = nutrient_concentration[point_offset:point_offset + num_points]

                # Create point cloud with concentration data
                grid_cloud = create_point_cloud(component.internal_grid_points)
                grid_cloud['concentration'] = conc

                plotter.add_mesh(
                    grid_cloud,
                    scalars='concentration',
                    cmap='YlOrRd',
                    point_size=5,
                    render_points_as_spheres=True,
                    opacity=0.8,
                    show_scalar_bar=True,
                    scalar_bar_args={'title': f'{nutrient_name} (μg/g)', 'vertical': True}
                )

                point_offset += num_points

        # Add saucepan for context
        saucepan = assembly.get_component('saucepan_body')
        if saucepan and saucepan.mesh:
            pv_mesh = warp_mesh_to_pyvista(saucepan.mesh)
            plotter.add_mesh(pv_mesh, color='silver', opacity=0.1, show_edges=True)

        plotter.add_axes(xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)')
        plotter.add_text(f'{nutrient_name} Concentration', position='upper_edge', font_size=14)
        plotter.camera_position = 'iso'

        if save_path:
            plotter.show(screenshot=save_path)
            print(f"Figure saved to {save_path}")
        else:
            plotter.show()

    def _get_component_style(self, comp_name: str) -> Tuple[str, float, bool]:
        """
        Get visualization style for a component

        Args:
            comp_name: Component name

        Returns:
            (color, opacity, show_edges)
        """
        # Default style
        color = 'lightgray'
        opacity = 0.5
        show_edges = True

        # Customize based on component name
        if 'saucepan' in comp_name.lower():
            color = 'silver'
            opacity = 0.3
            show_edges = True
        elif 'lid' in comp_name.lower():
            color = 'gray'
            opacity = 0.4
            show_edges = True
        elif 'water' in comp_name.lower():
            # Realistic water appearance: translucent blue-cyan
            color = 'lightblue'
            opacity = 0.4
            show_edges = False
        elif 'carrot' in comp_name.lower():
            color = 'orange'
            opacity = 0.8
            show_edges = True
        elif 'potato' in comp_name.lower():
            color = 'tan'
            opacity = 0.8
            show_edges = True

        return color, opacity, show_edges

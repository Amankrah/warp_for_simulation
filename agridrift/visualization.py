"""
Visualization module for AgriDrift using PyVista and Matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Circle
import pyvista as pv
from typing import Optional, Tuple, Dict
from pathlib import Path


class SprayVisualizer:
    """
    3D visualization for spray drift simulation using PyVista
    """

    def __init__(
        self,
        nozzle_position: Tuple[float, float, float],
        domain_x: Tuple[float, float],
        domain_y: Tuple[float, float],
        ground_level: float = 0.0,
        canopy_height: float = 0.0,
        window_size: Tuple[int, int] = (1200, 800),
        interactive: bool = True
    ):
        self.nozzle_pos = nozzle_position
        self.domain_x = domain_x
        self.domain_y = domain_y
        self.ground_level = ground_level
        self.canopy_height = canopy_height

        # Initialize plotter
        self.plotter = pv.Plotter(window_size=window_size, off_screen=not interactive)
        self.plotter.set_background('lightblue')

        # Add environment
        self._add_ground()
        if canopy_height > 0:
            self._add_canopy()
        self._add_nozzle()

        # Particle actor
        self.particle_actor = None

        # Camera setup
        self._setup_camera()

    def _add_ground(self):
        """Add ground plane"""
        x_center = (self.domain_x[0] + self.domain_x[1]) / 2
        y_center = (self.domain_y[0] + self.domain_y[1]) / 2
        x_size = self.domain_x[1] - self.domain_x[0]
        y_size = self.domain_y[1] - self.domain_y[0]

        ground = pv.Plane(
            center=(x_center, y_center, self.ground_level),
            direction=(0, 0, 1),
            i_size=x_size,
            j_size=y_size,
            i_resolution=10,
            j_resolution=10
        )

        self.plotter.add_mesh(
            ground,
            color='green',
            opacity=0.3,
            show_edges=True,
            lighting=True
        )

    def _add_canopy(self):
        """Add crop canopy representation"""
        x_center = (self.domain_x[0] + self.domain_x[1]) / 2
        y_center = (self.domain_y[0] + self.domain_y[1]) / 2
        x_size = self.domain_x[1] - self.domain_x[0]
        y_size = self.domain_y[1] - self.domain_y[0]

        canopy = pv.Box(
            bounds=[
                self.domain_x[0], self.domain_x[1],
                self.domain_y[0], self.domain_y[1],
                self.ground_level, self.ground_level + self.canopy_height
            ]
        )

        self.plotter.add_mesh(
            canopy,
            color='darkgreen',
            opacity=0.15,
            show_edges=False
        )

    def _add_nozzle(self):
        """Add spray nozzle marker"""
        nozzle = pv.Sphere(
            radius=0.1,
            center=self.nozzle_pos
        )

        self.plotter.add_mesh(
            nozzle,
            color='red',
            opacity=1.0,
            smooth_shading=True
        )

        # Add label
        self.plotter.add_point_labels(
            [self.nozzle_pos],
            ['Nozzle'],
            font_size=12,
            point_color='red',
            point_size=10,
            text_color='black',
            shape=None
        )

    def _setup_camera(self):
        """Setup default camera view"""
        # Isometric view
        self.plotter.camera_position = 'iso'
        self.plotter.camera.zoom(1.2)

    def update_droplets(
        self,
        positions: np.ndarray,
        active: np.ndarray,
        diameters: Optional[np.ndarray] = None,
        scalar_field: Optional[np.ndarray] = None,
        scalar_name: str = "Droplet Diameter (μm)",
        cmap: str = "plasma",
        point_size: float = 8.0
    ):
        """
        Update droplet visualization

        Args:
            positions: (N, 3) array of droplet positions
            active: (N,) array of active status (1=active, 0=deposited)
            diameters: (N,) array of droplet diameters (m)
            scalar_field: (N,) array for coloring, if None uses diameters
            scalar_name: Name for scalar field
            cmap: Colormap name
            point_size: Size of points
        """
        # Remove old actor
        if self.particle_actor is not None:
            self.plotter.remove_actor(self.particle_actor)

        # Filter to active droplets only
        active_mask = active > 0
        if not np.any(active_mask):
            return

        active_positions = positions[active_mask]

        # Create point cloud
        points = pv.PolyData(active_positions)

        # Set scalar field for coloring
        if scalar_field is not None:
            scalars = scalar_field[active_mask]
        elif diameters is not None:
            scalars = diameters[active_mask] * 1e6  # Convert to microns
        else:
            scalars = np.ones(len(active_positions))

        points[scalar_name] = scalars

        # Add to plotter
        self.particle_actor = self.plotter.add_mesh(
            points,
            scalars=scalar_name,
            cmap=cmap,
            point_size=point_size,
            render_points_as_spheres=True,
            show_scalar_bar=True,
            opacity=0.8
        )

    def add_deposition_pattern(
        self,
        deposition_positions: np.ndarray,
        deposition_mask: np.ndarray,
        point_size: float = 3.0
    ):
        """
        Add deposited droplet pattern to ground

        Args:
            deposition_positions: (N, 3) positions where droplets deposited
            deposition_mask: (N,) boolean mask for deposited droplets
            point_size: Size of deposition markers
        """
        if not np.any(deposition_mask):
            return

        dep_pos = deposition_positions[deposition_mask]

        points = pv.PolyData(dep_pos)
        self.plotter.add_mesh(
            points,
            color='yellow',
            point_size=point_size,
            render_points_as_spheres=True,
            opacity=0.6
        )

    def show(self):
        """Display the visualization"""
        self.plotter.show()

    def screenshot(self, filename: str):
        """Save screenshot"""
        self.plotter.screenshot(filename, transparent_background=False)

    def close(self):
        """Close the plotter"""
        self.plotter.close()


def plot_trajectory_2d(
    positions_history: list,
    active_history: list,
    deposition_positions: np.ndarray,
    deposition_mask: np.ndarray,
    nozzle_position: Tuple[float, float, float],
    domain_x: Tuple[float, float],
    domain_z: Tuple[float, float],
    save_path: Optional[str] = None
):
    """
    Plot 2D trajectory view (X-Z plane)

    Args:
        positions_history: List of position arrays over time
        active_history: List of active status arrays over time
        deposition_positions: Final deposition positions
        deposition_mask: Mask for deposited droplets
        nozzle_position: Nozzle (x, y, z) position
        domain_x: X domain bounds
        domain_z: Z domain bounds
        save_path: Optional path to save figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot trajectories (sample to avoid clutter)
    n_sample = min(100, len(positions_history[0]))
    indices = np.linspace(0, len(positions_history[0]) - 1, n_sample, dtype=int)

    for idx in indices:
        traj_x = []
        traj_z = []

        for pos, active in zip(positions_history, active_history):
            if active[idx] > 0:
                traj_x.append(pos[idx, 0])
                traj_z.append(pos[idx, 2])

        if len(traj_x) > 1:
            ax.plot(traj_x, traj_z, 'b-', alpha=0.1, linewidth=0.5)

    # Plot deposition points
    if np.any(deposition_mask):
        dep_pos = deposition_positions[deposition_mask]
        ax.scatter(
            dep_pos[:, 0],
            dep_pos[:, 2],
            c='red',
            s=10,
            alpha=0.5,
            label='Deposited'
        )

    # Plot nozzle
    ax.plot(
        nozzle_position[0],
        nozzle_position[2],
        'rs',
        markersize=10,
        label='Nozzle'
    )

    # Formatting
    ax.set_xlabel('Downwind Distance (m)', fontsize=12)
    ax.set_ylabel('Height (m)', fontsize=12)
    ax.set_title('Spray Drift Trajectories (Side View)', fontsize=14)
    ax.set_xlim(domain_x)
    ax.set_ylim(domain_z)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    plt.show()


def plot_deposition_heatmap(
    deposition_positions: np.ndarray,
    deposition_mask: np.ndarray,
    domain_x: Tuple[float, float],
    domain_y: Tuple[float, float],
    nozzle_position: Tuple[float, float],
    resolution: int = 50,
    save_path: Optional[str] = None
):
    """
    Plot 2D heatmap of deposition density

    Args:
        deposition_positions: Deposition positions (N, 3)
        deposition_mask: Boolean mask for deposited droplets
        domain_x: X domain bounds
        domain_y: Y domain bounds
        nozzle_position: Nozzle (x, y) position
        resolution: Grid resolution for heatmap
        save_path: Optional save path
    """
    if not np.any(deposition_mask):
        print("No deposited droplets to plot")
        return

    dep_pos = deposition_positions[deposition_mask]

    # Create 2D histogram
    x_edges = np.linspace(domain_x[0], domain_x[1], resolution)
    y_edges = np.linspace(domain_y[0], domain_y[1], resolution)

    H, xedges, yedges = np.histogram2d(
        dep_pos[:, 0],
        dep_pos[:, 1],
        bins=[x_edges, y_edges]
    )

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))

    extent = [domain_x[0], domain_x[1], domain_y[0], domain_y[1]]
    im = ax.imshow(
        H.T,
        origin='lower',
        extent=extent,
        cmap='YlOrRd',
        aspect='auto',
        interpolation='bilinear'
    )

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Droplet Count', fontsize=12)

    # Mark nozzle
    ax.plot(
        nozzle_position[0],
        nozzle_position[1],
        'b*',
        markersize=15,
        label='Nozzle',
        markeredgecolor='white',
        markeredgewidth=1
    )

    # Formatting
    ax.set_xlabel('X Position (m)', fontsize=12)
    ax.set_ylabel('Y Position (m)', fontsize=12)
    ax.set_title('Ground Deposition Pattern', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3, color='white', linewidth=0.5)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    plt.show()


def plot_drift_statistics(
    state_history: list,
    time_points: np.ndarray,
    save_path: Optional[str] = None
):
    """
    Plot drift statistics over time

    Args:
        state_history: List of state dictionaries
        time_points: Time points corresponding to states
        save_path: Optional save path
    """
    # Extract statistics
    active_counts = []
    mean_heights = []
    mean_distances = []
    mean_diameters = []

    for state in state_history:
        active_mask = state['active'] > 0
        n_active = np.sum(active_mask)
        active_counts.append(n_active)

        if n_active > 0:
            pos = state['positions'][active_mask]
            diam = state['diameters'][active_mask]

            mean_heights.append(np.mean(pos[:, 2]))
            mean_distances.append(np.mean(np.sqrt(pos[:, 0]**2 + pos[:, 1]**2)))
            mean_diameters.append(np.mean(diam) * 1e6)  # microns
        else:
            mean_heights.append(0)
            mean_distances.append(0)
            mean_diameters.append(0)

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Active droplets
    axes[0, 0].plot(time_points, active_counts, 'b-', linewidth=2)
    axes[0, 0].set_ylabel('Active Droplets', fontsize=11)
    axes[0, 0].set_title('Airborne Droplet Count', fontsize=12)
    axes[0, 0].grid(True, alpha=0.3)

    # Mean height
    axes[0, 1].plot(time_points, mean_heights, 'g-', linewidth=2)
    axes[0, 1].set_ylabel('Mean Height (m)', fontsize=11)
    axes[0, 1].set_title('Average Droplet Height', fontsize=12)
    axes[0, 1].grid(True, alpha=0.3)

    # Mean horizontal distance
    axes[1, 0].plot(time_points, mean_distances, 'r-', linewidth=2)
    axes[1, 0].set_xlabel('Time (s)', fontsize=11)
    axes[1, 0].set_ylabel('Mean Distance (m)', fontsize=11)
    axes[1, 0].set_title('Average Drift Distance', fontsize=12)
    axes[1, 0].grid(True, alpha=0.3)

    # Mean diameter
    axes[1, 1].plot(time_points, mean_diameters, 'm-', linewidth=2)
    axes[1, 1].set_xlabel('Time (s)', fontsize=11)
    axes[1, 1].set_ylabel('Mean Diameter (μm)', fontsize=11)
    axes[1, 1].set_title('Droplet Evaporation', fontsize=12)
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    plt.show()

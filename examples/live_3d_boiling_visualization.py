"""
Live 3D Boiling Simulation Visualization
=========================================

Real-time interactive visualization of multi-physics boiling simulation showing:
- 3D carrot geometry with live concentration gradients
- Temperature evolution
- Surface vs. interior concentration profiles
- Leaching and degradation effects

Controls:
- Rotate: Click and drag
- Zoom: Scroll wheel
- The simulation runs in real-time with live updates
"""

import warp as wp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cooking_sim.geometry.boiling import BoilingAssembly, SaucepanBuilder
from cooking_sim.geometry.boiling.config import create_standard_saucepan_config
from cooking_sim.physics.boiling import HeatTransferModel, MaterialDatabase
from cooking_sim.kinetics.boiling import VitaminAKinetics, VitaminAProperties


class LiveBoilingSimulation:
    """Interactive live 3D simulation of boiling process"""

    def __init__(self, duration=600, dt=2.0):
        """
        Initialize live simulation

        Args:
            duration: Total simulation time (s)
            dt: Time step between visualization frames (s)
        """
        self.duration = duration
        self.dt = dt
        self.num_steps = int(duration / dt)
        self.current_step = 0
        self.current_time = 0.0

        # Physics models
        self.heat_model = None
        self.vitamin_model = None
        self.grid_info = None
        self.assembly = None  # Store assembly for full geometry access

        # Visualization data
        self.grid_points = None
        self.concentration_history = []
        self.time_history = []
        self.temp_history = []
        self.retention_history = []

        # Setup
        self._setup_simulation()
        self._setup_visualization()

    def _setup_simulation(self):
        """Initialize geometry and physics"""
        print("Initializing live simulation...")

        # Create geometry
        config = create_standard_saucepan_config()
        config.num_food_pieces = 1  # Single piece for clarity
        config.food_type = "carrot"
        config.food.carrot_cut_type = "round"
        config.food.internal_resolution = (12, 12, 16)  # Moderate resolution for speed

        assembly = SaucepanBuilder.create_from_config(config)
        self.assembly = assembly  # Store for visualization

        # Extract grid info from first carrot piece
        food = assembly.get_component("carrot_piece_0")
        grid_points = food.internal_grid_points.numpy()

        nx, ny, nz = config.food.internal_resolution
        grid_indices = []
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    grid_indices.append([i, j, k])
        grid_indices = np.array(grid_indices[:len(grid_points)], dtype=np.int32)

        # Calculate dimensions
        min_coords = np.min(grid_points, axis=0)
        max_coords = np.max(grid_points, axis=0)
        food_dimensions = max_coords - min_coords

        dx = food_dimensions[0] / (nx - 1) if nx > 1 else 0.001
        dy = food_dimensions[1] / (ny - 1) if ny > 1 else 0.001
        dz = food_dimensions[2] / (nz - 1) if nz > 1 else 0.001

        self.grid_info = {
            'grid_points': grid_points,
            'grid_indices': grid_indices,
            'mesh_points': food.mesh.points.numpy(),
            'nx': nx, 'ny': ny, 'nz': nz,
            'dx': dx, 'dy': dy, 'dz': dz,
            'food_dimensions': food_dimensions,
            'num_points': len(grid_points)
        }

        # Initialize physics
        water = assembly.get_component("water")

        # Heat transfer
        self.heat_model = HeatTransferModel(
            water_properties=MaterialDatabase.WATER,
            food_properties=MaterialDatabase.CARROT,
            boiling_temperature=100.0,
            ambient_temperature=20.0
        )
        self.heat_model.initialize_temperatures(
            num_water_points=water.num_points,
            num_food_points=self.grid_info['num_points']
        )

        # Vitamin A kinetics with diffusion
        vitamin_props = VitaminAProperties(
            initial_concentration=83.35,
            activation_energy=80000,
            diffusion_coefficient=2e-10
        )

        self.vitamin_model = VitaminAKinetics(
            properties=vitamin_props,
            enable_diffusion=True,
            enable_leaching=True
        )

        self.vitamin_model.initialize_concentrations(
            num_food_points=self.grid_info['num_points'],
            num_water_points=water.num_points
        )

        self.vitamin_model.initialize_diffusion_grid(
            grid_indices=self.grid_info['grid_indices'],
            grid_points=self.grid_info['grid_points'],
            mesh_points=self.grid_info['mesh_points'],
            nx=nx, ny=ny, nz=nz,
            food_dimensions=food_dimensions
        )

        print(f"✓ Simulation initialized: {self.num_steps} frames at {self.dt}s per frame")

    def _setup_visualization(self):
        """Setup matplotlib figure for live visualization"""
        self.fig = plt.figure(figsize=(18, 10))

        # 3D scatter plot for concentration distribution WITH GEOMETRY
        self.ax_3d = self.fig.add_subplot(2, 3, 1, projection='3d')
        self.ax_3d.set_title('Live Concentration Distribution\n(Complete Assembly: Saucepan + Water + Carrot)', fontsize=11, fontweight='bold')
        self.ax_3d.set_xlabel('X (cm)', fontsize=9)
        self.ax_3d.set_ylabel('Y (cm)', fontsize=9)
        self.ax_3d.set_zlabel('Z (cm)', fontsize=9)

        # Get grid points for carrot
        points = self.grid_info['grid_points'] * 100  # Convert to cm
        conc = self.vitamin_model.food_concentration.numpy()[:self.grid_info['num_points']]

        # Plot assembled geometry using proper mesh rendering
        # Component names from assembly: saucepan_body, water, lid, carrot_piece_0, etc.
        # Store carrot mesh surfaces for dynamic color updates
        self.carrot_mesh_surfaces = []

        for comp_name in self.assembly.components.keys():
            comp = self.assembly.get_component(comp_name)
            if comp and comp.mesh:
                mesh_pts = comp.mesh.points.numpy() * 100  # Convert to cm
                mesh_indices = comp.mesh.indices.numpy().reshape(-1, 3)  # Triangle indices

                # Render based on component name (order matters - most specific first)
                if comp_name == "saucepan_body":
                    # Plot saucepan as gray semi-transparent surface
                    self.ax_3d.plot_trisurf(
                        mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                        triangles=mesh_indices,
                        alpha=0.2, color='gray', linewidth=0, shade=True
                    )
                elif comp_name == "water":
                    # Plot water as cyan semi-transparent surface
                    self.ax_3d.plot_trisurf(
                        mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                        triangles=mesh_indices,
                        alpha=0.2, color='cyan', linewidth=0, shade=True
                    )
                elif comp_name == "lid":
                    # Plot lid as dark gray semi-transparent surface
                    self.ax_3d.plot_trisurf(
                        mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                        triangles=mesh_indices,
                        alpha=0.3, color='darkgray', linewidth=0, shade=True
                    )
                elif comp_name.startswith("carrot_piece_"):
                    # Plot carrot mesh with DYNAMIC color based on concentration kinetics
                    # Initial color: healthy orange (will update based on degradation/leaching)
                    carrot_surf = self.ax_3d.plot_trisurf(
                        mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                        triangles=mesh_indices,
                        alpha=0.5, color='orange', linewidth=0, shade=True
                    )
                    # Store surface for dynamic color updates
                    self.carrot_mesh_surfaces.append(carrot_surf)
                elif comp_name.startswith("potato_piece_"):
                    # Plot potato mesh as tan surface
                    self.ax_3d.plot_trisurf(
                        mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                        triangles=mesh_indices,
                        alpha=0.3, color='tan', linewidth=0, shade=True
                    )
                else:
                    # Fallback: render unknown components as light gray with warning
                    print(f"Warning: Unknown component '{comp_name}' - rendering as light gray")
                    self.ax_3d.plot_trisurf(
                        mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                        triangles=mesh_indices,
                        alpha=0.2, color='lightgray', linewidth=0, shade=True
                    )

        # Carrot concentration scatter plot (ON TOP of mesh)
        self.scatter = self.ax_3d.scatter(
            points[:, 0], points[:, 1], points[:, 2],
            c=conc,
            cmap='RdYlGn',
            s=50,
            alpha=1.0,
            vmin=60,  # Fixed scale for consistent visualization
            vmax=85,
            edgecolors='black',
            linewidths=0.5,
            depthshade=True
        )
        self.colorbar = self.fig.colorbar(self.scatter, ax=self.ax_3d, shrink=0.6, pad=0.1)
        self.colorbar.set_label('Vitamin A (μg/g)', fontsize=9)

        # Set view limits to show full assembly
        all_x = [p * 100 for c in self.assembly.components.values() if c.mesh for p in c.mesh.points.numpy()[:, 0]]
        all_y = [p * 100 for c in self.assembly.components.values() if c.mesh for p in c.mesh.points.numpy()[:, 1]]
        all_z = [p * 100 for c in self.assembly.components.values() if c.mesh for p in c.mesh.points.numpy()[:, 2]]

        if all_x:
            padding = 2  # cm
            self.ax_3d.set_xlim([min(all_x) - padding, max(all_x) + padding])
            self.ax_3d.set_ylim([min(all_y) - padding, max(all_y) + padding])
            self.ax_3d.set_zlim([min(all_z) - 0.5, max(all_z) + padding])

        # Set better viewing angle
        self.ax_3d.view_init(elev=25, azim=45)

        # Add kinetic status text annotation
        self.kinetic_text = self.ax_3d.text2D(0.02, 0.98, '', transform=self.ax_3d.transAxes,
                                               fontsize=8, verticalalignment='top',
                                               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

        # Temperature profile (PHYSICS)
        self.ax_temp = self.fig.add_subplot(2, 3, 2)
        self.ax_temp.set_title('Temperature Evolution\n(Heat Transfer Physics)', fontsize=11, fontweight='bold')
        self.ax_temp.set_xlabel('Time (minutes)', fontsize=9)
        self.ax_temp.set_ylabel('Temperature (°C)', fontsize=9)
        self.ax_temp.set_xlim([0, self.duration / 60])
        self.ax_temp.set_ylim([15, 105])
        self.ax_temp.grid(True, alpha=0.3)
        self.line_temp, = self.ax_temp.plot([], [], 'r-', linewidth=2.5, label='Carrot Temp')
        self.ax_temp.axhline(100, color='b', linestyle='--', alpha=0.6, linewidth=1.5, label='Water (Boiling)')
        self.ax_temp.axhline(20, color='gray', linestyle=':', alpha=0.5, label='Initial')
        self.ax_temp.legend(fontsize=8, loc='lower right')
        self.ax_temp.text(0.02, 0.98, 'Exponential heating\nτ ≈ 120s',
                         transform=self.ax_temp.transAxes, fontsize=8,
                         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        # Retention profile (KINETICS)
        self.ax_retention = self.fig.add_subplot(2, 3, 3)
        self.ax_retention.set_title('Vitamin A Retention\n(Degradation + Leaching Kinetics)', fontsize=11, fontweight='bold')
        self.ax_retention.set_xlabel('Time (minutes)', fontsize=9)
        self.ax_retention.set_ylabel('Retention (%)', fontsize=9)
        self.ax_retention.set_xlim([0, self.duration / 60])
        self.ax_retention.set_ylim([70, 102])
        self.ax_retention.grid(True, alpha=0.3)
        self.line_retention, = self.ax_retention.plot([], [], 'g-', linewidth=2.5, label='Total Retention')
        self.ax_retention.axhline(100, color='k', linestyle='--', alpha=0.4, label='Initial (100%)')
        self.ax_retention.legend(fontsize=8)
        self.ax_retention.text(0.02, 0.02, f'Ea = {self.vitamin_model.props.activation_energy/1000:.0f} kJ/mol\nk = k₀·exp(-Ea/RT)',
                              transform=self.ax_retention.transAxes, fontsize=7,
                              verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

        # Concentration gradient (DIFFUSION + LEACHING)
        self.ax_gradient = self.fig.add_subplot(2, 3, 4)
        self.ax_gradient.set_title('Surface vs. Interior Concentration\n(Diffusion + Leaching)', fontsize=11, fontweight='bold')
        self.ax_gradient.set_xlabel('Time (minutes)', fontsize=9)
        self.ax_gradient.set_ylabel('Concentration (μg/g)', fontsize=9)
        self.ax_gradient.set_xlim([0, self.duration / 60])
        self.ax_gradient.set_ylim([60, 85])
        self.ax_gradient.grid(True, alpha=0.3)
        self.line_surface, = self.ax_gradient.plot([], [], 'b-', linewidth=2.5, label='Surface', marker='o', markersize=2, markevery=10)
        self.line_interior, = self.ax_gradient.plot([], [], 'r-', linewidth=2.5, label='Interior', marker='s', markersize=2, markevery=10)
        self.ax_gradient.axhline(self.vitamin_model.props.initial_concentration,
                                  color='k', linestyle='--', alpha=0.5, label='Initial')
        self.ax_gradient.legend(fontsize=8, loc='upper right')
        self.ax_gradient.text(0.02, 0.02, f'D = {self.vitamin_model.props.diffusion_coefficient:.1e} m²/s\nLeaching to water',
                             transform=self.ax_gradient.transAxes, fontsize=7,
                             verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))

        # Degradation rate (NEW - shows temperature dependence)
        self.ax_rate = self.fig.add_subplot(2, 3, 5)
        self.ax_rate.set_title('Degradation Rate Constant\n(Arrhenius Kinetics)', fontsize=11, fontweight='bold')
        self.ax_rate.set_xlabel('Time (minutes)', fontsize=9)
        self.ax_rate.set_ylabel('k (s⁻¹)', fontsize=9)
        self.ax_rate.set_xlim([0, self.duration / 60])
        self.ax_rate.set_yscale('log')
        self.ax_rate.grid(True, alpha=0.3, which='both')
        self.line_rate, = self.ax_rate.plot([], [], 'purple', linewidth=2.5, label='k(T)')
        self.ax_rate.legend(fontsize=8)
        self.rate_history = []

        # Concentration profile (NEW - spatial distribution)
        self.ax_profile = self.fig.add_subplot(2, 3, 6)
        self.ax_profile.set_title('Radial Concentration Profile\n(at current time)', fontsize=11, fontweight='bold')
        self.ax_profile.set_xlabel('Radial Distance from Center (mm)', fontsize=9)
        self.ax_profile.set_ylabel('Concentration (μg/g)', fontsize=9)
        self.ax_profile.grid(True, alpha=0.3)
        self.line_profile, = self.ax_profile.plot([], [], 'o-', linewidth=2, markersize=4, color='darkgreen', label='Current')
        self.ax_profile.legend(fontsize=8)

        # Add time display
        self.time_text = self.fig.text(0.5, 0.95, '', ha='center', fontsize=14, fontweight='bold')

        plt.tight_layout(rect=[0, 0, 1, 0.96])

    def step_simulation(self):
        """Advance simulation by one time step"""
        if self.current_step >= self.num_steps:
            return False

        # Update temperature
        if self.heat_model.food_temperature is not None:
            food_temps = self.heat_model.food_temperature.numpy()
            tau = 120.0  # time constant
            food_temps += (self.heat_model.T_boiling - food_temps) * (1 - np.exp(-self.dt/tau))
            self.heat_model.food_temperature = wp.array(food_temps, dtype=float)

        # Update degradation rate constants
        self.vitamin_model.update_rate_constants(self.heat_model.food_temperature)

        # Full multi-physics step
        self.vitamin_model.step_full(
            dt=self.dt,
            num_points=self.grid_info['num_points'],
            mass_transfer_coeff=5e-5
        )

        self.current_time += self.dt
        self.current_step += 1

        return True

    def update_frame(self, frame):
        """Update visualization for animation"""
        # Step simulation
        if not self.step_simulation():
            return

        # Get current data
        conc = self.vitamin_model.food_concentration.numpy()[:self.grid_info['num_points']]
        avg_temp = np.mean(self.heat_model.food_temperature.numpy())
        stats = self.vitamin_model.get_statistics()
        retention = stats.get('retention_%', 100.0)

        # Surface vs interior
        if self.vitamin_model.is_surface_point is not None:
            is_surface = self.vitamin_model.is_surface_point.numpy()[:self.grid_info['num_points']]
            surface_conc = np.mean(conc[is_surface == 1]) if np.any(is_surface) else np.mean(conc)
            interior_conc = np.mean(conc[is_surface == 0]) if np.any(is_surface == 0) else np.mean(conc)
        else:
            surface_conc = np.mean(conc)
            interior_conc = np.mean(conc)

        # Store history
        self.concentration_history.append(conc.copy())
        self.time_history.append(self.current_time / 60)  # Convert to minutes
        self.temp_history.append(avg_temp)
        self.retention_history.append(retention)

        # Update 3D scatter plot with dynamic color scaling
        self.scatter.set_array(conc)
        # Adjust color limits if concentration drops below 60 or exceeds 85
        min_conc_3d = np.min(conc)
        max_conc_3d = np.max(conc)
        if min_conc_3d < 60 or max_conc_3d > 85:
            # Use dynamic range with 2 μg/g padding
            self.scatter.set_clim(vmin=min_conc_3d - 2, vmax=max_conc_3d + 2)

        # Update carrot mesh color based on KINETICS (degradation + leaching + diffusion)
        # Color reflects current nutrient status: green (healthy) → yellow → orange → red (depleted)
        avg_conc = np.mean(conc)
        initial_conc = self.vitamin_model.props.initial_concentration  # 83.35 μg/g
        retention_ratio = avg_conc / initial_conc

        # Color mapping based on retention (kinetic effect visualization):
        # 100% retention → vibrant orange (RGB: 1.0, 0.5, 0.0)
        # 80% retention → orange-yellow (RGB: 1.0, 0.6, 0.1)
        # 60% retention → yellow-tan (RGB: 0.9, 0.7, 0.3)
        # 40% retention → pale tan (RGB: 0.8, 0.7, 0.5)
        # 20% retention → grayish-brown (RGB: 0.6, 0.6, 0.5)
        if retention_ratio >= 0.90:
            # Healthy: vibrant orange
            r, g, b = 1.0, 0.5, 0.0
        elif retention_ratio >= 0.75:
            # Mild degradation: orange-yellow transition
            t = (retention_ratio - 0.75) / 0.15
            r, g, b = 1.0, 0.5 + 0.1 * (1 - t), 0.0 + 0.1 * (1 - t)
        elif retention_ratio >= 0.60:
            # Moderate degradation: yellow-tan
            t = (retention_ratio - 0.60) / 0.15
            r, g, b = 1.0 - 0.1 * (1 - t), 0.6 + 0.1 * t, 0.1 + 0.2 * (1 - t)
        elif retention_ratio >= 0.40:
            # Significant degradation: pale tan
            t = (retention_ratio - 0.40) / 0.20
            r, g, b = 0.9 - 0.1 * (1 - t), 0.7, 0.3 + 0.2 * (1 - t)
        else:
            # Severe degradation: grayish-brown
            t = max(0, retention_ratio / 0.40)
            r, g, b = 0.6 + 0.2 * t, 0.6 + 0.1 * t, 0.5

        # Update all carrot mesh surfaces with new color
        for surf in self.carrot_mesh_surfaces:
            surf.set_color((r, g, b))

        # Update kinetic status annotation
        self.kinetic_text.set_text(
            f'Carrot Kinetics:\n'
            f'Retention: {retention_ratio*100:.1f}%\n'
            f'Avg Conc: {avg_conc:.1f} μg/g\n'
            f'Color: Degr+Leach+Diff'
        )

        # Update temperature plot
        self.line_temp.set_data(self.time_history, self.temp_history)

        # Update retention plot with dynamic Y-axis
        self.line_retention.set_data(self.time_history, self.retention_history)
        if len(self.retention_history) > 0:
            min_retention = min(self.retention_history)
            max_retention = max(self.retention_history)
            # Always show 100% reference line, but compress down if retention drops below 70%
            y_min = min(70, min_retention - 2)  # Go below 70 if needed
            y_max = max(102, max_retention + 2)  # Keep some headroom above 100%
            self.ax_retention.set_ylim([y_min, y_max])

        # Update gradient plot
        surface_conc_history = []
        interior_conc_history = []
        for c_hist in self.concentration_history:
            if self.vitamin_model.is_surface_point is not None:
                is_surf = self.vitamin_model.is_surface_point.numpy()[:self.grid_info['num_points']]
                surf_c = np.mean(c_hist[is_surf == 1]) if np.any(is_surf) else np.mean(c_hist)
                int_c = np.mean(c_hist[is_surf == 0]) if np.any(is_surf == 0) else np.mean(c_hist)
                surface_conc_history.append(surf_c)
                interior_conc_history.append(int_c)
            else:
                surface_conc_history.append(np.mean(c_hist))
                interior_conc_history.append(np.mean(c_hist))

        self.line_surface.set_data(self.time_history, surface_conc_history)
        self.line_interior.set_data(self.time_history, interior_conc_history)

        # Dynamically adjust Y-axis limits for concentration gradient plot
        if len(surface_conc_history) > 0 and len(interior_conc_history) > 0:
            all_conc = surface_conc_history + interior_conc_history
            min_conc = min(all_conc)
            max_conc = max(all_conc)
            # Add 5% padding for better visualization
            padding = (max_conc - min_conc) * 0.05 if max_conc > min_conc else 2.0
            self.ax_gradient.set_ylim([min_conc - padding, max_conc + padding])

        # Update degradation rate plot (shows temperature dependence via Arrhenius)
        if hasattr(self.vitamin_model, 'rate_constants') and self.vitamin_model.rate_constants is not None:
            k_val = np.mean(self.vitamin_model.rate_constants.numpy())
            self.rate_history.append(k_val)
            self.line_rate.set_data(self.time_history, self.rate_history)
            if len(self.rate_history) > 0:
                self.ax_rate.set_ylim([min(self.rate_history) * 0.5, max(self.rate_history) * 2])

        # Update radial concentration profile (NEW)
        grid_pts = self.grid_info['grid_points']
        center = np.mean(grid_pts, axis=0)
        distances = np.linalg.norm(grid_pts - center, axis=1) * 1000  # Convert to mm

        # Sort by distance for clean profile
        sorted_indices = np.argsort(distances)
        sorted_dist = distances[sorted_indices]
        sorted_conc = conc[sorted_indices]

        # Bin and average for smoother profile
        n_bins = 15
        bin_edges = np.linspace(0, sorted_dist.max(), n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_means = []
        for i in range(n_bins):
            mask = (sorted_dist >= bin_edges[i]) & (sorted_dist < bin_edges[i+1])
            if np.any(mask):
                bin_means.append(np.mean(sorted_conc[mask]))
            else:
                bin_means.append(np.nan)

        self.line_profile.set_data(bin_centers, bin_means)
        self.ax_profile.set_xlim([0, sorted_dist.max() * 1.1])
        self.ax_profile.set_ylim([min(conc) - 2, max(conc) + 2])

        # Update time display
        self.time_text.set_text(
            f'Multi-Physics Boiling Simulation | '
            f'Time: {self.current_time:.1f}s ({self.current_time/60:.2f} min) | '
            f'Temp: {avg_temp:.1f}°C | '
            f'Retention: {retention:.1f}% | '
            f'Surface Gradient: {interior_conc - surface_conc:.2f} μg/g | '
            f'Progress: {100*self.current_step/self.num_steps:.0f}%'
        )

        # Rotate 3D view slightly for dynamic effect
        self.ax_3d.view_init(elev=25, azim=30 + frame * 0.3)

        # Print progress
        if self.current_step % 10 == 0:
            print(f"  Frame {self.current_step}/{self.num_steps}: "
                  f"t={self.current_time:.1f}s, T={avg_temp:.1f}°C, "
                  f"Retention={retention:.1f}%, Surface={surface_conc:.1f} μg/g, "
                  f"Interior={interior_conc:.1f} μg/g, Gradient={interior_conc-surface_conc:.2f} μg/g")

        return self.scatter, self.line_temp, self.line_retention, self.line_surface, self.line_interior, self.line_rate, self.line_profile

    def run(self):
        """Run live simulation with animation"""
        print("\n" + "=" * 80)
        print("STARTING LIVE 3D VISUALIZATION")
        print("=" * 80)
        print(f"\nSimulation: {self.duration}s at {self.dt}s/frame = {self.num_steps} frames")
        print("Close the window to stop the simulation\n")

        # Create animation
        anim = FuncAnimation(
            self.fig,
            self.update_frame,
            frames=self.num_steps,
            interval=50,  # 50ms between frames (20 fps)
            blit=False,
            repeat=False
        )

        plt.show()

        print("\n" + "=" * 80)
        print("LIVE SIMULATION COMPLETE")
        print("=" * 80)
        print(f"\nFinal state:")
        print(f"  - Time: {self.current_time:.1f}s ({self.current_time/60:.2f} minutes)")
        print(f"  - Temperature: {self.temp_history[-1]:.1f}°C")
        print(f"  - Retention: {self.retention_history[-1]:.1f}%")
        print("=" * 80 + "\n")


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("LIVE 3D BOILING SIMULATION VISUALIZATION")
    print("Multi-physics real-time animation")
    print("=" * 80)

    # Initialize Warp
    wp.init()
    print(f"\nWarp initialized: {wp.get_device()}")

    # Create and run live simulation
    sim = LiveBoilingSimulation(
        duration=800,  # 10 minutes total
        dt=2.0         # 2 second time steps (smoother animation)
    )

    sim.run()


if __name__ == "__main__":
    main()

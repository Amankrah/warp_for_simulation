"""
Live Interactive 3D Boiling Simulation with Warp OpenGL Renderer
=================================================================

Real-time GPU-accelerated visualization with interactive 3D window.

Features:
- Live 3D OpenGL window with interactive controls
- Real-time concentration-based coloring (green → yellow → orange → red)
- Heat transfer, diffusion, and leaching physics running live
- Statistics overlay showing current state

Controls:
- Mouse drag: Rotate camera
- Mouse wheel: Zoom in/out
- WASD: Pan camera
- Space: Pause/Resume simulation
- R: Reset camera
- ESC/Q: Exit
"""

import warp as wp
import warp.render
import numpy as np
import sys
import os
import time
import imageio
from pathlib import Path
from PIL import Image
import tempfile

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cooking_sim.geometry.boiling import BoilingAssembly, SaucepanBuilder
from cooking_sim.geometry.boiling.config import create_standard_saucepan_config
from cooking_sim.physics.boiling import HeatTransferModel, MaterialDatabase
from cooking_sim.kinetics.boiling import VitaminAKinetics, VitaminAProperties


class InteractiveLiveSimulation:
    """Live interactive 3D simulation with OpenGL renderer"""

    def __init__(self, duration=600, dt=1.0, render_fps=60, save_video=True, output_path="output/live_boiling_simulation.mp4"):
        """
        Initialize interactive simulation

        Args:
            duration: Total simulation time (s)
            dt: Physics timestep (s)
            render_fps: Target rendering frame rate
            save_video: Whether to save video
            output_path: Path to save video file
        """
        self.duration = duration
        self.dt = dt
        self.render_fps = render_fps
        self.render_interval = 1.0 / render_fps

        self.current_time = 0.0
        self.frame_count = 0
        self.paused = False
        self.running = True

        # Video recording
        self.save_video = save_video
        self.output_path = output_path
        self.video_writer = None
        self.video_frames = []
        self.temp_frame_dir = None  # Temporary directory for frame images

        # Simulation components
        self.assembly = None
        self.heat_model = None
        self.vitamin_model = None
        self.grid_info = None

        # Warp renderer
        self.renderer = None

        # Statistics
        self.stats = {
            'temperature': 20.0,
            'retention': 100.0,
            'surface_conc': 83.35,
            'interior_conc': 83.35
        }

        self._setup_simulation()
        self._setup_renderer()

    def _setup_simulation(self):
        """Initialize geometry and physics"""
        print("\n" + "=" * 80)
        print("INITIALIZING INTERACTIVE SIMULATION")
        print("=" * 80)

        # Create assembly
        config = create_standard_saucepan_config()
        config.num_food_pieces = 1
        config.food_type = "carrot"
        config.food.carrot_cut_type = "round"
        config.food.internal_resolution = (10, 10, 12)  # Lower res for speed
        config.with_lid = False

        self.assembly = SaucepanBuilder.create_from_config(config)

        # Extract grid info
        food = self.assembly.get_component("carrot_piece_0")
        grid_points = food.internal_grid_points.numpy()

        nx, ny, nz = config.food.internal_resolution
        grid_indices = []
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    grid_indices.append([i, j, k])
        grid_indices = np.array(grid_indices[:len(grid_points)], dtype=np.int32)

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
        water = self.assembly.get_component("water")

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

        print(f"\n✓ Simulation initialized")
        print(f"  - Grid: {nx}×{ny}×{nz} = {self.grid_info['num_points']} points")
        print(f"  - Physics timestep: {self.dt}s")
        print(f"  - Render FPS: {self.render_fps}")

    def _setup_renderer(self):
        """Setup Warp OpenGL renderer"""
        print("\n" + "=" * 80)
        print("INITIALIZING OPENGL RENDERER")
        print("=" * 80)

        try:
            # Use correct OpenGLRenderer API
            # Adjust camera to view small meshes (carrot is ~3cm, water ~20cm)
            self.renderer = wp.render.OpenGLRenderer(
                title="Boiling Carrot Simulation",
                screen_width=1920,
                screen_height=1080,
                up_axis="Z",
                camera_pos=(0.0, -0.15, 0.08),  # Closer: 15cm back, 8cm up
                camera_front=(0.0, 1.0, -0.2),   # Look forward and slightly down
                draw_grid=True,
                draw_sky=True,
                show_info=True,
                scaling=10.0  # Scale up the scene for better visibility
            )

            # Create temporary directory for frame capture
            if self.save_video:
                self.temp_frame_dir = tempfile.mkdtemp(prefix="warp_sim_")

            print("\n✓ OpenGL renderer initialized")
            print("  - Window: 1920x1080")
            print("  - Interactive camera controls enabled")
        except Exception as e:
            print(f"\nWarning: Could not initialize OpenGL renderer: {e}")
            print("Falling back to headless mode (no visualization)")
            self.renderer = None

    def _get_concentration_color(self, concentration):
        """Convert concentration to RGB color"""
        c_min = 60.0
        c_max = 85.0
        t = np.clip((concentration - c_min) / (c_max - c_min), 0, 1)

        if t < 0.5:
            r = 1.0
            g = t * 2.0
            b = 0.0
        else:
            r = 1.0 - (t - 0.5) * 2.0
            g = 1.0
            b = 0.0

        return (r, g, b)

    def step_simulation(self):
        """Advance simulation by one timestep"""
        if self.paused:
            return

        # Update temperature
        if self.heat_model.food_temperature is not None:
            food_temps = self.heat_model.food_temperature.numpy()
            tau = 120.0
            food_temps += (self.heat_model.T_boiling - food_temps) * (1 - np.exp(-self.dt/tau))
            self.heat_model.food_temperature = wp.array(food_temps, dtype=float)

        # Update rate constants
        self.vitamin_model.update_rate_constants(self.heat_model.food_temperature)

        # Full physics step
        self.vitamin_model.step_full(
            dt=self.dt,
            num_points=self.grid_info['num_points'],
            mass_transfer_coeff=5e-5
        )

        self.current_time += self.dt

        # Update statistics
        conc = self.vitamin_model.food_concentration.numpy()[:self.grid_info['num_points']]
        self.stats['temperature'] = np.mean(self.heat_model.food_temperature.numpy())
        stats_dict = self.vitamin_model.get_statistics()
        self.stats['retention'] = stats_dict.get('retention_%', 100.0)

        if self.vitamin_model.is_surface_point is not None:
            is_surface = self.vitamin_model.is_surface_point.numpy()[:self.grid_info['num_points']]
            self.stats['surface_conc'] = np.mean(conc[is_surface == 1]) if np.any(is_surface) else np.mean(conc)
            self.stats['interior_conc'] = np.mean(conc[is_surface == 0]) if np.any(is_surface == 0) else np.mean(conc)
        else:
            self.stats['surface_conc'] = np.mean(conc)
            self.stats['interior_conc'] = np.mean(conc)

        # Update carrot colors based on concentration
        self._update_carrot_colors()

        # Print progress
        if int(self.current_time) % 10 == 0 and self.frame_count % self.render_fps == 0:
            progress = 100 * self.current_time / self.duration
            print(f"  t={self.current_time:.0f}s ({progress:.0f}%): "
                  f"T={self.stats['temperature']:.1f}°C, "
                  f"Retention={self.stats['retention']:.1f}%, "
                  f"Surface={self.stats['surface_conc']:.1f} μg/g")

    def _update_carrot_colors(self):
        """Update carrot mesh colors based on concentration"""
        food = self.assembly.get_component("carrot_piece_0")
        if not food or not food.mesh:
            return

        # Get concentrations
        conc = self.vitamin_model.food_concentration.numpy()[:self.grid_info['num_points']]

        # Map to mesh vertices
        mesh_verts = food.mesh.points.numpy()
        grid_pts = self.grid_info['grid_points']
        mesh_colors = np.zeros((len(mesh_verts), 3), dtype=np.float32)

        for i, vert in enumerate(mesh_verts):
            distances = np.linalg.norm(grid_pts - vert, axis=1)
            nearest_idx = np.argmin(distances)
            nearest_conc = conc[nearest_idx]
            mesh_colors[i] = self._get_concentration_color(nearest_conc)

        # Update colors in assembly (if renderer supports it)
        # Note: This is a simplified approach
        # For full color support, you'd need to modify the renderer

    def _render_frame(self):
        """Render current frame and optionally capture for video"""
        if not self.renderer:
            return

        # Begin rendering
        self.renderer.begin_frame(time.time())

        # Render the carrot mesh with average color based on concentration
        food = self.assembly.get_component("carrot_piece_0")
        if food and food.mesh:
            # Get mesh data
            vertices = food.mesh.points.numpy()
            indices = food.mesh.indices.numpy().reshape(-1, 3)

            # Get average concentration for color
            conc = self.vitamin_model.food_concentration.numpy()[:self.grid_info['num_points']]
            avg_conc = np.mean(conc)

            # Get color based on average concentration
            color_rgb = self._get_concentration_color(avg_conc)

            # Debug: Print mesh info on first frame
            if self.frame_count == 0:
                print(f"\nCarrot mesh: {len(vertices)} vertices, {len(indices)} triangles")
                print(f"  Bounds: {np.min(vertices, axis=0)} to {np.max(vertices, axis=0)}")
                print(f"  Color: {color_rgb}, Concentration: {avg_conc:.2f} μg/g")

            # Render the mesh with single color
            self.renderer.render_mesh(
                name="carrot",
                points=vertices,
                indices=indices,
                colors=color_rgb  # Single RGB tuple
            )

        # Render water (simple blue)
        water = self.assembly.get_component("water")
        if water and water.mesh:
            water_vertices = water.mesh.points.numpy()
            water_indices = water.mesh.indices.numpy().reshape(-1, 3)

            # Debug: Print mesh info on first frame
            if self.frame_count == 0:
                print(f"\nWater mesh: {len(water_vertices)} vertices, {len(water_indices)} triangles")
                print(f"  Bounds: {np.min(water_vertices, axis=0)} to {np.max(water_vertices, axis=0)}")

            self.renderer.render_mesh(
                name="water",
                points=water_vertices,
                indices=water_indices,
                colors=(0.2, 0.5, 0.8)  # Single RGB tuple
            )

        # End frame and capture
        self.renderer.end_frame()

        # Capture frame for video using pyglet's buffer capture
        if self.save_video and self.temp_frame_dir is not None:
            try:
                # Capture screen buffer using pyglet
                import pyglet.image
                color_buffer = pyglet.image.get_buffer_manager().get_color_buffer()
                image_data = color_buffer.get_image_data()

                # Convert to PIL Image and then numpy
                pil_image = image_data.get_image_data().get_data('RGB', image_data.width * 3)
                img_array = np.frombuffer(pil_image, dtype=np.uint8)
                img_array = img_array.reshape((image_data.height, image_data.width, 3))

                # Flip vertically (OpenGL has origin at bottom-left)
                img_array = np.flipud(img_array)

                self.video_frames.append(img_array.copy())
            except Exception as e:
                # Silently skip frame capture errors
                pass

    def run(self):
        """Run interactive simulation"""
        print("\n" + "=" * 80)
        print("STARTING INTERACTIVE SIMULATION")
        print("=" * 80)
        print("\nControls:")
        print("  - Mouse drag: Rotate camera")
        print("  - Mouse wheel: Zoom")
        print("  - WASD: Pan camera")
        print("  - Space: Pause/Resume")
        print("  - ESC/Q: Exit")
        if self.save_video:
            print(f"\n  Video will be saved to: {self.output_path}")
        print("\n" + "-" * 80 + "\n")

        last_render_time = time.time()

        try:
            if self.renderer:
                # Interactive rendering loop
                while self.running and self.current_time < self.duration:
                    # Step physics
                    self.step_simulation()

                    # Render frame
                    current_time = time.time()
                    if current_time - last_render_time >= self.render_interval:
                        self._render_frame()
                        last_render_time = current_time
                        self.frame_count += 1

                    # Check if window is still open
                    if not self.renderer.is_running():
                        print("\n\nWindow closed by user")
                        self.running = False
                        break

            else:
                # Headless mode - just run simulation
                while self.current_time < self.duration:
                    self.step_simulation()
                    time.sleep(self.render_interval)
                    self.frame_count += 1

        except KeyboardInterrupt:
            print("\n\nSimulation interrupted by user")

        # Save video
        if self.save_video and len(self.video_frames) > 0:
            self._save_video()

        # Final statistics
        print("\n" + "-" * 80)
        print("✓ SIMULATION COMPLETE")
        print("=" * 80)
        print(f"\nFinal Statistics:")
        print(f"  - Simulation time: {self.current_time:.1f}s ({self.current_time/60:.2f} minutes)")
        print(f"  - Frames: {self.frame_count}")
        print(f"  - Final temperature: {self.stats['temperature']:.1f}°C")
        print(f"  - Final retention: {self.stats['retention']:.1f}%")
        print(f"  - Surface concentration: {self.stats['surface_conc']:.2f} μg/g")
        print(f"  - Interior concentration: {self.stats['interior_conc']:.2f} μg/g")
        print(f"  - Gradient: {self.stats['interior_conc'] - self.stats['surface_conc']:.2f} μg/g")
        print("=" * 80 + "\n")

    def _save_video(self):
        """Save captured frames to video file"""
        print("\n" + "=" * 80)
        print("SAVING VIDEO")
        print("=" * 80)

        # Create output directory if needed
        output_dir = Path(self.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            print(f"\n  Writing {len(self.video_frames)} frames to {self.output_path}...")
            imageio.mimsave(
                self.output_path,
                self.video_frames,
                fps=self.render_fps,
                codec='libx264',
                quality=8
            )
            print(f"  ✓ Video saved successfully")
            print(f"  - File: {self.output_path}")
            print(f"  - Frames: {len(self.video_frames)}")
            print(f"  - Duration: {len(self.video_frames)/self.render_fps:.1f}s")
            print(f"  - FPS: {self.render_fps}")
        except Exception as e:
            print(f"  ✗ Error saving video: {e}")

        # Clean up temporary directory
        if self.temp_frame_dir and os.path.exists(self.temp_frame_dir):
            import shutil
            shutil.rmtree(self.temp_frame_dir, ignore_errors=True)

        print("=" * 80 + "\n")


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("WARP INTERACTIVE 3D BOILING SIMULATION")
    print("Live GPU-Accelerated Multi-Physics Visualization")
    print("=" * 80)

    # Initialize Warp
    wp.init()
    print(f"\n✓ Warp initialized: {wp.get_device()}")

    # Create and run simulation
    sim = InteractiveLiveSimulation(
        duration=600,     # 10 minutes
        dt=1.0,          # 1 second physics timestep
        render_fps=60    # 60 FPS rendering
    )

    sim.run()


if __name__ == "__main__":
    main()

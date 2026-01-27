"""
Save Spray Drift Video

A simplified wrapper to record spray drift animation as video.
This script runs in off-screen mode for faster rendering.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import time
import pyvista as pv
from agridrift import SprayConfig, WindConfig, SimulationConfig, DropletSimulator


def save_video(
    output_path: str = "output/spray_drift.mp4",
    fps: int = 10,
    num_droplets: int = 2000,
    wind_speed: float = 3.0,
    simulation_time: float = 12.0
):
    """
    Generate and save spray drift animation as video

    Args:
        output_path: Output video file path
        fps: Frames per second
        num_droplets: Number of droplets to simulate
        wind_speed: Wind speed in m/s
        simulation_time: Total simulation time (will stop early if all droplets land)
    """

    print("=" * 60)
    print("AGRIDRIFT - Video Recording")
    print("=" * 60)
    print()
    print(f"Output: {output_path}")
    print(f"FPS: {fps}")
    print(f"Droplets: {num_droplets}")
    print(f"Wind: {wind_speed} m/s")
    print()

    # Create output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Configuration
    spray_config = SprayConfig(
        nozzle_height=2.0,
        nozzle_position=(0.0, 0.0),
        spray_angle=30.0,
        num_droplets=num_droplets,
        droplet_diameter_mean=250e-6,
        droplet_diameter_std=75e-6,
        initial_velocity=5.0,
        concentration=2.0
    )

    wind_config = WindConfig(
        wind_speed=wind_speed,
        wind_direction=90.0,
        reference_height=10.0,
        turbulence_intensity=0.2,
        gust_amplitude=0.5,
        gust_period=10.0
    )

    sim_config = SimulationConfig(
        dt=0.02,
        total_time=simulation_time,
        output_interval=0.1,  # Frame every 0.1s of sim time
        domain_x=(-5.0, 20.0),
        domain_y=(-10.0, 10.0),
        domain_z=(0.0, 8.0),
        enable_evaporation=True,
        temperature=293.15,
        relative_humidity=0.6,
        device="cuda:0"
    )

    # Initialize simulator
    print("Initializing simulator...")
    simulator = DropletSimulator(spray_config, wind_config, sim_config)
    print(f"Initialized {simulator.num_droplets} droplets")
    print()

    # Setup plotter (off-screen for video recording)
    plotter = pv.Plotter(window_size=(1920, 1080), off_screen=True)
    plotter.set_background('lightblue')

    # Add ground
    x_center = (sim_config.domain_x[0] + sim_config.domain_x[1]) / 2
    y_center = (sim_config.domain_y[0] + sim_config.domain_y[1]) / 2
    x_size = sim_config.domain_x[1] - sim_config.domain_x[0]
    y_size = sim_config.domain_y[1] - sim_config.domain_y[0]

    ground = pv.Plane(
        center=(x_center, y_center, 0),
        direction=(0, 0, 1),
        i_size=x_size,
        j_size=y_size,
        i_resolution=10,
        j_resolution=10
    )
    plotter.add_mesh(ground, color='green', opacity=0.4, show_edges=True)

    # Add nozzle
    nozzle = pv.Sphere(
        radius=0.15,
        center=(spray_config.nozzle_position[0],
                spray_config.nozzle_position[1],
                spray_config.nozzle_height)
    )
    plotter.add_mesh(nozzle, color='red', opacity=1.0)

    # Add text display
    text_actor = plotter.add_text(
        "Initializing...",
        position='upper_left',
        font_size=12,
        color='black'
    )

    # Camera position
    plotter.camera_position = [
        (12, -15, 8),
        (7, 0, 1),
        (0, 0, 1)
    ]

    # Initial point cloud
    points = pv.PolyData(np.array([[0, 0, 0]]))
    points['diameter_um'] = np.array([250.0])

    particle_actor = plotter.add_mesh(
        points,
        scalars='diameter_um',
        cmap='plasma',
        point_size=15,
        render_points_as_spheres=True,
        show_scalar_bar=True,
        clim=[100, 400],
        opacity=0.8
    )

    # Deposition tracking
    deposited_points_list = []
    deposition_actor = None

    # Animation parameters
    n_steps_per_frame = int(sim_config.output_interval / sim_config.dt)
    frame_count = 0
    start_time = time.time()

    # Open video file
    plotter.open_movie(str(output_file), framerate=fps, quality=9)
    print("Recording...")

    try:
        # Animation loop
        while simulator.current_time < sim_config.total_time:
            # Run simulation steps
            for _ in range(n_steps_per_frame):
                simulator.step()

            # Get current state
            state = simulator.get_state()

            # Filter active droplets
            active_mask = state['active'] > 0
            n_active = np.sum(active_mask)

            # Check if done
            if n_active == 0:
                print(f"All droplets deposited at t={simulator.current_time:.1f}s")
                break

            # Update text
            sim_time = state['time']
            info_text = (
                f"Time: {sim_time:.1f}s\n"
                f"Active: {n_active} / {simulator.num_droplets}\n"
                f"Deposited: {simulator.num_droplets - n_active}\n"
                f"Wind: {wind_speed:.1f} m/s East"
            )
            text_actor.SetText(0, info_text)

            # Update active droplets
            if n_active > 0:
                active_positions = state['positions'][active_mask]
                active_diameters = state['diameters'][active_mask] * 1e6

                points = pv.PolyData(active_positions)
                points['diameter_um'] = active_diameters

                plotter.remove_actor(particle_actor)
                particle_actor = plotter.add_mesh(
                    points,
                    scalars='diameter_um',
                    cmap='plasma',
                    point_size=15,
                    render_points_as_spheres=True,
                    show_scalar_bar=True,
                    clim=[100, 400],
                    opacity=0.8,
                    scalar_bar_args={'title': 'Droplet Diameter (μm)'}
                )

            # Update deposited droplets
            deposition_mask = (state['active'] == 0) & (state['deposition_time'] > 0)
            if np.any(deposition_mask):
                new_deposited = state['deposition_position'][deposition_mask]
                if len(new_deposited) > 0:
                    deposited_points_list.append(new_deposited)
                    all_deposited = np.vstack(deposited_points_list)

                    if deposition_actor is not None:
                        plotter.remove_actor(deposition_actor)

                    dep_cloud = pv.PolyData(all_deposited)
                    deposition_actor = plotter.add_mesh(
                        dep_cloud,
                        color='yellow',
                        point_size=8,
                        render_points_as_spheres=True,
                        opacity=0.6
                    )

            # Write frame
            plotter.write_frame()
            frame_count += 1

            # Progress
            if frame_count % 10 == 0:
                print(f"  Frame {frame_count}: t={sim_time:.1f}s | Active: {n_active}")

        # Final statistics
        elapsed = time.time() - start_time
        print(f"\nRecording complete!")
        print(f"Total frames: {frame_count}")
        print(f"Recording time: {elapsed:.1f}s")
        print(f"Video duration: {frame_count / fps:.1f}s")

    finally:
        plotter.close()

    # Show file info
    video_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\nVideo saved: {output_file.absolute()}")
    print(f"File size: {video_size_mb:.2f} MB")
    print(f"Resolution: 1920x1080")
    print(f"Framerate: {fps} FPS")
    print("\nDone!")


if __name__ == "__main__":
    # Generate video with default settings
    save_video(
        output_path="output/spray_drift.mp4",
        fps=10,
        num_droplets=2000,
        wind_speed=3.0,
        simulation_time=12.0
    )

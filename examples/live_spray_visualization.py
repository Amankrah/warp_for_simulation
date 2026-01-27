"""
Live Real-Time Spray Drift Visualization

Shows droplets falling and drifting in real-time 3D animation using PyVista.
Press 'q' to quit the animation.

Usage:
    python live_spray_visualization.py              # Live view only
    python live_spray_visualization.py --save       # Save video to output/spray_animation.mp4
    python live_spray_visualization.py --save --output myvideo.mp4
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import time
import argparse
import pyvista as pv
from agridrift import SprayConfig, WindConfig, SimulationConfig, DropletSimulator


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Live spray drift visualization with optional video recording')
    parser.add_argument('--save', action='store_true', help='Save animation as video file')
    parser.add_argument('--output', type=str, default='output/spray_animation.mp4',
                        help='Output video filename (default: output/spray_animation.mp4)')
    parser.add_argument('--fps', type=int, default=10,
                        help='Target frames per second for video (default: 10)')
    args = parser.parse_args()

    print("=" * 60)
    print("AGRIDRIFT - Live Spray Drift Visualization")
    print("=" * 60)
    print()

    if args.save:
        print("VIDEO RECORDING MODE")
        print(f"  Output file: {args.output}")
        print(f"  Target FPS: {args.fps}")
        print()

    print("Controls:")
    print("  - Rotate: Left mouse button + drag")
    print("  - Zoom: Mouse wheel")
    print("  - Pan: Middle mouse button + drag")
    print("  - Quit: Press 'q' or close window")
    print()

    # Configuration - optimized for visualization
    spray_config = SprayConfig(
        nozzle_height=2.0,
        nozzle_position=(0.0, 0.0),
        spray_angle=30.0,
        num_droplets=2000,              # Reduced for smooth animation
        droplet_diameter_mean=250e-6,
        droplet_diameter_std=75e-6,
        initial_velocity=5.0,
        concentration=2.0
    )

    wind_config = WindConfig(
        wind_speed=3.0,
        wind_direction=90.0,
        reference_height=10.0,
        turbulence_intensity=0.2,
        gust_amplitude=0.5,
        gust_period=10.0
    )

    sim_config = SimulationConfig(
        dt=0.02,                        # 20ms for smooth animation
        total_time=30.0,
        output_interval=0.1,            # Update display every 0.1s
        domain_x=(-5.0, 20.0),
        domain_y=(-10.0, 10.0),
        domain_z=(0.0, 8.0),
        enable_evaporation=True,
        temperature=293.15,
        relative_humidity=0.6,
        device="cuda:0"
    )

    print("Configuration:")
    print(f"  Droplets: {spray_config.num_droplets}")
    print(f"  Wind speed: {wind_config.wind_speed} m/s")
    print(f"  Visualization update: {sim_config.output_interval}s")
    print()

    # Initialize simulator
    print("Initializing simulator...")
    simulator = DropletSimulator(spray_config, wind_config, sim_config)
    print(f"Initialized {simulator.num_droplets} droplets")
    print()

    # Setup output directory if saving
    if args.save:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Video will be saved to: {output_path.absolute()}")
        print()

    # Setup PyVista plotter for live rendering
    plotter = pv.Plotter(window_size=(1400, 900), off_screen=args.save)
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
        font_size=10,
        color='black'
    )

    # Camera position
    plotter.camera_position = [
        (12, -15, 8),   # Camera position
        (7, 0, 1),      # Focal point
        (0, 0, 1)       # View up
    ]

    # Initial empty point cloud
    points = pv.PolyData(np.array([[0, 0, 0]]))
    points['diameter_um'] = np.array([250.0])

    particle_actor = plotter.add_mesh(
        points,
        scalars='diameter_um',
        cmap='plasma',
        point_size=12,
        render_points_as_spheres=True,
        show_scalar_bar=True,
        clim=[100, 400],
        opacity=0.8
    )

    # Deposition points (accumulated)
    deposited_points_list = []
    deposition_actor = None

    # Animation parameters
    n_steps_per_frame = int(sim_config.output_interval / sim_config.dt)
    frame_count = 0
    start_time = time.time()

    # Video recording setup
    if args.save:
        plotter.open_movie(str(args.output), framerate=args.fps, quality=9)
        print(f"Recording started...")
        print(f"Capturing frames at {args.fps} FPS\n")
    else:
        print("Starting live visualization...")
        print("(Close window or press 'q' to stop)\n")

    # Show initial frame (only if not saving)
    if not args.save:
        plotter.show(interactive_update=True, auto_close=False)

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
                print(f"\nAll droplets deposited at t={simulator.current_time:.1f}s")
                break

            # Update statistics
            elapsed = time.time() - start_time
            sim_time = state['time']

            # Update text display
            info_text = (
                f"Time: {sim_time:.1f}s / {sim_config.total_time:.0f}s\n"
                f"Active Droplets: {n_active} / {simulator.num_droplets}\n"
                f"Deposited: {simulator.num_droplets - n_active}\n"
                f"Wind: {wind_config.wind_speed:.1f} m/s East\n"
                f"FPS: {frame_count/(elapsed+0.001):.1f}"
            )
            text_actor.SetText(0, info_text)

            # Update active droplets
            if n_active > 0:
                active_positions = state['positions'][active_mask]
                active_diameters = state['diameters'][active_mask] * 1e6  # to microns

                # Create new point cloud
                points = pv.PolyData(active_positions)
                points['diameter_um'] = active_diameters

                # Update mesh
                plotter.remove_actor(particle_actor)
                particle_actor = plotter.add_mesh(
                    points,
                    scalars='diameter_um',
                    cmap='plasma',
                    point_size=12,
                    render_points_as_spheres=True,
                    show_scalar_bar=True,
                    clim=[100, 400],
                    opacity=0.8,
                    scalar_bar_args={'title': 'Droplet Diameter (μm)'}
                )

            # Update deposited droplets (show as ground markers)
            deposition_mask = (state['active'] == 0) & (state['deposition_time'] > 0)
            if np.any(deposition_mask):
                new_deposited = state['deposition_position'][deposition_mask]
                if len(new_deposited) > 0:
                    deposited_points_list.append(new_deposited)

                    # Combine all deposited points
                    all_deposited = np.vstack(deposited_points_list)

                    # Remove old deposition actor
                    if deposition_actor is not None:
                        plotter.remove_actor(deposition_actor)

                    # Add new one
                    dep_cloud = pv.PolyData(all_deposited)
                    deposition_actor = plotter.add_mesh(
                        dep_cloud,
                        color='yellow',
                        point_size=6,
                        render_points_as_spheres=True,
                        opacity=0.6
                    )

            # Update display
            if args.save:
                # Write frame to video
                plotter.write_frame()
            else:
                # Update live display
                plotter.update()

            frame_count += 1

            # Print progress
            if frame_count % 10 == 0:
                if args.save:
                    print(f"  t={sim_time:.1f}s | Active: {n_active} | Frames: {frame_count}")
                else:
                    print(f"  t={sim_time:.1f}s | Active: {n_active} | FPS: {frame_count/(elapsed+0.001):.1f}")

        # Final statistics
        elapsed = time.time() - start_time
        print(f"\nSimulation complete!")
        print(f"Total frames rendered: {frame_count}")

        if args.save:
            print(f"Video recording time: {elapsed:.1f}s")
            print(f"Video duration: {frame_count / args.fps:.1f}s")
        else:
            print(f"Average FPS: {frame_count/elapsed:.1f}")
            print(f"Total time: {elapsed:.1f}s")

        # Finalize video or show final frame
        if args.save:
            print("\nFinalizing video file...")
            plotter.close()
            print(f"Video saved successfully to: {Path(args.output).absolute()}")

            # Show file size
            video_size_mb = Path(args.output).stat().st_size / (1024 * 1024)
            print(f"File size: {video_size_mb:.2f} MB")
        else:
            # Keep window open to view final result
            print("\nFinal view displayed. Close window to exit.")
            plotter.show()
            plotter.close()

    except KeyboardInterrupt:
        print("\nVisualization interrupted by user")
        if args.save:
            print("Closing video file...")
            plotter.close()
    finally:
        if not args.save:
            plotter.close()

    print("\nDone!")


if __name__ == "__main__":
    main()

"""
Save Air Classifier Video

Creates a 3D animation video of the air classifier simulation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pyvista as pv
from air_classifier import (
    ClassifierConfig,
    ParticleProperties,
    SimulationConfig,
    AirClassifierSimulator
)


def save_classifier_video(
    output_path: str = "output/air_classifier.mp4",
    fps: int = 15,
    num_particles: int = 5000,
    simulation_time: float = 2.0,
    rpm: float = 3500
):
    """
    Generate and save air classifier animation as video

    Args:
        output_path: Output video file path
        fps: Frames per second
        num_particles: Number of particles to simulate
        simulation_time: Total simulation time (seconds)
        rpm: Classifier wheel RPM
    """

    print("=" * 70)
    print("AIR CLASSIFIER - Video Recording")
    print("=" * 70)
    print()
    print(f"Output: {output_path}")
    print(f"FPS: {fps}")
    print(f"Particles: {num_particles}")
    print(f"Wheel RPM: {rpm}")
    print()

    # Create output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Configuration
    classifier_config = ClassifierConfig(
        wheel_rpm=rpm,
        num_particles=num_particles
    )
    particle_props = ParticleProperties()
    sim_config = SimulationConfig(
        total_time=simulation_time,
        output_interval=1.0 / fps  # Frame rate matches output
    )

    # Initialize simulator
    print("Initializing simulator...")
    simulator = AirClassifierSimulator(
        classifier_config,
        particle_props,
        sim_config
    )
    print(f"Initialized {num_particles} particles")
    print()

    # Setup plotter (off-screen for video recording)
    plotter = pv.Plotter(window_size=(1920, 1080), off_screen=True)
    plotter.set_background('white')

    # Create chamber (cylinder)
    chamber = pv.Cylinder(
        center=(0, 0, classifier_config.chamber_height/2),
        direction=(0, 0, 1),
        radius=classifier_config.chamber_radius,
        height=classifier_config.chamber_height,
        resolution=50
    )
    plotter.add_mesh(chamber, color='lightgray', opacity=0.15, show_edges=False)

    # Add ground
    ground = pv.Disc(
        center=(0, 0, 0),
        inner=0,
        outer=classifier_config.chamber_radius,
        normal=(0, 0, 1),
        r_res=1,
        c_res=50
    )
    plotter.add_mesh(ground, color='green', opacity=0.3)

    # Add classifier wheel
    wheel = pv.Cylinder(
        center=(0, 0, classifier_config.wheel_position_z),
        direction=(0, 0, 1),
        radius=classifier_config.wheel_radius,
        height=classifier_config.wheel_width,
        resolution=50
    )
    plotter.add_mesh(wheel, color='red', opacity=0.4, show_edges=True)

    # Add wheel blades (simplified)
    n_blades = 8  # Reduced for visualization
    for i in range(n_blades):
        angle = i * 2 * np.pi / n_blades
        x = classifier_config.wheel_radius * 0.7 * np.cos(angle)
        y = classifier_config.wheel_radius * 0.7 * np.sin(angle)

        blade = pv.Box(
            bounds=[
                x - 0.01, x + 0.01,
                y - 0.01, y + 0.01,
                classifier_config.wheel_position_z - classifier_config.wheel_width/2,
                classifier_config.wheel_position_z + classifier_config.wheel_width/2
            ]
        )
        plotter.add_mesh(blade, color='darkred', opacity=0.6)

    # Add text display
    text_actor = plotter.add_text(
        "Initializing...",
        position='upper_left',
        font_size=14,
        color='black'
    )

    # Camera position (side view with slight angle)
    plotter.camera_position = [
        (classifier_config.chamber_radius * 3, -classifier_config.chamber_radius * 2.5,
         classifier_config.chamber_height * 0.8),
        (0, 0, classifier_config.chamber_height * 0.5),
        (0, 0, 1)
    ]

    # Initial point cloud
    points = pv.PolyData(np.array([[0, 0, classifier_config.chamber_height/2]]))
    points['diameter_um'] = np.array([10.0])

    particle_actor = plotter.add_mesh(
        points,
        scalars='diameter_um',
        cmap='coolwarm',
        point_size=8,
        render_points_as_spheres=True,
        show_scalar_bar=True,
        clim=[0, 50],
        opacity=0.9,
        scalar_bar_args={'title': 'Diameter (μm)', 'vertical': True}
    )

    # Deposition tracking
    collected_fine_positions = []
    collected_coarse_positions = []
    fine_actor = None
    coarse_actor = None

    # Open video file
    plotter.open_movie(str(output_file), framerate=fps, quality=9)
    print("Recording...")

    frame_count = 0
    n_steps_per_frame = max(1, int(sim_config.output_interval / classifier_config.dt))

    try:
        # Animation loop
        while simulator.current_time < sim_config.total_time:
            # Run simulation steps
            for _ in range(n_steps_per_frame):
                simulator.step()

            # Get current state
            state = simulator.get_state()
            active_mask = state['active'] > 0
            n_active = np.sum(active_mask)

            # Check if done
            if n_active == 0:
                print(f"All particles collected at t={simulator.current_time:.2f}s")
                break

            # Update text
            info_text = (
                f"Time: {state['time']:.2f}s\n"
                f"RPM: {rpm:.0f}\n"
                f"Active: {n_active:,}\n"
                f"Fine: {state['collected_fine']:,}\n"
                f"Coarse: {state['collected_coarse']:,}"
            )
            text_actor.SetText(0, info_text)

            # Update active particles
            if n_active > 0:
                active_positions = state['positions'][active_mask]
                active_diameters = state['diameters'][active_mask] * 1e6
                active_types = state['particle_types'][active_mask]

                # Color by particle type (blue=protein, orange=starch)
                colors = np.where(active_types == 0, active_diameters * 0 + 5,
                                 active_diameters * 0 + 35)

                points = pv.PolyData(active_positions)
                points['diameter_um'] = colors

                plotter.remove_actor(particle_actor)
                particle_actor = plotter.add_mesh(
                    points,
                    scalars='diameter_um',
                    cmap='coolwarm',
                    point_size=8,
                    render_points_as_spheres=True,
                    show_scalar_bar=True,
                    clim=[0, 50],
                    opacity=0.9,
                    scalar_bar_args={'title': 'Protein←→Starch', 'vertical': True}
                )

            # Track collected particles
            collection_pos = state['collection_position']
            collection_times = state['collection_time']
            newly_collected = (collection_times > 0) & (state['active'] == 0)

            if np.any(newly_collected):
                new_positions = collection_pos[newly_collected]
                # Separate by height (rough estimate)
                fine_mask_new = new_positions[:, 2] > 0.5
                coarse_mask_new = new_positions[:, 2] <= 0.1

                if np.any(fine_mask_new):
                    collected_fine_positions.append(new_positions[fine_mask_new])

                if np.any(coarse_mask_new):
                    collected_coarse_positions.append(new_positions[coarse_mask_new])

            # Draw collected particles
            if len(collected_fine_positions) > 0:
                if fine_actor is not None:
                    plotter.remove_actor(fine_actor)

                all_fine = np.vstack(collected_fine_positions)
                fine_cloud = pv.PolyData(all_fine)
                fine_actor = plotter.add_mesh(
                    fine_cloud,
                    color='blue',
                    point_size=4,
                    render_points_as_spheres=True,
                    opacity=0.4
                )

            if len(collected_coarse_positions) > 0:
                if coarse_actor is not None:
                    plotter.remove_actor(coarse_actor)

                all_coarse = np.vstack(collected_coarse_positions)
                coarse_cloud = pv.PolyData(all_coarse)
                coarse_actor = plotter.add_mesh(
                    coarse_cloud,
                    color='orange',
                    point_size=4,
                    render_points_as_spheres=True,
                    opacity=0.3
                )

            # Write frame
            plotter.write_frame()
            frame_count += 1

            # Progress
            if frame_count % 10 == 0:
                print(f"  Frame {frame_count}: t={state['time']:.2f}s | Active: {n_active:,}")

        print(f"\nRecording complete!")
        print(f"Total frames: {frame_count}")
        print(f"Video duration: {frame_count / fps:.1f}s")

    finally:
        plotter.close()

    # Show file info
    if output_file.exists():
        video_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\nVideo saved: {output_file.absolute()}")
        print(f"File size: {video_size_mb:.2f} MB")
        print(f"Resolution: 1920x1080")
        print(f"Framerate: {fps} FPS")
    else:
        print("\nWarning: Video file was not created")

    print("\nDone!")


if __name__ == "__main__":
    # Generate video with default settings
    save_classifier_video(
        output_path="output/air_classifier.mp4",
        fps=15,
        num_particles=5000,
        simulation_time=2.0,
        rpm=3500
    )

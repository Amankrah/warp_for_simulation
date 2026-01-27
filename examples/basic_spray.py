"""
Basic Spray Drift Example

Simulates a simple agricultural spray application with moderate wind conditions.
Good starting point for understanding AgriDrift.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import time
from agridrift import SprayConfig, WindConfig, SimulationConfig, DropletSimulator
from agridrift.visualization import (
    SprayVisualizer,
    plot_trajectory_2d,
    plot_deposition_heatmap,
    plot_drift_statistics
)
from agridrift.analysis import DriftAnalyzer


def main():
    print("=" * 60)
    print("AGRIDRIFT - Basic Spray Drift Simulation")
    print("=" * 60)
    print()

    # Configuration
    spray_config = SprayConfig(
        nozzle_height=2.0,              # 2m spray height
        nozzle_position=(0.0, 0.0),
        spray_angle=30.0,               # 30 degree cone
        num_droplets=5000,              # 5000 droplets
        droplet_diameter_mean=250e-6,   # 250 micron mean
        droplet_diameter_std=75e-6,
        initial_velocity=5.0,           # 5 m/s initial velocity
        concentration=2.0               # 2 g/L active ingredient
    )

    wind_config = WindConfig(
        wind_speed=3.0,                 # 3 m/s wind (moderate)
        wind_direction=90.0,            # Eastward wind
        reference_height=10.0,
        turbulence_intensity=0.2,
        gust_amplitude=0.5,
        gust_period=10.0
    )

    sim_config = SimulationConfig(
        dt=0.01,                        # 10ms time step
        total_time=30.0,                # 30 second simulation
        output_interval=0.5,            # Output every 0.5s
        domain_x=(-5.0, 20.0),
        domain_y=(-10.0, 10.0),
        domain_z=(0.0, 8.0),
        enable_evaporation=True,
        temperature=293.15,             # 20°C
        relative_humidity=0.6,          # 60% RH
        device="cuda:0"
    )

    print("Configuration:")
    print(f"  Droplets: {spray_config.num_droplets}")
    print(f"  Mean diameter: {spray_config.droplet_diameter_mean*1e6:.0f} μm")
    print(f"  Wind speed: {wind_config.wind_speed} m/s")
    print(f"  Temperature: {sim_config.temperature-273.15:.1f} °C")
    print(f"  Simulation time: {sim_config.total_time} s")
    print()

    # Initialize simulator
    print("Initializing simulator...")
    simulator = DropletSimulator(spray_config, wind_config, sim_config)
    print(f"Initialized {simulator.num_droplets} droplets on {sim_config.device}")
    print()

    # Run simulation
    print("Running simulation...")
    start_time = time.time()

    state_history = []
    time_points = []

    n_steps = int(sim_config.total_time / sim_config.dt)
    output_every = int(sim_config.output_interval / sim_config.dt)

    for step in range(n_steps):
        simulator.step()

        # Save output
        if step % output_every == 0:
            state = simulator.get_state()
            state_history.append(state)
            time_points.append(state['time'])

            n_active = simulator.get_active_count()
            progress = (step / n_steps) * 100

            print(f"  Step {step}/{n_steps} ({progress:.1f}%) | "
                  f"Time: {state['time']:.1f}s | "
                  f"Active: {n_active}/{simulator.num_droplets}")

    elapsed = time.time() - start_time
    print(f"\nSimulation complete in {elapsed:.2f}s")
    print(f"Performance: {n_steps/elapsed:.0f} steps/second")
    print()

    # Final state
    final_state = simulator.get_state()

    # Analysis
    print("Analyzing results...")
    analyzer = DriftAnalyzer(
        nozzle_position=(
            spray_config.nozzle_position[0],
            spray_config.nozzle_position[1],
            spray_config.nozzle_height
        )
    )

    # Deposition mask (deposited on ground, not lost)
    deposition_mask = (final_state['active'] == 0) & (final_state['deposition_time'] > 0)

    # Deposition statistics
    dep_stats = analyzer.analyze_deposition(
        final_state['deposition_position'],
        deposition_mask,
        final_state['diameters'],
        final_state['masses'],
        spray_config.concentration
    )

    # Loss statistics
    loss_stats = analyzer.analyze_loss(
        final_state['deposition_time'],
        final_state['active'],
        final_state['masses']
    )

    # Coverage efficiency (target: 0-10m downwind, ±5m crosswind)
    coverage_stats = analyzer.compute_coverage_efficiency(
        final_state['deposition_position'],
        deposition_mask,
        target_area=(0.0, 10.0, -5.0, 5.0)
    )

    # Print report
    report = analyzer.generate_report(
        final_state,
        dep_stats,
        loss_stats,
        coverage_stats,
        save_path="output/basic_spray_report.txt"
    )
    print(report)

    # Export data
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    analyzer.export_to_csv(final_state, "output/basic_spray_data.csv")

    # Visualizations
    print("\nGenerating visualizations...")

    # 1. 3D visualization
    print("  Creating 3D view...")
    viz = SprayVisualizer(
        nozzle_position=(
            spray_config.nozzle_position[0],
            spray_config.nozzle_position[1],
            spray_config.nozzle_height
        ),
        domain_x=sim_config.domain_x,
        domain_y=sim_config.domain_y,
        ground_level=sim_config.ground_level,
        interactive=False  # Set to True for interactive viewing
    )

    # Show final state
    viz.update_droplets(
        final_state['positions'],
        final_state['active'],
        final_state['diameters']
    )

    # Add deposition pattern
    viz.add_deposition_pattern(
        final_state['deposition_position'],
        deposition_mask
    )

    viz.screenshot("output/basic_spray_3d.png")
    viz.close()

    # 2. 2D trajectory plot
    print("  Creating trajectory plot...")
    positions_history = [s['positions'] for s in state_history]
    active_history = [s['active'] for s in state_history]

    plot_trajectory_2d(
        positions_history,
        active_history,
        final_state['deposition_position'],
        deposition_mask,
        (spray_config.nozzle_position[0], spray_config.nozzle_position[1], spray_config.nozzle_height),
        sim_config.domain_x,
        sim_config.domain_z,
        save_path="output/basic_spray_trajectory.png"
    )

    # 3. Deposition heatmap
    print("  Creating deposition heatmap...")
    plot_deposition_heatmap(
        final_state['deposition_position'],
        deposition_mask,
        sim_config.domain_x,
        sim_config.domain_y,
        spray_config.nozzle_position,
        resolution=50,
        save_path="output/basic_spray_heatmap.png"
    )

    # 4. Time series statistics
    print("  Creating statistics plot...")
    plot_drift_statistics(
        state_history,
        np.array(time_points),
        save_path="output/basic_spray_statistics.png"
    )

    print("\nAll visualizations saved to output/")
    print("\nDone!")


if __name__ == "__main__":
    main()

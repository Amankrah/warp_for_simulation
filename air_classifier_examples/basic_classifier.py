"""
Basic Air Classifier Simulation Example

Demonstrates basic usage of the air classifier simulator
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from air_classifier import (
    AirClassifierSimulator,
    get_default_config,
    analyze_separation,
    print_separation_report,
    plot_particle_trajectories,
    plot_size_distributions,
    plot_collection_dynamics
)


def main():
    """Run basic air classifier simulation"""

    print("=" * 70)
    print("AIR CLASSIFIER SIMULATION - Basic Example")
    print("Yellow Pea Protein Separation")
    print("=" * 70)
    print()

    # Get default configuration
    classifier_config, particle_props, sim_config = get_default_config()

    # Modify for faster demo
    classifier_config.num_particles = 10000
    sim_config.total_time = 1.5
    sim_config.output_interval = 0.05

    print("Configuration:")
    print(f"  Particles: {classifier_config.num_particles:,}")
    print(f"  Wheel RPM: {classifier_config.wheel_rpm}")
    print(f"  Air velocity: {classifier_config.air_velocity} m/s")
    print(f"  Target cut size: {particle_props.target_cut_size*1e6:.1f} μm")
    print(f"  Simulation time: {sim_config.total_time}s")
    print()

    # Create simulator
    simulator = AirClassifierSimulator(
        classifier_config,
        particle_props,
        sim_config
    )

    # Run simulation
    results = simulator.run()

    # Analyze results
    print("\n" + "=" * 70)
    print("ANALYZING RESULTS")
    print("=" * 70)

    particle_types = simulator.particle_types.numpy()
    analysis = analyze_separation(results, particle_types)

    # Print report
    print_separation_report(analysis)

    # Plot results
    print("Generating plots...")

    # Collection dynamics
    plot_collection_dynamics(results, save_path="output/classifier_dynamics.png")

    # Particle trajectories
    plot_particle_trajectories(
        results,
        particle_types,
        classifier_config,
        max_particles=1000,
        save_path="output/classifier_trajectories.png"
    )

    # Size distributions
    plot_size_distributions(
        results['final_state'],
        particle_types,
        save_path="output/classifier_size_distributions.png"
    )

    print("\nSimulation complete!")
    print("Output files saved to 'output/' directory")


if __name__ == "__main__":
    main()

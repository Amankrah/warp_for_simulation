"""
Parameter Study Example

Demonstrates how to run parameter studies to optimize classifier performance
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt
from air_classifier import (
    ClassifierConfig,
    ParticleProperties,
    SimulationConfig,
    AirClassifierSimulator,
    analyze_separation
)


def run_rpm_study():
    """Study effect of wheel RPM on separation performance"""

    print("=" * 70)
    print("PARAMETER STUDY: Wheel RPM Effect on Separation")
    print("=" * 70)
    print()

    # RPM values to test
    rpm_values = [2500, 3000, 3500, 4000, 4500]

    results_list = []

    for rpm in rpm_values:
        print(f"\nRunning simulation at {rpm} RPM...")

        # Create configuration
        classifier_config = ClassifierConfig(
            wheel_rpm=rpm,
            num_particles=5000  # Reduced for speed
        )
        particle_props = ParticleProperties()
        sim_config = SimulationConfig(
            total_time=1.0,
            output_interval=0.1
        )

        # Run simulation
        simulator = AirClassifierSimulator(
            classifier_config,
            particle_props,
            sim_config
        )
        sim_results = simulator.run()

        # Analyze
        particle_types = simulator.particle_types.numpy()
        analysis = analyze_separation(sim_results, particle_types)

        results_list.append({
            'rpm': rpm,
            'protein_purity': analysis['protein_purity_fine'],
            'protein_recovery': analysis['protein_recovery'],
            'fine_yield': analysis['fine_yield'],
            'd50': analysis['d50_estimate']
        })

        print(f"  Protein purity: {analysis['protein_purity_fine']:.1f}%")
        print(f"  Protein recovery: {analysis['protein_recovery']:.1f}%")
        print(f"  d50: {analysis['d50_estimate']:.1f} μm")

    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    rpm_array = [r['rpm'] for r in results_list]

    # Protein purity
    axes[0, 0].plot(rpm_array, [r['protein_purity'] for r in results_list],
                    'bo-', linewidth=2, markersize=8)
    axes[0, 0].set_xlabel('Wheel RPM')
    axes[0, 0].set_ylabel('Protein Purity (%)')
    axes[0, 0].set_title('Effect of RPM on Protein Purity')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=58, color='red', linestyle='--', alpha=0.5, label='Target')
    axes[0, 0].legend()

    # Protein recovery
    axes[0, 1].plot(rpm_array, [r['protein_recovery'] for r in results_list],
                    'go-', linewidth=2, markersize=8)
    axes[0, 1].set_xlabel('Wheel RPM')
    axes[0, 1].set_ylabel('Protein Recovery (%)')
    axes[0, 1].set_title('Effect of RPM on Protein Recovery')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Target')
    axes[0, 1].legend()

    # Fine yield
    axes[1, 0].plot(rpm_array, [r['fine_yield'] for r in results_list],
                    'mo-', linewidth=2, markersize=8)
    axes[1, 0].set_xlabel('Wheel RPM')
    axes[1, 0].set_ylabel('Fine Yield (%)')
    axes[1, 0].set_title('Effect of RPM on Fine Fraction Yield')
    axes[1, 0].grid(True, alpha=0.3)

    # Cut size
    axes[1, 1].plot(rpm_array, [r['d50'] for r in results_list],
                    'ro-', linewidth=2, markersize=8)
    axes[1, 1].set_xlabel('Wheel RPM')
    axes[1, 1].set_ylabel('Cut Size d50 (μm)')
    axes[1, 1].set_title('Effect of RPM on Cut Size')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=20, color='green', linestyle='--', alpha=0.5, label='Target')
    axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig('output/rpm_parameter_study.png', dpi=150, bbox_inches='tight')
    print("\n\nParameter study plot saved to 'output/rpm_parameter_study.png'")
    plt.show()


def run_air_velocity_study():
    """Study effect of air velocity on separation"""

    print("\n" + "=" * 70)
    print("PARAMETER STUDY: Air Velocity Effect on Separation")
    print("=" * 70)
    print()

    air_velocities = [6.0, 7.0, 8.0, 9.0, 10.0]
    results_list = []

    for air_vel in air_velocities:
        print(f"\nRunning simulation at {air_vel} m/s air velocity...")

        classifier_config = ClassifierConfig(
            air_velocity=air_vel,
            num_particles=5000
        )
        particle_props = ParticleProperties()
        sim_config = SimulationConfig(
            total_time=1.0,
            output_interval=0.1
        )

        simulator = AirClassifierSimulator(
            classifier_config,
            particle_props,
            sim_config
        )
        sim_results = simulator.run()

        particle_types = simulator.particle_types.numpy()
        analysis = analyze_separation(sim_results, particle_types)

        results_list.append({
            'air_velocity': air_vel,
            'protein_purity': analysis['protein_purity_fine'],
            'protein_recovery': analysis['protein_recovery'],
            'fine_yield': analysis['fine_yield']
        })

        print(f"  Protein purity: {analysis['protein_purity_fine']:.1f}%")
        print(f"  Fine yield: {analysis['fine_yield']:.1f}%")

    # Simple bar plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    air_vel_array = [r['air_velocity'] for r in results_list]
    x = np.arange(len(air_vel_array))
    width = 0.25

    ax.bar(x - width, [r['protein_purity'] for r in results_list],
           width, label='Protein Purity (%)', color='blue', alpha=0.7)
    ax.bar(x, [r['protein_recovery'] for r in results_list],
           width, label='Protein Recovery (%)', color='green', alpha=0.7)
    ax.bar(x + width, [r['fine_yield'] for r in results_list],
           width, label='Fine Yield (%)', color='orange', alpha=0.7)

    ax.set_xlabel('Air Velocity (m/s)')
    ax.set_ylabel('Percentage (%)')
    ax.set_title('Effect of Air Velocity on Separation Performance')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{v}' for v in air_vel_array])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('output/air_velocity_study.png', dpi=150, bbox_inches='tight')
    print("\n\nAir velocity study plot saved to 'output/air_velocity_study.png'")
    plt.show()


if __name__ == "__main__":
    # Run studies
    run_rpm_study()
    run_air_velocity_study()

    print("\n" + "=" * 70)
    print("Parameter studies complete!")
    print("=" * 70)

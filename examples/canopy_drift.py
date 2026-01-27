"""
Canopy Drift Example

Simulates spray drift with crop canopy interception.
Demonstrates how vegetation affects deposition patterns.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import time
from agridrift import SprayConfig, WindConfig, SimulationConfig, DropletSimulator
from agridrift.visualization import (
    SprayVisualizer,
    plot_deposition_heatmap,
    plot_drift_statistics
)
from agridrift.analysis import DriftAnalyzer


def run_scenario(scenario_name: str, canopy_height: float, wind_speed: float):
    """Run a spray drift scenario with specified parameters"""

    print(f"\n{'='*60}")
    print(f"Scenario: {scenario_name}")
    print(f"{'='*60}")

    # Configuration
    spray_config = SprayConfig(
        nozzle_height=3.0,              # 3m spray height (above canopy)
        nozzle_position=(0.0, 0.0),
        spray_angle=25.0,
        num_droplets=3000,
        droplet_diameter_mean=300e-6,   # Larger droplets
        droplet_diameter_std=80e-6,
        initial_velocity=4.0,
        concentration=1.5
    )

    wind_config = WindConfig(
        wind_speed=wind_speed,
        wind_direction=90.0,
        reference_height=10.0,
        turbulence_intensity=0.25,      # Higher turbulence
        gust_amplitude=1.0,
        gust_period=8.0
    )

    sim_config = SimulationConfig(
        dt=0.01,
        total_time=25.0,
        output_interval=0.5,
        domain_x=(-5.0, 25.0),
        domain_y=(-12.0, 12.0),
        domain_z=(0.0, 10.0),
        canopy_height=canopy_height,    # Crop canopy
        canopy_density=2.0,             # Leaf area density
        enable_evaporation=True,
        temperature=298.15,             # Warmer: 25°C
        relative_humidity=0.5,          # Drier: 50% RH
        device="cuda:0"
    )

    print(f"  Canopy height: {canopy_height} m")
    print(f"  Wind speed: {wind_speed} m/s")
    print(f"  Droplets: {spray_config.num_droplets}")

    # Initialize and run
    simulator = DropletSimulator(spray_config, wind_config, sim_config)

    state_history = []
    time_points = []

    n_steps = int(sim_config.total_time / sim_config.dt)
    output_every = int(sim_config.output_interval / sim_config.dt)

    print("  Running simulation...", end=" ", flush=True)
    start_time = time.time()

    for step in range(n_steps):
        simulator.step()
        if step % output_every == 0:
            state_history.append(simulator.get_state())
            time_points.append(simulator.current_time)

    elapsed = time.time() - start_time
    print(f"done in {elapsed:.2f}s")

    # Analysis
    final_state = simulator.get_state()
    deposition_mask = (final_state['active'] == 0) & (final_state['deposition_time'] > 0)

    analyzer = DriftAnalyzer(
        nozzle_position=(
            spray_config.nozzle_position[0],
            spray_config.nozzle_position[1],
            spray_config.nozzle_height
        )
    )

    dep_stats = analyzer.analyze_deposition(
        final_state['deposition_position'],
        deposition_mask,
        final_state['diameters'],
        final_state['masses'],
        spray_config.concentration
    )

    loss_stats = analyzer.analyze_loss(
        final_state['deposition_time'],
        final_state['active'],
        final_state['masses']
    )

    # Print summary
    print(f"  Deposited: {dep_stats['total_deposited']} ({dep_stats['deposition_fraction']:.1%})")
    print(f"  Mean drift: {dep_stats['mean_drift_distance']:.2f} m")
    print(f"  Max drift: {dep_stats['max_drift_distance']:.2f} m")
    print(f"  Lost to drift: {loss_stats['fraction_drift_lost']:.1%}")

    return final_state, state_history, time_points, deposition_mask, dep_stats, analyzer


def main():
    print("=" * 60)
    print("AGRIDRIFT - Canopy Interception Study")
    print("=" * 60)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Run multiple scenarios
    scenarios = [
        ("Bare Soil - Low Wind", 0.0, 2.0),
        ("Short Crop - Low Wind", 0.5, 2.0),
        ("Tall Crop - Low Wind", 1.5, 2.0),
        ("Tall Crop - High Wind", 1.5, 5.0),
    ]

    results = []

    for name, canopy_height, wind_speed in scenarios:
        result = run_scenario(name, canopy_height, wind_speed)
        results.append((name, *result))

    # Comparative visualizations
    print(f"\n{'='*60}")
    print("Generating comparative visualizations...")
    print("=" * 60)

    import matplotlib.pyplot as plt

    # Compare deposition patterns
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    for idx, (name, final_state, _, _, dep_mask, _, _) in enumerate(results):
        ax = axes[idx]

        if np.any(dep_mask):
            dep_pos = final_state['deposition_position'][dep_mask]

            # 2D histogram
            x_edges = np.linspace(-5, 25, 50)
            y_edges = np.linspace(-12, 12, 50)
            H, xedges, yedges = np.histogram2d(
                dep_pos[:, 0],
                dep_pos[:, 1],
                bins=[x_edges, y_edges]
            )

            extent = [-5, 25, -12, 12]
            im = ax.imshow(
                H.T,
                origin='lower',
                extent=extent,
                cmap='YlOrRd',
                aspect='auto'
            )

            plt.colorbar(im, ax=ax, label='Count')

        ax.plot(0, 0, 'b*', markersize=12, label='Nozzle')
        ax.set_xlabel('Downwind (m)')
        ax.set_ylabel('Crosswind (m)')
        ax.set_title(name)
        ax.grid(True, alpha=0.3)
        ax.legend()

    plt.tight_layout()
    plt.savefig("output/canopy_comparison.png", dpi=150)
    print("  Saved: output/canopy_comparison.png")

    # Compare statistics
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    scenario_names = [r[0] for r in results]
    deposition_fractions = [r[5]['deposition_fraction'] for r in results]
    mean_drifts = [r[5]['mean_drift_distance'] for r in results]
    max_drifts = [r[5]['max_drift_distance'] for r in results]
    deposited_masses = [r[5]['deposited_mass_kg'] * 1000 for r in results]  # grams

    x_pos = np.arange(len(scenario_names))

    # Deposition fraction
    axes[0, 0].bar(x_pos, deposition_fractions, color='steelblue')
    axes[0, 0].set_ylabel('Deposition Fraction')
    axes[0, 0].set_title('Deposition Efficiency')
    axes[0, 0].set_xticks(x_pos)
    axes[0, 0].set_xticklabels(scenario_names, rotation=45, ha='right', fontsize=8)
    axes[0, 0].grid(axis='y', alpha=0.3)

    # Mean drift distance
    axes[0, 1].bar(x_pos, mean_drifts, color='coral')
    axes[0, 1].set_ylabel('Mean Drift (m)')
    axes[0, 1].set_title('Average Drift Distance')
    axes[0, 1].set_xticks(x_pos)
    axes[0, 1].set_xticklabels(scenario_names, rotation=45, ha='right', fontsize=8)
    axes[0, 1].grid(axis='y', alpha=0.3)

    # Max drift distance
    axes[1, 0].bar(x_pos, max_drifts, color='mediumseagreen')
    axes[1, 0].set_ylabel('Max Drift (m)')
    axes[1, 0].set_title('Maximum Drift Distance')
    axes[1, 0].set_xticks(x_pos)
    axes[1, 0].set_xticklabels(scenario_names, rotation=45, ha='right', fontsize=8)
    axes[1, 0].grid(axis='y', alpha=0.3)

    # Deposited mass
    axes[1, 1].bar(x_pos, deposited_masses, color='mediumpurple')
    axes[1, 1].set_ylabel('Deposited Mass (g)')
    axes[1, 1].set_title('Total Mass Deposited')
    axes[1, 1].set_xticks(x_pos)
    axes[1, 1].set_xticklabels(scenario_names, rotation=45, ha='right', fontsize=8)
    axes[1, 1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig("output/canopy_statistics.png", dpi=150)
    print("  Saved: output/canopy_statistics.png")

    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Scenario':<25} {'Dep%':>8} {'Mean(m)':>10} {'Max(m)':>10}")
    print("-" * 60)
    for name, _, _, _, _, stats, _ in results:
        print(f"{name:<25} {stats['deposition_fraction']*100:>7.1f}% "
              f"{stats['mean_drift_distance']:>9.2f}m "
              f"{stats['max_drift_distance']:>9.2f}m")
    print("=" * 60)

    print("\nDone! Check the output/ directory for results.")


if __name__ == "__main__":
    main()

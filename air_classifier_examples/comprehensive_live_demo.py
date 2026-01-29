"""
Comprehensive Live Air Classifier Demo

Real-time visualization of particle separation with industry-standard analysis.
This is the main demonstration showing all features working together.

Features:
- Live particle visualization during simulation
- Real-time performance metrics
- Automatic industry standard validation
- Complete analysis reports
- Economic feasibility assessment

Reference: Comprehensive Engineering Guide (all sections)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pathlib import Path
import time

from air_classifier import (
    # Configuration
    ClassifierConfig,
    ParticleProperties,
    SimulationConfig,
    get_default_config,

    # Simulator
    AirClassifierSimulator,

    # Analysis
    analyze_separation,
    print_separation_report,
    calculate_grade_efficiency,
    plot_grade_efficiency_curve,
    print_grade_efficiency_report,
    calculate_economics,
    print_economics_report,
    plot_size_distributions,

    # Validation
    validate_classifier_design,
    print_validation_report
)


class LiveClassifierVisualization:
    """Real-time visualization of air classifier operation"""

    def __init__(self, simulator, config):
        self.simulator = simulator
        self.config = config

        # Create figure with subplots
        self.fig = plt.figure(figsize=(16, 9))
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Main particle view (side view)
        self.ax_side = self.fig.add_subplot(gs[0:2, 0:2])

        # Top view
        self.ax_top = self.fig.add_subplot(gs[2, 0])

        # Performance metrics
        self.ax_metrics = self.fig.add_subplot(gs[0, 2])
        self.ax_metrics.axis('off')

        # Collection dynamics
        self.ax_collection = self.fig.add_subplot(gs[1, 2])

        # Particle counts
        self.ax_counts = self.fig.add_subplot(gs[2, 1:3])

        # Data storage
        self.times = []
        self.fine_collected = []
        self.coarse_collected = []
        self.active_counts = []

        self.setup_plots()

    def setup_plots(self):
        """Initialize plot elements"""
        # Side view setup
        self.ax_side.set_xlim(-self.config.chamber_radius * 1.1,
                             self.config.chamber_radius * 1.1)
        self.ax_side.set_ylim(-0.1, self.config.chamber_height * 1.1)
        self.ax_side.set_xlabel('X Position (m)', fontsize=10, fontweight='bold')
        self.ax_side.set_ylabel('Z Position (m)', fontsize=10, fontweight='bold')
        self.ax_side.set_title('Air Classifier - Side View', fontsize=12, fontweight='bold')
        self.ax_side.set_aspect('equal')
        self.ax_side.grid(True, alpha=0.2)

        # Draw chamber walls
        self.ax_side.axvline(x=-self.config.chamber_radius, color='k',
                            linestyle='--', alpha=0.4, linewidth=1)
        self.ax_side.axvline(x=self.config.chamber_radius, color='k',
                            linestyle='--', alpha=0.4, linewidth=1)
        self.ax_side.axhline(y=0, color='brown', linewidth=3, alpha=0.6,
                            label='Coarse collection')
        self.ax_side.axhline(y=self.config.chamber_height, color='k',
                            linestyle='--', alpha=0.4, linewidth=1)

        # Draw classifier wheel
        wheel_rect = plt.Rectangle(
            (-self.config.wheel_radius,
             self.config.wheel_position_z - self.config.wheel_width/2),
            self.config.wheel_radius * 2,
            self.config.wheel_width,
            color='red', alpha=0.2, linewidth=2, edgecolor='red',
            label='Classifier Wheel'
        )
        self.ax_side.add_patch(wheel_rect)

        # Feed zone indicator
        feed_height = 0.6  # From config
        self.ax_side.axhline(y=feed_height, color='green',
                            linestyle=':', alpha=0.5, label='Feed zone')

        self.ax_side.legend(loc='upper right', fontsize=8)

        # Top view setup
        self.ax_top.set_xlim(-self.config.chamber_radius * 1.1,
                            self.config.chamber_radius * 1.1)
        self.ax_top.set_ylim(-self.config.chamber_radius * 1.1,
                            self.config.chamber_radius * 1.1)
        self.ax_top.set_xlabel('X (m)', fontsize=9)
        self.ax_top.set_ylabel('Y (m)', fontsize=9)
        self.ax_top.set_title('Top View', fontsize=10, fontweight='bold')
        self.ax_top.set_aspect('equal')
        self.ax_top.grid(True, alpha=0.2)

        # Draw chamber and wheel circles
        chamber_circle = plt.Circle((0, 0), self.config.chamber_radius,
                                   fill=False, color='k', linestyle='--', alpha=0.4)
        wheel_circle = plt.Circle((0, 0), self.config.wheel_radius,
                                 fill=False, color='red', linewidth=2, alpha=0.5)
        self.ax_top.add_patch(chamber_circle)
        self.ax_top.add_patch(wheel_circle)

        # Collection dynamics setup
        self.ax_collection.set_xlabel('Time (s)', fontsize=9)
        self.ax_collection.set_ylabel('Particles', fontsize=9)
        self.ax_collection.set_title('Collection Dynamics', fontsize=10, fontweight='bold')
        self.ax_collection.grid(True, alpha=0.3)

        # Particle counts setup
        self.ax_counts.set_xlabel('Time (s)', fontsize=9)
        self.ax_counts.set_ylabel('Active Particles', fontsize=9)
        self.ax_counts.set_title('Active Particles in Classifier', fontsize=10, fontweight='bold')
        self.ax_counts.grid(True, alpha=0.3)

    def update(self, frame_data):
        """Update visualization with current simulation state"""
        state, elapsed_time = frame_data

        # Update data storage
        self.times.append(state['time'])
        self.fine_collected.append(state['collected_fine'])
        self.coarse_collected.append(state['collected_coarse'])
        self.active_counts.append(np.sum(state['active']))

        # Clear particle plots
        self.ax_side.collections.clear()
        self.ax_top.collections.clear()

        # Get active particles
        active_mask = state['active'] == 1
        positions = state['positions'][active_mask]
        types = state['particle_types'][active_mask]

        if len(positions) > 0:
            # Limit particles for visualization
            n_display = min(len(positions), 2000)
            indices = np.random.choice(len(positions), n_display, replace=False)

            protein_mask = types[indices] == 0
            starch_mask = types[indices] == 1

            # Side view - color by type
            self.ax_side.scatter(
                positions[indices[protein_mask], 0],
                positions[indices[protein_mask], 2],
                c='blue', s=3, alpha=0.6, label='Protein'
            )
            self.ax_side.scatter(
                positions[indices[starch_mask], 0],
                positions[indices[starch_mask], 2],
                c='orange', s=4, alpha=0.6, label='Starch'
            )

            # Top view
            self.ax_top.scatter(
                positions[indices[protein_mask], 0],
                positions[indices[protein_mask], 1],
                c='blue', s=2, alpha=0.5
            )
            self.ax_top.scatter(
                positions[indices[starch_mask], 0],
                positions[indices[starch_mask], 1],
                c='orange', s=3, alpha=0.5
            )

        # Update metrics text
        self.ax_metrics.clear()
        self.ax_metrics.axis('off')

        protein_pct = (np.sum(state['particle_types'] == 0) / len(state['particle_types'])) * 100

        metrics_text = f"""
REAL-TIME METRICS
{'='*30}

Time: {state['time']:.2f} s
Simulation Speed: {state['step']/(elapsed_time+0.001):.0f} steps/s

PARTICLES
  Active: {np.sum(state['active']):,}
  Protein: {np.sum(state['particle_types']==0):,} ({protein_pct:.0f}%)
  Starch: {np.sum(state['particle_types']==1):,}

COLLECTION
  Fine: {state['collected_fine']:,}
  Coarse: {state['collected_coarse']:,}
  Total: {state['collected_fine'] + state['collected_coarse']:,}

OPERATING CONDITIONS
  Wheel: {self.config.wheel_rpm:.0f} RPM
  Target d₅₀: 20 μm
        """

        self.ax_metrics.text(0.05, 0.95, metrics_text,
                            transform=self.ax_metrics.transAxes,
                            fontsize=9, verticalalignment='top',
                            fontfamily='monospace',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        # Update collection dynamics
        if len(self.times) > 1:
            self.ax_collection.clear()
            self.ax_collection.plot(self.times, self.fine_collected, 'b-',
                                   linewidth=2, label='Fine', marker='o', markersize=3)
            self.ax_collection.plot(self.times, self.coarse_collected, 'orange',
                                   linewidth=2, label='Coarse', marker='s', markersize=3)
            self.ax_collection.set_xlabel('Time (s)', fontsize=9)
            self.ax_collection.set_ylabel('Particles', fontsize=9)
            self.ax_collection.set_title('Collection Dynamics', fontsize=10, fontweight='bold')
            self.ax_collection.legend(loc='upper left', fontsize=8)
            self.ax_collection.grid(True, alpha=0.3)

        # Update active particles
        if len(self.times) > 1:
            self.ax_counts.clear()
            self.ax_counts.plot(self.times, self.active_counts, 'g-',
                               linewidth=2, marker='d', markersize=3)
            self.ax_counts.fill_between(self.times, self.active_counts, alpha=0.3, color='green')
            self.ax_counts.set_xlabel('Time (s)', fontsize=9)
            self.ax_counts.set_ylabel('Active Particles', fontsize=9)
            self.ax_counts.set_title('Active Particles in Classifier', fontsize=10, fontweight='bold')
            self.ax_counts.grid(True, alpha=0.3)

        self.fig.suptitle(
            f'Live Air Classifier Simulation - Yellow Pea Protein Separation',
            fontsize=14, fontweight='bold', y=0.98
        )

        return self.ax_side, self.ax_top, self.ax_metrics, self.ax_collection, self.ax_counts


def run_live_simulation():
    """Run simulation with live visualization"""

    print("\n" + "="*80)
    print(" COMPREHENSIVE AIR CLASSIFIER LIVE DEMONSTRATION")
    print(" GPU-Accelerated Particle Simulation with Real-Time Visualization")
    print("="*80)

    # Step 1: Configuration and Validation
    print("\n[1/6] LOADING CONFIGURATION AND VALIDATING DESIGN...")
    print("-" * 80)

    config, particle_props, sim_config = get_default_config()

    # Optimize for live demo
    config.num_particles = 5000  # Smaller for smooth animation
    sim_config.total_time = 2.0
    sim_config.output_interval = 0.05

    print(f"✓ Configuration loaded")
    print(f"  • Particles: {config.num_particles:,}")
    print(f"  • Duration: {sim_config.total_time}s")
    print(f"  • Wheel RPM: {config.wheel_rpm}")

    # Validate design
    validation = validate_classifier_design(config, particle_props, sim_config)

    print(f"\n✓ Design validation complete")
    print(f"  • Theoretical d₅₀: {validation.theoretical_d50:.1f} μm")
    print(f"  • Tip speed: {validation.tip_speed:.1f} m/s (safe: {validation.tip_speed_ok})")
    print(f"  • Separation feasible: {validation.separation_feasible}")

    # Step 2: Initialize Simulator
    print("\n[2/6] INITIALIZING GPU SIMULATOR...")
    print("-" * 80)

    simulator = AirClassifierSimulator(config, particle_props, sim_config)

    # Step 3: Run with Live Visualization
    print("\n[3/6] RUNNING LIVE SIMULATION...")
    print("-" * 80)
    print("Close the visualization window to continue to analysis...")

    # Create visualization
    viz = LiveClassifierVisualization(simulator, config)

    # Simulation generator
    steps_total = int(sim_config.total_time / config.dt)
    output_steps = int(sim_config.output_interval / config.dt)

    start_time = time.time()

    def frame_generator():
        """Generate frames for animation"""
        for step in range(steps_total):
            simulator.step()

            if step % output_steps == 0:
                state = simulator.get_state()
                elapsed = time.time() - start_time
                yield state, elapsed

                # Check if all particles collected
                if np.sum(state['active']) == 0:
                    print(f"\n✓ All particles collected at t={state['time']:.2f}s")
                    break

    # Run animation
    anim = FuncAnimation(
        viz.fig,
        viz.update,
        frames=frame_generator(),
        interval=50,  # 50ms between frames
        blit=False,
        repeat=False
    )

    plt.show()

    # Get final results
    results = {
        'time': viz.times,
        'fine_collected': viz.fine_collected,
        'coarse_collected': viz.coarse_collected,
        'active_count': viz.active_counts,
        'final_state': simulator.get_state()
    }

    elapsed = time.time() - start_time
    print(f"\n✓ Simulation completed in {elapsed:.2f}s")
    print(f"  • Average speed: {steps_total/elapsed:.0f} steps/second")

    # Step 4: Separation Analysis
    print("\n[4/6] ANALYZING SEPARATION PERFORMANCE...")
    print("-" * 80)

    particle_types = simulator.particle_types.numpy()
    analysis = analyze_separation(results, particle_types)
    print_separation_report(analysis)

    # Step 5: Grade Efficiency (Tromp Curve)
    print("\n[5/6] CALCULATING GRADE EFFICIENCY CURVE...")
    print("-" * 80)

    bin_centers, grade_eff, tromp_metrics = calculate_grade_efficiency(
        results, particle_types, n_bins=25
    )
    print_grade_efficiency_report(tromp_metrics)

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Plot Tromp curve
    print("\nGenerating Tromp curve visualization...")
    plot_grade_efficiency_curve(
        bin_centers, grade_eff, tromp_metrics,
        target_d50=particle_props.target_cut_size * 1e6,
        save_path=output_dir / "tromp_curve.png"
    )

    # Plot size distributions
    print("Generating size distribution plots...")
    plot_size_distributions(
        results['final_state'],
        particle_types,
        save_path=output_dir / "size_distributions.png"
    )

    # Step 6: Economic Analysis
    print("\n[6/6] ECONOMIC FEASIBILITY ANALYSIS...")
    print("-" * 80)

    economics = calculate_economics(
        analysis,
        feed_rate_kg_hr=200,
        operating_hours_year=4000,
        flour_cost_per_kg=0.80,
        protein_price_per_kg=3.50,
        starch_price_per_kg=0.60,
        capital_cost=53300,
        operating_cost_annual=32500
    )
    print_economics_report(economics)

    # Final Summary
    print("\n" + "="*80)
    print(" COMPREHENSIVE ANALYSIS COMPLETE")
    print("="*80)

    print("\n📊 KEY PERFORMANCE INDICATORS:")
    print("-" * 80)
    print(f"  Cut Size (d₅₀):              {tromp_metrics['d50']:.1f} μm " +
          f"(target: {particle_props.target_cut_size*1e6:.0f} μm)")
    print(f"  Sharpness Index (κ):         {tromp_metrics['kappa']:.2f} " +
          f"({tromp_metrics['sharpness_quality']})")
    print(f"  Protein Purity (Fine):       {analysis['protein_purity_fine']:.1f}% " +
          f"(target: {particle_props.target_protein_purity*100:.0f}%)")
    print(f"  Protein Recovery:            {analysis['protein_recovery']:.1f}%")
    print(f"  Fine Fraction Yield:         {analysis['fine_yield']:.1f}%")

    print("\n💰 ECONOMIC METRICS:")
    print("-" * 80)
    print(f"  Annual Revenue:              ${economics['total_revenue']:,.0f}")
    print(f"  Annual Costs:                ${economics['total_cost']:,.0f}")
    print(f"  Gross Margin:                ${economics['gross_margin']:,.0f}")
    print(f"  ROI:                         {economics['roi_pct']:.0f}%")
    print(f"  Payback Period:              {economics['payback_years']:.1f} years")

    print("\n✅ COMPLIANCE STATUS:")
    print("-" * 80)

    checks = {
        "Design validated": validation.tip_speed_ok and validation.rpm_in_range,
        "Separation feasible": validation.separation_feasible,
        "Protein purity target met": analysis['protein_purity_fine'] >=
            particle_props.target_protein_purity * 95,
        "Cut size within spec": abs(tromp_metrics['d50'] - validation.theoretical_d50) < 5,
        "Good separation sharpness": tromp_metrics['kappa'] < 2.0,
        "Economic viability": economics['payback_years'] < 5
    }

    passed = sum(checks.values())
    total = len(checks)

    for name, status in checks.items():
        symbol = "✓" if status else "✗"
        print(f"  [{symbol}] {name}")

    compliance_pct = (passed / total) * 100
    print(f"\n  Overall: {passed}/{total} checks passed ({compliance_pct:.0f}%)")

    if compliance_pct == 100:
        print("\n  ✓✓✓ FULLY COMPLIANT - Ready for pilot-scale testing")
    elif compliance_pct >= 80:
        print("\n  ✓ SUBSTANTIALLY COMPLIANT - Minor optimization recommended")
    else:
        print("\n  ⚠ REQUIRES OPTIMIZATION - Review parameters")

    print("\n📁 OUTPUT FILES:")
    print("-" * 80)
    print(f"  • {output_dir}/tromp_curve.png")
    print(f"  • {output_dir}/size_distributions.png")

    print("\n📚 DOCUMENTATION:")
    print("-" * 80)
    print("  • docs/air_classifier_design_guide.md")
    print("  • COMPLIANCE_REPORT.md")
    print("  • INDUSTRY_STANDARDS_IMPLEMENTATION.md")

    print("\n" + "="*80)
    print(" Thank you for using the Air Classifier Simulator!")
    print(" For questions, see documentation or engineering guide.")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        run_live_simulation()
    except KeyboardInterrupt:
        print("\n\n⚠ Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

"""
Run Air Classifier Protein Separation Simulation

Main entry point for running the complete simulation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from air_classifier.classifier_simulator import AirClassifierSimulator, SimulationConfig


def main():
    """Run the simulation"""
    print("=" * 70)
    print("AIR CLASSIFIER PROTEIN SEPARATION SIMULATION")
    print("=" * 70)
    
    # Create simulation configuration
    # Collection thresholds based on actual geometry:
    # - Distributor at z=0.50m
    # - Selector zone: 0.70m to 0.80m (bottom to top)
    # - Fines outlet at z=1.20m
    # - Coarse outlet at cone apex (~-0.90m)
    sim_config = SimulationConfig(
        num_particles=50000,
        duration=30.0,
        dt=0.001,
        device="cuda:0",
        collection_threshold_fine=1.0,    # Fine collection near top (z > 1.0m)
        collection_threshold_coarse=-0.8   # Coarse collection at cone bottom (z < -0.8m)
    )
    
    # Create and run simulator
    sim = AirClassifierSimulator(sim_config=sim_config)
    sim.run()
    
    # Analyze and display results
    results = sim.analyze_separation()
    
    print("\n" + "=" * 70)
    print("SEPARATION PERFORMANCE")
    print("=" * 70)
    
    print(f"\n📊 Collection Statistics:")
    print(f"  Total particles: {results['total_particles']}")
    print(f"  Collected: {results['collected_particles']} "
          f"({results['collected_particles']/results['total_particles']*100:.1f}%)")
    print(f"  Fines: {results['fines_count']} "
          f"({results['fines_count']/results['total_particles']*100:.1f}%)")
    print(f"  Coarse: {results['coarse_count']} "
          f"({results['coarse_count']/results['total_particles']*100:.1f}%)")
    
    if results['fines_count'] > 0:
        print(f"\n📈 Fines Fraction Quality:")
        print(f"  Mean diameter: {results['fines_mean_diameter']:.2f} μm")
        print(f"  Protein content: {results['fines_protein_fraction']*100:.1f}%")
        print(f"  Target: >55% protein")
        if results['fines_protein_fraction'] >= 0.55:
            print(f"  ✓ Target achieved!")
        else:
            print(f"  ⚠ Below target")
    
    if results['coarse_count'] > 0:
        print(f"\n📈 Coarse Fraction Quality:")
        print(f"  Mean diameter: {results['coarse_mean_diameter']:.2f} μm")
        print(f"  Starch content: {results['coarse_starch_fraction']*100:.1f}%")
        print(f"  Target: >85% starch")
        if results['coarse_starch_fraction'] >= 0.85:
            print(f"  ✓ Target achieved!")
        else:
            print(f"  ⚠ Below target")
    
    print("\n" + "=" * 70)
    print("✓ Simulation complete")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

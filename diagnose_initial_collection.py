"""
Diagnose Initial Collection Issue

Investigate why particles are being collected at step 0.
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from air_classifier.classifier_simulator import AirClassifierSimulator, SimulationConfig
from air_classifier.geometry.corrected_config import create_default_config

def main():
    print("=" * 70)
    print("DIAGNOSING INITIAL COLLECTION ISSUE")
    print("=" * 70)

    # Create configuration
    geom_config = create_default_config()
    sim_config = SimulationConfig(
        num_particles=50000,
        duration=0.001,  # Just one step
        dt=0.001,
        device="cuda:0",
        collection_threshold_fine=1.0,
        collection_threshold_coarse=-0.8
    )

    # Create simulator
    sim = AirClassifierSimulator(config=geom_config, sim_config=sim_config)

    # Check initial state
    print("\n📊 INITIAL STATE (before any simulation steps):")
    positions_init = sim.positions.numpy()
    diameters_init = sim.diameters.numpy()
    types_init = sim.types.numpy()
    active_init = sim.active.numpy()
    outlet_init = sim.collection_outlet.numpy()

    print(f"  Total particles: {len(positions_init)}")
    print(f"  Active particles: {np.sum(active_init)}")
    print(f"  Collected particles: {np.sum(active_init == 0)}")
    print(f"    Fines (outlet=1): {np.sum(outlet_init == 1)}")
    print(f"    Coarse (outlet=2): {np.sum(outlet_init == 2)}")

    z_positions = positions_init[:, 2]
    print(f"\n📏 Initial Z positions:")
    print(f"  Min Z: {np.min(z_positions):.4f} m")
    print(f"  Max Z: {np.max(z_positions):.4f} m")
    print(f"  Mean Z: {np.mean(z_positions):.4f} m")
    print(f"  Distributor Z: {geom_config.distributor_position_z:.4f} m")

    print(f"\n🎯 Collection thresholds:")
    print(f"  Fine threshold (z >): {sim_config.collection_threshold_fine:.4f} m")
    print(f"  Coarse threshold (z <): {sim_config.collection_threshold_coarse:.4f} m")

    # Check if any particles start in collection zones
    above_fine = np.sum(z_positions > sim_config.collection_threshold_fine)
    below_coarse = np.sum(z_positions < sim_config.collection_threshold_coarse)

    print(f"\n⚠️  Particles starting in collection zones:")
    print(f"  Above fine threshold: {above_fine}")
    print(f"  Below coarse threshold: {below_coarse}")

    # Run one step
    print("\n🔄 Running one simulation step...")
    sim.step()

    # Check state after one step
    print("\n📊 STATE AFTER ONE STEP:")
    active_after = sim.active.numpy()
    outlet_after = sim.collection_outlet.numpy()
    positions_after = sim.positions.numpy()

    print(f"  Active particles: {np.sum(active_after)}")
    print(f"  Collected particles: {np.sum(active_after == 0)}")
    print(f"    Fines (outlet=1): {np.sum(outlet_after == 1)}")
    print(f"    Coarse (outlet=2): {np.sum(outlet_after == 2)}")

    # Check collection counts
    fines_counted = sim.fines_collected
    coarse_counted = sim.coarse_collected
    print(f"\n📈 From atomic counters:")
    print(f"  Fines collected: {fines_counted}")
    print(f"  Coarse collected: {coarse_counted}")

    # Analyze collected particles
    collected_mask = (active_after == 0)
    fine_mask = (outlet_after == 1)
    coarse_mask = (outlet_after == 2)

    if np.sum(coarse_mask) > 0:
        print(f"\n🔍 COARSE FRACTION ANALYSIS:")
        coarse_z = positions_after[coarse_mask, 2]
        coarse_diameters = diameters_init[coarse_mask]
        coarse_types = types_init[coarse_mask]

        print(f"  Number collected: {np.sum(coarse_mask)}")
        print(f"  Z positions:")
        print(f"    Min: {np.min(coarse_z):.4f} m")
        print(f"    Max: {np.max(coarse_z):.4f} m")
        print(f"    Mean: {np.mean(coarse_z):.4f} m")
        print(f"  Diameters:")
        print(f"    Mean: {np.mean(coarse_diameters)*1e6:.2f} μm")
        print(f"    Min: {np.min(coarse_diameters)*1e6:.2f} μm")
        print(f"    Max: {np.max(coarse_diameters)*1e6:.2f} μm")
        print(f"  Types:")
        print(f"    Protein (type=0): {np.sum(coarse_types == 0)}")
        print(f"    Starch (type=1): {np.sum(coarse_types == 1)}")

    if np.sum(fine_mask) > 0:
        print(f"\n🔍 FINE FRACTION ANALYSIS:")
        fine_z = positions_after[fine_mask, 2]
        fine_diameters = diameters_init[fine_mask]
        fine_types = types_init[fine_mask]

        print(f"  Number collected: {np.sum(fine_mask)}")
        print(f"  Z positions:")
        print(f"    Min: {np.min(fine_z):.4f} m")
        print(f"    Max: {np.max(fine_z):.4f} m")
        print(f"    Mean: {np.mean(fine_z):.4f} m")
        print(f"  Diameters:")
        print(f"    Mean: {np.mean(fine_diameters)*1e6:.2f} μm")
        print(f"    Min: {np.min(fine_diameters)*1e6:.2f} μm")
        print(f"    Max: {np.max(fine_diameters)*1e6:.2f} μm")
        print(f"  Types:")
        print(f"    Protein (type=0): {np.sum(fine_types == 0)}")
        print(f"    Starch (type=1): {np.sum(fine_types == 1)}")

    print("\n" + "=" * 70)
    print("✓ Diagnosis complete")
    print("=" * 70)


if __name__ == "__main__":
    main()

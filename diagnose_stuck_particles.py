"""
Diagnose Stuck Particles

Check where particles are stuck and why they're not being collected.
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
    print("DIAGNOSING STUCK PARTICLES")
    print("=" * 70)

    # Create configuration
    geom_config = create_default_config()
    sim_config = SimulationConfig(
        num_particles=1000,  # Smaller for faster debugging
        duration=15.0,  # Run until particles freeze
        dt=0.001,
        device="cuda:0",
        collection_threshold_fine=1.0,
        collection_threshold_coarse=-0.8
    )

    # Create simulator
    sim = AirClassifierSimulator(config=geom_config, sim_config=sim_config)

    print("\n🎯 KEY GEOMETRY:")
    print(f"  Fines outlet Z: {sim.bc['fines_outlet_z']:.3f} m")
    print(f"  Coarse outlet Z: {sim.bc['coarse_outlet_z']:.3f} m")
    print(f"  Distributor Z: {geom_config.distributor_position_z:.3f} m")
    print(f"  Selector Z: {sim.bc['selector_z_min']:.3f} to {sim.bc['selector_z_max']:.3f} m")

    # Run simulation
    print("\n🔄 Running simulation...")
    steps = 15000  # 15 seconds
    for step in range(steps):
        sim.step()

        if step % 1000 == 0:
            active = sim.active.numpy()
            positions = sim.positions.numpy()
            velocities = sim.velocities.numpy()
            diameters = sim.diameters.numpy()

            active_mask = active == 1
            if np.sum(active_mask) > 0:
                z_pos = positions[active_mask, 2]
                v_z = velocities[active_mask, 2]
                d_active = diameters[active_mask]

                print(f"\n  Step {step:5d} (t={sim.time:.1f}s): {np.sum(active_mask)} active")
                print(f"    Z range: [{np.min(z_pos):.3f}, {np.max(z_pos):.3f}] m")
                print(f"    Z mean: {np.mean(z_pos):.3f} m")
                print(f"    V_z range: [{np.min(v_z):.2f}, {np.max(v_z):.2f}] m/s")
                print(f"    V_z mean: {np.mean(v_z):.2f} m/s")
                print(f"    Diameter range: [{np.min(d_active)*1e6:.1f}, {np.max(d_active)*1e6:.1f}] μm")

    # Final analysis
    print("\n" + "=" * 70)
    print("FINAL STATE ANALYSIS")
    print("=" * 70)

    positions_final = sim.positions.numpy()
    velocities_final = sim.velocities.numpy()
    diameters_final = sim.diameters.numpy()
    types_final = sim.types.numpy()
    active_final = sim.active.numpy()
    outlet_final = sim.collection_outlet.numpy()

    active_mask = active_final == 1
    n_active = np.sum(active_mask)

    print(f"\n📊 COLLECTION RESULTS:")
    print(f"  Total particles: {len(active_final)}")
    print(f"  Fines collected: {np.sum(outlet_final == 1)} ({np.sum(outlet_final == 1)/len(active_final)*100:.1f}%)")
    print(f"  Coarse collected: {np.sum(outlet_final == 2)} ({np.sum(outlet_final == 2)/len(active_final)*100:.1f}%)")
    print(f"  Still active (stuck): {n_active} ({n_active/len(active_final)*100:.1f}%)")

    if n_active > 0:
        print(f"\n🔍 STUCK PARTICLES ANALYSIS:")
        z_stuck = positions_final[active_mask, 2]
        r_stuck = np.sqrt(positions_final[active_mask, 0]**2 + positions_final[active_mask, 1]**2)
        v_z_stuck = velocities_final[active_mask, 2]
        v_r_stuck = (positions_final[active_mask, 0] * velocities_final[active_mask, 0] +
                     positions_final[active_mask, 1] * velocities_final[active_mask, 1]) / np.maximum(r_stuck, 0.01)
        d_stuck = diameters_final[active_mask]
        t_stuck = types_final[active_mask]

        print(f"  Position:")
        print(f"    Z: min={np.min(z_stuck):.3f}, max={np.max(z_stuck):.3f}, mean={np.mean(z_stuck):.3f} m")
        print(f"    R: min={np.min(r_stuck):.3f}, max={np.max(r_stuck):.3f}, mean={np.mean(r_stuck):.3f} m")
        print(f"  Velocity:")
        print(f"    V_z: min={np.min(v_z_stuck):.3f}, max={np.max(v_z_stuck):.3f}, mean={np.mean(v_z_stuck):.3f} m/s")
        print(f"    V_r: min={np.min(v_r_stuck):.3f}, max={np.max(v_r_stuck):.3f}, mean={np.mean(v_r_stuck):.3f} m/s")
        print(f"  Diameter:")
        print(f"    min={np.min(d_stuck)*1e6:.1f}, max={np.max(d_stuck)*1e6:.1f}, mean={np.mean(d_stuck)*1e6:.1f} μm")
        print(f"  Composition:")
        print(f"    Protein (type=0): {np.sum(t_stuck == 0)} ({np.sum(t_stuck == 0)/n_active*100:.1f}%)")
        print(f"    Starch (type=1): {np.sum(t_stuck == 1)} ({np.sum(t_stuck == 1)/n_active*100:.1f}%)")

        # Check proximity to outlets
        above_fine_z = np.sum(z_stuck > 0.9)
        near_fine_r = np.sum((z_stuck > 0.9) & (r_stuck < 0.1))
        below_coarse_z = np.sum(z_stuck < -0.7)
        near_coarse_r = np.sum((z_stuck < -0.7) & (r_stuck < 0.1))

        print(f"\n🎯 PROXIMITY TO OUTLETS:")
        print(f"  Near fines outlet (Z>0.9m): {above_fine_z}")
        print(f"    And R<0.1m: {near_fine_r}")
        print(f"  Near coarse outlet (Z<-0.7m): {below_coarse_z}")
        print(f"    And R<0.1m: {near_coarse_r}")

        # Check if particles are in equilibrium
        v_mag = np.sqrt(velocities_final[active_mask, 0]**2 +
                       velocities_final[active_mask, 1]**2 +
                       velocities_final[active_mask, 2]**2)
        stuck_stationary = np.sum(v_mag < 0.01)

        print(f"\n⚠️  PARTICLE DYNAMICS:")
        print(f"  Nearly stationary (|v| < 0.01 m/s): {stuck_stationary} ({stuck_stationary/n_active*100:.1f}%)")
        print(f"  Average speed: {np.mean(v_mag):.3f} m/s")

    print("\n" + "=" * 70)
    print("✓ Diagnosis complete")
    print("=" * 70)


if __name__ == "__main__":
    main()

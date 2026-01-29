"""Quick test of improved classifier"""

from air_classifier import (
    AirClassifierSimulator,
    get_default_config,
    analyze_separation,
)

# Small fast test
config, particle_props, sim_config = get_default_config()
config.num_particles = 500
sim_config.total_time = 5.0
sim_config.output_interval = 0.5

print("Quick Classifier Test")
print("="*60)
print(f"Particles: {config.num_particles}")
print(f"Time: {sim_config.total_time}s")
print(f"Wheel RPM: {config.wheel_rpm}")
print(f"Feed: z={sim_config.feed_height}m, r={sim_config.feed_radius_min}-{sim_config.feed_radius_max}m")
print(f"Wheel: z={config.wheel_position_z}m, r={config.wheel_radius}m")
print("="*60)

# Run
simulator = AirClassifierSimulator(config, particle_props, sim_config)
results = simulator.run()

# Analyze
particle_types = simulator.particle_types.numpy()
analysis = analyze_separation(results, particle_types)

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"Fine collected:   {analysis['fine_collected']:4d} ({analysis['fine_collected']/config.num_particles*100:5.1f}%)")
print(f"Coarse collected: {analysis['coarse_collected']:4d} ({analysis['coarse_collected']/config.num_particles*100:5.1f}%)")
print(f"Still active:     {config.num_particles - analysis['fine_collected'] - analysis['coarse_collected']:4d}")
print(f"Collection rate:  {(analysis['fine_collected'] + analysis['coarse_collected'])/config.num_particles*100:5.1f}%")

if analysis['fine_collected'] > 0:
    print(f"\nSeparation Performance:")
    print(f"  Protein purity (fine):    {analysis['protein_purity_fine']:.1f}%")
    print(f"  Protein recovery:         {analysis['protein_recovery']:.1f}%")
    print(f"  Fine yield:               {analysis['fine_yield']:.1f}%")
    print(f"  Estimated cut size:       {analysis['d50_estimate']:.1f} μm")

    if analysis['protein_purity_fine'] > 50:
        print(f"\n✓ SUCCESSFUL SEPARATION!")
        if analysis['protein_purity_fine'] >= 55:
            print(f"   Target purity achieved (55-65% target)")
    else:
        print(f"\n⚠ Separation working but purity below target")
else:
    print(f"\n✗ No fine particles collected")

print("="*60)

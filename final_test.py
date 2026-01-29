"""Final test after fixes"""
from air_classifier import AirClassifierSimulator, get_default_config, analyze_separation

config, particle_props, sim_config = get_default_config()
config.num_particles = 500
sim_config.total_time = 5.0
sim_config.output_interval = 0.5

print("="*60)
print("FINAL TEST - Air Classifier")
print("="*60)
print(f"Configuration:")
print(f"  Particles: {config.num_particles}")
print(f"  Wheel: R={config.wheel_radius}m at z={config.wheel_position_z}m, {config.wheel_rpm} RPM")
print(f"  Feed: z={sim_config.feed_height}m, r={sim_config.feed_radius_min}-{sim_config.feed_radius_max}m")
print(f"  Upward zone: r < {config.wheel_radius * 0.93:.3f}m")
print(f"  Downward zone: r > {config.wheel_radius * 1.15:.3f}m")
print("="*60)

simulator = AirClassifierSimulator(config, particle_props, sim_config)
results = simulator.run()

particle_types = simulator.particle_types.numpy()
analysis = analyze_separation(results, particle_types)

print("\n" + "="*60)
print("RESULTS")
print("="*60)
total_collected = analysis['fine_collected'] + analysis['coarse_collected']
print(f"Fine collected:   {analysis['fine_collected']:4d} ({analysis['fine_collected']/config.num_particles*100:5.1f}%)")
print(f"Coarse collected: {analysis['coarse_collected']:4d} ({analysis['coarse_collected']/config.num_particles*100:5.1f}%)")
print(f"Active:           {config.num_particles - total_collected:4d} ({(config.num_particles - total_collected)/config.num_particles*100:5.1f}%)")
print(f"Collection rate:  {total_collected/config.num_particles*100:5.1f}%")

if analysis['fine_collected'] > 0:
    print(f"\nSeparation Quality:")
    print(f"  Protein purity (fine):  {analysis['protein_purity_fine']:5.1f}%")
    print(f"  Protein recovery:       {analysis['protein_recovery']:5.1f}%")
    print(f"  Fine yield:             {analysis['fine_yield']:5.1f}%")
    print(f"  Cut size (est):         {analysis['d50_estimate']:5.1f} μm")

    if analysis['protein_purity_fine'] >= 55:
        print(f"\n✓✓✓ SUCCESS! Target purity achieved (55-65% target)")
    elif analysis['protein_purity_fine'] > 50:
        print(f"\n✓ Good separation, approaching target purity")
    else:
        print(f"\n⚠ Separation working but below target")
else:
    print(f"\n✗ FAILED - No fine particles collected")
    print(f"   All particles going to coarse outlet")

print("="*60)

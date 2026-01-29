"""Quick verification test"""
from air_classifier import AirClassifierSimulator, get_default_config, analyze_separation

config, particle_props, sim_config = get_default_config()
config.num_particles = 200
sim_config.total_time = 3.0
sim_config.output_interval = 0.5

print("Quick Test (200 particles, 3s)")
print("="*50)

simulator = AirClassifierSimulator(config, particle_props, sim_config)
results = simulator.run()

particle_types = simulator.particle_types.numpy()
analysis = analyze_separation(results, particle_types)

print("\nResults:")
print(f"  Fine: {analysis['fine_collected']} ({analysis['fine_collected']/config.num_particles*100:.1f}%)")
print(f"  Coarse: {analysis['coarse_collected']} ({analysis['coarse_collected']/config.num_particles*100:.1f}%)")
print(f"  Active: {config.num_particles - analysis['fine_collected'] - analysis['coarse_collected']}")

if analysis['fine_collected'] > 0:
    print(f"\n✓ Fine collection working!")
    print(f"  Protein purity: {analysis['protein_purity_fine']:.1f}%")
else:
    print(f"\n✗ Still broken - no fine particles")

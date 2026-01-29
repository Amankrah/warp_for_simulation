"""Quick test to verify particle collection is working"""

from air_classifier import (
    AirClassifierSimulator,
    get_default_config,
    analyze_separation,
    print_separation_report
)

print("Testing Particle Collection Fix...")
print("="*60)

# Get configuration
config, particle_props, sim_config = get_default_config()

# Small fast test
config.num_particles = 2000
sim_config.total_time = 10.0
sim_config.output_interval = 0.5

print(f"Configuration:")
print(f"  Particles: {config.num_particles}")
print(f"  Simulation time: {sim_config.total_time}s")
print(f"  Collection threshold (fine): {sim_config.collection_threshold_fine}m")
print(f"  Collection threshold (coarse): {sim_config.collection_threshold_coarse}m")

# Run simulation
simulator = AirClassifierSimulator(config, particle_props, sim_config)
results = simulator.run()

# Analyze
particle_types = simulator.particle_types.numpy()
analysis = analyze_separation(results, particle_types)

print("\n" + "="*60)
print("RESULTS:")
print("="*60)
print(f"Fine collected: {analysis['fine_collected']}")
print(f"Coarse collected: {analysis['coarse_collected']}")
print(f"Total collected: {analysis['fine_collected'] + analysis['coarse_collected']}")
print(f"Collection rate: {(analysis['fine_collected'] + analysis['coarse_collected'])/config.num_particles*100:.1f}%")

if analysis['fine_collected'] > 0:
    print(f"\n✓ PARTICLES ARE COLLECTING!")
    print(f"  Protein purity (fine): {analysis['protein_purity_fine']:.1f}%")
    print(f"  Protein recovery: {analysis['protein_recovery']:.1f}%")
else:
    print(f"\n✗ NO PARTICLES COLLECTED YET")
    print(f"  Try increasing simulation time or adjusting collection thresholds")

print("="*60)

"""Diagnose why particles aren't collecting - analyze particle positions"""

import numpy as np
import matplotlib.pyplot as plt
from air_classifier import AirClassifierSimulator, get_default_config

# Get configuration
config, particle_props, sim_config = get_default_config()
config.num_particles = 2000
sim_config.total_time = 10.0
sim_config.output_interval = 0.5

print("Diagnosing Collection Issues...")
print("="*60)

# Run simulation
simulator = AirClassifierSimulator(config, particle_props, sim_config)
results = simulator.run()

# Get final state
final_state = simulator.get_state()
positions = final_state['positions']
active = final_state['active']
collection_times = final_state['collection_time']
collection_positions = final_state['collection_position']
particle_types = simulator.particle_types.numpy()

# Analyze active particles
active_mask = active == 1
active_positions = positions[active_mask]
active_types = particle_types[active_mask]

n_active = int(np.sum(active_mask))
n_collected_by_time = int(np.sum(collection_times > 0))
# Use simulator counts when available (fine + coarse) so total matches simulator
state = simulator.get_state()
n_fine = int(state.get('collected_fine', 0))
n_coarse = int(state.get('collected_coarse', 0))
n_collected_total = n_fine + n_coarse

print(f"\nActive particles: {n_active}")
print(f"Collected particles: {n_collected_total} (Fine={n_fine}, Coarse={n_coarse})")
if n_collected_by_time != n_collected_total:
    print(f"  (by collection_time>0: {n_collected_by_time})")

# Analyze positions of active particles
if len(active_positions) > 0:
    r_active = np.sqrt(active_positions[:, 0]**2 + active_positions[:, 1]**2)
    z_active = active_positions[:, 2]
    
    print(f"\nActive particle statistics:")
    print(f"  Radial position: min={np.min(r_active):.3f}m, max={np.max(r_active):.3f}m, mean={np.mean(r_active):.3f}m")
    print(f"  Height position: min={np.min(z_active):.3f}m, max={np.max(z_active):.3f}m, mean={np.mean(z_active):.3f}m")
    
    # Check how many are in collection zones
    fine_zone = (z_active > sim_config.collection_threshold_fine) & (r_active < config.wheel_radius * 1.1)
    coarse_zone = z_active < sim_config.collection_threshold_coarse
    
    print(f"\nActive particles in collection zones:")
    print(f"  Fine zone (z>{sim_config.collection_threshold_fine}m, r<{config.wheel_radius*1.1:.3f}m): {np.sum(fine_zone)}")
    print(f"  Coarse zone (z<{sim_config.collection_threshold_coarse}m): {np.sum(coarse_zone)}")
    
    # Check middle region
    middle_zone = (z_active >= sim_config.collection_threshold_coarse) & (z_active <= sim_config.collection_threshold_fine)
    print(f"  Middle zone (stuck): {np.sum(middle_zone)}")

# Analyze collected particles
collected_mask = collection_times > 0
if np.sum(collected_mask) > 0:
    collected_positions = collection_positions[collected_mask]
    r_collected = np.sqrt(collected_positions[:, 0]**2 + collected_positions[:, 1]**2)
    z_collected = collected_positions[:, 2]
    
    print(f"\nCollected particle statistics:")
    print(f"  Radial position: min={np.min(r_collected):.3f}m, max={np.max(r_collected):.3f}m, mean={np.mean(r_collected):.3f}m")
    print(f"  Height position: min={np.min(z_collected):.3f}m, max={np.max(z_collected):.3f}m, mean={np.mean(z_collected):.3f}m")

# Create diagnostic plots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Plot 1: Side view - all particles
ax = axes[0, 0]
if len(active_positions) > 0:
    protein_active = active_types == 0
    starch_active = active_types == 1
    ax.scatter(active_positions[protein_active, 0], active_positions[protein_active, 2],
               c='blue', s=5, alpha=0.5, label=f'Active Protein ({np.sum(protein_active)})')
    ax.scatter(active_positions[starch_active, 0], active_positions[starch_active, 2],
               c='orange', s=6, alpha=0.5, label=f'Active Starch ({np.sum(starch_active)})')

if np.sum(collected_mask) > 0:
    collected_types = particle_types[collected_mask]
    protein_collected = collected_types == 0
    starch_collected = collected_types == 1
    ax.scatter(collected_positions[protein_collected, 0], collected_positions[protein_collected, 2],
               c='green', s=10, marker='x', label=f'Collected Protein ({np.sum(protein_collected)})')
    ax.scatter(collected_positions[starch_collected, 0], collected_positions[starch_collected, 2],
               c='red', s=12, marker='x', label=f'Collected Starch ({np.sum(starch_collected)})')

# Draw chamber boundaries
ax.axvline(x=-config.chamber_radius, color='k', linestyle='--', alpha=0.3)
ax.axvline(x=config.chamber_radius, color='k', linestyle='--', alpha=0.3)
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.axhline(y=config.chamber_height, color='k', linestyle='--', alpha=0.3)

# Draw wheel
wheel_rect = plt.Rectangle(
    (-config.wheel_radius, config.wheel_position_z - config.wheel_width/2),
    config.wheel_radius * 2,
    config.wheel_width,
    color='red', alpha=0.2, label='Wheel'
)
ax.add_patch(wheel_rect)

# Draw collection zones
ax.axhline(y=sim_config.collection_threshold_fine, color='g', linestyle=':', linewidth=2, label='Fine threshold')
ax.axhline(y=sim_config.collection_threshold_coarse, color='orange', linestyle=':', linewidth=2, label='Coarse threshold')
ax.axvline(x=config.wheel_radius * 1.1, color='g', linestyle=':', alpha=0.5, label='Fine radius limit')

ax.set_xlabel('X Position (m)')
ax.set_ylabel('Z Position (m)')
ax.set_title('Side View - All Particles')
ax.legend(loc='best', fontsize=8)
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')

# Plot 2: Height distribution
ax = axes[0, 1]
if len(active_positions) > 0:
    ax.hist(z_active, bins=50, alpha=0.6, label='Active', color='blue')
if np.sum(collected_mask) > 0:
    ax.hist(z_collected, bins=50, alpha=0.6, label='Collected', color='green')
ax.axvline(x=sim_config.collection_threshold_fine, color='g', linestyle='--', linewidth=2, label='Fine threshold')
ax.axvline(x=sim_config.collection_threshold_coarse, color='orange', linestyle='--', linewidth=2, label='Coarse threshold')
ax.axvline(x=config.wheel_position_z, color='r', linestyle=':', alpha=0.5, label='Wheel center')
ax.set_xlabel('Height (m)')
ax.set_ylabel('Count')
ax.set_title('Height Distribution')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 3: Radial distribution
ax = axes[1, 0]
if len(active_positions) > 0:
    ax.hist(r_active, bins=50, alpha=0.6, label='Active', color='blue')
if np.sum(collected_mask) > 0:
    ax.hist(r_collected, bins=50, alpha=0.6, label='Collected', color='green')
ax.axvline(x=config.wheel_radius, color='r', linestyle='--', linewidth=2, label='Wheel radius')
ax.axvline(x=config.wheel_radius * 1.1, color='g', linestyle=':', linewidth=2, label='Fine radius limit')
ax.axvline(x=config.chamber_radius, color='k', linestyle='--', alpha=0.5, label='Chamber radius')
ax.set_xlabel('Radial Distance (m)')
ax.set_ylabel('Count')
ax.set_title('Radial Distribution')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Collection over time
ax = axes[1, 1]
times = np.array(results['time'])
fine = np.array(results['fine_collected'])
coarse = np.array(results['coarse_collected'])
active_count = np.array(results['active_count'])
ax.plot(times, fine, 'b-', linewidth=2, label='Fine', marker='o', markersize=4)
ax.plot(times, coarse, 'orange', linewidth=2, label='Coarse', marker='s', markersize=4)
ax.plot(times, active_count, 'g-', linewidth=2, label='Active', marker='d', markersize=4)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Count')
ax.set_title('Collection Over Time')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('output/collection_diagnosis.png', dpi=150, bbox_inches='tight')
print(f"\nSaved diagnostic plot to output/collection_diagnosis.png")
plt.show()

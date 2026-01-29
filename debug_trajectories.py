"""Debug script to visualize particle trajectories and understand what's happening"""

import numpy as np
import matplotlib.pyplot as plt
from air_classifier import (
    AirClassifierSimulator,
    get_default_config,
)

# Small test
config, particle_props, sim_config = get_default_config()
config.num_particles = 100  # Very small for debugging
sim_config.total_time = 10.0
sim_config.output_interval = 0.02

print("Starting debug simulation...")
print(f"Chamber: R={config.chamber_radius}m, H={config.chamber_height}m")
print(f"Wheel: R={config.wheel_radius}m at z={config.wheel_position_z}m")
print(f"Feed zone: z={sim_config.feed_height}m, r={sim_config.feed_radius_min}-{sim_config.feed_radius_max}m")
print(f"Collection thresholds: fine z>{sim_config.collection_threshold_fine}m, coarse z<{sim_config.collection_threshold_coarse}m")

# Run simulation
simulator = AirClassifierSimulator(config, particle_props, sim_config)

# Track a few particles
track_indices = [0, 10, 20, 30, 40]  # Mix of protein and starch
trajectories = {idx: {'t': [], 'r': [], 'z': [], 'vz': []} for idx in track_indices}

# Manual stepping to track trajectories
steps = int(sim_config.total_time / config.dt)
output_steps = int(sim_config.output_interval / config.dt)

for step in range(steps):
    simulator.step()

    if step % output_steps == 0:
        state = simulator.get_state()
        positions = state['positions']
        velocities = state['velocities']
        active = state['active']

        # Track specific particles
        for idx in track_indices:
            if active[idx]:
                r = np.sqrt(positions[idx, 0]**2 + positions[idx, 1]**2)
                trajectories[idx]['t'].append(state['time'])
                trajectories[idx]['r'].append(r)
                trajectories[idx]['z'].append(positions[idx, 2])
                trajectories[idx]['vz'].append(velocities[idx, 2])

        # Print status
        if step % (output_steps * 5) == 0:
            n_active = np.sum(active)
            print(f"t={state['time']:.3f}s: Active={n_active}, Fine={state['collected_fine']}, Coarse={state['collected_coarse']}")

        if np.sum(active) == 0:
            print("All particles collected!")
            break

# Get final state
final_state = simulator.get_state()
particle_types = simulator.particle_types.numpy()

print(f"\nFinal results:")
print(f"  Fine: {final_state['collected_fine']}")
print(f"  Coarse: {final_state['collected_coarse']}")

# Plot trajectories
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Z position vs time
ax = axes[0, 0]
for idx in track_indices:
    ptype = 'Protein' if particle_types[idx] == 0 else 'Starch'
    d = simulator.diameters.numpy()[idx] * 1e6
    label = f'P{idx} ({ptype}, {d:.1f}μm)'
    ax.plot(trajectories[idx]['t'], trajectories[idx]['z'], 'o-', label=label, markersize=3)

ax.axhline(y=config.wheel_position_z, color='r', linestyle='--', label='Wheel height')
ax.axhline(y=sim_config.collection_threshold_fine, color='g', linestyle='--', label='Fine threshold')
ax.axhline(y=sim_config.collection_threshold_coarse, color='orange', linestyle='--', label='Coarse threshold')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Z position (m)')
ax.set_title('Particle Height vs Time')
ax.legend(fontsize=8, loc='best')
ax.grid(True, alpha=0.3)

# Plot 2: Radial position vs time
ax = axes[0, 1]
for idx in track_indices:
    ptype = 'Protein' if particle_types[idx] == 0 else 'Starch'
    ax.plot(trajectories[idx]['t'], trajectories[idx]['r'], 'o-', label=f'P{idx} ({ptype})', markersize=3)

ax.axhline(y=config.wheel_radius, color='r', linestyle='--', label='Wheel radius')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Radial position (m)')
ax.set_title('Radial Position vs Time')
ax.legend(fontsize=8, loc='best')
ax.grid(True, alpha=0.3)

# Plot 3: R-Z trajectory
ax = axes[1, 0]
for idx in track_indices:
    ptype = 'Protein' if particle_types[idx] == 0 else 'Starch'
    color = 'blue' if particle_types[idx] == 0 else 'orange'
    ax.plot(trajectories[idx]['r'], trajectories[idx]['z'], 'o-',
            color=color, label=f'P{idx} ({ptype})', markersize=3, alpha=0.7)

# Draw classifier geometry
theta = np.linspace(0, 2*np.pi, 100)
wheel_x = config.wheel_radius * np.cos(theta)
wheel_y = config.wheel_radius * np.sin(theta)
chamber_x = config.chamber_radius * np.cos(theta)
chamber_y = config.chamber_radius * np.sin(theta)

ax.plot([0, config.chamber_radius], [config.wheel_position_z]*2, 'r-', linewidth=2, label='Wheel')
ax.plot([0, config.chamber_radius], [sim_config.collection_threshold_fine]*2, 'g--', label='Fine collection')
ax.plot([0, config.chamber_radius], [sim_config.collection_threshold_coarse]*2, 'orange', linestyle='--', label='Coarse collection')
ax.axvline(x=config.wheel_radius, color='r', linestyle=':', alpha=0.5)
ax.axvline(x=config.chamber_radius, color='k', linestyle='-', alpha=0.3)

ax.set_xlabel('Radial position (m)')
ax.set_ylabel('Z position (m)')
ax.set_title('Particle Trajectories (R-Z plane)')
ax.legend(fontsize=8, loc='best')
ax.grid(True, alpha=0.3)
ax.set_xlim([0, config.chamber_radius * 1.1])
ax.set_ylim([0, config.chamber_height])

# Plot 4: Vertical velocity vs time
ax = axes[1, 1]
for idx in track_indices:
    ptype = 'Protein' if particle_types[idx] == 0 else 'Starch'
    ax.plot(trajectories[idx]['t'], trajectories[idx]['vz'], 'o-', label=f'P{idx} ({ptype})', markersize=3)

ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Vertical velocity (m/s)')
ax.set_title('Vertical Velocity vs Time')
ax.legend(fontsize=8, loc='best')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('output/debug_trajectories.png', dpi=150, bbox_inches='tight')
print("\nTrajectory plot saved to output/debug_trajectories.png")
plt.show()

# Print particle details
print("\nParticle details:")
diameters = simulator.diameters.numpy() * 1e6
for idx in track_indices:
    ptype = 'Protein' if particle_types[idx] == 0 else 'Starch'
    print(f"  P{idx}: {ptype:7s}, d={diameters[idx]:5.2f}μm, "
          f"initial z={trajectories[idx]['z'][0]:.3f}m, "
          f"final z={trajectories[idx]['z'][-1] if trajectories[idx]['z'] else 'N/A'}m")

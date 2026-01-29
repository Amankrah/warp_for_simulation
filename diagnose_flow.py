"""Diagnose air flow field to understand why no fine collection"""

import numpy as np
import matplotlib.pyplot as plt
from air_classifier.config import ClassifierConfig, SimulationConfig

# Configuration
config = ClassifierConfig()
wheel_radius = config.wheel_radius  # 0.2 m
wheel_z = config.wheel_position_z  # 0.9 m
wheel_width = config.wheel_width  # 0.06 m
wheel_omega = config.wheel_rpm * 2 * np.pi / 60  # rad/s
air_vel_radial = config.air_velocity  # 8 m/s

print(f"Configuration:")
print(f"  Wheel radius: {wheel_radius}m")
print(f"  Wheel z: {wheel_z}m")
print(f"  Wheel width: {wheel_width}m")
print(f"  Wheel RPM: {config.wheel_rpm}")
print(f"  Wheel omega: {wheel_omega:.1f} rad/s")

# Compute air velocity field
r_values = np.linspace(0, 0.5, 100)
z_values = np.linspace(0, 1.2, 100)

R, Z = np.meshgrid(r_values, z_values)
V_axial = np.zeros_like(R)

for i in range(len(z_values)):
    for j in range(len(r_values)):
        r = r_values[j]
        z = z_values[i]

        z_dist = abs(z - wheel_z)
        radial_factor = np.exp(-z_dist / (wheel_width * 4.0))

        # Axial velocity (copied from simulator logic)
        if r < wheel_radius * 0.93:
            radial_position_factor = 1.0 - (r / (wheel_radius * 0.93))

            if z > wheel_z + wheel_width * 0.5:
                height_factor = 1.3
            elif z > wheel_z - wheel_width * 0.5:
                height_factor = 1.1
            else:
                height_factor = 0.65 + 0.45 * np.exp(-(wheel_z - z) / (wheel_width * 3.0))

            v_axial = 22.0 * radial_position_factor * height_factor
        elif r > wheel_radius * 1.15:
            v_axial = -6.5
        else:
            transition_factor = (r - wheel_radius * 0.93) / (wheel_radius * 0.22)
            v_axial = -1.0 - transition_factor * 5.5

        V_axial[i, j] = v_axial

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Contour plot
ax = axes[0]
levels = np.linspace(-7, 25, 20)
contour = ax.contourf(R, Z, V_axial, levels=levels, cmap='RdBu_r')
ax.contour(R, Z, V_axial, levels=[0], colors='black', linewidths=2)
plt.colorbar(contour, ax=ax, label='Axial velocity (m/s)')

# Mark key zones
ax.axhline(y=wheel_z, color='yellow', linestyle='--', linewidth=2, label='Wheel height')
ax.axhline(y=0.85, color='green', linestyle='--', label='Feed height')
ax.axvline(x=wheel_radius, color='yellow', linestyle=':', linewidth=2, label='Wheel radius')
ax.axvline(x=wheel_radius * 0.93, color='cyan', linestyle=':', label='Upward zone edge')
ax.axvline(x=wheel_radius * 1.15, color='red', linestyle=':', label='Downward zone edge')

ax.set_xlabel('Radial position (m)')
ax.set_ylabel('Height (m)')
ax.set_title('Axial Air Velocity Field')
ax.legend(loc='upper right', fontsize=8)
ax.set_xlim([0, 0.5])
ax.set_ylim([0, 1.2])

# Velocity profile at feed height
ax = axes[1]
feed_z = 0.85
feed_profile = []
for r in r_values:
    z = feed_z
    z_dist = abs(z - wheel_z)

    if r < wheel_radius * 0.93:
        radial_position_factor = 1.0 - (r / (wheel_radius * 0.93))
        height_factor = 0.65 + 0.45 * np.exp(-(wheel_z - z) / (wheel_width * 3.0))
        v_axial = 22.0 * radial_position_factor * height_factor
    elif r > wheel_radius * 1.15:
        v_axial = -6.5
    else:
        transition_factor = (r - wheel_radius * 0.93) / (wheel_radius * 0.22)
        v_axial = -1.0 - transition_factor * 5.5

    feed_profile.append(v_axial)

ax.plot(r_values, feed_profile, 'b-', linewidth=2)
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.axvline(x=wheel_radius, color='yellow', linestyle='--', linewidth=2, label='Wheel radius')
ax.axvline(x=wheel_radius * 0.93, color='cyan', linestyle=':', label='Upward edge')
ax.axvline(x=wheel_radius * 1.15, color='red', linestyle=':', label='Downward edge')
ax.fill_between([0, wheel_radius * 0.93], -10, 30, alpha=0.2, color='blue', label='Upward zone')
ax.fill_between([wheel_radius * 1.15, 0.5], -10, 30, alpha=0.2, color='red', label='Downward zone')

ax.set_xlabel('Radial position (m)')
ax.set_ylabel('Axial velocity (m/s)')
ax.set_title(f'Velocity Profile at Feed Height (z={feed_z}m)')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xlim([0, 0.5])

plt.tight_layout()
plt.savefig('output/flow_field_diagnosis.png', dpi=150, bbox_inches='tight')
print(f"\nSaved flow field visualization to output/flow_field_diagnosis.png")
plt.show()

# Check velocity at key locations
print(f"\nVelocity at key locations (at feed height z=0.85m):")
test_radii = [0.0, 0.1, 0.15, 0.18, 0.186, 0.20, 0.23, 0.25, 0.3, 0.35]
for r_test in test_radii:
    z = 0.85
    if r_test < wheel_radius * 0.93:
        radial_position_factor = 1.0 - (r_test / (wheel_radius * 0.93))
        height_factor = 0.65 + 0.45 * np.exp(-(wheel_z - z) / (wheel_width * 3.0))
        v_axial = 22.0 * radial_position_factor * height_factor
        zone = "UPWARD"
    elif r_test > wheel_radius * 1.15:
        v_axial = -6.5
        zone = "DOWNWARD"
    else:
        transition_factor = (r_test - wheel_radius * 0.93) / (wheel_radius * 0.22)
        v_axial = -1.0 - transition_factor * 5.5
        zone = "TRANSITION"

    print(f"  r={r_test:.3f}m: v_z={v_axial:+6.2f} m/s ({zone})")

print(f"\nFeed zone: r={0.30}-{0.40}m")
print(f"Expected: Particles should be in DOWNWARD zone → fall to bottom → coarse")
print(f"Problem: Feed zone is outside upward flow zone!")

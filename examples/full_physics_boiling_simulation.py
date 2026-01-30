"""
Full Physics Boiling Simulation
================================

This example demonstrates the complete multi-physics simulation including:
1. Realistic carrot geometry (rounds, sticks, or chunks)
2. Heat transfer during boiling
3. Thermal degradation of Vitamin A (Arrhenius kinetics)
4. Internal diffusion in food matrix (3D Fickian diffusion)
5. Surface leaching to water (mass transfer)

Physical Processes:
------------------
- Heat Transfer: Carrots heat from 20°C to 100°C
- Degradation: First-order thermal degradation (k = A·exp(-Ea/RT))
- Diffusion: 3D Fickian diffusion within food matrix (∂C/∂t = D·∇²C)
- Leaching: Mass transfer at food-water interface (J = k_m·ΔC)

Results:
--------
- Temperature profiles
- Vitamin A concentration gradients (surface vs. interior)
- Total retention vs. time
- Leaching losses vs. degradation losses
"""

import warp as wp
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cooking_sim.geometry.boiling import BoilingAssembly, SaucepanBuilder
from cooking_sim.geometry.boiling.config import create_standard_saucepan_config
from cooking_sim.visualization import GeometryVisualizer
from cooking_sim.physics.boiling import HeatTransferModel, MaterialDatabase
from cooking_sim.kinetics.boiling import VitaminAKinetics, VitaminAProperties


def create_assembly_with_geometry():
    """Create saucepan assembly with realistic carrot geometry"""
    print("=" * 80)
    print("STEP 1: Creating Geometry")
    print("=" * 80)

    # Create configuration
    config = create_standard_saucepan_config()
    config.num_food_pieces = 4
    config.food_type = "carrot"
    config.food.carrot_cut_type = "round"  # "round", "stick", or "chunk"

    # Increase internal grid resolution for better diffusion accuracy
    config.food.internal_resolution = (16, 16, 20)  # Higher resolution

    print(f"\nConfiguration:")
    print(f"  - Cut type: {config.food.carrot_cut_type}")
    print(f"  - Number of pieces: {config.num_food_pieces}")
    print(f"  - Internal grid resolution: {config.food.internal_resolution}")
    print(f"  - Carrot density: 1075 kg/m³ (SINKS in water)")

    # Build assembly
    assembly = SaucepanBuilder.create_from_config(config)

    print(f"\n✓ Assembly created: {list(assembly.components.keys())}")

    return assembly, config


def extract_food_grid_info(assembly, config, piece_index=0):
    """Extract grid information from food geometry for diffusion initialization"""
    print("\n" + "=" * 80)
    print(f"STEP 2: Extracting Grid Information from Food Geometry")
    print("=" * 80)

    # Get the food component
    food = assembly.get_component(f"carrot_piece_{piece_index}")
    if food is None:
        raise ValueError(f"Could not find carrot_piece_{piece_index}")

    # Get internal grid points
    grid_points = food.internal_grid_points.numpy()
    num_points = len(grid_points)

    print(f"\nFood piece: {food.name}")
    print(f"  - Internal grid points: {num_points}")
    print(f"  - Grid shape: {config.food.internal_resolution}")

    # Get grid dimensions
    nx, ny, nz = config.food.internal_resolution

    # Calculate grid spacing from actual geometry
    # Get bounding box of internal grid
    min_coords = np.min(grid_points, axis=0)
    max_coords = np.max(grid_points, axis=0)
    food_dimensions = max_coords - min_coords

    dx = food_dimensions[0] / (nx - 1) if nx > 1 else 0.001
    dy = food_dimensions[1] / (ny - 1) if ny > 1 else 0.001
    dz = food_dimensions[2] / (nz - 1) if nz > 1 else 0.001

    print(f"  - Food dimensions: {food_dimensions * 100} cm")
    print(f"  - Grid spacing: dx={dx*1000:.3f}mm, dy={dy*1000:.3f}mm, dz={dz*1000:.3f}mm")

    # Create grid indices (structured grid assumption)
    grid_indices = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                grid_indices.append([i, j, k])
    grid_indices = np.array(grid_indices[:num_points], dtype=np.int32)

    # Get mesh points for surface identification
    mesh_points = food.mesh.points.numpy() if food.mesh is not None else grid_points

    print(f"  - Mesh vertices: {len(mesh_points)}")
    print(f"\n✓ Grid information extracted")

    return {
        'grid_points': grid_points,
        'grid_indices': grid_indices,
        'mesh_points': mesh_points,
        'nx': nx, 'ny': ny, 'nz': nz,
        'dx': dx, 'dy': dy, 'dz': dz,
        'food_dimensions': food_dimensions,
        'num_points': num_points
    }


def setup_physics_with_diffusion(assembly, config, grid_info):
    """Set up complete physics simulation with diffusion"""
    print("\n" + "=" * 80)
    print("STEP 3: Initializing Multi-Physics Models")
    print("=" * 80)

    # Get components
    water = assembly.get_component("water")
    num_carrot_pieces = len([c for c in assembly.components.keys() if c.startswith("carrot_piece_")])

    # Initialize heat transfer model
    print("\n3.1 Heat Transfer Model:")
    heat_model = HeatTransferModel(
        water_properties=MaterialDatabase.WATER,
        food_properties=MaterialDatabase.CARROT,
        boiling_temperature=100.0,
        ambient_temperature=20.0
    )

    # For simplicity, use grid info from first piece for all pieces
    total_food_points = grid_info['num_points'] * num_carrot_pieces

    heat_model.initialize_temperatures(
        num_water_points=water.num_points,
        num_food_points=total_food_points
    )
    print(f"  - Water temperature: {heat_model.T_boiling}°C")
    print(f"  - Initial food temperature: {heat_model.T_ambient}°C")
    print(f"  - Total food grid points: {total_food_points}")

    # Initialize Vitamin A kinetics WITH diffusion enabled
    print("\n3.2 Vitamin A Kinetics (with diffusion and leaching):")
    vitamin_props = VitaminAProperties(
        initial_concentration=83.35,      # μg/g (realistic for carrots)
        activation_energy=80000,          # J/mol (from literature)
        diffusion_coefficient=2e-10       # m²/s (typical for nutrients in vegetables)
    )

    vitamin_model = VitaminAKinetics(
        properties=vitamin_props,
        enable_diffusion=True,            # ← Enable diffusion
        enable_leaching=True              # ← Enable surface leaching
    )

    vitamin_model.initialize_concentrations(
        num_food_points=total_food_points,
        num_water_points=water.num_points
    )

    print(f"  - Initial Vitamin A: {vitamin_props.initial_concentration} μg/g")
    print(f"  - Degradation Ea: {vitamin_props.activation_energy/1000:.1f} kJ/mol")
    print(f"  - Diffusion coefficient: {vitamin_props.diffusion_coefficient:.2e} m²/s")
    print(f"  - Diffusion: ENABLED ✓")
    print(f"  - Surface leaching: ENABLED ✓")

    # Initialize diffusion grid from geometry
    print("\n3.3 Initializing Diffusion Grid:")
    vitamin_model.initialize_diffusion_grid(
        grid_indices=grid_info['grid_indices'],
        grid_points=grid_info['grid_points'],
        mesh_points=grid_info['mesh_points'],
        nx=grid_info['nx'],
        ny=grid_info['ny'],
        nz=grid_info['nz'],
        food_dimensions=grid_info['food_dimensions']
    )

    # Check stability
    dt_test = 1.0
    stable = vitamin_model.diffusion_model.check_stability(dt_test)
    dt_max = min(grid_info['dx'], grid_info['dy'], grid_info['dz'])**2 / (6.0 * vitamin_props.diffusion_coefficient)

    print(f"  - Grid initialized: {grid_info['nx']}×{grid_info['ny']}×{grid_info['nz']}")
    print(f"  - CFL stability: dt_max = {dt_max:.3f}s")

    # Surface points are stored in VitaminAKinetics, not NutrientDiffusion
    if vitamin_model.is_surface_point is not None:
        print(f"  - Surface points identified: {np.sum(vitamin_model.is_surface_point.numpy())} points")

    print(f"\n✓ Multi-physics models initialized")

    return heat_model, vitamin_model


def run_full_physics_simulation(heat_model, vitamin_model, grid_info, duration=600):
    """Run complete multi-physics simulation"""
    print("\n" + "=" * 80)
    print(f"STEP 4: Running Full Physics Simulation ({duration}s)")
    print("=" * 80)

    # Simulation parameters
    dt = 1.0  # 1 second time steps
    num_steps = int(duration / dt)
    num_points = grid_info['num_points']

    # Mass transfer coefficient (literature values: 1e-6 to 1e-4 m/s)
    k_mass_transfer = 5e-5  # m/s

    print(f"\nSimulation parameters:")
    print(f"  - Time step: {dt}s")
    print(f"  - Total steps: {num_steps}")
    print(f"  - Duration: {duration/60:.1f} minutes")
    print(f"  - Mass transfer coeff: {k_mass_transfer:.2e} m/s")

    # Storage for results
    times = []
    retention_history = []
    surface_conc_history = []
    interior_conc_history = []
    temp_history = []
    leaching_loss_history = []

    print("\nSimulation progress:")
    print("-" * 80)

    for step in range(num_steps):
        current_time = step * dt

        # Update temperature (simplified exponential approach to boiling)
        if heat_model.food_temperature is not None:
            food_temps = heat_model.food_temperature.numpy()
            tau = 120.0  # time constant (s) for heating
            food_temps += (heat_model.T_boiling - food_temps) * (1 - np.exp(-dt/tau))
            heat_model.food_temperature = wp.array(food_temps, dtype=float)

        # Update rate constants based on temperature
        vitamin_model.update_rate_constants(heat_model.food_temperature)

        # Full multi-physics step: degradation + diffusion + leaching
        vitamin_model.step_full(
            dt=dt,
            num_points=num_points,
            mass_transfer_coeff=k_mass_transfer
        )

        # Record data every 30 seconds
        if step % 30 == 0:
            stats = vitamin_model.get_statistics()
            retention = stats.get('retention_%', 100.0)
            avg_temp = np.mean(heat_model.food_temperature.numpy())

            # Get concentration profile
            conc = vitamin_model.food_concentration.numpy()[:num_points]

            # Identify surface vs. interior points (stored in VitaminAKinetics)
            if vitamin_model.is_surface_point is not None:
                is_surface = vitamin_model.is_surface_point.numpy()[:num_points]
                surface_conc = np.mean(conc[is_surface == 1]) if np.any(is_surface) else np.mean(conc)
                interior_conc = np.mean(conc[is_surface == 0]) if np.any(is_surface == 0) else np.mean(conc)
            else:
                surface_conc = np.mean(conc)
                interior_conc = np.mean(conc)

            times.append(current_time)
            retention_history.append(retention)
            surface_conc_history.append(surface_conc)
            interior_conc_history.append(interior_conc)
            temp_history.append(avg_temp)

            # Calculate cumulative leaching loss (difference from interior)
            leaching_loss = ((interior_conc - surface_conc) / vitamin_model.props.initial_concentration) * 100
            leaching_loss_history.append(leaching_loss)

            if step % 60 == 0:  # Print every 60 seconds
                print(f"  t={current_time:4.0f}s: T={avg_temp:5.1f}°C | "
                      f"Retention={retention:5.1f}% | "
                      f"Surface={surface_conc:5.1f} μg/g | "
                      f"Interior={interior_conc:5.1f} μg/g | "
                      f"Leaching loss={leaching_loss:4.1f}%")

    print("-" * 80)
    print("✓ Simulation complete")

    return {
        'times': np.array(times),
        'retention': np.array(retention_history),
        'surface_conc': np.array(surface_conc_history),
        'interior_conc': np.array(interior_conc_history),
        'temperature': np.array(temp_history),
        'leaching_loss': np.array(leaching_loss_history)
    }


def plot_comprehensive_results(results, vitamin_model, grid_info, assembly):
    """Plot comprehensive multi-physics results with enhanced visualization"""
    print("\n" + "=" * 80)
    print("STEP 5: Visualizing Results")
    print("=" * 80)

    fig = plt.figure(figsize=(18, 10))
    times_min = results['times'] / 60

    # Plot 1: 3D concentration with complete assembly geometry
    ax_3d = plt.subplot(2, 3, 1, projection='3d')
    ax_3d.set_title('Final Concentration Distribution\n(Complete Assembly: Saucepan + Water + Carrot)', fontsize=11, fontweight='bold')
    ax_3d.set_xlabel('X (cm)', fontsize=9)
    ax_3d.set_ylabel('Y (cm)', fontsize=9)
    ax_3d.set_zlabel('Z (cm)', fontsize=9)

    # Render assembled geometry
    for comp_name in assembly.components.keys():
        comp = assembly.get_component(comp_name)
        if comp and comp.mesh:
            mesh_pts = comp.mesh.points.numpy() * 100  # Convert to cm
            mesh_indices = comp.mesh.indices.numpy().reshape(-1, 3)

            if comp_name == "saucepan_body":
                ax_3d.plot_trisurf(mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                                   triangles=mesh_indices, alpha=0.2, color='gray', linewidth=0, shade=True)
            elif comp_name == "water":
                ax_3d.plot_trisurf(mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                                   triangles=mesh_indices, alpha=0.2, color='cyan', linewidth=0, shade=True)
            elif comp_name == "lid":
                ax_3d.plot_trisurf(mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                                   triangles=mesh_indices, alpha=0.3, color='darkgray', linewidth=0, shade=True)
            elif comp_name.startswith("carrot_piece_"):
                # Color carrot based on final retention
                grid_points = grid_info['grid_points']
                final_conc = vitamin_model.food_concentration.numpy()[:grid_info['num_points']]
                avg_conc = np.mean(final_conc)
                retention_ratio = avg_conc / vitamin_model.props.initial_concentration

                # Use kinetic color mapping
                if retention_ratio >= 0.90:
                    r, g, b = 1.0, 0.5, 0.0
                elif retention_ratio >= 0.75:
                    t = (retention_ratio - 0.75) / 0.15
                    r, g, b = 1.0, 0.5 + 0.1 * (1 - t), 0.0 + 0.1 * (1 - t)
                elif retention_ratio >= 0.60:
                    t = (retention_ratio - 0.60) / 0.15
                    r, g, b = 1.0 - 0.1 * (1 - t), 0.6 + 0.1 * t, 0.1 + 0.2 * (1 - t)
                else:
                    t = (retention_ratio - 0.40) / 0.20 if retention_ratio >= 0.40 else 0
                    r, g, b = 0.9 - 0.1 * (1 - t), 0.7, 0.3 + 0.2 * (1 - t)

                ax_3d.plot_trisurf(mesh_pts[:, 0], mesh_pts[:, 1], mesh_pts[:, 2],
                                   triangles=mesh_indices, alpha=0.5, color=(r, g, b), linewidth=0, shade=True)

    # Concentration scatter overlay
    grid_points = grid_info['grid_points']
    final_conc = vitamin_model.food_concentration.numpy()[:grid_info['num_points']]
    scatter = ax_3d.scatter(grid_points[:, 0] * 100, grid_points[:, 1] * 100, grid_points[:, 2] * 100,
                           c=final_conc, cmap='RdYlGn', s=50, alpha=1.0,
                           vmin=min(final_conc) - 2, vmax=max(final_conc) + 2,
                           edgecolors='black', linewidths=0.5, depthshade=True)
    colorbar = plt.colorbar(scatter, ax=ax_3d, shrink=0.6, pad=0.1)
    colorbar.set_label('Vitamin A (μg/g)', fontsize=9)
    ax_3d.view_init(elev=25, azim=45)

    # Plot 2: Temperature profile
    ax_temp = plt.subplot(2, 3, 2)
    ax_temp.plot(times_min, results['temperature'], 'r-', linewidth=2.5, label='Carrot Temp')
    ax_temp.axhline(100, color='b', linestyle='--', alpha=0.6, linewidth=1.5, label='Water (Boiling)')
    ax_temp.axhline(20, color='gray', linestyle=':', alpha=0.5, label='Initial')
    ax_temp.set_xlabel('Time (minutes)', fontsize=9)
    ax_temp.set_ylabel('Temperature (°C)', fontsize=9)
    ax_temp.set_title('Temperature Evolution\n(Heat Transfer Physics)', fontsize=11, fontweight='bold')
    ax_temp.grid(True, alpha=0.3)
    ax_temp.legend(fontsize=8, loc='lower right')
    ax_temp.text(0.02, 0.98, 'Exponential heating\nτ ≈ 120s',
                transform=ax_temp.transAxes, fontsize=8,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Plot 3: Vitamin A retention with dynamic Y-axis
    ax_retention = plt.subplot(2, 3, 3)
    ax_retention.plot(times_min, results['retention'], 'g-', linewidth=2.5, label='Total Retention')
    ax_retention.axhline(100, color='k', linestyle='--', alpha=0.4, label='Initial (100%)')
    ax_retention.set_xlabel('Time (minutes)', fontsize=9)
    ax_retention.set_ylabel('Retention (%)', fontsize=9)
    ax_retention.set_title('Vitamin A Retention\n(Degradation + Leaching Kinetics)', fontsize=11, fontweight='bold')
    ax_retention.grid(True, alpha=0.3)
    ax_retention.legend(fontsize=8)
    min_ret = min(results['retention'])
    ax_retention.set_ylim([min(70, min_ret - 2), 102])
    ax_retention.text(0.02, 0.02, f'Ea = {vitamin_model.props.activation_energy/1000:.0f} kJ/mol\nk = k₀·exp(-Ea/RT)',
                     transform=ax_retention.transAxes, fontsize=7,
                     verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

    # Plot 4: Concentration gradient with dynamic Y-axis
    ax_gradient = plt.subplot(2, 3, 4)
    ax_gradient.plot(times_min, results['surface_conc'], 'b-', linewidth=2.5, label='Surface', marker='o', markersize=2, markevery=10)
    ax_gradient.plot(times_min, results['interior_conc'], 'r-', linewidth=2.5, label='Interior', marker='s', markersize=2, markevery=10)
    ax_gradient.axhline(vitamin_model.props.initial_concentration, color='k', linestyle='--', alpha=0.5, label='Initial')
    ax_gradient.set_xlabel('Time (minutes)', fontsize=9)
    ax_gradient.set_ylabel('Concentration (μg/g)', fontsize=9)
    ax_gradient.set_title('Surface vs. Interior Concentration\n(Diffusion + Leaching)', fontsize=11, fontweight='bold')
    ax_gradient.grid(True, alpha=0.3)
    ax_gradient.legend(fontsize=8, loc='upper right')
    all_conc = list(results['surface_conc']) + list(results['interior_conc'])
    min_conc, max_conc = min(all_conc), max(all_conc)
    padding = (max_conc - min_conc) * 0.05 if max_conc > min_conc else 2.0
    ax_gradient.set_ylim([min_conc - padding, max_conc + padding])
    ax_gradient.text(0.02, 0.02, f'D = {vitamin_model.props.diffusion_coefficient:.1e} m²/s\nLeaching to water',
                    transform=ax_gradient.transAxes, fontsize=7,
                    verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))

    # Plot 5: Loss breakdown pie chart
    ax_pie = plt.subplot(2, 3, 5)
    final_retention = results['retention'][-1]
    final_leaching = results['leaching_loss'][-1]
    degradation_loss = 100 - final_retention - final_leaching

    losses = [degradation_loss, final_leaching, final_retention]
    labels = ['Thermal\nDegradation', 'Surface\nLeaching', 'Retained']
    colors = ['#ff6b6b', '#ffa726', '#4CAF50']
    explode = (0.05, 0.05, 0)

    ax_pie.pie(losses, labels=labels, colors=colors, autopct='%1.1f%%', explode=explode,
              startangle=90, textprops={'fontsize': 9, 'weight': 'bold'})
    ax_pie.set_title(f'Final Nutrient Balance\n(Total Loss: {100-final_retention:.1f}%)',
                    fontsize=11, fontweight='bold')

    # Plot 6: Radial concentration profile
    ax_profile = plt.subplot(2, 3, 6)
    center = np.mean(grid_points, axis=0)
    distances = np.linalg.norm(grid_points - center, axis=1) * 1000  # mm
    sorted_indices = np.argsort(distances)
    sorted_dist = distances[sorted_indices]
    sorted_conc = final_conc[sorted_indices]

    # Bin and average
    n_bins = 15
    bin_edges = np.linspace(0, sorted_dist.max(), n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_means = []
    for i in range(n_bins):
        mask = (sorted_dist >= bin_edges[i]) & (sorted_dist < bin_edges[i+1])
        if np.any(mask):
            bin_means.append(np.mean(sorted_conc[mask]))
        else:
            bin_means.append(np.nan)

    ax_profile.plot(bin_centers, bin_means, 'o-', linewidth=2, markersize=4, color='darkgreen', label='Final Profile')
    ax_profile.set_xlabel('Radial Distance from Center (mm)', fontsize=9)
    ax_profile.set_ylabel('Concentration (μg/g)', fontsize=9)
    ax_profile.set_title('Radial Concentration Profile\n(Final State)', fontsize=11, fontweight='bold')
    ax_profile.grid(True, alpha=0.3)
    ax_profile.legend(fontsize=8)
    ax_profile.set_xlim([0, sorted_dist.max() * 1.1])

    plt.tight_layout()
    plt.savefig('output/full_physics_boiling_results.png', dpi=150, bbox_inches='tight')
    print("\n✓ Results saved to: output/full_physics_boiling_results.png")

    # Print summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nBoiling duration: {results['times'][-1]/60:.1f} minutes")
    print(f"Final temperature: {results['temperature'][-1]:.1f}°C")
    print(f"\nVitamin A Analysis:")
    print(f"  - Initial concentration: {vitamin_model.props.initial_concentration:.2f} μg/g")
    print(f"  - Final surface concentration: {results['surface_conc'][-1]:.2f} μg/g")
    print(f"  - Final interior concentration: {results['interior_conc'][-1]:.2f} μg/g")
    print(f"  - Concentration gradient: {results['interior_conc'][-1] - results['surface_conc'][-1]:.2f} μg/g")
    print(f"\nLosses:")
    print(f"  - Total retention: {final_retention:.1f}%")
    print(f"  - Total loss: {100 - final_retention:.1f}%")
    print(f"    • Thermal degradation: {degradation_loss:.1f}%")
    print(f"    • Surface leaching: {final_leaching:.1f}%")
    print(f"\nPhysics enabled:")
    print(f"  ✓ Heat transfer")
    print(f"  ✓ Thermal degradation (Arrhenius kinetics)")
    print(f"  ✓ Internal diffusion (3D Fickian)")
    print(f"  ✓ Surface leaching (mass transfer)")
    print("=" * 80)

    plt.show()


def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("FULL PHYSICS BOILING SIMULATION")
    print("Multi-physics modeling: Heat + Degradation + Diffusion + Leaching")
    print("=" * 80)

    # Initialize Warp
    wp.init()
    print(f"\nWarp initialized: {wp.get_device()}")

    # Create output directory
    os.makedirs('output', exist_ok=True)

    # Step 1: Create geometry
    assembly, config = create_assembly_with_geometry()

    # Step 2: Extract grid information from food geometry
    grid_info = extract_food_grid_info(assembly, config, piece_index=0)

    # Step 3: Set up complete physics with diffusion
    heat_model, vitamin_model = setup_physics_with_diffusion(assembly, config, grid_info)

    # Step 4: Run full physics simulation
    results = run_full_physics_simulation(
        heat_model,
        vitamin_model,
        grid_info,
        duration=600  # 10 minutes
    )

    # Step 5: Visualize comprehensive results
    plot_comprehensive_results(results, vitamin_model, grid_info, assembly)

    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

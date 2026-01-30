"""
Example: Boiling carrot simulation with Vitamin A tracking

This example demonstrates:
1. Building saucepan geometry with components
2. Adding carrot pieces to the assembly
3. Visualizing the geometry
4. Simulating heat transfer during boiling
5. Tracking Vitamin A degradation and retention
"""

import warp as wp
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cooking_sim.geometry.boiling import BoilingAssembly, SaucepanBuilder
from cooking_sim.geometry.boiling.config import BoilingConfig, create_standard_saucepan_config
from cooking_sim.visualization import GeometryVisualizer
from cooking_sim.physics.boiling import HeatTransferModel, MaterialDatabase
from cooking_sim.kinetics.boiling import VitaminAKinetics, VitaminAProperties


def create_saucepan_with_carrot():
    """Create a saucepan assembly with carrot pieces"""
    print("=" * 60)
    print("Creating Saucepan Geometry")
    print("=" * 60)

    # Step 1: Create configuration with realistic carrot properties
    print("\n1. Creating configuration...")
    config = create_standard_saucepan_config()

    # Configure realistic carrot cuts
    config.num_food_pieces = 5  # Typical portion size
    config.food_type = "carrot"
    config.food.carrot_cut_type = "round"  # "round" (coins), "stick" (batons), or "chunk"

    print(f"\n   Carrot configuration:")
    print(f"   - Cut type: {config.food.carrot_cut_type}")
    print(f"   - Number of pieces: {config.num_food_pieces}")
    print(f"   - Density: 1075 kg/m³ (will SINK in water)")

    # Print configuration summary
    print(config.summary())

    # Step 2: Build assembly from configuration (all components added automatically)
    print("\n2. Building assembly from configuration...")
    assembly = SaucepanBuilder.create_from_config(config)
    print(f"   Created assembly: {assembly}")
    print(f"   Components: {list(assembly.components.keys())}")

    # Show physical behavior
    print(f"\n3. Physical behavior:")
    print(f"   - Carrots sink due to density > water (1075 vs 1000 kg/m³)")
    print(f"   - Pieces rest on saucepan bottom")
    print(f"   - Fully submerged in water")

    # Get assembly bounds
    bounds = assembly.get_bounds()
    print(f"\n4. Assembly bounds:")
    print(f"   Min: {bounds[0]}")
    print(f"   Max: {bounds[1]}")

    return assembly


def visualize_geometry(assembly):
    """Visualize the assembly geometry"""
    print("\n" + "=" * 60)
    print("Visualizing Geometry")
    print("=" * 60)

    visualizer = GeometryVisualizer(window_size=(1600, 1200))

    print("\n1. Generating 3D visualization...")
    visualizer.visualize_assembly(
        assembly=assembly,
        show_grid_points=True,
        save_path="output/boiling_carrot_geometry.png",
        camera_position='iso'
    )


def setup_physics_simulation(assembly):
    """Set up physics simulation"""
    print("\n" + "=" * 60)
    print("Setting Up Physics Simulation")
    print("=" * 60)

    # Get components
    water = assembly.get_component("water")
    carrot_0 = assembly.get_component("carrot_piece_0")

    if water is None or carrot_0 is None:
        print("Error: Missing components")
        return None, None

    print(f"\n1. Water domain: {water.num_points} grid points")
    print(f"2. Carrot piece: {carrot_0.num_internal_points} internal grid points")

    # Initialize heat transfer model
    print("\n3. Initializing heat transfer model...")
    heat_model = HeatTransferModel(
        water_properties=MaterialDatabase.WATER,
        food_properties=MaterialDatabase.CARROT,
        boiling_temperature=100.0,
        ambient_temperature=20.0
    )

    # Count food pieces dynamically
    num_carrot_pieces = len([c for c in assembly.components.keys() if c.startswith("carrot_piece_")])

    # Initialize temperatures
    total_food_points = sum(
        assembly.get_component(f"carrot_piece_{i}").num_internal_points
        for i in range(num_carrot_pieces)
    )

    heat_model.initialize_temperatures(
        num_water_points=water.num_points,
        num_food_points=total_food_points
    )
    print(f"   Water temperature: {heat_model.T_boiling}°C")
    print(f"   Initial food temperature: {heat_model.T_ambient}°C")

    # Initialize Vitamin A kinetics
    print("\n4. Initializing Vitamin A kinetics...")
    vitamin_props = VitaminAProperties(
        initial_concentration=83.35,  # μg/g (realistic for carrots)
        activation_energy=80000,      # J/mol
        diffusion_coefficient=1e-10   # m²/s
    )

    vitamin_model = VitaminAKinetics(properties=vitamin_props)
    vitamin_model.initialize_concentrations(
        num_food_points=total_food_points,
        num_water_points=water.num_points
    )

    print(f"   Initial Vitamin A: {vitamin_props.initial_concentration} μg/g")
    print(f"   Degradation activation energy: {vitamin_props.activation_energy/1000:.1f} kJ/mol")

    return heat_model, vitamin_model


def run_simulation(heat_model, vitamin_model, duration=600):
    """Run the boiling simulation"""
    print("\n" + "=" * 60)
    print(f"Running Simulation ({duration}s boiling time)")
    print("=" * 60)

    # Simulation parameters
    dt = 1.0  # 1 second time steps
    num_steps = int(duration / dt)

    print(f"\n1. Time step: {dt}s")
    print(f"2. Total steps: {num_steps}")
    print(f"3. Total simulation time: {duration}s ({duration/60:.1f} minutes)")

    # Storage for results
    times = []
    retention_history = []
    temp_history = []

    print("\n4. Simulation progress:")

    for step in range(num_steps):
        current_time = step * dt

        # Update temperature (simplified - food gradually heats up)
        if heat_model.food_temperature is not None:
            food_temps = heat_model.food_temperature.numpy()

            # Simple exponential approach to boiling temperature
            tau = 120.0  # time constant (s) for heating
            food_temps += (heat_model.T_boiling - food_temps) * (1 - np.exp(-dt/tau))

            heat_model.food_temperature = wp.array(food_temps, dtype=float)

        # Update degradation rate constants based on current temperature
        vitamin_model.update_rate_constants(heat_model.food_temperature)

        # Step degradation kinetics
        num_food_points = len(heat_model.food_temperature.numpy())
        vitamin_model.step_degradation(dt, num_food_points)

        # Record data every 30 seconds
        if step % 30 == 0:
            stats = vitamin_model.get_statistics()
            retention = stats.get('retention_%', 100.0)
            avg_temp = np.mean(heat_model.food_temperature.numpy())

            times.append(current_time)
            retention_history.append(retention)
            temp_history.append(avg_temp)

            print(f"   t={current_time:4.0f}s: Temp={avg_temp:5.1f}°C, "
                  f"Vitamin A retention={retention:5.1f}%")

    print("\n5. Simulation complete!")

    return times, retention_history, temp_history


def plot_results(times, retention_history, temp_history):
    """Plot simulation results"""
    print("\n" + "=" * 60)
    print("Plotting Results")
    print("=" * 60)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot temperature profile
    ax1.plot(np.array(times)/60, temp_history, 'r-', linewidth=2, label='Average Temperature')
    ax1.axhline(100, color='k', linestyle='--', alpha=0.5, label='Boiling Point')
    ax1.set_xlabel('Time (minutes)', fontsize=12)
    ax1.set_ylabel('Temperature (°C)', fontsize=12)
    ax1.set_title('Carrot Temperature During Boiling', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)

    # Plot Vitamin A retention
    ax2.plot(np.array(times)/60, retention_history, 'g-', linewidth=2, label='Vitamin A Retention')
    ax2.set_xlabel('Time (minutes)', fontsize=12)
    ax2.set_ylabel('Retention (%)', fontsize=12)
    ax2.set_title('Vitamin A Retention During Boiling', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    ax2.set_ylim([0, 105])

    plt.tight_layout()
    plt.savefig('output/boiling_carrot_results.png', dpi=150, bbox_inches='tight')
    print("\n1. Results saved to: output/boiling_carrot_results.png")

    # Print final summary
    print("\n2. Final Results:")
    print(f"   Boiling duration: {times[-1]/60:.1f} minutes")
    print(f"   Final temperature: {temp_history[-1]:.1f}°C")
    print(f"   Final Vitamin A retention: {retention_history[-1]:.1f}%")
    print(f"   Vitamin A loss: {100 - retention_history[-1]:.1f}%")

    plt.show()


def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("CARROT BOILING SIMULATION")
    print("Modeling heat transfer and Vitamin A degradation")
    print("=" * 60)

    # Initialize Warp
    wp.init()
    print(f"\nWarp initialized: {wp.get_device()}")

    # Create output directory
    os.makedirs('output', exist_ok=True)

    # Step 1: Create geometry
    assembly = create_saucepan_with_carrot()

    # Step 2: Visualize geometry
    visualize_geometry(assembly)

    # Step 3: Set up physics
    heat_model, vitamin_model = setup_physics_simulation(assembly)

    if heat_model is None or vitamin_model is None:
        print("\nError: Could not initialize physics models")
        return

    # Step 4: Run simulation (10 minutes of boiling)
    times, retention_history, temp_history = run_simulation(
        heat_model,
        vitamin_model,
        duration=600  # 10 minutes
    )

    # Step 5: Plot results
    plot_results(times, retention_history, temp_history)

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

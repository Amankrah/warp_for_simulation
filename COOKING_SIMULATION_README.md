# Cooking Process Simulation

A physics-based simulation framework for modeling cooking processes and their effects on nutrient retention using NVIDIA Warp.

## Overview

This project models various cooking processes (boiling, frying, microwaving, etc.) and simulates their effects on nutrients in food. The framework combines:

- **Geometry modeling**: Build and visualize cooking vessels and food items
- **Heat transfer physics**: Simulate conduction, convection, and boiling
- **Nutrient kinetics**: Track degradation and leaching of nutrients

## Project Structure

```
cooking_sim/
├── geometry/
│   └── boiling/
│       ├── components/          # Geometric components
│       │   ├── base.py          # Base component class
│       │   ├── cylinder.py      # Saucepan body
│       │   ├── lid.py           # Lid component
│       │   ├── liquid_domain.py # Water domain grid
│       │   └── food_object.py   # Food geometry (carrot, etc.)
│       └── assembly.py          # Assembly system
│
├── physics/
│   └── boiling/
│       ├── heat_transfer.py     # Heat transfer model
│       └── convection.py        # Convection model
│
├── kinetics/
│   └── boiling/
│       ├── vitamin_a_kinetics.py # Vitamin A degradation
│       └── diffusion_model.py    # Diffusion model
│
└── visualization/
    └── geometry_visualizer.py   # 3D visualization
```

## Current Implementation: Boiling Carrots

The first implementation focuses on **boiling carrots** and tracking **Vitamin A** (β-carotene) retention.

### Features

1. **Geometry Components**:
   - Cylindrical saucepan with walls and bottom
   - Optional lid
   - Liquid (water) domain with 3D grid
   - Food objects (carrot pieces) with internal grids

2. **Physics Models**:
   - Heat transfer via conduction
   - Convective heat transfer at food-water interface
   - Temperature-dependent material properties

3. **Nutrient Kinetics**:
   - First-order thermal degradation: `dC/dt = -k(T)·C`
   - Arrhenius temperature dependence: `k = A·exp(-Ea/RT)`
   - Diffusion within food matrix
   - Leaching to water (partition coefficient)

### Material Properties

**Water (at 100°C)**:
- Thermal conductivity: 0.6 W/(m·K)
- Specific heat: 4186 J/(kg·K)
- Density: 958.4 kg/m³

**Carrot**:
- Thermal conductivity: 0.55 W/(m·K)
- Specific heat: 3850 J/(kg·K)
- Density: 1030 kg/m³

**Vitamin A (β-carotene)**:
- Initial concentration: 83.35 μg/g fresh weight
- Activation energy: 80 kJ/mol
- Diffusion coefficient: 1×10⁻¹⁰ m²/s

## Quick Start

### Installation

```bash
# Ensure NVIDIA Warp is installed
pip install warp-lang matplotlib numpy
```

### Run Example

```bash
python examples/boiling_carrot_example.py
```

### Expected Output

The example will:
1. Create a saucepan geometry with 3 carrot pieces
2. Visualize the 3D geometry
3. Simulate 10 minutes of boiling
4. Track temperature rise and Vitamin A degradation
5. Generate plots showing:
   - Temperature profile over time
   - Vitamin A retention percentage

**Output files**:
- `output/boiling_carrot_geometry.png` - 3D visualization of geometry
- `output/boiling_carrot_results.png` - Simulation results

## Example Usage

### Create Custom Saucepan

```python
from cooking_sim.geometry.boiling import SaucepanBuilder

# Create saucepan
assembly = SaucepanBuilder.create_standard_saucepan(
    radius=0.10,         # 10 cm inner radius
    height=0.15,         # 15 cm height
    wall_thickness=0.003, # 3 mm wall
    water_level=0.10,    # 10 cm water level
    with_lid=True
)

# Add food
assembly = SaucepanBuilder.add_food_items(
    assembly=assembly,
    food_type="carrot",
    num_pieces=5,
    piece_dimensions=(0.015, 0.015, 0.04)  # radius, radius, height
)
```

### Visualize Geometry

```python
from cooking_sim.visualization import GeometryVisualizer

visualizer = GeometryVisualizer()
visualizer.visualize_assembly(
    assembly=assembly,
    show_grid_points=True,
    save_path="my_geometry.png"
)
```

### Run Physics Simulation

```python
from cooking_sim.physics.boiling import HeatTransferModel, MaterialDatabase
from cooking_sim.kinetics.boiling import VitaminAKinetics

# Set up heat transfer
heat_model = HeatTransferModel(
    water_properties=MaterialDatabase.WATER,
    food_properties=MaterialDatabase.CARROT,
    boiling_temperature=100.0
)

# Set up nutrient kinetics
vitamin_model = VitaminAKinetics()

# Initialize
heat_model.initialize_temperatures(num_water_points, num_food_points)
vitamin_model.initialize_concentrations(num_food_points, num_water_points)

# Simulate
for step in range(num_steps):
    vitamin_model.update_rate_constants(heat_model.food_temperature)
    vitamin_model.step_degradation(dt, num_food_points)
```

## Scientific Background

### Heat Transfer Model

The simulation uses the heat diffusion equation:

```
∂T/∂t = α·∇²T
```

where α = k/(ρ·cp) is the thermal diffusivity.

**Boundary conditions**:
- Convective heat transfer at food-water interface: `q = h(T_water - T_surface)`
- Typical h for boiling water: 500-10000 W/(m²·K)

### Vitamin A Degradation

Thermal degradation follows first-order kinetics:

```
dC/dt = -k(T)·C
```

with temperature-dependent rate constant:

```
k(T) = A·exp(-Ea/(R·T))
```

**Literature values**:
- Activation energy: 50-120 kJ/mol for carotenoids
- Retention after 10 min boiling: typically 70-90%

## Extending the Framework

### Add New Cooking Processes

To add a new cooking process (e.g., frying):

1. Create geometry components:
   ```
   cooking_sim/geometry/frying/components/
   ```

2. Create physics models:
   ```
   cooking_sim/physics/frying/
   ```

3. Create kinetics models:
   ```
   cooking_sim/kinetics/frying/
   ```

### Add New Nutrients

To track a different nutrient:

1. Create nutrient properties dataclass
2. Implement degradation kinetics
3. Define diffusion coefficients
4. Add partition coefficients for leaching

### Add New Food Items

Create new food object with:
- Geometry (shape, dimensions)
- Material properties
- Initial nutrient concentrations

## Validation

The model predictions should be validated against:
- Experimental temperature measurements
- Published nutrient retention data
- Literature on cooking kinetics

**Reference retention values** (approximate):
- Vitamin A in boiled carrots: 70-90% retention after 10 minutes
- Higher losses with longer cooking times
- Losses due to both thermal degradation and leaching

## Future Enhancements

- [ ] Full 3D heat conduction with neighbor lookup
- [ ] Coupled heat-mass transfer
- [ ] Multi-nutrient tracking
- [ ] Frying process (oil medium)
- [ ] Microwave heating (volumetric heating)
- [ ] Texture changes (starch gelatinization)
- [ ] Color changes (Maillard reactions)
- [ ] Validation against experimental data

## References

1. Thermal properties of foods (ASHRAE Handbook)
2. Carotenoid degradation kinetics (Food Chemistry literature)
3. Heat transfer in food processing (Singh & Heldman)
4. Nutrient retention in cooking (USDA database)

## License

This project is part of the Warp simulation framework.

---

**Contact**: For questions or contributions, see main README.md

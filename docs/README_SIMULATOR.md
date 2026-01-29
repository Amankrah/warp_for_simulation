# Air Classifier Simulator - Architecture

## Directory Structure

```
air_classifier/
├── geometry/              # Geometry construction
│   ├── components/       # Individual component builders
│   ├── assembly.py       # Geometry assembly
│   └── corrected_config.py
│
├── physics/              # Physics modeling (NEW)
│   ├── __init__.py
│   ├── particle_dynamics.py  # Forces and motion
│   ├── air_flow.py           # Air velocity field
│   ├── collisions.py         # Collision detection
│   └── separation.py         # Separation mechanism
│
├── warp_integration.py   # WARP mesh conversion (MOVED from geometry/)
├── particle_properties.py # Particle material properties (NEW)
├── classifier_simulator.py # Main simulator (NEW)
└── config.py             # Configuration
```

## Key Components

### 1. Particle Properties (`particle_properties.py`)

Defines material properties for:
- **Protein particles**: Small (5-15 μm), density 1350 kg/m³
- **Starch particles**: Large (20-40 μm), density 1520 kg/m³
- **Feed composition**: Yellow pea flour composition
- **Air properties**: Standard air at 20°C

**Usage:**
```python
from air_classifier.particle_properties import (
    PROTEIN_PROPERTIES,
    STARCH_PROPERTIES,
    create_particle_mixture
)

diameters, densities, types = create_particle_mixture(1000)
```

### 2. Physics Modeling (`physics/`)

#### Particle Dynamics (`particle_dynamics.py`)
- Drag force computation (Stokes + turbulent)
- Centrifugal force near selector rotor
- Gravity
- Motion integration

#### Air Flow (`air_flow.py`)
- Air velocity field computation
- Swirl from tangential inlets
- Upward flow from air inlets
- Rotor-induced flow

#### Collisions (`collisions.py`)
- Boundary collision detection
- Outlet collection detection
- Collision response (restitution)

#### Separation (`separation.py`)
- Particle classification (fines/coarse)
- Force balance model
- Cut size-based separation

### 3. WARP Integration (`warp_integration.py`)

**Moved from `geometry/` to `air_classifier/`**

Functions:
- `create_warp_mesh_from_pyvista()` - Convert PyVista to WARP
- `create_boundary_meshes()` - Convert all geometry components
- `create_boundary_conditions()` - Generate BC parameters
- `load_geometry_from_stl_directory()` - Load STL files

### 4. Main Simulator (`classifier_simulator.py`)

**Brings everything together**

**Usage:**
```python
from air_classifier.classifier_simulator import AirClassifierSimulator

# Create simulator
sim = AirClassifierSimulator()

# Run simulation
sim.run(duration=1.0)

# Get results
results = sim.analyze_separation()
print(f"Fines collected: {results['fines_count']}")
print(f"Protein in fines: {results['fines_protein_fraction']*100:.1f}%")
```

## Simulation Workflow

1. **Initialize**: Build geometry, create boundary meshes, initialize particles
2. **Time Step Loop**:
   - Compute air velocity field
   - Compute forces (drag, gravity, centrifugal)
   - Update particle motion
   - Handle collisions
   - Check outlet collection
3. **Analysis**: Analyze separation performance

## Example Usage

```python
from air_classifier.classifier_simulator import AirClassifierSimulator, SimulationConfig

# Custom simulation config
sim_config = SimulationConfig(
    num_particles=2000,
    duration=2.0,
    dt=0.0005,  # 0.5 ms
    device="cuda:0"
)

# Create and run simulator
sim = AirClassifierSimulator(sim_config=sim_config)
sim.run()

# Analyze results
results = sim.analyze_separation()
print(results)
```

## Next Steps

1. ✅ Geometry construction
2. ✅ Particle properties
3. ✅ Physics modeling
4. ✅ Main simulator
5. → Enhanced collision detection with WARP meshes
6. → Improved air flow field (CFD or analytical)
7. → Particle-particle interactions
8. → Visualization and analysis tools
9. → Parameter optimization

## File Locations

- **WARP Integration**: `air_classifier/warp_integration.py` (moved from `geometry/`)
- **Particle Properties**: `air_classifier/particle_properties.py` (new)
- **Physics Models**: `air_classifier/physics/` (new folder)
- **Main Simulator**: `air_classifier/classifier_simulator.py` (new)

## Import Updates

All imports have been updated:
- `from air_classifier.warp_integration import ...` (was `geometry.warp_integration`)
- `from air_classifier.particle_properties import ...` (new)
- `from air_classifier.physics import ...` (new)
- `from air_classifier.classifier_simulator import AirClassifierSimulator` (new)

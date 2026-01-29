# Air Classifier Simulation - Modular Architecture

GPU-accelerated simulation of industrial turbine-type air classifier for yellow pea protein separation using NVIDIA Warp.

## 📁 Module Structure

```
air_classifier/
├── config.py           # Operating & simulation parameters
├── geometry.py         # 3D geometry construction (NEW!)
├── simulator.py        # Physics simulation engine
├── analysis.py         # Results analysis & plotting
├── validation.py       # Validation against theory
└── README.md          # This file
```

## 🔧 Modular Design Philosophy

The codebase is organized into distinct modules, each with a specific responsibility:

### 1. **Geometry Module** (`geometry.py`) - Physical Structure
- **Purpose**: Construct the 3D physical structure of the air classifier
- **Components**:
  - Classification chamber (cylindrical vessel)
  - Classifier wheel (turbine with blades)
  - Feed inlet system
  - Fine and coarse outlets
  - Air inlets
  - Conical bottom section

- **Key Features**:
  - PyVista-based 3D mesh generation
  - 2D engineering drawings (side/top views)
  - Detailed specifications printout
  - Pre-configured industrial and pilot scale designs

- **When to use**:
  - Before running simulations (visualize the equipment)
  - When modifying physical dimensions
  - For documentation and presentations
  - To understand flow paths and collection zones

### 2. **Configuration Module** (`config.py`) - Operating Parameters
- **Purpose**: Define operating conditions and material properties
- **Components**:
  - `ClassifierConfig`: Operating conditions (RPM, air velocity)
  - `ParticleProperties`: Material properties (size, density)
  - `SimulationConfig`: Simulation control (time step, duration)
  - `ProcessParameters`: Process targets (throughput, purity)

- **Key Features**:
  - Dataclass-based for type safety
  - Pre-configured scenarios (high purity, high yield)
  - Scale-specific configurations (industrial, pilot)

- **When to use**:
  - Configuring material properties (NEXT STEP!)
  - Changing operating conditions (RPM, air flow)
  - Setting simulation duration and output frequency

### 3. **Simulator Module** (`simulator.py`) - Physics Engine
- **Purpose**: GPU-accelerated particle dynamics simulation
- **Physics Implemented**:
  - Drag force (Schiller-Naumann correlation)
  - Centrifugal force (classifier wheel rotation)
  - Gravity
  - Air velocity field (radial, tangential, axial components)
  - Boundary conditions

- **Key Features**:
  - Warp kernel-based GPU acceleration
  - Particle tracking and collection
  - Real-time state monitoring

- **When to use**:
  - Running particle separation simulations
  - Testing different operating conditions
  - Generating trajectory data

### 4. **Analysis Module** (`analysis.py`) - Results Processing
- **Purpose**: Analyze simulation results and generate plots
- **Capabilities**:
  - Separation efficiency calculation
  - Grade efficiency curves (Tromp curves)
  - Cut size determination (d50, d25, d75)
  - Sharpness index calculation
  - Particle size distribution analysis

- **When to use**:
  - After simulation completion
  - Comparing different operating conditions
  - Validating against experimental data

### 5. **Validation Module** (`validation.py`) - Theoretical Validation
- **Purpose**: Validate simulation against engineering theory
- **Validations**:
  - Cut size calculations
  - Centrifugal force scaling
  - Mass balance verification
  - Comparison with published data

- **When to use**:
  - Verifying simulation accuracy
  - Debugging physics implementation
  - Academic/research purposes

## 🚀 Workflow

### Phase 1: Geometry Visualization (CURRENT STEP)

**Goal**: Understand the physical structure before configuring materials

```bash
# Visualize the air classifier geometry
python examples/visualize_classifier_geometry.py
```

**Output**:
- 2D engineering drawings (side view, top view)
- 3D interactive model
- Detailed specifications printout

**What you'll see**:
- Classification chamber dimensions
- Classifier wheel with blades
- Feed inlet location
- Fine and coarse outlets
- Air flow paths

### Phase 2: Material Configuration (NEXT STEP)

**Goal**: Configure yellow pea particle properties

Edit `config.py` or create a custom configuration:

```python
from air_classifier.config import ParticleProperties

# Configure yellow pea properties
particles = ParticleProperties(
    # Protein particles (fine fraction)
    protein_diameter_mean=5e-6,      # 5 μm
    protein_diameter_std=2e-6,
    protein_density=1350.0,          # kg/m³
    protein_fraction=0.25,           # 25% by count

    # Starch particles (coarse fraction)
    starch_diameter_mean=28e-6,      # 28 μm
    starch_diameter_std=8e-6,
    starch_density=1520.0,           # kg/m³

    # Physical properties
    moisture_content=0.10,           # 10%
    temperature=298.15,              # 25°C

    # Target separation
    target_cut_size=20e-6,           # 20 μm
    target_protein_purity=0.58,      # 58% protein in fine
    target_starch_purity=0.88        # 88% starch in coarse
)
```

### Phase 3: Run Simulation

```python
from air_classifier.simulator import AirClassifierSimulator
from air_classifier.config import get_default_config

# Get default configuration
classifier_cfg, particle_cfg, sim_cfg = get_default_config()

# Create simulator
sim = AirClassifierSimulator(classifier_cfg, particle_cfg, sim_cfg)

# Run simulation
results = sim.run(duration=3.0, output_interval=0.05)
```

### Phase 4: Analyze Results

```python
from air_classifier.analysis import analyze_separation_performance

# Analyze results
analysis = analyze_separation_performance(results)

# Print summary
print(f"Fine fraction collected: {analysis['fine_count']}")
print(f"Coarse fraction collected: {analysis['coarse_count']}")
print(f"Protein purity in fine: {analysis['protein_purity_fine']:.1%}")
print(f"Cut size (d50): {analysis['d50']*1e6:.1f} μm")
```

## 📊 Key Geometry Specifications

### Standard Industrial Scale (200 kg/hr)

| Component | Dimension | Notes |
|-----------|-----------|-------|
| Chamber Diameter | 1000 mm | Main classification zone |
| Chamber Height | 1200 mm | Provides residence time |
| Wheel Diameter | 400 mm | D/T ratio = 0.4 |
| Wheel Width | 60 mm | Blade height |
| Number of Blades | 24 | Radial configuration |
| Wheel Position | 900 mm | From bottom |
| Cone Angle | 60° | Included angle |

### Design Ratios

Based on turbine classifier design principles:

- **D_wheel / D_chamber**: 0.40 (typical: 0.3-0.5)
- **H_wheel / D_wheel**: 0.15 (typical: 0.10-0.20)
- **H_chamber / D_chamber**: 1.20 (typical: 1.0-1.5)

## 🎯 Separation Principle

The air classifier separates particles based on **aerodynamic behavior**:

1. **Feed**: Particles enter the classification zone
2. **Air Flow**: Radial inward air flow carries particles toward wheel
3. **Centrifugal Force**: Rotating wheel creates centrifugal field
4. **Separation**:
   - **Small particles (protein)**: Low inertia → follow air through wheel → exit at top
   - **Large particles (starch)**: High inertia → rejected by centrifugal force → settle to bottom

### Collection Zones

- **Fine Outlet** (top center): Z > 1.0 m, R < 0.2 m
  - Collects protein-rich fraction
  - Target: 55-60% protein purity

- **Coarse Outlet** (bottom): Z < 0.1 m
  - Collects starch-rich fraction
  - Target: >85% starch purity

## 🔬 Next Steps After Geometry Visualization

1. ✓ **Geometry defined** - You understand the physical structure
2. → **Configure materials** - Set yellow pea particle properties
3. → **Run simulation** - See particles separate in real-time
4. → **Analyze performance** - Calculate separation efficiency

## 📖 References

- Design based on: [`docs/air_classifier_design_guide.md`](../docs/air_classifier_design_guide.md)
- Engineering principles: Turbine air classifier theory
- Application: Yellow pea protein separation (dry fractionation)

## 💡 Tips

### Modifying Geometry

To create a custom geometry:

```python
from air_classifier.geometry import AirClassifierGeometry

# Create custom classifier
custom = AirClassifierGeometry(
    chamber_radius=0.6,      # Larger chamber
    wheel_rpm=4000.0,        # Higher speed
    blade_count=32           # More blades
)

# Visualize
custom.build_all_components()
custom.visualize_3d()
```

### Changing Material Properties

Material properties are in `ParticleProperties`:

```python
# For different feed material (e.g., different pea variety)
particles = ParticleProperties(
    protein_diameter_mean=6e-6,   # Slightly larger protein
    starch_diameter_mean=25e-6,   # Smaller starch
    protein_fraction=0.30         # More protein
)
```

### Optimization

Use pre-configured scenarios:

```python
from air_classifier.config import (
    get_high_purity_config,    # Maximize protein purity
    get_high_yield_config,     # Maximize protein recovery
    get_pilot_scale_config     # Smaller scale testing
)
```

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Air Classifier System                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │  Geometry    │────────►│   Config     │             │
│  │  Module      │         │   Module     │             │
│  │              │         │              │             │
│  │ • 3D meshes  │         │ • Operating  │             │
│  │ • Drawings   │         │   params     │             │
│  │ • Specs      │         │ • Materials  │             │
│  └──────┬───────┘         └──────┬───────┘             │
│         │                        │                      │
│         └────────┬───────────────┘                      │
│                  ▼                                      │
│         ┌──────────────┐                                │
│         │  Simulator   │                                │
│         │   Module     │                                │
│         │              │                                │
│         │ • GPU kernel │                                │
│         │ • Physics    │                                │
│         │ • Tracking   │                                │
│         └──────┬───────┘                                │
│                │                                         │
│                ▼                                         │
│  ┌──────────────┐         ┌──────────────┐             │
│  │  Analysis    │◄────────│ Validation   │             │
│  │   Module     │         │   Module     │             │
│  │              │         │              │             │
│  │ • Results    │         │ • Theory     │             │
│  │ • Plots      │         │ • Checks     │             │
│  └──────────────┘         └──────────────┘             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

**Ready to proceed?** Run the geometry visualization to see your air classifier! 🚀

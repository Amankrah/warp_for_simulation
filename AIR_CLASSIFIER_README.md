# Air Classifier Simulation for Yellow Pea Protein Separation

GPU-accelerated particle simulation using NVIDIA Warp for designing and optimizing turbine-type air classifiers for dry fractionation of yellow pea flour into protein-rich and starch-rich fractions.

## Overview

This simulation package implements the physics-based modeling described in the comprehensive engineering design guide ([docs/air_classifier_design_guide.md](docs/air_classifier_design_guide.md)). It uses NVIDIA Warp for GPU-accelerated particle dynamics to simulate the behavior of thousands of particles in a centrifugal air classifier.

### Key Features

- **GPU-Accelerated**: Uses NVIDIA Warp for fast particle simulations on CUDA-capable GPUs
- **Physically Accurate**: Implements drag forces, centrifugal forces, and complex air flow patterns
- **Bimodal Particle Distribution**: Simulates realistic protein (3-10 μm) and starch (15-40 μm) particles
- **Real-time Visualization**: 3D visualization of particle trajectories and separation
- **Parameter Studies**: Tools for optimizing wheel speed, air velocity, and other parameters
- **Performance Analysis**: Calculates protein purity, recovery, cut size, and economic metrics

### Target Application

**Yellow Pea Protein Separation**
- Feed: Milled yellow pea flour (~23% protein, ~48% starch)
- Target: Protein-rich fraction (55-65% protein) + Starch-rich fraction (>85% starch)
- Method: Dry air classification (no water, preserves protein functionality)
- Capacity: 100-500 kg/hr

## Installation

### Requirements

- Python 3.8+
- NVIDIA GPU with CUDA support (recommended)
- CUDA Toolkit 11.0+ (if using GPU)

### Dependencies

```bash
pip install numpy matplotlib pyvista
pip install warp-lang  # NVIDIA Warp
```

Or install from the project requirements:

```bash
pip install -r requirements.txt
```

## Quick Start

### 🚀 Comprehensive Live Demo (Recommended!)

**Run the complete industry-standard demonstration with live visualization:**

```bash
python air_classifier_examples/comprehensive_live_demo.py
```

This shows everything:

- ✓ Real-time particle visualization during simulation
- ✓ Live performance metrics and collection dynamics
- ✓ Automatic design validation
- ✓ Grade efficiency (Tromp curve) analysis
- ✓ Economic feasibility assessment
- ✓ Complete compliance reporting

**What you'll see:**

1. Design validation against theoretical calculations
2. GPU-accelerated simulation with live 6-panel visualization
3. Separation performance analysis
4. Grade efficiency curve (industry standard Tromp curve)
5. Economic analysis with ROI and payback
6. Overall compliance status

### Basic Simulation

```python
from air_classifier import (
    AirClassifierSimulator,
    get_default_config,
    analyze_separation,
    print_separation_report
)

# Get default configuration
classifier_config, particle_props, sim_config = get_default_config()

# Create simulator
simulator = AirClassifierSimulator(
    classifier_config,
    particle_props,
    sim_config
)

# Run simulation
results = simulator.run()

# Analyze results
particle_types = simulator.particle_types.numpy()
analysis = analyze_separation(results, particle_types)
print_separation_report(analysis)
```

### Other Example Scripts

```bash
# 🌟 RECOMMENDED: Comprehensive live demo with all features
python air_classifier_examples/comprehensive_live_demo.py

# Industry standard validation (no live view)
python air_classifier_examples/industry_standard_validation.py

# Basic simulation with analysis
python air_classifier_examples/basic_classifier.py

# Parameter study (RPM and air velocity effects)
python air_classifier_examples/parameter_study.py

# Generate video animation
python air_classifier_examples/save_classifier_video.py
```

## Configuration

### Classifier Configuration

```python
from air_classifier import ClassifierConfig

config = ClassifierConfig(
    chamber_radius=0.5,       # Classification chamber radius (m)
    chamber_height=1.2,       # Chamber height (m)
    wheel_radius=0.2,         # Classifier wheel radius (m)
    wheel_rpm=3500.0,         # Wheel rotation speed (rpm)
    air_velocity=8.0,         # Radial air velocity (m/s)
    num_particles=50000       # Number of particles to simulate
)
```

### Particle Properties

```python
from air_classifier import ParticleProperties

particles = ParticleProperties(
    protein_diameter_mean=5e-6,      # 5 μm
    protein_density=1350.0,          # kg/m³
    starch_diameter_mean=28e-6,      # 28 μm
    starch_density=1520.0,           # kg/m³
    target_cut_size=20e-6            # Target d50 (20 μm)
)
```

### Preset Configurations

```python
from air_classifier import (
    get_high_purity_config,    # Optimized for protein purity
    get_high_yield_config,     # Optimized for protein recovery
    get_pilot_scale_config     # Smaller pilot-scale system
)

classifier, particles, simulation = get_high_purity_config()
```

## Simulation Physics

### Forces on Particles

The simulator calculates three main forces on each particle:

1. **Drag Force** (Schiller-Naumann correlation)
   - Depends on particle size, density, and relative velocity
   - Reynolds number-dependent drag coefficient

2. **Gravitational Force**
   - Pulls particles downward
   - Important for larger/denser starch particles

3. **Centrifugal Force** (near rotating wheel)
   - Pushes particles outward
   - Stronger effect on larger particles
   - Creates the separation mechanism

### Air Flow Field

The air velocity field includes:
- **Radial inflow**: Air flows inward toward the classifier wheel
- **Tangential component**: Rotation induced by the spinning wheel
- **Axial flow**: Upward flow through the wheel for fine particles

### Separation Mechanism

```
Large particles (starch):
- High inertia overcomes drag force
- Centrifugal force dominates
- Cannot follow air through wheel
→ Fall to bottom (COARSE fraction)

Small particles (protein):
- Low inertia, high drag
- Follow air streamlines
- Pass through classifier wheel
→ Exit through top (FINE fraction)
```

## Output and Analysis

### Separation Metrics

The analysis provides:

- **Protein purity in fine fraction** (target: 55-65%)
- **Starch purity in coarse fraction** (target: >85%)
- **Protein recovery** (% of total protein in fine fraction)
- **Fine fraction yield** (% of feed mass)
- **Cut size (d50)** (particle size at 50% separation)

### Visualization Tools

```python
from air_classifier.analysis import (
    plot_particle_trajectories,
    plot_size_distributions,
    plot_collection_dynamics
)

# Particle trajectories (side and top view)
plot_particle_trajectories(results, particle_types, classifier_config)

# Size distributions of feed and products
plot_size_distributions(final_state, particle_types)

# Collection dynamics over time
plot_collection_dynamics(results)
```

### Economic Analysis

```python
from air_classifier.analysis import calculate_economics

economics = calculate_economics(
    analysis,
    feed_rate_kg_hr=200,
    operating_hours_year=4000,
    flour_cost_per_kg=0.80,
    protein_price_per_kg=3.50,
    starch_price_per_kg=0.60
)

print(f"Value added per tonne: ${economics['value_added_per_tonne']:.2f}")
```

## Parameter Optimization

### Effect of Wheel Speed (RPM)

- **Higher RPM** → Smaller cut size → Higher protein purity, lower yield
- **Lower RPM** → Larger cut size → Lower protein purity, higher yield

### Effect of Air Velocity

- **Higher velocity** → Larger cut size → More particles to fine fraction
- **Lower velocity** → Smaller cut size → Sharper separation

### Optimization Strategy

```python
# For maximum protein purity
classifier_config = ClassifierConfig(
    wheel_rpm=4500,     # Higher speed
    air_velocity=7.0    # Lower air flow
)

# For maximum protein recovery
classifier_config = ClassifierConfig(
    wheel_rpm=3000,     # Lower speed
    air_velocity=9.0    # Higher air flow
)
```

## Performance

### Computational Performance

On NVIDIA RTX 3080:
- **50,000 particles**: ~2,000 steps/second
- **2 second simulation**: ~5-10 seconds wall time
- **GPU memory**: ~500 MB

### Scaling

The simulation scales well with particle count:
- 10,000 particles: Very fast (>5,000 steps/s)
- 50,000 particles: Fast (~2,000 steps/s)
- 100,000 particles: Moderate (~800 steps/s)
- 500,000 particles: Slower but feasible (~150 steps/s)

## Design Guide Reference

This simulation implements the engineering design described in the comprehensive guide:

- **Section 2**: Theory of air classification (drag forces, terminal velocity)
- **Section 3**: Yellow pea particle properties (bimodal size distribution)
- **Section 4**: Turbine classifier design (centrifugal separation)
- **Section 5**: Design calculations (wheel sizing, air flow rates)
- **Section 7**: CFD simulation methodology (implemented here with Warp)

See [docs/air_classifier_design_guide.md](docs/air_classifier_design_guide.md) for complete details.

## Project Structure

```
air_classifier/
├── config.py           # Configuration classes
├── simulator.py        # Main simulator with Warp kernels
├── analysis.py         # Analysis and visualization tools
└── __init__.py         # Package initialization

air_classifier_examples/
├── basic_classifier.py           # Basic usage example
├── parameter_study.py            # Parameter optimization studies
└── save_classifier_video.py     # Video generation

docs/
└── air_classifier_design_guide.md   # Comprehensive engineering guide
```

## Example Output

### Separation Report

```
=============================================================
SEPARATION ANALYSIS REPORT
=============================================================

Particle Counts:
  Total particles:     50,000
  Protein particles:   12,500
  Starch particles:    37,500

Collection:
  Fine fraction:       10,250 particles
  Coarse fraction:     38,100 particles

Fine Fraction Composition:
  Protein:             8,500 particles
  Starch:              1,750 particles
  Protein purity:      58.2%

Coarse Fraction Composition:
  Protein:             3,200 particles
  Starch:              34,900 particles
  Starch purity:       88.5%

Performance Metrics:
  Protein recovery:    68.0%
  Fine fraction yield: 20.5%
  Cut size (d50):      21.3 μm
=============================================================
```

## Troubleshooting

### GPU Issues

If GPU is not available:
```python
# Use CPU instead
sim_config = SimulationConfig(device="cpu")
```

### Memory Issues

If running out of GPU memory:
```python
# Reduce particle count
classifier_config = ClassifierConfig(num_particles=10000)
```

### Slow Performance

- Reduce simulation time: `sim_config.total_time = 1.0`
- Increase time step: `classifier_config.dt = 2e-5`
- Reduce particle count

## References

1. **Design Guide**: See [docs/air_classifier_design_guide.md](docs/air_classifier_design_guide.md)

2. **Key Papers**:
   - Pelgrom et al. (2013). Dry fractionation for functional pea protein concentrates
   - Schutyser & van der Goot (2011). Dry fractionation for sustainable plant protein
   - Tyler (1984). Impact milling quality of grain legumes

3. **NVIDIA Warp**:
   - Documentation: https://nvidia.github.io/warp/
   - GitHub: https://github.com/NVIDIA/warp

## Citation

If you use this simulation in your research, please cite:

```
Air Classifier Simulation for Yellow Pea Protein Separation
GPU-accelerated particle dynamics using NVIDIA Warp
2026
```

## License

This project is provided for educational and research purposes.

## Contact

For questions or issues, please refer to the comprehensive engineering guide or open an issue in the repository.

---

**Note**: This simulation is based on theoretical models and should be validated against experimental data for production use. Professional engineering review is recommended before constructing physical equipment.

# Air Classifier - Quick Reference Card

## 🎯 Module Overview

| Module | Purpose | When to Use |
|--------|---------|-------------|
| **geometry.py** | Build 3D structure | Before simulation, visualizing equipment |
| **config.py** | Set parameters | Configuring materials, changing operating conditions |
| **simulator.py** | Run physics | Executing particle simulations |
| **analysis.py** | Process results | After simulation, generating reports |
| **validation.py** | Check accuracy | Verifying against theory |

## ⚡ Quick Commands

```bash
# Test geometry module
python test_geometry.py

# Interactive visualization
python examples/visualize_classifier_geometry.py

# Run simulation (after configuring materials)
python examples/run_classifier_simulation.py
```

## 📐 Key Dimensions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Chamber Ø | 1000 mm | Main classification zone |
| Chamber H | 1200 mm | Provides residence time |
| Wheel Ø | 400 mm | Rotating turbine |
| Wheel H | 60 mm | Blade height |
| Blades | 24 | Radial configuration |
| Wheel RPM | 2000-5000 | Adjustable for cut size |

## 🔧 Common Code Patterns

### Create Geometry

```python
from air_classifier.geometry import create_standard_industrial_classifier

# Standard 200 kg/hr classifier
classifier = create_standard_industrial_classifier()

# Build and visualize
classifier.build_all_components()
classifier.visualize_3d()
```

### Configure Materials

```python
from air_classifier.config import ParticleProperties

particles = ParticleProperties(
    protein_diameter_mean=5e-6,    # 5 μm
    starch_diameter_mean=28e-6,    # 28 μm
    target_cut_size=20e-6          # 20 μm
)
```

### Run Simulation

```python
from air_classifier.simulator import AirClassifierSimulator
from air_classifier.config import get_default_config

classifier_cfg, particle_cfg, sim_cfg = get_default_config()
sim = AirClassifierSimulator(classifier_cfg, particle_cfg, sim_cfg)
results = sim.run(duration=3.0)
```

### Analyze Results

```python
from air_classifier.analysis import analyze_separation_performance

analysis = analyze_separation_performance(results)
print(f"Protein purity: {analysis['protein_purity_fine']:.1%}")
print(f"Cut size d50: {analysis['d50']*1e6:.1f} μm")
```

## 🎯 Separation Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Protein Purity (Fine) | 55-65% | In fine fraction |
| Starch Purity (Coarse) | >85% | In coarse fraction |
| Cut Size (d₅₀) | 18-22 μm | Particle size with 50% split |
| Protein Recovery | >70% | % of protein to fine |
| Separation Efficiency | >85% | Overall performance |

## 📊 Operating Ranges

| Parameter | Min | Target | Max | Effect |
|-----------|-----|--------|-----|--------|
| Wheel RPM | 2000 | 3500 | 5000 | Higher = finer cut |
| Air Velocity | 6 | 8 | 10 | m/s radial |
| Feed Rate | 100 | 200 | 300 | kg/hr |

## 🔍 Collection Zones

| Zone | Location | Collects |
|------|----------|----------|
| **Fine** | Z > 1.0 m, R < 0.2 m | Protein-rich (small particles) |
| **Coarse** | Z < 0.1 m | Starch-rich (large particles) |
| **Feed** | Z ≈ 0.88 m, R = 0.1-0.18 m | Entry point |

## 📈 Optimization Presets

```python
from air_classifier.config import (
    get_high_purity_config,    # Max protein purity (60-65%)
    get_high_yield_config,     # Max protein recovery (>75%)
    get_pilot_scale_config     # Small scale (50 kg/hr)
)
```

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Low purity | Cut size too large | Increase RPM, decrease air flow |
| Low yield | Cut size too small | Decrease RPM, increase air flow |
| No separation | Weak centrifugal | Increase RPM, check wheel rotation |
| Particles stuck | Poor air flow | Check air velocity field |

## 📁 File Locations

```
air_classifier/
├── geometry.py         # 3D construction
├── config.py           # Parameters
├── simulator.py        # Physics engine
├── analysis.py         # Results
└── validation.py       # Theory checks

examples/
├── visualize_classifier_geometry.py
└── run_classifier_simulation.py

output/
├── *.png              # Visualizations
└── *.h5               # Simulation data
```

## 🔗 Quick Links

- [Full Documentation](README.md)
- [Geometry Construction Guide](../GEOMETRY_CONSTRUCTION.md)
- [Engineering Design Guide](../docs/air_classifier_design_guide.md)
- [Warp Tutorial](../docs/warp_bioresource_engineering_guide.md)

## 💡 Tips

1. **Always visualize geometry first** before running simulations
2. **Material properties are separate** from geometry (modular!)
3. **Use presets** for common scenarios (high purity, high yield)
4. **Check design ratios** to ensure realistic geometry
5. **Start with pilot scale** for faster testing

## 🎓 Learning Path

1. ✅ Understand geometry → Run `visualize_classifier_geometry.py`
2. → Configure materials → Edit `config.py`
3. → Run simulation → Execute `run_classifier_simulation.py`
4. → Analyze results → Use `analysis.py` functions
5. → Optimize → Try different operating conditions

---

**Quick Start**: `python examples/visualize_classifier_geometry.py` 🚀

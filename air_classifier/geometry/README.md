# Air Classifier Geometry Module

## Modular Construction System for Corrected Cyclone Air Classifier

This module provides a systematic, component-based approach to constructing the geometry of a **Cyclone Air Classifier** optimized for yellow pea protein/starch separation at d₅₀ = 20 μm.

Based on specifications from: **`docs/corrected_classifier_geometry.md`**

---

## 📁 Module Structure

```
air_classifier/geometry/
├── __init__.py                    # Module exports
├── README.md                      # This file
├── corrected_config.py            # Configuration dataclass
├── assembly.py                    # Main assembly builder
├── visualize.py                   # 3D visualization
├── test_geometry.py               # Validation tests
└── components/                    # Individual component builders
    ├── __init__.py
    ├── chamber.py                 # Classification chamber + cone
    ├── selector_rotor.py          # Selector blades (24× corrected)
    ├── hub_assembly.py            # Hub with feed ports
    ├── distributor.py             # Distributor plate with grooves
    ├── air_inlets.py              # Air inlets + guide vanes
    ├── external_cyclone.py        # Stairmand high-efficiency cyclone
    ├── shaft.py                   # Vertical shaft
    └── outlets.py                 # Fines and coarse outlets
```

---

## 🚀 Quick Start

### 1. Basic Usage

```python
from air_classifier.geometry import CorrectedClassifierConfig, build_complete_classifier
from air_classifier.geometry.visualize import visualize_complete_assembly

# Create default corrected configuration
config = CorrectedClassifierConfig()

# Print specifications
config.print_specifications()

# Build complete geometry
assembly = build_complete_classifier(
    config,
    include_cyclone=True,
    include_vanes=True,
    include_ports=True
)

# Visualize in 3D
visualize_complete_assembly(assembly)
```

### 2. Run Tests

```bash
cd air_classifier/geometry
python test_geometry.py
```

This will validate all geometry components against the corrected specifications.

---

## 🔧 Key Components

### 1. **Configuration** (`corrected_config.py`)

The `CorrectedClassifierConfig` dataclass contains all corrected specifications:

```python
config = CorrectedClassifierConfig()

# Key corrected values
config.selector_blade_height         # 500mm (reduced from 600mm)
config.selector_blade_thickness      # 4mm (reduced from 5mm)
config.selector_blade_gap            # 48.5mm (increased from 47.4mm)
config.distributor_diameter          # 450mm (reduced from 500mm)
config.shaft_diameter                # 80mm (reduced from 100mm)
config.selector_zone_bottom          # 0.45m (raised from 0.35m)
```

**Calculated Properties:**
- `config.cone_height` - Cone height from angle
- `config.selector_blade_gap` - Gap between blades
- `config.tip_speed_design` - Rotor tip speed at design RPM
- `config.chamber_volume` - Total chamber volume

**Methods:**
- `calculate_cut_size(rpm, air_flow)` - Calculate theoretical d₅₀
- `calculate_required_rpm(target_d50, air_flow)` - Calculate RPM for target d₅₀
- `print_specifications()` - Print comprehensive specs

### 2. **Component Builders** (`components/`)

Each component has a dedicated builder module:

#### Chamber (`chamber.py`)
```python
from air_classifier.geometry.components import build_chamber, build_cone

chamber = build_chamber(config)
cone = build_cone(config)
```

#### Selector Rotor (`selector_rotor.py`)
```python
from air_classifier.geometry.components import build_selector_blades

blades = build_selector_blades(config)  # Returns list of 24 blade meshes
```

**Corrected Features:**
- 24 blades @ 4mm thickness (not 5mm)
- 500mm height (not 600mm)
- 5° forward lean angle
- 48.5mm blade gap

#### Hub Assembly (`hub_assembly.py`)
```python
from air_classifier.geometry.components import build_hub_assembly, build_feed_ports

hub = build_hub_assembly(config)
ports = build_feed_ports(config)  # 8 ports @ 45° intervals, 30° downward
```

#### Distributor Plate (`distributor.py`)
```python
from air_classifier.geometry.components import build_distributor_plate

distributor = build_distributor_plate(config)  # With edge lip and grooves
```

#### Air Distribution (`air_inlets.py`)
```python
from air_classifier.geometry.components import build_air_inlets, build_inlet_guide_vanes

inlets = build_air_inlets(config)  # 4× tangential inlets
vanes = build_inlet_guide_vanes(config)  # 6 vanes per inlet @ 45°
```

#### External Cyclone (`external_cyclone.py`)
```python
from air_classifier.geometry.components import build_external_cyclone

cylinder, cone, vortex_finder = build_external_cyclone(config)
```

**Stairmand Proportions (Section 6.2):**
- Body diameter: 500mm
- Inlet: 250mm × 100mm (rectangular)
- Vortex finder: Ø250mm × 250mm
- Cylinder height: 750mm
- Cone height: 1250mm
- Efficiency: >95% for d > 5μm

### 3. **Assembly** (`assembly.py`)

The main assembly function builds all components:

```python
from air_classifier.geometry import build_complete_classifier

assembly = build_complete_classifier(
    config,
    include_cyclone=True,    # Include external cyclone
    include_vanes=True,      # Include air inlet guide vanes
    include_ports=True       # Include hub feed ports
)

# Access components
assembly.chamber
assembly.cone
assembly.shaft
assembly.distributor
assembly.selector_blades  # List of 24 blades
assembly.hub
assembly.air_inlets
assembly.cyclone_cylinder
assembly.cyclone_cone
# ... and more

# Get all meshes as dictionary
meshes = assembly.get_all_meshes()

# Component counts
counts = assembly.count_components()
```

### 4. **Visualization** (`visualize.py`)

Comprehensive 3D visualization tools:

```python
from air_classifier.geometry.visualize import (
    visualize_complete_assembly,
    visualize_cross_section,
    compare_configurations
)

# Complete assembly view
visualize_complete_assembly(
    assembly,
    screenshot_path='classifier.png',  # Optional: save screenshot
    camera_position='iso'  # 'iso', 'xy', 'xz', or 'yz'
)

# Cross-section view
visualize_cross_section(assembly, plane='xz')

# Compare two configurations
from air_classifier.geometry.corrected_config import create_scaled_config

config1 = CorrectedClassifierConfig()
config2 = create_scaled_config(0.5)  # Half scale

compare_configurations(
    config1, config2,
    labels=("Full Scale", "Half Scale")
)
```

---

## 📊 Corrected Specifications Summary

### Key Corrections from Original Design

| Parameter | Original | Corrected | Change | Justification |
|-----------|----------|-----------|--------|---------------|
| **Selector Blade Height** | 600 mm | 500 mm | -17% | Better clearance from distributor |
| **Selector Blade Thickness** | 5 mm | 4 mm | -20% | Increased blade gap for fines |
| **Blade Gap** | 47.4 mm | 48.5 mm | +2% | Better fines passage |
| **Selector Zone Bottom** | Z=0.35 m | Z=0.45 m | +0.10 m | Clear of air inlets |
| **Distributor Diameter** | 500 mm | 450 mm | -10% | Better material spread |
| **Distributor Position** | Z=0.25 m | Z=0.35 m | +0.10 m | Clear of air inlets |
| **Shaft Diameter** | 100 mm | 80 mm | -20% | Less flow obstruction |
| **Hub Assembly** | Incomplete | Fully specified | NEW | 8 ports, 30° angle |
| **External Cyclone** | None | Ø500mm Stairmand | NEW | >95% efficiency @ 5μm |
| **Air Inlet Vanes** | None | 6 per inlet @ 45° | NEW | Improved swirl generation |

### Design Ratios (Section 10.1)

| Ratio | Value | Specification | Status |
|-------|-------|---------------|--------|
| D_selector/D_chamber | 0.40 | 0.3 - 0.5 | ✓ Within range |
| D_distributor/D_chamber | 0.45 | 0.4 - 0.6 | ✓ Within range |
| H_chamber/D_chamber | 1.20 | 1.0 - 1.5 | ✓ Within range |

### Operating Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Feed Rate** | 200 kg/hr | Yellow pea flour |
| **Air Flow** | 3000 m³/hr | Design point |
| **Rotor Speed** | 1500-4000 rpm | VFD controlled |
| **Design Speed** | 3000 rpm | For d₅₀ = 20 μm |
| **Target d₅₀** | 20 μm | Protein/starch cut |
| **Tip Speed** | 62.8 m/s | @ 3000 rpm (safe) |

---

## 🧪 Testing & Validation

### Test Suite (`test_geometry.py`)

The test suite validates:

1. **Configuration** - All dimensions and ratios
2. **Geometry Assembly** - Component creation and mesh validity
3. **Design Ratios** - Within specification ranges
4. **Blade Loading** - Safe operation at all speeds
5. **Cut Size Range** - Achieves target d₅₀
6. **Scaling** - Geometry scales correctly

Run tests:
```bash
python test_geometry.py
```

Expected output:
```
TEST SUMMARY
══════════════════════════════════════════════════════════════════════
  Configuration             ✓ PASS
  Geometry Assembly         ✓ PASS
  Design Ratios             ✓ PASS
  Blade Loading             ✓ PASS
  Cut Size Range            ✓ PASS
  Scaling                   ✓ PASS

  Total: 6/6 tests passed

🎉 ALL TESTS PASSED!
```

---

## 📈 Performance Predictions

### Cut Size vs RPM (@ 3000 m³/hr)

| RPM | d₅₀ (μm) | Application |
|-----|----------|-------------|
| 1500 | 42.6 | Coarse separation |
| 2000 | 32.0 | Mid-range |
| 2500 | 25.6 | Fine adjustment |
| **3000** | **21.3** | **Design point** |
| 3500 | 18.3 | Finer cut |
| 4000 | 16.0 | Maximum fineness |

### Blade Loading Analysis

| RPM | Tip Speed (m/s) | Stress (MPa) | Safe? |
|-----|-----------------|--------------|-------|
| 3000 | 62.8 | ~45 | ✓ Yes |
| 4000 | 83.8 | ~80 | ✓ Yes (< 100 m/s limit) |

---

## 🎯 Usage Examples

### Example 1: Build and Visualize

```python
from air_classifier.geometry import CorrectedClassifierConfig, build_complete_classifier
from air_classifier.geometry.visualize import visualize_complete_assembly

# Create configuration
config = CorrectedClassifierConfig()

# Build geometry
assembly = build_complete_classifier(config, include_cyclone=True)

# Visualize
visualize_complete_assembly(assembly, screenshot_path='output/classifier_3d.png')
```

### Example 2: Parameter Study

```python
import numpy as np
from air_classifier.geometry import CorrectedClassifierConfig

config = CorrectedClassifierConfig()

# Study cut size vs RPM
rpms = np.linspace(1500, 4000, 20)
d50s = [config.calculate_cut_size(rpm, 3000) for rpm in rpms]

# Find RPM for specific d50
target_rpm = config.calculate_required_rpm(20.0, 3000)
print(f"Required RPM for d50=20μm: {target_rpm:.0f} RPM")
```

### Example 3: Export Geometry

```python
from air_classifier.geometry import build_complete_classifier
from air_classifier.geometry.assembly import save_geometry
from air_classifier.geometry.corrected_config import create_default_config

config = create_default_config()
assembly = build_complete_classifier(config)

# Save all components as STL files
save_geometry(assembly, base_path='output/geometry', format='stl')
```

### Example 4: Scaled Configurations

```python
from air_classifier.geometry.corrected_config import create_scaled_config
from air_classifier.geometry import build_complete_classifier

# Create half-scale pilot unit
pilot_config = create_scaled_config(0.5)
pilot_assembly = build_complete_classifier(pilot_config)

print(f"Pilot scale:")
print(f"  Chamber: Ø{pilot_config.chamber_diameter*1000:.0f}mm")
print(f"  Capacity: {pilot_config.feed_rate_design:.0f} kg/hr")
```

---

## 🔗 References

1. **Primary Reference:**
   - Klumpar, I.V., Currier, F.N., & Ring, T.A. (1986). Air Classifiers. *Chemical Engineering*, March 3, 1986, pp. 77-92.
   - Figure 11: Humboldt Wedag cyclone air classifier

2. **Design Document:**
   - `docs/corrected_classifier_geometry.md` - Complete corrected specifications

3. **Related Modules:**
   - `air_classifier/config.py` - Operating parameters
   - `air_classifier/simulator.py` - WARP DEM simulation

---

## 📝 Notes

### Material Specifications
- **Chamber:** SS304, 4mm wall thickness
- **Selector Blades:** SS304, 4mm thick
- **Shaft:** SS316, Ø80mm
- **Distributor:** SS304 with WC-Co coating (wear resistant)
- **Wear Liners:** Hardox 400 (cylinder), Alumina ceramic (cone)

### Critical Design Features
1. **External cyclone collection** (>95% efficiency for protein particles)
2. **Guide vanes on air inlets** (45° angle for optimal swirl)
3. **Raised selector zone** (0.45m, clear of air inlet turbulence)
4. **Thinner blades** (4mm for improved open area)
5. **Hub feed ports** (8× Ø40mm @ 30° downward angle)

---

## 🤝 Contributing

When modifying geometry:

1. Update specifications in `corrected_config.py`
2. Update component builders in `components/`
3. Run test suite to validate changes
4. Update this README with any new features
5. Reference section numbers from `corrected_classifier_geometry.md`

---

## ⚠️ Important

This geometry module implements the **corrected** specifications from `docs/corrected_classifier_geometry.md`. It supersedes the original implementation in `air_classifier/geometry.py`.

Key differences:
- ✓ Cyclone Air Classifier (not Whirlwind)
- ✓ External fines collection
- ✓ Corrected selector rotor dimensions
- ✓ Complete hub assembly specification
- ✓ Air inlet guide vanes
- ✓ Stairmand high-efficiency cyclone

---

**Version:** 1.0.0
**Last Updated:** 2026-01-29
**Based on:** `docs/corrected_classifier_geometry.md` Rev 1.0

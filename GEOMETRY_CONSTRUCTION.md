# Air Classifier Geometry Construction - Complete Guide

## 🎯 Overview

We've successfully modularized the air classifier construction into a dedicated geometry module that creates detailed 3D models of an industrial turbine-type air classifier **before** configuring yellow pea material properties.

## 📦 What We Built

### 1. **Geometry Module** (`air_classifier/geometry.py`)

A comprehensive 3D geometry construction system with:

#### Components Constructed:
- ✅ **Classification Chamber**: Cylindrical vessel (1000mm diameter × 1200mm height)
- ✅ **Conical Bottom**: 60° cone for coarse particle collection
- ✅ **Classifier Wheel**: Rotating turbine (400mm diameter × 60mm width)
- ✅ **Blade System**: 24 radial blades (3mm thick)
- ✅ **Feed Inlet**: Material entry port at classification zone
- ✅ **Fine Outlet**: Top center exit for protein-rich particles
- ✅ **Coarse Outlet**: Bottom exit for starch-rich particles
- ✅ **Air Inlets**: 4 tangential ports for air flow

#### Features:
- 🔧 **Modular Construction**: Each component built separately, then assembled
- 📐 **2D Engineering Drawings**: Side view and top view with dimensions
- 🎨 **3D Interactive Model**: PyVista-based visualization
- 📊 **Specifications Report**: Detailed dimensional analysis
- 📏 **Design Validation**: Checks against industry standard ratios

### 2. **Visualization Examples** (`examples/visualize_classifier_geometry.py`)

Interactive script that:
- Shows 2D engineering drawings
- Opens 3D interactive model
- Prints detailed specifications
- Compares industrial vs pilot scale
- Guides next steps

### 3. **Documentation** (`air_classifier/README.md`)

Complete modular architecture documentation with:
- Module responsibilities
- Workflow phases
- Usage examples
- Design principles
- Next steps guide

### 4. **Test Suite** (`test_geometry.py`)

Automated testing for:
- Module imports
- Component creation
- 2D/3D rendering
- Multiple scales

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│           MODULAR AIR CLASSIFIER SYSTEM              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Phase 1: GEOMETRY (CURRENT - COMPLETED ✓)          │
│  ┌────────────────────────────────────────────┐     │
│  │  geometry.py                               │     │
│  │  • Build 3D structure                      │     │
│  │  • Generate drawings                       │     │
│  │  • Print specifications                    │     │
│  └────────────────────────────────────────────┘     │
│                       │                              │
│                       ▼                              │
│  Phase 2: MATERIALS (NEXT STEP)                     │
│  ┌────────────────────────────────────────────┐     │
│  │  config.py                                 │     │
│  │  • Yellow pea particle properties          │     │
│  │  • Size distributions                      │     │
│  │  • Densities                               │     │
│  └────────────────────────────────────────────┘     │
│                       │                              │
│                       ▼                              │
│  Phase 3: SIMULATION (AFTER MATERIALS)              │
│  ┌────────────────────────────────────────────┐     │
│  │  simulator.py                              │     │
│  │  • GPU particle dynamics                   │     │
│  │  • Separation physics                      │     │
│  │  • Collection tracking                     │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## 📐 Standard Industrial Classifier Specifications

Based on engineering guide for 200 kg/hr yellow pea protein separation:

### Geometry
- **Chamber Diameter**: 1.000 m (1000 mm)
- **Chamber Height**: 1.200 m (1200 mm)
- **Total Height**: 1.667 m (with cone)
- **Total Volume**: 1.2 m³ (1200 L)

### Classifier Wheel
- **Diameter**: 0.400 m (400 mm)
- **Width**: 0.060 m (60 mm)
- **Position**: 0.900 m above bottom
- **Blades**: 24 radial blades
- **Blade Thickness**: 3 mm
- **Blade Gap**: 49.1 mm

### Design Ratios (Validated)
- **D_wheel/D_chamber**: 0.40 ✓ (target: 0.3-0.5)
- **H_wheel/D_wheel**: 0.15 ✓ (target: 0.10-0.20)
- **H_chamber/D_chamber**: 1.20 ✓ (target: 1.0-1.5)

### Flow Paths
- **Feed Inlet**: 150×100 mm at Z=0.88m (below wheel)
- **Fine Outlet**: Ø320 mm at top center
- **Coarse Outlet**: Ø150 mm at cone bottom
- **Air Inlets**: 4× 100×80 mm tangential ports

## 🚀 Quick Start

### 1. Test the Geometry Module

```bash
# Quick test (non-interactive)
python test_geometry.py
```

**Output**:
- ✓ Module validation
- 2D drawings: `output/test_2d_drawings.png`
- 3D model: `output/test_3d_model.png`

### 2. Interactive Visualization

```bash
# Full interactive visualization
python examples/visualize_classifier_geometry.py
```

**What you'll see**:
1. Detailed specifications printout
2. 2D engineering drawings (side + top views)
3. Interactive 3D model (rotate/zoom)
4. Comparison table (industrial vs pilot)

### 3. Use in Code

```python
from air_classifier.geometry import create_standard_industrial_classifier

# Create classifier
classifier = create_standard_industrial_classifier()

# Print specs
classifier.print_specifications()

# Build components
components = classifier.build_all_components()

# Access individual components
chamber = components.chamber
wheel = components.wheel
blades = components.blades  # List of 24 blade meshes

# Visualize
classifier.visualize_3d(
    show_blades=True,
    show_inlets=True,
    camera_position='iso'
)
```

## 🎨 Visualization Examples

### 2D Engineering Drawings

The system generates professional engineering drawings showing:

**Side View (Vertical Cross-Section)**:
- Chamber walls and conical bottom
- Classifier wheel position and blades
- Feed inlet location
- Fine outlet (top) and coarse outlet (bottom)
- Air flow arrows
- Dimensional annotations

**Top View (Horizontal Cross-Section)**:
- Chamber outline
- Classifier wheel with 24 radial blades
- Rotation direction
- Air inlet positions (tangential)
- Feed zone (annular region)
- Fine collection zone (center)

### 3D Interactive Model

Features:
- Transparent chamber walls (see inside)
- Visible classifier wheel with all blades
- Color-coded outlets (green=fine, brown=coarse)
- Feed and air inlets shown
- Coordinate axes for orientation
- Legend for component identification

## 📊 Design Principles

### Separation Mechanism

The turbine air classifier separates particles based on **centrifugal force vs drag force balance**:

1. **Feed Entry**: Particles enter at Z=0.88m (just below wheel)
2. **Radial Airflow**: Pulls particles inward toward wheel
3. **Centrifugal Field**: Rotating wheel (3500 RPM) creates strong centrifugal force
4. **Size-Based Separation**:
   - **Fine particles (protein)**:
     - Size: 1-10 μm
     - Low mass/inertia
     - Follow air streamlines through wheel
     - Exit through top (fine outlet)

   - **Coarse particles (starch)**:
     - Size: 15-40 μm
     - High mass/inertia
     - Rejected by centrifugal force
     - Settle to bottom (coarse outlet)

### Target Cut Size

**d₅₀ = 20 μm** (particle size with 50% probability of reporting to either fraction)

Determined by:
- Wheel rotation speed (RPM)
- Air flow rate
- Wheel geometry
- Particle density

## 🔬 Next Steps

### Phase 2: Configure Yellow Pea Material Properties

Now that the **physical structure is defined**, configure the **material properties**:

1. **Open** `air_classifier/config.py`

2. **Review** `ParticleProperties` class:
   ```python
   @dataclass
   class ParticleProperties:
       # Already configured based on engineering guide:
       protein_diameter_mean = 5e-6      # 5 μm ✓
       protein_density = 1350.0          # kg/m³ ✓
       starch_diameter_mean = 28e-6      # 28 μm ✓
       starch_density = 1520.0           # kg/m³ ✓
       target_cut_size = 20e-6           # 20 μm ✓
   ```

3. **Customize** if needed (different pea variety, moisture, etc.)

4. **Run simulation** with configured materials:
   ```bash
   python examples/run_classifier_simulation.py
   ```

### What Happens in Simulation

With geometry + materials configured:
1. 50,000 particles initialized in feed zone
2. GPU kernels compute forces (drag, centrifugal, gravity)
3. Particles move according to physics
4. Collection tracking (fine vs coarse)
5. Real-time visualization
6. Performance analysis

## 📁 Files Created

```
air_classifier/
├── geometry.py                          # ← NEW: 3D geometry module
├── README.md                            # ← NEW: Architecture docs
├── config.py                            # ← UPDATED: Added geometry note
├── simulator.py                         # (existing)
├── analysis.py                          # (existing)
└── validation.py                        # (existing)

examples/
└── visualize_classifier_geometry.py    # ← NEW: Interactive visualization

output/
├── test_2d_drawings.png                # ← Generated by test
└── test_3d_model.png                   # ← Generated by test

GEOMETRY_CONSTRUCTION.md                # ← NEW: This file
test_geometry.py                        # ← NEW: Module tests
```

## 💡 Key Advantages of Modular Approach

### 1. **Separation of Concerns**
- Geometry = Physical structure
- Config = Operating parameters + materials
- Simulator = Physics engine
- Analysis = Results processing

### 2. **Flexibility**
- Change geometry without touching simulation code
- Test different materials with same geometry
- Swap components independently

### 3. **Validation**
- Visualize geometry before simulation
- Verify dimensions against engineering specs
- Check design ratios

### 4. **Documentation**
- 2D drawings for presentations
- 3D models for understanding
- Specifications for validation

### 5. **Debugging**
- Isolate geometry issues
- Test components individually
- Clear module boundaries

## 🎓 Educational Value

This modular structure follows **engineering best practices**:

1. **CAD-like Workflow**: Build geometry → Configure materials → Simulate
2. **Professional Engineering**: Drawings → Specs → Validation
3. **Software Engineering**: Modular → Testable → Maintainable
4. **Bioresource Engineering**: Design → Process → Optimize

## 📚 References

Based on:
- [`docs/air_classifier_design_guide.md`](docs/air_classifier_design_guide.md) - Complete engineering guide
- [`docs/warp_bioresource_engineering_guide.md`](docs/warp_bioresource_engineering_guide.md) - NVIDIA Warp tutorial
- Industrial turbine classifier design principles
- Yellow pea protein separation literature

## ✅ Completion Checklist

- [x] Geometry module created
- [x] Component construction methods
- [x] 2D drawing generation
- [x] 3D visualization system
- [x] Specifications calculator
- [x] Test suite
- [x] Documentation
- [x] Example scripts
- [ ] Material properties configuration (NEXT)
- [ ] Particle simulation (AFTER MATERIALS)
- [ ] Results analysis (AFTER SIMULATION)

---

## 🏁 Summary

**You now have a fully modular air classifier geometry system!**

**What's Complete**:
✓ 3D physical structure defined
✓ Engineering drawings generated
✓ Specifications validated
✓ Visualization tools ready

**What's Next**:
→ Configure yellow pea particle properties
→ Run GPU-accelerated particle simulation
→ Analyze separation performance

**To proceed**:
```bash
# 1. Visualize the geometry
python examples/visualize_classifier_geometry.py

# 2. Review material properties
# Edit air_classifier/config.py if needed

# 3. Run simulation (after configuring materials)
python examples/run_classifier_simulation.py
```

---

**The modular foundation is complete - ready to add yellow pea materials!** 🌱⚙️

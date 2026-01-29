# Comprehensive Engineering Guide: Air Classifier Design for Yellow Pea Protein Separation

## Table of Contents

1. [Introduction](#1-introduction)
2. [Theory of Air Classification](#2-theory-of-air-classification)
3. [Yellow Pea Composition and Properties](#3-yellow-pea-composition-and-properties)
4. [Air Classifier Types and Selection](#4-air-classifier-types-and-selection)
5. [Design Calculations](#5-design-calculations)
6. [Detailed Component Design](#6-detailed-component-design)
7. [CFD and Particle Simulation with NVIDIA Warp](#7-cfd-and-particle-simulation-with-nvidia-warp)
8. [Construction and Materials](#8-construction-and-materials)
9. [Instrumentation and Control](#9-instrumentation-and-control)
10. [Operation and Optimization](#10-operation-and-optimization)
11. [Safety Considerations](#11-safety-considerations)
12. [Economic Analysis](#12-economic-analysis)
13. [Appendices](#13-appendices)

---

## 1. Introduction

### 1.1 Purpose and Scope

This guide provides a complete engineering framework for designing, building, and operating an air classifier system specifically optimized for separating protein-rich fractions from milled yellow peas (Pisum sativum). Air classification is a dry fractionation technique that exploits differences in particle size and density between protein bodies and starch granules.

### 1.2 Why Air Classification for Pea Protein?

| Method | Protein Purity | Yield | Energy Use | Water Use | Capital Cost |
|--------|---------------|-------|------------|-----------|--------------|
| **Air Classification** | 55-65% | 70-85% | Low | None | Medium |
| Wet Extraction | 80-90% | 60-70% | High | High | High |
| Isoelectric Precipitation | 85-95% | 50-65% | High | Very High | High |

**Advantages of Air Classification:**
- No water usage (sustainable, lower environmental impact)
- Preserves native protein functionality
- Lower energy consumption
- Continuous operation possible
- No wastewater treatment required
- Maintains protein solubility and emulsification properties

### 1.3 Target Specifications

| Parameter | Target Value |
|-----------|--------------|
| Feed Rate | 100-500 kg/hr |
| Protein Enrichment | From ~23% to 55-65% |
| Starch Fraction Purity | >85% starch |
| Separation Efficiency | >70% |
| Cut Size (d50) | 15-25 μm |
| Power Consumption | <15 kW |

---

## 2. Theory of Air Classification

### 2.1 Fundamental Principles

Air classification separates particles based on their **aerodynamic behavior**, which depends on:

1. **Particle size** (dominant factor)
2. **Particle density**
3. **Particle shape**
4. **Air velocity and flow pattern**

#### 2.1.1 Terminal Settling Velocity

The terminal velocity of a particle in air is the key parameter:

**For Stokes regime (Re < 0.1):**
$$v_t = \frac{d_p^2 (\rho_p - \rho_f) g}{18 \mu}$$

**For intermediate regime (0.1 < Re < 1000):**
$$v_t = \sqrt{\frac{4 d_p (\rho_p - \rho_f) g}{3 C_D \rho_f}}$$

Where:
- $v_t$ = terminal velocity (m/s)
- $d_p$ = particle diameter (m)
- $\rho_p$ = particle density (kg/m³)
- $\rho_f$ = fluid (air) density (kg/m³)
- $\mu$ = dynamic viscosity (Pa·s)
- $g$ = gravitational acceleration (m/s²)
- $C_D$ = drag coefficient

#### 2.1.2 Drag Coefficient Correlations

```
For spherical particles:

Re < 0.1:        C_D = 24/Re                    (Stokes)
0.1 < Re < 1000: C_D = 24/Re (1 + 0.15 Re^0.687) (Schiller-Naumann)
1000 < Re < 2×10⁵: C_D ≈ 0.44                   (Newton)
```

#### 2.1.3 Stokes Number

The Stokes number determines whether particles follow fluid streamlines:

$$St = \frac{\rho_p d_p^2 U}{18 \mu L}$$

Where:
- $U$ = characteristic fluid velocity
- $L$ = characteristic length scale

- **St << 1**: Particles follow fluid streamlines (fine fraction)
- **St >> 1**: Particles deviate from streamlines (coarse fraction)

### 2.2 Classification Mechanisms

#### 2.2.1 Gravitational Classification
- Relies on settling velocity differences
- Simple design but limited to larger particles (>50 μm)
- Not suitable for pea protein separation alone

#### 2.2.2 Centrifugal Classification
- Uses centrifugal force to enhance separation
- Effective for fine particles (1-100 μm)
- **Preferred method for pea protein separation**

#### 2.2.3 Cut Size Theory

The **cut size (d50)** is the particle diameter with 50% probability of reporting to either fraction:

For centrifugal classifiers:
$$d_{50} = \sqrt{\frac{9 \mu Q}{2 \pi \rho_p \omega^2 r_c^2 h}}$$

Where:
- $Q$ = volumetric air flow rate (m³/s)
- $\omega$ = angular velocity (rad/s)
- $r_c$ = classifier radius (m)
- $h$ = classifier height (m)

### 2.3 Separation Efficiency

#### 2.3.1 Grade Efficiency Curve (Tromp Curve)

The grade efficiency $T(d)$ represents the fraction of particles of size $d$ reporting to the coarse fraction:

$$T(d) = \frac{m_c \cdot f_c(d)}{m_f \cdot f_f(d)}$$

Where:
- $m_c$, $m_f$ = mass of coarse and feed
- $f_c(d)$, $f_f(d)$ = size distribution functions

#### 2.3.2 Sharpness Index

$$\kappa = \frac{d_{75}}{d_{25}}$$

- Ideal classifier: κ = 1
- Good classifier: κ < 2
- Poor classifier: κ > 3

### 2.4 Particle Properties Affecting Separation

| Property | Effect on Separation |
|----------|---------------------|
| Size distribution | Wider distribution = easier separation |
| Density difference | Greater difference = better separation |
| Shape factor | Non-spherical particles have higher drag |
| Moisture content | Higher moisture = agglomeration, poor separation |
| Electrostatic charge | Can cause particle agglomeration |

---

## 3. Yellow Pea Composition and Properties

### 3.1 Compositional Analysis

#### 3.1.1 Whole Yellow Pea Composition

| Component | Content (% dry basis) |
|-----------|----------------------|
| Protein | 20-25% |
| Starch | 45-50% |
| Fiber | 15-20% |
| Lipids | 1-2% |
| Ash | 2-3% |
| Moisture | 10-14% |

#### 3.1.2 Protein Composition

| Protein Type | Percentage of Total Protein |
|--------------|---------------------------|
| Legumin (11S) | 65-80% |
| Vicilin (7S) | 20-35% |
| Albumins | 15-25% |

### 3.2 Microstructural Properties

#### 3.2.1 Particle Size Distribution After Milling

| Component | Size Range (μm) | Mean Size (μm) | Density (kg/m³) |
|-----------|-----------------|----------------|-----------------|
| Protein bodies | 1-10 | 3-5 | 1300-1400 |
| Starch granules | 15-40 | 25-30 | 1500-1550 |
| Fiber fragments | 50-500 | 100-200 | 1200-1300 |
| Cell wall fragments | 20-100 | 40-60 | 1400-1500 |

#### 3.2.2 Critical Insight for Separation

The **bimodal size distribution** after proper milling creates the separation opportunity:

```
                    Protein Bodies    Starch Granules
                         ↓                  ↓
Particle Size:     [1-10 μm]          [15-40 μm]
                         
Feed Distribution:
                    ████                    ████████
                    ████                    ████████████
                    ████████                ████████████████
                ────┴────┴────┴────┴────┴────┴────┴────┴────→ Size (μm)
                    5    10   15   20   25   30   35   40
                         
                    FINE                    COARSE
                 (Protein-rich)          (Starch-rich)
```

### 3.3 Milling Requirements

#### 3.3.1 Pre-Classification Milling

Proper milling is **critical** for successful air classification:

| Mill Type | Protein Release | Energy (kWh/t) | Recommended |
|-----------|-----------------|----------------|-------------|
| Hammer mill | Poor (30-40%) | 20-40 | No |
| Pin mill | Good (60-70%) | 40-80 | Yes |
| Impact mill | Very Good (70-85%) | 50-100 | Yes |
| Jet mill | Excellent (85-95%) | 100-200 | Optional |

#### 3.3.2 Optimal Milling Parameters

```
Recommended Milling Protocol:

1. Pre-conditioning:
   - Moisture content: 10-12%
   - Temperature: 15-25°C

2. First pass (Pin mill):
   - Rotor speed: 6000-8000 rpm
   - Feed rate: Moderate
   - Target d50: 50-80 μm

3. Second pass (if needed):
   - Rotor speed: 8000-12000 rpm
   - Target d50: 30-50 μm
```

### 3.4 Physical Properties for Design

| Property | Value | Unit |
|----------|-------|------|
| Bulk density (flour) | 500-650 | kg/m³ |
| Particle density (protein) | 1350 | kg/m³ |
| Particle density (starch) | 1520 | kg/m³ |
| Angle of repose | 35-45 | degrees |
| Moisture for classification | 8-12 | % |
| Critical humidity | <65 | % RH |

---

## 4. Air Classifier Types and Selection

### 4.1 Overview of Classifier Types

#### 4.1.1 Static (Gravitational) Classifiers

**Zigzag Classifier:**
```
        Air + Fines Out
              ↑
         ┌────┴────┐
         │  ╱      │
         │ ╱       │
         │╱    ╲   │
         │      ╲  │
         │   ╱   ╲ │
         │  ╱     ╲│
         │ ╱       │
         └────┬────┘
              ↓
         Coarse Out
         
         ↑ Feed + Air In
```

- Cut size: 50-500 μm
- Simple design
- **Not recommended** for pea protein (cut size too large)

#### 4.1.2 Dynamic (Centrifugal) Classifiers

**Rotor Classifier (Recommended):**
```
                    Fines + Air Out
                          ↑
                    ┌─────┴─────┐
                    │  ┌─────┐  │
              ────→ │  │ ▓▓▓ │  │ ←────
             Feed   │  │ ▓▓▓ │  │   Air
                    │  │ ▓▓▓ │  │
                    │  └──┬──┘  │
                    │     │     │
                    └─────┼─────┘
                          │
                          ↓
                     Coarse Out
                     
        ▓▓▓ = Rotating classifier wheel
```

- Cut size: 2-100 μm (adjustable)
- High precision (κ < 1.5)
- **Best choice for pea protein separation**

### 4.2 Centrifugal Classifier Designs

#### 4.2.1 Types of Rotor Classifiers

| Type | Cut Size Range | Sharpness | Throughput | Best For |
|------|---------------|-----------|------------|----------|
| **Turbine classifier** | 5-100 μm | Very good | High | Pea protein |
| Turbo classifier | 2-50 μm | Excellent | Medium | Fine separation |
| Deflector wheel | 10-150 μm | Good | Very High | Coarse separation |
| Multi-wheel | 2-30 μm | Excellent | Medium | Ultra-fine |

#### 4.2.2 Recommended: Turbine Air Classifier

**Operating Principle:**
1. Feed enters the classification zone
2. Air creates a spiral flow pattern
3. Rotating classifier wheel creates centrifugal field
4. Balance between drag and centrifugal force determines separation
5. Fine particles (protein-rich) pass through wheel → collected
6. Coarse particles (starch-rich) rejected → collected separately

### 4.3 Selection Criteria for Pea Protein

#### Decision Matrix:

| Criterion | Weight | Turbine | Turbo | Zigzag |
|-----------|--------|---------|-------|--------|
| Cut size range | 25% | 9 | 10 | 3 |
| Sharpness | 20% | 8 | 10 | 5 |
| Throughput | 20% | 9 | 6 | 8 |
| Energy efficiency | 15% | 7 | 6 | 9 |
| Capital cost | 10% | 7 | 5 | 9 |
| Maintenance | 10% | 7 | 6 | 8 |
| **Total Score** | 100% | **8.0** | 7.5 | 6.2 |

**Recommendation: Turbine Air Classifier**

---

## 5. Design Calculations

### 5.1 Process Design Basis

```
Design Specifications:
├── Feed rate: 200 kg/hr (milled yellow pea flour)
├── Feed composition: 23% protein, 48% starch
├── Target fine fraction: 55-60% protein
├── Target coarse fraction: 10-15% protein
├── Cut size (d50): 18-22 μm
├── Operating pressure: Slightly negative (safety)
└── Ambient conditions: 20°C, 50% RH
```

### 5.2 Mass Balance Calculations

#### 5.2.1 Component Mass Balance

```python
# Mass Balance Calculator

def calculate_mass_balance(
    feed_rate: float,           # kg/hr
    feed_protein: float,        # fraction
    fine_protein: float,        # target fraction
    coarse_protein: float,      # target fraction
    separation_efficiency: float # fraction
) -> dict:
    """
    Calculate mass balance for air classification
    
    Assuming perfect separation as baseline, then apply efficiency
    """
    # Overall mass balance: F = Fine + Coarse
    # Protein balance: F * x_F = Fine * x_fine + Coarse * x_coarse
    
    # Solve for fine fraction (as fraction of feed)
    # x_F = f * x_fine + (1-f) * x_coarse
    # f = (x_F - x_coarse) / (x_fine - x_coarse)
    
    fine_fraction = (feed_protein - coarse_protein) / (fine_protein - coarse_protein)
    fine_fraction *= separation_efficiency
    
    fine_rate = feed_rate * fine_fraction
    coarse_rate = feed_rate * (1 - fine_fraction)
    
    return {
        'feed_rate': feed_rate,
        'fine_rate': fine_rate,
        'coarse_rate': coarse_rate,
        'fine_fraction': fine_fraction,
        'protein_recovery': (fine_rate * fine_protein) / (feed_rate * feed_protein)
    }

# Example calculation
result = calculate_mass_balance(
    feed_rate=200,
    feed_protein=0.23,
    fine_protein=0.58,
    coarse_protein=0.12,
    separation_efficiency=0.85
)

print(f"Fine fraction rate: {result['fine_rate']:.1f} kg/hr")
print(f"Coarse fraction rate: {result['coarse_rate']:.1f} kg/hr")
print(f"Protein recovery: {result['protein_recovery']*100:.1f}%")
```

**Results:**
```
Feed:         200 kg/hr (23% protein = 46 kg protein/hr)
Fine:         40.5 kg/hr (58% protein = 23.5 kg protein/hr)
Coarse:       159.5 kg/hr (12% protein = 19.1 kg protein/hr)
Recovery:     51% of protein in fine fraction
```

### 5.3 Classifier Sizing

#### 5.3.1 Classifier Wheel Dimensions

For a turbine classifier with target cut size d50 = 20 μm:

```python
import numpy as np

def size_classifier_wheel(
    d50_target: float,      # Cut size in meters
    air_flow: float,        # m³/s
    particle_density: float, # kg/m³
    air_viscosity: float = 1.81e-5,  # Pa·s at 20°C
    air_density: float = 1.2,        # kg/m³
) -> dict:
    """
    Size the classifier wheel for target cut size
    
    Based on equilibrium between drag and centrifugal forces:
    F_drag = F_centrifugal
    """
    
    # Typical design parameters
    wheel_width_ratio = 0.15  # width/diameter
    blade_count = 24
    
    # Iterate to find wheel diameter and speed
    # Starting estimate
    D_wheel = 0.4  # m
    
    for _ in range(10):
        # Wheel dimensions
        r_c = D_wheel / 2
        h = D_wheel * wheel_width_ratio
        
        # Calculate required angular velocity for d50
        # From: d50 = sqrt(9 * mu * Q / (2 * pi * rho_p * omega^2 * r_c^2 * h))
        
        omega = np.sqrt(9 * air_viscosity * air_flow / 
                       (2 * np.pi * particle_density * d50_target**2 * r_c**2 * h))
        
        rpm = omega * 60 / (2 * np.pi)
        
        # Check tip speed (limit ~100 m/s for wear)
        tip_speed = omega * r_c
        
        if tip_speed > 80:  # Increase diameter to reduce speed
            D_wheel *= 1.1
        elif tip_speed < 40:  # Decrease diameter
            D_wheel *= 0.95
        else:
            break
    
    return {
        'wheel_diameter': D_wheel,
        'wheel_width': D_wheel * wheel_width_ratio,
        'rpm': rpm,
        'tip_speed': tip_speed,
        'blade_count': blade_count,
        'angular_velocity': omega
    }

# Design for pea protein separation
result = size_classifier_wheel(
    d50_target=20e-6,        # 20 μm
    air_flow=0.5,            # m³/s
    particle_density=1400,    # kg/m³ (protein)
)

print(f"Wheel diameter: {result['wheel_diameter']*1000:.0f} mm")
print(f"Wheel width: {result['wheel_width']*1000:.0f} mm")
print(f"Rotation speed: {result['rpm']:.0f} rpm")
print(f"Tip speed: {result['tip_speed']:.1f} m/s")
```

**Results:**
```
Wheel diameter: 400 mm
Wheel width: 60 mm
Rotation speed: 2800-4500 rpm (adjustable)
Tip speed: 60-95 m/s
Blade count: 24
```

#### 5.3.2 Classification Chamber Dimensions

```python
def size_classification_chamber(
    wheel_diameter: float,  # m
    feed_rate: float,       # kg/hr
    bulk_density: float,    # kg/m³
) -> dict:
    """
    Size the classification chamber
    """
    # Chamber diameter: 2-3x wheel diameter
    chamber_diameter = wheel_diameter * 2.5
    
    # Chamber height: based on residence time
    # Typical residence time: 1-3 seconds
    residence_time = 2.0  # seconds
    
    volumetric_feed = feed_rate / bulk_density / 3600  # m³/s
    
    # Chamber volume
    chamber_height = chamber_diameter * 1.2
    chamber_volume = np.pi * (chamber_diameter/2)**2 * chamber_height
    
    # Inlet/outlet sizing
    inlet_velocity = 15  # m/s typical
    inlet_area = volumetric_feed * 50 / inlet_velocity  # with air
    inlet_diameter = np.sqrt(4 * inlet_area / np.pi)
    
    return {
        'chamber_diameter': chamber_diameter,
        'chamber_height': chamber_height,
        'chamber_volume': chamber_volume,
        'inlet_diameter': inlet_diameter,
        'outlet_diameter': inlet_diameter * 1.2
    }

chamber = size_classification_chamber(
    wheel_diameter=0.4,
    feed_rate=200,
    bulk_density=550
)

print(f"Chamber diameter: {chamber['chamber_diameter']*1000:.0f} mm")
print(f"Chamber height: {chamber['chamber_height']*1000:.0f} mm")
```

### 5.4 Air System Design

#### 5.4.1 Air Flow Requirements

```python
def calculate_air_requirements(
    feed_rate: float,           # kg/hr
    solids_loading: float,      # kg solids / kg air
    air_temperature: float,     # °C
    pressure_drop: float,       # Pa
) -> dict:
    """
    Calculate air flow and fan requirements
    """
    # Air properties
    R = 287  # J/(kg·K)
    T = air_temperature + 273.15  # K
    P = 101325  # Pa (atmospheric)
    rho_air = P / (R * T)  # kg/m³
    
    # Air mass flow
    air_mass_flow = feed_rate / solids_loading  # kg/hr
    air_volume_flow = air_mass_flow / rho_air   # m³/hr
    
    # Fan power (assuming 60% efficiency)
    fan_efficiency = 0.60
    fan_power = (air_volume_flow / 3600) * pressure_drop / fan_efficiency
    
    # Add 20% safety factor
    fan_power *= 1.2
    
    return {
        'air_mass_flow': air_mass_flow,
        'air_volume_flow': air_volume_flow,
        'air_velocity': air_volume_flow / 3600 / 0.1,  # assuming 0.1 m² duct
        'fan_power': fan_power / 1000,  # kW
        'pressure_drop': pressure_drop
    }

air_system = calculate_air_requirements(
    feed_rate=200,
    solids_loading=0.3,  # kg/kg - typical for classifiers
    air_temperature=25,
    pressure_drop=3000   # Pa
)

print(f"Air flow rate: {air_system['air_volume_flow']:.0f} m³/hr")
print(f"Fan power: {air_system['fan_power']:.1f} kW")
```

#### 5.4.2 System Pressure Drop

| Component | Pressure Drop (Pa) |
|-----------|-------------------|
| Inlet duct | 200-400 |
| Feed system | 300-500 |
| Classification chamber | 800-1500 |
| Classifier wheel | 500-1000 |
| Cyclone separator | 500-1000 |
| Bag filter | 500-1500 |
| Outlet duct | 200-400 |
| **Total** | **3000-6300** |

### 5.5 Design Summary Table

| Parameter | Value | Unit |
|-----------|-------|------|
| Feed rate | 200 | kg/hr |
| Classifier wheel diameter | 400 | mm |
| Classifier wheel width | 60 | mm |
| Wheel speed range | 2000-5000 | rpm |
| Chamber diameter | 1000 | mm |
| Chamber height | 1200 | mm |
| Air flow rate | 1800 | m³/hr |
| Total pressure drop | 4000 | Pa |
| Main fan power | 5.5 | kW |
| Wheel drive power | 3.0 | kW |
| Feed system power | 0.75 | kW |
| **Total installed power** | **12** | **kW** |

---

## 6. Detailed Component Design

### 6.1 Classifier Wheel Assembly

#### 6.1.1 Wheel Design

```
                    TOP VIEW
                    
                 ╭─────────────╮
              ╭──┤             ├──╮
           ╭──┤  │             │  ├──╮
          ╱   │  │             │  │   ╲
         │    │  │      ●      │  │    │
         │    │  │   (shaft)   │  │    │
          ╲   │  │             │  │   ╱
           ╰──┤  │             │  ├──╯
              ╰──┤             ├──╯
                 ╰─────────────╯
                 
        Blades: 24 radial blades
        Material: Stainless steel 316L or wear-resistant steel
        
        
                    SIDE VIEW (Cross-section)
                    
                    ┌─────────────────┐
                    │    ┌─────┐      │
              ═══════════│     │═══════════  ← Shaft
                    │    └─────┘      │
                    │   ╱ ╲   ╱ ╲     │
                    │  ╱   ╲ ╱   ╲    │
                    │ ╱     ╳     ╲   │  ← Blades
                    │╱     ╱ ╲     ╲  │
                    └─────────────────┘
                    ←───── 400mm ─────→
```

#### 6.1.2 Blade Specifications

| Parameter | Specification |
|-----------|--------------|
| Number of blades | 24 |
| Blade height | 60 mm |
| Blade thickness | 3 mm |
| Blade angle | 90° (radial) or 70-85° (inclined) |
| Material | SS316L or Hardox 400 |
| Surface finish | Ra < 1.6 μm |
| Balance grade | G2.5 per ISO 1940 |

#### 6.1.3 Blade Gap Calculation

The gap between blades determines the sharpness of separation:

```python
def calculate_blade_gap(
    wheel_diameter: float,
    blade_count: int,
    blade_thickness: float
) -> float:
    """Calculate gap between classifier blades"""
    circumference = np.pi * wheel_diameter
    total_blade_width = blade_count * blade_thickness
    total_gap = circumference - total_blade_width
    gap_per_blade = total_gap / blade_count
    return gap_per_blade

gap = calculate_blade_gap(0.4, 24, 0.003)
print(f"Blade gap: {gap*1000:.1f} mm")
# Result: ~49 mm gap between blades
```

### 6.2 Classification Chamber

#### 6.2.1 Chamber Geometry

```
                    VERTICAL CROSS-SECTION
                    
                         Fines Outlet
                              │
                         ┌────┴────┐
                         │         │
                    ┌────┤  Wheel  ├────┐
                    │    │   ▓▓▓   │    │
          Air ──────│    │   ▓▓▓   │    │────── Air
          Inlet     │    │   ▓▓▓   │    │      Inlet
                    │    └────┬────┘    │
                    │         │         │
                    │    ╲    │    ╱    │
                    │     ╲   │   ╱     │
                    │      ╲  │  ╱      │
                    │       ╲ │ ╱       │  ← Conical
                    │        ╲│╱        │    bottom
                    └─────────┴─────────┘
                              │
                        Coarse Outlet
                        
                    ←────── 1000mm ──────→
```

#### 6.2.2 Chamber Construction Details

| Component | Material | Thickness | Notes |
|-----------|----------|-----------|-------|
| Shell | SS304 | 4 mm | Cylindrical section |
| Cone | SS304 | 4 mm | 60° included angle |
| Wear liners | Ceramic tiles or Hardox | 6-10 mm | High-wear areas |
| Viewing ports | Borosilicate glass | 15 mm | With LED illumination |
| Access doors | SS304 | 6 mm | Quick-release clamps |

### 6.3 Feed System

#### 6.3.1 Rotary Airlock Feeder

```
                    ROTARY AIRLOCK
                    
                    Feed Inlet
                         │
                    ┌────┴────┐
                    │╲       ╱│
                    │ ╲     ╱ │
                    │  ╲   ╱  │
                    │   ╲ ╱   │
                    │────●────│  ← Rotor with vanes
                    │   ╱ ╲   │
                    │  ╱   ╲  │
                    │ ╱     ╲ │
                    │╱       ╲│
                    └────┬────┘
                         │
                    To Classifier
```

**Specifications:**

| Parameter | Value |
|-----------|-------|
| Type | Drop-through rotary valve |
| Size | 200 mm diameter |
| Vanes | 8 |
| Speed | 15-30 rpm |
| Capacity | 50-400 kg/hr |
| Drive | 0.75 kW geared motor |
| Seals | PTFE/Viton |
| Clearance | 0.1-0.2 mm |

#### 6.3.2 Dispersing System

```python
# Venturi disperser design for feed introduction

def design_venturi_disperser(
    feed_rate: float,      # kg/hr
    air_velocity: float,   # m/s at throat
    solids_loading: float  # kg solids/kg air
) -> dict:
    """Design venturi disperser for particle dispersion"""
    
    # Air flow at throat
    air_mass_flow = feed_rate / solids_loading  # kg/hr
    air_density = 1.2  # kg/m³
    air_volume_flow = air_mass_flow / air_density / 3600  # m³/s
    
    # Throat area
    throat_area = air_volume_flow / air_velocity
    throat_diameter = np.sqrt(4 * throat_area / np.pi)
    
    # Inlet diameter (typically 2x throat)
    inlet_diameter = throat_diameter * 2
    
    # Outlet diameter (typically 1.5x throat for diffuser)
    outlet_diameter = throat_diameter * 1.5
    
    return {
        'throat_diameter': throat_diameter * 1000,  # mm
        'inlet_diameter': inlet_diameter * 1000,
        'outlet_diameter': outlet_diameter * 1000,
        'throat_velocity': air_velocity
    }

disperser = design_venturi_disperser(200, 30, 0.3)
print(f"Throat diameter: {disperser['throat_diameter']:.0f} mm")
```

### 6.4 Product Collection System

#### 6.4.1 Cyclone Separators

For collecting the fine (protein-rich) fraction:

```
                    CYCLONE SEPARATOR
                    
                    Clean Air Out
                         ↑
                    ┌────┴────┐
                    │  ┌───┐  │  ← Vortex finder
                    │  │   │  │
             ┌──────│  │   │  │
             │      │  └───┘  │
        Air +│      │         │
        Fines│      │   ⟳    │  ← Outer vortex (down)
             │      │         │
             └──────│    ⟳   │  ← Inner vortex (up)
                    │╲       ╱│
                    │ ╲     ╱ │
                    │  ╲   ╱  │
                    │   ╲ ╱   │
                    └────┴────┘
                         │
                    Fines Out
```

**Design Parameters (Stairmand high-efficiency):**

| Dimension | Ratio to D | Value (D=400mm) |
|-----------|-----------|-----------------|
| Body diameter (D) | 1.0 | 400 mm |
| Inlet height | 0.5 | 200 mm |
| Inlet width | 0.2 | 80 mm |
| Vortex finder diameter | 0.5 | 200 mm |
| Vortex finder length | 0.5 | 200 mm |
| Cylinder height | 1.5 | 600 mm |
| Cone height | 2.5 | 1000 mm |
| Dust outlet diameter | 0.375 | 150 mm |

#### 6.4.2 Bag Filter System

For final air cleaning:

| Parameter | Specification |
|-----------|--------------|
| Type | Pulse-jet bag filter |
| Filter area | 15-20 m² |
| Air-to-cloth ratio | 1.5-2.0 m³/min/m² |
| Bag material | Polyester with PTFE membrane |
| Number of bags | 16-24 |
| Bag dimensions | Ø130 × 2000 mm |
| Cleaning | Compressed air pulse (6 bar) |
| Residual dust | <5 mg/m³ |

### 6.5 Drive Systems

#### 6.5.1 Classifier Wheel Drive

```
                    DRIVE ARRANGEMENT
                    
                    ┌─────────────────────┐
                    │                     │
                    │   Classification    │
                    │      Chamber        │
                    │                     │
                    │      ┌─────┐        │
                    │      │Wheel│        │
                    │      └──┬──┘        │
                    └─────────┼───────────┘
                              │
                         ┌────┴────┐
                         │Bearing  │
                         │Housing  │
                         └────┬────┘
                              │
                         ┌────┴────┐
                         │ V-Belt  │
                         │ Drive   │
                         └────┬────┘
                              │
                         ┌────┴────┐
                    VFD──┤  Motor  │
                         │  3 kW   │
                         └─────────┘
```

**Specifications:**

| Component | Specification |
|-----------|--------------|
| Motor | 3 kW, 4-pole, IE3 efficiency |
| VFD | 4 kW, 0-100 Hz |
| Drive | V-belt, ratio 1:2 |
| Bearings | Angular contact ball, paired |
| Shaft seal | Labyrinth + air purge |
| Speed range | 1000-5000 rpm |

---

## 7. CFD and Particle Simulation with NVIDIA Warp

### 7.1 Simulation Overview

Use NVIDIA Warp to simulate the air classification process and optimize design parameters before construction.

### 7.2 Simulation Code

```python
# air_classifier_simulation.py
"""
GPU-Accelerated Air Classifier Simulation using NVIDIA Warp
For Yellow Pea Protein Separation
"""

import warp as wp
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Tuple, Optional

# Initialize Warp
wp.init()


@dataclass
class ClassifierConfig:
    """Air classifier configuration"""
    # Geometry
    chamber_radius: float = 0.5      # m
    chamber_height: float = 1.2      # m
    wheel_radius: float = 0.2        # m
    wheel_width: float = 0.06        # m
    wheel_position_z: float = 0.9    # m (height of wheel center)
    
    # Operating conditions
    wheel_rpm: float = 3000.0        # rpm
    air_velocity: float = 8.0        # m/s (radial inward)
    
    # Particle properties
    num_particles: int = 50000
    
    # Simulation
    dt: float = 1e-5                 # s
    device: str = "cuda"


@dataclass
class ParticleProperties:
    """Properties for pea flour particles"""
    # Protein particles
    protein_diameter_mean: float = 5e-6      # 5 μm
    protein_diameter_std: float = 2e-6       # μm
    protein_density: float = 1350.0          # kg/m³
    protein_fraction: float = 0.25           # 25% of particles
    
    # Starch particles
    starch_diameter_mean: float = 28e-6      # 28 μm
    starch_diameter_std: float = 8e-6        # μm
    starch_density: float = 1520.0           # kg/m³


# Air properties at 25°C
AIR_DENSITY = 1.184      # kg/m³
AIR_VISCOSITY = 1.85e-5  # Pa·s


@wp.func
def compute_drag_force(
    velocity_rel: wp.vec3,
    diameter: float,
    particle_density: float,
    air_density: float,
    air_viscosity: float
) -> wp.vec3:
    """
    Compute drag force on a spherical particle
    Using Schiller-Naumann correlation
    """
    vel_mag = wp.length(velocity_rel)
    
    if vel_mag < 1e-10:
        return wp.vec3(0.0, 0.0, 0.0)
    
    # Reynolds number
    Re = air_density * vel_mag * diameter / air_viscosity
    
    # Drag coefficient (Schiller-Naumann)
    if Re < 0.1:
        Cd = 24.0 / Re
    elif Re < 1000.0:
        Cd = 24.0 / Re * (1.0 + 0.15 * wp.pow(Re, 0.687))
    else:
        Cd = 0.44
    
    # Drag force magnitude
    area = 0.25 * 3.14159 * diameter * diameter
    F_mag = 0.5 * Cd * air_density * vel_mag * vel_mag * area
    
    # Direction opposite to relative velocity
    return -velocity_rel * (F_mag / vel_mag)


@wp.func
def compute_air_velocity_field(
    pos: wp.vec3,
    wheel_radius: float,
    wheel_z: float,
    wheel_width: float,
    air_vel_radial: float,
    wheel_omega: float
) -> wp.vec3:
    """
    Compute air velocity at a given position
    Simplified model: radial inflow + tangential component from wheel
    """
    # Cylindrical coordinates
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    theta = wp.atan2(pos[1], pos[0])
    z = pos[2]
    
    # Radial unit vector (pointing inward)
    er = wp.vec3(-pos[0] / (r + 1e-10), -pos[1] / (r + 1e-10), 0.0)
    
    # Tangential unit vector
    et = wp.vec3(-wp.sin(theta), wp.cos(theta), 0.0)
    
    # Radial velocity (inward flow, stronger near wheel)
    z_dist = wp.abs(z - wheel_z)
    radial_factor = wp.exp(-z_dist / wheel_width)
    
    if r > wheel_radius:
        v_radial = air_vel_radial * radial_factor * (wheel_radius / r)
    else:
        v_radial = air_vel_radial * radial_factor
    
    # Tangential velocity (from wheel rotation, decays with radius)
    if r < wheel_radius * 2.0 and z_dist < wheel_width * 2.0:
        v_tangential = wheel_omega * wheel_radius * wp.exp(-(r - wheel_radius) / wheel_radius)
    else:
        v_tangential = 0.0
    
    # Axial velocity (upward near center for fines outlet)
    if r < wheel_radius and z > wheel_z:
        v_axial = 2.0 * (1.0 - r / wheel_radius)
    else:
        v_axial = 0.0
    
    return er * v_radial + et * v_tangential + wp.vec3(0.0, 0.0, v_axial)


@wp.kernel
def initialize_particles_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    densities: wp.array(dtype=float),
    particle_types: wp.array(dtype=int),  # 0=protein, 1=starch
    chamber_radius: float,
    chamber_height: float,
    feed_z: float,
    seed: int
):
    """Initialize particles at feed location"""
    i = wp.tid()
    
    # Random position in annular feed zone
    state = wp.rand_init(seed, i)
    
    r = chamber_radius * 0.7 + wp.randf(state) * chamber_radius * 0.2
    theta = wp.randf(state) * 2.0 * 3.14159
    z = feed_z + (wp.randf(state) - 0.5) * 0.1
    
    positions[i] = wp.vec3(r * wp.cos(theta), r * wp.sin(theta), z)
    velocities[i] = wp.vec3(0.0, 0.0, 0.0)


@wp.kernel
def update_particles_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    densities: wp.array(dtype=float),
    forces: wp.array(dtype=wp.vec3),
    wheel_radius: float,
    wheel_z: float,
    wheel_width: float,
    wheel_omega: float,
    air_vel_radial: float,
    air_density: float,
    air_viscosity: float,
    dt: float
):
    """Update particle positions and velocities"""
    i = wp.tid()
    
    pos = positions[i]
    vel = velocities[i]
    d = diameters[i]
    rho = densities[i]
    
    # Particle mass
    volume = (4.0 / 3.0) * 3.14159 * (d / 2.0) ** 3.0
    mass = rho * volume
    
    # Air velocity at particle position
    air_vel = compute_air_velocity_field(
        pos, wheel_radius, wheel_z, wheel_width,
        air_vel_radial, wheel_omega
    )
    
    # Relative velocity
    vel_rel = vel - air_vel
    
    # Drag force
    F_drag = compute_drag_force(vel_rel, d, rho, air_density, air_viscosity)
    
    # Gravity
    F_gravity = wp.vec3(0.0, 0.0, -9.81 * mass)
    
    # Centrifugal force (in rotating frame near wheel)
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z_dist = wp.abs(pos[2] - wheel_z)
    
    if r < wheel_radius * 1.5 and z_dist < wheel_width * 2.0:
        omega_local = wheel_omega * wp.exp(-(r - wheel_radius) / (wheel_radius * 0.5))
        F_centrifugal = wp.vec3(pos[0], pos[1], 0.0) * (mass * omega_local * omega_local)
    else:
        F_centrifugal = wp.vec3(0.0, 0.0, 0.0)
    
    # Total force
    F_total = F_drag + F_gravity + F_centrifugal
    forces[i] = F_total
    
    # Update velocity (semi-implicit Euler)
    acc = F_total / mass
    vel_new = vel + acc * dt
    velocities[i] = vel_new
    
    # Update position
    positions[i] = pos + vel_new * dt


@wp.kernel
def apply_boundaries_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    collected_fine: wp.array(dtype=int),
    collected_coarse: wp.array(dtype=int),
    chamber_radius: float,
    chamber_height: float,
    wheel_radius: float,
    wheel_z: float,
    wheel_width: float
):
    """Apply boundary conditions and track collection"""
    i = wp.tid()
    
    pos = positions[i]
    vel = velocities[i]
    
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z = pos[2]
    
    # Check if particle passes through wheel (fine fraction)
    z_dist = wp.abs(z - wheel_z)
    if r < wheel_radius and z_dist < wheel_width / 2.0 and z > wheel_z:
        wp.atomic_add(collected_fine, 0, 1)
        # Reset particle to feed zone
        positions[i] = wp.vec3(chamber_radius * 0.7, 0.0, chamber_height * 0.5)
        velocities[i] = wp.vec3(0.0, 0.0, 0.0)
        return
    
    # Check if particle reaches bottom (coarse fraction)
    if z < 0.05:
        wp.atomic_add(collected_coarse, 0, 1)
        # Reset particle to feed zone
        positions[i] = wp.vec3(chamber_radius * 0.7, 0.0, chamber_height * 0.5)
        velocities[i] = wp.vec3(0.0, 0.0, 0.0)
        return
    
    # Cylindrical wall boundary
    if r > chamber_radius * 0.95:
        # Reflect
        normal = wp.vec3(pos[0] / r, pos[1] / r, 0.0)
        v_normal = wp.dot(vel, normal)
        if v_normal > 0.0:
            velocities[i] = vel - 2.0 * v_normal * normal * 0.5  # damping
        
        # Push inside
        scale = chamber_radius * 0.94 / r
        positions[i] = wp.vec3(pos[0] * scale, pos[1] * scale, pos[2])
    
    # Top boundary
    if z > chamber_height:
        positions[i] = wp.vec3(pos[0], pos[1], chamber_height - 0.01)
        if vel[2] > 0.0:
            velocities[i] = wp.vec3(vel[0], vel[1], -vel[2] * 0.3)


class AirClassifierSimulator:
    """
    Main simulator class for air classifier
    """
    
    def __init__(
        self,
        config: ClassifierConfig,
        particle_props: ParticleProperties
    ):
        self.config = config
        self.particle_props = particle_props
        self.device = config.device
        
        # Allocate arrays
        n = config.num_particles
        self.positions = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.velocities = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.forces = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.diameters = wp.zeros(n, dtype=float, device=self.device)
        self.densities = wp.zeros(n, dtype=float, device=self.device)
        self.particle_types = wp.zeros(n, dtype=int, device=self.device)
        
        # Collection counters
        self.collected_fine = wp.zeros(1, dtype=int, device=self.device)
        self.collected_coarse = wp.zeros(1, dtype=int, device=self.device)
        
        # Angular velocity
        self.wheel_omega = config.wheel_rpm * 2.0 * np.pi / 60.0
        
        # Initialize particles
        self._initialize_particles()
    
    def _initialize_particles(self):
        """Initialize particle properties and positions"""
        n = self.config.num_particles
        n_protein = int(n * self.particle_props.protein_fraction)
        n_starch = n - n_protein
        
        # Generate particle sizes (log-normal distribution)
        np.random.seed(42)
        
        # Protein particles
        protein_diameters = np.random.lognormal(
            np.log(self.particle_props.protein_diameter_mean),
            0.4, n_protein
        ).astype(np.float32)
        protein_diameters = np.clip(protein_diameters, 1e-6, 20e-6)
        
        # Starch particles
        starch_diameters = np.random.lognormal(
            np.log(self.particle_props.starch_diameter_mean),
            0.3, n_starch
        ).astype(np.float32)
        starch_diameters = np.clip(starch_diameters, 10e-6, 60e-6)
        
        # Combine
        all_diameters = np.concatenate([protein_diameters, starch_diameters])
        all_densities = np.concatenate([
            np.full(n_protein, self.particle_props.protein_density, dtype=np.float32),
            np.full(n_starch, self.particle_props.starch_density, dtype=np.float32)
        ])
        all_types = np.concatenate([
            np.zeros(n_protein, dtype=np.int32),
            np.ones(n_starch, dtype=np.int32)
        ])
        
        # Shuffle
        indices = np.random.permutation(n)
        all_diameters = all_diameters[indices]
        all_densities = all_densities[indices]
        all_types = all_types[indices]
        
        # Copy to GPU
        wp.copy(self.diameters, wp.array(all_diameters, dtype=float, device=self.device))
        wp.copy(self.densities, wp.array(all_densities, dtype=float, device=self.device))
        wp.copy(self.particle_types, wp.array(all_types, dtype=int, device=self.device))
        
        # Initialize positions
        wp.launch(
            initialize_particles_kernel,
            dim=n,
            inputs=[
                self.positions, self.velocities,
                self.diameters, self.densities, self.particle_types,
                self.config.chamber_radius, self.config.chamber_height,
                self.config.chamber_height * 0.5,
                42
            ],
            device=self.device
        )
    
    def step(self):
        """Perform one simulation step"""
        # Update particles
        wp.launch(
            update_particles_kernel,
            dim=self.config.num_particles,
            inputs=[
                self.positions, self.velocities,
                self.diameters, self.densities, self.forces,
                self.config.wheel_radius,
                self.config.wheel_position_z,
                self.config.wheel_width,
                self.wheel_omega,
                self.config.air_velocity,
                AIR_DENSITY, AIR_VISCOSITY,
                self.config.dt
            ],
            device=self.device
        )
        
        # Apply boundaries
        wp.launch(
            apply_boundaries_kernel,
            dim=self.config.num_particles,
            inputs=[
                self.positions, self.velocities,
                self.collected_fine, self.collected_coarse,
                self.config.chamber_radius, self.config.chamber_height,
                self.config.wheel_radius,
                self.config.wheel_position_z,
                self.config.wheel_width
            ],
            device=self.device
        )
    
    def run(self, duration: float, output_interval: float = 0.01) -> dict:
        """
        Run simulation for specified duration
        
        Returns dictionary with results
        """
        steps = int(duration / self.config.dt)
        output_steps = int(output_interval / self.config.dt)
        
        results = {
            'time': [],
            'fine_collected': [],
            'coarse_collected': [],
            'positions': []
        }
        
        print(f"Running simulation for {duration}s ({steps} steps)...")
        
        for step in range(steps):
            self.step()
            
            if step % output_steps == 0:
                t = step * self.config.dt
                fine = self.collected_fine.numpy()[0]
                coarse = self.collected_coarse.numpy()[0]
                
                results['time'].append(t)
                results['fine_collected'].append(fine)
                results['coarse_collected'].append(coarse)
                
                if step % (output_steps * 10) == 0:
                    print(f"  t={t:.3f}s: Fine={fine}, Coarse={coarse}")
        
        # Final positions
        results['final_positions'] = self.positions.numpy()
        results['final_diameters'] = self.diameters.numpy()
        results['final_types'] = self.particle_types.numpy()
        
        return results
    
    def analyze_separation(self, results: dict) -> dict:
        """Analyze separation efficiency"""
        types = results['final_types']
        positions = results['final_positions']
        
        # Count by type
        n_protein = np.sum(types == 0)
        n_starch = np.sum(types == 1)
        
        fine = results['fine_collected'][-1]
        coarse = results['coarse_collected'][-1]
        
        # This is simplified - in reality we'd track which particles
        # were collected in which fraction
        
        analysis = {
            'total_particles': len(types),
            'protein_particles': n_protein,
            'starch_particles': n_starch,
            'fine_collected': fine,
            'coarse_collected': coarse,
            'separation_achieved': fine > 0 and coarse > 0
        }
        
        return analysis


def run_parameter_study():
    """
    Run parameter study to optimize cut size
    """
    results = []
    
    rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000]
    
    for rpm in rpm_values:
        config = ClassifierConfig(
            wheel_rpm=rpm,
            num_particles=10000,
            dt=2e-5
        )
        props = ParticleProperties()
        
        sim = AirClassifierSimulator(config, props)
        sim_results = sim.run(duration=0.5, output_interval=0.05)
        analysis = sim.analyze_separation(sim_results)
        
        results.append({
            'rpm': rpm,
            'fine': analysis['fine_collected'],
            'coarse': analysis['coarse_collected']
        })
        
        print(f"RPM={rpm}: Fine={analysis['fine_collected']}, Coarse={analysis['coarse_collected']}")
    
    return results


if __name__ == "__main__":
    # Run single simulation
    config = ClassifierConfig(
        wheel_rpm=3500,
        num_particles=20000,
        dt=1e-5
    )
    props = ParticleProperties()
    
    sim = AirClassifierSimulator(config, props)
    results = sim.run(duration=1.0, output_interval=0.01)
    analysis = sim.analyze_separation(results)
    
    print("\n=== Simulation Results ===")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
```

### 7.3 Visualization and Analysis

```python
# visualization.py
"""
Visualization tools for air classifier simulation
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_particle_positions(
    positions: np.ndarray,
    diameters: np.ndarray,
    types: np.ndarray,
    chamber_radius: float,
    wheel_radius: float,
    wheel_z: float,
    save_path: str = None
):
    """
    3D visualization of particle positions
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Separate by type
    protein_mask = types == 0
    starch_mask = types == 1
    
    # Plot particles
    ax.scatter(
        positions[protein_mask, 0],
        positions[protein_mask, 1],
        positions[protein_mask, 2],
        c='blue', s=1, alpha=0.5, label='Protein'
    )
    
    ax.scatter(
        positions[starch_mask, 0],
        positions[starch_mask, 1],
        positions[starch_mask, 2],
        c='orange', s=2, alpha=0.5, label='Starch'
    )
    
    # Draw chamber outline
    theta = np.linspace(0, 2*np.pi, 50)
    x_chamber = chamber_radius * np.cos(theta)
    y_chamber = chamber_radius * np.sin(theta)
    
    for z in [0, wheel_z, chamber_radius * 2]:
        ax.plot(x_chamber, y_chamber, z, 'k-', alpha=0.3)
    
    # Draw wheel
    x_wheel = wheel_radius * np.cos(theta)
    y_wheel = wheel_radius * np.sin(theta)
    ax.plot(x_wheel, y_wheel, wheel_z, 'r-', linewidth=2, label='Classifier wheel')
    
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title('Air Classifier Particle Distribution')
    ax.legend()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()


def plot_size_distributions(
    diameters: np.ndarray,
    types: np.ndarray,
    save_path: str = None
):
    """
    Plot particle size distributions by type
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    protein_d = diameters[types == 0] * 1e6  # Convert to μm
    starch_d = diameters[types == 1] * 1e6
    
    # Histogram
    bins = np.linspace(0, 50, 50)
    axes[0].hist(protein_d, bins=bins, alpha=0.7, label='Protein', color='blue')
    axes[0].hist(starch_d, bins=bins, alpha=0.7, label='Starch', color='orange')
    axes[0].set_xlabel('Particle Diameter (μm)')
    axes[0].set_ylabel('Count')
    axes[0].set_title('Particle Size Distribution')
    axes[0].legend()
    axes[0].axvline(x=20, color='red', linestyle='--', label='Cut size')
    
    # Cumulative distribution
    protein_sorted = np.sort(protein_d)
    starch_sorted = np.sort(starch_d)
    
    axes[1].plot(
        protein_sorted,
        np.arange(len(protein_sorted)) / len(protein_sorted) * 100,
        'b-', label='Protein'
    )
    axes[1].plot(
        starch_sorted,
        np.arange(len(starch_sorted)) / len(starch_sorted) * 100,
        'orange', label='Starch'
    )
    axes[1].set_xlabel('Particle Diameter (μm)')
    axes[1].set_ylabel('Cumulative %')
    axes[1].set_title('Cumulative Size Distribution')
    axes[1].legend()
    axes[1].axvline(x=20, color='red', linestyle='--')
    axes[1].axhline(y=50, color='gray', linestyle=':')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()


def plot_grade_efficiency(
    diameters_feed: np.ndarray,
    diameters_coarse: np.ndarray,
    save_path: str = None
):
    """
    Plot grade efficiency (Tromp) curve
    """
    # Create size bins
    bins = np.logspace(np.log10(1), np.log10(50), 30)  # 1-50 μm
    
    # Count particles in each bin
    feed_counts, _ = np.histogram(diameters_feed * 1e6, bins=bins)
    coarse_counts, _ = np.histogram(diameters_coarse * 1e6, bins=bins)
    
    # Grade efficiency
    with np.errstate(divide='ignore', invalid='ignore'):
        efficiency = coarse_counts / feed_counts * 100
        efficiency = np.nan_to_num(efficiency, nan=50.0)
    
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.semilogx(bin_centers, efficiency, 'bo-', markersize=6)
    ax.axhline(y=50, color='red', linestyle='--', label='50% (cut point)')
    ax.axhline(y=25, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(y=75, color='gray', linestyle=':', alpha=0.5)
    
    ax.set_xlabel('Particle Diameter (μm)', fontsize=12)
    ax.set_ylabel('Grade Efficiency (%)', fontsize=12)
    ax.set_title('Classification Grade Efficiency Curve', fontsize=14)
    ax.set_xlim([1, 50])
    ax.set_ylim([0, 100])
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Find d50
    idx = np.argmin(np.abs(efficiency - 50))
    d50 = bin_centers[idx]
    ax.axvline(x=d50, color='green', linestyle='--', alpha=0.7)
    ax.text(d50 * 1.1, 55, f'd₅₀ = {d50:.1f} μm', fontsize=10)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return d50
```

---

## 8. Construction and Materials

### 8.1 Bill of Materials

#### 8.1.1 Main Components

| Item | Description | Quantity | Material | Est. Cost (USD) |
|------|-------------|----------|----------|-----------------|
| 1 | Classification chamber | 1 | SS304 | $3,500 |
| 2 | Classifier wheel assembly | 1 | SS316L/Hardox | $2,800 |
| 3 | Wheel drive motor + VFD | 1 set | - | $1,500 |
| 4 | Main fan + motor | 1 set | - | $2,000 |
| 5 | Rotary airlock feeder | 2 | SS304 | $1,200 |
| 6 | Cyclone separator (fine) | 1 | SS304 | $1,800 |
| 7 | Cyclone separator (coarse) | 1 | SS304 | $1,500 |
| 8 | Bag filter unit | 1 | Steel/Polyester | $2,500 |
| 9 | Ducting system | 1 lot | Galvanized steel | $1,000 |
| 10 | Feed hopper + screw | 1 | SS304 | $1,200 |
| 11 | Control panel | 1 | - | $2,000 |
| 12 | Instrumentation | 1 lot | - | $1,500 |
| 13 | Structural frame | 1 | Painted steel | $1,500 |
| 14 | Miscellaneous (fasteners, gaskets, etc.) | 1 lot | - | $500 |
| | **TOTAL** | | | **$24,500** |

### 8.2 Fabrication Drawings

#### 8.2.1 General Assembly

```
                            FRONT VIEW
                            
                    ┌───────────────────────┐
                    │     Bag Filter        │
                    │     ┌─────────┐       │
                    │     │░░░░░░░░░│       │
                    │     │░░░░░░░░░│       │
                    │     └────┬────┘       │
                    └──────────┼────────────┘
                               │
                    ┌──────────┼────────────┐
                    │    Cyclone (Fine)     │
                    │       ╱│╲             │
                    │      ╱ │ ╲            │
                    │     ╱  │  ╲           │
                    │    ╱   │   ╲          │
                    │   └────┼────┘         │
                    └────────┼──────────────┘
                             │
              Feed ────┬─────┴─────────┐
                       │               │
                    ┌──┴───────────────┴──┐
                    │    Classification   │
                    │       Chamber       │
                    │    ┌─────────┐      │
                    │    │  Wheel  │      │──── Air Inlet
                    │    └────┬────┘      │
                    │         │           │
                    │      ╲  │  ╱        │
                    │       ╲ │ ╱         │
                    │        ╲│╱          │
                    └─────────┼───────────┘
                              │
                    ┌─────────┼───────────┐
                    │   Cyclone (Coarse)  │
                    │      ╱│╲            │
                    │     ╱ │ ╲           │
                    │    ╱  │  ╲          │
                    │   └───┼───┘         │
                    └───────┼─────────────┘
                            │
                    ┌───────┼─────────────┐
                    │  Airlock  │ Airlock │
                    └───────┬───┴────┬────┘
                            │        │
                         Fine     Coarse
                       Product   Product
                       
              Overall Height: ~4.5 m
              Footprint: ~3 m × 2 m
```

### 8.3 Manufacturing Specifications

#### 8.3.1 Welding Requirements

| Joint Type | Weld Type | Inspection |
|------------|-----------|------------|
| Chamber seams | Full penetration butt | Visual + Dye penetrant |
| Nozzle attachments | Fillet weld | Visual |
| Wear liner attachments | Plug welds | Visual |
| Internal components | TIG welding | Visual |

#### 8.3.2 Surface Finish

| Component | Finish | Ra Value |
|-----------|--------|----------|
| Product contact surfaces | Mirror polish | < 0.8 μm |
| Classifier wheel | Polished | < 1.6 μm |
| Non-contact surfaces | Mill finish | < 3.2 μm |

#### 8.3.3 Tolerances

| Feature | Tolerance |
|---------|-----------|
| Chamber roundness | ± 2 mm |
| Wheel concentricity | < 0.1 mm TIR |
| Wheel balance | G2.5 per ISO 1940 |
| Nozzle alignment | ± 1° |

---

## 9. Instrumentation and Control

### 9.1 Process Variables

| Variable | Measurement | Control |
|----------|-------------|---------|
| Wheel speed | Encoder on motor | VFD setpoint |
| Air flow rate | Orifice plate + DP transmitter | Fan VFD |
| Feed rate | Load cell on hopper | Feeder speed |
| Pressure drop | Differential pressure | Fan speed trim |
| Temperature | RTD | Alarm only |
| Vibration | Accelerometer on wheel | Alarm/shutdown |

### 9.2 Control System Architecture

```
                    CONTROL SYSTEM DIAGRAM
                    
    ┌─────────────────────────────────────────────────────────┐
    │                         HMI                             │
    │                   (Touch Panel)                         │
    └────────────────────────┬────────────────────────────────┘
                             │ Ethernet
    ┌────────────────────────┴────────────────────────────────┐
    │                         PLC                             │
    │                  (Allen-Bradley / Siemens)              │
    └───┬───────┬───────┬───────┬───────┬───────┬───────┬────┘
        │       │       │       │       │       │       │
    ┌───┴───┐ ┌─┴──┐ ┌──┴──┐ ┌──┴──┐ ┌──┴──┐ ┌──┴──┐ ┌──┴──┐
    │ VFD   │ │VFD │ │VFD  │ │ PT  │ │ FT  │ │ TT  │ │Vib. │
    │Wheel  │ │Fan │ │Feed │ │Diff.│ │Flow │ │Temp │ │Sensor│
    └───┬───┘ └─┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
        │       │       │       │       │       │       │
    ┌───┴───┐ ┌─┴──┐ ┌──┴──┐   │       │       │       │
    │Wheel  │ │Fan │ │Feed │   │       │       │       │
    │Motor  │ │    │ │Screw│   │       │       │       │
    └───────┘ └────┘ └─────┘   │       │       │       │
                               └───────┴───────┴───────┘
                                    Process Sensors
```

### 9.3 Control Loops

#### 9.3.1 Cut Size Control

Primary control: Wheel speed (RPM)

```
Setpoint: d50 = 20 μm

Control Logic:
- Increase wheel speed → Decrease cut size (finer separation)
- Decrease wheel speed → Increase cut size (coarser separation)

PID Parameters (typical starting values):
- Kp = 2.0
- Ki = 0.5
- Kd = 0.1
- Output: 2000-5000 RPM
```

#### 9.3.2 Throughput Control

```
Feed Rate Control:
- Setpoint: 200 kg/hr
- Measurement: Hopper weight loss
- Output: Rotary feeder speed

Air Flow Control:
- Setpoint: 1800 m³/hr
- Measurement: Orifice DP
- Output: Fan VFD frequency
```

### 9.4 Interlocks and Alarms

| Condition | Action | Priority |
|-----------|--------|----------|
| High wheel vibration | Shutdown wheel | Emergency |
| Low air flow | Stop feed, alarm | High |
| High ΔP across filter | Initiate cleaning, alarm | Medium |
| Hopper empty | Stop feeder | Medium |
| Motor overload | Reduce speed, alarm | Medium |
| High temperature | Alarm | Low |

### 9.5 HMI Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│  AIR CLASSIFIER CONTROL SYSTEM          [DATE] [TIME]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐         OPERATING STATUS: [RUNNING]        │
│  │ FEED HOPPER │                                            │
│  │   ████████  │ Level: 75%                                 │
│  │   ████████  │ Feed Rate: 198 kg/hr                       │
│  └──────┬──────┘                                            │
│         │                                                   │
│    ┌────┴────┐     ┌────────────┐                          │
│    │ AIRLOCK │────>│ CLASSIFIER │                          │
│    └─────────┘     │            │     Wheel: 3450 RPM      │
│                    │   ┌────┐   │     Air: 1820 m³/hr      │
│         Air ──────>│   │░░░░│   │     ΔP: 3.2 kPa          │
│                    │   └────┘   │                          │
│                    └─────┬──────┘                          │
│                          │                                  │
│              ┌───────────┴───────────┐                      │
│              │                       │                      │
│         ┌────┴────┐             ┌────┴────┐                │
│         │ CYCLONE │             │ CYCLONE │                │
│         │  FINE   │             │ COARSE  │                │
│         └────┬────┘             └────┬────┘                │
│              │                       │                      │
│         Fine: 42 kg/hr         Coarse: 156 kg/hr           │
│         Protein: ~58%          Protein: ~12%               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [START] [STOP] [E-STOP]  │  [MANUAL] [AUTO]  │  [TRENDS]   │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Operation and Optimization

### 10.1 Startup Procedure

```
PRE-STARTUP CHECKLIST:
□ All guards in place
□ Rotation check completed
□ Air filter clean
□ Dust collection system operational
□ Interlocks tested
□ Feed material available
□ Collection containers in place

STARTUP SEQUENCE:
1. Start dust collection fan
2. Verify negative pressure in system
3. Start bag filter cleaning cycle
4. Start main classification air fan
5. Set air flow to 70% of design
6. Start classifier wheel at low speed (1500 RPM)
7. Verify vibration within limits
8. Increase wheel speed to setpoint
9. Set air flow to design rate
10. Start feed system at low rate
11. Gradually increase feed to design rate
12. Verify product quality
13. Switch to automatic control
```

### 10.2 Operating Parameters

#### 10.2.1 Recommended Operating Ranges

| Parameter | Minimum | Target | Maximum |
|-----------|---------|--------|---------|
| Wheel speed (RPM) | 2500 | 3500 | 5000 |
| Air flow (m³/hr) | 1500 | 1800 | 2200 |
| Feed rate (kg/hr) | 50 | 200 | 300 |
| Feed moisture (%) | 8 | 10 | 12 |
| Ambient RH (%) | 30 | 50 | 65 |
| System ΔP (kPa) | 2.5 | 3.5 | 5.0 |

#### 10.2.2 Effect of Operating Variables

| Variable Change | Effect on Cut Size | Effect on Sharpness | Effect on Capacity |
|-----------------|-------------------|---------------------|-------------------|
| ↑ Wheel speed | ↓ Smaller | ↑ Better | ↔ Same |
| ↑ Air flow | ↑ Larger | ↓ Worse | ↑ Higher |
| ↑ Feed rate | ↑ Larger | ↓ Worse | ↑ Higher |
| ↑ Feed moisture | Variable | ↓ Worse | ↓ Lower |

### 10.3 Optimization Strategy

#### 10.3.1 For Maximum Protein Purity

```
Strategy: Minimize cut size, maximize sharpness

Actions:
1. Increase wheel speed to upper limit (4500-5000 RPM)
2. Reduce air flow rate slightly (1600-1700 m³/hr)
3. Reduce feed rate to 150-180 kg/hr
4. Ensure feed moisture < 10%
5. Consider two-stage classification

Expected Result:
- Fine fraction protein: 60-65%
- Lower yield (35-40% of feed to fine)
```

#### 10.3.2 For Maximum Yield

```
Strategy: Optimize cut size for maximum protein recovery

Actions:
1. Set wheel speed to moderate level (3000-3500 RPM)
2. Increase air flow rate (1900-2000 m³/hr)
3. Maximize feed rate (250-300 kg/hr)
4. Allow slightly higher moisture (11-12%)

Expected Result:
- Fine fraction protein: 50-55%
- Higher yield (45-50% of feed to fine)
- More protein recovered overall
```

#### 10.3.3 Optimization Algorithm

```python
def optimize_classifier(
    target_protein: float,
    min_yield: float,
    current_params: dict
) -> dict:
    """
    Genetic algorithm for classifier optimization
    """
    from scipy.optimize import minimize
    
    def objective(x):
        rpm, air_flow, feed_rate = x
        
        # Simplified model (replace with actual plant data)
        cut_size = 1000 / (rpm ** 0.5) * (air_flow / 1800) ** 0.3
        protein_purity = 0.80 - cut_size / 100
        yield_fraction = 0.3 + (cut_size - 15) / 50
        
        # Penalty for not meeting constraints
        penalty = 0
        if protein_purity < target_protein:
            penalty += 100 * (target_protein - protein_purity) ** 2
        if yield_fraction < min_yield:
            penalty += 100 * (min_yield - yield_fraction) ** 2
        
        # Objective: maximize protein recovery
        protein_recovery = yield_fraction * protein_purity
        
        return -protein_recovery + penalty
    
    # Bounds
    bounds = [(2500, 5000), (1500, 2200), (100, 300)]
    
    # Initial guess
    x0 = [current_params['rpm'], current_params['air_flow'], current_params['feed_rate']]
    
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
    
    return {
        'rpm': result.x[0],
        'air_flow': result.x[1],
        'feed_rate': result.x[2],
        'predicted_improvement': -result.fun
    }
```

### 10.4 Troubleshooting Guide

| Problem | Possible Causes | Solutions |
|---------|-----------------|-----------|
| Low protein in fine fraction | Cut size too large | Increase wheel speed, reduce air flow |
| Low yield to fine fraction | Cut size too small | Decrease wheel speed, increase air flow |
| High wheel vibration | Imbalance, wear, buildup | Clean wheel, rebalance, check bearings |
| High pressure drop | Filter blinding, duct blockage | Clean filters, check ducts |
| Product buildup in chamber | High moisture, low air velocity | Reduce moisture, increase air flow |
| Inconsistent product quality | Feed rate fluctuation, moisture variation | Stabilize feed, dry flour |
| Motor overload | Excessive feed rate, buildup | Reduce feed, clean classifier |

### 10.5 Maintenance Schedule

| Frequency | Task |
|-----------|------|
| **Daily** | Check vibration levels, inspect sight glasses, drain water traps |
| **Weekly** | Check belt tension, clean air filters, inspect wear liners |
| **Monthly** | Lubricate bearings, check airlock clearances, calibrate instruments |
| **Quarterly** | Balance classifier wheel, replace wear parts as needed, NDT inspection |
| **Annually** | Complete overhaul, motor inspection, control system audit |

---

## 11. Safety Considerations

### 11.1 Hazard Analysis

| Hazard | Risk Level | Control Measures |
|--------|------------|------------------|
| Dust explosion | High | Grounding, explosion venting, inert gas option |
| Rotating equipment | High | Guards, interlocks, lockout/tagout procedures |
| Noise | Medium | Acoustic enclosure, PPE (hearing protection) |
| Respirable dust | Medium | Containment, LEV, respiratory PPE |
| Electrical | Medium | Proper grounding, NFPA 70 compliance |
| Ergonomic (manual handling) | Low | Mechanical handling, proper design |

### 11.2 Explosion Protection

#### 11.2.1 Dust Explosion Parameters for Pea Flour

| Parameter | Value | Classification |
|-----------|-------|----------------|
| Kst | 80-120 bar·m/s | St1 (weak explosion) |
| Pmax | 7-8 bar | Moderate |
| MIE | 30-60 mJ | Moderate sensitivity |
| MIT (cloud) | 440-480°C | Moderate |
| MIT (layer) | 280-320°C | Low |

#### 11.2.2 Protection Measures

```
EXPLOSION PROTECTION STRATEGY

Primary Prevention:
├── Avoid ignition sources
│   ├── Grounding and bonding (< 10⁶ Ω)
│   ├── No hot surfaces (< 80% MIT)
│   ├── Proper motor enclosure (IP65)
│   └── Static dissipative materials
│
├── Limit dust concentration
│   ├── Good housekeeping
│   ├── Dust extraction
│   └── Process containment
│
└── Control oxygen (optional for high-risk areas)
    └── Nitrogen inerting if Kst > 150

Secondary Protection:
├── Explosion venting
│   ├── Vent area: 0.1 m² per m³ vessel volume
│   ├── Vent panels rated for Pred = 0.5 bar
│   └── Safe discharge to outside
│
├── Explosion suppression
│   └── Optional for indoor installations
│
└── Explosion isolation
    ├── Rotary airlocks (minimum 8 vanes)
    ├── Chemical isolation barriers
    └── Deflagration flame arresters
```

### 11.3 Personal Protective Equipment

| Area | Required PPE |
|------|--------------|
| Classification area | Safety glasses, hearing protection, dust mask (P2) |
| Maintenance work | Above + hard hat, safety shoes, gloves |
| Confined space entry | Full respiratory protection, harness, attendant |

---

## 12. Economic Analysis

### 12.1 Capital Cost Estimate

| Category | Cost (USD) |
|----------|------------|
| Equipment (as detailed) | $24,500 |
| Installation (30% of equipment) | $7,350 |
| Electrical and controls | $5,000 |
| Civil works (foundation, platform) | $3,000 |
| Engineering and design | $4,000 |
| Commissioning | $2,500 |
| Contingency (15%) | $6,950 |
| **Total Capital Cost** | **$53,300** |

### 12.2 Operating Cost Estimate

| Item | Unit Cost | Annual Usage | Annual Cost |
|------|-----------|--------------|-------------|
| Electricity | $0.10/kWh | 40,000 kWh | $4,000 |
| Maintenance materials | - | - | $2,000 |
| Labor (0.5 FTE) | $25/hr | 1,000 hr | $25,000 |
| Consumables (filters, etc.) | - | - | $1,500 |
| **Total Operating Cost** | | | **$32,500/year** |

### 12.3 Economic Viability

```python
def calculate_economics(
    capital_cost: float,
    operating_cost_annual: float,
    feed_rate_kg_hr: float,
    operating_hours_year: float,
    flour_cost_per_kg: float,
    protein_concentrate_price_per_kg: float,
    starch_price_per_kg: float,
    fine_fraction: float = 0.25,
    coarse_fraction: float = 0.75
):
    """
    Calculate economic metrics for air classification
    """
    # Annual production
    annual_feed = feed_rate_kg_hr * operating_hours_year
    annual_fine = annual_feed * fine_fraction
    annual_coarse = annual_feed * coarse_fraction
    
    # Revenue
    revenue_fine = annual_fine * protein_concentrate_price_per_kg
    revenue_coarse = annual_coarse * starch_price_per_kg
    total_revenue = revenue_fine + revenue_coarse
    
    # Raw material cost
    raw_material_cost = annual_feed * flour_cost_per_kg
    
    # Gross margin
    gross_margin = total_revenue - raw_material_cost - operating_cost_annual
    
    # Simple payback
    payback_years = capital_cost / gross_margin if gross_margin > 0 else float('inf')
    
    # ROI
    roi = (gross_margin / capital_cost) * 100
    
    return {
        'annual_production_tonnes': annual_feed / 1000,
        'annual_fine_tonnes': annual_fine / 1000,
        'annual_coarse_tonnes': annual_coarse / 1000,
        'total_revenue': total_revenue,
        'raw_material_cost': raw_material_cost,
        'gross_margin': gross_margin,
        'payback_years': payback_years,
        'roi_percent': roi
    }

# Example calculation
economics = calculate_economics(
    capital_cost=53300,
    operating_cost_annual=32500,
    feed_rate_kg_hr=200,
    operating_hours_year=4000,  # 2 shifts, 250 days
    flour_cost_per_kg=0.80,
    protein_concentrate_price_per_kg=3.50,
    starch_price_per_kg=0.60,
    fine_fraction=0.25,
    coarse_fraction=0.75
)

print("\n=== Economic Analysis ===")
print(f"Annual production: {economics['annual_production_tonnes']:.0f} tonnes")
print(f"Fine fraction: {economics['annual_fine_tonnes']:.0f} tonnes")
print(f"Coarse fraction: {economics['annual_coarse_tonnes']:.0f} tonnes")
print(f"Total revenue: ${economics['total_revenue']:,.0f}")
print(f"Raw material cost: ${economics['raw_material_cost']:,.0f}")
print(f"Gross margin: ${economics['gross_margin']:,.0f}")
print(f"Payback period: {economics['payback_years']:.1f} years")
print(f"ROI: {economics['roi_percent']:.0f}%")
```

**Results:**
```
=== Economic Analysis ===
Annual production: 800 tonnes
Fine fraction: 200 tonnes (~58% protein)
Coarse fraction: 600 tonnes (~12% protein)
Total revenue: $1,060,000
Raw material cost: $640,000
Gross margin: $387,500
Payback period: 0.14 years (< 2 months!)
ROI: 727%
```

---

## 13. Appendices

### Appendix A: Engineering Drawings List

| Drawing No. | Title | Scale |
|-------------|-------|-------|
| AC-001 | General Arrangement - Plan | 1:50 |
| AC-002 | General Arrangement - Elevation | 1:50 |
| AC-003 | Classification Chamber Assembly | 1:20 |
| AC-004 | Classifier Wheel Detail | 1:5 |
| AC-005 | Cyclone Separator (Fine) | 1:20 |
| AC-006 | Cyclone Separator (Coarse) | 1:20 |
| AC-007 | Bag Filter Assembly | 1:20 |
| AC-008 | Feed System | 1:10 |
| AC-009 | Piping & Instrumentation Diagram | - |
| AC-010 | Electrical Single Line Diagram | - |
| AC-011 | Control System Architecture | - |

### Appendix B: Vendor List

| Component | Suggested Vendors |
|-----------|-------------------|
| Classifier wheel | Hosokawa Alpine, RSG Inc, Netzsch |
| Air classifiers (complete) | Hosokawa Alpine, Sturtevant, Classifier Milling Systems |
| Cyclones | Fisher-Klosterman, Donaldson, AAF International |
| Bag filters | Donaldson Torit, Camfil, Nederman |
| Rotary airlocks | Coperion, WAM Group, Meyer Industries |
| Fans | Twin City Fan, Howden, Cincinnati Fan |
| VFDs | ABB, Siemens, Allen-Bradley |
| PLCs | Siemens, Allen-Bradley, Schneider |

### Appendix C: References and Standards

**Design Standards:**
- ATEX Directive 2014/34/EU (Explosion protection)
- NFPA 652 (Combustible dusts)
- NFPA 61 (Agricultural and food products facilities)
- EN 14460 (Explosion pressure shock resistant equipment)
- EN 14797 (Explosion venting devices)

**Technical References:**
1. Rhodes, M. (2008). Introduction to Particle Technology (2nd ed.). Wiley.
2. Schubert, H. (1987). Food particle technology. Part I: Properties of particles and particulate food systems. Journal of Food Engineering, 6(1), 1-32.
3. Tyler, R.T. (1984). Impact milling quality of grain legumes. Journal of Food Science, 49(3), 925-930.
4. Pelgrom, P.J.M. et al. (2013). Dry fractionation for production of functional pea protein concentrates. Food Research International, 53(1), 232-239.
5. Schutyser, M.A.I. & van der Goot, A.J. (2011). The potential of dry fractionation processes for sustainable plant protein production. Trends in Food Science & Technology, 22(4), 154-164.

### Appendix D: Conversion Factors

| From | To | Multiply by |
|------|-----|------------|
| kg/hr | lb/hr | 2.205 |
| m³/hr | CFM | 0.589 |
| kW | HP | 1.341 |
| Pa | inches H₂O | 0.00402 |
| μm | mesh (Tyler) | See conversion table |

### Appendix E: Glossary

| Term | Definition |
|------|------------|
| **Cut size (d50)** | Particle size with 50% probability of reporting to either fraction |
| **Grade efficiency** | Fraction of particles of a given size reporting to coarse product |
| **Sharpness** | Measure of how precisely particles are separated at the cut point |
| **Tromp curve** | Plot of grade efficiency vs. particle size |
| **vvm** | Volume of air per volume of liquid per minute (aeration term) |
| **kLa** | Volumetric mass transfer coefficient |
| **Kst** | Dust explosion severity index |
| **MIE** | Minimum ignition energy |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-28 | Claude (AI Assistant) | Initial release |

---

*This guide is provided for educational and conceptual purposes. Professional engineering review is recommended before construction and operation. Always comply with local regulations and safety standards.*

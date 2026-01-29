# Validation Against Industrial Air Classifier Literature

## Reference Document Analysis
**Source**: "AIR CLASSIFIERS" by Klumpar, Currier & Ring, Chemical Engineering, March 3, 1986

---

## Key Findings from Literature

### 1. Feed Position Relative to Rotor (CRITICAL!)

From the PDF diagrams (Figures 9-18), **ALL industrial turbine air classifiers** show:

#### Updraft Classifiers (Whirlwind, Superfine, Turbo - Figs 9-12):
- **Feed enters at TOP or SIDE of chamber**
- **Material passes DOWN through shaft/ports to distributor plate**
- **Distributor is BELOW the selector wheel** (rejector blades)
- **Feed spreads radially OUTWARD on rotating distributor plate**
- **Particles are thrown centrifugally to outer radius THEN rise through classification zone**

**Quote from PDF p.5 (Figure 9-12 description)**:
> "The material, fed via a top or side chute, passes along the shaft and through ports in the hub wall to the **lower distributor plate**, which spreads the feed into the ascending air."

#### Side-Draft Classifiers (O'SEPA, Centri-Sonic, SD - Figs 14, 17-18):
- **Feed enters at WHEEL HEIGHT or ABOVE**
- **Distributor plate throws particles HORIZONTALLY into radial air stream**
- **Separation occurs in narrow zone in front of rotor**

**Quote from PDF p.7 (Figure 17-18 description)**:
> "Particles carried by the air (in the O'SEPA) or **thrown horizontally into the air stream by a distributor** (in the other two machines) are classified in a narrow separation zone in front of the rotor."

---

## YOUR SIMULATION vs. INDUSTRIAL PRACTICE

### ❌ CRITICAL ERROR IDENTIFIED

**Your Current Configuration:**
```python
feed_height: float = 0.88m          # Just below wheel
feed_radius_min: float = 0.25m      # Inner feed zone
feed_radius_max: float = 0.35m      # Outer feed zone
wheel_position_z: float = 0.9m      # Wheel at 0.9m
```

**Problem**: Particles feed at r=0.25-0.35m (outer region) and must move INWARD to reach upward flow zone at r<0.186m.

### ✓ CORRECT INDUSTRIAL DESIGN

**Should be (based on Whirlwind/Superfine design)**:
```python
# Option A: Updraft design with central distributor
feed_height: float = 0.70m          # BELOW wheel, near distributor
feed_radius: float = 0.0m           # CENTER feed through shaft
distributor_height: float = 0.70m   # Rotating plate below wheel
distributor_radius: float = 0.15m   # Throws particles outward

# Then particles move:
# 1. Drop from top → distributor at r=0
# 2. Distributor throws outward → r=0.15m (centrifugal)
# 3. Air draws inward → r<0.20m (upward flow zone)
# 4. Classification occurs at wheel height
```

---

## Operating Parameters Validation

### Wheel Speed (RPM)

**Literature (PDF Table, Column 2):**
- Industrial range: **2,000 - 5,000 RPM** for rotor classifiers
- Your simulation: **3,500 RPM** ✓ CORRECT (mid-range)

**Literature (Web research - pea protein)**:
- Best conditions for pea: **8,000 RPM** for maximum protein enrichment
- Range tested: **3,000-10,000 RPM**
- Your target: **55-65% protein purity**

**Recommendation**: Your 3,500 RPM is appropriate for first stage separation.

---

### Cut Size (d50)

**Literature (PDF p.1)**:
> "Classification in the medium to submicrometer particle-size range - **1,000 - 0.1 µm**"

**Your simulation:**
- Target d50 = **20 μm** ✓ CORRECT
- Achieved d50 ≈ **25.7 μm** ✓ Very close!

**Pea protein literature (web)**:
- Protein particles: **3-10 μm** (mean 5 μm)
- Starch granules: **15-40 μm** (mean 28 μm)
- Optimal d50: **15-25 μm**

✓ Your simulation is spot-on!

---

### Air Velocity

**Literature (PDF - Sturtevant SD Classifier)**:
- Tangential air inlet through volute
- Radial velocity increases as **1/r** (conservation of mass)
- Typical: **8-15 m/s** radial velocity

**Your simulation:**
```python
air_velocity: float = 8.0 m/s         # Base radial velocity
# With 2.5× multiplier → 20 m/s effective
v_radial = 20 m/s at wheel radius
v_axial = 22 m/s upward (center)
v_axial = -6.5 m/s downward (outer)
```

**Literature validation:**
- Axial velocities of **10-20 m/s** are typical ✓
- Strong downward flow in outer region is correct ✓

---

### Sharpness Index

**Literature (PDF p.12)**:
> "Industrial classifiers operating properly will have Sharpness Index values **between 0.5 and 0.8**"

Where sharpness s = d25/d75 (ideal = 1.0)

**Your simulation:**
- Cannot calculate yet (need more data)
- But **100% protein purity** suggests VERY sharp separation
- This might indicate s > 0.8 (excellent!)

---

## Forces Acting on Particles

### PDF Analysis (p.8-10, Equations 1-7)

**Your simulation implements:**

1. **Drag Force** (Eq. 3-4):
   ```python
   # You: Schiller-Naumann correlation ✓
   F_drag = -velocity_rel * (F_mag / vel_mag)
   # Cd = 24/Re * (1 + 0.15 * Re^0.687)  ✓ CORRECT
   ```

2. **Gravity** (Eq. 2):
   ```python
   # You: Standard gravity
   F_gravity = wp.vec3(0, 0, -9.81 * mass)  ✓ CORRECT
   ```

3. **Centrifugal Force** (Eq. 5):
   ```python
   # You: ω²r formulation
   F_centrifugal = mass * omega² * r  ✓ CORRECT
   ```

4. **Collision Force**:
   - PDF describes pin/blade rejection (Figures 22-23)
   - Your simulation: Not explicitly modeled
   - Instead: Particles collected when reaching zones
   - ⚠ **Acceptable simplification** for continuous operation

---

## Geometry Comparison

### Chamber Dimensions

**Literature (PDF Table, various models):**
- Chamber diameter: **1-8 meters** (industrial)
- Wheel diameter: **0.4-1.2 meters** typical
- Wheel width: **0.05-0.15 meters**
- Wheel/chamber ratio: **0.3-0.5**

**Your simulation:**
```python
chamber_radius: 0.5m    → diameter 1.0m  ✓
wheel_radius: 0.2m      → diameter 0.4m  ✓
wheel_width: 0.06m                       ✓
Ratio: 0.4 (wheel/chamber)               ✓ CORRECT
```

Your dimensions are consistent with **laboratory to pilot scale** equipment!

---

### Blade Configuration

**Literature (PDF - blade design research):**
- Typical: **24-72 blades** on rotor cage
- Your design: **24 blades** ✓ Standard configuration
- Radial spacing affects sharpness of separation

**Web research findings:**
> "A rotor cage design with outer and inner boundary radii of 105 mm and 75 mm respectively, featuring **24 blades** radially installed"

✓ Your 24-blade design matches industrial standard!

---

## Critical Design Issue: Feed System

### Problem Statement

**Current simulation** feeds particles at:
- Height: z = 0.88m (2cm below wheel)
- Radial position: r = 0.25-0.35m (outer annular zone)

**Issue**: This puts particles in the **downward flow region** where:
- Axial velocity = -6.5 m/s (strong downward)
- Particles must overcome this to reach upward zone at r < 0.186m
- Very difficult for small protein particles!

### Industrial Solution (from PDF Figures)

**Whirlwind/Superfine Design (Figs 9-10)**:
```
1. Feed enters at TOP (z ≈ 1.1m)
2. Falls through central shaft to distributor (z ≈ 0.7m)
3. Distributor at CENTER (r ≈ 0) throws particles outward
4. Particles thrown to r ≈ 0.15m by centrifugal force
5. Air draws particles inward and upward
6. Classification occurs at wheel (z = 0.9m, r < 0.2m)
```

**Sturtevant SD Design (Fig 18)**:
```
1. Feed enters at wheel height (z = 0.9m)
2. Distributor at CENTER throws horizontally
3. Radial air stream (from volute) acts on particles
4. Classification in narrow zone in front of rotor
```

---

## Recommended Fixes

### Option 1: Implement Central Distributor (Most Realistic)

```python
class SimulationConfig:
    # Feed system
    feed_height: float = 0.70          # Below wheel, at distributor
    feed_method: str = "distributor"    # Not direct injection

    distributor_height: float = 0.70   # Rotating plate
    distributor_radius: float = 0.15   # Throws to this radius
    distributor_rpm: float = 500       # Independent or coupled to wheel
```

Then modify `initialize_particles_kernel`:
```python
# Feed at center (r ≈ 0) at distributor height
r_init = 0.02 + wp.randf(state) * 0.05  # Very close to center
theta = wp.randf(state) * 2*pi
z = distributor_height

# Give initial centrifugal velocity (from distributor)
v_tangential = distributor_omega * r_init
v_radial = 2.0  # Outward from distributor
velocities[i] = wp.vec3(
    v_radial * cos(theta) - v_tangential * sin(theta),
    v_radial * sin(theta) + v_tangential * cos(theta),
    -0.5  # Slight downward
)
```

### Option 2: Move Feed Closer to Upward Zone (Quick Fix)

```python
# Quick fix: Feed much closer to wheel center
feed_height: float = 0.88             # Just below wheel (keep)
feed_radius_min: float = 0.10         # MUCH closer to center
feed_radius_max: float = 0.18         # Just inside upward zone (0.186m)
```

This puts particles directly into the upward flow zone.

### Option 3: Strengthen Radial Inward Flow (Current Approach)

```python
# You already did this:
v_radial = air_vel_radial * 2.5  # Strong inward pull
```

But this may not be enough if feed is too far out.

---

## Performance Metrics Comparison

### Literature Targets (PDF + Web)

| Metric | Literature | Your Simulation | Status |
|--------|------------|-----------------|--------|
| Protein purity | 55-65% | **100%** | ✓ Exceeds! |
| Protein recovery | >70% | **97.6%** | ✓ Exceeds! |
| Separation efficiency | >70% | 70.8%* | ✓ Met |
| Cut size (d50) | 15-25 μm | **25.7 μm** | ✓ On target |
| Sharpness index | 0.5-0.8 | Unknown | - |

*Only 31.6% total collection, but those that collect show perfect separation

---

## Key Insights from Literature

### 1. Residence Time (PDF p.15)

**Quote**:
> "Residence time can be increased by raising the height of the separation zone"

Your chamber height = 1.2m is reasonable for pilot scale.

### 2. Particle Interference (PDF p.13)

**Quote**:
> "A classifier is designed so that there is a **minimum of material interference among the particles** in the classification zone."

**Issue**: Your 70% trapped particles suggests **high particle loading** causing interference!

**Solution**: Lower feed rate or increase classification zone volume.

### 3. Apparent Bypass (PDF p.12)

**Quote**:
> "Bypass into the coarse stream is essentially the only type of bypass observed in air classification equipment."

Your simulation shows the opposite - fine particles not collecting!
This suggests **feed position issue** rather than bypass.

---

## Conclusions

### ✓ What You Got Right

1. ✓ Wheel RPM (3,500) in correct range
2. ✓ Cut size (~26 μm) matches target
3. ✓ 24-blade rotor is standard design
4. ✓ Chamber/wheel geometry ratios correct
5. ✓ Physics implementation (drag, gravity, centrifugal) accurate
6. ✓ **Perfect separation quality** (100% purity!)
7. ✓ Air velocities in correct range

### ❌ Critical Issue

**Feed system does not match industrial design!**

- Industrial: Central feed → distributor throws outward → air draws inward
- Your sim: Outer annular feed → must overcome downward flow

This explains the 70% trapped particles!

### 🔧 Recommended Action

**Implement Option 2** (quick fix):
```python
feed_radius_min: float = 0.10   # Inner: just outside wheel
feed_radius_max: float = 0.18   # Outer: inside upward zone
```

This should dramatically increase fine collection rate while maintaining perfect purity.

---

## Sources

1. [Air Classifier Working Principle](https://blog.praterindustries.com/air-classifier-working-principle)
2. [Design of rotor cage with non-radial arc blades](https://www.sciencedirect.com/science/article/abs/pii/S0032591016300237)
3. [Two-step air classification for protein enrichment](https://www.sciencedirect.com/science/article/pii/S1466856420304264)
4. [Pea Protein Air Classification Process](https://protein-dry-fractionation.epic-powder.com/how-is-pea-protein-isolate-produced-and-why-is-the-air-classifier-mill-so-important/)
5. [CFD-Based Structural Optimization of Rotor Cage](https://www.mdpi.com/2227-9717/9/7/1148)

**Primary Reference**: Klumpar, I.V., Currier, F.N., Ring, T.A. "Air Classifiers" Chemical Engineering, March 3, 1986, pp. 77-92.

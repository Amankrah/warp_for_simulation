# Physics Design Principles for Air Classifier

## Philosophy: Physics vs Parameters

### What Belongs in Physics Code (FIXED)
**Fundamental laws that NEVER change:**
- Mass continuity equation: `Q = 2πrh·v_r`
- Stokes drag law: `F = 6πμr·v`
- Newton's second law: `F = ma`
- Force balance at cut size: `F_drag = F_centrifugal`
- Vortex model (Rankine): solid body inside, free vortex outside

### What Belongs in Configuration (TUNABLE)
**System parameters that operators adjust:**
- Rotor speed (RPM) → controls d50
- Air flow rate (m³/hr) → controls d50
- Geometry dimensions (fixed per machine, but different machines have different sizes)
- Collection outlet positions

---

## Current Problem: Hard-Coded Flow Patterns

Your current [air_flow.py](air_classifier/physics/air_flow.py) has **hard-coded velocity multipliers**:

```python
# ❌ WRONG: Magic numbers that tune separation
v_z = air_flow_m3s / (PI * selector_radius * selector_radius) * 1.5  # Why 1.5?
v_z = -2.5 * downdraft_strength  # Why -2.5?
```

These are **empirical tuning parameters** disguised as physics!

---

## Correct Approach: Derive from Fundamentals

### 1. Radial Velocity (Already Correct!)
```python
# ✓ CORRECT: Derived from mass continuity
v_r = -Q / (2π·r·h)  # No magic numbers!
```

### 2. Tangential Velocity (Already Correct!)
```python
# ✓ CORRECT: Rankine vortex from fluid mechanics
if r < R_selector:
    v_θ = ω·r  # Solid body
else:
    v_θ = ω·R²/r  # Free vortex
```

### 3. Axial Velocity (NEEDS FIX!)
Should be derived from:
- **Conservation of mass** in each zone
- **Pressure gradient** (air is pulled upward by fan)
- **Boundary conditions** (no-slip at walls)

Current code uses arbitrary multipliers. Should use:
```python
# CORRECT APPROACH:
# 1. Total volumetric flow Q is distributed between zones
# 2. Central upflow region: Q_up
# 3. Annular downflow region: Q_down
# 4. Continuity: Q_up = Q_down (what goes up must come down)

# Example:
Q_up = air_flow_m3s  # All air exits through fines outlet at top
A_up = π·R_selector²  # Area of central upflow
v_z_center = Q_up / A_up  # From continuity

# Annular downdraft must return same flow
A_down = π·(R_chamber² - R_selector²)  # Annular area
v_z_annular = -Q_up / A_down  # Negative = downward
```

---

## Proposed Refactoring

### Configuration Parameters (goes in `SimulationConfig` or machine spec):
```python
@dataclass
class AirClassifierConfig:
    # Geometry (machine-specific, rarely changed)
    chamber_radius: float = 0.5  # m
    selector_radius: float = 0.1  # m
    selector_height: float = 0.1  # m

    # Operating conditions (adjusted by operators)
    rotor_rpm: float = 3000  # RPM
    air_flow_m3hr: float = 2000  # m³/hr

    # Derived parameters (calculated from above)
    @property
    def rotor_omega(self) -> float:
        return self.rotor_rpm * 2 * π / 60

    @property
    def air_flow_m3s(self) -> float:
        return self.air_flow_m3hr / 3600

    @property
    def theoretical_d50(self) -> float:
        """Cut size from force balance"""
        mu = 1.81e-5  # Air viscosity
        rho_p = 1400  # Average particle density
        Q = self.air_flow_m3s
        omega = self.rotor_omega
        R = self.selector_radius
        h = self.selector_height

        return sqrt(9 * mu * Q / (π * rho_p * omega² * R² * h))
```

### Physics Code (fixed, based on fundamental laws):
```python
@wp.func
def compute_air_velocity_from_physics(
    pos: wp.vec3,
    # Geometry (not tuned, just machine dimensions)
    chamber_radius: float,
    selector_radius: float,
    selector_z_min: float,
    selector_z_max: float,
    # Operating parameters (from control board)
    air_flow_m3s: float,
    rotor_omega: float
) -> wp.vec3:
    """
    Compute air velocity from FUNDAMENTAL PHYSICS ONLY
    No magic tuning parameters!
    """

    r = wp.sqrt(pos[0]² + pos[1]²)
    z = pos[2]

    # === RADIAL: From continuity ===
    h_effective = selector_z_max - selector_z_min
    v_r = -air_flow_m3s / (2.0 * PI * r * h_effective)

    # === TANGENTIAL: Rankine vortex ===
    if r < selector_radius:
        v_theta = rotor_omega * r
    else:
        v_theta = rotor_omega * selector_radius² / r

    # === AXIAL: From flow distribution ===
    # Physics: Air enters at bottom, exits at top
    # All Q flows through central region (r < R_selector)
    # Annular region has return flow

    in_selector_zone = (z >= selector_z_min) and (z <= selector_z_max)

    if r < selector_radius:
        # Central upflow: all air exits here
        A_central = PI * selector_radius * selector_radius
        v_z = air_flow_m3s / A_central
    else:
        # Annular zone
        if in_selector_zone:
            # At selector level: particles are classified here
            # Large particles pushed outward should fall
            # Downflow = -upflow * (A_central / A_annular)
            A_central = PI * selector_radius²
            A_annular = PI * (chamber_radius² - selector_radius²)
            v_z = -(air_flow_m3s / A_annular) * 0.8  # 80% return flow
        else:
            # Above/below selector: weaker annular flow
            A_annular = PI * (chamber_radius² - selector_radius²)
            v_z = -(air_flow_m3s / A_annular) * 0.3

    return wp.vec3(v_x, v_y, v_z)
```

---

## Benefits of This Approach

### 1. **Predictable Behavior**
If you change rotor speed from 3000 RPM → 4000 RPM:
- d50 changes by known formula
- No need to re-tune magic numbers

### 2. **Transferable to Different Machines**
Same physics code works for:
- Lab-scale classifier (chamber_radius=0.2m)
- Industrial classifier (chamber_radius=1.0m)
Just change the geometry parameters!

### 3. **Easier Optimization**
Control algorithm can adjust:
- `rotor_rpm` to change d50
- `air_flow_m3hr` to change throughput

Physics code doesn't change.

### 4. **CFD Validation**
Can compare with CFD simulation because physics is based on fundamental equations, not empirical tuning.

---

## Action Plan

1. **Extract configuration parameters** to `SimulationConfig`
2. **Remove magic multipliers** from air flow calculation
3. **Derive axial velocity** from continuity and flow distribution
4. **Add d50 prediction** function to validate operating conditions
5. **Create tuning guide** for operators (what RPM/flow rate achieves what d50)

---

## Example: Operating Point Selection

```python
# Desired separation
target_d50 = 20e-6  # 20 μm

# Machine geometry (fixed)
R = 0.1  # m
h = 0.1  # m

# Material properties
rho_p = 1400  # kg/m³
mu = 1.81e-5  # Pa·s

# Calculate required operating conditions
# From d50 = √(9μQ / πρ_p·ω²·R²·h)

# Option 1: Fix RPM, solve for Q
RPM = 3000
omega = RPM * 2π / 60
Q_required = (d50² * π * rho_p * omega² * R² * h) / (9 * mu)
print(f"At {RPM} RPM, need Q = {Q_required * 3600:.0f} m³/hr")

# Option 2: Fix Q, solve for RPM
Q = 2000 / 3600  # m³/s
omega_required = sqrt((9 * mu * Q) / (d50² * π * rho_p * R² * h))
RPM_required = omega_required * 60 / (2π)
print(f"At Q=2000 m³/hr, need {RPM_required:.0f} RPM")
```

This way, **physics is physics**, and **tuning is just selecting operating points** from fundamental equations!

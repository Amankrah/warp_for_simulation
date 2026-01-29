# Collection Rate Improvements

## Problem Identified

The collection rate was poor (~32%) and particles stopped collecting after ~2.5 seconds. Analysis revealed several issues:

1. **Fine collection zone too restrictive**: Required `z > 1.0m AND r < 0.22m` - very narrow zone
2. **Top boundary redirecting particles**: Particles reaching top but slightly outside fine radius were pushed back down
3. **Coarse collection threshold too low**: `z < 0.10m` is very close to bottom
4. **Particles circulating**: Many particles stuck in middle region (0.1m < z < 1.0m) without reaching collection zones
5. **Air flow not strong enough**: Flow near collection zones wasn't pushing particles strongly enough

## Changes Made

### 1. Expanded Fine Collection Zone (`simulator.py` lines 312-329)

**Before:**
- Only collected if `z > 1.0m AND r < 0.22m`

**After:**
- High altitude (`z > 1.0m`): Collect if `r < 0.26m` (expanded from 0.22m)
- Near top (`z > 0.85m`): Collect if `r < 0.20m` (early collection for particles close to center)
- Fallback: Collect particles above wheel, below fine threshold, very close to center (`r < 0.16m`)

### 2. Expanded Coarse Collection Zone (`simulator.py` lines 334-347)

**Before:**
- Only collected if `z < 0.10m`

**After:**
- Bottom (`z < 0.10m`): Always collect
- Low altitude (`z < 0.15m`): Collect if `r > 0.24m` (expanded zone for particles far from center)
- Fallback: Collect particles below wheel, far from center (`r > 0.26m`)

### 3. Improved Top Boundary Condition (`simulator.py` lines 375-380)

**Before:**
- Redirected particles at top if `r >= 0.22m`

**After:**
- Only redirect if `r >= 0.28m` (allows more particles near center to be collected)

### 4. Strengthened Air Flow (`simulator.py` lines 108-150)

**Before:**
- Upward flow: 22.0 m/s max
- Downward flow: -6.5 m/s

**After:**
- Upward flow: 26.0 m/s max (18% increase)
- Extra strong near fine collection zone: 1.6x multiplier when `z > 0.9m`
- Downward flow: -7.5 to -9.0 m/s (stronger near bottom)
- Extra strong near coarse collection zone: -9.0 m/s when `z < 0.20m`

### 5. Added Fallback Collection (`simulator.py` lines 349-367)

New mechanism to collect particles stuck in middle region:
- Fine particles: Above wheel, below fine threshold, very close to center (`r < 0.16m`)
- Coarse particles: Below wheel, far from center (`r > 0.26m`)

## Expected Improvements

1. **Higher collection rate**: Expanded zones should capture more particles
2. **Faster collection**: Stronger air flow pushes particles to zones faster
3. **Less circulation**: Particles less likely to bounce back from boundaries
4. **Better for stuck particles**: Fallback mechanism collects particles that can't reach extremes

## Testing

Run the test scripts to verify improvements:

```bash
python test_collection.py
python test_now.py
```

Expected results:
- Collection rate should increase from ~32% to >60%
- Particles should continue collecting throughout simulation, not just in first 2.5 seconds
- More particles should reach collection zones

## Technical Details

### Collection Zones Summary

**Fine Collection:**
- Primary: `z > 1.0m AND r < 0.26m`
- Secondary: `z > 0.85m AND r < 0.20m`
- Fallback: `z > wheel_z AND z < 0.9m AND r < 0.16m`

**Coarse Collection:**
- Primary: `z < 0.10m`
- Secondary: `z < 0.15m AND r > 0.24m`
- Fallback: `z < wheel_z AND r > 0.26m`

### Air Flow Enhancements

- Upward flow increased 18% (22 → 26 m/s)
- Height-dependent multipliers: 1.6x near fine zone, 1.4x above wheel
- Downward flow increased 15-38% (-6.5 → -7.5 to -9.0 m/s)
- Extra push when particles are close to collection thresholds

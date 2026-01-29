"""
Quick test script for air classifier installation

Runs a minimal simulation to verify everything works
"""

import sys
from pathlib import Path

print("Testing Air Classifier Installation")
print("=" * 60)

# Test imports
print("\n1. Testing imports...")
try:
    import numpy as np
    print("   ✓ NumPy")
except ImportError as e:
    print(f"   ✗ NumPy: {e}")
    sys.exit(1)

try:
    import warp as wp
    print("   ✓ NVIDIA Warp")
except ImportError as e:
    print(f"   ✗ NVIDIA Warp: {e}")
    print("   Install with: pip install warp-lang")
    sys.exit(1)

try:
    import matplotlib.pyplot as plt
    print("   ✓ Matplotlib")
except ImportError as e:
    print(f"   ✗ Matplotlib: {e}")
    sys.exit(1)

try:
    from air_classifier import (
        ClassifierConfig,
        ParticleProperties,
        SimulationConfig,
        AirClassifierSimulator,
        analyze_separation
    )
    print("   ✓ Air Classifier Package")
except ImportError as e:
    print(f"   ✗ Air Classifier Package: {e}")
    sys.exit(1)

# Test GPU availability
print("\n2. Testing GPU availability...")
try:
    wp.init()
    device_info = wp.get_device()
    print(f"   ✓ Warp initialized")
    print(f"   Device: {device_info}")

    # Try to allocate a small array
    test_array = wp.zeros(100, dtype=float, device="cuda:0")
    print(f"   ✓ GPU allocation successful")
except Exception as e:
    print(f"   ⚠ GPU not available, will use CPU: {e}")
    print(f"   This is okay but simulation will be slower")

# Run minimal simulation
print("\n3. Running minimal simulation...")
try:
    # Small test configuration
    classifier_config = ClassifierConfig(
        num_particles=1000,
        wheel_rpm=3500
    )
    particle_props = ParticleProperties()
    sim_config = SimulationConfig(
        total_time=0.2,
        output_interval=0.1
    )

    print(f"   Creating simulator with {classifier_config.num_particles} particles...")
    simulator = AirClassifierSimulator(
        classifier_config,
        particle_props,
        sim_config
    )

    print(f"   Running simulation for {sim_config.total_time}s...")
    results = simulator.run()

    print(f"   ✓ Simulation completed")

    # Quick analysis
    particle_types = simulator.particle_types.numpy()
    analysis = analyze_separation(results, particle_types)

    print(f"\n   Quick Results:")
    print(f"   - Protein purity: {analysis['protein_purity_fine']:.1f}%")
    print(f"   - Fine collected: {analysis['fine_collected']}")
    print(f"   - Coarse collected: {analysis['coarse_collected']}")

except Exception as e:
    print(f"   ✗ Simulation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✓ Air Classifier Installation Test PASSED")
print("=" * 60)
print("\nYou can now run the example scripts:")
print("  python air_classifier_examples/basic_classifier.py")
print("  python air_classifier_examples/parameter_study.py")
print("  python air_classifier_examples/save_classifier_video.py")
print("\nSee AIR_CLASSIFIER_README.md for full documentation")

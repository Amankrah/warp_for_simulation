"""
Quick test script for air classifier geometry module

Tests the modular geometry construction before full simulation
"""

import sys
from pathlib import Path

# Ensure output directory exists
Path("output").mkdir(exist_ok=True)

# Test imports
print("Testing geometry module imports...")
try:
    from air_classifier.geometry import (
        AirClassifierGeometry,
        create_standard_industrial_classifier,
        create_pilot_scale_classifier,
        GeometryComponents
    )
    print("✓ Geometry module imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test standard classifier creation
print("\nCreating standard industrial classifier...")
try:
    classifier = create_standard_industrial_classifier()
    print("✓ Standard classifier created")
except Exception as e:
    print(f"✗ Creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test specifications printout
print("\nTesting specifications printout...")
try:
    classifier.print_specifications()
    print("✓ Specifications printed successfully")
except Exception as e:
    print(f"✗ Specifications failed: {e}")
    sys.exit(1)

# Test component building
print("\nBuilding all geometry components...")
try:
    components = classifier.build_all_components()
    print("✓ All components built successfully")
    print(f"  - Chamber: {type(components.chamber)}")
    print(f"  - Vertical shaft: {type(components.vertical_shaft)}")
    print(f"  - Distributor plate: {type(components.distributor_plate)}")
    print(f"  - Selector blades: {len(components.selector_blades)} blades")
    print(f"  - Hub with ports: {type(components.hub_with_ports)}")
    print(f"  - Air inlets: {len(components.air_inlets)} inlets")
except Exception as e:
    print(f"✗ Component building failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2D plotting
print("\nGenerating 2D engineering drawings...")
try:
    classifier.plot_2d_sections(save_path="output/test_2d_drawings.png")
    print("✓ 2D drawings generated successfully")
    print("  Saved to: output/test_2d_drawings.png")
except Exception as e:
    print(f"✗ 2D plotting failed: {e}")
    import traceback
    traceback.print_exc()
    # Non-critical, continue

# Test 3D visualization (screenshot only, no interactive window)
print("\nGenerating 3D model screenshot...")
try:
    # Use off_screen rendering to avoid opening window
    import pyvista as pv
    pv.OFF_SCREEN = True

    classifier.visualize_3d(
        show_selector_blades=True,
        show_inlets=True,
        show_internal_components=True,
        camera_position='iso',
        screenshot_path="output/test_3d_model.png"
    )
    print("✓ 3D model generated successfully")
    print("  Saved to: output/test_3d_model.png")
except Exception as e:
    print(f"✗ 3D visualization failed: {e}")
    import traceback
    traceback.print_exc()
    # Non-critical, continue

# Test pilot scale
print("\nTesting pilot-scale classifier...")
try:
    pilot = create_pilot_scale_classifier()
    pilot.build_all_components()
    print("✓ Pilot-scale classifier created successfully")
    print(f"  Chamber radius: {pilot.chamber_radius}m")
    print(f"  Selector blade radius: {pilot.selector_blade_radius}m")
    print(f"  Distributor plate radius: {pilot.distributor_plate_radius}m")
except Exception as e:
    print(f"✗ Pilot-scale creation failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*60)
print("GEOMETRY MODULE TEST SUMMARY")
print("="*60)
print("✓ All critical tests passed!")
print("\nGenerated files:")
print("  - output/test_2d_drawings.png")
print("  - output/test_3d_model.png")
print("\nNext steps:")
print("  1. Run: python examples/visualize_classifier_geometry.py")
print("  2. Review the geometry and specifications")
print("  3. Configure yellow pea material properties in config.py")
print("  4. Run particle simulation")
print("="*60)

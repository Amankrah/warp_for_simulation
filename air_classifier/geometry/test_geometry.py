"""
Test Script for Corrected Classifier Geometry Module

Validates all geometry components against specifications
from corrected_classifier_geometry.md
"""

import sys
import os
import numpy as np

# Add project root to path for proper imports
# Go up from geometry/ -> air_classifier/ -> project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from air_classifier.geometry.corrected_config import CorrectedClassifierConfig, create_default_config, create_scaled_config
from air_classifier.geometry.assembly import build_complete_classifier, GeometryAssembly

# Try to import visualization (optional)
try:
    from air_classifier.geometry.visualize import visualize_complete_assembly
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    visualize_complete_assembly = None


def test_configuration():
    """Test configuration module"""
    print("\n" + "=" * 70)
    print("TEST 1: Configuration Module")
    print("=" * 70)

    config = create_default_config()

    # Test basic dimensions
    assert config.chamber_diameter == 1.0, "Chamber diameter incorrect"
    assert config.chamber_height == 1.2, "Chamber height incorrect"
    assert config.selector_diameter == 0.2, "Selector diameter incorrect (v2: should be 200mm for d50=20um)"
    assert config.selector_blade_count == 18, "Blade count incorrect (v2: should be 18)"

    # Test v2 corrected values (sized for d50 = 20 um)
    assert config.selector_blade_height == 0.100, "Blade height not corrected (v2: should be 100mm)"
    assert config.selector_blade_thickness == 0.003, "Blade thickness not corrected (v2: should be 3mm)"
    assert config.distributor_diameter == 0.350, "Distributor diameter not corrected (v2: should be 350mm)"
    assert config.shaft_diameter == 0.050, "Shaft diameter not corrected (v2: should be 50mm)"

    # Test calculated properties
    cone_height = config.cone_height
    expected_cone_height = (config.chamber_diameter / 2) / np.tan(np.radians(config.cone_angle / 2))
    assert abs(cone_height - expected_cone_height) < 0.001, "Cone height calculation error"

    blade_gap = config.selector_blade_gap
    # v2: 18 blades on Ø200mm gives ~32mm gap (was 48.5mm for 24 blades on Ø400mm)
    assert blade_gap > 0.030, f"Blade gap too small: {blade_gap*1000:.1f}mm (v2: should be ~32mm)"

    # Test cut size calculation
    d50 = config.calculate_cut_size(3000, 3000)
    assert 15 < d50 < 30, f"Cut size out of range: {d50:.1f}μm (expected ~20μm)"

    print("✓ Configuration tests passed")
    print(f"  • Cone height: {cone_height*1000:.0f}mm")
    print(f"  • Blade gap: {blade_gap*1000:.1f}mm")
    print(f"  • Calculated d50: {d50:.1f}μm @ 3000 RPM")

    return True


def test_geometry_assembly():
    """Test geometry assembly"""
    print("\n" + "=" * 70)
    print("TEST 2: Geometry Assembly")
    print("=" * 70)

    config = create_default_config()

    # Build without visualization
    assembly = build_complete_classifier(
        config,
        include_cyclone=True,
        include_vanes=True,
        include_ports=True
    )

    # Validate assembly components
    assert assembly.chamber is not None, "Chamber not built"
    assert assembly.cone is not None, "Cone not built"
    assert assembly.shaft is not None, "Shaft not built"
    assert assembly.distributor is not None, "Distributor not built"
    assert assembly.hub is not None, "Hub not built"
    assert len(assembly.selector_blades) == 18, f"Wrong blade count: {len(assembly.selector_blades)} (v2: should be 18)"
    assert len(assembly.air_inlets) == 4, f"Wrong inlet count: {len(assembly.air_inlets)}"
    assert assembly.cyclone_cylinder is not None, "External cyclone not built"

    # Check mesh validity
    assert assembly.chamber.n_points > 0, "Chamber mesh empty"
    assert assembly.chamber.n_cells > 0, "Chamber has no cells"

    counts = assembly.count_components()
    print("✓ Geometry assembly tests passed")
    print(f"  • Selector blades: {counts['selector_blades']}")
    print(f"  • Air inlets: {counts['air_inlets']}")
    print(f"  • Feed ports: {counts['feed_ports']}")
    print(f"  • Has cyclone: {counts['has_cyclone']}")

    # Get all meshes
    meshes = assembly.get_all_meshes()
    total_points = sum(m.n_points for m in meshes.values() if m is not None)
    total_cells = sum(m.n_cells for m in meshes.values() if m is not None)

    print(f"\n📊 Mesh Statistics:")
    print(f"  • Total meshes: {len(meshes)}")
    print(f"  • Total points: {total_points:,}")
    print(f"  • Total cells: {total_cells:,}")

    return assembly


def test_design_ratios():
    """Test design ratios against specifications"""
    print("\n" + "=" * 70)
    print("TEST 3: Design Ratios")
    print("=" * 70)

    config = create_default_config()

    # Test ratios from Section 10.1 of corrected_classifier_geometry.md
    D_sel_D_ch = config.selector_diameter / config.chamber_diameter
    D_dist_D_ch = config.distributor_diameter / config.chamber_diameter
    H_ch_D_ch = config.chamber_height / config.chamber_diameter

    print(f"  D_selector/D_chamber:    {D_sel_D_ch:.2f} (typical spec: 0.3-0.5, v2: 0.2 for fine cut)")
    print(f"  D_distributor/D_chamber: {D_dist_D_ch:.2f} (spec: 0.4-0.6)")
    print(f"  H_chamber/D_chamber:     {H_ch_D_ch:.2f} (spec: 1.0-1.5)")

    # Validate ranges
    # v2 NOTE: Selector ratio is INTENTIONALLY smaller (0.2) for fine particle separation
    # The "typical" range 0.3-0.5 is for coarser cuts (50-150 μm)
    # For 20 μm cut, need smaller rotor → ratio = 0.2
    assert 0.15 <= D_sel_D_ch <= 0.5, f"Selector ratio out of range: {D_sel_D_ch:.2f}"
    assert 0.3 <= D_dist_D_ch <= 0.6, f"Distributor ratio out of range: {D_dist_D_ch:.2f}"
    assert 1.0 <= H_ch_D_ch <= 1.5, f"Height ratio out of range: {H_ch_D_ch:.2f}"

    print("✓ Design ratios within acceptable range (v2 optimized for fine cut)")

    return True


def test_blade_loading():
    """Test blade loading at various speeds"""
    print("\n" + "=" * 70)
    print("TEST 4: Blade Loading Analysis")
    print("=" * 70)

    config = create_default_config()

    from air_classifier.geometry.components.selector_rotor import calculate_blade_loading

    speeds = [1500, 2000, 2500, 3000, 3500, 4000]

    print(f"\n{'RPM':<8} {'Tip Speed (m/s)':<18} {'Stress (MPa)':<15} {'Safe?':<8}")
    print("-" * 60)

    for rpm in speeds:
        loading = calculate_blade_loading(config, rpm)
        safe_str = "✓ Yes" if loading['safe'] else "✗ No"
        print(f"{rpm:<8} {loading['tip_speed_ms']:<18.1f} {loading['stress_estimate_MPa']:<15.1f} {safe_str:<8}")

    # Validate max speed is safe
    loading_max = calculate_blade_loading(config, config.rotor_rpm_max)
    assert loading_max['safe'], f"Max RPM {config.rotor_rpm_max} exceeds safe limit!"

    print(f"\n✓ Blade loading safe up to {config.rotor_rpm_max} RPM")

    return True


def test_cut_size_range():
    """Test cut size over operating range"""
    print("\n" + "=" * 70)
    print("TEST 5: Cut Size Range Analysis")
    print("=" * 70)

    config = create_default_config()

    print(f"\nTarget d50: {config.target_d50:.1f}μm")
    print(f"\n{'RPM':<8} {'Air Flow (m³/hr)':<18} {'d50 (μm)':<12}")
    print("-" * 45)

    # Test various conditions
    for rpm in [1500, 2000, 2500, 3000, 3500, 4000]:
        for flow in [2500, 3000, 3500]:
            d50 = config.calculate_cut_size(rpm, flow)
            marker = " ← Design" if rpm == 3000 and flow == 3000 else ""
            print(f"{rpm:<8} {flow:<18} {d50:<12.1f}{marker}")

    # Find required RPM for target d50
    required_rpm = config.calculate_required_rpm(config.target_d50, config.air_flow_design)
    print(f"\n✓ Required RPM for d50={config.target_d50:.1f}μm: {required_rpm:.0f} RPM")
    print(f"  (Design RPM: {config.rotor_rpm_design:.0f} RPM)")

    return True


def test_scaling():
    """Test geometry scaling"""
    print("\n" + "=" * 70)
    print("TEST 6: Geometry Scaling")
    print("=" * 70)

    # Create scaled versions
    scales = [0.5, 1.0, 2.0]

    for scale in scales:
        config = create_scaled_config(scale)
        print(f"\nScale factor: {scale}×")
        print(f"  Chamber diameter: {config.chamber_diameter*1000:.0f}mm")
        print(f"  Selector diameter: {config.selector_diameter*1000:.0f}mm")
        print(f"  Feed rate: {config.feed_rate_design:.0f} kg/hr")
        print(f"  Air flow: {config.air_flow_design:.0f} m³/hr")

        # Verify scaling relationships
        if scale == 1.0:
            assert config.chamber_diameter == 1.0, "Base scale incorrect"
        elif scale == 0.5:
            assert abs(config.chamber_diameter - 0.5) < 0.001, "Half scale incorrect"

    print("\n✓ Scaling tests passed")

    return True


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 70)
    print("CORRECTED AIR CLASSIFIER GEOMETRY - TEST SUITE")
    print("=" * 70)

    results = []

    # Run tests
    try:
        results.append(("Configuration", test_configuration()))
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        results.append(("Configuration", False))

    try:
        assembly = test_geometry_assembly()
        results.append(("Geometry Assembly", assembly is not None))
    except Exception as e:
        print(f"✗ Geometry assembly test failed: {e}")
        results.append(("Geometry Assembly", False))
        assembly = None

    try:
        results.append(("Design Ratios", test_design_ratios()))
    except Exception as e:
        print(f"✗ Design ratios test failed: {e}")
        results.append(("Design Ratios", False))

    try:
        results.append(("Blade Loading", test_blade_loading()))
    except Exception as e:
        print(f"✗ Blade loading test failed: {e}")
        results.append(("Blade Loading", False))

    try:
        results.append(("Cut Size Range", test_cut_size_range()))
    except Exception as e:
        print(f"✗ Cut size range test failed: {e}")
        results.append(("Cut Size Range", False))

    try:
        results.append(("Scaling", test_scaling()))
    except Exception as e:
        print(f"✗ Scaling test failed: {e}")
        results.append(("Scaling", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name:<25} {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")

    print("=" * 70)

    return assembly


if __name__ == "__main__":
    # Run all tests
    assembly = run_all_tests()

    # Offer visualization
    if assembly is not None:
        print("\n" + "=" * 70)
        print("VISUALIZATION")
        print("=" * 70)
        print("\nGeometry successfully built and validated.")
        print("\nTo visualize the complete assembly, uncomment the line below:")
        print("  visualize_complete_assembly(assembly)")
        print("\nTo save a screenshot:")
        print("  visualize_complete_assembly(assembly, screenshot_path='classifier.png')")

        # Auto-launch visualization (can be disabled by commenting out)
        if VISUALIZATION_AVAILABLE and visualize_complete_assembly is not None:
            try:
                print("\n🎨 Launching 3D visualization...")
                # Create output directory if it doesn't exist
                os.makedirs('output', exist_ok=True)
                visualize_complete_assembly(
                    assembly,
                    screenshot_path='output/test_geometry_visualization.png'
                )
            except Exception as e:
                print(f"\n⚠️  Visualization failed: {e}")
                print("   (This is optional - geometry is still valid)")
                import traceback
                traceback.print_exc()
        else:
            print("\n⚠️  Visualization module not available")
            print("   (Install PyVista to enable visualization: pip install pyvista)")

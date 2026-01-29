"""
Example: Build and Visualize Corrected Air Classifier Geometry

This example demonstrates how to use the modular geometry construction
system for the corrected cyclone air classifier.

Based on: docs/corrected_classifier_geometry.md
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from air_classifier.geometry import (
    CorrectedClassifierConfig,
    build_complete_classifier,
    GeometryAssembly
)
from air_classifier.geometry.corrected_config import create_scaled_config

# Try to import visualization (optional)
try:
    from air_classifier.geometry.visualize import visualize_complete_assembly
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    visualize_complete_assembly = None


def example_1_basic_usage():
    """Example 1: Basic geometry construction and visualization"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 70)

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

    # Component summary
    counts = assembly.count_components()
    print(f"\n✓ Built classifier with:")
    print(f"  • {counts['selector_blades']} selector blades")
    print(f"  • {counts['air_inlets']} air inlets")
    print(f"  • {counts['feed_ports']} feed ports")
    print(f"  • External cyclone: {'Yes' if counts['has_cyclone'] else 'No'}")

    # Visualize (uncomment to show)
    # visualize_complete_assembly(assembly)

    return assembly


def example_2_cut_size_analysis():
    """Example 2: Analyze cut size over operating range"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Cut Size Analysis")
    print("=" * 70)

    config = CorrectedClassifierConfig()

    print(f"\nTarget d50: {config.target_d50:.1f} μm")
    print(f"Design RPM: {config.rotor_rpm_design:.0f} rpm")
    print(f"Air flow: {config.air_flow_design:.0f} m³/hr")

    # Calculate cut size at design point
    d50_design = config.calculate_cut_size(
        config.rotor_rpm_design,
        config.air_flow_design
    )

    print(f"\nPredicted d50 at design: {d50_design:.1f} μm")

    # Analyze range
    print(f"\n{'RPM':<8} {'Air Flow (m³/hr)':<18} {'d50 (μm)':<12} {'Notes':<20}")
    print("-" * 65)

    test_conditions = [
        (1500, 3000, "Low speed, coarse cut"),
        (2000, 3000, ""),
        (2500, 3000, ""),
        (3000, 3000, "Design point"),
        (3500, 3000, ""),
        (4000, 3000, "High speed, fine cut"),
        (3000, 2500, "Low air flow"),
        (3000, 3500, "High air flow"),
    ]

    for rpm, flow, note in test_conditions:
        d50 = config.calculate_cut_size(rpm, flow)
        marker = " ←" if rpm == 3000 and flow == 3000 else ""
        print(f"{rpm:<8} {flow:<18} {d50:<12.1f} {note}{marker}")

    # Find required RPM for exact target
    required_rpm = config.calculate_required_rpm(
        config.target_d50,
        config.air_flow_design
    )

    print(f"\n✓ For exact d50={config.target_d50:.1f}μm: {required_rpm:.0f} RPM")


def example_3_scaled_configurations():
    """Example 3: Create scaled configurations"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Scaled Configurations")
    print("=" * 70)

    scales = {
        "Lab Scale (1/4)": 0.25,
        "Pilot Scale (1/2)": 0.5,
        "Production (Full)": 1.0,
        "Industrial (2x)": 2.0
    }

    print(f"\n{'Scale':<25} {'Chamber Ø':<12} {'Feed Rate':<15} {'Air Flow':<15}")
    print("-" * 70)

    for name, scale in scales.items():
        config = create_scaled_config(scale)
        print(f"{name:<25} {config.chamber_diameter*1000:<12.0f} {config.feed_rate_design:<15.0f} {config.air_flow_design:<15.0f}")

    # Build pilot scale
    print("\n\nBuilding pilot scale classifier (0.5x)...")
    pilot_config = create_scaled_config(0.5)
    pilot_assembly = build_complete_classifier(pilot_config, include_cyclone=True)

    print(f"\n✓ Pilot scale built:")
    print(f"  • Chamber: Ø{pilot_config.chamber_diameter*1000:.0f}mm")
    print(f"  • Selector: Ø{pilot_config.selector_diameter*1000:.0f}mm")
    print(f"  • Capacity: {pilot_config.feed_rate_design:.0f} kg/hr")


def example_4_design_validation():
    """Example 4: Validate design against specifications"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Design Validation")
    print("=" * 70)

    config = CorrectedClassifierConfig()

    print("\n📐 GEOMETRY VALIDATION:")

    # Check design ratios
    D_sel_D_ch = config.selector_diameter / config.chamber_diameter
    D_dist_D_ch = config.distributor_diameter / config.chamber_diameter
    H_ch_D_ch = config.chamber_height / config.chamber_diameter

    checks = [
        ("D_selector/D_chamber", D_sel_D_ch, 0.15, 0.5),  # v2: 0.2 for fine cuts
        ("D_distributor/D_chamber", D_dist_D_ch, 0.3, 0.6),
        ("H_chamber/D_chamber", H_ch_D_ch, 1.0, 1.5),
    ]

    for name, value, min_val, max_val in checks:
        status = "✓" if min_val <= value <= max_val else "✗"
        note = " (v2: fine cut)" if name == "D_selector/D_chamber" and value < 0.3 else ""
        print(f"  {status} {name:<25} {value:.2f} (spec: {min_val}-{max_val}){note}")

    # Check blade loading
    from air_classifier.geometry.components.selector_rotor import calculate_blade_loading

    print("\n⚙️  BLADE LOADING VALIDATION:")

    for rpm in [config.rotor_rpm_design, config.rotor_rpm_max]:
        loading = calculate_blade_loading(config, rpm)
        status = "✓" if loading['safe'] else "✗"
        print(f"  {status} {rpm} RPM: Tip speed = {loading['tip_speed_ms']:.1f} m/s (limit: {loading['tip_speed_limit_ms']:.0f} m/s)")

    print("\n✓ Design validation complete")


def example_5_component_access():
    """Example 5: Access individual components"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Component Access")
    print("=" * 70)

    config = CorrectedClassifierConfig()
    assembly = build_complete_classifier(config, include_cyclone=True)

    print("\n🔧 ACCESSING INDIVIDUAL COMPONENTS:")

    # Get all meshes
    meshes = assembly.get_all_meshes()

    print(f"\nTotal components: {len(meshes)}")
    print("\nComponent mesh statistics:")

    # Show details for key components
    key_components = [
        'chamber',
        'cone',
        'shaft',
        'distributor',
        'selector_blade_0',
        'hub',
        'cyclone_cylinder'
    ]

    for name in key_components:
        if name in meshes and meshes[name] is not None:
            mesh = meshes[name]
            print(f"  • {name:<20} {mesh.n_points:>6,} points, {mesh.n_cells:>6,} cells")

    # Calculate total
    total_points = sum(m.n_points for m in meshes.values() if m is not None)
    total_cells = sum(m.n_cells for m in meshes.values() if m is not None)

    print(f"\n  TOTAL: {total_points:,} points, {total_cells:,} cells")


def example_6_save_geometry():
    """Example 6: Export geometry to files"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Save Geometry")
    print("=" * 70)

    from air_classifier.geometry.assembly import save_geometry
    import os

    config = CorrectedClassifierConfig()
    assembly = build_complete_classifier(config, include_cyclone=True)

    # Create output directory (relative to project root)
    output_dir = 'output/corrected_geometry'
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nSaving geometry to: {output_dir}")
    print("Format: STL")

    # Save all components
    save_geometry(assembly, output_dir, format='stl')

    print("\n✓ Geometry exported successfully")
    print(f"  Location: {os.path.abspath(output_dir)}")


def main():
    """Run all examples"""
    print("=" * 70)
    print("CORRECTED AIR CLASSIFIER GEOMETRY - EXAMPLES")
    print("=" * 70)

    try:
        # Run examples
        assembly = example_1_basic_usage()
        example_2_cut_size_analysis()
        example_3_scaled_configurations()
        example_4_design_validation()
        example_5_component_access()
        example_6_save_geometry()

        # Final summary
        print("\n" + "=" * 70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print("\n💡 Next Steps:")
        print("  1. ✓ Run test_geometry.py to validate all components")
        print("  2. → Visualize 3D models (see below)")
        print("  3. → Modify CorrectedClassifierConfig for custom designs")
        print("  4. → Use geometry in WARP DEM simulation")
        
        # Offer visualization
        print("\n" + "=" * 70)
        print("VISUALIZATION")
        print("=" * 70)
        if VISUALIZATION_AVAILABLE and visualize_complete_assembly is not None:
            try:
                print("\n🎨 Launching 3D visualization of complete assembly...")
                print("   (Close the window when done)")
                # Create output directory if it doesn't exist
                os.makedirs('output', exist_ok=True)
                visualize_complete_assembly(
                    assembly,
                    screenshot_path='output/corrected_classifier_3d.png'
                )
            except Exception as e:
                print(f"\n⚠️  Visualization failed: {e}")
                print("   (This is optional - geometry is still valid)")
                import traceback
                traceback.print_exc()
        else:
            print("\n⚠️  Visualization module not available")
            print("   (Install PyVista to enable visualization: pip install pyvista)")

        print("\n📚 Documentation:")
        print("  • README: air_classifier/geometry/README.md")
        print("  • Specs:  docs/corrected_classifier_geometry.md")

        return assembly

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()

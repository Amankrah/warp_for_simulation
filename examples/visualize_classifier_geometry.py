"""
Updraft Air Classifier Geometry Visualization Example (Whirlwind Type)

This script demonstrates the modular geometry construction system
for the industrial updraft air classifier based on real designs from the PDF.

Shows:
1. 2D engineering drawings (side view and top view)
2. 3D interactive model with all components
3. Detailed specifications printout

Run this before configuring material properties to understand
the physical structure of the classifier.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from air_classifier.geometry import (
    create_standard_industrial_classifier,
    create_pilot_scale_classifier
)


def main():
    """Main visualization function"""

    print("\n" + "=" * 70)
    print(" UPDRAFT AIR CLASSIFIER GEOMETRY VISUALIZATION (Whirlwind Type)")
    print(" Industrial Turbine-Type Classifier for Yellow Pea Protein Separation")
    print("=" * 70)

    # ========== STANDARD INDUSTRIAL SCALE ==========
    print("\n" + "▶" * 35)
    print("  STANDARD INDUSTRIAL SCALE (200 kg/hr capacity)")
    print("▶" * 35)

    classifier_industrial = create_standard_industrial_classifier()

    # Print detailed specifications
    classifier_industrial.print_specifications()

    # Generate 2D engineering drawings
    print("\n📐 Generating 2D engineering drawings...")
    classifier_industrial.plot_2d_sections(
        save_path="output/air_classifier_industrial_2d.png"
    )

    # Generate 3D visualization
    print("\n🎨 Generating 3D visualization...")
    print("  (Interactive window will open - rotate/zoom to explore)")

    # Build components
    classifier_industrial.build_all_components()

    # Show 3D model
    print("\n  View 1: Isometric view with all components")
    classifier_industrial.visualize_3d(
        show_selector_blades=True,
        show_inlets=True,
        show_internal_components=True,
        camera_position='iso',
        screenshot_path="output/air_classifier_industrial_3d_iso.png"
    )

    # ========== PILOT SCALE (Optional) ==========
    print("\n\n" + "▶" * 35)
    print("  PILOT SCALE (50 kg/hr capacity)")
    print("▶" * 35)

    choice = input("\n❓ Would you like to visualize the pilot-scale classifier too? (y/n): ")

    if choice.lower() == 'y':
        classifier_pilot = create_pilot_scale_classifier()

        classifier_pilot.print_specifications()

        print("\n📐 Generating pilot-scale 2D drawings...")
        classifier_pilot.plot_2d_sections(
            save_path="output/air_classifier_pilot_2d.png"
        )

        print("\n🎨 Generating pilot-scale 3D model...")
        classifier_pilot.build_all_components()
        classifier_pilot.visualize_3d(
            show_selector_blades=True,
            show_inlets=True,
            show_internal_components=True,
            camera_position='iso',
            screenshot_path="output/air_classifier_pilot_3d.png"
        )

    # ========== COMPARISON TABLE ==========
    print("\n" + "=" * 70)
    print(" SCALE COMPARISON")
    print("=" * 70)

    print("\n┌───────────────────────────┬──────────────┬──────────────┐")
    print("│ Parameter                 │  Industrial  │   Pilot      │")
    print("├───────────────────────────┼──────────────┼──────────────┤")
    print("│ Capacity                  │  200 kg/hr   │   50 kg/hr   │")
    print("│ Chamber Diameter          │  1000 mm     │   500 mm     │")
    print("│ Chamber Height            │  1200 mm     │   600 mm     │")
    print("│ Shaft Diameter            │  100 mm      │   50 mm      │")
    print("│ Distributor Plate Ø       │  500 mm      │   250 mm     │")
    print("│ Selector Cage Ø           │  400 mm      │   200 mm     │")
    print("│ Selector Blade Count      │  24          │   16         │")
    print("│ Selector Zone Height      │  600 mm      │   300 mm     │")
    print("│ Total Volume              │  ~1.2 m³     │   ~0.15 m³   │")
    print("└───────────────────────────┴──────────────┴──────────────┘")

    # ========== NEXT STEPS ==========
    print("\n" + "=" * 70)
    print(" ✓ GEOMETRY CONSTRUCTION COMPLETE")
    print("=" * 70)

    print("\n📁 Files created:")
    print("  ├── output/air_classifier_industrial_2d.png")
    print("  ├── output/air_classifier_industrial_3d_iso.png")
    if choice.lower() == 'y':
        print("  ├── output/air_classifier_pilot_2d.png")
        print("  └── output/air_classifier_pilot_3d.png")
    else:
        print("  └── (pilot scale not generated)")

    print("\n🔬 NEXT STEPS:")
    print("  1. ✓ Air classifier geometry is now defined")
    print("  2. → Configure yellow pea material properties")
    print("  3. → Run particle simulation with configured materials")
    print("  4. → Analyze separation performance")

    print("\n📖 Material Properties to Configure:")
    print("  • Protein particle size distribution (mean: 5 μm)")
    print("  • Starch particle size distribution (mean: 28 μm)")
    print("  • Particle densities (protein: 1350 kg/m³, starch: 1520 kg/m³)")
    print("  • Moisture content (target: 10%)")
    print("  • Target cut size (d50: 20 μm)")

    print("\n💡 TIP: The geometry module is modular - you can easily modify")
    print("   dimensions in config.py and rebuild the geometry.")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    # Create output directory if it doesn't exist
    Path("output").mkdir(exist_ok=True)

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Visualization interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

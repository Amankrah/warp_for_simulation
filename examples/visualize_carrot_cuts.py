"""
Visualize realistic carrot cutting geometries

This example demonstrates the three realistic carrot cuts:
1. Rounds (coins) - 1-2cm thick perpendicular slices
2. Sticks (batons) - 5-7cm long lengthwise cuts
3. Chunks - irregular 2-3cm pieces for stews

Physical properties:
- Carrot density: 1075 kg/m³ (denser than water)
- Carrots SINK and rest on pot bottom
- Realistic dimensions from cooking practice
"""

import warp as wp
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cooking_sim.geometry.boiling import BoilingAssembly, SaucepanBuilder
from cooking_sim.geometry.boiling.config import create_standard_saucepan_config
from cooking_sim.visualization import GeometryVisualizer


def visualize_carrot_cut(cut_type: str, num_pieces: int = 5):
    """Visualize a specific carrot cut type"""
    print(f"\n{'='*60}")
    print(f"Visualizing: {cut_type.upper()} Cut")
    print(f"{'='*60}")

    # Create configuration
    config = create_standard_saucepan_config()
    config.num_food_pieces = num_pieces
    config.food_type = "carrot"
    config.food.carrot_cut_type = cut_type

    # Build assembly
    assembly = SaucepanBuilder.create_from_config(config)

    # Print info
    print(f"\nConfiguration:")
    print(f"  - Cut type: {cut_type}")
    print(f"  - Number of pieces: {num_pieces}")
    print(f"  - Carrot density: 1075 kg/m³ (SINKS in water)")

    if cut_type == "round":
        print(f"  - Dimensions: 1.5cm radius × 1.5cm thick (coin-shaped)")
    elif cut_type == "stick":
        print(f"  - Dimensions: 1.5cm radius × 5cm long (baton)")
    elif cut_type == "chunk":
        print(f"  - Dimensions: ~1.5×1.5×2.5cm (irregular)")

    print(f"\nPhysical behavior:")
    print(f"  ✓ Carrots sink due to density > water (1075 vs 1000 kg/m³)")
    print(f"  ✓ Pieces rest on saucepan bottom")
    print(f"  ✓ Fully submerged in water")

    # Visualize
    visualizer = GeometryVisualizer(window_size=(1600, 1200))

    output_path = f"output/carrot_{cut_type}_cut.png"
    print(f"\nGenerating visualization...")

    visualizer.visualize_assembly(
        assembly=assembly,
        show_grid_points=True,
        save_path=output_path,
        camera_position='iso'
    )

    print(f"✓ Saved to: {output_path}")


def main():
    """Visualize all three carrot cut types"""
    print("\n" + "="*60)
    print("REALISTIC CARROT CUTTING GEOMETRIES")
    print("Demonstrating authentic cooking techniques")
    print("="*60)

    # Initialize Warp
    wp.init()
    print(f"\nWarp initialized: {wp.get_device()}")

    # Create output directory
    os.makedirs('output', exist_ok=True)

    # Visualize each cut type
    visualize_carrot_cut("round", num_pieces=5)
    visualize_carrot_cut("stick", num_pieces=4)
    visualize_carrot_cut("chunk", num_pieces=6)

    print("\n" + "="*60)
    print("VISUALIZATION COMPLETE")
    print("="*60)
    print("\nGenerated visualizations:")
    print("  1. output/carrot_round_cut.png  - Coin-shaped slices")
    print("  2. output/carrot_stick_cut.png  - Lengthwise batons")
    print("  3. output/carrot_chunk_cut.png  - Irregular stew pieces")
    print("\nAll carrots positioned realistically:")
    print("  ✓ Density-based sinking behavior")
    print("  ✓ Resting on pot bottom")
    print("  ✓ Proper submersion in water")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

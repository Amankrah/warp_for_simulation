"""
Main Geometry Assembly Module

Assembles all corrected classifier components into complete geometry
Based on corrected_classifier_geometry.md specifications
"""

import numpy as np
import pyvista as pv
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .corrected_config import CorrectedClassifierConfig
from .components.chamber import build_chamber, build_cone
from .components.selector_rotor import build_selector_blades, build_selector_rotor
from .components.hub_assembly import build_hub_assembly, build_feed_ports
from .components.distributor import build_distributor_plate
from .components.air_inlets import build_air_inlets, build_inlet_guide_vanes
from .components.external_cyclone import build_external_cyclone, build_cyclone_inlet
from .components.shaft import build_vertical_shaft
from .components.outlets import build_fines_outlet, build_coarse_outlet


@dataclass
class GeometryAssembly:
    """
    Container for all geometry components of corrected classifier

    Components follow the corrected specifications from
    corrected_classifier_geometry.md
    """
    # Main chamber
    chamber: pv.PolyData
    cone: pv.PolyData

    # Shaft and rotation components
    shaft: pv.PolyData
    distributor: pv.PolyData
    selector_blades: List[pv.PolyData]
    hub: pv.PolyData
    feed_ports: List[pv.PolyData] = field(default_factory=list)

    # Air system
    air_inlets: List[pv.PolyData] = field(default_factory=list)
    inlet_vanes: List[List[pv.PolyData]] = field(default_factory=list)

    # Outlets
    fines_outlet: pv.PolyData = None
    coarse_outlet: pv.PolyData = None

    # External cyclone
    cyclone_cylinder: Optional[pv.PolyData] = None
    cyclone_cone: Optional[pv.PolyData] = None
    cyclone_vortex_finder: Optional[pv.PolyData] = None
    cyclone_inlet: Optional[pv.PolyData] = None

    # Configuration
    config: CorrectedClassifierConfig = None

    def get_all_meshes(self) -> Dict[str, pv.PolyData]:
        """Get dictionary of all meshes"""
        meshes = {
            'chamber': self.chamber,
            'cone': self.cone,
            'shaft': self.shaft,
            'distributor': self.distributor,
            'hub': self.hub,
            'fines_outlet': self.fines_outlet,
            'coarse_outlet': self.coarse_outlet
        }

        # Add selector blades
        for i, blade in enumerate(self.selector_blades):
            meshes[f'selector_blade_{i}'] = blade

        # Add air inlets
        for i, inlet in enumerate(self.air_inlets):
            meshes[f'air_inlet_{i}'] = inlet

        # Add feed ports
        for i, port in enumerate(self.feed_ports):
            meshes[f'feed_port_{i}'] = port

        # Add cyclone if present
        if self.cyclone_cylinder is not None:
            meshes['cyclone_cylinder'] = self.cyclone_cylinder
            meshes['cyclone_cone'] = self.cyclone_cone
            meshes['cyclone_vortex_finder'] = self.cyclone_vortex_finder
            if self.cyclone_inlet is not None:
                meshes['cyclone_inlet'] = self.cyclone_inlet

        return meshes

    def count_components(self) -> dict:
        """Count all components"""
        return {
            'selector_blades': len(self.selector_blades),
            'air_inlets': len(self.air_inlets),
            'feed_ports': len(self.feed_ports),
            'inlet_vane_sets': len(self.inlet_vanes),
            'has_cyclone': self.cyclone_cylinder is not None
        }


def build_complete_classifier(
    config: CorrectedClassifierConfig,
    include_cyclone: bool = True,
    include_vanes: bool = True,
    include_ports: bool = True
) -> GeometryAssembly:
    """
    Build complete corrected classifier geometry

    Args:
        config: Corrected classifier configuration
        include_cyclone: Include external cyclone system
        include_vanes: Include air inlet guide vanes
        include_ports: Include hub feed ports

    Returns:
        GeometryAssembly with all components
    """
    print("=" * 70)
    print("BUILDING CORRECTED AIR CLASSIFIER GEOMETRY")
    print("Cyclone Air Classifier Configuration")
    print("=" * 70)

    # Build main chamber
    print("\n[1/10] Building classification chamber...")
    chamber = build_chamber(config)
    cone = build_cone(config)
    print(f"  ✓ Chamber: Ø{config.chamber_diameter*1000:.0f}mm × H{config.chamber_height*1000:.0f}mm")
    print(f"  ✓ Cone: H={config.cone_height*1000:.0f}mm, {config.cone_angle:.0f}°")

    # Build vertical shaft
    print("\n[2/10] Building vertical shaft...")
    shaft = build_vertical_shaft(config)
    print(f"  ✓ Shaft: Ø{config.shaft_diameter*1000:.0f}mm, Z={config.shaft_bottom_z:.2f}m to {config.shaft_top_z:.2f}m")

    # Build distributor plate
    print("\n[3/10] Building distributor plate...")
    distributor = build_distributor_plate(config)
    print(f"  ✓ Distributor: Ø{config.distributor_diameter*1000:.0f}mm at Z={config.distributor_position_z:.2f}m")

    # Build selector rotor
    print("\n[4/10] Building selector rotor...")
    selector_blades = build_selector_blades(config)
    print(f"  ✓ Selector: {config.selector_blade_count} blades, Ø{config.selector_diameter*1000:.0f}mm")
    print(f"    • Blade thickness: {config.selector_blade_thickness*1000:.1f}mm (corrected)")
    print(f"    • Blade height: {config.selector_blade_height*1000:.0f}mm (corrected)")
    print(f"    • Blade gap: {config.selector_blade_gap*1000:.1f}mm")

    # Build hub assembly
    print("\n[5/10] Building hub assembly...")
    hub = build_hub_assembly(config)
    feed_ports = build_feed_ports(config) if include_ports else []
    print(f"  ✓ Hub: Ø{config.hub_outer_diameter*1000:.0f}mm with {len(feed_ports)} feed ports")

    # Build air inlets
    print("\n[6/10] Building air distribution system...")
    air_inlets = build_air_inlets(config)
    inlet_vanes = build_inlet_guide_vanes(config) if include_vanes else []
    print(f"  ✓ Air inlets: {len(air_inlets)} × Ø{config.air_inlet_diameter*1000:.0f}mm")
    if include_vanes:
        print(f"  ✓ Guide vanes: {config.air_inlet_vane_count} per inlet @ {config.air_inlet_vane_angle:.0f}°")

    # Build outlets
    print("\n[7/10] Building outlets...")
    fines_outlet = build_fines_outlet(config)
    coarse_outlet = build_coarse_outlet(config)
    print(f"  ✓ Fines outlet: Ø{config.fines_outlet_diameter*1000:.0f}mm (to cyclone)")
    print(f"  ✓ Coarse outlet: Ø{config.coarse_outlet_diameter*1000:.0f}mm")

    # Build external cyclone
    cyclone_cylinder = None
    cyclone_cone = None
    cyclone_vortex_finder = None
    cyclone_inlet = None

    if include_cyclone:
        print("\n[8/10] Building external cyclone (Stairmand high-efficiency)...")
        cyclone_cylinder, cyclone_cone, cyclone_vortex_finder = build_external_cyclone(config)
        cyclone_inlet = build_cyclone_inlet(config)
        print(f"  ✓ Cyclone body: Ø{config.cyclone_body_diameter*1000:.0f}mm")
        print(f"  ✓ Cylinder height: {config.cyclone_cylinder_height*1000:.0f}mm")
        print(f"  ✓ Cone height: {config.cyclone_cone_height*1000:.0f}mm")
        print(f"  ✓ Total height: {config.cyclone_total_height*1000:.0f}mm")
        print(f"  ✓ Vortex finder: Ø{config.cyclone_vortex_finder_diameter*1000:.0f}mm")
    else:
        print("\n[8/10] Skipping external cyclone...")

    # Create assembly
    print("\n[9/10] Assembling components...")
    assembly = GeometryAssembly(
        chamber=chamber,
        cone=cone,
        shaft=shaft,
        distributor=distributor,
        selector_blades=selector_blades,
        hub=hub,
        feed_ports=feed_ports,
        air_inlets=air_inlets,
        inlet_vanes=inlet_vanes,
        fines_outlet=fines_outlet,
        coarse_outlet=coarse_outlet,
        cyclone_cylinder=cyclone_cylinder,
        cyclone_cone=cyclone_cone,
        cyclone_vortex_finder=cyclone_vortex_finder,
        cyclone_inlet=cyclone_inlet,
        config=config
    )

    # Summary
    print("\n[10/10] Assembly complete!")
    print("\n📊 COMPONENT SUMMARY:")
    counts = assembly.count_components()
    print(f"  • Selector blades: {counts['selector_blades']}")
    print(f"  • Air inlets: {counts['air_inlets']}")
    print(f"  • Feed ports: {counts['feed_ports']}")
    print(f"  • External cyclone: {'Yes' if counts['has_cyclone'] else 'No'}")

    meshes = assembly.get_all_meshes()
    total_points = sum(m.n_points for m in meshes.values() if m is not None)
    total_cells = sum(m.n_cells for m in meshes.values() if m is not None)
    print(f"\n🔢 MESH STATISTICS:")
    print(f"  • Total meshes: {len(meshes)}")
    print(f"  • Total points: {total_points:,}")
    print(f"  • Total cells: {total_cells:,}")

    print("\n" + "=" * 70)
    print("✓ GEOMETRY CONSTRUCTION COMPLETE")
    print("=" * 70)

    return assembly


def save_geometry(
    assembly: GeometryAssembly,
    base_path: str,
    format: str = 'stl'
):
    """
    Save all geometry components to files

    Args:
        assembly: Geometry assembly
        base_path: Base path for saved files
        format: File format ('stl', 'vtk', 'ply')
    """
    import os

    # Create directory if needed
    os.makedirs(base_path, exist_ok=True)

    print(f"\nSaving geometry to: {base_path}")
    print(f"Format: {format}")

    meshes = assembly.get_all_meshes()

    for name, mesh in meshes.items():
        if mesh is not None:
            filepath = os.path.join(base_path, f"{name}.{format}")
            mesh.save(filepath)
            print(f"  ✓ Saved {name}")

    print(f"\n✓ Saved {len(meshes)} components to {base_path}")


if __name__ == "__main__":
    from .corrected_config import create_default_config

    # Create configuration
    config = create_default_config()

    # Build complete geometry
    assembly = build_complete_classifier(
        config,
        include_cyclone=True,
        include_vanes=True,
        include_ports=True
    )

    print("\n✓ Geometry assembly module loaded successfully")
    print("\nTo visualize, run:")
    print("  from air_classifier.geometry.visualize import visualize_complete_assembly")
    print("  visualize_complete_assembly(assembly)")

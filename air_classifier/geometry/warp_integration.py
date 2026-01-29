"""
WARP Integration Module for Air Classifier Geometry

This module provides functions to convert PyVista geometry to WARP mesh formats
and set up boundary conditions for DEM/particle simulations.
"""

import numpy as np
import warp as wp
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pyvista as pv

from .assembly import GeometryAssembly
from .corrected_config import CorrectedClassifierConfig


def load_stl_to_warp_mesh(stl_path: str, device: str = "cuda:0") -> wp.Mesh:
    """
    Load an STL file and convert it to a WARP mesh
    
    Args:
        stl_path: Path to STL file
        device: WARP device ('cuda:0', 'cpu', etc.)
        
    Returns:
        WARP mesh object
    """
    # Read STL with PyVista
    mesh = pv.read(stl_path)
    
    # Use the same conversion function
    return create_warp_mesh_from_pyvista(mesh, device=device)


def create_warp_mesh_from_pyvista(mesh: pv.PolyData, device: str = "cuda:0") -> wp.Mesh:
    """
    Convert a PyVista mesh directly to WARP mesh
    
    Args:
        mesh: PyVista PolyData mesh
        device: WARP device
        
    Returns:
        WARP mesh object
    """
    # Extract vertices
    vertices = mesh.points.astype(np.float32)
    
    # Extract faces (PyVista stores as [n, i0, i1, i2, ..., n, i0, i1, i2, ...])
    # where n is the number of vertices in each face
    faces_flat = mesh.faces
    
    # Parse PyVista face format: iterate through and extract triangles
    triangles = []
    i = 0
    while i < len(faces_flat):
        n_verts = int(faces_flat[i])
        i += 1
        
        if n_verts == 3:
            # Triangle: directly add indices
            triangles.append([faces_flat[i], faces_flat[i+1], faces_flat[i+2]])
            i += 3
        elif n_verts == 4:
            # Quad: split into two triangles
            v0, v1, v2, v3 = faces_flat[i], faces_flat[i+1], faces_flat[i+2], faces_flat[i+3]
            triangles.append([v0, v1, v2])
            triangles.append([v0, v2, v3])
            i += 4
        else:
            # Polygon with >4 vertices: triangulate using fan method
            v0 = faces_flat[i]
            for j in range(1, n_verts - 1):
                triangles.append([v0, faces_flat[i+j], faces_flat[i+j+1]])
            i += n_verts
    
    if len(triangles) == 0:
        raise ValueError(f"Mesh has no valid faces (found {len(faces_flat)} face elements)")
    
    # Convert to numpy array and flatten
    triangles_array = np.array(triangles, dtype=np.int32)
    indices = triangles_array.flatten()
    
    # Create WARP mesh
    wp_mesh = wp.Mesh(
        points=wp.array(vertices, dtype=wp.vec3, device=device),
        indices=wp.array(indices, dtype=int, device=device)
    )
    
    return wp_mesh


def create_boundary_meshes(
    assembly: GeometryAssembly,
    device: str = "cuda:0",
    include_components: Optional[List[str]] = None
) -> Dict[str, wp.Mesh]:
    """
    Create WARP meshes for all boundary components
    
    Args:
        assembly: Geometry assembly
        device: WARP device
        include_components: List of component names to include (None = all)
        
    Returns:
        Dictionary mapping component names to WARP meshes
    """
    meshes = {}
    
    # Component mapping
    components = {
        'chamber': assembly.chamber,
        'cone': assembly.cone,
        'shaft': assembly.shaft,
        'distributor': assembly.distributor,
        'hub': assembly.hub,
        'fines_outlet': assembly.fines_outlet,
        'coarse_outlet': assembly.coarse_outlet,
    }
    
    # Add selector blades
    for i, blade in enumerate(assembly.selector_blades):
        components[f'selector_blade_{i}'] = blade
    
    # Add air inlets
    for i, inlet in enumerate(assembly.air_inlets):
        components[f'air_inlet_{i}'] = inlet
    
    # Add feed ports
    for i, port in enumerate(assembly.feed_ports):
        components[f'feed_port_{i}'] = port
    
    # Add cyclone components if present
    if assembly.cyclone_cylinder is not None:
        components['cyclone_cylinder'] = assembly.cyclone_cylinder
        components['cyclone_cone'] = assembly.cyclone_cone
        components['cyclone_vortex_finder'] = assembly.cyclone_vortex_finder
        if assembly.cyclone_inlet is not None:
            components['cyclone_inlet'] = assembly.cyclone_inlet
    
    # Filter components if requested
    if include_components is not None:
        components = {k: v for k, v in components.items() if k in include_components}
    
    # Convert each component
    for name, mesh in components.items():
        if mesh is not None and mesh.n_points > 0:
            try:
                wp_mesh = create_warp_mesh_from_pyvista(mesh, device=device)
                meshes[name] = wp_mesh
            except Exception as e:
                print(f"Warning: Failed to convert {name}: {e}")
    
    return meshes


def load_geometry_from_stl_directory(
    stl_dir: str,
    device: str = "cuda:0"
) -> Dict[str, wp.Mesh]:
    """
    Load all STL files from a directory and convert to WARP meshes
    
    Args:
        stl_dir: Directory containing STL files
        device: WARP device
        
    Returns:
        Dictionary mapping filenames (without .stl) to WARP meshes
    """
    stl_path = Path(stl_dir)
    meshes = {}
    
    for stl_file in stl_path.glob("*.stl"):
        name = stl_file.stem  # Filename without extension
        try:
            wp_mesh = load_stl_to_warp_mesh(str(stl_file), device=device)
            meshes[name] = wp_mesh
        except Exception as e:
            print(f"Warning: Failed to load {stl_file.name}: {e}")
    
    return meshes


def create_boundary_conditions(
    config: CorrectedClassifierConfig,
    assembly: GeometryAssembly
) -> Dict:
    """
    Create boundary condition parameters for simulation
    
    Args:
        config: Classifier configuration
        assembly: Geometry assembly
        
    Returns:
        Dictionary of boundary condition parameters
    """
    # Calculate selector rotor parameters
    selector_radius = config.selector_diameter / 2
    selector_z_center = (config.selector_zone_bottom + config.selector_zone_top) / 2
    selector_height = config.selector_zone_top - config.selector_zone_bottom
    
    # Air flow parameters
    air_flow_rate = config.air_flow_design  # m³/hr
    air_flow_rate_per_second = air_flow_rate / 3600  # m³/s
    
    # Calculate inlet velocity (assuming 4 inlets)
    inlet_area = np.pi * (config.air_inlet_diameter / 2) ** 2 * config.air_inlet_count
    inlet_velocity = air_flow_rate_per_second / inlet_area  # m/s
    
    # Rotor speed
    rotor_rpm = config.rotor_rpm_design
    rotor_omega = rotor_rpm * 2 * np.pi / 60  # rad/s
    tip_speed = rotor_omega * selector_radius  # m/s
    
    boundary_conditions = {
        # Geometry
        'chamber_radius': config.chamber_diameter / 2,
        'chamber_height': config.chamber_height,
        'cone_height': config.cone_height,
        'selector_radius': selector_radius,
        'selector_z_center': selector_z_center,
        'selector_height': selector_height,
        'distributor_radius': config.distributor_diameter / 2,
        'distributor_z': config.distributor_position_z,
        
        # Motion
        'rotor_rpm': rotor_rpm,
        'rotor_omega': rotor_omega,
        'tip_speed': tip_speed,
        
        # Air flow
        'air_flow_rate': air_flow_rate,
        'air_flow_rate_per_second': air_flow_rate_per_second,
        'inlet_velocity': inlet_velocity,
        'inlet_count': config.air_inlet_count,
        'inlet_diameter': config.air_inlet_diameter,
        
        # Outlets
        'fines_outlet_radius': config.fines_outlet_diameter / 2,
        'fines_outlet_z': config.fines_outlet_position_z,
        'coarse_outlet_radius': config.coarse_outlet_diameter / 2,
        
        # Material properties (defaults - should be overridden)
        'air_density': 1.2,  # kg/m³
        'air_viscosity': 1.81e-5,  # Pa·s
        'gravity': 9.81,  # m/s²
    }
    
    return boundary_conditions


@wp.kernel
def check_particle_boundary(
    positions: wp.array(dtype=wp.vec3),
    active: wp.array(dtype=int),
    chamber_radius: float,
    chamber_height: float,
    cone_height: float,
    z_min: float,
    z_max: float
):
    """Check if particles are within chamber boundaries"""
    i = wp.tid()
    
    if active[i] == 0:
        return
    
    pos = positions[i]
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z = pos[2]
    
    # Check if outside chamber
    if r > chamber_radius or z < z_min or z > z_max:
        active[i] = 0  # Deactivate particle


# =============================================================================
# Example usage
# =============================================================================

if __name__ == "__main__":
    from .corrected_config import create_default_config
    from .assembly import build_complete_classifier
    
    print("=" * 70)
    print("WARP INTEGRATION TEST")
    print("=" * 70)
    
    # Initialize WARP
    wp.init()
    
    # Build geometry
    print("\nBuilding geometry...")
    config = create_default_config()
    assembly = build_complete_classifier(config, include_cyclone=True)
    
    # Create WARP meshes
    print("\nConverting to WARP meshes...")
    # Check device availability
    try:
        test_device = wp.get_device("cuda:0")
        test_array = wp.zeros(1, dtype=float, device="cuda:0")
        device = "cuda:0"
    except Exception:
        device = "cpu"
    print(f"  Using device: {device}")
    
    boundary_meshes = create_boundary_meshes(assembly, device=device)
    print(f"\n✓ Created {len(boundary_meshes)} boundary meshes:")
    for name, mesh in boundary_meshes.items():
        print(f"  • {name}: {mesh.points.shape[0]} points, {mesh.indices.shape[0] // 3} faces")
    
    # Create boundary conditions
    print("\nCreating boundary conditions...")
    bc = create_boundary_conditions(config, assembly)
    print(f"  Rotor RPM: {bc['rotor_rpm']:.0f}")
    print(f"  Tip speed: {bc['tip_speed']:.1f} m/s")
    print(f"  Air flow: {bc['air_flow_rate']:.0f} m³/hr")
    print(f"  Inlet velocity: {bc['inlet_velocity']:.1f} m/s")
    
    print("\n" + "=" * 70)
    print("✓ WARP integration test complete")
    print("=" * 70)
    
    print("\n💡 Next steps:")
    print("  1. Use boundary_meshes in WARP collision detection")
    print("  2. Use boundary_conditions for particle dynamics")
    print("  3. Implement particle injection at feed ports")
    print("  4. Track particles through selector rotor")
    print("  5. Collect fines and coarse fractions")

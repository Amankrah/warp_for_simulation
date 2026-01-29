"""
WARP Integration Module for Air Classifier Geometry (FIXED)

This module provides functions to convert PyVista geometry to WARP mesh formats
and set up boundary conditions for DEM/particle simulations.

FIXES:
- Proper handling of PyVista face formats (triangles, quads, mixed)
- Triangulation before conversion
- Robust error handling
- Support for empty meshes
"""

import numpy as np
import warp as wp
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
import pyvista as pv

# Try to import geometry modules (may not be available in all contexts)
try:
    from air_classifier.geometry.assembly import GeometryAssembly
    from air_classifier.geometry.corrected_config import CorrectedClassifierConfig
except ImportError:
    GeometryAssembly = None
    CorrectedClassifierConfig = None


# =============================================================================
# MESH CONVERSION FUNCTIONS (FIXED)
# =============================================================================

def pyvista_to_triangles(mesh: pv.PolyData) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert PyVista mesh to vertices and triangle indices
    
    Handles:
    - Pure triangle meshes
    - Quad meshes (splits into triangles)
    - Mixed meshes
    - Meshes with polygon faces
    
    Args:
        mesh: PyVista PolyData mesh
        
    Returns:
        Tuple of (vertices, triangle_indices)
        - vertices: (N, 3) float32 array
        - triangle_indices: (M, 3) int32 array
    """
    if mesh is None or mesh.n_points == 0:
        return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.int32)
    
    # Triangulate the mesh first - this converts all faces to triangles
    try:
        tri_mesh = mesh.triangulate()
    except Exception:
        # If triangulation fails, try to work with original
        tri_mesh = mesh
    
    # Extract vertices
    vertices = tri_mesh.points.astype(np.float32)
    
    # Extract faces - need to handle PyVista's face format
    # PyVista stores faces as: [n0, i0, i1, ..., n1, j0, j1, ...]
    # where n is the number of vertices in each face
    
    if tri_mesh.n_cells == 0:
        return vertices, np.zeros((0, 3), dtype=np.int32)
    
    faces_raw = tri_mesh.faces
    
    # Parse the faces array
    triangles = []
    idx = 0
    
    while idx < len(faces_raw):
        n_verts = faces_raw[idx]
        
        if n_verts == 3:
            # Triangle - take directly
            triangles.append(faces_raw[idx + 1:idx + 4])
        elif n_verts == 4:
            # Quad - split into two triangles
            i0, i1, i2, i3 = faces_raw[idx + 1:idx + 5]
            triangles.append([i0, i1, i2])
            triangles.append([i0, i2, i3])
        elif n_verts > 4:
            # Polygon - fan triangulation from first vertex
            base = faces_raw[idx + 1]
            for j in range(1, n_verts - 1):
                triangles.append([
                    base,
                    faces_raw[idx + 1 + j],
                    faces_raw[idx + 1 + j + 1]
                ])
        
        idx += n_verts + 1
    
    if len(triangles) == 0:
        return vertices, np.zeros((0, 3), dtype=np.int32)
    
    triangle_indices = np.array(triangles, dtype=np.int32)
    
    return vertices, triangle_indices


def load_stl_to_warp_mesh(stl_path: str, device: str = "cuda:0") -> Optional[wp.Mesh]:
    """
    Load an STL file and convert it to a WARP mesh
    
    Args:
        stl_path: Path to STL file
        device: WARP device ('cuda:0', 'cpu', etc.)
        
    Returns:
        WARP mesh object, or None if loading fails
    """
    try:
        mesh = pv.read(stl_path)
        return create_warp_mesh_from_pyvista(mesh, device=device)
    except Exception as e:
        print(f"Warning: Failed to load STL {stl_path}: {e}")
        return None


def create_warp_mesh_from_pyvista(mesh: pv.PolyData, device: str = "cuda:0") -> Optional[wp.Mesh]:
    """
    Convert a PyVista mesh to WARP mesh (FIXED VERSION)
    
    Args:
        mesh: PyVista PolyData mesh
        device: WARP device ('cuda:0', 'cpu', etc.)
        
    Returns:
        WARP mesh object, or None if conversion fails
    """
    if mesh is None or mesh.n_points == 0:
        return None
    
    # Convert to triangles
    vertices, triangles = pyvista_to_triangles(mesh)
    
    if len(triangles) == 0:
        return None
    
    # Create WARP arrays
    try:
        points_wp = wp.array(vertices, dtype=wp.vec3, device=device)
        indices_wp = wp.array(triangles.flatten(), dtype=wp.int32, device=device)
        
        # Create WARP mesh
        wp_mesh = wp.Mesh(
            points=points_wp,
            indices=indices_wp
        )
        
        return wp_mesh
        
    except Exception as e:
        print(f"Warning: Failed to create WARP mesh: {e}")
        return None


# =============================================================================
# BOUNDARY MESH CREATION
# =============================================================================

def create_boundary_meshes(
    assembly: GeometryAssembly,
    device: str = "cuda:0",
    include_components: Optional[List[str]] = None,
    verbose: bool = True
) -> Dict[str, wp.Mesh]:
    """
    Create WARP meshes for all boundary components (FIXED VERSION)
    
    Args:
        assembly: Geometry assembly from build_complete_classifier()
        device: WARP device
        include_components: List of component names to include (None = all)
        verbose: Print progress messages
        
    Returns:
        Dictionary mapping component names to WARP meshes
    """
    meshes = {}
    failed = []
    
    # Build component dictionary
    components = {}
    
    # Main components
    if assembly.chamber is not None:
        components['chamber'] = assembly.chamber
    if assembly.cone is not None:
        components['cone'] = assembly.cone
    if assembly.shaft is not None:
        components['shaft'] = assembly.shaft
    if assembly.distributor is not None:
        components['distributor'] = assembly.distributor
    if assembly.hub is not None:
        components['hub'] = assembly.hub
    if assembly.fines_outlet is not None:
        components['fines_outlet'] = assembly.fines_outlet
    if assembly.coarse_outlet is not None:
        components['coarse_outlet'] = assembly.coarse_outlet
    
    # Selector blades
    for i, blade in enumerate(assembly.selector_blades):
        if blade is not None:
            components[f'selector_blade_{i}'] = blade
    
    # Air inlets
    for i, inlet in enumerate(assembly.air_inlets):
        if inlet is not None:
            components[f'air_inlet_{i}'] = inlet
    
    # Feed ports
    for i, port in enumerate(assembly.feed_ports):
        if port is not None:
            components[f'feed_port_{i}'] = port
    
    # Inlet guide vanes (nested list: inlet_vanes[i] is list of vanes for inlet i)
    if hasattr(assembly, 'inlet_vanes'):
        for inlet_idx, vane_list in enumerate(assembly.inlet_vanes):
            if vane_list is not None:
                for vane_idx, vane in enumerate(vane_list):
                    if vane is not None:
                        components[f'inlet_{inlet_idx}_vane_{vane_idx}'] = vane
    
    # Cyclone components
    if assembly.cyclone_cylinder is not None:
        components['cyclone_cylinder'] = assembly.cyclone_cylinder
    if assembly.cyclone_cone is not None:
        components['cyclone_cone'] = assembly.cyclone_cone
    if assembly.cyclone_vortex_finder is not None:
        components['cyclone_vortex_finder'] = assembly.cyclone_vortex_finder
    if assembly.cyclone_inlet is not None:
        components['cyclone_inlet'] = assembly.cyclone_inlet
    
    # Filter components if requested
    if include_components is not None:
        components = {k: v for k, v in components.items() if k in include_components}
    
    # Convert each component
    for name, pv_mesh in components.items():
        if pv_mesh is None or pv_mesh.n_points == 0:
            if verbose:
                print(f"  Skipping {name}: empty mesh")
            continue
        
        try:
            wp_mesh = create_warp_mesh_from_pyvista(pv_mesh, device=device)
            if wp_mesh is not None:
                meshes[name] = wp_mesh
                if verbose:
                    n_points = wp_mesh.points.shape[0]
                    n_tris = wp_mesh.indices.shape[0] // 3
                    print(f"  ✓ {name}: {n_points} points, {n_tris} triangles")
            else:
                failed.append(name)
        except Exception as e:
            failed.append(name)
            if verbose:
                print(f"  ✗ {name}: {e}")
    
    if verbose and len(failed) > 0:
        print(f"\n  Warning: {len(failed)} components failed to convert")
    
    return meshes


def load_geometry_from_stl_directory(
    stl_dir: str,
    device: str = "cuda:0",
    verbose: bool = True
) -> Dict[str, wp.Mesh]:
    """
    Load all STL files from a directory and convert to WARP meshes
    
    Args:
        stl_dir: Directory containing STL files
        device: WARP device
        verbose: Print progress messages
        
    Returns:
        Dictionary mapping filenames (without .stl) to WARP meshes
    """
    stl_path = Path(stl_dir)
    meshes = {}
    
    stl_files = list(stl_path.glob("*.stl"))
    
    if verbose:
        print(f"Loading {len(stl_files)} STL files from {stl_dir}...")
    
    for stl_file in stl_files:
        name = stl_file.stem
        wp_mesh = load_stl_to_warp_mesh(str(stl_file), device=device)
        
        if wp_mesh is not None:
            meshes[name] = wp_mesh
            if verbose:
                n_points = wp_mesh.points.shape[0]
                n_tris = wp_mesh.indices.shape[0] // 3
                print(f"  ✓ {name}: {n_points} points, {n_tris} triangles")
        else:
            if verbose:
                print(f"  ✗ {name}: failed to load")
    
    return meshes


# =============================================================================
# BOUNDARY CONDITIONS
# =============================================================================

def create_boundary_conditions(
    config: CorrectedClassifierConfig,
    assembly: Optional[GeometryAssembly] = None
) -> Dict[str, Any]:
    """
    Create boundary condition parameters for simulation
    
    Args:
        config: Classifier configuration
        assembly: Optional geometry assembly (for derived values)
        
    Returns:
        Dictionary of boundary condition parameters
    """
    # Selector rotor parameters
    selector_radius = config.selector_diameter / 2
    selector_z_center = (config.selector_zone_bottom + config.selector_zone_top) / 2
    selector_height = config.selector_zone_top - config.selector_zone_bottom
    
    # Rotor angular velocity
    rotor_omega = config.rotor_rpm_design * 2 * np.pi / 60  # rad/s
    tip_speed = rotor_omega * selector_radius  # m/s
    
    # Air flow parameters
    air_flow_m3s = config.air_flow_design / 3600  # m³/s
    inlet_area = np.pi * (config.air_inlet_diameter / 2) ** 2 * config.air_inlet_count
    inlet_velocity = air_flow_m3s / inlet_area  # m/s
    
    # Chamber radial velocity (at selector radius)
    selector_area = 2 * np.pi * selector_radius * selector_height
    radial_velocity = air_flow_m3s / selector_area
    
    # Particle properties (yellow pea)
    protein_density = 1350.0  # kg/m³
    protein_diameter_mean = 5e-6  # m (5 um)
    starch_density = 1520.0  # kg/m³
    starch_diameter_mean = 28e-6  # m (28 um)
    
    boundary_conditions = {
        # === GEOMETRY ===
        'chamber_radius': config.chamber_diameter / 2,
        'chamber_height': config.chamber_height,
        'cone_height': config.cone_height,
        'cone_angle_rad': np.radians(config.cone_angle / 2),
        
        # === SELECTOR ROTOR ===
        'selector_radius': selector_radius,
        'selector_z_min': config.selector_zone_bottom,
        'selector_z_max': config.selector_zone_top,
        'selector_z_center': selector_z_center,
        'selector_height': selector_height,
        'selector_blade_count': config.selector_blade_count,
        
        # === DISTRIBUTOR ===
        'distributor_radius': config.distributor_diameter / 2,
        'distributor_z': config.distributor_position_z,
        
        # === ROTOR MOTION ===
        'rotor_rpm': config.rotor_rpm_design,
        'rotor_omega': rotor_omega,
        'tip_speed': tip_speed,
        
        # === AIR FLOW ===
        'air_flow_m3hr': config.air_flow_design,
        'air_flow_m3s': air_flow_m3s,
        'air_flow_rate': config.air_flow_design,  # For backward compatibility
        'air_flow_rate_per_second': air_flow_m3s,  # For backward compatibility
        'inlet_velocity': inlet_velocity,
        'radial_velocity': radial_velocity,
        'inlet_count': config.air_inlet_count,
        'inlet_diameter': config.air_inlet_diameter,
        'inlet_z': config.air_inlet_position_z,
        
        # === OUTLETS ===
        'fines_outlet_radius': config.fines_outlet_diameter / 2,
        'fines_outlet_z': config.fines_outlet_position_z,
        'coarse_outlet_radius': config.coarse_outlet_diameter / 2,
        'coarse_outlet_z': -config.cone_height,
        
        # === AIR PROPERTIES ===
        'air_density': 1.2,  # kg/m³
        'air_viscosity': 1.81e-5,  # Pa·s
        'gravity': 9.81,  # m/s² (scalar for backward compatibility)
        
        # === PARTICLE PROPERTIES ===
        'protein_density': protein_density,
        'protein_diameter_mean': protein_diameter_mean,
        'protein_diameter_std': 2e-6,
        'starch_density': starch_density,
        'starch_diameter_mean': starch_diameter_mean,
        'starch_diameter_std': 8e-6,
        
        # === DERIVED PARAMETERS ===
        'target_d50': config.target_d50 * 1e-6,  # Convert to meters
        'predicted_d50': config.calculate_cut_size(
            config.rotor_rpm_design, 
            config.air_flow_design
        ) * 1e-6,
    }
    
    return boundary_conditions


def get_device(preferred: str = "cuda:0") -> str:
    """
    Get available WARP device
    
    Args:
        preferred: Preferred device string
        
    Returns:
        Available device string
    """
    try:
        wp.get_device(preferred)
        # Test with small array
        test = wp.zeros(1, dtype=wp.float32, device=preferred)
        del test
        return preferred
    except Exception:
        print(f"Warning: {preferred} not available, using CPU")
        return "cpu"


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

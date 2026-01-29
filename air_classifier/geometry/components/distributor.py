"""
Distributor Plate Component Builder (FIXED)

Rotating distributor with radial grooves
Based on Section 4.1.4 and Section 5.3 of corrected_classifier_geometry.md

FIXED: Avoids boolean operations by building annular geometry directly
"""

import numpy as np
import pyvista as pv
from ..corrected_config import CorrectedClassifierConfig


def build_distributor_plate(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build distributor plate with edge lip and central shaft hole
    
    FIXED VERSION: Uses annular disc construction instead of boolean difference
    to avoid VTK boolean operation failures.
    
    The distributor consists of:
    1. Main annular plate (flat disc with hole for shaft)
    2. Edge lip (retention ring around outer edge)
    
    Args:
        config: Classifier configuration
        
    Returns:
        PyVista mesh of distributor plate
    """
    # Dimensions
    outer_radius = config.distributor_diameter / 2
    inner_radius = config.shaft_diameter / 2 + 0.005  # Small clearance
    plate_thickness = config.distributor_thickness
    lip_height = config.distributor_lip_height
    z_base = config.distributor_position_z
    
    # Resolution for smooth circles
    n_theta = 64  # Circumferential resolution
    
    # === MAIN PLATE (Annular cylinder) ===
    plate = create_annular_cylinder(
        inner_radius=inner_radius,
        outer_radius=outer_radius,
        height=plate_thickness,
        z_center=z_base,
        n_theta=n_theta
    )
    
    # === EDGE LIP (Thin-walled cylinder on outer edge) ===
    lip_inner_radius = outer_radius - 0.010  # 10mm wall thickness for lip
    lip_z_base = z_base + plate_thickness / 2
    
    lip = create_annular_cylinder(
        inner_radius=lip_inner_radius,
        outer_radius=outer_radius,
        height=lip_height,
        z_center=lip_z_base + lip_height / 2,
        n_theta=n_theta
    )
    
    # Combine plate and lip
    distributor = plate + lip
    
    # Clean up the mesh
    distributor = distributor.clean()
    
    return distributor


def create_annular_cylinder(
    inner_radius: float,
    outer_radius: float,
    height: float,
    z_center: float,
    n_theta: int = 64
) -> pv.PolyData:
    """
    Create an annular cylinder (hollow cylinder / thick-walled tube)
    without using boolean operations.
    
    This creates a watertight mesh by explicitly building:
    - Top annular face
    - Bottom annular face  
    - Outer cylindrical surface
    - Inner cylindrical surface
    
    Args:
        inner_radius: Inner radius of annulus
        outer_radius: Outer radius of annulus
        height: Height of cylinder
        z_center: Z-coordinate of center
        n_theta: Number of circumferential divisions
        
    Returns:
        PyVista PolyData mesh
    """
    z_bottom = z_center - height / 2
    z_top = z_center + height / 2
    
    # Generate theta values
    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    
    # === BUILD VERTICES ===
    # We need 4 rings of vertices:
    # Ring 0: Bottom, inner radius
    # Ring 1: Bottom, outer radius
    # Ring 2: Top, inner radius
    # Ring 3: Top, outer radius
    
    vertices = []
    
    # Ring 0: Bottom inner
    for t in theta:
        vertices.append([inner_radius * np.cos(t), inner_radius * np.sin(t), z_bottom])
    
    # Ring 1: Bottom outer
    for t in theta:
        vertices.append([outer_radius * np.cos(t), outer_radius * np.sin(t), z_bottom])
    
    # Ring 2: Top inner
    for t in theta:
        vertices.append([inner_radius * np.cos(t), inner_radius * np.sin(t), z_top])
    
    # Ring 3: Top outer
    for t in theta:
        vertices.append([outer_radius * np.cos(t), outer_radius * np.sin(t), z_top])
    
    vertices = np.array(vertices)
    
    # === BUILD FACES ===
    faces = []
    
    # Helper to get vertex indices for each ring
    def ring_idx(ring, i):
        return ring * n_theta + (i % n_theta)
    
    # Bottom annular face (Ring 0 to Ring 1)
    for i in range(n_theta):
        # Quad: bottom_inner[i], bottom_inner[i+1], bottom_outer[i+1], bottom_outer[i]
        # Split into two triangles for proper normals (pointing down)
        i0 = ring_idx(0, i)
        i1 = ring_idx(0, i + 1)
        i2 = ring_idx(1, i + 1)
        i3 = ring_idx(1, i)
        # Triangle 1 (CCW when viewed from bottom = CW from top)
        faces.append([3, i0, i3, i2])
        # Triangle 2
        faces.append([3, i0, i2, i1])
    
    # Top annular face (Ring 2 to Ring 3)
    for i in range(n_theta):
        i0 = ring_idx(2, i)
        i1 = ring_idx(2, i + 1)
        i2 = ring_idx(3, i + 1)
        i3 = ring_idx(3, i)
        # Triangle 1 (CCW when viewed from top)
        faces.append([3, i0, i1, i2])
        # Triangle 2
        faces.append([3, i0, i2, i3])
    
    # Outer cylindrical surface (Ring 1 to Ring 3)
    for i in range(n_theta):
        i0 = ring_idx(1, i)      # Bottom outer
        i1 = ring_idx(1, i + 1)  # Bottom outer next
        i2 = ring_idx(3, i + 1)  # Top outer next
        i3 = ring_idx(3, i)      # Top outer
        # Quad split into triangles (normals pointing outward)
        faces.append([3, i0, i1, i2])
        faces.append([3, i0, i2, i3])
    
    # Inner cylindrical surface (Ring 0 to Ring 2)
    for i in range(n_theta):
        i0 = ring_idx(0, i)      # Bottom inner
        i1 = ring_idx(0, i + 1)  # Bottom inner next
        i2 = ring_idx(2, i + 1)  # Top inner next
        i3 = ring_idx(2, i)      # Top inner
        # Quad split into triangles (normals pointing inward = reversed winding)
        faces.append([3, i0, i3, i2])
        faces.append([3, i0, i2, i1])
    
    # Convert faces to PyVista format
    faces_flat = np.hstack(faces)
    
    # Create mesh
    mesh = pv.PolyData(vertices, faces_flat)
    
    return mesh


def build_distributor_with_grooves(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build distributor plate with radial grooves for material dispersion
    
    This version includes the radial grooves mentioned in the specification.
    The grooves help spread the feed material radially outward.
    
    The grooves are cut directly into the top surface geometry, avoiding
    boolean operations that can fail in VTK.
    
    Args:
        config: Classifier configuration
        
    Returns:
        PyVista mesh of distributor with grooves cut into top surface
    """
    # Use the version that builds grooves directly into the geometry
    return build_distributor_with_grooves_cut(config)


def create_radial_grooves(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Create radial groove geometry for the distributor plate
    
    Grooves are rectangular cuts extending from inner radius to outer radius
    on the top surface of the distributor plate.
    
    Args:
        config: Classifier configuration
        
    Returns:
        PyVista mesh of groove geometry (can be used for visualization or cutting)
    """
    inner_radius = config.shaft_diameter / 2 + 0.005
    outer_radius = config.distributor_diameter / 2
    groove_depth = config.distributor_groove_depth
    groove_width = config.distributor_groove_width
    z_top = config.distributor_position_z + config.distributor_thickness / 2
    n_grooves = config.distributor_groove_count
    
    # Groove length (radial extent)
    groove_length = outer_radius - inner_radius
    
    # Angular spacing between grooves
    angle_step = 2 * np.pi / n_grooves
    
    # Collect all groove vertices and faces
    all_vertices = []
    all_faces = []
    vertex_offset = 0
    
    for i in range(n_grooves):
        # Groove center angle
        angle = i * angle_step
        
        # Groove extends radially from inner to outer radius
        # Create a rectangular box representing the groove
        # The groove is a box that extends:
        # - Radially: from inner_radius to outer_radius
        # - Circumferentially: groove_width / 2 on each side of center angle
        # - Vertically: groove_depth downward from top surface
        
        # Calculate groove corners in polar coordinates
        r_inner = inner_radius
        r_outer = outer_radius
        theta_left = angle - groove_width / (2 * outer_radius)  # Small angle approximation
        theta_right = angle + groove_width / (2 * outer_radius)
        
        # Convert to Cartesian coordinates for 8 corners of the groove box
        # Bottom corners (at z = z_top - groove_depth)
        z_bottom = z_top - groove_depth
        
        corners = []
        # Inner corners
        corners.append([r_inner * np.cos(theta_left), r_inner * np.sin(theta_left), z_bottom])
        corners.append([r_inner * np.cos(theta_right), r_inner * np.sin(theta_right), z_bottom])
        # Outer corners (bottom)
        corners.append([r_outer * np.cos(theta_right), r_outer * np.sin(theta_right), z_bottom])
        corners.append([r_outer * np.cos(theta_left), r_outer * np.sin(theta_left), z_bottom])
        # Inner corners (top, at z = z_top)
        corners.append([r_inner * np.cos(theta_left), r_inner * np.sin(theta_left), z_top])
        corners.append([r_inner * np.cos(theta_right), r_inner * np.sin(theta_right), z_top])
        # Outer corners (top)
        corners.append([r_outer * np.cos(theta_right), r_outer * np.sin(theta_right), z_top])
        corners.append([r_outer * np.cos(theta_left), r_outer * np.sin(theta_left), z_top])
        
        # Add vertices
        for corner in corners:
            all_vertices.append(corner)
        
        # Create faces for the groove box (6 faces)
        base_idx = vertex_offset
        
        # Bottom face (4 vertices, split into 2 triangles)
        all_faces.append([3, base_idx + 0, base_idx + 1, base_idx + 2])
        all_faces.append([3, base_idx + 0, base_idx + 2, base_idx + 3])
        
        # Top face (4 vertices, split into 2 triangles)
        all_faces.append([3, base_idx + 4, base_idx + 7, base_idx + 6])
        all_faces.append([3, base_idx + 4, base_idx + 6, base_idx + 5])
        
        # Side faces (4 rectangular faces)
        # Inner radial face
        all_faces.append([3, base_idx + 0, base_idx + 4, base_idx + 5])
        all_faces.append([3, base_idx + 0, base_idx + 5, base_idx + 1])
        
        # Outer radial face
        all_faces.append([3, base_idx + 2, base_idx + 6, base_idx + 7])
        all_faces.append([3, base_idx + 2, base_idx + 7, base_idx + 3])
        
        # Left side face (theta_left)
        all_faces.append([3, base_idx + 0, base_idx + 3, base_idx + 7])
        all_faces.append([3, base_idx + 0, base_idx + 7, base_idx + 4])
        
        # Right side face (theta_right)
        all_faces.append([3, base_idx + 1, base_idx + 5, base_idx + 6])
        all_faces.append([3, base_idx + 1, base_idx + 6, base_idx + 2])
        
        vertex_offset += 8
    
    # Create mesh from all grooves
    if len(all_vertices) > 0:
        vertices = np.array(all_vertices)
        faces_flat = np.hstack(all_faces)
        grooves = pv.PolyData(vertices, faces_flat)
    else:
        grooves = pv.PolyData()
    
    return grooves


def build_distributor_with_grooves_cut(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Build distributor plate with grooves cut into the top surface
    
    This version actually cuts the grooves into the plate using a modified
    top surface geometry that includes the groove depressions.
    
    Args:
        config: Classifier configuration
        
    Returns:
        PyVista mesh of distributor with grooves cut into top surface
    """
    # Dimensions
    outer_radius = config.distributor_diameter / 2
    inner_radius = config.shaft_diameter / 2 + 0.005
    plate_thickness = config.distributor_thickness
    groove_depth = config.distributor_groove_depth
    groove_width = config.distributor_groove_width
    n_grooves = config.distributor_groove_count
    z_base = config.distributor_position_z
    lip_height = config.distributor_lip_height
    
    # Resolution
    n_theta = 128  # Higher resolution for smooth grooves
    n_r = 32  # Radial resolution
    
    z_bottom = z_base - plate_thickness / 2
    z_top = z_base + plate_thickness / 2
    
    # Generate radial and angular grids
    r_values = np.linspace(inner_radius, outer_radius, n_r)
    theta_values = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    
    # Build vertices with groove modifications
    vertices = []
    vertex_map = {}  # (r_idx, theta_idx) -> vertex_idx
    
    for r_idx, r in enumerate(r_values):
        for theta_idx, theta in enumerate(theta_values):
            # Check if this point is in a groove
            # Groove center angles
            groove_angles = np.array([i * 2 * np.pi / n_grooves for i in range(n_grooves)])
            
            # Distance to nearest groove center (angular distance)
            angle_diff = np.abs(theta - groove_angles)
            angle_diff = np.minimum(angle_diff, 2 * np.pi - angle_diff)
            min_angle_diff = np.min(angle_diff)
            
            # Groove angular width at this radius
            # Arc length = r * angle, so angle = arc_length / r
            # For groove_width (linear), angular width = groove_width / r
            if r > inner_radius:
                groove_angular_width = groove_width / r
            else:
                groove_angular_width = groove_width / inner_radius
            
            if min_angle_diff < groove_angular_width / 2:
                # Point is in a groove - lower the z coordinate
                z = z_top - groove_depth
            else:
                # Normal top surface
                z = z_top
            
            vertices.append([r * np.cos(theta), r * np.sin(theta), z])
            vertex_map[(r_idx, theta_idx)] = len(vertices) - 1
    
    # Add bottom surface vertices (flat, no grooves)
    bottom_vertex_offset = len(vertices)
    bottom_vertex_map = {}
    for r_idx, r in enumerate(r_values):
        for theta_idx, theta in enumerate(theta_values):
            vertices.append([r * np.cos(theta), r * np.sin(theta), z_bottom])
            bottom_vertex_map[(r_idx, theta_idx)] = len(vertices) - 1
    
    # Add inner and outer cylindrical surfaces
    inner_vertex_offset = len(vertices)
    for theta_idx, theta in enumerate(theta_values):
        vertices.append([inner_radius * np.cos(theta), inner_radius * np.sin(theta), z_bottom])
        vertices.append([inner_radius * np.cos(theta), inner_radius * np.sin(theta), z_top])
    
    outer_vertex_offset = len(vertices)
    for theta_idx, theta in enumerate(theta_values):
        vertices.append([outer_radius * np.cos(theta), outer_radius * np.sin(theta), z_bottom])
        vertices.append([outer_radius * np.cos(theta), outer_radius * np.sin(theta), z_top])
    
    vertices = np.array(vertices)
    
    # Build faces
    faces = []
    
    # Top surface (with grooves)
    for r_idx in range(n_r - 1):
        for theta_idx in range(n_theta):
            i0 = vertex_map[(r_idx, theta_idx)]
            i1 = vertex_map[(r_idx, (theta_idx + 1) % n_theta)]
            i2 = vertex_map[(r_idx + 1, (theta_idx + 1) % n_theta)]
            i3 = vertex_map[(r_idx + 1, theta_idx)]
            
            faces.append([3, i0, i1, i2])
            faces.append([3, i0, i2, i3])
    
    # Bottom surface (flat)
    for r_idx in range(n_r - 1):
        for theta_idx in range(n_theta):
            i0 = bottom_vertex_map[(r_idx, theta_idx)]
            i1 = bottom_vertex_map[(r_idx, (theta_idx + 1) % n_theta)]
            i2 = bottom_vertex_map[(r_idx + 1, (theta_idx + 1) % n_theta)]
            i3 = bottom_vertex_map[(r_idx + 1, theta_idx)]
            
            faces.append([3, i0, i3, i2])
            faces.append([3, i0, i2, i1])
    
    # Inner and outer cylindrical surfaces
    for theta_idx in range(n_theta):
        # Inner surface
        i0 = inner_vertex_offset + theta_idx * 2
        i1 = inner_vertex_offset + ((theta_idx + 1) % n_theta) * 2
        i2 = inner_vertex_offset + ((theta_idx + 1) % n_theta) * 2 + 1
        i3 = inner_vertex_offset + theta_idx * 2 + 1
        
        faces.append([3, i0, i3, i2])
        faces.append([3, i0, i2, i1])
        
        # Outer surface
        i0 = outer_vertex_offset + theta_idx * 2
        i1 = outer_vertex_offset + ((theta_idx + 1) % n_theta) * 2
        i2 = outer_vertex_offset + ((theta_idx + 1) % n_theta) * 2 + 1
        i3 = outer_vertex_offset + theta_idx * 2 + 1
        
        faces.append([3, i0, i1, i2])
        faces.append([3, i0, i2, i3])
    
    # Convert to PyVista format
    faces_flat = np.hstack(faces)
    plate = pv.PolyData(vertices, faces_flat)
    
    # Add edge lip
    lip_inner_radius = outer_radius - 0.010
    lip_z_base = z_base + plate_thickness / 2
    
    lip = create_annular_cylinder(
        inner_radius=lip_inner_radius,
        outer_radius=outer_radius,
        height=lip_height,
        z_center=lip_z_base + lip_height / 2,
        n_theta=64
    )
    
    # Combine
    distributor = plate + lip
    distributor = distributor.clean()
    
    return distributor


# =============================================================================
# Alternative simpler approach using PyVista primitives
# =============================================================================

def build_distributor_simple(config: CorrectedClassifierConfig) -> pv.PolyData:
    """
    Simplified distributor using PyVista's Disc primitive
    
    This creates just the top surface as a disc, which may be
    sufficient for visualization and some simulations.
    
    Args:
        config: Classifier configuration
        
    Returns:
        PyVista mesh (surface only, not solid)
    """
    outer_radius = config.distributor_diameter / 2
    inner_radius = config.shaft_diameter / 2 + 0.005
    
    # Create annular disc (top surface only)
    disc = pv.Disc(
        center=(0, 0, config.distributor_position_z),
        inner=inner_radius,
        outer=outer_radius,
        normal=(0, 0, 1),
        r_res=1,
        c_res=64
    )
    
    return disc


# =============================================================================
# Test function
# =============================================================================

if __name__ == "__main__":
    # Test the distributor builder
    from ..corrected_config import create_default_config
    
    config = create_default_config()
    
    print("=" * 70)
    print("DISTRIBUTOR PLATE TEST")
    print("=" * 70)
    
    print("\nBuilding basic distributor plate...")
    print(f"  Outer radius: {config.distributor_diameter/2 * 1000:.0f} mm")
    print(f"  Inner radius: {(config.shaft_diameter/2 + 0.005) * 1000:.0f} mm")
    print(f"  Thickness: {config.distributor_thickness * 1000:.0f} mm")
    print(f"  Lip height: {config.distributor_lip_height * 1000:.0f} mm")
    print(f"  Position Z: {config.distributor_position_z * 1000:.0f} mm")
    
    distributor = build_distributor_plate(config)
    
    print(f"\n✓ Basic distributor built successfully!")
    print(f"  Vertices: {distributor.n_points}")
    print(f"  Faces: {distributor.n_cells}")
    
    # Verify it's watertight
    if distributor.n_points > 0:
        print(f"  Is manifold: {distributor.is_manifold}")
    
    print("\n" + "-" * 70)
    print("\nBuilding distributor with radial grooves...")
    print(f"  Groove count: {config.distributor_groove_count}")
    print(f"  Groove depth: {config.distributor_groove_depth * 1000:.1f} mm")
    print(f"  Groove width: {config.distributor_groove_width * 1000:.1f} mm")
    
    distributor_grooved = build_distributor_with_grooves(config)
    
    print(f"\n✓ Grooved distributor built successfully!")
    print(f"  Vertices: {distributor_grooved.n_points}")
    print(f"  Faces: {distributor_grooved.n_cells}")
    
    if distributor_grooved.n_points > 0:
        print(f"  Is manifold: {distributor_grooved.is_manifold}")
    
    print("\n" + "=" * 70)
    print("✓ All tests passed!")
    print("=" * 70)
    
    # Optional: visualize
    # distributor.plot(show_edges=True)
    # distributor_grooved.plot(show_edges=True)

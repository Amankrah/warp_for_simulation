"""
Realistic liquid domain for boiling simulation

Physical Model:
---------------
Water behavior is governed by fundamental fluid properties:

1. **Gravity & Hydrostatic Pressure**
   - Water fills the container from bottom upward
   - Uniform horizontal layers due to gravitational settling
   - Pressure increases linearly with depth: P = ρgh

2. **Container Conformity**
   - Water takes the exact shape of the cylindrical chamber
   - Direct contact with saucepan inner walls (no air gaps)
   - Direct contact with flat circular bottom

3. **Free Surface**
   - Top surface is flat and horizontal (air-water interface)
   - Surface level determined by volume and container geometry
   - Surface tension effects (meniscus) neglected for large containers

4. **Incompressibility**
   - Water density assumed constant (ρ ≈ 1000 kg/m³)
   - Volume preservation: V = πr²h
   - No compression under atmospheric pressure

5. **Thermal Properties**
   - Heat capacity: cp ≈ 4186 J/(kg·K)
   - Thermal conductivity: k ≈ 0.6 W/(m·K)
   - Convection currents develop during heating

Implementation:
--------------
- Visual mesh: Closed cylindrical volume for realistic 3D rendering
- Computational grid: Discrete points for physics simulation (SPH, temperature, convection)
- Dual representation allows both visualization and accurate physics
"""

import warp as wp
import numpy as np
from typing import Tuple, Optional
from .base import GeometryComponent
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import LiquidDomainConfig


class LiquidDomain(GeometryComponent):
    """
    Realistic 3D liquid volume for boiling simulation

    Features:
    - Volumetric mesh representation (not just point cloud)
    - Cylindrical water volume with realistic surface
    - Computational grid for physics (SPH particles, temperature, convection)
    - Configuration-driven parameters
    """

    def __init__(
        self,
        name: str,
        config: Optional[LiquidDomainConfig] = None,
        radius: Optional[float] = None,
        height: Optional[float] = None,
        resolution: Optional[Tuple[int, int, int]] = None,
        use_cylindrical_grid: bool = True
    ):
        """
        Create a realistic liquid domain for boiling simulation

        Args:
            name: Component name
            config: LiquidDomainConfig (preferred method)
            radius: Domain radius (m) - should match saucepan inner radius
            height: Liquid height (m)
            resolution: Grid resolution (nr, ntheta, nz) for cylindrical or (nx, ny, nz) for Cartesian
            use_cylindrical_grid: Use cylindrical coordinates (better for round containers)
        """
        super().__init__(name)

        # Use config or individual parameters
        if config is None:
            config = LiquidDomainConfig()

        self.radius = radius if radius is not None else 1.0  # Will be set by assembly
        self.height = height if height is not None else 1.0  # Will be set by assembly
        self.resolution = resolution if resolution is not None else config.resolution
        self.use_cylindrical_grid = use_cylindrical_grid

        # Build both visual mesh and computational grid
        self._build_visual_mesh()
        self._build_computational_grid()

    def _build_visual_mesh(self):
        """
        Build realistic volumetric mesh for water visualization

        Water behavior follows fundamental fluid properties:
        1. Gravity: Water fills from bottom upward
        2. Container conformity: Water takes exact shape of cylindrical chamber
        3. Free surface: Flat horizontal surface at top (no container constraint)
        4. Incompressibility: Uniform density, fills volume completely
        5. No air gaps: Water is in direct contact with chamber walls and bottom

        Creates a cylindrical volume with:
        - Curved side wall (in contact with saucepan inner wall)
        - Flat horizontal top surface (free water surface exposed to air)
        - Flat bottom surface (in contact with saucepan bottom)
        """
        vertices = []
        faces = []

        # Number of segments for smooth cylindrical shape
        num_theta = 48  # Circumferential segments (smooth contact with walls)
        num_radial = 10  # Radial segments for top/bottom surfaces
        num_z = 12      # Vertical segments (for convection visualization)

        # Build cylindrical side wall (water in contact with container)
        # Water perfectly conforms to the cylindrical shape of the saucepan
        for iz in range(num_z + 1):
            z = (iz / num_z) * self.height

            for itheta in range(num_theta):
                theta = (itheta / num_theta) * 2 * np.pi
                # Water extends to full radius - direct contact with saucepan inner wall
                x = self.radius * np.cos(theta)
                y = self.radius * np.sin(theta)
                vertices.append([x, y, z])

        # Build side wall faces (water-container interface)
        # These faces represent the water in contact with the cylindrical chamber wall
        for iz in range(num_z):
            for itheta in range(num_theta):
                next_theta = (itheta + 1) % num_theta

                v0 = iz * num_theta + itheta
                v1 = iz * num_theta + next_theta
                v2 = (iz + 1) * num_theta + next_theta
                v3 = (iz + 1) * num_theta + itheta

                # Inward-facing normals (visible from inside the water volume)
                faces.append([v0, v2, v1])
                faces.append([v0, v3, v2])

        # Build top surface (free water surface exposed to air)
        # This is a flat, horizontal surface due to gravity
        # Surface tension creates a meniscus at edges (not modeled here for simplicity)
        top_start_idx = len(vertices)

        # Center point at water surface
        center_top_idx = len(vertices)
        vertices.append([0.0, 0.0, self.height])

        # Radial rings - water surface extends to full radius
        for ir in range(1, num_radial + 1):
            r = (ir / num_radial) * self.radius

            for itheta in range(num_theta):
                theta = (itheta / num_theta) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                # All points at same height - flat horizontal surface
                vertices.append([x, y, self.height])

        # Top surface faces (upward-facing normals - visible from above)
        # Center to first ring
        for itheta in range(num_theta):
            next_theta = (itheta + 1) % num_theta
            v0 = center_top_idx
            v1 = center_top_idx + 1 + itheta
            v2 = center_top_idx + 1 + next_theta
            faces.append([v0, v2, v1])  # Upward normal

        # Between radial rings
        for ir in range(num_radial - 1):
            for itheta in range(num_theta):
                next_theta = (itheta + 1) % num_theta

                v0 = center_top_idx + 1 + ir * num_theta + itheta
                v1 = center_top_idx + 1 + (ir + 1) * num_theta + itheta
                v2 = center_top_idx + 1 + (ir + 1) * num_theta + next_theta
                v3 = center_top_idx + 1 + ir * num_theta + next_theta

                faces.append([v0, v2, v1])  # Upward normal
                faces.append([v0, v3, v2])

        # Connect outer ring of top surface to top edge of side wall
        # This ensures water volume is closed and conforms to container
        last_ring_idx = center_top_idx + 1 + (num_radial - 1) * num_theta
        top_wall_idx = num_z * num_theta

        for itheta in range(num_theta):
            next_theta = (itheta + 1) % num_theta

            v0 = last_ring_idx + itheta
            v1 = top_wall_idx + itheta
            v2 = top_wall_idx + next_theta
            v3 = last_ring_idx + next_theta

            faces.append([v0, v2, v1])
            faces.append([v0, v3, v2])

        # Build bottom surface (water in direct contact with saucepan bottom)
        # Due to gravity, water settles and makes complete contact with the base
        # No air gaps - water conforms perfectly to the flat circular bottom
        bottom_start_idx = len(vertices)

        # Center point at z=0 (resting on saucepan bottom)
        center_bottom_idx = len(vertices)
        vertices.append([0.0, 0.0, 0.0])

        # Radial rings - water covers entire circular base
        for ir in range(1, num_radial + 1):
            r = (ir / num_radial) * self.radius

            for itheta in range(num_theta):
                theta = (itheta / num_theta) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                # All points at z=0 - flat surface in contact with container bottom
                vertices.append([x, y, 0.0])

        # Bottom surface faces (downward-facing normals - visible from below)
        # Center to first ring
        for itheta in range(num_theta):
            next_theta = (itheta + 1) % num_theta
            v0 = center_bottom_idx
            v1 = center_bottom_idx + 1 + itheta
            v2 = center_bottom_idx + 1 + next_theta
            faces.append([v0, v1, v2])  # Downward normal

        # Between radial rings
        for ir in range(num_radial - 1):
            for itheta in range(num_theta):
                next_theta = (itheta + 1) % num_theta

                v0 = center_bottom_idx + 1 + ir * num_theta + itheta
                v1 = center_bottom_idx + 1 + (ir + 1) * num_theta + itheta
                v2 = center_bottom_idx + 1 + (ir + 1) * num_theta + next_theta
                v3 = center_bottom_idx + 1 + ir * num_theta + next_theta

                faces.append([v0, v1, v2])
                faces.append([v0, v2, v3])

        # Connect outer ring of bottom surface to bottom edge of side wall
        # Ensures water volume is sealed and conforms perfectly to cylindrical chamber
        last_ring_bottom_idx = center_bottom_idx + 1 + (num_radial - 1) * num_theta
        bottom_wall_idx = 0

        for itheta in range(num_theta):
            next_theta = (itheta + 1) % num_theta

            v0 = last_ring_bottom_idx + itheta
            v1 = bottom_wall_idx + itheta
            v2 = bottom_wall_idx + next_theta
            v3 = last_ring_bottom_idx + next_theta

            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

        # Convert to Warp mesh
        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32)

        self.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=wp.array(faces.flatten(), dtype=int)
        )

    def _build_computational_grid(self):
        """Build computational grid for physics simulation"""
        if self.use_cylindrical_grid:
            self._build_cylindrical_grid()
        else:
            self._build_cartesian_grid()

    def _build_cylindrical_grid(self):
        """
        Build cylindrical grid (r, theta, z)

        This is more efficient for round containers as it naturally
        follows the saucepan geometry
        """
        nr, ntheta, nz = self.resolution

        grid_points = []
        grid_indices = []  # Store (ir, itheta, iz) indices

        for iz in range(nz):
            z = (iz / (nz - 1)) * self.height if nz > 1 else self.height / 2

            for ir in range(nr):
                # Radial position (0 at center, radius at edge)
                r = (ir / (nr - 1)) * self.radius if nr > 1 else 0

                # Special case: center point only needs one theta value
                if r < 1e-6:  # Near center
                    x, y = 0.0, 0.0
                    grid_points.append([x, y, z])
                    grid_indices.append([ir, 0, iz])
                else:
                    # Multiple theta values for off-center points
                    for itheta in range(ntheta):
                        theta = (itheta / ntheta) * 2 * np.pi

                        # Convert to Cartesian
                        x = r * np.cos(theta)
                        y = r * np.sin(theta)

                        grid_points.append([x, y, z])
                        grid_indices.append([ir, itheta, iz])

        self.grid_points = wp.array(np.array(grid_points, dtype=np.float32), dtype=wp.vec3)
        self.grid_indices = np.array(grid_indices, dtype=np.int32)
        self.num_points = len(grid_points)
        self._points_array = np.array(grid_points, dtype=np.float32)

        # Store grid type for neighbor computation
        self.grid_type = "cylindrical"
        self.grid_params = {"nr": nr, "ntheta": ntheta, "nz": nz}

    def _build_cartesian_grid(self):
        """
        Build Cartesian grid (x, y, z) within cylindrical boundary

        Traditional approach - generates points on rectangular grid
        but only keeps points inside the cylinder
        """
        nx, ny, nz = self.resolution

        grid_points = []
        grid_indices = []  # Store (i, j, k) indices

        for k in range(nz):
            z = (k / (nz - 1)) * self.height if nz > 1 else self.height / 2

            for i in range(nx):
                for j in range(ny):
                    # Convert to Cartesian coordinates centered at origin
                    x = ((i / (nx - 1)) - 0.5) * 2 * self.radius if nx > 1 else 0
                    y = ((j / (ny - 1)) - 0.5) * 2 * self.radius if ny > 1 else 0

                    # Only include points inside cylinder
                    r = np.sqrt(x**2 + y**2)
                    if r <= self.radius:
                        grid_points.append([x, y, z])
                        grid_indices.append([i, j, k])

        self.grid_points = wp.array(np.array(grid_points, dtype=np.float32), dtype=wp.vec3)
        self.grid_indices = np.array(grid_indices, dtype=np.int32)
        self.num_points = len(grid_points)
        self._points_array = np.array(grid_points, dtype=np.float32)

        # Store grid type for neighbor computation
        self.grid_type = "cartesian"
        self.grid_params = {"nx": nx, "ny": ny, "nz": nz}

    def get_point_at_index(self, i: int, j: int, k: int) -> Optional[np.ndarray]:
        """
        Get the physical position of a grid point

        Args:
            i, j, k: Grid indices

        Returns:
            [x, y, z] position or None if index is out of bounds
        """
        mask = (self.grid_indices[:, 0] == i) & \
               (self.grid_indices[:, 1] == j) & \
               (self.grid_indices[:, 2] == k)

        idx = np.where(mask)[0]
        if len(idx) > 0:
            return self._points_array[idx[0]]
        return None

    def get_neighbors(self, point_idx: int, connectivity: str = "face") -> list:
        """
        Get neighboring grid points for a given point index

        Args:
            point_idx: Index of the point
            connectivity: Type of connectivity ("face" for 6-connected, "edge" for 18-connected, "vertex" for 26-connected)

        Returns:
            List of neighboring point indices
        """
        if point_idx >= self.num_points:
            return []

        i, j, k = self.grid_indices[point_idx]
        neighbors = []

        # Define neighbor offsets based on connectivity
        if connectivity == "face":
            # 6-connected (face neighbors only)
            offsets = [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]
        elif connectivity == "edge":
            # 18-connected (face + edge neighbors)
            offsets = []
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    for dk in [-1, 0, 1]:
                        if (di, dj, dk) != (0, 0, 0) and abs(di) + abs(dj) + abs(dk) <= 2:
                            offsets.append((di, dj, dk))
        else:  # vertex
            # 26-connected (all neighbors)
            offsets = []
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    for dk in [-1, 0, 1]:
                        if (di, dj, dk) != (0, 0, 0):
                            offsets.append((di, dj, dk))

        # Special handling for cylindrical grid (wrap around in theta)
        if self.grid_type == "cylindrical":
            ntheta = self.grid_params["ntheta"]
            for di, dj, dk in offsets:
                ni, nj, nk = i + di, (j + dj) % ntheta, k + dk  # Wrap theta

                mask = (self.grid_indices[:, 0] == ni) & \
                       (self.grid_indices[:, 1] == nj) & \
                       (self.grid_indices[:, 2] == nk)

                idx = np.where(mask)[0]
                if len(idx) > 0:
                    neighbors.append(idx[0])
        else:
            # Cartesian grid (no wrapping)
            for di, dj, dk in offsets:
                ni, nj, nk = i + di, j + dj, k + dk

                mask = (self.grid_indices[:, 0] == ni) & \
                       (self.grid_indices[:, 1] == nj) & \
                       (self.grid_indices[:, 2] == nk)

                idx = np.where(mask)[0]
                if len(idx) > 0:
                    neighbors.append(idx[0])

        return neighbors

    def get_surface_points(self) -> np.ndarray:
        """
        Get indices of points on the liquid surface (top)

        Returns:
            Array of point indices at the top surface
        """
        # Find maximum z coordinate
        max_z = np.max(self._points_array[:, 2])
        tolerance = self.height / (self.grid_params.get("nz", 30) * 2)

        # Points near the top
        surface_mask = self._points_array[:, 2] > (max_z - tolerance)
        return np.where(surface_mask)[0]

    def get_boundary_points(self) -> np.ndarray:
        """
        Get indices of points on the cylindrical boundary (walls)

        Returns:
            Array of point indices at the boundary
        """
        # Calculate radial distance for each point
        r = np.sqrt(self._points_array[:, 0]**2 + self._points_array[:, 1]**2)

        # Points near the wall
        tolerance = self.radius * 0.05  # 5% tolerance
        boundary_mask = r > (self.radius - tolerance)

        return np.where(boundary_mask)[0]

    def get_bottom_points(self) -> np.ndarray:
        """
        Get indices of points on the bottom surface

        Returns:
            Array of point indices at the bottom
        """
        # Find minimum z coordinate
        min_z = np.min(self._points_array[:, 2])
        tolerance = self.height / (self.grid_params.get("nz", 30) * 2)

        # Points near the bottom
        bottom_mask = self._points_array[:, 2] < (min_z + tolerance)
        return np.where(bottom_mask)[0]

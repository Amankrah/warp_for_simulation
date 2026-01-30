"""
Improved food object geometry with realistic shapes
"""

import warp as wp
import numpy as np
from typing import Tuple, Optional
from .base import GeometryComponent
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import FoodItemConfig


class FoodObject(GeometryComponent):
    """
    Realistic food object for simulation

    Supports:
    - Realistic carrot shapes (tapered cylinder)
    - Realistic potato shapes (ellipsoid)
    - Configuration-driven parameters
    - Internal grid for nutrient tracking
    """

    def __init__(
        self,
        name: str,
        food_type: str = "carrot",
        config: Optional[FoodItemConfig] = None,
        dimensions: Optional[Tuple[float, float, float]] = None,
        resolution: Optional[Tuple[int, int, int]] = None,
        position: Tuple[float, float, float] = (0, 0, 0)
    ):
        """
        Create a food object

        Args:
            name: Component name
            food_type: Type of food ("carrot", "potato")
            config: FoodItemConfig (preferred method)
            dimensions: Override dimensions (radius, radius, length) for carrot or (radius, radius, radius) for potato
            resolution: Internal grid resolution (nx, ny, nz) - overrides config if provided
            position: Initial position (x, y, z) - used by assembly system
        """
        super().__init__(name)

        # Use config or defaults
        if config is None:
            config = FoodItemConfig()

        self.food_type = food_type
        self.config = config
        self.position = position

        # Set dimensions based on food type
        if dimensions is not None:
            self.dimensions = dimensions
        else:
            if food_type == "carrot":
                self.dimensions = (config.carrot_radius, config.carrot_radius, config.carrot_length)
            elif food_type == "potato":
                self.dimensions = (config.potato_radius, config.potato_radius, config.potato_radius)
            else:
                raise ValueError(f"Unknown food type: {food_type}")

        # Set resolution
        if resolution is not None:
            self.resolution = resolution
        else:
            self.resolution = config.internal_resolution

        self._build_geometry()

    def _build_geometry(self):
        """Build the food object geometry and internal grid"""
        if self.food_type == "carrot":
            self._build_carrot()
        elif self.food_type == "potato":
            self._build_potato()
        else:
            raise ValueError(f"Unknown food type: {self.food_type}")

    def _build_carrot(self):
        """
        Build realistic carrot piece (tapered cylinder)

        Carrot tapers from full radius at base to smaller radius at top
        """
        radius_base, _, length = self.dimensions
        radius_top = radius_base * 0.6  # Taper to 60% of base radius
        nx, ny, nz = self.resolution

        vertices = []
        faces = []

        num_segments = self.config.circumferential_segments
        num_length_segments = self.config.length_segments

        # Generate vertices along length with tapering
        for i in range(num_length_segments + 1):
            z = (i / num_length_segments) * length
            t = i / num_length_segments  # 0 at base, 1 at top

            # Linear taper from base to top
            radius = radius_base * (1 - t) + radius_top * t

            # Center vertex at this level
            vertices.append([0.0, 0.0, z])

            # Circle vertices at this level
            for j in range(num_segments):
                theta = (j / num_segments) * 2 * np.pi
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                vertices.append([x, y, z])

        verts_per_layer = 1 + num_segments

        # Generate faces
        # Top cap
        for j in range(num_segments):
            next_j = (j + 1) % num_segments
            v0 = num_length_segments * verts_per_layer  # Top center
            v1 = num_length_segments * verts_per_layer + 1 + j
            v2 = num_length_segments * verts_per_layer + 1 + next_j
            faces.append([v0, v1, v2])

        # Bottom cap
        for j in range(num_segments):
            next_j = (j + 1) % num_segments
            v0 = 0  # Bottom center
            v1 = 1 + j
            v2 = 1 + next_j
            faces.append([v0, v2, v1])  # Reversed winding

        # Side faces (tapered)
        for i in range(num_length_segments):
            for j in range(num_segments):
                next_j = (j + 1) % num_segments

                # Current layer
                v0 = i * verts_per_layer + 1 + j
                v1 = i * verts_per_layer + 1 + next_j

                # Next layer
                v2 = (i + 1) * verts_per_layer + 1 + next_j
                v3 = (i + 1) * verts_per_layer + 1 + j

                faces.append([v0, v1, v2])
                faces.append([v0, v2, v3])

        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32)

        self.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=wp.array(faces.flatten(), dtype=int)
        )

        # Build internal grid
        self._build_cylindrical_internal_grid(radius_base, length, nx, ny, nz, taper_ratio=radius_top/radius_base)

    def _build_potato(self):
        """
        Build realistic potato piece (ellipsoid)

        Potato is modeled as a slightly irregular ellipsoid
        """
        radius_x, radius_y, radius_z = self.dimensions
        nx, ny, nz = self.resolution

        vertices = []
        faces = []

        # Use latitude-longitude tessellation for ellipsoid
        num_lat = 16  # Latitude divisions
        num_lon = 24  # Longitude divisions

        # Generate vertices
        for i in range(num_lat + 1):
            theta = (i / num_lat) * np.pi  # 0 to pi (pole to pole)

            for j in range(num_lon):
                phi = (j / num_lon) * 2 * np.pi  # 0 to 2pi (around equator)

                # Ellipsoid parametric equations
                x = radius_x * np.sin(theta) * np.cos(phi)
                y = radius_y * np.sin(theta) * np.sin(phi)
                z = radius_z * np.cos(theta)

                # Add slight irregularity for realism
                noise = 0.05 * np.sin(3 * theta) * np.cos(4 * phi)
                scale = 1 + noise

                vertices.append([x * scale, y * scale, z * scale])

        # Generate faces
        for i in range(num_lat):
            for j in range(num_lon):
                next_j = (j + 1) % num_lon

                v0 = i * num_lon + j
                v1 = i * num_lon + next_j
                v2 = (i + 1) * num_lon + next_j
                v3 = (i + 1) * num_lon + j

                # Skip degenerate triangles at poles
                if i > 0:
                    faces.append([v0, v1, v2])
                if i < num_lat - 1:
                    faces.append([v0, v2, v3])

        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32)

        self.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=wp.array(faces.flatten(), dtype=int)
        )

        # Build internal grid
        self._build_ellipsoidal_internal_grid(radius_x, radius_y, radius_z, nx, ny, nz)

    def _build_cylindrical_internal_grid(
        self,
        radius: float,
        length: float,
        nx: int,
        ny: int,
        nz: int,
        taper_ratio: float = 1.0
    ):
        """
        Build internal computational grid for cylindrical food at origin

        Args:
            radius: Base radius
            length: Length
            nx, ny, nz: Grid resolution
            taper_ratio: Ratio of top radius to base radius (1.0 = no taper)
        """
        grid_points = []
        grid_indices = []

        for k in range(nz):
            z = (k / (nz - 1)) * length if nz > 1 else length / 2
            t = z / length  # Normalized position along length

            # Local radius at this height (accounting for taper)
            local_radius = radius * (1 - t + taper_ratio * t)

            for i in range(nx):
                for j in range(ny):
                    x = ((i / (nx - 1)) - 0.5) * 2 * local_radius if nx > 1 else 0
                    y = ((j / (ny - 1)) - 0.5) * 2 * local_radius if ny > 1 else 0

                    # Only include points inside tapered cylinder
                    r = np.sqrt(x**2 + y**2)
                    if r <= local_radius:
                        grid_points.append([x, y, z])
                        grid_indices.append([i, j, k])

        self.internal_grid_points = wp.array(np.array(grid_points, dtype=np.float32), dtype=wp.vec3)
        self.internal_grid_indices = np.array(grid_indices, dtype=np.int32)
        self.num_internal_points = len(grid_points)
        self._internal_points_array = np.array(grid_points, dtype=np.float32)

    def _build_ellipsoidal_internal_grid(
        self,
        radius_x: float,
        radius_y: float,
        radius_z: float,
        nx: int,
        ny: int,
        nz: int
    ):
        """
        Build internal computational grid for ellipsoidal food at origin

        Args:
            radius_x, radius_y, radius_z: Ellipsoid radii
            nx, ny, nz: Grid resolution
        """
        grid_points = []
        grid_indices = []

        for k in range(nz):
            z = ((k / (nz - 1)) - 0.5) * 2 * radius_z if nz > 1 else 0

            for i in range(nx):
                x = ((i / (nx - 1)) - 0.5) * 2 * radius_x if nx > 1 else 0

                for j in range(ny):
                    y = ((j / (ny - 1)) - 0.5) * 2 * radius_y if ny > 1 else 0

                    # Only include points inside ellipsoid
                    # Ellipsoid equation: (x/rx)^2 + (y/ry)^2 + (z/rz)^2 <= 1
                    dist = (x/radius_x)**2 + (y/radius_y)**2 + (z/radius_z)**2

                    if dist <= 1.0:
                        grid_points.append([x, y, z])
                        grid_indices.append([i, j, k])

        self.internal_grid_points = wp.array(np.array(grid_points, dtype=np.float32), dtype=wp.vec3)
        self.internal_grid_indices = np.array(grid_indices, dtype=np.int32)
        self.num_internal_points = len(grid_points)
        self._internal_points_array = np.array(grid_points, dtype=np.float32)

"""
Realistic food object geometry with physical properties

Physical Properties of Common Foods:
-----------------------------------
**Carrots (Raw)**
- Density: ρ ≈ 1050-1100 kg/m³ (slightly denser than water)
- Water content: ~88%
- Will SINK in water (ρ > 1000 kg/m³)
- Typical cuts: rounds (1-2cm thick), sticks (5-7cm long × 1-2cm diameter), chunks

**Potatoes (Raw)**
- Density: ρ ≈ 1070-1100 kg/m³
- Water content: ~80%
- Will SINK in water
- Typical cuts: chunks (2-3cm cubes), halves, quarters

Cutting Methods:
---------------
- **Rounds/Coins**: Perpendicular cuts to carrot axis (1-2cm thick)
- **Sticks/Batons**: Lengthwise cuts (5-7cm long)
- **Chunks**: Irregular pieces for stews
- **Julienne**: Thin matchsticks (not common for boiling)

Behavior in Boiling Water:
-------------------------
- Fresh vegetables SINK (density > water)
- Rest on pot bottom initially
- May float slightly when cooked (cells break down, air pockets)
- Move with convection currents during boiling
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
    Realistic food object with physical properties for accurate simulation

    Features:
    - Realistic cutting geometries (rounds, sticks, chunks)
    - Physical properties (density, buoyancy)
    - Actual food dimensions from cooking practice
    - Configuration-driven parameters
    - Internal grid for nutrient tracking and heat diffusion
    """

    def __init__(
        self,
        name: str,
        food_type: str = "carrot",
        cut_type: str = "round",
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
            cut_type: Cut style ("round", "stick", "chunk") - only for carrots
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
        self.cut_type = cut_type
        self.config = config
        self.position = position

        # Physical properties
        if food_type == "carrot":
            self.density = 1075.0  # kg/m³ (denser than water - will sink)
        elif food_type == "potato":
            self.density = 1085.0  # kg/m³ (denser than water - will sink)
        else:
            self.density = 1000.0  # Default to water density

        # Set dimensions based on food type and cut
        if dimensions is not None:
            self.dimensions = dimensions
        else:
            if food_type == "carrot":
                # Realistic carrot cut dimensions
                if cut_type == "round":
                    # Coin-shaped: 1-2cm thick rounds
                    self.dimensions = (config.carrot_radius, config.carrot_radius, 0.015)  # 1.5cm thick
                elif cut_type == "stick":
                    # Baton: 5-7cm long sticks
                    self.dimensions = (config.carrot_radius, config.carrot_radius, config.carrot_length)
                elif cut_type == "chunk":
                    # Irregular chunks: ~2-3cm pieces
                    self.dimensions = (0.015, 0.015, 0.025)  # 1.5cm x 1.5cm x 2.5cm
                else:
                    raise ValueError(f"Unknown cut type: {cut_type}")
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
        Build realistic carrot piece based on cut type
        """
        if self.cut_type == "round":
            self._build_carrot_round()
        elif self.cut_type == "stick":
            self._build_carrot_stick()
        elif self.cut_type == "chunk":
            self._build_carrot_chunk()
        else:
            raise ValueError(f"Unknown carrot cut type: {self.cut_type}")

    def _build_carrot_round(self):
        """
        Build carrot round (coin-shaped slice)

        Realistic geometry:
        - Perpendicular cut to carrot axis
        - 1-2cm thick cylinder
        - Minimal taper (slice from same section of carrot)
        """
        radius_base, _, thickness = self.dimensions
        radius_top = radius_base * 0.95  # Very slight taper
        nx, ny, nz = self.resolution

        vertices = []
        faces = []

        num_segments = self.config.circumferential_segments
        num_thickness_segments = 4  # Fewer segments for thin rounds

        # Generate vertices along thickness with minimal tapering
        for i in range(num_thickness_segments + 1):
            z = (i / num_thickness_segments) * thickness
            t = i / num_thickness_segments

            radius = radius_base * (1 - t) + radius_top * t

            # Center vertex
            vertices.append([0.0, 0.0, z])

            # Circle vertices
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
            v0 = num_thickness_segments * verts_per_layer
            v1 = num_thickness_segments * verts_per_layer + 1 + j
            v2 = num_thickness_segments * verts_per_layer + 1 + next_j
            faces.append([v0, v1, v2])

        # Bottom cap
        for j in range(num_segments):
            next_j = (j + 1) % num_segments
            v0 = 0
            v1 = 1 + j
            v2 = 1 + next_j
            faces.append([v0, v2, v1])

        # Side faces
        for i in range(num_thickness_segments):
            for j in range(num_segments):
                next_j = (j + 1) % num_segments

                v0 = i * verts_per_layer + 1 + j
                v1 = i * verts_per_layer + 1 + next_j
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
        self._build_cylindrical_internal_grid(radius_base, thickness, nx, ny, nz, taper_ratio=radius_top/radius_base)

    def _build_carrot_stick(self):
        """
        Build carrot stick (baton cut)

        Realistic geometry:
        - Lengthwise cut: 5-7cm long
        - Tapered from base to top (natural carrot shape)
        - 1-2cm diameter
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

    def _build_carrot_chunk(self):
        """
        Build carrot chunk (irregular piece for stews)

        Realistic geometry:
        - Roughly cuboid with rounded edges
        - 2-3cm irregular pieces
        - Slight asymmetry for natural appearance
        """
        width, depth, height = self.dimensions
        nx, ny, nz = self.resolution

        vertices = []
        faces = []

        # Create rounded box with slight irregularity
        segments_x = 8
        segments_y = 8
        segments_z = 10

        for k in range(segments_z + 1):
            z = ((k / segments_z) - 0.5) * height

            for i in range(segments_x + 1):
                x_norm = (i / segments_x) - 0.5

                for j in range(segments_y + 1):
                    y_norm = (j / segments_y) - 0.5

                    # Round the corners/edges
                    dist_to_edge = max(abs(x_norm), abs(y_norm))
                    rounding_factor = 0.85 if dist_to_edge > 0.4 else 1.0

                    # Add slight irregularity
                    noise = 0.05 * np.sin(3.7 * x_norm) * np.cos(4.3 * y_norm) * np.sin(2.1 * z / height)

                    x = x_norm * width * (rounding_factor + noise)
                    y = y_norm * depth * (rounding_factor + noise)

                    vertices.append([x, y, z])

        # Generate faces (hexahedral mesh converted to triangles)
        verts_per_layer = (segments_x + 1) * (segments_y + 1)

        for k in range(segments_z):
            for i in range(segments_x):
                for j in range(segments_y):
                    # Current layer base index
                    base = k * verts_per_layer + i * (segments_y + 1) + j

                    # Current layer vertices
                    v0 = base
                    v1 = base + 1
                    v2 = base + segments_y + 2
                    v3 = base + segments_y + 1

                    # Next layer vertices
                    v4 = v0 + verts_per_layer
                    v5 = v1 + verts_per_layer
                    v6 = v2 + verts_per_layer
                    v7 = v3 + verts_per_layer

                    # Convert hex to 12 triangles (proper decomposition)
                    faces.extend([
                        [v0, v1, v2], [v0, v2, v3],  # Bottom
                        [v4, v6, v5], [v4, v7, v6],  # Top
                        [v0, v4, v5], [v0, v5, v1],  # Front
                        [v3, v2, v6], [v3, v6, v7],  # Back
                        [v0, v3, v7], [v0, v7, v4],  # Left
                        [v1, v5, v6], [v1, v6, v2],  # Right
                    ])

        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32)

        self.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=wp.array(faces.flatten(), dtype=int)
        )

        # Build internal grid (box-shaped)
        self._build_box_internal_grid(width, depth, height, nx, ny, nz)

    def _build_box_internal_grid(
        self,
        width: float,
        depth: float,
        height: float,
        nx: int,
        ny: int,
        nz: int
    ):
        """
        Build internal computational grid for box-shaped food at origin

        Args:
            width, depth, height: Box dimensions
            nx, ny, nz: Grid resolution
        """
        grid_points = []
        grid_indices = []

        for k in range(nz):
            z = ((k / (nz - 1)) - 0.5) * height if nz > 1 else 0

            for i in range(nx):
                x = ((i / (nx - 1)) - 0.5) * width if nx > 1 else 0

                for j in range(ny):
                    y = ((j / (ny - 1)) - 0.5) * depth if ny > 1 else 0

                    grid_points.append([x, y, z])
                    grid_indices.append([i, j, k])

        self.internal_grid_points = wp.array(np.array(grid_points, dtype=np.float32), dtype=wp.vec3)
        self.internal_grid_indices = np.array(grid_indices, dtype=np.int32)
        self.num_internal_points = len(grid_points)
        self._internal_points_array = np.array(grid_points, dtype=np.float32)

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

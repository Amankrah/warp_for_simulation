"""
Improved cylindrical saucepan component with realistic geometry
"""

import warp as wp
import numpy as np
from .base import GeometryComponent
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import SaucepanGeometryConfig


class CylinderComponent(GeometryComponent):
    """
    Realistic cylindrical saucepan body component

    Features:
    - Inner and outer walls
    - Solid bottom with proper thickness
    - Optional rounded bottom edge (for stability)
    - Smooth mesh generation
    """

    def __init__(
        self,
        name: str,
        config: Optional[SaucepanGeometryConfig] = None,
        radius: Optional[float] = None,
        height: Optional[float] = None,
        wall_thickness: Optional[float] = None,
        bottom_thickness: Optional[float] = None,
        num_segments: Optional[int] = None,
        num_height_segments: Optional[int] = None,
        rounded_bottom: bool = True
    ):
        """
        Create a realistic cylindrical saucepan component

        Args:
            name: Component name
            config: SaucepanGeometryConfig (preferred method)
            radius: Inner radius (m) - overrides config if provided
            height: Height (m) - overrides config if provided
            wall_thickness: Wall thickness (m) - overrides config if provided
            bottom_thickness: Bottom thickness (m) - overrides config if provided
            num_segments: Number of circular segments - overrides config if provided
            num_height_segments: Number of vertical segments - overrides config if provided
            rounded_bottom: Add slight rounding to bottom edge
        """
        super().__init__(name)

        # Use config or individual parameters
        if config is None:
            config = SaucepanGeometryConfig()

        self.radius = radius if radius is not None else config.inner_radius
        self.height = height if height is not None else config.height
        self.wall_thickness = wall_thickness if wall_thickness is not None else config.wall_thickness
        self.bottom_thickness = bottom_thickness if bottom_thickness is not None else config.bottom_thickness
        self.num_segments = num_segments if num_segments is not None else config.num_segments
        self.num_height_segments = num_height_segments if num_height_segments is not None else config.num_height_segments
        self.rounded_bottom = rounded_bottom

        self._build_mesh()

    def _build_mesh(self):
        """Build realistic saucepan mesh with proper bottom"""
        vertices = []
        faces = []

        outer_radius = self.radius + self.wall_thickness

        # Generate vertices for walls (inner and outer)
        for i in range(self.num_height_segments + 1):
            z = (i / self.num_height_segments) * self.height

            for j in range(self.num_segments):
                theta = (j / self.num_segments) * 2 * np.pi

                # Inner wall vertices
                x_inner = self.radius * np.cos(theta)
                y_inner = self.radius * np.sin(theta)
                vertices.append([x_inner, y_inner, z])

                # Outer wall vertices
                x_outer = outer_radius * np.cos(theta)
                y_outer = outer_radius * np.sin(theta)
                vertices.append([x_outer, y_outer, z])

        # Generate wall faces
        for i in range(self.num_height_segments):
            for j in range(self.num_segments):
                next_j = (j + 1) % self.num_segments

                base_idx = i * (self.num_segments * 2)
                top_idx = (i + 1) * (self.num_segments * 2)

                # Inner wall faces (facing inward - correct winding)
                v0 = base_idx + j * 2
                v1 = base_idx + next_j * 2
                v2 = top_idx + next_j * 2
                v3 = top_idx + j * 2

                faces.append([v0, v1, v2])
                faces.append([v0, v2, v3])

                # Outer wall faces (facing outward)
                v0 = base_idx + j * 2 + 1
                v1 = base_idx + next_j * 2 + 1
                v2 = top_idx + next_j * 2 + 1
                v3 = top_idx + j * 2 + 1

                faces.append([v0, v2, v1])
                faces.append([v0, v3, v2])

        # Build bottom geometry
        self._build_bottom(vertices, faces)

        # Convert to numpy arrays
        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32)

        # Create Warp mesh
        self.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=wp.array(faces.flatten(), dtype=int)
        )

    def _build_bottom(self, vertices: list, faces: list):
        """
        Build realistic bottom geometry with proper thickness

        Bottom consists of:
        1. Top surface (inside the pan) - flat
        2. Bottom surface (underneath) - flat or slightly rounded
        3. Side ring connecting inner wall to outer wall
        """
        base_offset = 0  # First ring of vertices
        outer_radius = self.radius + self.wall_thickness

        # Number of radial segments for bottom (more detailed)
        num_bottom_radial = max(5, int(self.radius / 0.01))  # ~1cm spacing

        # Bottom z-levels
        z_top = 0.0  # Inside surface at z=0
        z_bottom = -self.bottom_thickness  # Outside surface below

        # Generate bottom vertices (top surface)
        bottom_start_idx = len(vertices)

        # Center point (top)
        center_top_idx = len(vertices)
        vertices.append([0.0, 0.0, z_top])

        # Radial rings (top surface)
        for ring in range(1, num_bottom_radial + 1):
            r = (ring / num_bottom_radial) * self.radius

            for j in range(self.num_segments):
                theta = (j / self.num_segments) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                vertices.append([x, y, z_top])

        # Generate bottom vertices (bottom surface)
        # Center point (bottom)
        center_bottom_idx = len(vertices)

        if self.rounded_bottom:
            # Slightly rounded center
            vertices.append([0.0, 0.0, z_bottom + self.bottom_thickness * 0.1])
        else:
            vertices.append([0.0, 0.0, z_bottom])

        # Radial rings (bottom surface) extending to outer radius
        for ring in range(1, num_bottom_radial + 2):
            if ring <= num_bottom_radial:
                r = (ring / num_bottom_radial) * self.radius
            else:
                r = outer_radius  # Final ring at outer edge

            for j in range(self.num_segments):
                theta = (j / self.num_segments) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)

                # Slight rounding on bottom surface edge
                if self.rounded_bottom and ring == num_bottom_radial + 1:
                    z = z_bottom + self.bottom_thickness * 0.05
                else:
                    z = z_bottom

                vertices.append([x, y, z])

        # Generate top surface faces (inside the pan)
        # From center to first ring
        for j in range(self.num_segments):
            next_j = (j + 1) % self.num_segments
            v0 = center_top_idx
            v1 = center_top_idx + 1 + j
            v2 = center_top_idx + 1 + next_j
            faces.append([v0, v1, v2])

        # Between rings
        for ring in range(num_bottom_radial - 1):
            for j in range(self.num_segments):
                next_j = (j + 1) % self.num_segments

                v0 = center_top_idx + 1 + ring * self.num_segments + j
                v1 = center_top_idx + 1 + (ring + 1) * self.num_segments + j
                v2 = center_top_idx + 1 + (ring + 1) * self.num_segments + next_j
                v3 = center_top_idx + 1 + ring * self.num_segments + next_j

                faces.append([v0, v1, v2])
                faces.append([v0, v2, v3])

        # Connect top surface outer ring to inner wall base
        last_ring_start = center_top_idx + 1 + (num_bottom_radial - 1) * self.num_segments
        for j in range(self.num_segments):
            next_j = (j + 1) % self.num_segments

            v0 = last_ring_start + j
            v1 = base_offset + j * 2  # Inner wall base
            v2 = base_offset + next_j * 2
            v3 = last_ring_start + next_j

            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

        # Generate bottom surface faces (underneath - reversed winding)
        # From center outward
        for j in range(self.num_segments):
            next_j = (j + 1) % self.num_segments
            v0 = center_bottom_idx
            v1 = center_bottom_idx + 1 + j
            v2 = center_bottom_idx + 1 + next_j
            faces.append([v0, v2, v1])  # Reversed

        # Between rings
        for ring in range(num_bottom_radial):
            for j in range(self.num_segments):
                next_j = (j + 1) % self.num_segments

                v0 = center_bottom_idx + 1 + ring * self.num_segments + j
                v1 = center_bottom_idx + 1 + (ring + 1) * self.num_segments + j
                v2 = center_bottom_idx + 1 + (ring + 1) * self.num_segments + next_j
                v3 = center_bottom_idx + 1 + ring * self.num_segments + next_j

                faces.append([v0, v2, v1])  # Reversed
                faces.append([v0, v3, v2])  # Reversed

        # Connect bottom surface outer ring to outer wall base
        last_ring_start_bottom = center_bottom_idx + 1 + num_bottom_radial * self.num_segments
        for j in range(self.num_segments):
            next_j = (j + 1) % self.num_segments

            v0 = last_ring_start_bottom + j
            v1 = base_offset + j * 2 + 1  # Outer wall base
            v2 = base_offset + next_j * 2 + 1
            v3 = last_ring_start_bottom + next_j

            faces.append([v0, v2, v1])  # Reversed
            faces.append([v0, v3, v2])  # Reversed

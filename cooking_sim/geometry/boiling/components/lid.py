"""
Improved lid component with realistic geometry
"""

import warp as wp
import numpy as np
from .base import GeometryComponent
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import LidGeometryConfig


class LidComponent(GeometryComponent):
    """
    Realistic lid component for cookware

    Features:
    - Domed top surface (more realistic than flat)
    - Central knob/handle
    - Optional steam vent holes
    - Proper thickness modeling
    - Configuration-driven parameters
    """

    def __init__(
        self,
        name: str,
        config: Optional[LidGeometryConfig] = None,
        radius: Optional[float] = None,
        thickness: Optional[float] = None,
        num_segments: Optional[int] = None,
        num_radial_segments: Optional[int] = None,
        has_knob: Optional[bool] = None,
        has_steam_vent: Optional[bool] = None,
        dome_height_ratio: float = 0.15
    ):
        """
        Create a realistic lid component

        Args:
            name: Component name
            config: LidGeometryConfig (preferred method)
            radius: Lid radius (m) - overrides config if provided
            thickness: Lid thickness (m) - overrides config if provided
            num_segments: Number of circular segments - overrides config if provided
            num_radial_segments: Number of radial segments - overrides config if provided
            has_knob: Whether to include knob - overrides config if provided
            has_steam_vent: Whether to include steam vent - overrides config if provided
            dome_height_ratio: Ratio of dome height to radius (0 = flat, 0.15 = realistic)
        """
        super().__init__(name)

        # Use config or individual parameters
        if config is None:
            config = LidGeometryConfig()

        self.radius = radius if radius is not None else config.radius_ratio  # Note: needs saucepan radius
        self.thickness = thickness if thickness is not None else config.thickness
        self.num_segments = num_segments if num_segments is not None else config.num_segments
        self.num_radial_segments = num_radial_segments if num_radial_segments is not None else config.num_radial_segments
        self.has_knob = has_knob if has_knob is not None else config.has_knob
        self.has_steam_vent = has_steam_vent if has_steam_vent is not None else config.has_steam_vent
        self.dome_height_ratio = dome_height_ratio

        # Store config for knob dimensions
        self.knob_radius = config.knob_radius
        self.knob_height = config.knob_height

        self._build_mesh()

    def _build_mesh(self):
        """Build realistic lid mesh with dome and optional knob"""
        vertices = []
        faces = []

        dome_height = self.radius * self.dome_height_ratio

        # Build main lid body (domed)
        self._build_lid_body(vertices, faces, dome_height)

        # Add knob if requested
        if self.has_knob:
            self._build_knob(vertices, faces, dome_height)

        # Convert to numpy arrays
        vertices = np.array(vertices, dtype=np.float32)
        faces = np.array(faces, dtype=np.int32)

        # Create Warp mesh
        self.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=wp.array(faces.flatten(), dtype=int)
        )

    def _build_lid_body(self, vertices: list, faces: list, dome_height: float):
        """
        Build domed lid body

        The lid has:
        1. Top surface - domed (curved upward)
        2. Bottom surface - flat or slightly concave
        3. Outer edge ring
        """
        # Generate top surface (domed) vertices
        top_center_idx = len(vertices)
        vertices.append([0.0, 0.0, dome_height + self.thickness])

        for i in range(1, self.num_radial_segments + 1):
            r = (i / self.num_radial_segments) * self.radius

            # Dome curve: parabolic profile
            # Height decreases quadratically from center to edge
            t = i / self.num_radial_segments  # 0 at center, 1 at edge
            z_dome = dome_height * (1 - t**2) + self.thickness

            for j in range(self.num_segments):
                theta = (j / self.num_segments) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                vertices.append([x, y, z_dome])

        # Generate bottom surface (flat) vertices
        bottom_center_idx = len(vertices)
        vertices.append([0.0, 0.0, 0.0])

        for i in range(1, self.num_radial_segments + 1):
            r = (i / self.num_radial_segments) * self.radius

            for j in range(self.num_segments):
                theta = (j / self.num_segments) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                vertices.append([x, y, 0.0])

        # Generate top surface faces
        for i in range(self.num_radial_segments):
            for j in range(self.num_segments):
                next_j = (j + 1) % self.num_segments

                if i == 0:
                    # Connect to center
                    v0 = top_center_idx
                    v1 = top_center_idx + 1 + j
                    v2 = top_center_idx + 1 + next_j
                    faces.append([v0, v1, v2])
                else:
                    v0 = top_center_idx + 1 + (i - 1) * self.num_segments + j
                    v1 = top_center_idx + 1 + i * self.num_segments + j
                    v2 = top_center_idx + 1 + i * self.num_segments + next_j
                    v3 = top_center_idx + 1 + (i - 1) * self.num_segments + next_j

                    faces.append([v0, v1, v2])
                    faces.append([v0, v2, v3])

        # Generate bottom surface faces (reversed winding)
        for i in range(self.num_radial_segments):
            for j in range(self.num_segments):
                next_j = (j + 1) % self.num_segments

                if i == 0:
                    v0 = bottom_center_idx
                    v1 = bottom_center_idx + 1 + j
                    v2 = bottom_center_idx + 1 + next_j
                    faces.append([v0, v2, v1])  # Reversed
                else:
                    v0 = bottom_center_idx + 1 + (i - 1) * self.num_segments + j
                    v1 = bottom_center_idx + 1 + i * self.num_segments + j
                    v2 = bottom_center_idx + 1 + i * self.num_segments + next_j
                    v3 = bottom_center_idx + 1 + (i - 1) * self.num_segments + next_j

                    faces.append([v0, v2, v1])  # Reversed
                    faces.append([v0, v3, v2])  # Reversed

        # Connect outer edge (side ring)
        for j in range(self.num_segments):
            next_j = (j + 1) % self.num_segments

            # Top edge ring
            v0 = top_center_idx + 1 + (self.num_radial_segments - 1) * self.num_segments + j
            v1 = top_center_idx + 1 + (self.num_radial_segments - 1) * self.num_segments + next_j

            # Bottom edge ring
            v2 = bottom_center_idx + 1 + (self.num_radial_segments - 1) * self.num_segments + next_j
            v3 = bottom_center_idx + 1 + (self.num_radial_segments - 1) * self.num_segments + j

            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    def _build_knob(self, vertices: list, faces: list, dome_height: float):
        """
        Build central knob/handle on top of lid

        Knob is a simple cylinder with rounded top
        """
        knob_base_z = dome_height + self.thickness
        knob_top_z = knob_base_z + self.knob_height

        num_knob_segments = max(16, self.num_segments // 3)

        # Knob base vertices (on lid top surface)
        knob_base_start = len(vertices)

        # Center of knob base
        knob_center_base_idx = len(vertices)
        vertices.append([0.0, 0.0, knob_base_z])

        for j in range(num_knob_segments):
            theta = (j / num_knob_segments) * 2 * np.pi
            x = self.knob_radius * np.cos(theta)
            y = self.knob_radius * np.sin(theta)
            vertices.append([x, y, knob_base_z])

        # Knob top vertices (rounded)
        knob_center_top_idx = len(vertices)
        vertices.append([0.0, 0.0, knob_top_z])

        for j in range(num_knob_segments):
            theta = (j / num_knob_segments) * 2 * np.pi
            # Slightly smaller radius at top for rounded appearance
            r = self.knob_radius * 0.7
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            vertices.append([x, y, knob_top_z])

        # Knob base faces (connecting to lid top)
        for j in range(num_knob_segments):
            next_j = (j + 1) % num_knob_segments

            v0 = knob_center_base_idx
            v1 = knob_center_base_idx + 1 + j
            v2 = knob_center_base_idx + 1 + next_j

            faces.append([v0, v1, v2])

        # Knob top faces
        for j in range(num_knob_segments):
            next_j = (j + 1) % num_knob_segments

            v0 = knob_center_top_idx
            v1 = knob_center_top_idx + 1 + j
            v2 = knob_center_top_idx + 1 + next_j

            faces.append([v0, v2, v1])  # Reversed for outward normal

        # Knob side faces
        for j in range(num_knob_segments):
            next_j = (j + 1) % num_knob_segments

            v0 = knob_center_base_idx + 1 + j
            v1 = knob_center_base_idx + 1 + next_j
            v2 = knob_center_top_idx + 1 + next_j
            v3 = knob_center_top_idx + 1 + j

            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

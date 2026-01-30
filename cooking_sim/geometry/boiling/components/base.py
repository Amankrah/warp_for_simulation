"""
Base geometry component
"""

import warp as wp
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeometryComponent:
    """Base class for geometry components"""
    name: str
    mesh: Optional[wp.Mesh] = None
    transform: wp.mat44 = None

    def __post_init__(self):
        if self.transform is None:
            self.transform = wp.mat44(np.eye(4))

    def get_bounds(self) -> tuple:
        """
        Get the bounding box of the component

        Returns:
            ((min_x, min_y, min_z), (max_x, max_y, max_z))
        """
        if self.mesh is None:
            return ((0, 0, 0), (0, 0, 0))

        points = self.mesh.points.numpy()
        min_bounds = np.min(points, axis=0)
        max_bounds = np.max(points, axis=0)

        return (tuple(min_bounds), tuple(max_bounds))

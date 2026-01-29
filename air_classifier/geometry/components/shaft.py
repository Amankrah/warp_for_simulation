"""
Vertical Shaft Component Builder

Central rotating shaft (SS316)
Based on Section 4.1.5 of corrected_classifier_geometry.md
"""

import pyvista as pv
from ..corrected_config import CorrectedClassifierConfig


def build_vertical_shaft(config: CorrectedClassifierConfig) -> pv.PolyData:
    """Build vertical shaft extending through classifier"""
    shaft_height = config.shaft_top_z - config.shaft_bottom_z

    shaft = pv.Cylinder(
        radius=config.shaft_diameter / 2,
        height=shaft_height,
        center=(0, 0, (config.shaft_top_z + config.shaft_bottom_z) / 2),
        direction=(0, 0, 1),
        resolution=32
    )

    return shaft

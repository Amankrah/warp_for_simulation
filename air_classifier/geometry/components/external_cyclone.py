"""
External Cyclone Component Builder

Stairmand high-efficiency cyclone for fine fraction collection
Based on Section 6.2 of corrected_classifier_geometry.md
"""

import numpy as np
import pyvista as pv
from typing import Tuple
from ..corrected_config import CorrectedClassifierConfig


def build_external_cyclone(config: CorrectedClassifierConfig) -> Tuple[pv.PolyData, pv.PolyData, pv.PolyData]:
    """
    Build external cyclone (Stairmand proportions)

    Returns:
        Tuple of (cylinder, cone, vortex_finder)
    """
    # Horizontal offset from classifier
    x_offset = config.chamber_diameter / 2 + config.cyclone_offset_x

    # Cyclone cylinder
    cyclone_cylinder = pv.Cylinder(
        radius=config.cyclone_body_diameter / 2,
        height=config.cyclone_cylinder_height,
        center=(x_offset, 0, config.chamber_height + config.cyclone_cylinder_height / 2),
        direction=(0, 0, 1),
        resolution=64
    )

    # Cyclone cone
    cyclone_cone = pv.Cone(
        center=(x_offset, 0, config.chamber_height - config.cyclone_cone_height / 2),
        direction=(0, 0, -1),
        height=config.cyclone_cone_height,
        radius=config.cyclone_body_diameter / 2,
        resolution=64
    )

    # Vortex finder (inner cylinder)
    vortex_finder = pv.Cylinder(
        radius=config.cyclone_vortex_finder_diameter / 2,
        height=config.cyclone_vortex_finder_length,
        center=(x_offset, 0, config.chamber_height + config.cyclone_cylinder_height - config.cyclone_vortex_finder_length / 2),
        direction=(0, 0, 1),
        resolution=48
    )

    return cyclone_cylinder, cyclone_cone, vortex_finder


def build_cyclone_inlet(config: CorrectedClassifierConfig) -> pv.PolyData:
    """Build rectangular tangential inlet for cyclone"""
    x_offset = config.chamber_diameter / 2 + config.cyclone_offset_x

    inlet = pv.Box(
        bounds=[
            -config.cyclone_inlet_width / 2,
            config.cyclone_inlet_width / 2,
            0,
            0.2,  # depth
            -config.cyclone_inlet_height / 2,
            config.cyclone_inlet_height / 2
        ]
    )

    # Position at cyclone wall, top of cylinder
    inlet.translate((x_offset, config.cyclone_body_diameter / 2, config.chamber_height + config.cyclone_cylinder_height * 0.8), inplace=True)

    return inlet

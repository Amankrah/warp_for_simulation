"""
Outlet Components Builder

Fines and coarse outlets
Based on Section 4.1 of corrected_classifier_geometry.md
"""

import pyvista as pv
from ..corrected_config import CorrectedClassifierConfig


def build_fines_outlet(config: CorrectedClassifierConfig) -> pv.PolyData:
    """Build fines outlet at chamber top (to external cyclone)"""
    outlet = pv.Cylinder(
        radius=config.fines_outlet_diameter / 2,
        height=0.15,
        center=(0, 0, config.fines_outlet_position_z + 0.075),
        direction=(0, 0, 1),
        resolution=32
    )

    return outlet


def build_coarse_outlet(config: CorrectedClassifierConfig) -> pv.PolyData:
    """Build coarse outlet at cone bottom"""
    outlet = pv.Cylinder(
        radius=config.coarse_outlet_diameter / 2,
        height=0.15,
        center=(0, 0, -config.cone_height - 0.075),
        direction=(0, 0, 1),
        resolution=24
    )

    return outlet

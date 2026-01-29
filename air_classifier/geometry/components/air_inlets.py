"""
Air Distribution System Component Builder

Tangential air inlets with guide vanes
Based on Section 4.1.5 and Section 6.3 of corrected_classifier_geometry.md
"""

import numpy as np
import pyvista as pv
from typing import List
from ..corrected_config import CorrectedClassifierConfig


def build_air_inlets(config: CorrectedClassifierConfig) -> List[pv.PolyData]:
    """Build tangential air inlets (4× at 90° intervals)"""
    inlets = []

    for i in range(config.air_inlet_count):
        angle = 2 * np.pi * i / config.air_inlet_count

        # Inlet position on chamber wall
        r = config.chamber_diameter / 2
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        z = config.air_inlet_position_z

        # Rectangular inlet duct
        inlet = pv.Cylinder(
            radius=config.air_inlet_diameter / 2,
            height=0.3,
            center=(x * 1.15, y * 1.15, z),
            direction=(np.cos(angle), np.sin(angle), 0),
            resolution=32
        )

        inlets.append(inlet)

    return inlets


def build_inlet_guide_vanes(config: CorrectedClassifierConfig) -> List[List[pv.PolyData]]:
    """Build guide vanes for each inlet (6 vanes per inlet at 45°)"""
    all_vanes = []

    for i in range(config.air_inlet_count):
        angle = 2 * np.pi * i / config.air_inlet_count
        inlet_vanes = []

        # 6 vanes per inlet
        for j in range(config.air_inlet_vane_count):
            # Simple rectangular vane
            vane = pv.Box(
                bounds=[
                    -0.001, 0.001,  # 2mm thick
                    0, 0.1,  # 100mm length
                    -0.05, 0.05  # 100mm height
                ]
            )

            # Rotate to 45° angle
            vane.rotate_z(config.air_inlet_vane_angle, inplace=True)

            # Position at inlet
            r = config.chamber_diameter / 2
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            vane.translate((x, y, config.air_inlet_position_z), inplace=True)

            inlet_vanes.append(vane)

        all_vanes.append(inlet_vanes)

    return all_vanes

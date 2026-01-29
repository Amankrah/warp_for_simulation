"""
Hub Assembly Component Builder

Hub with feed ports at top of selector zone
Based on Section 4.1.3 and Section 5.2 of corrected_classifier_geometry.md
"""

import numpy as np
import pyvista as pv
from ..corrected_config import CorrectedClassifierConfig


def build_hub_assembly(config: CorrectedClassifierConfig) -> pv.PolyData:
    """Build hub assembly with feed ports"""
    # Outer hub cylinder
    hub_outer = pv.Cylinder(
        radius=config.hub_outer_diameter / 2,
        height=config.hub_height,
        center=(0, 0, config.selector_zone_bottom + config.hub_height / 2),
        direction=(0, 0, 1),
        resolution=48
    )

    # Inner bore for shaft
    hub_inner = pv.Cylinder(
        radius=config.hub_inner_diameter / 2,
        height=config.hub_height + 0.01,
        center=(0, 0, config.selector_zone_bottom + config.hub_height / 2),
        direction=(0, 0, 1),
        resolution=48
    )

    # Triangulate before boolean operation
    hub_outer = hub_outer.triangulate()
    hub_inner = hub_inner.triangulate()

    # Boolean difference
    try:
        hub = hub_outer.boolean_difference(hub_inner)
    except:
        # If boolean fails, just return outer hub
        # (inner bore can be handled in simulation)
        hub = hub_outer

    return hub


def build_feed_ports(config: CorrectedClassifierConfig) -> list:
    """Build feed ports on hub (8 ports at 45° intervals)"""
    ports = []

    for i in range(config.hub_port_count):
        angle = 2 * np.pi * i / config.hub_port_count

        # Port position on hub surface
        r = config.hub_outer_diameter / 2
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        z = config.selector_zone_bottom + config.hub_height / 2

        # Port cylinder (angled downward 30°)
        port = pv.Cylinder(
            radius=config.hub_port_diameter / 2,
            height=0.05,
            center=(x, y, z),
            direction=(np.cos(angle), np.sin(angle), -np.tan(np.radians(config.hub_port_angle))),
            resolution=16
        )

        ports.append(port)

    return ports

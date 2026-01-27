"""
AgriDrift - GPU-Accelerated Agricultural Spray Drift Simulation

A Warp-based simulator for modeling pesticide and fertilizer spray drift,
including droplet dynamics, wind effects, and deposition patterns.
"""

__version__ = "0.1.0"

from .config import SprayConfig, WindConfig, SimulationConfig
from .physics import DropletSimulator

__all__ = [
    "SprayConfig",
    "WindConfig",
    "SimulationConfig",
    "DropletSimulator",
]

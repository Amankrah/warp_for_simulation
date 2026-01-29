"""
Air Classifier Simulation Package

GPU-accelerated particle simulation for yellow pea protein separation
using NVIDIA Warp.

Based on comprehensive engineering design guide for turbine-type air classifiers.
"""


try:
    from .classifier_simulator import AirClassifierSimulator, SimulationConfig
except (ImportError, ModuleNotFoundError) as e:
    # Fallback if classifier_simulator doesn't exist or dependencies missing
    print(f"Warning: Could not import AirClassifierSimulator: {e}")
    AirClassifierSimulator = None
    SimulationConfig = None


__version__ = "1.0.0"

__all__ = [
    # Simulator
    'AirClassifierSimulator',
    'SimulationConfig',
]

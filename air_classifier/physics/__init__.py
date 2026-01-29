"""
Physics Modeling for Air Classifier Simulation

This package contains physics models for:
- Particle dynamics (forces, motion)
- Air flow field
- Collision detection
- Separation mechanisms
"""

from .particle_dynamics import (
    compute_particle_forces,
    update_particle_motion
)
from .air_flow import (
    AirFlowModel
)
from .collisions import (
    handle_collisions,
    apply_boundaries_and_collection,
    check_particle_status
)

__all__ = [
    'compute_particle_forces',
    'update_particle_motion',
    'AirFlowModel',
    'handle_collisions',
    'apply_boundaries_and_collection',
    'check_particle_status'
]

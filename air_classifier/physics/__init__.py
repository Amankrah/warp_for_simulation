"""
Physics Modeling for Air Classifier Simulation

DESIGN PHILOSOPHY:
==================
This package separates FUNDAMENTAL PHYSICS from TUNABLE PARAMETERS:

1. PHYSICS MODULES (air_flow, particle_dynamics, collisions):
   - Contain ONLY fundamental equations (Stokes drag, continuity, etc.)
   - NO magic numbers or empirical tuning
   - Same code works for any classifier geometry or operating conditions

2. CONTROL PARAMETERS MODULE:
   - Defines machine geometry (fixed dimensions)
   - Defines operating conditions (RPM, air flow - operator adjustable)
   - Defines physical constants (air viscosity, gravity - universal)
   - Provides theoretical predictions (d50, velocities)

3. USAGE:
   ```python
   from air_classifier.physics import (
       AirFlowModel,
       compute_particle_forces,
       AirClassifierConfig,
       create_default_config
   )

   # Create configuration (geometry + operating conditions)
   config = create_default_config()
   config.print_summary()  # Shows theoretical predictions

   # Use in simulation
   boundary_conditions = config.to_dict()
   air_model = AirFlowModel(boundary_conditions)
   ```
"""

# Physics modules (fundamental equations)
from .particle_dynamics import (
    compute_particle_forces,
    update_particle_motion,
    compute_theoretical_d50,
    analyze_force_balance
)
from .air_flow import (
    AirFlowModel
)
from .collisions import (
    handle_collisions,
    apply_boundaries_and_collection,
    check_particle_status
)

# Control parameters (system configuration)
from .control_parameters import (
    PhysicalConstants,
    OperatingConditions,
    ClassifierGeometry,
    MaterialProperties,
    AirClassifierConfig,
    OperatingPointCalculator,
    create_default_config,
    create_lab_scale_config
)

__all__ = [
    # Physics (fundamental equations)
    'compute_particle_forces',
    'update_particle_motion',
    'compute_theoretical_d50',
    'analyze_force_balance',
    'AirFlowModel',
    'handle_collisions',
    'apply_boundaries_and_collection',
    'check_particle_status',

    # Control parameters (configuration)
    'PhysicalConstants',
    'OperatingConditions',
    'ClassifierGeometry',
    'MaterialProperties',
    'AirClassifierConfig',
    'OperatingPointCalculator',
    'create_default_config',
    'create_lab_scale_config'
]

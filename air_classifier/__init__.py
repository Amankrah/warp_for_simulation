"""
Air Classifier Simulation Package

GPU-accelerated particle simulation for yellow pea protein separation
using NVIDIA Warp.

Based on comprehensive engineering design guide for turbine-type air classifiers.
"""

from .config import (
    ClassifierConfig,
    ParticleProperties,
    SimulationConfig,
    ProcessParameters,
    get_default_config,
    get_high_purity_config,
    get_high_yield_config,
    get_pilot_scale_config
)

# Import from new classifier_simulator module
# Note: This import may fail if warp is not available, so we make it optional
try:
    from .classifier_simulator import AirClassifierSimulator
    # Note: SimulationConfig is already imported from .config above
    # For the new simulator's SimulationConfig, import directly:
    # from air_classifier.classifier_simulator import SimulationConfig
except (ImportError, ModuleNotFoundError):
    # Fallback if classifier_simulator doesn't exist or dependencies missing
    AirClassifierSimulator = None

from .analysis import (
    analyze_separation,
    print_separation_report,
    plot_particle_trajectories,
    plot_size_distributions,
    plot_collection_dynamics,
    calculate_grade_efficiency,
    plot_grade_efficiency_curve,
    print_grade_efficiency_report,
    calculate_economics,
    print_economics_report
)

from .validation import (
    validate_classifier_design,
    print_validation_report,
    calculate_theoretical_cut_size,
    calculate_terminal_velocity,
    calculate_mass_balance
)

__version__ = "1.0.0"

__all__ = [
    # Configuration
    'ClassifierConfig',
    'ParticleProperties',
    'SimulationConfig',
    'ProcessParameters',
    'get_default_config',
    'get_high_purity_config',
    'get_high_yield_config',
    'get_pilot_scale_config',

    # Simulator
    'AirClassifierSimulator',

    # Analysis
    'analyze_separation',
    'print_separation_report',
    'plot_particle_trajectories',
    'plot_size_distributions',
    'plot_collection_dynamics',
    'calculate_grade_efficiency',
    'plot_grade_efficiency_curve',
    'print_grade_efficiency_report',
    'calculate_economics',
    'print_economics_report',

    # Validation
    'validate_classifier_design',
    'print_validation_report',
    'calculate_theoretical_cut_size',
    'calculate_terminal_velocity',
    'calculate_mass_balance',
]

"""
Air Classifier Geometry Module

Modular construction system for Cyclone Air Classifier geometry
based on corrected specifications from corrected_classifier_geometry.md

This module provides systematic, component-based geometry construction
following the Humboldt Wedag / Sturtevant Superfine cyclone classifier design.
"""

from .corrected_config import CorrectedClassifierConfig
from .assembly import build_complete_classifier, GeometryAssembly

__all__ = [
    'CorrectedClassifierConfig',
    'build_complete_classifier',
    'GeometryAssembly'
]

__version__ = '1.0.0'

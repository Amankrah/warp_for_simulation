"""
Particle Properties for Air Classifier Simulation

Defines material properties for protein and starch particles
used in yellow pea flour separation.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class ParticleProperties:
    """Base particle properties"""
    density: float  # kg/m³
    diameter_mean: float  # m (mean diameter)
    diameter_std: float  # m (standard deviation)
    diameter_min: float  # m (minimum diameter)
    diameter_max: float  # m (maximum diameter)
    shape_factor: float = 1.0  # Sphericity (1.0 = perfect sphere)
    surface_roughness: float = 0.0  # Surface roughness factor
    charge: float = 0.0  # Electrical charge (C)
    moisture_content: float = 0.10  # Fraction (10% default)
    
    def sample_diameter(self, n: int = 1, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """
        Sample particle diameters from distribution
        
        Args:
            n: Number of samples
            rng: Random number generator (optional)
            
        Returns:
            Array of diameters in meters
        """
        if rng is None:
            rng = np.random.default_rng()
        
        # Use truncated normal distribution
        diameters = []
        for _ in range(n):
            while True:
                d = rng.normal(self.diameter_mean, self.diameter_std)
                if self.diameter_min <= d <= self.diameter_max:
                    diameters.append(d)
                    break
        return np.array(diameters)
    
    def volume(self, diameter: float) -> float:
        """Calculate particle volume"""
        return (4.0 / 3.0) * np.pi * (diameter / 2.0) ** 3
    
    def mass(self, diameter: float) -> float:
        """Calculate particle mass"""
        vol = self.volume(diameter)
        # Account for moisture content (assume water density = 1000 kg/m³)
        dry_mass = self.density * vol * (1.0 - self.moisture_content)
        water_mass = 1000.0 * vol * self.moisture_content
        return dry_mass + water_mass
    
    def effective_density(self) -> float:
        """Calculate effective density accounting for moisture"""
        return self.density * (1.0 - self.moisture_content) + 1000.0 * self.moisture_content


# =============================================================================
# Yellow Pea Material Properties
# =============================================================================

# Protein particle properties (fine fraction)
PROTEIN_PROPERTIES = ParticleProperties(
    density=1350.0,  # kg/m³ (dry protein density)
    diameter_mean=10e-6,  # 10 μm mean
    diameter_std=5e-6,  # 5 μm std
    diameter_min=2e-6,  # 2 μm min
    diameter_max=20e-6,  # 20 μm max
    shape_factor=0.85,  # Slightly irregular
    moisture_content=0.10  # 10% moisture
)

# Starch particle properties (coarse fraction)
STARCH_PROPERTIES = ParticleProperties(
    density=1520.0,  # kg/m³ (dry starch density)
    diameter_mean=30e-6,  # 30 μm mean
    diameter_std=10e-6,  # 10 μm std
    diameter_min=15e-6,  # 15 μm min
    diameter_max=60e-6,  # 60 μm max
    shape_factor=0.75,  # More irregular (granular)
    moisture_content=0.10  # 10% moisture
)

# Mixed feed properties (typical yellow pea flour)
FEED_PROPERTIES = ParticleProperties(
    density=1450.0,  # kg/m³ (average)
    diameter_mean=20e-6,  # 20 μm mean
    diameter_std=12e-6,  # 12 μm std
    diameter_min=2e-6,  # 2 μm min
    diameter_max=60e-6,  # 60 μm max
    shape_factor=0.80,  # Mixed shapes
    moisture_content=0.10  # 10% moisture
)


# =============================================================================
# Air Properties
# =============================================================================

@dataclass
class AirProperties:
    """Air properties for simulation"""
    density: float = 1.2  # kg/m³ at 20°C, 1 atm
    viscosity: float = 1.81e-5  # Pa·s at 20°C
    temperature: float = 293.15  # K (20°C)
    pressure: float = 101325.0  # Pa (1 atm)
    humidity: float = 0.5  # Relative humidity (0-1)
    
    def reynolds_number(self, velocity: float, diameter: float) -> float:
        """Calculate Reynolds number for particle"""
        return self.density * velocity * diameter / self.viscosity


# Standard air at 20°C
STANDARD_AIR = AirProperties()


# =============================================================================
# Feed Composition
# =============================================================================

@dataclass
class FeedComposition:
    """Feed material composition"""
    protein_fraction: float = 0.23  # 23% protein by mass
    starch_fraction: float = 0.48  # 48% starch by mass
    fiber_fraction: float = 0.15  # 15% fiber
    other_fraction: float = 0.14  # 14% other (ash, lipids, etc.)
    moisture_content: float = 0.10  # 10% moisture
    
    def validate(self):
        """Validate that fractions sum to 1.0"""
        total = (self.protein_fraction + self.starch_fraction + 
                self.fiber_fraction + self.other_fraction)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Feed fractions sum to {total:.3f}, should be 1.0")


# Typical yellow pea flour composition
YELLOW_PEA_FLOUR = FeedComposition(
    protein_fraction=0.23,
    starch_fraction=0.48,
    fiber_fraction=0.15,
    other_fraction=0.14,
    moisture_content=0.10
)


# =============================================================================
# Target Separation Specifications
# =============================================================================

@dataclass
class SeparationTargets:
    """Target separation specifications"""
    cut_size_d50: float = 20e-6  # 20 μm cut size
    fine_fraction_protein: float = 0.58  # 58% protein in fine fraction
    coarse_fraction_starch: float = 0.85  # 85% starch in coarse fraction
    protein_recovery: float = 0.50  # 50% protein recovery target
    sharpness_index: float = 0.6  # Separation sharpness (lower is better)


# Standard targets for yellow pea separation
STANDARD_TARGETS = SeparationTargets()


# =============================================================================
# Helper Functions
# =============================================================================

def create_particle_mixture(
    n_particles: int,
    feed_composition: FeedComposition = YELLOW_PEA_FLOUR,
    protein_props: ParticleProperties = PROTEIN_PROPERTIES,
    starch_props: ParticleProperties = STARCH_PROPERTIES,
    rng: Optional[np.random.Generator] = None
) -> tuple:
    """
    Create a particle mixture based on feed composition
    
    Args:
        n_particles: Total number of particles
        feed_composition: Feed composition
        protein_props: Protein particle properties
        starch_props: Starch particle properties
        rng: Random number generator
        
    Returns:
        Tuple of (diameters, densities, types)
        where types: 0 = protein, 1 = starch
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Calculate number of each type
    n_protein = int(n_particles * feed_composition.protein_fraction)
    n_starch = n_particles - n_protein
    
    # Sample diameters
    protein_diameters = protein_props.sample_diameter(n_protein, rng)
    starch_diameters = starch_props.sample_diameter(n_starch, rng)
    
    # Combine
    diameters = np.concatenate([protein_diameters, starch_diameters])
    
    # Calculate densities (accounting for moisture)
    protein_densities = np.full(n_protein, protein_props.effective_density())
    starch_densities = np.full(n_starch, starch_props.effective_density())
    densities = np.concatenate([protein_densities, starch_densities])
    
    # Create type array (0 = protein, 1 = starch)
    types = np.concatenate([
        np.zeros(n_protein, dtype=int),
        np.ones(n_starch, dtype=int)
    ])
    
    # Shuffle to randomize order
    indices = rng.permutation(n_particles)
    diameters = diameters[indices]
    densities = densities[indices]
    types = types[indices]
    
    return diameters, densities, types


if __name__ == "__main__":
    """Test particle properties"""
    print("=" * 70)
    print("PARTICLE PROPERTIES TEST")
    print("=" * 70)
    
    print("\n📊 Protein Properties:")
    print(f"  Density: {PROTEIN_PROPERTIES.density} kg/m³")
    print(f"  Diameter: {PROTEIN_PROPERTIES.diameter_mean*1e6:.1f} ± {PROTEIN_PROPERTIES.diameter_std*1e6:.1f} μm")
    print(f"  Range: {PROTEIN_PROPERTIES.diameter_min*1e6:.1f} - {PROTEIN_PROPERTIES.diameter_max*1e6:.1f} μm")
    
    print("\n📊 Starch Properties:")
    print(f"  Density: {STARCH_PROPERTIES.density} kg/m³")
    print(f"  Diameter: {STARCH_PROPERTIES.diameter_mean*1e6:.1f} ± {STARCH_PROPERTIES.diameter_std*1e6:.1f} μm")
    print(f"  Range: {STARCH_PROPERTIES.diameter_min*1e6:.1f} - {STARCH_PROPERTIES.diameter_max*1e6:.1f} μm")
    
    print("\n📊 Feed Composition:")
    print(f"  Protein: {YELLOW_PEA_FLOUR.protein_fraction*100:.0f}%")
    print(f"  Starch: {YELLOW_PEA_FLOUR.starch_fraction*100:.0f}%")
    print(f"  Fiber: {YELLOW_PEA_FLOUR.fiber_fraction*100:.0f}%")
    print(f"  Other: {YELLOW_PEA_FLOUR.other_fraction*100:.0f}%")
    
    print("\n🧪 Creating particle mixture (1000 particles)...")
    diameters, densities, types = create_particle_mixture(1000)
    
    protein_mask = types == 0
    starch_mask = types == 1
    
    print(f"\n✓ Created {len(diameters)} particles:")
    print(f"  Protein: {np.sum(protein_mask)} particles")
    print(f"    Mean diameter: {np.mean(diameters[protein_mask])*1e6:.2f} μm")
    print(f"    Mean density: {np.mean(densities[protein_mask]):.0f} kg/m³")
    print(f"  Starch: {np.sum(starch_mask)} particles")
    print(f"    Mean diameter: {np.mean(diameters[starch_mask])*1e6:.2f} μm")
    print(f"    Mean density: {np.mean(densities[starch_mask]):.0f} kg/m³")
    
    print("\n" + "=" * 70)
    print("✓ Particle properties test complete")
    print("=" * 70)

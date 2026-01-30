"""
Configuration module for boiling process geometry
Centralized control of all dimensional and physical parameters
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class SaucepanGeometryConfig:
    """Geometry parameters for saucepan"""

    # Main dimensions
    inner_radius: float = 0.10          # Inner radius (m) - 10 cm
    height: float = 0.15                # Total height (m) - 15 cm
    wall_thickness: float = 0.003       # Wall thickness (m) - 3 mm
    bottom_thickness: float = 0.005     # Bottom thickness (m) - 5 mm

    # Mesh resolution
    num_segments: int = 48              # Circular segments (higher = smoother)
    num_height_segments: int = 30       # Vertical segments

    # Material
    material: str = "stainless_steel"

    @property
    def outer_radius(self) -> float:
        """Calculate outer radius"""
        return self.inner_radius + self.wall_thickness

    @property
    def volume_liters(self) -> float:
        """Calculate inner volume in liters"""
        import math
        volume_m3 = math.pi * self.inner_radius**2 * self.height
        return volume_m3 * 1000  # Convert to liters


@dataclass
class LidGeometryConfig:
    """Geometry parameters for lid"""

    # Dimensions
    radius_ratio: float = 1.05          # Ratio to saucepan outer radius
    thickness: float = 0.005            # Lid thickness (m) - 5 mm
    knob_radius: float = 0.015          # Knob radius (m) - 1.5 cm
    knob_height: float = 0.02           # Knob height (m) - 2 cm

    # Mesh resolution
    num_segments: int = 48
    num_radial_segments: int = 15

    # Features
    has_knob: bool = True
    has_steam_vent: bool = False


@dataclass
class LiquidDomainConfig:
    """Liquid domain computational grid"""

    # Dimensions (relative to saucepan)
    radius_ratio: float = 0.98          # Slightly smaller than inner radius
    fill_level: float = 0.67            # Fraction of height (0-1)

    # Grid resolution
    resolution: Tuple[int, int, int] = (40, 40, 40)

    # Liquid properties
    liquid_type: str = "water"


@dataclass
class FoodItemConfig:
    """Configuration for food items (carrots, potatoes, etc.)"""

    # Carrot dimensions
    carrot_radius: float = 0.015        # 1.5 cm radius
    carrot_length: float = 0.05         # 5 cm length

    # Potato dimensions
    potato_radius: float = 0.03         # 3 cm radius (spherical)

    # Mesh resolution
    circumferential_segments: int = 24
    length_segments: int = 20

    # Internal grid for nutrient tracking
    internal_resolution: Tuple[int, int, int] = (12, 12, 18)


@dataclass
class AssemblyConfig:
    """Assembly and positioning configuration"""

    # Clearances and offsets (in meters)
    water_bottom_clearance: float = 0.001       # Gap between water and saucepan bottom
    food_wall_margin_ratio: float = 0.6         # Food placement radius as ratio of saucepan radius
    food_spacing_multiplier: float = 2.5        # Spacing between food pieces (multiple of food radius)

    # Lid positioning
    lid_at_top: bool = True                     # Position lid at top of saucepan to cover opening


@dataclass
class BoilingConfig:
    """Complete boiling process configuration"""

    # Geometry configs
    saucepan: SaucepanGeometryConfig = None
    lid: LidGeometryConfig = None
    liquid: LiquidDomainConfig = None
    food: FoodItemConfig = None
    assembly: AssemblyConfig = None

    # Scene settings
    num_food_pieces: int = 3
    food_type: str = "carrot"           # "carrot", "potato", etc.
    with_lid: bool = True

    def __post_init__(self):
        """Initialize sub-configs if not provided"""
        if self.saucepan is None:
            self.saucepan = SaucepanGeometryConfig()
        if self.lid is None:
            self.lid = LidGeometryConfig()
        if self.liquid is None:
            self.liquid = LiquidDomainConfig()
        if self.food is None:
            self.food = FoodItemConfig()
        if self.assembly is None:
            self.assembly = AssemblyConfig()

    def get_water_level(self) -> float:
        """Calculate actual water level in meters"""
        return self.saucepan.height * self.liquid.fill_level

    def get_lid_radius(self) -> float:
        """Calculate lid radius"""
        return self.saucepan.outer_radius * self.lid.radius_ratio

    def get_water_bottom_position(self) -> float:
        """Calculate z position of water bottom surface"""
        return self.saucepan.bottom_thickness + self.assembly.water_bottom_clearance

    def get_lid_position(self) -> float:
        """Calculate z position of lid bottom surface"""
        # Lid should sit on top of the saucepan to cover the opening
        # The saucepan goes from z=0 (bottom) to z=height (top rim)
        # The lid sits on the rim, so its bottom surface is at the saucepan height
        return self.saucepan.height

    def summary(self) -> str:
        """Get configuration summary"""
        return f"""
Boiling Configuration
=====================
Saucepan:
  - Inner radius: {self.saucepan.inner_radius*100:.1f} cm
  - Height: {self.saucepan.height*100:.1f} cm
  - Volume: {self.saucepan.volume_liters:.2f} L
  - Wall thickness: {self.saucepan.wall_thickness*1000:.1f} mm
  - Bottom thickness: {self.saucepan.bottom_thickness*1000:.1f} mm

Liquid:
  - Type: {self.liquid.liquid_type}
  - Fill level: {self.liquid.fill_level*100:.0f}%
  - Water height: {self.get_water_level()*100:.1f} cm
  - Water bottom z: {self.get_water_bottom_position()*100:.2f} cm

Food:
  - Type: {self.food_type}
  - Number of pieces: {self.num_food_pieces}
  - Piece dimensions: {self._get_food_dimensions()}

Lid:
  - Included: {self.with_lid}
  - Radius: {self.get_lid_radius()*100:.1f} cm
  - Has knob: {self.lid.has_knob}
  - Position z: {self.get_lid_position()*100:.1f} cm

Assembly:
  - Water clearance: {self.assembly.water_bottom_clearance*1000:.1f} mm
  - Food wall margin: {self.assembly.food_wall_margin_ratio*100:.0f}% of radius
  - Food spacing: {self.assembly.food_spacing_multiplier:.1f}x food radius
  - Lid at top: {self.assembly.lid_at_top}
"""

    def _get_food_dimensions(self) -> str:
        """Get food dimensions string"""
        if self.food_type == "carrot":
            return f"r={self.food.carrot_radius*100:.1f}cm, L={self.food.carrot_length*100:.1f}cm"
        elif self.food_type == "potato":
            return f"r={self.food.potato_radius*100:.1f}cm (spherical)"
        return "unknown"


# Predefined boiling configurations
def create_small_saucepan_config() -> BoilingConfig:
    """Create a small saucepan configuration (1L)"""
    return BoilingConfig(
        saucepan=SaucepanGeometryConfig(
            inner_radius=0.08,      # 8 cm
            height=0.12,            # 12 cm
            wall_thickness=0.002
        ),
        num_food_pieces=2,
        food_type="carrot"
    )


def create_standard_saucepan_config() -> BoilingConfig:
    """Create a standard saucepan configuration (2L)"""
    return BoilingConfig(
        saucepan=SaucepanGeometryConfig(
            inner_radius=0.10,      # 10 cm
            height=0.15,            # 15 cm
            wall_thickness=0.003
        ),
        num_food_pieces=3,
        food_type="carrot"
    )


def create_large_pot_config() -> BoilingConfig:
    """Create a large pot configuration (5L)"""
    return BoilingConfig(
        saucepan=SaucepanGeometryConfig(
            inner_radius=0.13,      # 13 cm
            height=0.20,            # 20 cm
            wall_thickness=0.004
        ),
        liquid=LiquidDomainConfig(
            fill_level=0.75
        ),
        num_food_pieces=5,
        food_type="carrot"
    )


def create_potato_boiling_config() -> BoilingConfig:
    """Create configuration for boiling potatoes"""
    return BoilingConfig(
        saucepan=SaucepanGeometryConfig(
            inner_radius=0.12,
            height=0.18
        ),
        liquid=LiquidDomainConfig(
            fill_level=0.70
        ),
        num_food_pieces=4,
        food_type="potato"
    )

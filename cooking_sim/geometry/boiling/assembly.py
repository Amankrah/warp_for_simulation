"""
Improved assembly system for boiling geometry components
"""

import warp as wp
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .components import CylinderComponent, LidComponent, LiquidDomain, FoodObject
from .components.base import GeometryComponent
from .config import BoilingConfig, SaucepanGeometryConfig


@dataclass
class BoilingAssembly:
    """
    Assembly of components for boiling simulation

    Manages component positioning, transformations, and spatial relationships
    """

    name: str
    components: Dict[str, GeometryComponent] = field(default_factory=dict)
    config: Optional[BoilingConfig] = None

    def add_component(
        self,
        component: GeometryComponent,
        position: tuple = (0, 0, 0),
        rotation: tuple = (0, 0, 0)
    ):
        """
        Add a component to the assembly and apply transformation

        Args:
            component: Geometry component to add
            position: (x, y, z) position offset
            rotation: (rx, ry, rz) rotation in radians
        """
        # Store the transformation matrix
        transform = self._create_transform(position, rotation)
        component.transform = transform
        component.position = position
        component.rotation = rotation

        # Apply transformation to mesh vertices if needed
        if (position != (0, 0, 0) or rotation != (0, 0, 0)) and component.mesh is not None:
            self._apply_transform_to_mesh(component, position, rotation)

        # Apply transformation to grid points if they exist
        if (position != (0, 0, 0) or rotation != (0, 0, 0)):
            if hasattr(component, 'grid_points'):
                self._apply_transform_to_points(component, 'grid_points', position, rotation)
            if hasattr(component, 'internal_grid_points'):
                self._apply_transform_to_points(component, 'internal_grid_points', position, rotation)

        self.components[component.name] = component

    def _apply_transform_to_mesh(self, component: GeometryComponent, position: tuple, rotation: tuple):
        """Apply transformation to mesh vertices"""
        if component.mesh is None:
            return

        # Get current vertices
        vertices = component.mesh.points.numpy()

        # Apply rotation (if any)
        if rotation != (0, 0, 0):
            vertices = self._rotate_points(vertices, rotation)

        # Apply translation
        vertices[:, 0] += position[0]
        vertices[:, 1] += position[1]
        vertices[:, 2] += position[2]

        # Update mesh with transformed vertices
        component.mesh = wp.Mesh(
            points=wp.array(vertices, dtype=wp.vec3),
            indices=component.mesh.indices
        )

    def _apply_transform_to_points(self, component: GeometryComponent, attr_name: str, position: tuple, rotation: tuple):
        """Apply transformation to point arrays (grid points, internal grids)"""
        if not hasattr(component, attr_name):
            return

        points_array = getattr(component, attr_name)
        if points_array is None:
            return

        # Get current points
        points = points_array.numpy()

        # Apply rotation
        if rotation != (0, 0, 0):
            points = self._rotate_points(points, rotation)

        # Apply translation
        points[:, 0] += position[0]
        points[:, 1] += position[1]
        points[:, 2] += position[2]

        # Update the array
        setattr(component, attr_name, wp.array(points, dtype=wp.vec3))

        # Also update numpy cache if it exists
        cache_name = f'_{attr_name.replace("_points", "_points_array")}'
        if hasattr(component, cache_name):
            setattr(component, cache_name, points)

    def _rotate_points(self, points: np.ndarray, rotation: tuple) -> np.ndarray:
        """Rotate points around origin"""
        rx, ry, rz = rotation

        # Rotation around X
        if rx != 0:
            cos_x, sin_x = np.cos(rx), np.sin(rx)
            Rx = np.array([
                [1, 0, 0],
                [0, cos_x, -sin_x],
                [0, sin_x, cos_x]
            ])
            points = points @ Rx.T

        # Rotation around Y
        if ry != 0:
            cos_y, sin_y = np.cos(ry), np.sin(ry)
            Ry = np.array([
                [cos_y, 0, sin_y],
                [0, 1, 0],
                [-sin_y, 0, cos_y]
            ])
            points = points @ Ry.T

        # Rotation around Z
        if rz != 0:
            cos_z, sin_z = np.cos(rz), np.sin(rz)
            Rz = np.array([
                [cos_z, -sin_z, 0],
                [sin_z, cos_z, 0],
                [0, 0, 1]
            ])
            points = points @ Rz.T

        return points

    def _create_transform(self, position: tuple, rotation: tuple) -> wp.mat44:
        """Create a transformation matrix from position and rotation"""
        px, py, pz = position
        rx, ry, rz = rotation

        # Create rotation matrices
        cos_x, sin_x = np.cos(rx), np.sin(rx)
        cos_y, sin_y = np.cos(ry), np.sin(ry)
        cos_z, sin_z = np.cos(rz), np.sin(rz)

        # Rotation around X
        Rx = np.array([
            [1, 0, 0, 0],
            [0, cos_x, -sin_x, 0],
            [0, sin_x, cos_x, 0],
            [0, 0, 0, 1]
        ])

        # Rotation around Y
        Ry = np.array([
            [cos_y, 0, sin_y, 0],
            [0, 1, 0, 0],
            [-sin_y, 0, cos_y, 0],
            [0, 0, 0, 1]
        ])

        # Rotation around Z
        Rz = np.array([
            [cos_z, -sin_z, 0, 0],
            [sin_z, cos_z, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        # Translation
        T = np.array([
            [1, 0, 0, px],
            [0, 1, 0, py],
            [0, 0, 1, pz],
            [0, 0, 0, 1]
        ])

        # Combine: T * Rz * Ry * Rx
        transform = T @ Rz @ Ry @ Rx

        return wp.mat44(transform)

    def get_component(self, name: str) -> Optional[GeometryComponent]:
        """Get a component by name"""
        return self.components.get(name)

    def get_all_meshes(self) -> List[wp.Mesh]:
        """Get all meshes from the assembly"""
        meshes = []
        for component in self.components.values():
            if component.mesh is not None:
                meshes.append(component.mesh)
        return meshes

    def get_bounds(self) -> tuple:
        """
        Get the bounding box of the assembly

        Returns:
            ((min_x, min_y, min_z), (max_x, max_y, max_z))
        """
        all_points = []

        for component in self.components.values():
            if component.mesh is not None:
                points = component.mesh.points.numpy()
                all_points.append(points)

        if not all_points:
            return ((0, 0, 0), (0, 0, 0))

        all_points = np.vstack(all_points)
        min_bounds = np.min(all_points, axis=0)
        max_bounds = np.max(all_points, axis=0)

        return (tuple(min_bounds), tuple(max_bounds))

    def get_food_components(self) -> List[GeometryComponent]:
        """Get all food components in the assembly"""
        return [
            comp for name, comp in self.components.items()
            if 'carrot' in name.lower() or 'potato' in name.lower()
        ]

    def __repr__(self) -> str:
        return f"BoilingAssembly(name='{self.name}', components={list(self.components.keys())})"


class SaucepanBuilder:
    """
    Builder for creating saucepan assemblies with configuration support

    Provides helper methods for creating standardized assemblies
    """

    @staticmethod
    def create_from_config(config: BoilingConfig) -> BoilingAssembly:
        """
        Create a complete boiling assembly from configuration

        All positioning and spacing is controlled by configuration - no magic numbers!

        Args:
            config: BoilingConfig with all parameters

        Returns:
            Fully assembled BoilingAssembly
        """
        assembly = BoilingAssembly(name="boiling_simulation", config=config)

        # Create saucepan body at origin (bottom at z=0)
        saucepan = CylinderComponent(
            name="saucepan_body",
            config=config.saucepan,
            rounded_bottom=True
        )
        assembly.add_component(saucepan, position=(0, 0, 0))

        # Create liquid domain
        water_radius = config.saucepan.inner_radius * config.liquid.radius_ratio
        water_height = config.get_water_level()
        liquid = LiquidDomain(
            name="water",
            config=config.liquid,
            radius=water_radius,
            height=water_height,
            use_cylindrical_grid=True
        )
        # Position water above saucepan bottom (using config-defined clearance)
        water_z = config.get_water_bottom_position()
        assembly.add_component(liquid, position=(0, 0, water_z))

        # Add food items (positioning controlled by config)
        SaucepanBuilder.add_food_items_from_config(assembly, config)

        # Add lid if requested
        if config.with_lid:
            lid_radius = config.get_lid_radius()
            lid = LidComponent(
                name="lid",
                config=config.lid,
                radius=lid_radius,
                has_knob=config.lid.has_knob,
                has_steam_vent=config.lid.has_steam_vent
            )
            # Position lid (using config-defined positioning strategy)
            lid_z = config.get_lid_position()
            assembly.add_component(lid, position=(0, 0, lid_z))

        return assembly

    @staticmethod
    def add_food_items_from_config(
        assembly: BoilingAssembly,
        config: BoilingConfig
    ):
        """
        Add food items based on configuration

        All positioning controlled by config - no magic numbers!

        Args:
            assembly: Existing BoilingAssembly
            config: BoilingConfig
        """
        num_pieces = config.num_food_pieces
        food_type = config.food_type

        # Calculate horizontal positions (using config-defined spacing)
        positions = SaucepanBuilder._calculate_food_positions(
            num_pieces,
            config.saucepan.inner_radius,
            config.food,
            config.assembly
        )

        # Get water positioning from config
        water_bottom_z = config.get_water_bottom_position()
        water_height = config.get_water_level()
        water_top_z = water_bottom_z + water_height

        # Get cut type from config
        cut_type = config.food.carrot_cut_type if food_type == "carrot" else None

        # Get food height from config based on cut type
        if food_type == "carrot":
            if cut_type == "round":
                food_height = config.food.carrot_round_thickness
            elif cut_type == "stick":
                food_height = config.food.carrot_length
            elif cut_type == "chunk":
                food_height = config.food.carrot_chunk_height
            else:
                food_height = config.food.carrot_length
        elif food_type == "potato":
            food_height = config.food.potato_radius * 2
        else:
            raise ValueError(f"Unknown food type: {food_type}")

        # Create food pieces
        for i, (x, y) in enumerate(positions):
            food = FoodObject(
                name=f"{food_type}_piece_{i}",
                food_type=food_type,
                cut_type=cut_type if food_type == "carrot" else "",
                config=config.food,
                position=(0, 0, 0)  # Create at origin
            )

            # Realistic physics: Carrots and potatoes sink (density > water)
            # They rest on the saucepan bottom, not floating in water
            # Position food so bottom rests on saucepan bottom (with slight clearance)
            bottom_clearance = 0.002  # 2mm clearance from saucepan bottom
            z_bottom = config.saucepan.bottom_thickness + bottom_clearance
            z_center = z_bottom + food_height * 0.5

            # Verify food is submerged (top should be below water surface)
            food_top_z = z_center + food_height * 0.5
            if food_top_z > water_top_z:
                print(f"Warning: {food.name} extends above water surface!")
                print(f"  Food top: {food_top_z*100:.2f}cm, Water top: {water_top_z*100:.2f}cm")

            assembly.add_component(food, position=(x, y, z_center))

    @staticmethod
    def _calculate_food_positions(
        num_pieces: int,
        saucepan_radius: float,
        food_config,
        assembly_config
    ) -> List[tuple]:
        """
        Calculate optimal food piece positions using config-defined spacing

        Args:
            num_pieces: Number of food pieces
            saucepan_radius: Inner radius of saucepan
            food_config: FoodItemConfig
            assembly_config: AssemblyConfig

        Returns:
            List of (x, y) positions
        """
        positions = []

        # Get food dimensions from config
        food_radius = food_config.carrot_radius  # Use carrot as reference

        # Maximum placement radius from config
        max_radius = saucepan_radius * assembly_config.food_wall_margin_ratio

        # Spacing between pieces from config
        spacing = food_radius * assembly_config.food_spacing_multiplier

        if num_pieces == 1:
            # Single piece at center
            positions.append((0.0, 0.0))

        elif num_pieces == 2:
            # Two pieces side by side along x-axis
            positions.append((-spacing / 2, 0.0))
            positions.append((spacing / 2, 0.0))

        elif num_pieces == 3:
            # Three pieces in a line along x-axis
            positions.append((-spacing, 0.0))
            positions.append((0.0, 0.0))
            positions.append((spacing, 0.0))

        elif num_pieces == 4:
            # Four pieces in a square pattern
            offset = max_radius * 0.5
            positions.append((-offset, -offset))
            positions.append((offset, -offset))
            positions.append((-offset, offset))
            positions.append((offset, offset))

        else:
            # Circular arrangement for 5+ pieces
            for i in range(num_pieces):
                angle = (i / num_pieces) * 2 * np.pi
                x = max_radius * np.cos(angle)
                y = max_radius * np.sin(angle)
                positions.append((x, y))

        return positions

    @staticmethod
    def create_standard_saucepan(
        radius: float = 0.1,
        height: float = 0.15,
        wall_thickness: float = 0.003,
        water_level: float = 0.10,
        bottom_thickness: float = 0.005,
        with_lid: bool = True
    ) -> BoilingAssembly:
        """
        Create a standard saucepan assembly (legacy method)

        For new code, use create_from_config() instead

        Args:
            radius: Inner radius in meters
            height: Saucepan height in meters
            wall_thickness: Wall thickness in meters
            water_level: Water level from bottom in meters
            bottom_thickness: Bottom plate thickness in meters
            with_lid: Whether to include a lid

        Returns:
            BoilingAssembly
        """
        # Create config from parameters
        saucepan_config = SaucepanGeometryConfig(
            inner_radius=radius,
            height=height,
            wall_thickness=wall_thickness,
            bottom_thickness=bottom_thickness
        )

        config = BoilingConfig(
            saucepan=saucepan_config,
            with_lid=with_lid
        )
        config.liquid.fill_level = water_level / height

        return SaucepanBuilder.create_from_config(config)

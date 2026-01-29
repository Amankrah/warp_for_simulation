"""
Air Classifier Geometry Construction Module

Modular construction of industrial updraft turbine air classifier based on
real industrial designs (Sturtevant Whirlwind type - Figure 9 from PDF).

Components:
- Classification chamber (cylindrical vessel)
- Rotating distributor plate (bottom feeder)
- Selector blades (rejector cage around shaft)
- Vertical shaft with hub and ports
- Feed inlet system (tangential or top entry)
- Fine outlet (through shaft or top center)
- Coarse outlet (conical bottom)
- Optional fan (internal or external)

Design based on:
- air-classifier.pdf Figures 9-12 (Updraft classifiers)
- Whirlwind, Superfine, Cyclone Air designs
"""

import numpy as np
import pyvista as pv
from dataclasses import dataclass
from typing import Tuple, Optional, List
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge
import matplotlib.patches as mpatches


@dataclass
class GeometryComponents:
    """Container for all geometry meshes for updraft classifier"""
    chamber: pv.PolyData
    chamber_cone: pv.PolyData
    vertical_shaft: pv.PolyData
    distributor_plate: pv.PolyData
    selector_blades: List[pv.PolyData]
    hub_with_ports: pv.PolyData
    feed_inlet: pv.PolyData
    fine_outlet: pv.PolyData
    coarse_outlet: pv.PolyData
    air_inlets: List[pv.PolyData]
    fan_blades: Optional[List[pv.PolyData]] = None


class AirClassifierGeometry:
    """
    Constructs 3D geometry for updraft turbine air classifier (Whirlwind type)

    Based on industrial design from PDF Figure 9 (Sturtevant Whirlwind):
    - Cylindrical chamber with conical bottom
    - Vertical shaft extending through center
    - Rotating distributor plate at bottom (feeds material into chamber)
    - Selector blades (rejector cage) around shaft in classification zone
    - Hub with ports for material passage
    - Feed inlet at top or side (tangential)
    - Fine outlet through top (through shaft or around it)
    - Coarse outlet at bottom cone
    - Optional internal fan at top of shaft
    """

    def __init__(
        self,
        chamber_radius: float = 0.5,
        chamber_height: float = 1.2,
        shaft_radius: float = 0.05,  # Vertical shaft through center
        distributor_plate_radius: float = 0.25,  # Bottom rotating plate
        distributor_height: float = 0.25,  # Height above cone - raised for better air flow space
        selector_blade_radius: float = 0.2,  # Radius of selector cage
        selector_blade_count: int = 24,  # Number of vertical selector blades
        selector_blade_height: float = 0.6,  # Height of selector zone
        selector_blade_thickness: float = 0.005,  # 5mm thick blades for better strength
        hub_radius: float = 0.15,  # Hub at top of selector zone
        include_internal_fan: bool = False
    ):
        """
        Initialize updraft air classifier geometry

        Args:
            chamber_radius: Classification chamber radius (m)
            chamber_height: Chamber height (m)
            shaft_radius: Vertical shaft radius (m)
            distributor_plate_radius: Rotating distributor plate radius (m)
            distributor_height: Height of distributor above cone bottom (m)
            selector_blade_radius: Radius of selector blade cage (m)
            selector_blade_count: Number of vertical selector blades
            selector_blade_height: Height of selector blade zone (m)
            selector_blade_thickness: Thickness of selector blades (m)
            hub_radius: Radius of hub with ports at top of selector zone (m)
            include_internal_fan: Include internal fan at top of shaft
        """
        self.chamber_radius = chamber_radius
        self.chamber_height = chamber_height
        self.shaft_radius = shaft_radius
        self.distributor_plate_radius = distributor_plate_radius
        self.distributor_height = distributor_height
        self.selector_blade_radius = selector_blade_radius
        self.selector_blade_count = selector_blade_count
        self.selector_blade_height = selector_blade_height
        self.selector_blade_thickness = selector_blade_thickness
        self.hub_radius = hub_radius
        self.include_internal_fan = include_internal_fan

        # Derived dimensions
        self.cone_angle = 60.0  # degrees (included angle)
        self.cone_height = chamber_radius / np.tan(np.radians(self.cone_angle / 2))

        # Selector blade zone starts above distributor
        self.selector_start_z = self.distributor_height + 0.1
        self.selector_end_z = self.selector_start_z + self.selector_blade_height

        # Hub position at top of selector blades
        self.hub_position_z = self.selector_end_z

        # Shaft extends from cone bottom to above chamber
        self.shaft_bottom_z = -self.cone_height
        self.shaft_top_z = self.chamber_height + 0.2

        # Component references
        self.components: Optional[GeometryComponents] = None

    def build_chamber(self) -> Tuple[pv.PolyData, pv.PolyData]:
        """
        Build classification chamber

        Returns:
            Tuple of (cylindrical section, conical bottom)
        """
        # Cylindrical section
        cylinder = pv.Cylinder(
            center=(0, 0, self.chamber_height / 2),
            direction=(0, 0, 1),
            radius=self.chamber_radius,
            height=self.chamber_height,
            resolution=60
        )

        # Conical bottom section
        cone = pv.Cone(
            center=(0, 0, -self.cone_height / 2),
            direction=(0, 0, 1),
            height=self.cone_height,
            radius=self.chamber_radius,
            resolution=60
        )

        return cylinder, cone

    def build_vertical_shaft(self) -> pv.PolyData:
        """
        Build vertical shaft extending through center of classifier

        Returns:
            Vertical shaft mesh
        """
        shaft_height = self.shaft_top_z - self.shaft_bottom_z

        shaft = pv.Cylinder(
            center=(0, 0, (self.shaft_top_z + self.shaft_bottom_z) / 2),
            direction=(0, 0, 1),
            radius=self.shaft_radius,
            height=shaft_height,
            resolution=30
        )

        return shaft

    def build_distributor_plate(self) -> pv.PolyData:
        """
        Build rotating distributor plate at bottom (feeder)

        This plate rotates to distribute material into the chamber
        from the feed inlet. Key component of updraft design.

        Returns:
            Distributor plate mesh
        """
        # Thin rotating disk
        plate_thickness = 0.02

        plate = pv.Cylinder(
            center=(0, 0, self.distributor_height),
            direction=(0, 0, 1),
            radius=self.distributor_plate_radius,
            height=plate_thickness,
            resolution=60
        )

        return plate

    def build_hub_with_ports(self) -> pv.PolyData:
        """
        Build hub with ports at top of selector zone

        The hub has openings (ports) that allow fine material
        to pass through after being accepted by selector blades.

        Returns:
            Hub mesh
        """
        hub_height = 0.15

        hub = pv.Cylinder(
            center=(0, 0, self.hub_position_z),
            direction=(0, 0, 1),
            radius=self.hub_radius,
            height=hub_height,
            resolution=40
        )

        return hub

    def build_selector_blades(self) -> List[pv.PolyData]:
        """
        Build selector blades (rejector cage)

        Vertical blades arranged in a cylinder around the shaft.
        These blades rotate and create centrifugal force that rejects
        coarse particles while allowing fine particles to pass through.

        Returns:
            List of selector blade meshes
        """
        blades = []

        # Blades extend vertically in the selector zone
        blade_height = self.selector_blade_height

        for i in range(self.selector_blade_count):
            angle = 2 * np.pi * i / self.selector_blade_count

            # Vertical blade as thin box extending from shaft radius to selector radius
            blade = pv.Box(
                bounds=[
                    self.shaft_radius * 1.5, self.selector_blade_radius,  # X: radial extent
                    -self.selector_blade_thickness / 2, self.selector_blade_thickness / 2,  # Y: thickness
                    -blade_height / 2, blade_height / 2  # Z: vertical height
                ]
            )

            # Rotate around Z axis to position
            blade = blade.rotate_z(np.degrees(angle), point=(0, 0, 0))

            # Translate to selector zone vertical position
            blade_center_z = self.selector_start_z + blade_height / 2
            blade = blade.translate((0, 0, blade_center_z))

            blades.append(blade)

        return blades

    def build_fan_blades(self) -> List[pv.PolyData]:
        """
        Build optional internal fan blades at top of shaft

        Returns:
            List of fan blade meshes
        """
        if not self.include_internal_fan:
            return []

        fan_blades = []
        fan_radius = self.chamber_radius * 0.4
        fan_blade_count = 8
        fan_height = 0.1
        fan_z = self.chamber_height - 0.2

        for i in range(fan_blade_count):
            angle = 2 * np.pi * i / fan_blade_count

            # Fan blade
            blade = pv.Box(
                bounds=[
                    self.shaft_radius, fan_radius,
                    -0.01, 0.01,
                    -fan_height / 2, fan_height / 2
                ]
            )

            # Rotate for swept angle (not radial)
            blade = blade.rotate_z(np.degrees(angle) - 20, point=(0, 0, 0))
            blade = blade.translate((0, 0, fan_z))

            fan_blades.append(blade)

        return fan_blades

    def build_feed_inlet(self, feed_type: str = "top") -> pv.PolyData:
        """
        Build feed inlet port

        Updraft classifiers can have:
        - Top feed: Material enters from top, falls onto distributor plate
        - Side feed: Material enters tangentially at distributor level

        Args:
            feed_type: "top" or "side"

        Returns:
            Feed inlet mesh
        """
        if feed_type == "top":
            # Top feed inlet (larger cylindrical port at top)
            inlet_radius = 0.15  # Increased from 0.1 for adequate feed capacity
            inlet_height = 0.2   # Taller inlet

            inlet = pv.Cylinder(
                center=(0, 0, self.chamber_height + inlet_height / 2),
                direction=(0, 0, 1),
                radius=inlet_radius,
                height=inlet_height,
                resolution=30
            )
        else:  # side feed
            # Side feed at distributor level
            inlet_width = 0.15
            inlet_height = 0.1
            inlet_depth = 0.1

            inlet_x = self.chamber_radius - inlet_depth / 2

            inlet = pv.Box(
                bounds=[
                    inlet_x - inlet_depth / 2, inlet_x + inlet_depth / 2,
                    -inlet_width / 2, inlet_width / 2,
                    self.distributor_height - inlet_height / 2,
                    self.distributor_height + inlet_height / 2
                ]
            )

        return inlet

    def build_fine_outlet(self) -> pv.PolyData:
        """
        Build fine fraction outlet at top

        In updraft design, fine particles exit through top center,
        either through hollow shaft or around shaft in expansion zone.

        Returns:
            Fine outlet mesh (annular or cylindrical duct)
        """
        # Annular outlet around shaft at top
        outlet_inner_radius = self.shaft_radius * 1.2
        outlet_outer_radius = self.chamber_radius * 0.4
        outlet_height = 0.15

        # Create annular outlet (ring shape)
        outer = pv.Cylinder(
            center=(0, 0, self.chamber_height + outlet_height / 2),
            direction=(0, 0, 1),
            radius=outlet_outer_radius,
            height=outlet_height,
            resolution=40
        )

        inner = pv.Cylinder(
            center=(0, 0, self.chamber_height + outlet_height / 2),
            direction=(0, 0, 1),
            radius=outlet_inner_radius,
            height=outlet_height * 1.1,
            resolution=40
        )

        # Subtract inner from outer to create annular ring
        # (Note: PyVista boolean operations can be tricky, using outer for visualization)
        outlet = outer

        return outlet

    def build_coarse_outlet(self) -> pv.PolyData:
        """
        Build coarse fraction outlet at bottom

        Returns:
            Coarse outlet mesh (cylindrical duct at cone bottom)
        """
        outlet_radius = 0.075  # 150mm diameter outlet
        outlet_height = 0.1

        outlet = pv.Cylinder(
            center=(0, 0, -self.cone_height - outlet_height / 2),
            direction=(0, 0, 1),
            radius=outlet_radius,
            height=outlet_height,
            resolution=20
        )

        return outlet

    def build_air_inlets(self, count: int = 4) -> List[pv.PolyData]:
        """
        Build air inlet ports

        In updraft design, air enters tangentially at chamber base level,
        creating a spiral upward flow pattern through the classifier.

        Args:
            count: Number of air inlets

        Returns:
            List of air inlet meshes
        """
        inlets = []

        # Larger tangential inlets for proper air distribution
        inlet_width = 0.15  # Wider for better flow
        inlet_height = 0.12  # Taller for adequate air volume
        inlet_depth = 0.12  # Deeper penetration into chamber

        # Position at chamber base, just above cone-cylinder transition
        inlet_z = 0.05  # Slightly above bottom

        for i in range(count):
            angle = 2 * np.pi * i / count

            # Position at chamber wall with slight inset
            x = (self.chamber_radius - inlet_depth / 2) * np.cos(angle)
            y = (self.chamber_radius - inlet_depth / 2) * np.sin(angle)

            inlet = pv.Box(
                bounds=[
                    -inlet_depth / 2, inlet_depth / 2,
                    -inlet_width / 2, inlet_width / 2,
                    -inlet_height / 2, inlet_height / 2
                ]
            )

            # Rotate to face tangentially (for spiral flow pattern)
            inlet = inlet.rotate_z(np.degrees(angle) + 90, point=(0, 0, 0))

            # Translate to position
            inlet = inlet.translate((x, y, inlet_z))

            inlets.append(inlet)

        return inlets

    def build_all_components(self) -> GeometryComponents:
        """
        Build all geometry components for updraft classifier

        Returns:
            GeometryComponents object with all meshes
        """
        print("Building updraft air classifier geometry (Whirlwind type)...")

        chamber, cone = self.build_chamber()
        shaft = self.build_vertical_shaft()
        distributor = self.build_distributor_plate()
        selector_blades = self.build_selector_blades()
        hub = self.build_hub_with_ports()
        feed = self.build_feed_inlet()
        fine = self.build_fine_outlet()
        coarse = self.build_coarse_outlet()
        air_inlets = self.build_air_inlets()
        fan_blades = self.build_fan_blades() if self.include_internal_fan else None

        self.components = GeometryComponents(
            chamber=chamber,
            chamber_cone=cone,
            vertical_shaft=shaft,
            distributor_plate=distributor,
            selector_blades=selector_blades,
            hub_with_ports=hub,
            feed_inlet=feed,
            fine_outlet=fine,
            coarse_outlet=coarse,
            air_inlets=air_inlets,
            fan_blades=fan_blades
        )

        print(f"  Chamber: R={self.chamber_radius}m, H={self.chamber_height}m")
        print(f"  Shaft: R={self.shaft_radius}m")
        print(f"  Distributor plate: R={self.distributor_plate_radius}m at Z={self.distributor_height}m")
        print(f"  Selector blades: {self.selector_blade_count} blades, R={self.selector_blade_radius}m")
        print(f"  Selector zone: Z={self.selector_start_z:.2f}m to {self.selector_end_z:.2f}m")
        print(f"  Cone: H={self.cone_height:.3f}m, angle={self.cone_angle}°")

        return self.components

    def visualize_3d(
        self,
        show_selector_blades: bool = True,
        show_inlets: bool = True,
        show_internal_components: bool = True,
        camera_position: str = 'iso',
        window_size: Tuple[int, int] = (1200, 900),
        screenshot_path: Optional[str] = None
    ):
        """
        Create 3D visualization of updraft air classifier

        Args:
            show_selector_blades: Show vertical selector blades
            show_inlets: Show feed and air inlets
            show_internal_components: Show shaft, distributor, hub
            camera_position: Camera position ('iso', 'xy', 'xz', 'yz')
            window_size: Window size (width, height)
            screenshot_path: Path to save screenshot (optional)
        """
        if self.components is None:
            self.build_all_components()

        plotter = pv.Plotter(window_size=window_size)
        plotter.set_background('white')

        # Add chamber (transparent)
        plotter.add_mesh(
            self.components.chamber,
            opacity=0.15,
            color='lightblue',
            show_edges=True,
            line_width=1,
            label='Chamber'
        )

        # Add cone (transparent)
        plotter.add_mesh(
            self.components.chamber_cone,
            opacity=0.15,
            color='lightblue',
            show_edges=True,
            line_width=1
        )

        # Add internal components
        if show_internal_components:
            # Vertical shaft
            plotter.add_mesh(
                self.components.vertical_shaft,
                color='darkgray',
                show_edges=True,
                label='Vertical Shaft'
            )

            # Distributor plate (rotating feeder)
            plotter.add_mesh(
                self.components.distributor_plate,
                color='chocolate',
                opacity=0.8,
                show_edges=True,
                label='Distributor Plate'
            )

            # Hub with ports
            plotter.add_mesh(
                self.components.hub_with_ports,
                color='goldenrod',
                opacity=0.7,
                show_edges=True,
                label='Hub with Ports'
            )

        # Add selector blades (rejector cage)
        if show_selector_blades:
            for i, blade in enumerate(self.components.selector_blades):
                plotter.add_mesh(
                    blade,
                    color='steelblue',
                    opacity=0.7,
                    show_edges=True,
                    line_width=0.5,
                    label='Selector Blades' if i == 0 else None
                )

        # Add fan blades if present
        if self.components.fan_blades:
            for i, fan_blade in enumerate(self.components.fan_blades):
                plotter.add_mesh(
                    fan_blade,
                    color='lightcoral',
                    opacity=0.6,
                    show_edges=True,
                    label='Fan Blades' if i == 0 else None
                )

        # Add outlets
        plotter.add_mesh(
            self.components.fine_outlet,
            color='green',
            opacity=0.6,
            label='Fine Outlet (Top)'
        )

        plotter.add_mesh(
            self.components.coarse_outlet,
            color='brown',
            opacity=0.6,
            label='Coarse Outlet (Bottom)'
        )

        # Add inlets
        if show_inlets:
            plotter.add_mesh(
                self.components.feed_inlet,
                color='orange',
                opacity=0.7,
                label='Feed Inlet'
            )

            for i, inlet in enumerate(self.components.air_inlets):
                plotter.add_mesh(
                    inlet,
                    color='cyan',
                    opacity=0.6,
                    label='Air Inlets (Bottom)' if i == 0 else None
                )

        # Add coordinate axes
        plotter.add_axes(
            xlabel='X (m)',
            ylabel='Y (m)',
            zlabel='Z (m)',
            line_width=3,
            color='black'
        )

        # Set camera position
        if camera_position == 'iso':
            plotter.camera_position = 'iso'
        elif camera_position == 'xy':
            plotter.view_xy()
        elif camera_position == 'xz':
            plotter.view_xz()
        elif camera_position == 'yz':
            plotter.view_yz()

        # Add legend
        plotter.add_legend(bcolor='white', size=(0.25, 0.35))

        # Add title
        plotter.add_text(
            'Updraft Air Classifier - Whirlwind Type',
            position='upper_edge',
            font_size=14,
            color='black'
        )

        # Show or save
        if screenshot_path:
            plotter.show(screenshot=screenshot_path)
        else:
            plotter.show()

        return plotter

    def plot_2d_sections(self, save_path: Optional[str] = None):
        """
        Create 2D engineering drawings (side view and top view) for updraft classifier

        Args:
            save_path: Path to save figure (optional)
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # ============ SIDE VIEW (vertical cross-section) ============
        ax1.set_aspect('equal')
        ax1.set_title('Updraft Classifier - Vertical Cross-Section', fontsize=14, weight='bold')
        ax1.set_xlabel('Radial Distance (m)', fontsize=12)
        ax1.set_ylabel('Height (m)', fontsize=12)
        ax1.grid(True, alpha=0.3)

        # Chamber walls
        chamber_left = -self.chamber_radius
        chamber_right = self.chamber_radius
        chamber_top = self.chamber_height
        chamber_bottom = 0

        ax1.plot([chamber_left, chamber_left], [chamber_bottom, chamber_top],
                'k-', linewidth=2, label='Chamber Wall')
        ax1.plot([chamber_right, chamber_right], [chamber_bottom, chamber_top],
                'k-', linewidth=2)
        ax1.plot([chamber_left, chamber_right], [chamber_top, chamber_top],
                'k-', linewidth=2)

        # Conical bottom
        cone_bottom = -self.cone_height
        ax1.plot([chamber_left, 0], [chamber_bottom, cone_bottom],
                'k-', linewidth=2, label='Conical Bottom')
        ax1.plot([chamber_right, 0], [chamber_bottom, cone_bottom],
                'k-', linewidth=2)

        # Vertical shaft (centerline)
        ax1.plot([0, 0], [cone_bottom, chamber_top + 0.2],
                'darkgray', linewidth=4, label='Vertical Shaft', solid_capstyle='round')
        ax1.plot([-self.shaft_radius, -self.shaft_radius], [cone_bottom, chamber_top + 0.2],
                'darkgray', linewidth=1, linestyle='--', alpha=0.5)
        ax1.plot([self.shaft_radius, self.shaft_radius], [cone_bottom, chamber_top + 0.2],
                'darkgray', linewidth=1, linestyle='--', alpha=0.5)

        # Distributor plate
        dist_plate = Rectangle(
            (-self.distributor_plate_radius, self.distributor_height - 0.01),
            2 * self.distributor_plate_radius,
            0.02,
            facecolor='chocolate',
            edgecolor='black',
            linewidth=1.5,
            label='Distributor Plate'
        )
        ax1.add_patch(dist_plate)

        # Selector blades (show a few vertical blades)
        selector_bottom = self.selector_start_z
        selector_top = self.selector_end_z
        for x in np.linspace(self.shaft_radius * 1.5, self.selector_blade_radius, 4):
            ax1.plot([x, x], [selector_bottom, selector_top],
                    'steelblue', linewidth=3, alpha=0.7)
            ax1.plot([-x, -x], [selector_bottom, selector_top],
                    'steelblue', linewidth=3, alpha=0.7)

        # Selector cage outline
        ax1.plot([-self.selector_blade_radius, -self.selector_blade_radius],
                [selector_bottom, selector_top],
                'steelblue', linewidth=2, linestyle='--', alpha=0.5, label='Selector Cage')
        ax1.plot([self.selector_blade_radius, self.selector_blade_radius],
                [selector_bottom, selector_top],
                'steelblue', linewidth=2, linestyle='--', alpha=0.5)

        # Hub with ports
        hub_bottom = self.hub_position_z - 0.075
        hub_top = self.hub_position_z + 0.075
        hub_rect = Rectangle(
            (-self.hub_radius, hub_bottom),
            2 * self.hub_radius,
            0.15,
            facecolor='goldenrod',
            edgecolor='black',
            linewidth=1.5,
            alpha=0.7,
            label='Hub with Ports'
        )
        ax1.add_patch(hub_rect)

        # Feed inlet (top)
        ax1.add_patch(Rectangle(
            (-0.1, chamber_top),
            0.2, 0.15,
            facecolor='orange', edgecolor='black', linewidth=1,
            label='Feed Inlet (Top)', alpha=0.7
        ))
        ax1.arrow(0, chamber_top + 0.15, 0, -0.08,
                 head_width=0.05, head_length=0.03, fc='orange', ec='black')

        # Fine outlet (annular)
        fine_outlet_radius = self.chamber_radius * 0.4
        ax1.add_patch(Rectangle(
            (self.shaft_radius * 1.2, chamber_top),
            fine_outlet_radius - self.shaft_radius * 1.2, 0.1,
            facecolor='green', edgecolor='black', linewidth=1,
            alpha=0.6
        ))
        ax1.add_patch(Rectangle(
            (-(fine_outlet_radius), chamber_top),
            fine_outlet_radius - self.shaft_radius * 1.2, 0.1,
            facecolor='green', edgecolor='black', linewidth=1,
            label='Fine Outlet (Top)', alpha=0.6
        ))
        # Fine exit arrow
        ax1.arrow(fine_outlet_radius * 0.6, chamber_top + 0.1, 0, 0.08,
                 head_width=0.04, head_length=0.03, fc='green', ec='black')
        ax1.arrow(-fine_outlet_radius * 0.6, chamber_top + 0.1, 0, 0.08,
                 head_width=0.04, head_length=0.03, fc='green', ec='black')

        # Coarse outlet
        outlet_radius = 0.075
        ax1.add_patch(Rectangle(
            (-outlet_radius, cone_bottom - 0.1),
            2 * outlet_radius, 0.1,
            facecolor='brown', edgecolor='black', linewidth=1,
            label='Coarse Outlet (Bottom)', alpha=0.6
        ))
        ax1.arrow(0, cone_bottom - 0.15, 0, -0.08,
                 head_width=0.05, head_length=0.03, fc='brown', ec='black')

        # Air flow arrows (upward)
        # Air enters at bottom, flows up
        for x_pos in [-self.chamber_radius * 0.7, -self.chamber_radius * 0.3,
                      self.chamber_radius * 0.3, self.chamber_radius * 0.7]:
            ax1.arrow(x_pos, 0.05, 0, 0.15,
                     head_width=0.04, head_length=0.03,
                     fc='cyan', ec='black', linewidth=0.5, alpha=0.5)
        ax1.text(self.chamber_radius * 0.75, 0.15,
                'Air Up', fontsize=9, ha='center', color='blue')

        # Air inlet at bottom (larger, tangential)
        ax1.add_patch(Rectangle(
            (self.chamber_radius - 0.08, 0.0),
            0.12, 0.12,
            facecolor='cyan', edgecolor='black', linewidth=1,
            label='Air Inlet (Tangential)', alpha=0.7
        ))
        # Arrow showing tangential air entry
        ax1.arrow(self.chamber_radius + 0.05, 0.06, -0.10, 0,
                 head_width=0.04, head_length=0.03, fc='cyan', ec='black')

        # Labels and annotations
        ax1.text(0, self.distributor_height - 0.08,
                'Distributor\n(rotates)',
                ha='center', va='top', fontsize=8,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax1.text(self.selector_blade_radius * 1.3, (selector_bottom + selector_top) / 2,
                f'Selector Zone\n{self.selector_blade_count} blades\n(rotates)',
                ha='left', va='center', fontsize=8,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

        ax1.set_xlim(-self.chamber_radius * 1.3, self.chamber_radius * 1.3)
        ax1.set_ylim(cone_bottom - 0.3, chamber_top + 0.3)
        ax1.legend(loc='upper right', fontsize=9)

        # ============ TOP VIEW (horizontal cross-section at selector) ============
        ax2.set_aspect('equal')
        ax2.set_title(f'Top View at Selector Level (Z = {(self.selector_start_z + self.selector_end_z)/2:.2f}m)',
                     fontsize=14, weight='bold')
        ax2.set_xlabel('X (m)', fontsize=12)
        ax2.set_ylabel('Y (m)', fontsize=12)
        ax2.grid(True, alpha=0.3)

        # Chamber outline
        chamber_circle = Circle((0, 0), self.chamber_radius,
                               fill=False, edgecolor='black',
                               linewidth=2, label='Chamber Wall')
        ax2.add_patch(chamber_circle)

        # Shaft (center)
        shaft_circle = Circle((0, 0), self.shaft_radius,
                             facecolor='darkgray', edgecolor='black',
                             linewidth=1.5, label='Vertical Shaft')
        ax2.add_patch(shaft_circle)

        # Selector blades (vertical blades, radial arrangement)
        for i in range(self.selector_blade_count):
            angle = 2 * np.pi * i / self.selector_blade_count
            x_inner = self.shaft_radius * 1.5 * np.cos(angle)
            y_inner = self.shaft_radius * 1.5 * np.sin(angle)
            x_outer = self.selector_blade_radius * np.cos(angle)
            y_outer = self.selector_blade_radius * np.sin(angle)

            ax2.plot([x_inner, x_outer], [y_inner, y_outer],
                    'steelblue', linewidth=2, alpha=0.7)

        # Selector cage circle
        selector_circle = Circle((0, 0), self.selector_blade_radius,
                                fill=False, edgecolor='steelblue',
                                linewidth=1.5, linestyle='--',
                                label=f'Selector Cage ({self.selector_blade_radius}m)')
        ax2.add_patch(selector_circle)

        # Air inlets (radial or tangential)
        for i in range(4):
            angle = 2 * np.pi * i / 4
            x = self.chamber_radius * np.cos(angle)
            y = self.chamber_radius * np.sin(angle)

            # Arrow showing inward radial air flow
            dx = -0.12 * np.cos(angle)
            dy = -0.12 * np.sin(angle)

            ax2.arrow(x, y, dx, dy,
                     head_width=0.05, head_length=0.03,
                     fc='cyan', ec='black', linewidth=1, alpha=0.7,
                     label='Air Inlets' if i == 0 else None)

        # Rotation arrow for selector/distributor
        rotation_arrow = mpatches.FancyArrowPatch(
            (self.selector_blade_radius * 0.7, 0),
            (self.selector_blade_radius * 0.7 * np.cos(0.6),
             self.selector_blade_radius * 0.7 * np.sin(0.6)),
            arrowstyle='->,head_width=0.4,head_length=0.8',
            color='red', linewidth=2,
            connectionstyle='arc3,rad=0.3'
        )
        ax2.add_patch(rotation_arrow)
        ax2.text(self.selector_blade_radius * 0.5, self.selector_blade_radius * 0.3,
                'Rotation', fontsize=10, color='red', weight='bold')

        # Annular separation zone (between shaft and selector cage)
        separation_zone = mpatches.Annulus((0, 0), self.selector_blade_radius,
                                           self.selector_blade_radius - self.shaft_radius * 1.5,
                                           facecolor='yellow', alpha=0.2,
                                           edgecolor='orange', linewidth=1.5, linestyle=':',
                                           label='Separation Zone')
        ax2.add_patch(separation_zone)

        # Fine passage zone (inside selector)
        fine_zone = Circle((0, 0), self.shaft_radius * 1.5,
                          facecolor='green', alpha=0.15,
                          edgecolor='green', linewidth=1.5,
                          linestyle=':', label='Fine Passage')
        ax2.add_patch(fine_zone)

        ax2.set_xlim(-self.chamber_radius * 1.2, self.chamber_radius * 1.2)
        ax2.set_ylim(-self.chamber_radius * 1.2, self.chamber_radius * 1.2)
        ax2.legend(loc='upper right', fontsize=9)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"2D engineering drawings saved to: {save_path}")

        plt.show()

    def print_specifications(self):
        """Print detailed specifications of the updraft air classifier"""
        print("\n" + "=" * 70)
        print("UPDRAFT AIR CLASSIFIER SPECIFICATIONS (Whirlwind Type)")
        print("=" * 70)

        print("\n📐 CHAMBER GEOMETRY:")
        print(f"  Chamber Diameter:        {self.chamber_radius * 2:.3f} m ({self.chamber_radius * 2000:.0f} mm)")
        print(f"  Chamber Height:          {self.chamber_height:.3f} m ({self.chamber_height * 1000:.0f} mm)")
        print(f"  Cone Height:             {self.cone_height:.3f} m ({self.cone_height * 1000:.0f} mm)")
        print(f"  Cone Angle:              {self.cone_angle:.0f}° (included angle)")
        print(f"  Total Height:            {self.chamber_height + self.cone_height:.3f} m")

        print(f"\n🔧 VERTICAL SHAFT:")
        print(f"  Shaft Diameter:          {self.shaft_radius * 2:.3f} m ({self.shaft_radius * 2000:.0f} mm)")
        print(f"  Shaft Extends:           Z = {self.shaft_bottom_z:.2f}m to {self.shaft_top_z:.2f}m")

        print(f"\n🔄 DISTRIBUTOR PLATE (Rotating Feeder):")
        print(f"  Plate Diameter:          {self.distributor_plate_radius * 2:.3f} m ({self.distributor_plate_radius * 2000:.0f} mm)")
        print(f"  Position:                Z = {self.distributor_height:.2f} m (above cone bottom)")
        print(f"  Function:                Feeds material into chamber radially")

        print(f"\n⚙️  SELECTOR BLADES (Rejector Cage):")
        print(f"  Blade Cage Diameter:     {self.selector_blade_radius * 2:.3f} m ({self.selector_blade_radius * 2000:.0f} mm)")
        print(f"  Number of Blades:        {self.selector_blade_count}")
        print(f"  Blade Height:            {self.selector_blade_height:.3f} m ({self.selector_blade_height * 1000:.0f} mm)")
        print(f"  Blade Thickness:         {self.selector_blade_thickness * 1000:.1f} mm")
        print(f"  Selector Zone:           Z = {self.selector_start_z:.2f}m to {self.selector_end_z:.2f}m")

        # Blade gap calculation
        circumference = 2 * np.pi * self.selector_blade_radius
        total_blade_width = self.selector_blade_count * self.selector_blade_thickness
        total_gap = circumference - total_blade_width
        gap_per_blade = total_gap / self.selector_blade_count
        print(f"  Gap Between Blades:      {gap_per_blade * 1000:.1f} mm")

        print(f"\n🎯 HUB WITH PORTS:")
        print(f"  Hub Diameter:            {self.hub_radius * 2:.3f} m ({self.hub_radius * 2000:.0f} mm)")
        print(f"  Position:                Z = {self.hub_position_z:.2f} m (top of selector zone)")
        print(f"  Function:                Allows fine particles to pass through")

        print(f"\n🔄 FLOW PATHS:")
        print(f"  Feed Inlet:              Top or side entry onto distributor plate")
        print(f"  Air Inlets:              Bottom (4× tangential/radial)")
        print(f"  Fine Outlet:             Top center (annular around shaft)")
        print(f"  Coarse Outlet:           Bottom cone (Ø150 mm)")

        print(f"\n📊 VOLUME CALCULATIONS:")
        volume_cylinder = np.pi * self.chamber_radius**2 * self.chamber_height
        volume_cone = (1/3) * np.pi * self.chamber_radius**2 * self.cone_height
        total_volume = volume_cylinder + volume_cone
        print(f"  Cylinder Volume:         {volume_cylinder:.3f} m³ ({volume_cylinder * 1000:.0f} L)")
        print(f"  Cone Volume:             {volume_cone:.3f} m³ ({volume_cone * 1000:.0f} L)")
        print(f"  Total Volume:            {total_volume:.3f} m³ ({total_volume * 1000:.0f} L)")

        print(f"\n🎯 DESIGN RATIOS:")
        selector_chamber_ratio = 2 * self.selector_blade_radius / (2 * self.chamber_radius)
        print(f"  D_selector/D_chamber:    {selector_chamber_ratio:.2f} (typical: 0.3-0.5)")
        distributor_chamber_ratio = 2 * self.distributor_plate_radius / (2 * self.chamber_radius)
        print(f"  D_distributor/D_chamber: {distributor_chamber_ratio:.2f} (typical: 0.4-0.6)")
        hc_ratio = self.chamber_height / (2 * self.chamber_radius)
        print(f"  H_chamber/D_chamber:     {hc_ratio:.2f} (typical: 1.0-1.5)")

        print(f"\n💡 OPERATING PRINCIPLE:")
        print(f"  1. Material enters from top/side onto distributor plate")
        print(f"  2. Rotating distributor throws material radially into chamber")
        print(f"  3. Upward air flow carries particles toward selector blades")
        print(f"  4. Rotating selector blades create centrifugal field")
        print(f"  5. Fine particles: Pass through selector blades → exit top")
        print(f"  6. Coarse particles: Rejected by centrifugal force → fall to cone")

        print("=" * 70 + "\n")


def create_standard_industrial_classifier() -> AirClassifierGeometry:
    """
    Create a standard industrial-scale updraft air classifier (Whirlwind type)

    Based on typical industrial specifications for 200 kg/hr capacity

    Returns:
        AirClassifierGeometry instance
    """
    return AirClassifierGeometry(
        chamber_radius=0.5,                    # 1000 mm diameter chamber
        chamber_height=1.2,                    # 1200 mm height
        shaft_radius=0.05,                     # 100 mm diameter shaft
        distributor_plate_radius=0.25,         # 500 mm diameter distributor
        distributor_height=0.25,               # 250 mm above cone bottom - raised for air flow
        selector_blade_radius=0.2,             # 400 mm diameter selector cage
        selector_blade_count=24,               # 24 vertical blades
        selector_blade_height=0.6,             # 600 mm tall selector zone
        selector_blade_thickness=0.005,        # 5 mm thick blades for strength
        hub_radius=0.15,                       # 300 mm diameter hub
        include_internal_fan=False             # External fan (typical)
    )


def create_pilot_scale_classifier() -> AirClassifierGeometry:
    """
    Create a pilot-scale updraft air classifier (half size)

    Returns:
        AirClassifierGeometry instance
    """
    return AirClassifierGeometry(
        chamber_radius=0.25,                   # 500 mm diameter chamber
        chamber_height=0.6,                    # 600 mm height
        shaft_radius=0.025,                    # 50 mm diameter shaft
        distributor_plate_radius=0.125,        # 250 mm diameter distributor
        distributor_height=0.075,              # 75 mm above cone bottom
        selector_blade_radius=0.1,             # 200 mm diameter selector cage
        selector_blade_count=16,               # 16 vertical blades
        selector_blade_height=0.3,             # 300 mm tall selector zone
        selector_blade_thickness=0.002,        # 2 mm thick blades
        hub_radius=0.075,                      # 150 mm diameter hub
        include_internal_fan=False
    )


if __name__ == "__main__":
    """Example usage"""

    # Create standard industrial updraft classifier
    print("Creating standard industrial updraft air classifier (Whirlwind type)...")
    classifier = create_standard_industrial_classifier()

    # Print specifications
    classifier.print_specifications()

    # Build all components
    components = classifier.build_all_components()

    # Create 2D engineering drawings
    print("\nGenerating 2D engineering drawings...")
    classifier.plot_2d_sections(save_path="air_classifier_2d_drawings.png")

    # Create 3D visualization
    print("\nGenerating 3D visualization...")
    classifier.visualize_3d(
        show_selector_blades=True,
        show_inlets=True,
        show_internal_components=True,
        camera_position='iso',
        screenshot_path="air_classifier_3d_model.png"
    )

    print("\n✓ Updraft classifier geometry construction complete!")
    print("  - 2D drawings saved to: air_classifier_2d_drawings.png")
    print("  - 3D model saved to: air_classifier_3d_model.png")
    print("\nKey components:")
    print("  • Vertical shaft through center")
    print("  • Rotating distributor plate at bottom (feeds material)")
    print("  • Selector blades (rejector cage) in classification zone")
    print("  • Hub with ports for fine particle passage")
    print("  • Upward air flow for particle classification")

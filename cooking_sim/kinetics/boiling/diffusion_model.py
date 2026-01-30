"""
Nutrient diffusion model for food internal grid

Implements 3D diffusion equation using finite difference method:
    ∂C/∂t = D·∇²C

Where:
    C: Nutrient concentration (μg/g)
    D: Diffusion coefficient (m²/s)
    ∇²C: Laplacian operator

Physical Context:
-----------------
Nutrients (e.g., Vitamin A) diffuse through the food matrix toward the surface,
where they leach into the surrounding water. This creates a concentration gradient
from the interior (high) to the surface (low) of the food.

Typical diffusion coefficients:
    - Vitamin A in carrots: D ≈ 1×10⁻¹⁰ m²/s
    - Water-soluble vitamins: D ≈ 5×10⁻¹⁰ m²/s

Boundary Conditions:
-------------------
1. **Interior boundaries** (food center): Neumann BC (∂C/∂n = 0) - no flux
2. **Surface boundaries** (food-water interface): Robin BC - mass transfer
   Flux: J = k_m·(C_surface - C_water/K_partition)
   where k_m is mass transfer coefficient and K is partition coefficient
"""

import warp as wp
import numpy as np


@wp.kernel
def apply_surface_leaching(
    concentration: wp.array(dtype=float),
    grid_points: wp.array(dtype=wp.vec3),
    is_surface_point: wp.array(dtype=int),
    mass_transfer_coeff: float,
    water_concentration: float,
    partition_coefficient: float,
    dt: float,
    num_points: int
):
    """
    Apply surface leaching boundary condition

    At the food-water interface, nutrients transfer to water according to:
        dC/dt = -k_m·A/V·(C_food - C_water/K_partition)

    Args:
        concentration: Nutrient concentration in food [num_points]
        grid_points: 3D positions of grid points [num_points]
        is_surface_point: 1 if point is on surface, 0 otherwise [num_points]
        mass_transfer_coeff: k_m (m/s)
        water_concentration: C_water (μg/m³)
        partition_coefficient: K (dimensionless)
        dt: Time step (s)
        num_points: Number of grid points
    """
    tid = wp.tid()

    if tid >= num_points:
        return

    # Only apply leaching to surface points
    if is_surface_point[tid] == 0:
        return

    C_food = concentration[tid]

    # Equilibrium concentration in food (accounting for partition)
    C_eq = water_concentration / partition_coefficient

    # Driving force for mass transfer
    driving_force = C_food - C_eq

    # Mass transfer rate (simplified, assuming unit surface area)
    # In reality, should account for actual surface area of grid cell
    rate = mass_transfer_coeff * driving_force

    # Update concentration (explicit)
    C_new = C_food - rate * dt

    # Ensure non-negative concentration
    if C_new < 0.0:
        C_new = 0.0

    concentration[tid] = C_new


@wp.kernel
def compute_diffusion_3d_structured(
    concentration: wp.array(dtype=float),
    concentration_new: wp.array(dtype=float),
    grid_indices: wp.array(dtype=wp.vec3i),
    nx: int,
    ny: int,
    nz: int,
    diffusion_coefficient: float,
    dx: float,
    dy: float,
    dz: float,
    dt: float,
    num_points: int
):
    """
    Compute 3D diffusion on structured grid using 7-point stencil

    Uses central difference approximation:
    ∇²C ≈ (C_{i+1} - 2C_i + C_{i-1})/dx² +
          (C_{j+1} - 2C_j + C_{j-1})/dy² +
          (C_{k+1} - 2C_k + C_{k-1})/dz²

    Args:
        concentration: Current concentration field [num_points]
        concentration_new: Updated concentration field [num_points]
        grid_indices: 3D indices (i,j,k) for each point [num_points]
        nx, ny, nz: Grid dimensions
        diffusion_coefficient: D (m²/s)
        dx, dy, dz: Grid spacing (m)
        dt: Time step (s)
        num_points: Number of grid points
    """
    tid = wp.tid()

    if tid >= num_points:
        return

    # Get 3D grid indices for this point
    idx = grid_indices[tid]
    i = idx[0]
    j = idx[1]
    k = idx[2]

    C_center = concentration[tid]

    # Compute Laplacian using 7-point stencil
    # Initialize with boundary handling (Neumann: zero flux at boundaries)
    d2C_dx2 = float(0.0)
    d2C_dy2 = float(0.0)
    d2C_dz2 = float(0.0)

    # X-direction second derivative
    if i > 0 and i < nx - 1:
        # Interior point - use central difference
        idx_left = int((k * ny + j) * nx + (i - 1))
        idx_right = int((k * ny + j) * nx + (i + 1))
        C_left = concentration[idx_left]
        C_right = concentration[idx_right]
        d2C_dx2 = (C_right - 2.0 * C_center + C_left) / (dx * dx)
    elif i == 0:
        # Left boundary - one-sided difference (Neumann BC: ∂C/∂x = 0)
        idx_right = int((k * ny + j) * nx + (i + 1))
        C_right = concentration[idx_right]
        d2C_dx2 = (C_right - C_center) / (dx * dx)
    else:  # i == nx - 1
        # Right boundary - one-sided difference
        idx_left = int((k * ny + j) * nx + (i - 1))
        C_left = concentration[idx_left]
        d2C_dx2 = (C_left - C_center) / (dx * dx)

    # Y-direction second derivative
    if j > 0 and j < ny - 1:
        idx_down = int((k * ny + (j - 1)) * nx + i)
        idx_up = int((k * ny + (j + 1)) * nx + i)
        C_down = concentration[idx_down]
        C_up = concentration[idx_up]
        d2C_dy2 = (C_up - 2.0 * C_center + C_down) / (dy * dy)
    elif j == 0:
        idx_up = int((k * ny + (j + 1)) * nx + i)
        C_up = concentration[idx_up]
        d2C_dy2 = (C_up - C_center) / (dy * dy)
    else:  # j == ny - 1
        idx_down = int((k * ny + (j - 1)) * nx + i)
        C_down = concentration[idx_down]
        d2C_dy2 = (C_down - C_center) / (dy * dy)

    # Z-direction second derivative
    if k > 0 and k < nz - 1:
        idx_below = int(((k - 1) * ny + j) * nx + i)
        idx_above = int(((k + 1) * ny + j) * nx + i)
        C_below = concentration[idx_below]
        C_above = concentration[idx_above]
        d2C_dz2 = (C_above - 2.0 * C_center + C_below) / (dz * dz)
    elif k == 0:
        idx_above = int(((k + 1) * ny + j) * nx + i)
        C_above = concentration[idx_above]
        d2C_dz2 = (C_above - C_center) / (dz * dz)
    else:  # k == nz - 1
        idx_below = int(((k - 1) * ny + j) * nx + i)
        C_below = concentration[idx_below]
        d2C_dz2 = (C_below - C_center) / (dz * dz)

    # Total Laplacian
    laplacian = d2C_dx2 + d2C_dy2 + d2C_dz2

    # Explicit Euler time integration
    # C_{n+1} = C_n + D·dt·∇²C_n
    concentration_new[tid] = C_center + diffusion_coefficient * dt * laplacian


class NutrientDiffusion:
    """
    Nutrient diffusion in food matrix

    Models 3D diffusion of nutrients within the food internal grid using
    finite difference method. This is essential for capturing nutrient
    gradients from the interior to the surface of food pieces.

    Features:
    - Structured 3D grid support
    - Stability checking (CFL condition)
    - Neumann boundary conditions (zero flux at interior boundaries)
    - Explicit time integration
    """

    def __init__(self, diffusion_coefficient: float = 1e-10):
        """
        Initialize diffusion model

        Args:
            diffusion_coefficient: D in m²/s
                - Vitamin A in vegetables: ~1×10⁻¹⁰ m²/s
                - Water-soluble vitamins: ~5×10⁻¹⁰ m²/s
        """
        self.D = diffusion_coefficient
        self.grid_indices = None
        self.nx = 0
        self.ny = 0
        self.nz = 0
        self.dx = 0.0
        self.dy = 0.0
        self.dz = 0.0

    def initialize_grid(
        self,
        grid_indices: np.ndarray,
        nx: int,
        ny: int,
        nz: int,
        dx: float,
        dy: float,
        dz: float
    ):
        """
        Initialize structured grid information

        Args:
            grid_indices: Array of shape (num_points, 3) with (i,j,k) indices
            nx, ny, nz: Grid dimensions
            dx, dy, dz: Grid spacing in each direction (m)
        """
        self.grid_indices = wp.array(grid_indices, dtype=wp.vec3i)
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.dx = dx
        self.dy = dy
        self.dz = dz

        # Verify grid
        print(f"\nDiffusion grid initialized:")
        print(f"  - Dimensions: {nx} × {ny} × {nz} = {len(grid_indices)} points")
        print(f"  - Spacing: dx={dx*1000:.3f}mm, dy={dy*1000:.3f}mm, dz={dz*1000:.3f}mm")
        print(f"  - Diffusion coefficient: D={self.D:.2e} m²/s")

        # Check stability
        dt_max = self.get_max_stable_timestep(min(dx, dy, dz))
        print(f"  - Maximum stable timestep: {dt_max:.3f}s")

    def check_stability(self, dt: float) -> bool:
        """
        Check if time step satisfies stability criterion (CFL condition)

        For explicit FTCS scheme in 3D:
            dt ≤ 1/(2D) · 1/(1/dx² + 1/dy² + 1/dz²)

        Simplified for uniform grid (dx=dy=dz): dt ≤ dx²/(6D)

        Args:
            dt: Time step (s)

        Returns:
            True if stable, False otherwise
        """
        # Use minimum grid spacing for conservative stability check
        h_min = min(self.dx, self.dy, self.dz)
        dt_max = h_min * h_min / (6.0 * self.D)
        return dt <= dt_max

    def get_max_stable_timestep(self, h: float = None) -> float:
        """
        Get maximum stable time step for explicit scheme

        Args:
            h: Grid spacing (m). If None, uses minimum of (dx, dy, dz)

        Returns:
            Maximum dt (s)
        """
        if h is None:
            h = min(self.dx, self.dy, self.dz) if self.dx > 0 else 0.001

        # CFL condition: dt ≤ h²/(6D) for 3D explicit scheme
        return h * h / (6.0 * self.D)

    def step(
        self,
        concentration: wp.array,
        concentration_new: wp.array,
        dt: float,
        num_points: int
    ):
        """
        Advance diffusion simulation by one time step

        Solves: ∂C/∂t = D·∇²C using explicit finite difference

        Args:
            concentration: Current concentration field [num_points]
            concentration_new: Updated concentration field [num_points]
            dt: Time step (s)
            num_points: Number of grid points
        """
        if self.grid_indices is None:
            raise RuntimeError("Grid not initialized. Call initialize_grid() first.")

        # Check stability
        if not self.check_stability(dt):
            dt_max = self.get_max_stable_timestep()
            print(f"Warning: dt={dt:.3f}s exceeds stability limit {dt_max:.3f}s")
            print(f"  Diffusion may be unstable. Consider reducing timestep.")

        # Launch kernel
        wp.launch(
            kernel=compute_diffusion_3d_structured,
            dim=num_points,
            inputs=[
                concentration,
                concentration_new,
                self.grid_indices,
                self.nx,
                self.ny,
                self.nz,
                self.D,
                self.dx,
                self.dy,
                self.dz,
                dt,
                num_points
            ]
        )

    def identify_surface_points(
        self,
        grid_points: np.ndarray,
        food_mesh_points: np.ndarray,
        threshold_distance: float = None
    ) -> np.ndarray:
        """
        Identify which grid points are on or near the food surface

        Surface points are those within a threshold distance of the mesh boundary.

        Args:
            grid_points: Internal grid point positions [num_points, 3]
            food_mesh_points: Mesh vertex positions [num_vertices, 3]
            threshold_distance: Distance threshold (m). If None, uses max(dx,dy,dz)

        Returns:
            Array of 0/1 indicating surface points [num_points]
        """
        if threshold_distance is None:
            threshold_distance = max(self.dx, self.dy, self.dz)

        num_points = len(grid_points)
        is_surface = np.zeros(num_points, dtype=np.int32)

        # Simple approach: Mark points near any mesh vertex
        # More sophisticated: Use distance to mesh surface
        for i in range(num_points):
            point = grid_points[i]

            # Find minimum distance to any mesh vertex
            distances = np.linalg.norm(food_mesh_points - point, axis=1)
            min_dist = np.min(distances)

            if min_dist <= threshold_distance:
                is_surface[i] = 1

        num_surface = np.sum(is_surface)
        print(f"\nSurface identification:")
        print(f"  - Threshold: {threshold_distance*1000:.2f}mm")
        print(f"  - Surface points: {num_surface}/{num_points} ({100*num_surface/num_points:.1f}%)")

        return is_surface

    def apply_leaching(
        self,
        concentration: wp.array,
        grid_points: wp.array,
        is_surface_point: wp.array,
        mass_transfer_coeff: float,
        water_concentration: float,
        partition_coefficient: float,
        dt: float,
        num_points: int
    ):
        """
        Apply surface leaching to nutrients at food-water interface

        Args:
            concentration: Nutrient concentration field [num_points]
            grid_points: Grid point positions [num_points]
            is_surface_point: Surface indicator array [num_points]
            mass_transfer_coeff: k_m (m/s), typically ~1e-5 m/s
            water_concentration: C_water (μg/m³)
            partition_coefficient: K (dimensionless), typically 0.1-10
            dt: Time step (s)
            num_points: Number of grid points
        """
        wp.launch(
            kernel=apply_surface_leaching,
            dim=num_points,
            inputs=[
                concentration,
                grid_points,
                is_surface_point,
                mass_transfer_coeff,
                water_concentration,
                partition_coefficient,
                dt,
                num_points
            ]
        )

    def step_with_leaching(
        self,
        concentration: wp.array,
        concentration_new: wp.array,
        grid_points: wp.array,
        is_surface_point: wp.array,
        dt: float,
        num_points: int,
        mass_transfer_coeff: float = 1e-5,
        water_concentration: float = 0.0,
        partition_coefficient: float = 1.0
    ):
        """
        Combined diffusion + surface leaching step

        1. Compute internal diffusion
        2. Apply surface leaching boundary condition

        Args:
            concentration: Current concentration [num_points]
            concentration_new: Updated concentration [num_points]
            grid_points: Grid positions [num_points]
            is_surface_point: Surface indicator [num_points]
            dt: Time step (s)
            num_points: Number of points
            mass_transfer_coeff: k_m (m/s)
            water_concentration: C_water (μg/m³)
            partition_coefficient: K (dimensionless)
        """
        # Step 1: Internal diffusion
        self.step(concentration, concentration_new, dt, num_points)

        # Step 2: Surface leaching
        self.apply_leaching(
            concentration_new,
            grid_points,
            is_surface_point,
            mass_transfer_coeff,
            water_concentration,
            partition_coefficient,
            dt,
            num_points
        )

    def get_adaptive_timestep(
        self,
        current_dt: float,
        target_dt: float,
        safety_factor: float = 0.8
    ) -> float:
        """
        Calculate adaptive timestep for diffusion stability

        Uses CFL condition with safety margin to ensure stable integration.

        Args:
            current_dt: Current timestep (s)
            target_dt: Desired timestep for other physics (s)
            safety_factor: Safety margin (0-1), default 0.8

        Returns:
            Recommended timestep (s)
        """
        # Maximum stable timestep from CFL condition
        dt_max = self.get_max_stable_timestep() * safety_factor

        # If target timestep is stable, use it
        if target_dt <= dt_max:
            return target_dt

        # Otherwise, suggest stable substeps
        num_substeps = int(np.ceil(target_dt / dt_max))
        dt_substep = target_dt / num_substeps

        print(f"\nAdaptive timestepping:")
        print(f"  - Target dt: {target_dt:.3f}s")
        print(f"  - Max stable dt: {dt_max:.3f}s")
        print(f"  - Recommended: {num_substeps} substeps of {dt_substep:.3f}s")

        return dt_substep

    def step_adaptive(
        self,
        concentration: wp.array,
        concentration_new: wp.array,
        target_dt: float,
        num_points: int,
        safety_factor: float = 0.8
    ) -> int:
        """
        Diffusion step with adaptive substepping for stability

        Args:
            concentration: Current concentration
            concentration_new: Updated concentration
            target_dt: Target timestep (s)
            num_points: Number of points
            safety_factor: CFL safety factor

        Returns:
            Number of substeps taken
        """
        # Calculate stable substep size
        dt_max = self.get_max_stable_timestep() * safety_factor

        if target_dt <= dt_max:
            # Single step is stable
            self.step(concentration, concentration_new, target_dt, num_points)
            return 1

        # Multiple substeps needed
        num_substeps = int(np.ceil(target_dt / dt_max))
        dt_substep = target_dt / num_substeps

        # Perform substeps
        for substep in range(num_substeps):
            self.step(concentration, concentration_new, dt_substep, num_points)
            # Swap buffers for next substep
            concentration, concentration_new = concentration_new, concentration

        return num_substeps

"""
Nutrient diffusion model
"""

import warp as wp
import numpy as np


@wp.kernel
def compute_diffusion_3d(
    concentration: wp.array(dtype=float),
    concentration_new: wp.array(dtype=float),
    diffusion_coefficient: float,
    dx: float,
    dy: float,
    dz: float,
    dt: float,
    num_points: int
):
    """
    Compute 3D diffusion using finite difference method
    ∂C/∂t = D·∇²C

    Args:
        concentration: Current concentration field
        concentration_new: Updated concentration field
        diffusion_coefficient: D (m²/s)
        dx, dy, dz: Grid spacing (m)
        dt: Time step (s)
        num_points: Number of grid points
    """
    tid = wp.tid()

    if tid >= num_points:
        return

    C_curr = concentration[tid]

    # TODO: Implement proper 3D diffusion with neighbor lookup
    # For now, placeholder

    # Stability criterion: dt < dx²/(6·D) for 3D
    laplacian = 0.0

    # Update using explicit Euler
    # C_new = C_old + D·dt·∇²C
    concentration_new[tid] = C_curr + diffusion_coefficient * dt * laplacian


class NutrientDiffusion:
    """Nutrient diffusion in food matrix"""

    def __init__(self, diffusion_coefficient: float = 1e-10):
        """
        Initialize diffusion model

        Args:
            diffusion_coefficient: D in m²/s
        """
        self.D = diffusion_coefficient

    def check_stability(self, dx: float, dt: float) -> bool:
        """
        Check if time step satisfies stability criterion
        For explicit scheme in 3D: dt < dx²/(6·D)

        Args:
            dx: Grid spacing (m)
            dt: Time step (s)

        Returns:
            True if stable, False otherwise
        """
        dt_max = dx * dx / (6 * self.D)
        return dt <= dt_max

    def get_max_stable_timestep(self, dx: float) -> float:
        """
        Get maximum stable time step

        Args:
            dx: Grid spacing (m)

        Returns:
            Maximum dt (s)
        """
        return dx * dx / (6 * self.D)

    def step(
        self,
        concentration: wp.array,
        concentration_new: wp.array,
        dx: float,
        dt: float,
        num_points: int
    ):
        """
        Advance diffusion simulation by one time step

        Args:
            concentration: Current concentration field
            concentration_new: Updated concentration field
            dx: Grid spacing (m)
            dt: Time step (s)
            num_points: Number of grid points
        """
        # Check stability
        if not self.check_stability(dx, dt):
            dt_max = self.get_max_stable_timestep(dx)
            print(f"Warning: dt={dt}s exceeds stability limit {dt_max}s")

        wp.launch(
            kernel=compute_diffusion_3d,
            dim=num_points,
            inputs=[
                concentration,
                concentration_new,
                self.D,
                dx,
                dx,
                dx,
                dt,
                num_points
            ]
        )

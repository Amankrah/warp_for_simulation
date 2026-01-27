"""
Statistical analysis module for spray drift patterns
"""

import numpy as np
from typing import Dict, Tuple, Optional
import pandas as pd
from pathlib import Path


class DriftAnalyzer:
    """
    Analyze spray drift patterns and compute statistics
    """

    def __init__(self, nozzle_position: Tuple[float, float, float]):
        self.nozzle_pos = np.array(nozzle_position)

    def analyze_deposition(
        self,
        deposition_positions: np.ndarray,
        deposition_mask: np.ndarray,
        diameters: np.ndarray,
        masses: np.ndarray,
        concentration: float
    ) -> Dict[str, float]:
        """
        Analyze deposition pattern

        Args:
            deposition_positions: (N, 3) deposition positions
            deposition_mask: (N,) boolean mask for deposited droplets
            diameters: (N,) droplet diameters
            masses: (N,) droplet masses
            concentration: Active ingredient concentration (g/L)

        Returns:
            Dictionary of statistics
        """
        if not np.any(deposition_mask):
            return {
                'total_deposited': 0,
                'deposition_fraction': 0.0,
                'mean_drift_distance': 0.0,
                'max_drift_distance': 0.0,
                'std_drift_distance': 0.0,
                'deposited_mass_kg': 0.0,
                'deposited_ai_kg': 0.0
            }

        dep_pos = deposition_positions[deposition_mask]
        dep_diam = diameters[deposition_mask]
        dep_mass = masses[deposition_mask]

        # Number deposited
        n_deposited = len(dep_pos)
        n_total = len(deposition_mask)

        # Drift distances (horizontal)
        drift_vectors = dep_pos[:, :2] - self.nozzle_pos[:2]
        drift_distances = np.sqrt(np.sum(drift_vectors**2, axis=1))

        # Mass deposited
        total_mass_kg = np.sum(dep_mass)
        total_ai_kg = total_mass_kg * concentration / 1000.0  # concentration in g/L

        stats = {
            'total_deposited': n_deposited,
            'deposition_fraction': n_deposited / n_total,
            'mean_drift_distance': float(np.mean(drift_distances)),
            'max_drift_distance': float(np.max(drift_distances)),
            'std_drift_distance': float(np.std(drift_distances)),
            'median_drift_distance': float(np.median(drift_distances)),
            'deposited_mass_kg': float(total_mass_kg),
            'deposited_ai_kg': float(total_ai_kg),
            'mean_deposited_diameter_um': float(np.mean(dep_diam) * 1e6),
            'std_deposited_diameter_um': float(np.std(dep_diam) * 1e6)
        }

        return stats

    def analyze_loss(
        self,
        deposition_time: np.ndarray,
        active: np.ndarray,
        masses: np.ndarray
    ) -> Dict[str, float]:
        """
        Analyze losses (evaporation, drift out of domain)

        Args:
            deposition_time: (N,) deposition times (-1 = lost to drift)
            active: (N,) active status
            masses: (N,) current masses

        Returns:
            Dictionary of loss statistics
        """
        n_total = len(deposition_time)

        # Lost to drift (out of domain)
        drift_lost_mask = deposition_time < 0
        n_drift_lost = np.sum(drift_lost_mask)

        # Evaporated completely (active=0 but deposition_time=0)
        evaporated_mask = (active == 0) & (deposition_time == 0)
        n_evaporated = np.sum(evaporated_mask)

        # Still airborne
        n_airborne = np.sum(active > 0)

        stats = {
            'n_drift_lost': int(n_drift_lost),
            'n_evaporated': int(n_evaporated),
            'n_airborne': int(n_airborne),
            'fraction_drift_lost': n_drift_lost / n_total,
            'fraction_evaporated': n_evaporated / n_total,
            'fraction_airborne': n_airborne / n_total
        }

        return stats

    def compute_coverage_efficiency(
        self,
        deposition_positions: np.ndarray,
        deposition_mask: np.ndarray,
        target_area: Tuple[float, float, float, float]  # (x_min, x_max, y_min, y_max)
    ) -> Dict[str, float]:
        """
        Compute spray coverage efficiency in target area

        Args:
            deposition_positions: (N, 3) deposition positions
            deposition_mask: (N,) boolean mask
            target_area: Target coverage area bounds

        Returns:
            Coverage statistics
        """
        if not np.any(deposition_mask):
            return {
                'n_in_target': 0,
                'n_out_target': 0,
                'target_efficiency': 0.0
            }

        dep_pos = deposition_positions[deposition_mask]

        # Check which droplets are in target
        x_min, x_max, y_min, y_max = target_area
        in_target = (
            (dep_pos[:, 0] >= x_min) & (dep_pos[:, 0] <= x_max) &
            (dep_pos[:, 1] >= y_min) & (dep_pos[:, 1] <= y_max)
        )

        n_in = np.sum(in_target)
        n_out = len(dep_pos) - n_in

        stats = {
            'n_in_target': int(n_in),
            'n_out_target': int(n_out),
            'target_efficiency': n_in / len(dep_pos) if len(dep_pos) > 0 else 0.0
        }

        return stats

    def generate_report(
        self,
        state: Dict,
        deposition_stats: Dict,
        loss_stats: Dict,
        coverage_stats: Optional[Dict] = None,
        save_path: Optional[str] = None
    ) -> str:
        """
        Generate text report of simulation results

        Args:
            state: Final state dictionary
            deposition_stats: Deposition statistics
            loss_stats: Loss statistics
            coverage_stats: Optional coverage statistics
            save_path: Optional path to save report

        Returns:
            Report as string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("AGRIDRIFT SIMULATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Deposition
        lines.append("DEPOSITION STATISTICS")
        lines.append("-" * 60)
        lines.append(f"Total droplets simulated: {len(state['active'])}")
        lines.append(f"Droplets deposited: {deposition_stats['total_deposited']}")
        lines.append(f"Deposition fraction: {deposition_stats['deposition_fraction']:.2%}")
        lines.append(f"Mean drift distance: {deposition_stats['mean_drift_distance']:.2f} m")
        lines.append(f"Max drift distance: {deposition_stats['max_drift_distance']:.2f} m")
        lines.append(f"Std drift distance: {deposition_stats['std_drift_distance']:.2f} m")
        lines.append(f"Deposited mass: {deposition_stats['deposited_mass_kg']*1000:.2f} g")
        lines.append(f"Deposited AI: {deposition_stats['deposited_ai_kg']*1000:.2f} g")
        lines.append("")

        # Losses
        lines.append("LOSS STATISTICS")
        lines.append("-" * 60)
        lines.append(f"Lost to drift (out of domain): {loss_stats['n_drift_lost']} ({loss_stats['fraction_drift_lost']:.2%})")
        lines.append(f"Evaporated: {loss_stats['n_evaporated']} ({loss_stats['fraction_evaporated']:.2%})")
        lines.append(f"Still airborne: {loss_stats['n_airborne']} ({loss_stats['fraction_airborne']:.2%})")
        lines.append("")

        # Coverage (if provided)
        if coverage_stats:
            lines.append("COVERAGE EFFICIENCY")
            lines.append("-" * 60)
            lines.append(f"Droplets in target area: {coverage_stats['n_in_target']}")
            lines.append(f"Droplets outside target: {coverage_stats['n_out_target']}")
            lines.append(f"Target efficiency: {coverage_stats['target_efficiency']:.2%}")
            lines.append("")

        # Droplet characteristics
        lines.append("DROPLET CHARACTERISTICS")
        lines.append("-" * 60)
        lines.append(f"Mean deposited diameter: {deposition_stats['mean_deposited_diameter_um']:.1f} μm")
        lines.append(f"Std deposited diameter: {deposition_stats['std_deposited_diameter_um']:.1f} μm")
        lines.append("")

        lines.append("=" * 60)

        report = "\n".join(lines)

        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def export_to_csv(
        self,
        state: Dict,
        save_path: str
    ):
        """
        Export final state to CSV for further analysis

        Args:
            state: State dictionary
            save_path: Path to save CSV
        """
        # Create DataFrame
        df = pd.DataFrame({
            'x': state['positions'][:, 0],
            'y': state['positions'][:, 1],
            'z': state['positions'][:, 2],
            'diameter_um': state['diameters'] * 1e6,
            'mass_kg': state['masses'],
            'active': state['active'],
            'deposition_time_s': state['deposition_time'],
            'deposition_x': state['deposition_position'][:, 0],
            'deposition_y': state['deposition_position'][:, 1],
            'deposition_z': state['deposition_position'][:, 2]
        })

        # Add computed fields
        drift_dist = np.sqrt(
            state['deposition_position'][:, 0]**2 +
            state['deposition_position'][:, 1]**2
        )
        df['drift_distance_m'] = drift_dist

        # Status
        status = np.where(
            state['active'] > 0,
            'airborne',
            np.where(
                state['deposition_time'] < 0,
                'drift_lost',
                np.where(
                    state['deposition_time'] == 0,
                    'evaporated',
                    'deposited'
                )
            )
        )
        df['status'] = status

        # Save
        df.to_csv(save_path, index=False)
        print(f"Data exported to {save_path}")

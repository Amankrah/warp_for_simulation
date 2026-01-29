"""
Analysis and visualization tools for air classifier simulation
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional, Tuple
from pathlib import Path


def analyze_separation(results: Dict, particle_types: np.ndarray) -> Dict:
    """
    Analyze separation efficiency and product quality

    Args:
        results: Simulation results dictionary
        particle_types: Array of particle types (0=protein, 1=starch)

    Returns:
        Dictionary with separation metrics
    """
    final_state = results['final_state']

    # Count particles by type
    n_protein_total = np.sum(particle_types == 0)
    n_starch_total = np.sum(particle_types == 1)
    n_total = len(particle_types)

    # Identify collected particles
    collection_times = final_state['collection_time']
    collected_mask = collection_times > 0

    # Separate by collection type: use outlet if available, else infer from position
    if 'collection_outlet' in final_state:
        # Use actual outlet (1=fine, 2=coarse) for correct purity/recovery
        outlet = final_state['collection_outlet']
        fine_mask = collected_mask & (outlet == 1)
        coarse_mask = collected_mask & (outlet == 2)
    else:
        # Fallback: infer from collection position z (fine threshold 1.0m, coarse 0.1m)
        collection_pos = final_state['collection_position']
        fine_mask = collected_mask & (collection_pos[:, 2] > 0.55)
        coarse_mask = collected_mask & (collection_pos[:, 2] <= 0.55)

    # Count by type in each fraction
    protein_to_fine = np.sum(fine_mask & (particle_types == 0))
    starch_to_fine = np.sum(fine_mask & (particle_types == 1))

    protein_to_coarse = np.sum(coarse_mask & (particle_types == 0))
    starch_to_coarse = np.sum(coarse_mask & (particle_types == 1))

    # Totals: use simulator counts when available so reported totals match simulator
    if 'collection_outlet' in final_state:
        n_fine = int(final_state.get('collected_fine', protein_to_fine + starch_to_fine))
        n_coarse = int(final_state.get('collected_coarse', protein_to_coarse + starch_to_coarse))
        # Ensure we have at least mask-based counts for composition
        n_fine_from_mask = protein_to_fine + starch_to_fine
        n_coarse_from_mask = protein_to_coarse + starch_to_coarse
        if n_fine_from_mask > 0 and n_fine_from_mask != n_fine:
            # Use mask totals for purity calculation when they differ
            n_fine_for_purity = n_fine_from_mask
        else:
            n_fine_for_purity = n_fine
        if n_coarse_from_mask > 0 and n_coarse_from_mask != n_coarse:
            n_coarse_for_purity = n_coarse_from_mask
        else:
            n_coarse_for_purity = n_coarse
    else:
        n_fine = protein_to_fine + starch_to_fine
        n_coarse = protein_to_coarse + starch_to_coarse
        n_fine_for_purity = n_fine
        n_coarse_for_purity = n_coarse

    # Purities (use purity counts which may differ from totals if outlet mask incomplete)
    protein_purity_fine = protein_to_fine / n_fine_for_purity if n_fine_for_purity > 0 else 0
    starch_purity_coarse = starch_to_coarse / n_coarse_for_purity if n_coarse_for_purity > 0 else 0

    # Recovery
    protein_recovery = protein_to_fine / n_protein_total if n_protein_total > 0 else 0

    # Yield
    fine_yield = n_fine / n_total

    # Calculate cut size from particle size distribution
    diameters = final_state['diameters']
    fine_diameters = diameters[fine_mask]
    coarse_diameters = diameters[coarse_mask]

    if len(fine_diameters) > 0 and len(coarse_diameters) > 0:
        # Rough estimate of d50
        d50_estimate = np.mean([np.max(fine_diameters), np.min(coarse_diameters)])
    else:
        d50_estimate = 0

    analysis = {
        'total_particles': n_total,
        'protein_particles': n_protein_total,
        'starch_particles': n_starch_total,
        'fine_collected': n_fine,
        'coarse_collected': n_coarse,
        'protein_to_fine': protein_to_fine,
        'starch_to_fine': starch_to_fine,
        'protein_to_coarse': protein_to_coarse,
        'starch_to_coarse': starch_to_coarse,
        'protein_purity_fine': protein_purity_fine * 100,
        'starch_purity_coarse': starch_purity_coarse * 100,
        'protein_recovery': protein_recovery * 100,
        'fine_yield': fine_yield * 100,
        'd50_estimate': d50_estimate * 1e6,  # Convert to μm
    }

    return analysis


def print_separation_report(analysis: Dict):
    """Print formatted separation analysis report"""
    print("\n" + "=" * 60)
    print("SEPARATION ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nParticle Counts:")
    print(f"  Total particles:     {analysis['total_particles']:,}")
    print(f"  Protein particles:   {analysis['protein_particles']:,}")
    print(f"  Starch particles:    {analysis['starch_particles']:,}")

    print(f"\nCollection:")
    print(f"  Fine fraction:       {analysis['fine_collected']:,} particles")
    print(f"  Coarse fraction:     {analysis['coarse_collected']:,} particles")

    print(f"\nFine Fraction Composition:")
    print(f"  Protein:             {analysis['protein_to_fine']:,} particles")
    print(f"  Starch:              {analysis['starch_to_fine']:,} particles")
    print(f"  Protein purity:      {analysis['protein_purity_fine']:.1f}%")

    print(f"\nCoarse Fraction Composition:")
    print(f"  Protein:             {analysis['protein_to_coarse']:,} particles")
    print(f"  Starch:              {analysis['starch_to_coarse']:,} particles")
    print(f"  Starch purity:       {analysis['starch_purity_coarse']:.1f}%")

    print(f"\nPerformance Metrics:")
    print(f"  Protein recovery:    {analysis['protein_recovery']:.1f}%")
    print(f"  Fine fraction yield: {analysis['fine_yield']:.1f}%")
    print(f"  Cut size (d50):      {analysis['d50_estimate']:.1f} μm")

    print("=" * 60 + "\n")


def plot_particle_trajectories(
    results: Dict,
    particle_types: np.ndarray,
    classifier_config,
    max_particles: int = 500,
    save_path: Optional[str] = None
):
    """
    Plot particle trajectories in 2D (side view and top view)
    """
    final_state = results['final_state']
    positions = final_state['positions']
    active = final_state['active']

    # Sample particles for visualization
    n_particles = min(len(positions), max_particles)
    indices = np.random.choice(len(positions), n_particles, replace=False)

    protein_mask = particle_types[indices] == 0
    starch_mask = particle_types[indices] == 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Side view (X-Z plane)
    ax1.scatter(
        positions[indices[protein_mask], 0],
        positions[indices[protein_mask], 2],
        c='blue', s=2, alpha=0.6, label='Protein'
    )
    ax1.scatter(
        positions[indices[starch_mask], 0],
        positions[indices[starch_mask], 2],
        c='orange', s=3, alpha=0.6, label='Starch'
    )

    # Draw chamber
    ax1.axvline(x=-classifier_config.chamber_radius, color='k', linestyle='--', alpha=0.3)
    ax1.axvline(x=classifier_config.chamber_radius, color='k', linestyle='--', alpha=0.3)
    ax1.axhline(y=0, color='green', linewidth=2, alpha=0.5, label='Ground')
    ax1.axhline(y=classifier_config.chamber_height, color='k', linestyle='--', alpha=0.3)

    # Draw classifier wheel
    wheel_rect = plt.Rectangle(
        (-classifier_config.wheel_radius,
         classifier_config.wheel_position_z - classifier_config.wheel_width/2),
        classifier_config.wheel_radius * 2,
        classifier_config.wheel_width,
        color='red', alpha=0.3, label='Classifier Wheel'
    )
    ax1.add_patch(wheel_rect)

    ax1.set_xlabel('X Position (m)')
    ax1.set_ylabel('Z Position (m)')
    ax1.set_title('Side View (X-Z Plane)')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # Top view (X-Y plane)
    ax2.scatter(
        positions[indices[protein_mask], 0],
        positions[indices[protein_mask], 1],
        c='blue', s=2, alpha=0.6, label='Protein'
    )
    ax2.scatter(
        positions[indices[starch_mask], 0],
        positions[indices[starch_mask], 1],
        c='orange', s=3, alpha=0.6, label='Starch'
    )

    # Draw chamber circle
    circle = plt.Circle((0, 0), classifier_config.chamber_radius,
                        fill=False, color='k', linestyle='--', alpha=0.3)
    ax2.add_patch(circle)

    # Draw wheel circle
    wheel_circle = plt.Circle((0, 0), classifier_config.wheel_radius,
                             fill=False, color='red', linewidth=2, alpha=0.5,
                             label='Classifier Wheel')
    ax2.add_patch(wheel_circle)

    ax2.set_xlabel('X Position (m)')
    ax2.set_ylabel('Y Position (m)')
    ax2.set_title('Top View (X-Y Plane)')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved trajectory plot to {save_path}")

    plt.show()


def plot_size_distributions(
    final_state: Dict,
    particle_types: np.ndarray,
    save_path: Optional[str] = None
):
    """Plot particle size distributions for feed and products"""
    diameters = final_state['diameters'] * 1e6  # Convert to μm
    collection_times = final_state['collection_time']
    collected_mask = collection_times > 0

    # Separate by collection type (use outlet if available)
    if 'collection_outlet' in final_state:
        outlet = final_state['collection_outlet']
        fine_mask = collected_mask & (outlet == 1)
        coarse_mask = collected_mask & (outlet == 2)
    else:
        collection_pos = final_state['collection_position']
        fine_mask = collected_mask & (collection_pos[:, 2] > 0.5)
        coarse_mask = collected_mask & (collection_pos[:, 2] <= 0.1)

    protein_mask = particle_types == 0
    starch_mask = particle_types == 1

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Feed distribution
    bins = np.linspace(0, 60, 60)
    axes[0, 0].hist(diameters[protein_mask], bins=bins, alpha=0.7,
                    label='Protein', color='blue', density=True)
    axes[0, 0].hist(diameters[starch_mask], bins=bins, alpha=0.7,
                    label='Starch', color='orange', density=True)
    axes[0, 0].set_xlabel('Particle Diameter (μm)')
    axes[0, 0].set_ylabel('Probability Density')
    axes[0, 0].set_title('Feed Particle Size Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axvline(x=20, color='red', linestyle='--', label='Target d50')

    # Fine fraction
    if np.sum(fine_mask) > 0:
        axes[0, 1].hist(diameters[fine_mask & protein_mask], bins=bins, alpha=0.7,
                       label='Protein', color='blue', density=True)
        axes[0, 1].hist(diameters[fine_mask & starch_mask], bins=bins, alpha=0.7,
                       label='Starch', color='orange', density=True)
    axes[0, 1].set_xlabel('Particle Diameter (μm)')
    axes[0, 1].set_ylabel('Probability Density')
    axes[0, 1].set_title('Fine Fraction (Protein-Rich)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Coarse fraction
    if np.sum(coarse_mask) > 0:
        axes[1, 0].hist(diameters[coarse_mask & protein_mask], bins=bins, alpha=0.7,
                       label='Protein', color='blue', density=True)
        axes[1, 0].hist(diameters[coarse_mask & starch_mask], bins=bins, alpha=0.7,
                       label='Starch', color='orange', density=True)
    axes[1, 0].set_xlabel('Particle Diameter (μm)')
    axes[1, 0].set_ylabel('Probability Density')
    axes[1, 0].set_title('Coarse Fraction (Starch-Rich)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Cumulative distribution
    if np.sum(fine_mask) > 0 and np.sum(coarse_mask) > 0:
        fine_sorted = np.sort(diameters[fine_mask])
        coarse_sorted = np.sort(diameters[coarse_mask])

        axes[1, 1].plot(
            fine_sorted,
            np.arange(len(fine_sorted)) / len(fine_sorted) * 100,
            'b-', linewidth=2, label='Fine Fraction'
        )
        axes[1, 1].plot(
            coarse_sorted,
            np.arange(len(coarse_sorted)) / len(coarse_sorted) * 100,
            'orange', linewidth=2, label='Coarse Fraction'
        )
        axes[1, 1].axhline(y=50, color='gray', linestyle=':', alpha=0.5)
        axes[1, 1].axvline(x=20, color='red', linestyle='--', alpha=0.5)

    axes[1, 1].set_xlabel('Particle Diameter (μm)')
    axes[1, 1].set_ylabel('Cumulative %')
    axes[1, 1].set_title('Cumulative Size Distribution')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved size distribution plot to {save_path}")

    plt.show()


def plot_collection_dynamics(results: Dict, save_path: Optional[str] = None):
    """Plot how particles are collected over time"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    times = np.array(results['time'])
    fine = np.array(results['fine_collected'])
    coarse = np.array(results['coarse_collected'])
    active = np.array(results['active_count'])

    # Collection over time
    ax1.plot(times, fine, 'b-', linewidth=2, label='Fine Fraction', marker='o')
    ax1.plot(times, coarse, 'orange', linewidth=2, label='Coarse Fraction', marker='s')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Particles Collected')
    ax1.set_title('Particle Collection Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Active particles
    ax2.plot(times, active, 'g-', linewidth=2, marker='d')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Active Particles')
    ax2.set_title('Active Particles in Classifier')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved collection dynamics plot to {save_path}")

    plt.show()


def calculate_grade_efficiency(
    results: Dict,
    particle_types: np.ndarray,
    n_bins: int = 30
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Calculate grade efficiency (Tromp) curve

    Grade efficiency T(d) = fraction of particles of size d reporting to coarse fraction

    Reference: Engineering Guide §2.3.1

    Args:
        results: Simulation results
        particle_types: Particle type array
        n_bins: Number of size bins for analysis

    Returns:
        Tuple of (bin_centers, grade_efficiency, metrics_dict)
    """
    final_state = results['final_state']
    diameters = final_state['diameters'] * 1e6  # Convert to μm
    collection_times = final_state['collection_time']
    collected_mask = collection_times > 0

    # Identify fine and coarse fractions (use outlet if available)
    if 'collection_outlet' in final_state:
        outlet = final_state['collection_outlet']
        fine_mask = collected_mask & (outlet == 1)
        coarse_mask = collected_mask & (outlet == 2)
    else:
        collection_pos = final_state['collection_position']
        fine_mask = collected_mask & (collection_pos[:, 2] > 0.5)
        coarse_mask = collected_mask & (collection_pos[:, 2] <= 0.1)

    # Create logarithmic size bins
    d_min, d_max = 1, 60  # μm
    bins = np.logspace(np.log10(d_min), np.log10(d_max), n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    # Count particles in each bin for feed, fine, and coarse
    feed_counts, _ = np.histogram(diameters[collected_mask], bins=bins)
    coarse_counts, _ = np.histogram(diameters[coarse_mask], bins=bins)

    # Grade efficiency: fraction reporting to coarse
    # T(d) = (mass_coarse at size d) / (mass_feed at size d)
    with np.errstate(divide='ignore', invalid='ignore'):
        grade_efficiency = coarse_counts / feed_counts * 100
        grade_efficiency = np.nan_to_num(grade_efficiency, nan=50.0)

    # Calculate d50 (cut size where efficiency = 50%)
    try:
        idx_50 = np.argmin(np.abs(grade_efficiency - 50))
        d50 = bin_centers[idx_50]
    except:
        d50 = np.nan

    # Calculate d25 and d75 for sharpness index
    try:
        idx_25 = np.argmin(np.abs(grade_efficiency - 25))
        idx_75 = np.argmin(np.abs(grade_efficiency - 75))
        d25 = bin_centers[idx_25]
        d75 = bin_centers[idx_75]
        kappa = d75 / d25  # Sharpness index
    except:
        d25, d75, kappa = np.nan, np.nan, np.nan

    # Classify sharpness quality
    if np.isnan(kappa):
        sharpness_quality = "Unable to calculate"
    elif kappa < 1.5:
        sharpness_quality = "Excellent (κ < 1.5)"
    elif kappa < 2.0:
        sharpness_quality = "Good (κ < 2.0)"
    elif kappa < 3.0:
        sharpness_quality = "Acceptable (κ < 3.0)"
    else:
        sharpness_quality = "Poor (κ > 3.0)"

    metrics = {
        'd50': d50,
        'd25': d25,
        'd75': d75,
        'kappa': kappa,
        'sharpness_quality': sharpness_quality,
        'bin_centers': bin_centers,
        'grade_efficiency': grade_efficiency,
        'feed_counts': feed_counts,
        'coarse_counts': coarse_counts
    }

    return bin_centers, grade_efficiency, metrics


def plot_grade_efficiency_curve(
    bin_centers: np.ndarray,
    grade_efficiency: np.ndarray,
    metrics: Dict,
    target_d50: float = 20.0,
    save_path: Optional[str] = None
):
    """
    Plot grade efficiency (Tromp) curve

    Reference: Engineering Guide §2.3.1

    Args:
        bin_centers: Particle size bin centers (μm)
        grade_efficiency: Grade efficiency values (%)
        metrics: Dictionary with d50, d25, d75, kappa
        target_d50: Target cut size for reference (μm)
        save_path: Path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot grade efficiency
    ax.semilogx(bin_centers, grade_efficiency, 'bo-', markersize=6, linewidth=2,
                label='Measured Grade Efficiency')

    # Reference lines
    ax.axhline(y=50, color='red', linestyle='--', linewidth=2, label='50% (cut point)')
    ax.axhline(y=25, color='gray', linestyle=':', alpha=0.5, linewidth=1)
    ax.axhline(y=75, color='gray', linestyle=':', alpha=0.5, linewidth=1)

    # Mark d50, d25, d75
    if not np.isnan(metrics['d50']):
        ax.axvline(x=metrics['d50'], color='green', linestyle='--', alpha=0.7, linewidth=2)
        ax.text(metrics['d50'] * 1.15, 55, f"d₅₀ = {metrics['d50']:.1f} μm",
                fontsize=11, color='green', fontweight='bold')

    if not np.isnan(metrics['d25']) and not np.isnan(metrics['d75']):
        ax.axvline(x=metrics['d25'], color='purple', linestyle=':', alpha=0.5)
        ax.axvline(x=metrics['d75'], color='purple', linestyle=':', alpha=0.5)
        ax.text(metrics['d25'] * 0.7, 28, f"d₂₅", fontsize=9, color='purple')
        ax.text(metrics['d75'] * 1.05, 78, f"d₇₅", fontsize=9, color='purple')

    # Target cut size
    if target_d50:
        ax.axvline(x=target_d50, color='orange', linestyle='-.', alpha=0.5, linewidth=1.5,
                  label=f'Target d₅₀ = {target_d50} μm')

    ax.set_xlabel('Particle Diameter (μm)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Grade Efficiency (%)', fontsize=13, fontweight='bold')
    ax.set_title('Classification Grade Efficiency Curve (Tromp Curve)',
                fontsize=14, fontweight='bold')
    ax.set_xlim([1, 60])
    ax.set_ylim([0, 100])
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(loc='upper left', fontsize=10)

    # Add text box with metrics
    if not np.isnan(metrics['kappa']):
        textstr = f"Sharpness Index (κ): {metrics['kappa']:.2f}\n" + \
                  f"Quality: {metrics['sharpness_quality']}\n" + \
                  f"d₂₅ = {metrics['d25']:.1f} μm\n" + \
                  f"d₅₀ = {metrics['d50']:.1f} μm\n" + \
                  f"d₇₅ = {metrics['d75']:.1f} μm"

        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.65, 0.30, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=props, family='monospace')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved grade efficiency curve to {save_path}")

    plt.show()


def print_grade_efficiency_report(metrics: Dict):
    """
    Print formatted grade efficiency report

    Args:
        metrics: Dictionary from calculate_grade_efficiency
    """
    print("\n" + "="*70)
    print(" GRADE EFFICIENCY ANALYSIS (TROMP CURVE)")
    print("="*70)

    print("\n1. CUT SIZE CHARACTERISTICS")
    print("-" * 70)
    print(f"  d₂₅ (25% to coarse):          {metrics['d25']:.2f} μm")
    print(f"  d₅₀ (50% to coarse):          {metrics['d50']:.2f} μm")
    print(f"  d₇₅ (75% to coarse):          {metrics['d75']:.2f} μm")

    print("\n2. SEPARATION SHARPNESS")
    print("-" * 70)
    print(f"  Sharpness Index (κ):          {metrics['kappa']:.2f}")
    print(f"  Quality Assessment:           {metrics['sharpness_quality']}")

    print("\n3. INDUSTRY STANDARDS (Guide §2.3.2)")
    print("-" * 70)
    print("  Ideal classifier:             κ = 1.0")
    print("  Good classifier:              κ < 2.0")
    print("  Poor classifier:              κ > 3.0")

    if not np.isnan(metrics['kappa']):
        if metrics['kappa'] < 2.0:
            print("\n  ✓ This classifier meets industry standards for good separation")
        elif metrics['kappa'] < 3.0:
            print("\n  ⚠ This classifier is acceptable but could be improved")
        else:
            print("\n  ✗ This classifier needs optimization to meet standards")

    print("\n" + "="*70 + "\n")


def calculate_economics(
    analysis: Dict,
    feed_rate_kg_hr: float = 200,
    operating_hours_year: float = 4000,
    flour_cost_per_kg: float = 0.80,
    protein_price_per_kg: float = 3.50,
    starch_price_per_kg: float = 0.60,
    capital_cost: float = 53300,
    operating_cost_annual: float = 32500
) -> Dict:
    """
    Calculate comprehensive economic metrics

    Reference: Engineering Guide §12

    Args:
        analysis: Separation analysis results
        feed_rate_kg_hr: Feed rate (kg/hr)
        operating_hours_year: Operating hours per year
        flour_cost_per_kg: Cost of feed flour ($/kg)
        protein_price_per_kg: Selling price of protein concentrate ($/kg)
        starch_price_per_kg: Selling price of starch fraction ($/kg)
        capital_cost: Total capital investment ($)
        operating_cost_annual: Annual operating costs ($)

    Returns:
        Dictionary with economic analysis
    """
    # Mass flow rates
    fine_yield_fraction = analysis['fine_yield'] / 100
    coarse_yield_fraction = 1 - fine_yield_fraction

    annual_feed = feed_rate_kg_hr * operating_hours_year  # kg/year
    annual_fine = annual_feed * fine_yield_fraction
    annual_coarse = annual_feed * coarse_yield_fraction

    # Revenue calculation
    # Fine fraction: protein concentrate pricing
    protein_purity_fine = analysis['protein_purity_fine'] / 100
    # Price scales with protein content (simplified model)
    fine_price = flour_cost_per_kg + (protein_price_per_kg - flour_cost_per_kg) * \
                 (protein_purity_fine - 0.23) / (0.60 - 0.23)

    # Coarse fraction: starch-rich, lower value
    coarse_price = starch_price_per_kg

    revenue_fine = annual_fine * fine_price
    revenue_coarse = annual_coarse * coarse_price
    total_revenue = revenue_fine + revenue_coarse

    # Costs
    raw_material_cost = annual_feed * flour_cost_per_kg
    total_cost = raw_material_cost + operating_cost_annual

    # Profitability
    gross_margin = total_revenue - total_cost
    gross_margin_pct = (gross_margin / total_revenue) * 100 if total_revenue > 0 else 0

    # Return on investment
    roi_pct = (gross_margin / capital_cost) * 100 if capital_cost > 0 else 0
    payback_years = capital_cost / gross_margin if gross_margin > 0 else float('inf')

    # Per tonne metrics
    feed_tonnes = annual_feed / 1000
    value_added_per_tonne = gross_margin / feed_tonnes if feed_tonnes > 0 else 0

    return {
        # Production volumes
        'annual_feed_tonnes': feed_tonnes,
        'annual_fine_tonnes': annual_fine / 1000,
        'annual_coarse_tonnes': annual_coarse / 1000,

        # Revenues
        'fine_price_per_kg': fine_price,
        'coarse_price_per_kg': coarse_price,
        'revenue_fine': revenue_fine,
        'revenue_coarse': revenue_coarse,
        'total_revenue': total_revenue,

        # Costs
        'raw_material_cost': raw_material_cost,
        'operating_cost': operating_cost_annual,
        'total_cost': total_cost,

        # Profitability
        'gross_margin': gross_margin,
        'gross_margin_pct': gross_margin_pct,
        'roi_pct': roi_pct,
        'payback_years': payback_years,
        'value_added_per_tonne': value_added_per_tonne,

        # Capital
        'capital_cost': capital_cost
    }


def print_economics_report(economics: Dict):
    """
    Print formatted economic analysis report

    Args:
        economics: Results from calculate_economics
    """
    print("\n" + "="*70)
    print(" ECONOMIC ANALYSIS REPORT")
    print("="*70)

    print("\n1. PRODUCTION VOLUMES")
    print("-" * 70)
    print(f"  Annual feed:                  {economics['annual_feed_tonnes']:.1f} tonnes")
    print(f"  Annual fine fraction:         {economics['annual_fine_tonnes']:.1f} tonnes")
    print(f"  Annual coarse fraction:       {economics['annual_coarse_tonnes']:.1f} tonnes")

    print("\n2. PRICING")
    print("-" * 70)
    print(f"  Fine fraction price:          ${economics['fine_price_per_kg']:.2f}/kg")
    print(f"  Coarse fraction price:        ${economics['coarse_price_per_kg']:.2f}/kg")

    print("\n3. REVENUES")
    print("-" * 70)
    print(f"  Fine fraction revenue:        ${economics['revenue_fine']:,.0f}")
    print(f"  Coarse fraction revenue:      ${economics['revenue_coarse']:,.0f}")
    print(f"  Total revenue:                ${economics['total_revenue']:,.0f}")

    print("\n4. COSTS")
    print("-" * 70)
    print(f"  Raw material cost:            ${economics['raw_material_cost']:,.0f}")
    print(f"  Operating cost:               ${economics['operating_cost']:,.0f}")
    print(f"  Total cost:                   ${economics['total_cost']:,.0f}")

    print("\n5. PROFITABILITY")
    print("-" * 70)
    print(f"  Gross margin:                 ${economics['gross_margin']:,.0f}")
    print(f"  Gross margin %:               {economics['gross_margin_pct']:.1f}%")
    print(f"  Value added per tonne:        ${economics['value_added_per_tonne']:.2f}")

    print("\n6. RETURN ON INVESTMENT")
    print("-" * 70)
    print(f"  Capital cost:                 ${economics['capital_cost']:,.0f}")
    print(f"  ROI:                          {economics['roi_pct']:.1f}%")
    if economics['payback_years'] < 10:
        print(f"  Payback period:               {economics['payback_years']:.2f} years")
    else:
        print(f"  Payback period:               >10 years")

    if economics['payback_years'] < 2:
        print("\n  ✓ Excellent investment - very fast payback")
    elif economics['payback_years'] < 5:
        print("\n  ✓ Good investment - acceptable payback")
    else:
        print("\n  ⚠ Marginal investment - consider optimization")

    print("\n" + "="*70)
    print(" Reference: Comprehensive Engineering Guide §12")
    print("="*70 + "\n")

"""
Industry Standard Validation Example

Demonstrates comprehensive validation of air classifier design
against engineering guide specifications and industry standards.

This example shows:
1. Design validation calculations
2. Simulation execution
3. Grade efficiency (Tromp curve) analysis
4. Economic analysis
5. Compliance reporting

Reference: Comprehensive Engineering Guide (all sections)
"""

import numpy as np
from pathlib import Path

from air_classifier import (
    # Configuration
    ClassifierConfig,
    ParticleProperties,
    SimulationConfig,
    get_default_config,

    # Simulator
    AirClassifierSimulator,

    # Analysis
    analyze_separation,
    print_separation_report,
    calculate_grade_efficiency,
    plot_grade_efficiency_curve,
    print_grade_efficiency_report,
    calculate_economics,
    print_economics_report,

    # Validation
    validate_classifier_design,
    print_validation_report
)


def run_complete_validation():
    """
    Run complete industry-standard validation workflow
    """
    print("\n" + "="*80)
    print(" AIR CLASSIFIER - INDUSTRY STANDARD VALIDATION")
    print(" Based on: Comprehensive Engineering Guide for Yellow Pea Protein Separation")
    print("="*80)

    # =========================================================================
    # STEP 1: DESIGN VALIDATION
    # =========================================================================
    print("\n" + "="*80)
    print(" STEP 1: THEORETICAL DESIGN VALIDATION")
    print("="*80)

    # Load default configuration
    config, particle_props, sim_config = get_default_config()

    # Validate design against theoretical calculations
    validation = validate_classifier_design(config, particle_props, sim_config)
    print_validation_report(validation, config, particle_props)

    # Check if design passes validation
    if not validation.tip_speed_ok:
        print("⚠ WARNING: Tip speed outside safe operating range!")
    if not validation.rpm_in_range:
        print("⚠ WARNING: RPM outside recommended range!")
    if not validation.separation_feasible:
        print("⚠ WARNING: Separation may be challenging with current parameters!")

    # =========================================================================
    # STEP 2: SIMULATION EXECUTION
    # =========================================================================
    print("\n" + "="*80)
    print(" STEP 2: GPU-ACCELERATED PARTICLE SIMULATION")
    print("="*80)

    # Adjust simulation for reasonable run time
    config.num_particles = 10000  # Reduced for faster demo
    sim_config.total_time = 1.5
    sim_config.output_interval = 0.05

    print(f"\nSimulation parameters:")
    print(f"  Particles: {config.num_particles:,}")
    print(f"  Duration: {sim_config.total_time} seconds")
    print(f"  Wheel RPM: {config.wheel_rpm}")
    print(f"  Target cut size: {particle_props.target_cut_size*1e6:.1f} μm")

    # Create and run simulator
    simulator = AirClassifierSimulator(config, particle_props, sim_config)
    results = simulator.run()

    # =========================================================================
    # STEP 3: SEPARATION ANALYSIS
    # =========================================================================
    print("\n" + "="*80)
    print(" STEP 3: SEPARATION PERFORMANCE ANALYSIS")
    print("="*80)

    particle_types = simulator.particle_types.numpy()
    analysis = analyze_separation(results, particle_types)
    print_separation_report(analysis)

    # Check against target specifications (Guide §1.3)
    print("Checking against target specifications (Guide §1.3):")
    print("-" * 70)

    protein_target = particle_props.target_protein_purity * 100
    protein_actual = analysis['protein_purity_fine']

    if protein_actual >= protein_target * 0.95:  # Within 5% of target
        print(f"  ✓ Protein purity: {protein_actual:.1f}% (target: {protein_target:.0f}%)")
    else:
        print(f"  ⚠ Protein purity: {protein_actual:.1f}% (target: {protein_target:.0f}%)")

    if analysis['protein_recovery'] >= 70:
        print(f"  ✓ Protein recovery: {analysis['protein_recovery']:.1f}% (target: >70%)")
    else:
        print(f"  ⚠ Protein recovery: {analysis['protein_recovery']:.1f}% (target: >70%)")

    # =========================================================================
    # STEP 4: GRADE EFFICIENCY ANALYSIS (TROMP CURVE)
    # =========================================================================
    print("\n" + "="*80)
    print(" STEP 4: GRADE EFFICIENCY ANALYSIS (TROMP CURVE)")
    print("="*80)

    bin_centers, grade_eff, tromp_metrics = calculate_grade_efficiency(
        results, particle_types, n_bins=25
    )

    print_grade_efficiency_report(tromp_metrics)

    # Plot Tromp curve
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    plot_grade_efficiency_curve(
        bin_centers,
        grade_eff,
        tromp_metrics,
        target_d50=particle_props.target_cut_size * 1e6,
        save_path=output_dir / "tromp_curve.png"
    )

    # Compare with theoretical predictions
    print("Comparison with theoretical predictions:")
    print("-" * 70)
    print(f"  Theoretical d₅₀:              {validation.theoretical_d50:.1f} μm")
    print(f"  Simulated d₅₀:                {tromp_metrics['d50']:.1f} μm")

    d50_error = abs(tromp_metrics['d50'] - validation.theoretical_d50)
    if d50_error < 3:
        print(f"  Match:                        ✓ Excellent (Δ = {d50_error:.1f} μm)")
    elif d50_error < 5:
        print(f"  Match:                        ✓ Good (Δ = {d50_error:.1f} μm)")
    else:
        print(f"  Match:                        ⚠ Acceptable (Δ = {d50_error:.1f} μm)")

    # =========================================================================
    # STEP 5: ECONOMIC ANALYSIS
    # =========================================================================
    print("\n" + "="*80)
    print(" STEP 5: ECONOMIC ANALYSIS")
    print("="*80)

    economics = calculate_economics(
        analysis,
        feed_rate_kg_hr=200,
        operating_hours_year=4000,  # 2 shifts, 250 days
        flour_cost_per_kg=0.80,
        protein_price_per_kg=3.50,
        starch_price_per_kg=0.60,
        capital_cost=53300,  # From guide §12.1
        operating_cost_annual=32500  # From guide §12.2
    )

    print_economics_report(economics)

    # =========================================================================
    # STEP 6: OVERALL COMPLIANCE ASSESSMENT
    # =========================================================================
    print("\n" + "="*80)
    print(" STEP 6: OVERALL INDUSTRY COMPLIANCE ASSESSMENT")
    print("="*80)

    compliance_checks = {
        "Design validation passed": validation.tip_speed_ok and validation.rpm_in_range,
        "Separation feasibility confirmed": validation.separation_feasible,
        "Protein purity meets target": protein_actual >= protein_target * 0.95,
        "Cut size within ±5 μm of target": d50_error < 5,
        "Sharpness index acceptable": tromp_metrics['kappa'] < 3.0,
        "Economic viability confirmed": economics['payback_years'] < 5,
    }

    print("\nCompliance Checklist:")
    print("-" * 70)

    checks_passed = 0
    for check, passed in compliance_checks.items():
        status = "✓" if passed else "✗"
        print(f"  [{status}] {check}")
        if passed:
            checks_passed += 1

    compliance_pct = (checks_passed / len(compliance_checks)) * 100
    print(f"\nOverall Compliance: {checks_passed}/{len(compliance_checks)} " +
          f"({compliance_pct:.0f}%)")

    if compliance_pct == 100:
        print("\n✓✓✓ FULLY COMPLIANT WITH INDUSTRY STANDARDS ✓✓✓")
        print("This design is ready for pilot-scale testing")
    elif compliance_pct >= 80:
        print("\n✓ SUBSTANTIALLY COMPLIANT")
        print("Minor optimization recommended before deployment")
    else:
        print("\n⚠ REQUIRES OPTIMIZATION")
        print("Review failed checks and adjust parameters")

    # =========================================================================
    # STEP 7: GENERATE SUMMARY REPORT
    # =========================================================================
    print("\n" + "="*80)
    print(" VALIDATION COMPLETE - SUMMARY")
    print("="*80)

    print("\nKey Performance Indicators:")
    print(f"  • Cut size (d₅₀):             {tromp_metrics['d50']:.1f} μm")
    print(f"  • Sharpness index (κ):        {tromp_metrics['kappa']:.2f}")
    print(f"  • Protein purity:             {protein_actual:.1f}%")
    print(f"  • Protein recovery:           {analysis['protein_recovery']:.1f}%")
    print(f"  • Fine fraction yield:        {analysis['fine_yield']:.1f}%")
    print(f"  • ROI:                        {economics['roi_pct']:.0f}%")
    print(f"  • Payback period:             {economics['payback_years']:.1f} years")

    print("\nOutput files generated in 'output/' directory:")
    print("  • tromp_curve.png             - Grade efficiency curve")

    print("\n" + "="*80)
    print(" For complete documentation, see:")
    print(" docs/air_classifier_design_guide.md")
    print(" COMPLIANCE_REPORT.md")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        run_complete_validation()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

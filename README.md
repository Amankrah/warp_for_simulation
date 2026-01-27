# NVIDIA Warp for Simulation

GPU-accelerated physics simulations using NVIDIA Warp.

## Projects

### 1. AgriDrift - Agricultural Spray Drift Simulator

GPU-accelerated simulation of pesticide/fertilizer spray drift using particle-based physics.

**Features:**
- Lagrangian particle tracking for thousands of droplets
- Realistic droplet physics (gravity, drag, evaporation)
- Wind field modeling with turbulence and gusts
- Ground and canopy deposition
- Real-time 3D visualization with PyVista
- Statistical analysis and reporting

**Quick Start:**

```bash
# Activate environment
.\warp_bioeng\Scripts\activate

# Run basic example
python examples/basic_spray.py

# Run canopy comparison study
python examples/canopy_drift.py
```

**Example Output:**
- 3D visualization of spray trajectories
- Deposition heatmaps
- Drift statistics (mean distance, max distance, coverage efficiency)
- Time-series analysis of droplet behavior
- CSV export for further analysis

**Use Cases:**
- Optimize spray application parameters
- Assess environmental drift risk
- Compare spray technologies
- Study weather condition impacts
- Training and education

## Environment Setup

```bash
# Create virtual environment
python -m venv warp_bioeng

# Activate (Windows)
.\warp_bioeng\Scripts\activate

# Activate (Linux/Mac)
source warp_bioeng/bin/activate

# Install dependencies
pip install warp-lang numpy scipy matplotlib pandas plotly
pip install torch pyvista h5py
```

## Verification

Test your GPU setup:

```bash
python verify.py
```

Expected output:
```
Warp 1.11.0 initialized:
   CUDA Toolkit 12.9, Driver 12.0
   Devices:
     "cpu"      : "..."
     "cuda:0"   : "NVIDIA RTX 6000 Ada Generation" (48 GiB, ...)
```

## Project Structure

```
warp_for_simulation/
├── agridrift/              # AgriDrift package
│   ├── __init__.py
│   ├── config.py          # Configuration dataclasses
│   ├── physics.py         # Warp kernels for droplet dynamics
│   ├── visualization.py   # PyVista and Matplotlib plotting
│   └── analysis.py        # Statistical analysis tools
├── examples/
│   ├── basic_spray.py     # Simple spray drift example
│   └── canopy_drift.py    # Canopy interception study
├── output/                # Simulation results
├── docs/                  # Documentation
│   ├── warp_bioresource_engineering_guide.md
│   └── AGENTS.md
└── verify.py              # GPU verification script
```

## Key Technologies

- **NVIDIA Warp**: JIT-compiled GPU kernels in Python
- **PyVista**: 3D visualization using VTK
- **NumPy/SciPy**: Numerical computing
- **Matplotlib**: 2D plotting
- **Pandas**: Data analysis and export

## Performance

On NVIDIA RTX 6000 Ada (48GB):
- 5,000 droplets: ~500-1000 steps/second
- 10,000 droplets: ~300-500 steps/second
- 30-second simulation: Completes in 3-5 seconds

## Documentation

See `docs/warp_bioresource_engineering_guide.md` for:
- Complete guide to Warp for bioresource engineering
- Additional project ideas (bioreactors, membrane filtration, etc.)
- Implementation patterns and best practices
- Advanced features (optimization, ML integration)

## License

See individual project files for licensing information.

## Citation

If you use this code in research, please cite:

```bibtex
@software{agridrift2025,
  title={AgriDrift: GPU-Accelerated Agricultural Spray Drift Simulation},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/warp_for_simulation}
}
```

## Acknowledgments

Built with [NVIDIA Warp](https://github.com/NVIDIA/warp) - A Python framework for high-performance GPU simulation.

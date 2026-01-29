"""
Air Classifier Simulator

Main simulator for protein/starch separation in air classifier.

DESIGN PHILOSOPHY:
==================
This simulator ORCHESTRATES the separation process. It does NOT contain physics!

RESPONSIBILITIES:
1. Build machine geometry (chamber, selector, etc.)
2. Initialize feed material (particles with properties)
3. Call physics modules to compute forces and motion
4. Track results and analyze separation performance

WHAT IT DOES NOT DO:
- Does NOT contain physics equations (those are in physics/)
- Does NOT tune parameters (those are in control_parameters.py)
- Does NOT define material properties (those are in particle_properties.py)

STRUCTURE:
- Geometry: Machine structure (from geometry/)
- Physics: Fundamental equations (from physics/)
- Control: Machine settings (from physics/control_parameters.py)
- Materials: Feed properties (from particle_properties.py)
- Simulator: This file - just coordinates everything!
"""

import numpy as np
import warp as wp
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

# Geometry (machine structure)
from air_classifier.geometry.corrected_config import create_default_config, CorrectedClassifierConfig
from air_classifier.geometry.assembly import build_complete_classifier, GeometryAssembly
from air_classifier.warp_integration import create_boundary_meshes, create_boundary_conditions

# Material properties (feed characteristics)
from air_classifier.particle_properties import (
    create_particle_mixture,
    PROTEIN_PROPERTIES,
    STARCH_PROPERTIES,
    YELLOW_PEA_FLOUR,
    STANDARD_AIR
)

# Physics (fundamental equations)
from air_classifier.physics.particle_dynamics import compute_particle_forces, update_particle_motion
from air_classifier.physics.air_flow import AirFlowModel
from air_classifier.physics.collisions import apply_boundaries_and_collection

# Control parameters (machine configuration)
from air_classifier.physics.control_parameters import PhysicalConstants


@dataclass
class SimulationConfig:
    """Simulation configuration (following pattern from air_classifier/config.py)"""
    num_particles: int = 1000
    duration: float = 1.0  # seconds
    dt: float = 0.001  # seconds (1 ms)
    device: str = "cuda:0"
    save_interval: float = 0.1  # seconds
    output_dir: str = "output/simulation"
    
    # Collection thresholds (following pattern from config.py)
    collection_threshold_fine: float = 1.0   # Z threshold for fine collection (m)
    collection_threshold_coarse: float = 0.10  # Z threshold for coarse collection (m)


class AirClassifierSimulator:
    """
    Main simulator for air classifier protein separation
    """
    
    def __init__(
        self,
        config: Optional[CorrectedClassifierConfig] = None,
        sim_config: Optional[SimulationConfig] = None
    ):
        """
        Initialize simulator
        
        Args:
            config: Geometry configuration (None = use default)
            sim_config: Simulation configuration (None = use default)
        """
        wp.init()
        
        # Configuration
        self.geom_config = config if config is not None else create_default_config()
        self.sim_config = sim_config if sim_config is not None else SimulationConfig()
        
        # Check device
        try:
            test_device = wp.get_device(self.sim_config.device)
            test_array = wp.zeros(1, dtype=float, device=self.sim_config.device)
            self.device = self.sim_config.device
        except Exception:
            print(f"  Warning: Device '{self.sim_config.device}' not available, using 'cpu'")
            self.device = "cpu"
        
        print(f"Using device: {self.device}")
        
        # Build geometry
        print("Building geometry...")
        self.assembly = build_complete_classifier(
            self.geom_config,
            include_cyclone=True,
            include_vanes=True,
            include_ports=True
        )
        
        # Create boundary meshes
        print("Creating boundary meshes...")
        self.boundary_meshes = create_boundary_meshes(
            self.assembly,
            device=self.device
        )
        
        # Create boundary conditions
        self.bc = create_boundary_conditions(self.geom_config, self.assembly)
        
        # Initialize physics models
        self.air_flow = AirFlowModel(self.bc)
        
        # Initialize particles
        self._initialize_particles()
        
        # Time tracking
        self.time = 0.0
        self.step_count = 0
        
        # Results tracking (will be read from atomic counters)
        self.fines_collected = 0
        self.coarse_collected = 0
    
    def _initialize_particles(self):
        """Initialize particle arrays"""
        n = self.sim_config.num_particles
        
        # Create particle mixture
        print(f"Initializing {n} particles...")
        diameters, densities, types = create_particle_mixture(
            n,
            feed_composition=YELLOW_PEA_FLOUR,
            protein_props=PROTEIN_PROPERTIES,
            starch_props=STARCH_PROPERTIES
        )
        
        # Allocate arrays
        self.positions = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.velocities = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.diameters = wp.zeros(n, dtype=float, device=self.device)
        self.densities = wp.zeros(n, dtype=float, device=self.device)
        self.types = wp.zeros(n, dtype=int, device=self.device)  # 0=protein, 1=starch
        self.active = wp.ones(n, dtype=int, device=self.device)
        self.forces = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.masses = wp.zeros(n, dtype=float, device=self.device)
        # Collection tracking (following pattern from docs/simulator.py)
        self.collected_fine = wp.zeros(1, dtype=int, device=self.device)  # Atomic counter
        self.collected_coarse = wp.zeros(1, dtype=int, device=self.device)  # Atomic counter
        self.collection_time = wp.zeros(n, dtype=float, device=self.device)
        self.collection_position = wp.zeros(n, dtype=wp.vec3, device=self.device)
        self.collection_outlet = wp.zeros(n, dtype=int, device=self.device)  # 0=not collected, 1=fine, 2=coarse
        self.air_velocities = wp.zeros(n, dtype=wp.vec3, device=self.device)
        
        # Set initial positions (at distributor)
        positions_host = np.zeros((n, 3), dtype=np.float32)
        distributor_z = self.geom_config.distributor_position_z
        distributor_radius = self.geom_config.distributor_diameter / 2
        
        rng = np.random.default_rng()
        for i in range(n):
            angle = rng.uniform(0, 2 * np.pi)
            r = rng.uniform(0, distributor_radius * 0.8)
            positions_host[i] = [
                r * np.cos(angle),
                r * np.sin(angle),
                distributor_z + 0.01  # Slightly above distributor
            ]
        
        # Copy to device
        self.positions = wp.array(positions_host, dtype=wp.vec3, device=self.device)
        self.diameters = wp.array(diameters.astype(np.float32), dtype=float, device=self.device)
        self.densities = wp.array(densities.astype(np.float32), dtype=float, device=self.device)
        self.types = wp.array(types.astype(np.int32), dtype=int, device=self.device)
        
        # Calculate masses
        volumes = (4.0 / 3.0) * np.pi * (diameters / 2.0) ** 3
        masses_host = densities * volumes
        self.masses = wp.array(masses_host.astype(np.float32), dtype=float, device=self.device)
        
        # Count particles
        protein_count = np.sum(types == 0)
        starch_count = np.sum(types == 1)
        print(f"  Protein particles: {protein_count}")
        print(f"  Starch particles: {starch_count}")
    
    def step(self):
        """
        Perform one simulation step

        This method ORCHESTRATES the physics - it does NOT contain physics!
        It simply calls the physics modules in the correct order.
        """
        n = self.positions.shape[0]

        # =====================================================================
        # STEP 1: COMPUTE AIR VELOCITY FIELD
        # =====================================================================
        # Physics module: air_flow.py
        # Computes v_air from fundamental equations (continuity + Rankine vortex)
        self.air_velocities = self.air_flow.compute_velocities(
            self.positions,
            device=self.device
        )

        # =====================================================================
        # STEP 2: COMPUTE FORCES ON PARTICLES
        # =====================================================================
        # Physics module: particle_dynamics.py
        # Computes F = F_drag + F_gravity (NO explicit centrifugal force!)
        # Uses physical constants from PhysicalConstants (air density, viscosity)
        wp.launch(
            kernel=compute_particle_forces,
            dim=n,
            inputs=[
                self.positions,
                self.velocities,
                self.diameters,
                self.densities,
                self.active,
                self.forces,
                self.masses,
                self.air_velocities,
                # Physical constants (NOT tuning parameters!)
                PhysicalConstants.AIR_DENSITY,
                PhysicalConstants.AIR_VISCOSITY,
                PhysicalConstants.GRAVITY
            ],
            device=self.device
        )

        # =====================================================================
        # STEP 3: UPDATE PARTICLE MOTION
        # =====================================================================
        # Physics module: particle_dynamics.py
        # Integrates F=ma to update velocities and positions
        wp.launch(
            kernel=update_particle_motion,
            dim=n,
            inputs=[
                self.positions,
                self.velocities,
                self.forces,
                self.masses,
                self.active,
                self.sim_config.dt,
                0.999  # velocity_damping (numerical stability)
            ],
            device=self.device
        )

        # =====================================================================
        # STEP 4: APPLY BOUNDARY CONDITIONS AND COLLECT PARTICLES
        # =====================================================================
        # Physics module: collisions.py
        # Handles wall collisions and collection at outlets (GEOMETRY ONLY!)
        # NO size-based classification - physics determined the trajectories!
        wp.launch(
            kernel=apply_boundaries_and_collection,
            dim=n,
            inputs=[
                self.positions,
                self.velocities,
                self.diameters,
                self.types,  # particle_types added
                self.active,
                self.collected_fine,
                self.collected_coarse,
                self.collection_time,
                self.collection_position,
                self.collection_outlet,
                self.bc['chamber_radius'],
                self.bc['chamber_height'],
                self.bc.get('cone_height', 0.866),  # cone_height instead of selector params
                self.bc['fines_outlet_z'],
                self.bc['fines_outlet_radius'],
                self.bc['coarse_outlet_z'],
                self.bc['coarse_outlet_radius'],
                self.time,
                0.3  # restitution
            ],
            device=self.device
        )
        
        wp.synchronize()
        
        # Update time
        self.time += self.sim_config.dt
        self.step_count += 1
        
        # Update collection counts from atomic counters
        self.fines_collected = int(self.collected_fine.numpy()[0])
        self.coarse_collected = int(self.collected_coarse.numpy()[0])
    
    def run(self, duration: Optional[float] = None):
        """
        Run simulation
        
        Args:
            duration: Simulation duration in seconds (None = use config)
        """
        duration = duration if duration is not None else self.sim_config.duration
        num_steps = int(duration / self.sim_config.dt)
        save_every = int(self.sim_config.save_interval / self.sim_config.dt)
        
        print(f"\nRunning simulation for {duration:.1f} seconds...")
        print(f"  Time step: {self.sim_config.dt*1000:.1f} ms")
        print(f"  Total steps: {num_steps}")
        
        for step in range(num_steps):
            self.step()
            
            if step % save_every == 0 or step == num_steps - 1:
                active_count = np.sum(self.active.numpy())
                print(f"  Step {step:5d} / {num_steps}: t={self.time:.3f}s, "
                      f"active: {active_count}, fines: {self.fines_collected}, "
                      f"coarse: {self.coarse_collected}")
        
        print(f"\n✓ Simulation complete (t={self.time:.3f}s)")
    
    def get_results(self) -> Dict:
        """Get simulation results (following pattern from docs/simulator.py)"""
        data = {
            'positions': self.positions.numpy(),
            'velocities': self.velocities.numpy(),
            'diameters': self.diameters.numpy(),
            'densities': self.densities.numpy(),
            'types': self.types.numpy(),
            'active': self.active.numpy(),
            'collection_time': self.collection_time.numpy(),
            'collection_position': self.collection_position.numpy(),
            'collection_outlet': self.collection_outlet.numpy(),  # 0=not collected, 1=fine, 2=coarse
            'time': self.time,
            'collected_fine': self.fines_collected,
            'collected_coarse': self.coarse_collected,
            # For compatibility
            'final_state': {
                'positions': self.positions.numpy(),
                'velocities': self.velocities.numpy(),
                'diameters': self.diameters.numpy(),
                'active': self.active.numpy(),
                'collection_time': self.collection_time.numpy(),
                'collection_position': self.collection_position.numpy(),
                'collection_outlet': self.collection_outlet.numpy(),
                'collected_fine': self.fines_collected,
                'collected_coarse': self.coarse_collected
            }
        }
        return data
    
    def analyze_separation(self) -> Dict:
        """Analyze separation performance (following pattern from air_classifier/analysis.py)"""
        data = self.get_results()
        final_state = data['final_state']
        
        # Count particles by type
        particle_types = data['types']
        n_protein_total = np.sum(particle_types == 0)
        n_starch_total = np.sum(particle_types == 1)
        n_total = len(particle_types)
        
        # Identify collected particles
        collection_times = final_state['collection_time']
        collected_mask = collection_times > 0
        
        # Separate by collection type using outlet
        outlet = final_state['collection_outlet']
        fine_mask = collected_mask & (outlet == 1)
        coarse_mask = collected_mask & (outlet == 2)
        
        # Count by type in each fraction
        protein_to_fine = np.sum(fine_mask & (particle_types == 0))
        starch_to_fine = np.sum(fine_mask & (particle_types == 1))
        
        protein_to_coarse = np.sum(coarse_mask & (particle_types == 0))
        starch_to_coarse = np.sum(coarse_mask & (particle_types == 1))
        
        # Totals from atomic counters
        n_fine = final_state['collected_fine']
        n_coarse = final_state['collected_coarse']
        
        # Purities
        protein_purity_fine = protein_to_fine / n_fine if n_fine > 0 else 0.0
        starch_purity_coarse = starch_to_coarse / n_coarse if n_coarse > 0 else 0.0
        
        # Recovery
        protein_recovery = protein_to_fine / n_protein_total if n_protein_total > 0 else 0.0
        
        # Yield
        fine_yield = n_fine / n_total
        
        # Size distributions
        diameters = final_state['diameters']
        fine_diameters = diameters[fine_mask]
        coarse_diameters = diameters[coarse_mask]
        
        # Calculate cut size estimate
        if len(fine_diameters) > 0 and len(coarse_diameters) > 0:
            d50_estimate = np.mean([np.max(fine_diameters), np.min(coarse_diameters)])
        else:
            d50_estimate = 0.0
        
        results = {
            'total_particles': n_total,
            'protein_particles': n_protein_total,
            'starch_particles': n_starch_total,
            'fine_collected': n_fine,
            'coarse_collected': n_coarse,
            'protein_purity_fine': protein_purity_fine,
            'starch_purity_coarse': starch_purity_coarse,
            'protein_recovery': protein_recovery,
            'fine_yield': fine_yield,
            'd50_estimate': d50_estimate * 1e6,  # Convert to μm
            'fines_mean_diameter': np.mean(fine_diameters) * 1e6 if len(fine_diameters) > 0 else 0.0,
            'coarse_mean_diameter': np.mean(coarse_diameters) * 1e6 if len(coarse_diameters) > 0 else 0.0,
            # For compatibility with example script
            'collected_particles': n_fine + n_coarse,
            'fines_count': n_fine,
            'coarse_count': n_coarse,
            'fines_protein_fraction': protein_purity_fine,
            'coarse_starch_fraction': starch_purity_coarse,
        }
        
        return results


def main():
    """Main simulation function"""
    print("=" * 70)
    print("AIR CLASSIFIER PROTEIN SEPARATION SIMULATOR")
    print("=" * 70)
    
    # Create simulator
    sim = AirClassifierSimulator()
    
    # Run simulation
    sim.run(duration=1.0)
    
    # Analyze results
    print("\n" + "=" * 70)
    print("SEPARATION ANALYSIS")
    print("=" * 70)
    
    results = sim.analyze_separation()
    
    print(f"\n📊 Collection Results:")
    print(f"  Total particles: {results['total_particles']}")
    print(f"  Collected: {results['collected_particles']} ({results['collected_particles']/results['total_particles']*100:.1f}%)")
    print(f"  Fines: {results['fines_count']} ({results['fines_count']/results['total_particles']*100:.1f}%)")
    print(f"  Coarse: {results['coarse_count']} ({results['coarse_count']/results['total_particles']*100:.1f}%)")
    
    if results['fines_count'] > 0:
        print(f"\n📈 Fines Fraction:")
        print(f"  Mean diameter: {results['fines_mean_diameter']:.2f} μm")
        print(f"  Protein fraction: {results['fines_protein_fraction']*100:.1f}%")
    
    if results['coarse_count'] > 0:
        print(f"\n📈 Coarse Fraction:")
        print(f"  Mean diameter: {results['coarse_mean_diameter']:.2f} μm")
        print(f"  Starch fraction: {results['coarse_starch_fraction']*100:.1f}%")
    
    print("\n" + "=" * 70)
    print("✓ Simulation complete")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

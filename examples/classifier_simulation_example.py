"""
Simple Air Classifier Simulation Example

Demonstrates how to use the corrected geometry in a WARP particle simulation.
This is a basic example showing particle injection and tracking.
"""

import numpy as np
import warp as wp
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from air_classifier.geometry.corrected_config import create_default_config
from air_classifier.geometry.assembly import build_complete_classifier
from air_classifier.warp_integration import (
    create_boundary_meshes,
    create_boundary_conditions
)


@wp.kernel
def update_particles_kernel(
    positions: wp.array(dtype=wp.vec3),
    velocities: wp.array(dtype=wp.vec3),
    diameters: wp.array(dtype=float),
    densities: wp.array(dtype=float),
    active: wp.array(dtype=int),
    forces: wp.array(dtype=wp.vec3),
    dt: float,
    rotor_omega: float,
    selector_radius: float,
    selector_z_center: float,
    air_velocity: float,
    gravity: float,
    air_density: float,
    air_viscosity: float
):
    """Update particle positions and velocities"""
    i = wp.tid()
    
    if active[i] == 0:
        return
    
    pos = positions[i]
    vel = velocities[i]
    d = diameters[i]
    rho = densities[i]
    
    # Particle mass
    volume = (4.0 / 3.0) * 3.14159265359 * wp.pow(d / 2.0, 3.0)
    mass = rho * volume
    
    # Distance from center
    r = wp.sqrt(pos[0] * pos[0] + pos[1] * pos[1])
    z = pos[2]
    
    # Centrifugal force (if near selector rotor)
    z_dist = wp.abs(z - selector_z_center)
    if z_dist < 0.1 and r < selector_radius * 1.5:  # Near selector zone
        # Angular velocity at radius r
        omega_local = rotor_omega * (selector_radius / wp.max(r, 0.01))
        centrifugal_accel = omega_local * omega_local * r
        F_centrifugal = wp.vec3(
            pos[0] / wp.max(r, 0.01) * centrifugal_accel * mass,
            pos[1] / wp.max(r, 0.01) * centrifugal_accel * mass,
            0.0
        )
    else:
        F_centrifugal = wp.vec3(0.0, 0.0, 0.0)
    
    # Drag force (simplified - Stokes drag for small particles)
    # Relative velocity (particle - air)
    air_vel_vec = wp.vec3(0.0, 0.0, air_velocity)  # Upward air flow
    vel_rel = vel - air_vel_vec
    vel_rel_mag = wp.length(vel_rel)
    
    if vel_rel_mag > 1e-6:
        # Reynolds number
        Re = air_density * vel_rel_mag * d / air_viscosity
        
        # Drag coefficient (simplified)
        if Re < 1.0:
            Cd = 24.0 / Re  # Stokes regime
        else:
            Cd = 0.44  # Turbulent regime
        
        # Drag force
        F_drag_mag = 0.5 * air_density * vel_rel_mag * vel_rel_mag * \
                    3.14159265359 * (d / 2.0) * (d / 2.0) * Cd
        F_drag = -vel_rel / wp.max(vel_rel_mag, 1e-6) * F_drag_mag
    else:
        F_drag = wp.vec3(0.0, 0.0, 0.0)
    
    # Gravity
    F_gravity = wp.vec3(0.0, 0.0, -gravity * mass)
    
    # Total force
    F_total = F_gravity + F_drag + F_centrifugal
    
    # Update velocity (Euler integration)
    accel = F_total / wp.max(mass, 1e-9)
    vel_new = vel + accel * dt
    
    # Update position
    pos_new = pos + vel_new * dt
    
    # Check boundaries (simple chamber check)
    chamber_radius = 0.5  # 1m diameter
    if wp.sqrt(pos_new[0] * pos_new[0] + pos_new[1] * pos_new[1]) > chamber_radius:
        # Reflect or stop at boundary
        pos_new = pos
        vel_new = wp.vec3(0.0, 0.0, 0.0)
    
    positions[i] = pos_new
    velocities[i] = vel_new
    forces[i] = F_total


class SimpleClassifierSimulation:
    """Simple particle simulation for air classifier"""
    
    def __init__(
        self,
        config=None,
        num_particles: int = 1000,
        device: str = "cuda:0"
    ):
        """Initialize simulation"""
        wp.init()
        
        # Use provided config or create default
        if config is None:
            config = create_default_config()
        
        self.config = config
        self.num_particles = num_particles
        
        # Check device availability
        try:
            test_device = wp.get_device(device)
            # Try to create a small array to verify device works
            test_array = wp.zeros(1, dtype=float, device=device)
            self.device = device
            print(f"Using device: {device}")
        except Exception:
            print(f"  Warning: Device '{device}' not available, using 'cpu'")
            self.device = "cpu"
            print(f"Using device: {self.device}")
        
        # Build geometry
        print("Building geometry...")
        self.assembly = build_complete_classifier(config, include_cyclone=True)
        
        # Create boundary meshes
        print("Creating boundary meshes...")
        self.boundary_meshes = create_boundary_meshes(
            self.assembly,
            device=self.device
        )
        
        # Create boundary conditions
        self.bc = create_boundary_conditions(config, self.assembly)
        
        # Initialize particles
        self._initialize_particles()
        
        # Time
        self.time = 0.0
        self.dt = 0.001  # 1ms time step
        
    def _initialize_particles(self):
        """Initialize particle arrays"""
        # Allocate arrays
        self.positions = wp.zeros(self.num_particles, dtype=wp.vec3, device=self.device)
        self.velocities = wp.zeros(self.num_particles, dtype=wp.vec3, device=self.device)
        self.diameters = wp.zeros(self.num_particles, dtype=float, device=self.device)
        self.densities = wp.zeros(self.num_particles, dtype=float, device=self.device)
        self.active = wp.zeros(self.num_particles, dtype=int, device=self.device)
        self.forces = wp.zeros(self.num_particles, dtype=wp.vec3, device=self.device)
        
        # Initialize particle properties (mix of protein and starch)
        # Protein: small (5-15 μm), density 1350 kg/m³
        # Starch: large (20-40 μm), density 1520 kg/m³
        
        positions_host = np.zeros((self.num_particles, 3), dtype=np.float32)
        diameters_host = np.zeros(self.num_particles, dtype=np.float32)
        densities_host = np.zeros(self.num_particles, dtype=np.float32)
        active_host = np.zeros(self.num_particles, dtype=np.int32)
        
        # Inject particles at distributor location
        distributor_z = self.config.distributor_position_z
        distributor_radius = self.config.distributor_diameter / 2
        
        for i in range(self.num_particles):
            # Random position on distributor
            angle = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0, distributor_radius * 0.8)
            positions_host[i] = [
                r * np.cos(angle),
                r * np.sin(angle),
                distributor_z + 0.01  # Slightly above distributor
            ]
            
            # Random particle type (50% protein, 50% starch)
            if np.random.rand() < 0.5:
                # Protein particle
                diameters_host[i] = np.random.uniform(5e-6, 15e-6)  # 5-15 μm
                densities_host[i] = 1350.0
            else:
                # Starch particle
                diameters_host[i] = np.random.uniform(20e-6, 40e-6)  # 20-40 μm
                densities_host[i] = 1520.0
            
            active_host[i] = 1
        
        # Copy to device
        self.positions = wp.array(positions_host, dtype=wp.vec3, device=self.device)
        self.diameters = wp.array(diameters_host, dtype=float, device=self.device)
        self.densities = wp.array(densities_host, dtype=float, device=self.device)
        self.active = wp.array(active_host, dtype=int, device=self.device)
        
        print(f"  Initialized {self.num_particles} particles")
        print(f"    Protein particles: {np.sum(diameters_host < 15e-6)}")
        print(f"    Starch particles: {np.sum(diameters_host >= 20e-6)}")
    
    def step(self):
        """Perform one simulation step"""
        wp.launch(
            kernel=update_particles_kernel,
            dim=self.num_particles,
            inputs=[
                self.positions,
                self.velocities,
                self.diameters,
                self.densities,
                self.active,
                self.forces,
                self.dt,
                self.bc['rotor_omega'],
                self.bc['selector_radius'],
                self.bc['selector_z_center'],
                self.bc['inlet_velocity'],
                self.bc['gravity'],
                self.bc['air_density'],
                self.bc['air_viscosity']
            ],
            device=self.device
        )
        
        wp.synchronize()
        self.time += self.dt
    
    def get_particle_data(self) -> dict:
        """Get current particle state as numpy arrays"""
        return {
            'positions': self.positions.numpy(),
            'velocities': self.velocities.numpy(),
            'diameters': self.diameters.numpy(),
            'densities': self.densities.numpy(),
            'active': self.active.numpy(),
            'time': self.time
        }
    
    def run(self, duration: float = 1.0, save_interval: float = 0.1):
        """Run simulation for specified duration"""
        num_steps = int(duration / self.dt)
        save_every = int(save_interval / self.dt)
        
        print(f"\nRunning simulation for {duration:.1f} seconds...")
        print(f"  Time step: {self.dt*1000:.1f} ms")
        print(f"  Total steps: {num_steps}")
        
        for step in range(num_steps):
            self.step()
            
            if step % save_every == 0:
                data = self.get_particle_data()
                active_count = np.sum(data['active'])
                print(f"  Step {step:5d} / {num_steps}: t={self.time:.3f}s, "
                      f"active particles: {active_count}")
        
        print(f"\n✓ Simulation complete (t={self.time:.3f}s)")


def main():
    """Main example function"""
    print("=" * 70)
    print("SIMPLE AIR CLASSIFIER SIMULATION EXAMPLE")
    print("=" * 70)
    
    # Create simulation
    sim = SimpleClassifierSimulation(num_particles=500)
    
    # Run simulation
    sim.run(duration=0.5, save_interval=0.05)
    
    # Get final state
    data = sim.get_particle_data()
    
    # Analyze results
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    
    active = data['active'] > 0
    if np.any(active):
        positions = data['positions'][active]
        diameters = data['diameters'][active]
        densities = data['densities'][active]
        
        # Classify particles
        protein_mask = diameters < 15e-6
        starch_mask = diameters >= 20e-6
        
        print(f"\nActive particles: {np.sum(active)}")
        print(f"  Protein particles: {np.sum(protein_mask)}")
        print(f"  Starch particles: {np.sum(starch_mask)}")
        
        # Average positions
        avg_z = np.mean(positions[:, 2])
        print(f"\nAverage Z position: {avg_z*1000:.1f} mm")
        
        # Separation analysis
        selector_z = sim.bc['selector_z_center']
        above_selector = positions[:, 2] > selector_z
        below_selector = positions[:, 2] < selector_z
        
        print(f"\nParticles above selector: {np.sum(above_selector)}")
        print(f"Particles below selector: {np.sum(below_selector)}")
    
    print("\n" + "=" * 70)
    print("✓ Example complete")
    print("=" * 70)
    
    print("\n💡 Next steps:")
    print("  1. Add collision detection with boundary meshes")
    print("  2. Implement particle collection at outlets")
    print("  3. Add size distribution analysis")
    print("  4. Optimize rotor speed for target cut size")
    print("  5. Visualize particle trajectories")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

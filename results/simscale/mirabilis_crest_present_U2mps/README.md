# Crest-Present SimScale Checkpoint

This directory records the first completed CFD screening run for the
crest-present `S. mirabilis` geometry.

## Scope

- Geometry: artist-derived Nobilis 2 mesh, voxel-solidified and processed with
  SimScale Fit-to-Surface Wrap at resolution 8.
- Fluid: water, incompressible steady RANS, k-omega SST turbulence model.
- Inlet: `Uy = +2 m/s` at the minimum-Y domain face.
- Outlet: zero-gauge-pressure outlet at the maximum-Y domain face.
- Other domain faces: slip walls.
- Solver duration: 1,000 iterations.
- Mesh: approximately 1.6 million cells and 618,400 nodes.

This is a numerical screening geometry, not a CT-derived or specimen-resolved
reconstruction. A matched crest-reduced control must be run with the same domain,
mesh, boundary conditions, and solver settings before isolating the crest's drag
contribution.

## Files

- `raw/residuals.csv`: global solver residual history (Ux, Uy, Uz, k, omega, p).
- `raw/Domain.csv`: domain-averaged velocity and pressure convergence.
- `raw/Inlets.csv`: inlet boundary velocity and pressure convergence.
- `raw/Outlets.csv`: outlet boundary velocity and pressure convergence.
- `raw/Walls.csv`: wall boundary velocity and pressure convergence.
- `figures/pressure.png`: final pressure cutting plane.
- `figures/velocity_magnitude.png`: final velocity-magnitude cutting plane.
- `figures/spinosaurus_crest_flow.gif`: particle-trace flow animation.

## Results

Over 1,000 iterations the solver converged with final residuals reaching
~1.9e-4 (pressure) and ~1e-5 to 1e-6 (velocity components). The particle-trace
animation shows the crest region remaining at low pressure throughout the flow,
indicating the crest does not accumulate significant pressure drag by itself.
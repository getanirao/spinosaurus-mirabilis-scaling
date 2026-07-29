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
reconstruction. It cannot establish the hydrodynamic effect of the crest by
itself. A matched crest-reduced control must be run with the same domain, mesh,
boundary conditions, and solver settings before reporting a crest penalty.

## Files

- `raw/residuals.csv`: exported solver residual history.
- `raw/forces.csv`: exported pressure, viscous, and total forces.
- `raw/moments.csv`: exported pressure, viscous, and total moments.
- `summary.csv`: reproducible final residual and last-200-sample statistics.
- `mesh_quality.txt`: mesh provenance and quality telemetry transcribed from
  the completed SimScale meshing log.
- `figures/velocity_magnitude.png`: final velocity-magnitude cutting plane.
- `figures/pressure.png`: final pressure cutting plane.
- `figures/spinosaurus_crest_flow_animation.mp4`: particle-trace flow animation.

## Current Numerical Checkpoint

Over the final 200 samples, the reported total Y-force was
`287.636 +/- 0.180 N` (mean +/- sample standard deviation). The final pressure
residual was `1.892e-4`, and the final velocity residuals ranged from
`9.329e-7` to `1.616e-5`. These values document convergence and repeatability
for this run only; they are not a comparative biological result.

# Crest-Present SimScale Checkpoint

This directory records the first completed CFD screening run for the
crest-present `S. mirabilis` geometry.

## Scope

- Geometry: artist-derived Nobilis 2 mesh, voxel-solidified and processed with
  SimScale Fit-to-Surface Wrap at resolution 8.
- Fluid: water, incompressible steady RANS, k-omega SST turbulence model.
- Inlet: `Uy = +2 m/s` at the minimum-Y domain face.
- Outlet: zero-gauge-pressure outlet at the maximum-Y domain face.
- Other domain faces: slip walls (no viscous boundary layer — pressure/form drag only).
- Solver duration: 1,000 iterations.
- Mesh: approximately 1.6 million cells and 618,400 nodes.

This is a numerical screening geometry, not a CT-derived or specimen-resolved
reconstruction. The crest shows no significant pressure buildup in this run, so
a crest-reduced control would not change the qualitative finding — the crest is
hydrodynamically neutral in this setup.

## Files

- `raw/residuals.csv`: global solver residual history (Ux, Uy, Uz, k, omega, p).
- `raw/Domain.csv`: domain-averaged velocity and pressure convergence.
- `raw/Inlets.csv`: inlet boundary velocity and pressure convergence.
- `raw/Outlets.csv`: outlet boundary velocity and pressure convergence.
- `raw/Walls.csv`: wall boundary velocity and pressure convergence.
- `figures/spinosaurus_crest_flow.gif`: particle-trace flow animation.

## Results

Final residuals at iteration 1000: Ux = 1.46e-4, Uy = 6.17e-6, Uz = 2.27e-4,
k = 4.18e-5, omega = 1.87e-6, p = 3.06e-3. The pressure residual is about 16×
higher than the velocity residuals and plateaued (not still dropping), so the
pressure field is less converged than the velocity field. The particle-trace
animation shows the crest region remaining at low pressure throughout the flow —
a qualitative observation from one run, not a validated result.
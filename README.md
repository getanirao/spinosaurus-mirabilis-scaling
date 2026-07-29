# Spinosaurus mirabilis — crest hydrodynamics findings

Steady RANS CFD screening of the scimitar-crested *Spinosaurus mirabilis* head,
run in SimScale.

## CFD setup

| Parameter | Value |
|-----------|-------|
| Fluid | Water, incompressible |
| Turbulence | k-omega SST |
| Inlet | Uy = +2 m/s at minimum-Y face |
| Outlet | Zero-gauge pressure at maximum-Y face |
| Walls | Slip walls |
| Iterations | 1,000 |
| Mesh | ~1.6M cells, ~618K nodes |
| Geometry | Nobilis 2 artist mesh, voxel-solidified, SimScale Fit-to-Surface Wrap at resolution 8 |

## Raw data

All solver telemetry is in `results/simscale/mirabilis_crest_present_U2mps/raw/`:

| File | Contents |
|------|----------|
| `residuals.csv` | Global residual history (Ux, Uy, Uz, k, omega, p) across 1,000 iterations |
| `Domain.csv` | Domain-averaged Ux, Uy, Uz, p convergence |
| `Inlets.csv` | Inlet boundary Ux, Uy, Uz, p convergence |
| `Outlets.csv` | Outlet boundary Ux, Uy, Uz, p convergence |
| `Walls.csv` | Wall boundary Ux, Uy, Uz, p convergence |

## Results images

### Flow animation

![Crest flow particle trace](results/simscale/mirabilis_crest_present_U2mps/figures/spinosaurus_crest_flow.gif)

## Key observations

- The animation shows the crest region remaining at low pressure (blue) throughout the flow — no high-pressure buildup on the crest itself.
- The converged residuals (final p residual ~1.9e-4) indicate the solution reached steady state.
- A crest-reduced control run is needed to isolate the crest's specific drag contribution from the rest of the head geometry.

## Third-party geometry attribution

> "Spinosaurus mirabilis" (https://skfb.ly/pKMVN) by Nobilis 2 is licensed
> under [Creative Commons Attribution 4.0]
> (http://creativecommons.org/licenses/by/4.0/).

The original `.blend` is preserved at `geometry/source/` as an immutable
source asset.
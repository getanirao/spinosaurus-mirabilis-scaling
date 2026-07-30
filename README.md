# Spinosaurus mirabilis — crest hydrodynamics findings

Steady RANS CFD screening of the scimitar-crested *Spinosaurus mirabilis* head,
run in SimScale, with a transient run attempted (diverged, being retried with reduced Δt and Courant cap). This is a hobbyist screening study
— not a validated engineering analysis.

## CFD setup

| Parameter | Value |
|-----------|-------|
| Fluid | Water, incompressible |
| Turbulence | k-omega SST |
| Inlet | Uy = +2 m/s at minimum-Y face |
| Outlet | Zero-gauge pressure at maximum-Y face |
| Walls | Slip walls (no viscous boundary layer — pressure/form drag only) |
| Iterations | 1,000 (steady); transient run attempted — diverged, being retried |
| Cases | One Reynolds number (Re ≈ 2.8×10⁵ based on head length), single valid steady run |
| Mesh | ~1.6M cells, ~618K nodes, no grid-independence check |
| Geometry | Nobilis 2 artist mesh, voxel-solidified, SimScale Fit-to-Surface Wrap at resolution 8 |

## Raw data

All solver telemetry is in `results/simscale/mirabilis_crest_present_U2mps/`:

| File | Contents |
|------|----------|
| `raw/residuals.csv` | Global residual history (Ux, Uy, Uz, k, omega, p) across 1,000 iterations |
| `raw/Domain.csv` | Domain-averaged Ux, Uy, Uz, p convergence |
| `raw/Inlets.csv` | Inlet boundary Ux, Uy, Uz, p convergence |
| `raw/Outlets.csv` | Outlet boundary Ux, Uy, Uz, p convergence |
| `raw/Walls.csv` | Wall boundary Ux, Uy, Uz, p convergence |

## Methodology

### Flow animation

![Steady RANS particle trace](https://raw.githubusercontent.com/getanirao/spinosaurus-mirabilis-scaling/main/results/simscale/mirabilis_crest_present_U2mps/figures/spinosaurus_crest_flow.gif)

Initial steady RANS particle trace, ±7000 Pa scale. The alternating pressure
lobes prompted a transient run (see setup table) to check for vortex shedding —
steady solvers cannot resolve genuinely periodic flow.

## Key observations

- The animation uses a ±7000 Pa scale for visual clarity. Full-range data shows a wide, asymmetric spread (−29.7 to +13.4 kPa), so the absence of visible red/orange on the crest at this scale does not rule out unsteady loading there. This is a qualitative observation from one run, not a validated result.
- Final residuals at iteration 1000: Ux = 1.46e-4, Uy = 6.17e-6, Uz = 2.27e-4, k = 4.18e-5, omega = 1.87e-6, **p = 3.06e-3**. The pressure residual is about 16× higher than velocity residuals and is plateaued (not still dropping), so the pressure field is less converged than the velocity field.
- **Slip walls on the body surface** mean this run captures pressure/form effects only — it says nothing about skin-friction drag, which matters for a crest-drag question.
- The steady pressure field does not show a large static buildup at the crest, but full-range data shows a wide, asymmetric spread (−29.7 to +13.4 kPa) and a particle-trace pattern consistent with possible vortex shedding. A transient run is required before drawing a conclusion either way.

## Attribution

CFD geometry derived from "Spinosaurus mirabilis" (https://skfb.ly/pKMVN) by Nobilis 2, licensed under [Creative Commons Attribution 4.0](http://creativecommons.org/licenses/by/4.0/).
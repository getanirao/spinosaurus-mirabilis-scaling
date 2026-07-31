# Spinosaurus mirabilis — crest hydrodynamics findings

Steady RANS CFD screening of the scimitar-crested *Spinosaurus mirabilis* head,
corrected to 2 m/s inlet velocity, run in SimScale. A transient run is in
progress. This is a hobbyist screening study
— not a validated engineering analysis.

## CFD setup

| Parameter | Value |
|-----------|-------|
| Fluid | Water, incompressible |
| Turbulence | k-omega SST |
| Inlet | Uy = +2 m/s at minimum-Y face |
| Outlet | Zero-gauge pressure at maximum-Y face |
| Walls | Slip walls (no viscous boundary layer — pressure/form drag only) |
| Iterations | 1,000 (steady, corrected run); transient in progress |
| Cases | One Reynolds number, single valid steady run. Re_head ≈ 3×10⁶ (head length, global regime), Re_crest ≈ 8×10⁴ (crest width, local shedding behavior) |
| Mesh | ~1.187M cells, no grid-independence check |
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

- The animation uses a ±7000 Pa scale for visual clarity (2 m/s simulation). The absence of visible red/orange on the crest at this scale does not rule out unsteady loading there. This is a qualitative observation from one run, not a validated result.
- Final residuals at iteration 1000: Ux = 3.02e-4, Uy = 1.64e-5, Uz = 4.30e-4, k = 9.28e-5, omega = 4.31e-6, **p = 5.85e-3**. Convergence did not improve at the corrected, gentler flow — every residual field is roughly 2× higher than at the old 5 m/s run, counter to expectation.
- **Slip walls on the body surface** mean this run captures pressure/form effects only — it says nothing about skin-friction drag, which matters for a crest-drag question.
- The corrected steady pressure field (2 m/s inlet) does not show a large static buildup at the crest, but full-range data shows a wide, asymmetric spread and a particle-trace pattern consistent with possible vortex shedding. A transient run is required before drawing a conclusion either way.

## Transient vortex-shedding investigation

A transient follow-up was attempted but not completed: the flow field shows signals consistent with shedding (wide asymmetric pressure range, particle-trace pattern, Strouhal estimate ~8–13 Hz), but confirming this requires resolving a persistent slow-convergence issue in the mesh near the head/neck transition, which is beyond what local mesh refinement (currently unavailable) can fix.

**Future work**: refine mesh at y≈−1.77, or attempt at coarser overall resolution to trade accuracy for tractable runtime.

## Attribution

CFD geometry derived from "Spinosaurus mirabilis" (https://skfb.ly/pKMVN) by Nobilis 2, licensed under [Creative Commons Attribution 4.0](http://creativecommons.org/licenses/by/4.0/).
# Spinosaurus mirabilis — crest hydrodynamics findings

Steady RANS CFD screening of the scimitar-crested *Spinosaurus mirabilis* head,
corrected to 2 m/s inlet velocity, run in SimScale. This is a hobbyist screening
study — not a validated engineering analysis.

## CFD setup

| Parameter | Value |
|-----------|-------|
| Fluid | Water, incompressible |
| Turbulence | k-omega SST |
| Inlet | Uy = +2 m/s at minimum-Y face |
| Outlet | Zero-gauge pressure at maximum-Y face |
| Walls | Slip walls (no viscous boundary layer — pressure/form drag only) |
| Iterations | 1,000 (steady, corrected run) |
| Cases | One Reynolds number, single valid steady run. Re_head ≈ 3×10⁶ (head length, global regime), Re_crest ≈ 8×10⁴ (crest width, local behavior) |
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

Initial steady RANS particle trace, ±7000 Pa scale.

## Key observations

- The animation uses a ±7000 Pa scale for visual clarity (2 m/s simulation). The absence of visible red/orange on the crest at this scale does not rule out unsteady loading there. This is a qualitative observation from one run, not a validated result.
- Final residuals at iteration 1000: Ux = 3.02e-4, Uy = 1.64e-5, Uz = 4.30e-4, k = 9.28e-5, omega = 4.31e-6, **p = 5.85e-3**. Convergence did not improve at the corrected, gentler flow — every residual field is roughly 2× higher than at the old 5 m/s run, counter to expectation.
- **Slip walls on the body surface** mean this run captures pressure/form effects only — no skin-friction drag. Pressure is still computed normally at the walls, but the slip condition is itself the likely reason the head/crest appears to create so little drag: without a viscous boundary layer, flow separation is delayed, the wake shrinks, and the front-to-back pressure difference that produces form drag is reduced. The low drag is therefore likely an artifact of the run setup, not a validated hydrodynamic result.
- **Geometry limitation**: the real S. mirabilis crest is asymmetric along the midline (Sereno et al. 2026), but this study used a symmetrized artist mesh (Nobilis 2). Geometry is derived from a publicly available artist reconstruction, not from fossil scan data or holotype measurements — this is an exploratory hydrodynamic study of an idealized shape, not a test of the actual specimen's morphology.
- The corrected steady pressure field (2 m/s inlet) shows no large static buildup at the crest — but for the slip-wall reason above, this cannot be read as "the crest is low-drag."

## Attribution

CFD geometry derived from "Spinosaurus mirabilis" (https://skfb.ly/pKMVN) by Nobilis 2, licensed under [Creative Commons Attribution 4.0](http://creativecommons.org/licenses/by/4.0/).
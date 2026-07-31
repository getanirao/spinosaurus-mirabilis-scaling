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
| Reference dynamic pressure | q = 0.5 rho U^2 = 1,995 Pa at 2 m/s |
| Outer side boundaries | Slip on the minimum/maximum X and Z faces |
| Body surface | Separate imported wall face (`face 77`); force-and-moment monitor assigned to this face |
| Body surface BC | Default no-slip wall with wall functions on `face 77` (implicit; no explicit BC assignment) |
| Force monitoring | Pressure and viscous forces integrated over `face 77` |
| Iterations | 1,000 (steady, corrected run) |
| Cases | One Reynolds number, single valid steady run. Re_head ≈ 3×10⁶ (head length, global regime), Re_crest ≈ 8×10⁴ (crest width, local behavior) |
| Mesh | 1.6M cells, 618.4k nodes; no grid-independence check |
| Geometry | Nobilis 2 artist mesh, voxel-solidified, SimScale Fit-to-Surface Wrap at resolution 8 |

## Raw data

All solver telemetry is in `results/simscale/mirabilis_crest_present_U2mps/`:

| File | Contents |
|------|----------|
| `raw/residuals.csv` | Global residual history (Ux, Uy, Uz, k, omega, p) across 1,000 iterations |
| `raw/Domain.csv` | Normalized domain convergence-monitor values |
| `raw/Inlets.csv` | Normalized inlet convergence-monitor values |
| `raw/Outlets.csv` | Normalized outlet convergence-monitor values |
| `raw/Walls.csv` | Normalized wall convergence-monitor values |

## Methodology

### Pressure-colored particle trace

![Pressure-colored steady RANS particle trace](https://raw.githubusercontent.com/getanirao/spinosaurus-mirabilis-scaling/main/results/simscale/mirabilis_crest_present_U2mps/figures/spinosaurus_crest_flow.gif)

The GIF shows particle-trace paths colored by static gauge pressure from
−3,693 to +2,269 Pa. It is a post-processing visualization of a steady RANS
solution, not a transient water-entry animation.

## Key observations

- The only inlet speed analyzed here is **2.0 m/s**.
- The freestream dynamic pressure, `q = 1,995 Pa`, is a reference scale rather
  than a measured peak pressure or a threshold for significance. Relative to
  this scale, the displayed gauge-pressure limits correspond to approximately
  `Cp = −1.85` and `Cp = +1.14`. These order-one pressure coefficients are not
  negligible in the flow model.
- Pressure magnitude alone does not determine hydrodynamic load. Net force
  requires integrating pressure and shear over the body surface, including
  direction: `F = integral(-p n + tau) dA`.
- At nominal zero yaw, the sagittal crest is nearly edge-on to the streamwise
  flow. Its axial projected area is therefore governed mainly by transverse
  thickness rather than its large lateral silhouette. A keel-like crest could
  produce modest axial drag while generating a much stronger lateral force or
  yawing moment under sideslip; this remains untested until matched yaw sweeps
  and crest-ablated controls are run.
- Final residuals at iteration 1000: Ux = 3.02e-4, Uy = 1.64e-5, Uz = 4.30e-4, k = 9.28e-5, omega = 4.31e-6, and **p = 5.85e-3**. The residuals decay, but the pressure solution is not tightly converged.
- The pressure-colored particle trace shows localized acceleration and wake structure around the idealized head. It does not by itself measure crest drag or establish a diving penalty.
- There is not yet a matched crest-ablated or *S. aegyptiacus* control run. Without a control, force decomposition, transient test, and grid-convergence study, this run cannot isolate the crest's hydrodynamic effect.
- **Geometry limitation**: the real S. mirabilis crest is asymmetric along the midline (Sereno et al. 2026), but this study used a symmetrized artist mesh (Nobilis 2). Geometry is derived from a publicly available artist reconstruction, not from fossil scan data or holotype measurements — this is an exploratory hydrodynamic study of an idealized shape, not a test of the actual specimen's morphology.
- The body no-slip condition was inherited from SimScale's default treatment of unassigned faces. Future runs should assign it explicitly.

## Attribution

CFD geometry derived from "Spinosaurus mirabilis" (https://skfb.ly/pKMVN) by Nobilis 2, licensed under [Creative Commons Attribution 4.0](http://creativecommons.org/licenses/by/4.0/).

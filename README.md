# Exploratory hydrodynamics of an idealized *Spinosaurus mirabilis* head

This repository documents steady and short transient incompressible RANS CFD
experiments on a public artist reconstruction of the scimitar-crested
*Spinosaurus mirabilis* head in water at a 2 m/s inlet velocity. It is a
hobbyist pilot study, not a validated engineering or paleobiological analysis.

## Result in brief

The clearest result is a repeatable **whole-head static-yaw response**. With the
same wrapped geometry held at +15° and -15° to the flow, the endpoint lateral
force and yaw moment reversed direction while retaining nearly the same
magnitude:

| Static yaw | Fx, lateral (N) | Fy, streamwise (N) | Fz (N) | Resultant force (N) | Mz, yaw (N·m) |
|---:|---:|---:|---:|---:|---:|
| 0° corrected baseline | -12.278 | 287.913 | 177.462 | 338.434 | -2.986 |
| +15° | +664.007 | 399.902 | 101.009 | 781.684 | +430.531 |
| -15° | -674.607 | 398.821 | 96.366 | 789.582 | -433.756 |

Between the two yawed cases, lateral-force magnitude differed by 1.58%,
streamwise force by 0.27%, yaw-moment magnitude by 0.75%, and resultant force
by 1.01%. The meshes differed by 0.46% in cell count. This sign reversal and
close magnitude agreement make a one-sided setup or meshing accident less
likely and support a numerically repeatable off-axis response for the modeled
whole head.

This result **does not isolate the crest**. The crest is fused to the head, the
posterior head is truncated, and the geometry is an artistic reconstruction.
Without a defensible crest-absent control, the load cannot be assigned to the
crest rather than the snout, skull, cut posterior surface, or their interaction.
The cases are also static sideslip tests, not simulations of an actively
swiveling head or prey capture.

The ±15° archives contain endpoint force and moment records at iteration 1,000,
but not their chart histories. SimScale marked both runs `Succeeded`, and their
mirror agreement is a useful consistency check, but neither fact proves a
time-window plateau. The yaw values are therefore reported as endpoints rather
than converged means.

## Simulation setup

| Parameter | Value |
|---|---|
| Fluid model | Water, incompressible |
| Turbulence model | k-ω SST |
| Inlet | 2 m/s along global +Y at the minimum-Y face |
| Outlet | Zero-gauge pressure at the maximum-Y face |
| Reference dynamic pressure | 1,995 Pa at 2 m/s |
| Domain | X: -1.75 to 1.75 m; Y: -5.81 to 5 m; Z: -0.5 to 4.5 m |
| Outer side boundaries | Slip on minimum/maximum X and Z for corrected Run 29 and both yaw cases |
| Head surface | `face 77@Flow region`; unassigned surface inherits SimScale's no-slip wall default with wall functions |
| Force monitor | Head surface only |
| Steady-run length | 1,000 iterations |
| Geometry | Nobilis 2 artist mesh, voxel-solidified and wrapped at resolution 8 |

For the yaw study, the same wrapped whole head was rotated ±15° about global Z
while the inlet remained fixed along +Y. The force monitor remained on the head.
The moment reference point was rotated with the geometry to
`(+0.456816, -1.704859, 1.972) m` for +15° and
`(-0.456816, -1.704859, 1.972) m` for -15°.

The response was pressure dominated. At +15°, the normal-pressure contribution
was +665.714 N in X and +441.371 N·m about Z; tangential contributions were
-1.706 N and -10.840 N·m. At -15°, the corresponding values were -676.467 N,
-444.738 N·m, +1.860 N, and +10.982 N·m.

## Repository layout

### Static-yaw study

`results/simscale/mirabilis_crest_present_U2mps_yaw_static/`

| Path | Contents |
|---|---|
| `raw/final_force_moment_yaw_plus15.csv` | Exact +15° pressure/normal, viscous/tangential, porous, and total endpoint components |
| `raw/final_force_moment_yaw_minus15.csv` | Exact -15° endpoint components |
| `processed/yaw_endpoint_summary.csv` | Compact 0°, +15°, and -15° force/moment summary |
| `processed/yaw_mirror_symmetry.csv` | Component-by-component mirror check and magnitude mismatch |
| `case-config/run_metadata.csv` | Run identity, transformation, mesh, domain, boundaries, and moment centers |
| `README.md` | Dataset provenance, calculations, and interpretation limits |

### Corrected zero-yaw baseline

`results/simscale/mirabilis_crest_present_U2mps_corrected_farfield_run29/`

| Path | Contents |
|---|---|
| `raw/forces_run29_corrected_farfield.csv` | Pressure, viscous, and total head-force histories over 1,000 iterations |
| `raw/final_force_moment_run29_corrected_farfield.csv` | Exact endpoint force and moment components from the OpenFOAM archive |
| `raw/residuals.csv` | Ux, Uy, Uz, k, ω, and p residual histories |
| `raw/Domain.csv`, `Inlets.csv`, `Outlets.csv`, `Walls.csv` | Normalized convergence-monitor exports |
| `figures/run29_particle_trace_velocity.png` | Static velocity-colored particle trace |
| `figures/run29_particle_trace_velocity.gif` | Animated particle trace shown below |

All six Run 29 history exports contain 1,000 data rows and end at iteration
1,000. The final 100 force samples are stable: mean
`(Fx, Fy, Fz) = (-12.229, 287.793, 177.409) N` with standard deviations
`(0.029, 0.082, 0.044) N`. Final residuals were Ux = 1.62e-5,
Uy = 9.33e-7, Uz = 1.57e-5, k = 9.94e-5, ω = 3.72e-7, and p = 1.89e-4.

### Older exploratory baseline

`results/simscale/mirabilis_crest_present_U2mps/` preserves the original
telemetry and solver configuration. Its outer X/Z faces had no explicit side
boundary assignment and therefore inherited no-slip. `forces_run3_face77.csv`
is the head-surface integral; `forces_run2_boxwide.csv` is an invalid seven-face
box-wide integral dominated by inlet/outlet momentum flux and must not be used
as head drag.

## Particle-trace visualization

![Velocity-colored corrected steady RANS particle trace](https://raw.githubusercontent.com/getanirao/spinosaurus-mirabilis-scaling/main/results/simscale/mirabilis_crest_present_U2mps_corrected_farfield_run29/figures/run29_particle_trace_velocity.gif)

This animation shows particles moving through the fixed velocity field of
corrected steady Run 29, colored from 0 to 3.016 m/s. It is not a transient
water-entry or head-motion animation and supplies no independent evidence of a
crest effect.

## Run history and data quality

| Case | Purpose | Mesh | Status in this repository |
|---|---|---:|---|
| Run 2 | Early force-monitor test | — | Invalid box-wide force integral retained for provenance |
| Older Run 3 | Zero-yaw head-force baseline with inherited no-slip outer sides | 1,187,479 cells | Complete endpoint/configuration data; superseded by Run 29 |
| Corrected Run 29 | Zero-yaw baseline with slip far field | 1,587,747 cells / 618,407 points | Stable 1,000-iteration force and residual histories |
| Static yaw +15° (`run41`) | Whole-head steady sideslip | 1,613,164 cells / 623,974 points | Exact iteration-1,000 endpoint; no history export |
| Static yaw -15° (`run48`) | Mirrored whole-head steady sideslip | 1,605,714 cells / 621,478 points | Exact iteration-1,000 endpoint; no history export |
| Short transient | Startup/oscillation pilot | — | 0.5 s inspected in SimScale; not exported here |

The short transient run did not reach a sustained periodic regime during its
0.5 s window. Forces were still drifting after an instantaneous-inlet startup,
so it is inconclusive rather than evidence that oscillation is absent.

The large OpenFOAM solution archives (about 150 MB per yaw case) are not stored
here because they duplicate field data hosted by SimScale. The compact raw CSVs
preserve the exact force/moment records extracted from those archives. The raw
SimScale history exports are otherwise left unchanged, including quoted numeric
fields and initial blank residual entries where the solver had not yet emitted a
value.

## Interpretation limits

- There is only one inlet speed and no grid-convergence study.
- The ±15° cases are endpoint comparisons; force, moment, and residual histories
  are still needed before reporting window means or temporal convergence.
- The head is an artist reconstruction, the posterior surface is truncated, and
  the moment origin is not a verified anatomical neck joint.
- No crest-absent, fossil-derived, or alternative-species control exists. A
  crestless surface invented by smoothing or filling the artist mesh would test
  that invented geometry, not the biological crest in isolation.
- Static yaw represents a held oblique orientation. It does not reproduce an
  angular acceleration, a rapid strike, neck motion, body turning, or prey flow.
- These data cannot quantify catch rate, swimming performance, muscle demand,
  diving ability, or ecological behavior.

The defensible hypothesis for future work is limited: **this idealized whole-head
shape may generate substantial hydrodynamic control loads when held oblique to a
2 m/s flow.** The mirrored runs support that numerical pattern but do not identify
the anatomical source of the load.

## Attribution

CFD geometry derived from [“Spinosaurus mirabilis” by Nobilis 2](https://skfb.ly/pKMVN), licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

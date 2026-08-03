# Static-yaw endpoint dataset

This folder contains the matched +15° and -15° steady-yaw cases from SimScale
project `Mirabilis Yaw 15deg Pilot` (`project_id = 1024734913210931576`). The
same wrapped whole-head geometry was rotated about global Z while the 2 m/s
inlet remained aligned with global +Y. Both cases used the corrected slip
far-field treatment, k-ω SST, a head-only force monitor, and 1,000 iterations.

## Cases

| Case | SimScale run | Mesh | Moment center (m) |
|---|---|---:|---|
| +15° | `Static yaw +15deg steady` (`run41`) | 1,613,164 cells / 623,974 points | (0.456816, -1.704859, 1.972) |
| -15° | `Static yaw -15deg mirror` (`run48`) | 1,605,714 cells / 621,478 points | (-0.456816, -1.704859, 1.972) |

The moment centers are mirrored locations representing the same physical point
on the rotated geometry.

## Files

- `raw/final_force_moment_yaw_plus15.csv` and
  `raw/final_force_moment_yaw_minus15.csv` preserve the exact normal/pressure,
  tangential/viscous, porous, and total force and moment components from each
  exported OpenFOAM `functionObjectProperties` record at iteration 1,000.
- `processed/yaw_endpoint_summary.csv` places the corrected 0° baseline and both
  yaw endpoints in one machine-readable table.
- `processed/yaw_mirror_symmetry.csv` checks the expected mirror relationships.
- `case-config/run_metadata.csv` records project/run identity and relevant setup.

## Mirror calculation

For reflection across the Y-Z plane, the expected force relationships are
`Fx(-15) = -Fx(+15)`, `Fy(-15) = Fy(+15)`, and
`Fz(-15) = Fz(+15)`. Moments are axial vectors, so the expected relationships
are `Mx(-15) = Mx(+15)`, `My(-15) = -My(+15)`, and
`Mz(-15) = -Mz(+15)`.

`mirror_residual` in the processed CSV is the -15° value minus the +15° value
for same-sign relationships, and their sum for opposite-sign relationships.
`magnitude_mismatch_percent` is the absolute difference in magnitudes divided
by their mean magnitude.

The yaw-relevant components agree closely: lateral-force magnitude differs by
1.58%, yaw-moment magnitude by 0.75%, streamwise force by 0.27%, and resultant
force by 1.01%. `Mx` has a large relative mismatch because both values are very
small compared with the approximately 432 N·m yaw moment; it is retained for
transparency rather than treated as a primary yaw metric.

## Interpretation limit

These are whole-head static-sideslip endpoints. The close mirrored response is
a numerical consistency check, not evidence that the crest caused the load.
The crest is fused to the head, the posterior geometry is truncated, and the
mesh is an artist reconstruction. The archives do not contain force, moment, or
residual chart histories, so the values are not labeled as converged-window
means. Neither case simulates angular head motion, a prey strike, or neck loads.

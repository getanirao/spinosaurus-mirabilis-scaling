#!/usr/bin/env python3
"""Sensitivity model for hydrodynamic costs of the Spinosaurus cranial crest.

This is not computational fluid dynamics and cannot establish that either animal
could or could not dive. It uses projected area, pressure drag, and skin-friction
terms to identify which directions of movement would be most sensitive to the
crest geometry.

The important anatomical point is that the scimitar crest is sagittal. Its full
lateral silhouette is therefore exposed during off-axis head movement. In a
head-first entry, the crest's full vertical span still contributes to the leading
area, but its lateral side profile does not.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_INPUT_FILE = Path(__file__).with_name("crest_hydrodynamics_inputs.csv")
TAXA = ("Spinosaurus mirabilis", "Spinosaurus aegyptiacus")

METRICS = {
    "aligned_drag_n": "N",
    "aligned_base_moment_nm": "N m",
    "head_first_entry_drag_n": "N",
    "head_first_entry_base_moment_nm": "N m",
    "off_axis_drag_n": "N",
    "off_axis_base_moment_nm": "N m",
    "off_axis_to_aligned_drag_ratio": "ratio",
    "aligned_drag_to_tail_thrust_fraction": "fraction",
}


def load_parameter_ranges(path: Path) -> pd.DataFrame:
    """Load and validate sourced measurements and declared sensitivity ranges."""
    frame = pd.read_csv(path)
    required = {
        "taxon",
        "parameter",
        "lower",
        "upper",
        "unit",
        "evidence_status",
        "basis",
        "url",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise KeyError(f"Missing input columns: {sorted(missing)}")

    frame["lower"] = pd.to_numeric(frame["lower"], errors="raise")
    frame["upper"] = pd.to_numeric(frame["upper"], errors="raise")
    if (frame["lower"] < 0).any() or (frame["upper"] < frame["lower"]).any():
        raise ValueError("Every parameter range must be non-negative and ordered lower <= upper.")

    expected = {
        (taxon, parameter)
        for taxon in (*TAXA, "shared")
        for parameter in (
            ("crest_height_m", "crest_chord_m", "crest_thickness_m")
            if taxon != "shared"
            else (
                "speed_m_s",
                "head_first_entry_speed_m_s",
                "immersion_fraction",
                "off_axis_angle_deg",
                "edge_pressure_cd",
                "head_first_entry_cd",
                "broadside_pressure_cd",
                "skin_friction_cf",
                "water_density_kg_m3",
            )
        )
    }
    observed = set(zip(frame["taxon"], frame["parameter"], strict=True))
    missing_parameters = expected.difference(observed)
    if missing_parameters:
        raise KeyError(f"Missing parameter ranges: {sorted(missing_parameters)}")
    return frame


def sample_range(frame: pd.DataFrame, taxon: str, parameter: str, samples: int, rng: np.random.Generator) -> np.ndarray:
    row = frame.loc[(frame["taxon"] == taxon) & (frame["parameter"] == parameter)]
    if len(row) != 1:
        raise ValueError(f"Expected one range for {taxon!r} / {parameter!r}.")
    lower = float(row["lower"].iloc[0])
    upper = float(row["upper"].iloc[0])
    return rng.uniform(lower, upper, size=samples)


def published_tail_thrust_reference(speed_m_s: np.ndarray) -> np.ndarray:
    """Return the eLife S. aegyptiacus tail-thrust curve as a scale reference.

    This is not a force model for S. mirabilis. It is included only to show the
    size of an incremental crest force relative to a published whole-animal model.
    """
    thrust_n = -164.93 + 1899.1 * speed_m_s - 896.35 * speed_m_s**2
    return np.maximum(thrust_n, 1.0)


def simulate_taxon(
    parameters: pd.DataFrame,
    taxon: str,
    shared: dict[str, np.ndarray],
    samples: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Simulate directional crest loads for one taxon across uncertainty ranges."""
    height = sample_range(parameters, taxon, "crest_height_m", samples, rng)
    chord = sample_range(parameters, taxon, "crest_chord_m", samples, rng)
    thickness = sample_range(parameters, taxon, "crest_thickness_m", samples, rng)

    submerged_height = height * shared["immersion_fraction"]
    dynamic_pressure = 0.5 * shared["water_density_kg_m3"] * shared["speed_m_s"] ** 2
    wetted_side_area = 2.0 * submerged_height * chord
    skin_drag = dynamic_pressure * shared["skin_friction_cf"] * wetted_side_area

    # A sagittal crest is edge-on during aligned movement through the water.
    aligned_pressure_area = submerged_height * thickness
    aligned_drag = dynamic_pressure * shared["edge_pressure_cd"] * aligned_pressure_area + skin_drag

    # The reconstruction's near-perpendicular crest meets head-first flow along a
    # leading edge spanning the crest height. This is a quasi-steady force estimate,
    # not an unsteady slamming or cavitation model.
    entry_dynamic_pressure = (
        0.5 * shared["water_density_kg_m3"] * shared["head_first_entry_speed_m_s"] ** 2
    )
    entry_skin_drag = entry_dynamic_pressure * shared["skin_friction_cf"] * wetted_side_area
    head_first_entry_drag = (
        entry_dynamic_pressure * shared["head_first_entry_cd"] * aligned_pressure_area
        + entry_skin_drag
    )

    # Off-axis flow progressively exposes the lateral silhouette of the crest.
    off_axis_pressure_area = submerged_height * chord * np.sin(shared["off_axis_angle_rad"])
    off_axis_drag = dynamic_pressure * shared["broadside_pressure_cd"] * off_axis_pressure_area + skin_drag

    crest_base_lever_m = submerged_height / 2.0
    tail_thrust = published_tail_thrust_reference(shared["speed_m_s"])

    return pd.DataFrame(
        {
            "taxon": taxon,
            "crest_height_m": height,
            "crest_chord_m": chord,
            "crest_thickness_m": thickness,
            "speed_m_s": shared["speed_m_s"],
            "head_first_entry_speed_m_s": shared["head_first_entry_speed_m_s"],
            "immersion_fraction": shared["immersion_fraction"],
            "off_axis_angle_deg": np.degrees(shared["off_axis_angle_rad"]),
            "aligned_drag_n": aligned_drag,
            "aligned_base_moment_nm": aligned_drag * crest_base_lever_m,
            "head_first_entry_drag_n": head_first_entry_drag,
            "head_first_entry_base_moment_nm": head_first_entry_drag * crest_base_lever_m,
            "off_axis_drag_n": off_axis_drag,
            "off_axis_base_moment_nm": off_axis_drag * crest_base_lever_m,
            "off_axis_to_aligned_drag_ratio": off_axis_drag / np.maximum(aligned_drag, 1e-12),
            "aligned_drag_to_tail_thrust_fraction": aligned_drag / tail_thrust,
        }
    )


def run_simulation(parameters: pd.DataFrame, samples: int, seed: int) -> pd.DataFrame:
    """Run paired draws so the taxa share the same water and movement conditions."""
    rng = np.random.default_rng(seed)
    speed = sample_range(parameters, "shared", "speed_m_s", samples, rng)
    shared = {
        "speed_m_s": speed,
        "head_first_entry_speed_m_s": sample_range(
            parameters, "shared", "head_first_entry_speed_m_s", samples, rng
        ),
        "immersion_fraction": sample_range(parameters, "shared", "immersion_fraction", samples, rng),
        "off_axis_angle_rad": np.radians(
            sample_range(parameters, "shared", "off_axis_angle_deg", samples, rng)
        ),
        "edge_pressure_cd": sample_range(parameters, "shared", "edge_pressure_cd", samples, rng),
        "head_first_entry_cd": sample_range(
            parameters, "shared", "head_first_entry_cd", samples, rng
        ),
        "broadside_pressure_cd": sample_range(parameters, "shared", "broadside_pressure_cd", samples, rng),
        "skin_friction_cf": sample_range(parameters, "shared", "skin_friction_cf", samples, rng),
        "water_density_kg_m3": sample_range(
            parameters, "shared", "water_density_kg_m3", samples, rng
        ),
    }
    return pd.concat(
        [simulate_taxon(parameters, taxon, shared, samples, rng) for taxon in TAXA],
        ignore_index=True,
    )


def summarize_samples(samples: pd.DataFrame) -> pd.DataFrame:
    """Return 5th, 50th, and 95th percentiles for taxon loads and paired ratios."""
    rows: list[dict[str, object]] = []
    for taxon, group in samples.groupby("taxon", sort=False):
        for metric, unit in METRICS.items():
            values = group[metric].to_numpy()
            p05, median, p95 = np.quantile(values, [0.05, 0.50, 0.95])
            rows.append(
                {
                    "comparison": taxon,
                    "metric": metric,
                    "unit": unit,
                    "p05": p05,
                    "median": median,
                    "p95": p95,
                }
            )

    mirabilis = samples.loc[samples["taxon"] == "Spinosaurus mirabilis"].reset_index(drop=True)
    aegyptiacus = samples.loc[samples["taxon"] == "Spinosaurus aegyptiacus"].reset_index(drop=True)
    for metric, unit in METRICS.items():
        ratio = mirabilis[metric].to_numpy() / np.maximum(aegyptiacus[metric].to_numpy(), 1e-12)
        p05, median, p95 = np.quantile(ratio, [0.05, 0.50, 0.95])
        rows.append(
            {
                "comparison": "S. mirabilis / S. aegyptiacus",
                "metric": f"{metric}_ratio",
                "unit": "ratio",
                "p05": p05,
                "median": median,
                "p95": p95,
            }
        )
    return pd.DataFrame(rows)


def summary_value(summary: pd.DataFrame, comparison: str, metric: str, column: str = "median") -> float:
    matches = summary.loc[(summary["comparison"] == comparison) & (summary["metric"] == metric), column]
    if len(matches) != 1:
        raise KeyError(f"Missing summary value for {comparison!r} / {metric!r}.")
    return float(matches.iloc[0])


def build_report(summary: pd.DataFrame, parameters: pd.DataFrame, samples: int, seed: int) -> str:
    """Create an interpretation that keeps the model's limits explicit."""
    ratio_name = "S. mirabilis / S. aegyptiacus"
    aligned_ratio = summary_value(summary, ratio_name, "aligned_drag_n_ratio")
    entry_ratio = summary_value(summary, ratio_name, "head_first_entry_drag_n_ratio")
    entry_moment_ratio = summary_value(
        summary, ratio_name, "head_first_entry_base_moment_nm_ratio"
    )
    off_axis_ratio = summary_value(summary, ratio_name, "off_axis_drag_n_ratio")
    moment_ratio = summary_value(summary, ratio_name, "off_axis_base_moment_nm_ratio")
    mirabilis_forward = summary_value(summary, "Spinosaurus mirabilis", "aligned_drag_n")
    mirabilis_entry = summary_value(summary, "Spinosaurus mirabilis", "head_first_entry_drag_n")
    mirabilis_entry_moment = summary_value(
        summary, "Spinosaurus mirabilis", "head_first_entry_base_moment_nm"
    )
    mirabilis_off_axis = summary_value(summary, "Spinosaurus mirabilis", "off_axis_drag_n")
    mirabilis_anisotropy = summary_value(
        summary, "Spinosaurus mirabilis", "off_axis_to_aligned_drag_ratio"
    )
    tail_fraction = summary_value(
        summary, "Spinosaurus mirabilis", "aligned_drag_to_tail_thrust_fraction"
    )

    sourced = int((parameters["evidence_status"] != "assumption").sum())
    assumed = int((parameters["evidence_status"] == "assumption").sum())
    lines = [
        "Spinosaurus cranial-crest hydrodynamic sensitivity analysis",
        "=" * 58,
        "",
        f"Monte Carlo draws: {samples:,}",
        f"Random seed: {seed}",
        f"Input rows: {len(parameters)} ({sourced} source-informed, {assumed} explicit assumptions)",
        "",
        "What the model actually represents",
        "- Freshwater drag on the crest only during a crest-contact episode.",
        "- The crest is represented as a sagittal thickened blade with uncertain height, fore-aft chord, and thickness.",
        "- Aligned movement and head-first entry expose height x thickness; off-axis motion exposes the larger lateral profile.",
        "- The head-first entry force is a quasi-steady approximation, not a CFD water-entry/slamming simulation.",
        "- Moments are about the crest base, not an estimated neck joint or whole-animal center of mass.",
        "",
        "Median modeled result",
        f"- S. mirabilis aligned crest drag: {mirabilis_forward:.2f} N.",
        f"- S. mirabilis head-first entry crest load: {mirabilis_entry:.2f} N.",
        f"- S. mirabilis head-first entry crest-base moment: {mirabilis_entry_moment:.2f} N m.",
        f"- S. mirabilis off-axis crest drag: {mirabilis_off_axis:.2f} N.",
        f"- S. mirabilis off-axis / aligned drag anisotropy: {mirabilis_anisotropy:.1f}x.",
        f"- S. mirabilis aligned crest drag as a fraction of the published S. aegyptiacus tail-thrust reference: {tail_fraction:.3f}.",
        "",
        "Paired comparison with the incomplete S. aegyptiacus UCPC-2 crest baseline",
        f"- Aligned drag ratio: {aligned_ratio:.1f}x.",
        f"- Head-first entry drag ratio: {entry_ratio:.1f}x.",
        f"- Head-first entry crest-base moment ratio: {entry_moment_ratio:.1f}x.",
        f"- Off-axis drag ratio: {off_axis_ratio:.1f}x.",
        f"- Off-axis crest-base moment ratio: {moment_ratio:.1f}x.",
        "",
        "Interpretation",
        "- The model's central prediction is directional, not simply 'large crest equals large drag.'",
        "- The near-perpendicular crest geometry increases the leading height in a head-first entry. Even so, the relevant area is height x thickness, not the full lateral side profile. This model therefore cannot, by projected area alone, prove that diving was impossible.",
        "- The crest becomes much more costly when water flow is off-axis. That creates a testable functional prediction: rapid lateral underwater head sweeps or oblique strikes should impose a substantially larger crest load on S. mirabilis than on the S. aegyptiacus fragment baseline.",
        "- Normal wading with the crest above water is outside this drag calculation and receives no modeled penalty.",
        "",
        "What would make this publishable-quality",
        "- Replace the assumed S. mirabilis crest thickness and lateral profile with CT-derived cross-sections or calibrated photogrammetry of MNBH JEN1/JEN2/JEN3.",
        "- Obtain a defensible, non-eroded S. aegyptiacus crest reconstruction rather than relying on UCPC-2 as a fragment baseline.",
        "- Add skull and neck geometry to convert crest-base moments into neck-joint moments, then test the strongest cases with CFD or a physical flume model.",
        "",
        "Bottom line",
        "- This first-pass physics model supports a sharper hypothesis than a generic 'water is bad for the crest': the scimitar crest may selectively penalize off-axis underwater pursuit motions while leaving stationary wading and low-speed aligned movement comparatively unconstrained.",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a reproducible crest-only hydrodynamic sensitivity analysis."
    )
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT_FILE)
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-markdown", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.samples < 1:
        raise ValueError("--samples must be at least 1.")

    parameters = load_parameter_ranges(args.input_file)
    samples = run_simulation(parameters, args.samples, args.seed)
    summary = summarize_samples(samples)
    report = build_report(summary, parameters, args.samples, args.seed)
    print(report)

    if args.output_csv is not None:
        summary.to_csv(args.output_csv, index=False, float_format="%.8f")
    if args.output_markdown is not None:
        args.output_markdown.write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

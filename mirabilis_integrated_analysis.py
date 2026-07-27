#!/usr/bin/env python3
"""Integrated analysis of Spinosaurus mirabilis using quantitative and qualitative evidence.

The goal here is not to predict environment from geology.
Instead, we use:
- quantitative morphology (crest height, estimated body length)
- density context from the better-documented S. aegyptiacus literature
- qualitative ecological context

to make a species-level generalization about what makes S. mirabilis distinctive.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_MORPH_FILE = Path(__file__).with_name("mirabilis_evidence.csv")
DEFAULT_HABITAT_FILE = Path(__file__).with_name("mirabilis_habitat_evidence.csv")
DEFAULT_DENSITY_FILE = Path(__file__).with_name("mirabilis_density_context.csv")

FAMILY_ORDER = (
    "inland_riparian",
    "coastal_inland_margin",
    "coastal_margin",
    "nearshore_marginal",
    "nearshore_marine",
    "inland_access",
)

FAMILY_LABELS = {
    "inland_riparian": "inland / riparian",
    "coastal_inland_margin": "coastal + inland margin",
    "coastal_margin": "coastal margin",
    "nearshore_marginal": "nearshore / marginal",
    "nearshore_marine": "nearshore / marine",
    "inland_access": "inland access",
}


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [
        re.sub(r"[^0-9a-zA-Z]+", "_", str(column).strip().lower()).strip("_")
        for column in normalized.columns
    ]
    return normalized


def parse_numeric_value(raw_value: str) -> tuple[float | None, float | None, float | None]:
    text = str(raw_value).strip().lower()
    if not text:
        return None, None, None

    cleaned = text.replace(",", "")
    match = re.fullmatch(r"(?P<low>\d+(?:\.\d+)?)\s*-\s*(?P<high>\d+(?:\.\d+)?)", cleaned)
    if match:
        low = float(match.group("low"))
        high = float(match.group("high"))
        return low, high, (low + high) / 2.0

    match = re.fullmatch(r"(?P<value>\d+(?:\.\d+)?)", cleaned)
    if match:
        value = float(match.group("value"))
        return value, value, value

    return None, None, None


def load_morphology(path: Path) -> pd.DataFrame:
    frame = normalize_columns(pd.read_csv(path))
    required = {"source", "date", "category", "metric", "value", "unit", "notes", "url"}
    missing = required.difference(frame.columns)
    if missing:
        raise KeyError(f"Missing required morphology columns: {sorted(missing)}")

    parsed = frame["value"].apply(parse_numeric_value)
    frame["numeric_low"] = parsed.apply(lambda item: item[0])
    frame["numeric_high"] = parsed.apply(lambda item: item[1])
    frame["numeric_midpoint"] = parsed.apply(lambda item: item[2])
    return frame


def load_habitat(path: Path) -> pd.DataFrame:
    frame = normalize_columns(pd.read_csv(path))
    required = {
        "taxon",
        "source",
        "date",
        "evidence_type",
        "environment_family",
        "descriptor",
        "strength",
        "url",
        "notes",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise KeyError(f"Missing required habitat columns: {sorted(missing)}")

    frame["strength"] = pd.to_numeric(frame["strength"], errors="coerce").fillna(1.0)
    frame["environment_family"] = frame["environment_family"].str.strip().str.lower()
    frame["taxon"] = frame["taxon"].str.strip()
    return frame


def load_density_context(path: Path) -> pd.DataFrame:
    frame = normalize_columns(pd.read_csv(path))
    required = {"taxon", "source", "date", "metric", "value", "unit", "notes", "url"}
    missing = required.difference(frame.columns)
    if missing:
        raise KeyError(f"Missing required density columns: {sorted(missing)}")

    parsed = frame["value"].apply(parse_numeric_value)
    frame["numeric_low"] = parsed.apply(lambda item: item[0])
    frame["numeric_high"] = parsed.apply(lambda item: item[1])
    frame["numeric_midpoint"] = parsed.apply(lambda item: item[2])
    return frame


def morphology_summary(frame: pd.DataFrame) -> dict[str, float]:
    crest = frame.loc[frame["metric"] == "crest_height"]
    body_length = frame.loc[frame["metric"] == "body_length"]
    mass = frame.loc[frame["metric"] == "mass"]

    crest_cm = float(crest["numeric_midpoint"].iloc[0]) if not crest.empty else np.nan
    body_length_m = float(body_length["numeric_midpoint"].mean()) if not body_length.empty else np.nan
    body_low = float(body_length["numeric_low"].min()) if not body_length.empty else np.nan
    body_high = float(body_length["numeric_high"].max()) if not body_length.empty else np.nan
    mass_low = float(mass["numeric_low"].min()) if not mass.empty else np.nan
    mass_high = float(mass["numeric_high"].max()) if not mass.empty else np.nan

    crest_to_body_pct = (crest_cm / 100.0) / body_length_m * 100.0 if body_length_m and crest_cm else np.nan
    body_spread_pct = ((body_high - body_low) / body_length_m * 100.0) if body_length_m else np.nan
    mass_mid = float(mass["numeric_midpoint"].mean()) if not mass.empty else np.nan

    return {
        "crest_cm": crest_cm,
        "body_length_m": body_length_m,
        "body_low_m": body_low,
        "body_high_m": body_high,
        "mass_low_t": mass_low,
        "mass_high_t": mass_high,
        "mass_mid_t": mass_mid,
        "crest_to_body_pct": crest_to_body_pct,
        "body_spread_pct": body_spread_pct,
    }


def habitat_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for taxon, group in frame.groupby("taxon", sort=True):
        total_strength = float(group["strength"].sum())
        family_scores = (
            group.groupby("environment_family")["strength"].sum().reindex(FAMILY_ORDER, fill_value=0.0)
        )
        inland_score = float(
            family_scores.get("inland_riparian", 0.0) + family_scores.get("inland_access", 0.0)
        )
        coastal_score = float(
            family_scores.get("coastal_margin", 0.0)
            + family_scores.get("coastal_inland_margin", 0.0)
            + family_scores.get("nearshore_marginal", 0.0)
            + family_scores.get("nearshore_marine", 0.0)
        )
        dominant_family = family_scores.idxmax() if family_scores.max() > 0 else "unknown"
        rows.append(
            {
                "taxon": taxon,
                "total_strength": total_strength,
                "dominant_family": dominant_family,
                "dominant_family_label": FAMILY_LABELS.get(dominant_family, dominant_family),
                "inland_score": inland_score,
                "coastal_score": coastal_score,
                "balance": inland_score - coastal_score,
                "inland_share": (inland_score / total_strength) if total_strength else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["taxon"]).reset_index(drop=True)


def density_context_summary(frame: pd.DataFrame) -> pd.DataFrame:
    numeric = frame.dropna(subset=["numeric_midpoint"]).copy()
    if numeric.empty:
        return pd.DataFrame(columns=["taxon", "metric", "midpoint", "notes"])

    rows = []
    for (taxon, metric), group in numeric.groupby(["taxon", "metric"], sort=True):
        rows.append(
            {
                "taxon": taxon,
                "metric": metric,
                "midpoint": float(group["numeric_midpoint"].mean()),
                "unit": group["unit"].iloc[0],
                "source_count": int(group["source"].nunique()),
                "notes": "; ".join(sorted(group["notes"].unique())),
            }
        )
    return pd.DataFrame(rows).sort_values(["taxon", "metric"]).reset_index(drop=True)


def build_report(morphology: pd.DataFrame, habitat: pd.DataFrame, density: pd.DataFrame) -> str:
    morph = morphology_summary(morphology)
    habitat_sum = habitat_summary(habitat)
    density_sum = density_context_summary(density)

    mirabilis = habitat_sum.loc[habitat_sum["taxon"] == "Spinosaurus mirabilis"]
    aegyptiacus = habitat_sum.loc[habitat_sum["taxon"] == "Spinosaurus aegyptiacus"]
    density_aegy = density_sum.loc[density_sum["taxon"] == "Spinosaurus aegyptiacus"]

    lines: list[str] = []
    lines.append("Spinosaurus mirabilis integrated synthesis")
    lines.append("=" * 43)
    lines.append("")
    lines.append(f"Morphology rows: {len(morphology)}")
    lines.append(f"Habitat rows: {len(habitat)}")
    lines.append(f"Density-context rows: {len(density)}")
    lines.append("")

    lines.append("Quantitative morphology")
    lines.append(
        f"- Crest height: {morph['crest_cm']:.0f} cm"
        if not np.isnan(morph["crest_cm"])
        else "- Crest height: unavailable"
    )
    lines.append(
        f"- Estimated body length: {morph['body_low_m']:.1f} to {morph['body_high_m']:.1f} m "
        f"(midpoint {morph['body_length_m']:.1f} m)"
        if not np.isnan(morph["body_length_m"])
        else "- Estimated body length: unavailable"
    )
    if not np.isnan(morph["crest_to_body_pct"]):
        lines.append(
            f"- Crest-to-body-length ratio: {morph['crest_to_body_pct']:.1f}% of body length"
        )
    if not np.isnan(morph["body_spread_pct"]):
        lines.append(
            f"- Body-length uncertainty band: {morph['body_spread_pct']:.1f}% of midpoint length"
        )
    if not np.isnan(morph["mass_mid_t"]):
        lines.append(
            f"- Mass estimate midpoint: {morph['mass_mid_t']:.1f} tonnes"
        )
    lines.append("")

    lines.append("Context from S. aegyptiacus density work")
    if not density_aegy.empty:
        for _, row in density_aegy.iterrows():
            if row["metric"] == "mean_whole_body_density":
                lines.append(f"- Whole-body density estimate: {row['midpoint']:.0f} {row['unit']}")
            elif row["metric"] == "body_mass":
                lines.append(f"- Adult flesh-model mass: {row['midpoint']:.0f} {row['unit']}")
            elif row["metric"] == "juvenile_femur_cg":
                lines.append(f"- Juvenile femur compactness: {row['midpoint']:.3f}")
            elif row["metric"] == "juvenile_femur_length":
                lines.append(f"- Juvenile femur length used in the context literature: {row['midpoint']:.1f} {row['unit']}")
    lines.append(
        "- The density literature shows why a single compactness number is not enough by itself: age, body size, and whole-body pneumaticity matter."
    )
    lines.append("")

    lines.append("Qualitative habitat context")
    lines.append(
        f"- S. mirabilis: {mirabilis['dominant_family_label'].iloc[0]} "
        f"(inland share {mirabilis['inland_share'].iloc[0]:.2f})"
        if not mirabilis.empty
        else "- S. mirabilis habitat coding unavailable"
    )
    lines.append(
        f"- S. aegyptiacus: {aegyptiacus['dominant_family_label'].iloc[0]} "
        f"(inland share {aegyptiacus['inland_share'].iloc[0]:.2f})"
        if not aegyptiacus.empty
        else "- S. aegyptiacus habitat coding unavailable"
    )
    lines.append("")

    lines.append("Generalization")
    lines.append(
        "- S. mirabilis is best read as a crest-dominant spinosaur that is morphologically striking at the skull "
        "and ecologically anchored in inland-riparian settings."
    )
    lines.append(
        "- The combination of a large display crest, incomplete/likely immature body material, and riverine context "
        "suggests a species-level signal centered on display and habitat differentiation, not a new claim that density alone proves aquatic behavior."
    )
    lines.append(
        "- In short: mirabilis looks less like a body-plan revolution and more like a distinct inland-river spinosaur with an exaggerated cranial display feature."
    )
    lines.append("")
    lines.append("Why this matters")
    lines.append(
        "- This generalization uses quantitative morphology to measure how unusual the crest is, density context to avoid overreading bone compactness, "
        "and qualitative ecology to interpret what the morphology may have meant in life."
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Produce an integrated morphology + density + ecology synthesis for S. mirabilis."
    )
    parser.add_argument("--morph-file", type=Path, default=DEFAULT_MORPH_FILE)
    parser.add_argument("--habitat-file", type=Path, default=DEFAULT_HABITAT_FILE)
    parser.add_argument("--density-file", type=Path, default=DEFAULT_DENSITY_FILE)
    parser.add_argument("--output-markdown", type=Path, default=None)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    morphology = load_morphology(args.morph_file)
    habitat = load_habitat(args.habitat_file)
    density = load_density_context(args.density_file)

    report = build_report(morphology, habitat, density)
    print(report)

    if args.output_markdown is not None:
        args.output_markdown.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

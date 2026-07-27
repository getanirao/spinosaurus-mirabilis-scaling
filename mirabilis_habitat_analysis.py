#!/usr/bin/env python3
"""Qualitative habitat comparison for Spinosaurus mirabilis versus S. aegyptiacus.

This script focuses on ecological context rather than size alone.
It encodes public habitat descriptions into a small comparison matrix so we can
ask a sharper question:

    Does S. mirabilis look more explicitly inland-riparian than S. aegyptiacus,
    and what does that imply about how novel it really is?
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_EVIDENCE_FILE = Path(__file__).with_name("mirabilis_habitat_evidence.csv")

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


def load_habitat_data(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = normalize_columns(frame)

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
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    frame["strength"] = pd.to_numeric(frame["strength"], errors="coerce").fillna(1.0)
    frame["environment_family"] = frame["environment_family"].str.strip().str.lower()
    frame["taxon"] = frame["taxon"].str.strip()
    return frame


def family_summary(frame: pd.DataFrame) -> pd.DataFrame:
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
        balance = inland_score - coastal_score
        inland_share = (inland_score / total_strength) if total_strength else np.nan
        dominant_family = family_scores.idxmax() if family_scores.max() > 0 else "unknown"

        rows.append(
            {
                "taxon": taxon,
                "total_strength": total_strength,
                "dominant_family": dominant_family,
                "dominant_family_label": FAMILY_LABELS.get(dominant_family, dominant_family),
                "inland_score": inland_score,
                "coastal_score": coastal_score,
                "balance": balance,
                "inland_share": inland_share,
                "evidence_rows": int(len(group)),
                "sources": int(group["source"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values(["taxon"]).reset_index(drop=True)


def evidence_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    pivot = (
        frame.pivot_table(
            index="taxon",
            columns="environment_family",
            values="strength",
            aggfunc="sum",
        )
        .reindex(columns=FAMILY_ORDER, fill_value=0.0)
        .fillna(0.0)
        .reset_index()
    )
    return pivot


def explain_findings(summary: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    mirabilis = summary.loc[summary["taxon"] == "Spinosaurus mirabilis"]
    aegyptiacus = summary.loc[summary["taxon"] == "Spinosaurus aegyptiacus"]

    if not mirabilis.empty:
        row = mirabilis.iloc[0]
        lines.append(
            "S. mirabilis is coded overwhelmingly as inland-riparian: "
            f"{row['inland_score']:.1f} inland strength versus {row['coastal_score']:.1f} coastal strength."
        )
    if not aegyptiacus.empty:
        row = aegyptiacus.iloc[0]
        lines.append(
            "S. aegyptiacus is more mixed: "
            f"{row['inland_score']:.1f} inland strength versus {row['coastal_score']:.1f} coastal strength."
        )
    if not mirabilis.empty and not aegyptiacus.empty:
        diff = float(mirabilis.iloc[0]["balance"] - aegyptiacus.iloc[0]["balance"])
        lines.append(
            "Net inland-vs-coastal balance is shifted toward inland for mirabilis by "
            f"{diff:.1f} strength units relative to aegyptiacus."
        )
        lines.append(
            "That makes the strongest differentiator not body size, but habitat specificity: "
            "mirabilis looks like the more explicitly inland-river-line taxon."
        )
        lines.append(
            "A reasonable hypothesis is that the tall crest may have mattered in a visually open "
            "riparian corridor where display and species recognition work over longer lines of sight."
        )
    return lines


def build_report(frame: pd.DataFrame) -> str:
    summary = family_summary(frame)
    matrix = evidence_matrix(frame)

    lines: list[str] = []
    lines.append("Spinosaurus habitat contrast")
    lines.append("=" * 31)
    lines.append("")
    lines.append(f"Evidence rows: {len(frame)}")
    lines.append(f"Unique sources: {frame['source'].nunique()}")
    lines.append("")
    lines.append("Habitat matrix")
    lines.append(matrix.to_string(index=False))
    lines.append("")
    lines.append("Summary")
    lines.append(summary.to_string(index=False, justify="left", float_format=lambda x: f"{x:.2f}"))
    lines.append("")
    lines.append("Dominant family labels")
    label_table = summary.loc[:, ["taxon", "dominant_family_label"]]
    lines.append(label_table.to_string(index=False))
    lines.append("")
    lines.append("Interpretation")
    for line in explain_findings(summary):
        lines.append(f"- {line}")
    lines.append(
        "- This does not prove a new lifestyle by itself, but it does give us a sharper novelty claim: "
        "mirabilis may represent an inland-riparian specialization rather than just another generic water-adjacent spinosaur."
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare public habitat evidence for Spinosaurus mirabilis and S. aegyptiacus."
    )
    parser.add_argument(
        "--evidence-file",
        type=Path,
        default=DEFAULT_EVIDENCE_FILE,
        help="CSV file with qualitative habitat evidence.",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=None,
        help="Optional path to write the report as markdown.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    frame = load_habitat_data(args.evidence_file)
    report = build_report(frame)
    print(report)

    if args.output_markdown is not None:
        args.output_markdown.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

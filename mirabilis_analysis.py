#!/usr/bin/env python3
"""Analyze public evidence around Spinosaurus mirabilis and the UChicago Fossil Lab.

This is a small, source-backed prototype meant to convert public claims into a
compact quantitative summary. It is intentionally simple so it can be extended
later with fuller measurement tables or literature-extracted data.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_EVIDENCE_FILE = Path(__file__).with_name("mirabilis_evidence.csv")


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


def load_evidence(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = normalize_columns(frame)
    for required in ("source", "date", "category", "metric", "value", "unit", "notes", "url"):
        if required not in frame.columns:
            raise KeyError(f"Missing required column: {required}")

    parsed = frame["value"].apply(parse_numeric_value)
    frame["numeric_low"] = parsed.apply(lambda item: item[0])
    frame["numeric_high"] = parsed.apply(lambda item: item[1])
    frame["numeric_midpoint"] = parsed.apply(lambda item: item[2])
    return frame


def summarize_numeric_claims(frame: pd.DataFrame) -> pd.DataFrame:
    numeric = frame.dropna(subset=["numeric_midpoint"]).copy()
    if numeric.empty:
        return pd.DataFrame(
            columns=[
                "metric",
                "sources",
                "low",
                "high",
                "midpoint",
                "spread",
                "relative_spread_pct",
            ]
        )

    rows = []
    for metric, group in numeric.groupby("metric", sort=True):
        low = float(group["numeric_low"].min())
        high = float(group["numeric_high"].max())
        midpoint = float(group["numeric_midpoint"].mean())
        spread = high - low
        relative_spread = (spread / midpoint * 100.0) if midpoint else np.nan
        rows.append(
            {
                "metric": metric,
                "sources": int(group["source"].nunique()),
                "low": low,
                "high": high,
                "midpoint": midpoint,
                "spread": spread,
                "relative_spread_pct": relative_spread,
            }
        )

    return pd.DataFrame(rows).sort_values(["metric"]).reset_index(drop=True)


def summarize_categorical_claims(frame: pd.DataFrame) -> pd.DataFrame:
    categorical = frame[frame["numeric_midpoint"].isna()].copy()
    if categorical.empty:
        return pd.DataFrame(columns=["category", "metrics", "claims"])

    rows = []
    for category, group in categorical.groupby("category", sort=True):
        rows.append(
            {
                "category": category,
                "metrics": ", ".join(sorted(group["metric"].unique())),
                "claims": int(len(group)),
            }
        )
    return pd.DataFrame(rows).sort_values(["category"]).reset_index(drop=True)


def format_metric_table(table: pd.DataFrame) -> str:
    if table.empty:
        return "No numeric claims parsed."

    display = table.copy()
    for column in ("low", "high", "midpoint", "spread", "relative_spread_pct"):
        display[column] = display[column].map(lambda value: f"{value:.2f}")
    return display.to_string(index=False)


def format_category_table(table: pd.DataFrame) -> str:
    if table.empty:
        return "No categorical claims parsed."
    return table.to_string(index=False)


def build_report(frame: pd.DataFrame) -> str:
    numeric_table = summarize_numeric_claims(frame)
    categorical_table = summarize_categorical_claims(frame)

    body_length = numeric_table.loc[numeric_table["metric"] == "body_length"]
    mass = numeric_table.loc[numeric_table["metric"] == "mass"]
    crest = numeric_table.loc[numeric_table["metric"] == "crest_height"]

    lines: list[str] = []
    lines.append("Mirabilis public-evidence analysis")
    lines.append("=" * 33)
    lines.append("")
    lines.append(f"Claims parsed: {len(frame)}")
    lines.append(f"Unique sources: {frame['source'].nunique()}")
    lines.append(f"Numeric claims: {frame['numeric_midpoint'].notna().sum()}")
    lines.append(f"Categorical claims: {frame['numeric_midpoint'].isna().sum()}")
    lines.append("")

    if not body_length.empty:
        row = body_length.iloc[0]
        lines.append(
            f"Public body-length range: {row['low']:.1f} to {row['high']:.1f} m "
            f"(midpoint {row['midpoint']:.1f} m, spread {row['relative_spread_pct']:.1f}%)"
        )
    if not mass.empty:
        row = mass.iloc[0]
        lines.append(
            f"Public mass range: {row['low']:.1f} to {row['high']:.1f} tonnes "
            f"(midpoint {row['midpoint']:.1f} t, spread {row['relative_spread_pct']:.1f}%)"
        )
    if not crest.empty:
        row = crest.iloc[0]
        lines.append(f"Crest-height estimate: about {row['midpoint']:.0f} cm")

    lines.append("")
    lines.append("Numeric summary")
    lines.append(format_metric_table(numeric_table))
    lines.append("")
    lines.append("Categorical summary")
    lines.append(format_category_table(categorical_table))
    lines.append("")
    lines.append("Interpretation")
    lines.append(
        "- Public reporting is converging on a very tall display crest (~50 cm) and a semiaquatic, fish-eating animal."
    )
    lines.append(
        "- Size reporting is still loose: publicly cited body-length estimates span 8 to 12 meters, which is a large relative spread."
    )
    lines.append(
        "- The lab's public workflow already includes CT scanning, 3D restoration, database curation, and PCA-style body-proportion analysis, which maps well to remote quantitative support."
    )
    lines.append(
        "- The most realistic remote contribution is cleaning and structuring measurement tables, not fieldwork."
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize public claims about Spinosaurus mirabilis and the UChicago Fossil Lab."
    )
    parser.add_argument(
        "--evidence-file",
        type=Path,
        default=DEFAULT_EVIDENCE_FILE,
        help="CSV file containing sourced evidence rows.",
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

    frame = load_evidence(args.evidence_file)
    report = build_report(frame)

    print(report)

    if args.output_markdown is not None:
        args.output_markdown.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

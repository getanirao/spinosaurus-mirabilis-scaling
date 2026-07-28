"""Summarize exported SimScale residual, force, and moment telemetry."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the final residuals and force/moment stability window."
    )
    parser.add_argument("run_dir", type=Path, help="SimScale run export directory")
    parser.add_argument(
        "--tail",
        type=int,
        default=200,
        help="Number of final force/moment samples used for stability statistics",
    )
    return parser.parse_args()


def read_numeric_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.columns = frame.columns.str.strip()
    return frame.apply(pd.to_numeric, errors="coerce")


def add_final_residuals(rows: list[dict[str, object]], frame: pd.DataFrame) -> None:
    final = frame.iloc[-1]
    for metric in frame.columns:
        if metric.lower().startswith("time") or not np.isfinite(final[metric]):
            continue
        rows.append(
            {
                "source": "residuals",
                "metric": metric,
                "statistic": "final",
                "value": float(final[metric]),
                "unit": "-",
                "sample_count": 1,
            }
        )


def add_window_statistics(
    rows: list[dict[str, object]],
    frame: pd.DataFrame,
    source: str,
    unit: str,
    tail: int,
) -> None:
    window = frame.tail(tail)
    for metric in frame.columns:
        if metric.lower().startswith("time"):
            continue
        values = window[metric].dropna()
        values = values[np.isfinite(values)]
        if values.empty:
            continue
        for statistic, value, count in (
            ("mean", values.mean(), len(values)),
            ("std", values.std(), len(values)),
            ("final", values.iloc[-1], 1),
        ):
            rows.append(
                {
                    "source": source,
                    "metric": metric,
                    "statistic": statistic,
                    "value": float(value),
                    "unit": unit,
                    "sample_count": count,
                }
            )


def main() -> None:
    args = parse_args()
    if args.tail < 2:
        raise ValueError("--tail must be at least 2")

    raw_dir = args.run_dir / "raw"
    residuals = read_numeric_csv(raw_dir / "residuals.csv")
    forces = read_numeric_csv(raw_dir / "forces.csv")
    moments = read_numeric_csv(raw_dir / "moments.csv")

    rows: list[dict[str, object]] = []
    add_final_residuals(rows, residuals)
    add_window_statistics(rows, forces, "forces", "N", args.tail)
    add_window_statistics(rows, moments, "moments", "N m", args.tail)

    output = args.run_dir / "summary.csv"
    pd.DataFrame(rows).to_csv(output, index=False)

    print(f"[telemetry] residual rows parsed: {len(residuals)}")
    print(f"[telemetry] force rows parsed: {len(forces)}")
    print(f"[telemetry] moment rows parsed: {len(moments)}")
    print(f"[telemetry] stability window: final {min(args.tail, len(forces))} samples")
    print(f"[telemetry] summary ready: {output}")


if __name__ == "__main__":
    main()

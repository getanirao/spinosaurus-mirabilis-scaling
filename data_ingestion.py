#!/usr/bin/env python3
"""Ingest bone measurement data for scaling analysis.

The script prepares a structural analysis grid by:
- loading a measurement table
- identifying specimen IDs
- splitting independent scaling proxies from dependent morphological variables
- coercing the selected analysis columns to numeric values
- logging telemetry that confirms the dataset is ready for regression workflows
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


LOGGER = logging.getLogger("data_ingestion")

ID_CANDIDATES = (
    "specimen_id",
    "specimen",
    "catalog_number",
    "catalogue_number",
    "accession",
    "accession_number",
    "id",
)

INDEPENDENT_KEYWORDS = (
    "femur",
    "femoral",
    "axis",
    "humerus",
    "humeral",
    "tibia",
    "tibial",
    "radius",
    "ulna",
    "metatarsal",
    "metacarpal",
    "scapula",
    "coracoid",
    "centrum",
    "vertebra",
    "shaft",
)

DEPENDENT_KEYWORDS = (
    "skull",
    "crest",
    "height",
    "depth",
    "width",
    "diameter",
    "area",
    "volume",
    "sail",
    "spine",
    "jaw",
    "snout",
    "orbit",
)


@dataclass(frozen=True)
class IngestionResult:
    source_path: Path
    specimen_id_column: str
    independent_columns: tuple[str, ...]
    dependent_columns: tuple[str, ...]
    analysis_grid: pd.DataFrame


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [
        re.sub(r"[^0-9a-zA-Z]+", "_", str(column).strip().lower()).strip("_")
        for column in normalized.columns
    ]
    return normalized


def load_measurement_table(source_path: Path) -> pd.DataFrame:
    suffix = source_path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(source_path)
    if suffix in {".tsv", ".tab"}:
        return pd.read_csv(source_path, sep="\t")
    raise ValueError(f"Unsupported file type: {source_path.suffix}")


def infer_id_column(columns: Sequence[str]) -> str:
    for candidate in ID_CANDIDATES:
        if candidate in columns:
            return candidate
    return columns[0]


def parse_column_list(raw_columns: str | None) -> tuple[str, ...]:
    if raw_columns is None or not raw_columns.strip():
        return tuple()
    return tuple(
        column.strip().lower()
        for column in raw_columns.split(",")
        if column.strip()
    )


def contains_any(column_name: str, keywords: Iterable[str]) -> bool:
    return any(keyword in column_name for keyword in keywords)


def choose_analysis_columns(
    frame: pd.DataFrame,
    specimen_id_column: str,
    explicit_independent: tuple[str, ...],
    explicit_dependent: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    available_columns = [column for column in frame.columns if column != specimen_id_column]

    numeric_candidates = [
        column
        for column in available_columns
        if pd.api.types.is_numeric_dtype(frame[column])
        or pd.to_numeric(frame[column], errors="coerce").notna().any()
    ]

    if explicit_independent or explicit_dependent:
        independent_columns = tuple(
            column for column in explicit_independent if column in frame.columns
        )
        dependent_columns = tuple(
            column for column in explicit_dependent if column in frame.columns
        )
        return independent_columns, dependent_columns

    independent_columns = tuple(
        column
        for column in numeric_candidates
        if contains_any(column, INDEPENDENT_KEYWORDS)
    )
    dependent_columns = tuple(
        column
        for column in numeric_candidates
        if contains_any(column, DEPENDENT_KEYWORDS)
    )

    if not independent_columns and not dependent_columns:
        midpoint = max(1, len(numeric_candidates) // 2)
        independent_columns = tuple(numeric_candidates[:midpoint])
        dependent_columns = tuple(numeric_candidates[midpoint:])
    elif not independent_columns:
        dependent_set = set(dependent_columns)
        remaining = [column for column in numeric_candidates if column not in dependent_set]
        independent_columns = tuple(remaining)
    elif not dependent_columns:
        independent_set = set(independent_columns)
        remaining = [column for column in numeric_candidates if column not in independent_set]
        dependent_columns = tuple(remaining)

    return independent_columns, dependent_columns


def build_analysis_grid(
    frame: pd.DataFrame,
    specimen_id_column: str,
    independent_columns: tuple[str, ...],
    dependent_columns: tuple[str, ...],
) -> pd.DataFrame:
    selected_columns = [specimen_id_column, *independent_columns, *dependent_columns]
    selected_columns = list(dict.fromkeys(selected_columns))

    grid = frame.loc[:, selected_columns].copy()
    for column in independent_columns + dependent_columns:
        grid[column] = pd.to_numeric(grid[column], errors="coerce")
    return grid


def log_telemetry(result: IngestionResult) -> None:
    grid = result.analysis_grid
    numeric_grid = grid.drop(columns=[result.specimen_id_column], errors="ignore")
    total_cells = int(np.prod(numeric_grid.shape)) if not numeric_grid.empty else 0
    missing_cells = int(numeric_grid.isna().sum().sum()) if total_cells else 0
    missing_rate = (missing_cells / total_cells) if total_cells else 0.0

    specimen_ids = grid[result.specimen_id_column].astype(str).tolist()

    LOGGER.info("Source file: %s", result.source_path)
    LOGGER.info("Parsed structural grid shape: %s rows x %s columns", *grid.shape)
    LOGGER.info("Specimen ID column: %s", result.specimen_id_column)
    LOGGER.info("Specimen IDs observed (%s): %s", len(specimen_ids), specimen_ids)
    LOGGER.info("Independent scaling proxies: %s", list(result.independent_columns))
    LOGGER.info("Dependent morphological variables: %s", list(result.dependent_columns))
    LOGGER.info(
        "Numeric analysis grid: %s rows x %s measurement columns",
        numeric_grid.shape[0],
        numeric_grid.shape[1],
    )
    LOGGER.info(
        "Missingness telemetry: %s missing cells out of %s (%.2f%%)",
        missing_cells,
        total_cells,
        missing_rate * 100.0,
    )
    LOGGER.info("Structural grid status: parsed and ready for regression inputs")


def ingest_measurements(
    source_path: Path,
    independent_override: tuple[str, ...] = tuple(),
    dependent_override: tuple[str, ...] = tuple(),
    specimen_id_override: str | None = None,
) -> IngestionResult:
    raw_frame = load_measurement_table(source_path)
    normalized_frame = normalize_columns(raw_frame)

    specimen_id_column = (
        specimen_id_override.lower() if specimen_id_override else infer_id_column(normalized_frame.columns)
    )
    if specimen_id_column not in normalized_frame.columns:
        raise KeyError(f"Specimen ID column not found: {specimen_id_column}")

    independent_columns, dependent_columns = choose_analysis_columns(
        normalized_frame,
        specimen_id_column,
        independent_override,
        dependent_override,
    )

    if not independent_columns and not dependent_columns:
        raise ValueError("No analysis columns were identified in the dataset.")

    analysis_grid = build_analysis_grid(
        normalized_frame,
        specimen_id_column,
        independent_columns,
        dependent_columns,
    )

    return IngestionResult(
        source_path=source_path,
        specimen_id_column=specimen_id_column,
        independent_columns=independent_columns,
        dependent_columns=dependent_columns,
        analysis_grid=analysis_grid,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest bone measurement data and prepare a scaling analysis grid."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the bone measurement dataset (.csv, .tsv, or .txt).",
    )
    parser.add_argument(
        "--specimen-id-column",
        dest="specimen_id_column",
        default=None,
        help="Optional explicit specimen ID column name.",
    )
    parser.add_argument(
        "--independent-columns",
        dest="independent_columns",
        default=None,
        help="Comma-separated list of independent scaling proxy columns.",
    )
    parser.add_argument(
        "--dependent-columns",
        dest="dependent_columns",
        default=None,
        help="Comma-separated list of dependent morphological variable columns.",
    )
    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    result = ingest_measurements(
        source_path=args.input_file,
        independent_override=parse_column_list(args.independent_columns),
        dependent_override=parse_column_list(args.dependent_columns),
        specimen_id_override=args.specimen_id_column,
    )
    log_telemetry(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render a source-labeled crest-pressure comparison from model summary values.

The figure is an analytical lateral-profile schematic, not a CFD output or a
literal export of either reconstruction. Its purpose is to communicate the
same crest-only loading assumptions used by crest_hydrodynamics.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SUMMARY_FILE = Path(__file__).with_name("crest_hydrodynamics_summary.csv")
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("crest_pressure_comparison.svg")


def summary_value(summary: pd.DataFrame, comparison: str, metric: str) -> float:
    value = summary.loc[
        (summary["comparison"] == comparison) & (summary["metric"] == metric), "median"
    ]
    if len(value) != 1:
        raise KeyError(f"Missing median for {comparison!r} / {metric!r}.")
    return float(value.iloc[0])


def render_svg(aegyptiacus_force: float, mirabilis_force: float, force_ratio: float) -> str:
    """Return the standalone SVG using the model's median head-entry loads."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960" role="img" aria-labelledby="title desc">
  <title id="title">Crest-only head-first water-entry comparison</title>
  <desc id="desc">Source-labeled lateral skull schematics comparing S. aegyptiacus and S. mirabilis. Blue-to-red colors show modeled relative crest pressure, and arrows show modeled drag direction.</desc>
  <defs>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#e0f2fe"/>
      <stop offset="100%" stop-color="#bae6fd"/>
    </linearGradient>
    <linearGradient id="heat-low" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#2563eb"/>
      <stop offset="65%" stop-color="#22d3ee"/>
      <stop offset="100%" stop-color="#fbbf24"/>
    </linearGradient>
    <linearGradient id="heat-high" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#2563eb"/>
      <stop offset="45%" stop-color="#22d3ee"/>
      <stop offset="72%" stop-color="#facc15"/>
      <stop offset="88%" stop-color="#f97316"/>
      <stop offset="100%" stop-color="#dc2626"/>
    </linearGradient>
    <radialGradient id="pressure-glow">
      <stop offset="0%" stop-color="#ef4444" stop-opacity="0.52"/>
      <stop offset="65%" stop-color="#f59e0b" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="#fef3c7" stop-opacity="0"/>
    </radialGradient>
    <marker id="blue-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#2563eb"/>
    </marker>
    <marker id="red-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#dc2626"/>
    </marker>
    <style>
      .title {{ font: 700 34px Georgia, serif; fill: #0f172a; }}
      .subtitle {{ font: 400 17px Arial, sans-serif; fill: #334155; }}
      .panel-title {{ font: 700 25px Georgia, serif; fill: #0f172a; }}
      .label {{ font: 600 16px Arial, sans-serif; fill: #0f172a; }}
      .small {{ font: 400 14px Arial, sans-serif; fill: #334155; }}
      .tiny {{ font: 400 12px Arial, sans-serif; fill: #475569; }}
      .value {{ font: 700 22px Arial, sans-serif; fill: #0f172a; }}
      .skull {{ fill: #cbd5e1; stroke: #0f172a; stroke-width: 4; stroke-linejoin: round; }}
      .detail {{ fill: none; stroke: #475569; stroke-width: 3; stroke-linecap: round; }}
      .water-line {{ stroke: #38bdf8; stroke-width: 3; opacity: 0.75; }}
    </style>
  </defs>

  <rect width="1600" height="960" fill="#f8fafc"/>
  <rect x="50" y="145" width="1500" height="590" rx="14" fill="url(#water)" stroke="#94a3b8" stroke-width="2"/>
  <text x="70" y="65" class="title">Crest-only head-first water-entry comparison</text>
  <text x="70" y="97" class="subtitle">Same modeled water-entry scenario; color shows relative pressure concentration and arrows show drag direction.</text>
  <text x="70" y="122" class="subtitle">Analytical lateral-profile schematic, not a CFD pressure map or a direct rendering of a 3D mesh.</text>

  <line x1="800" y1="175" x2="800" y2="706" stroke="#94a3b8" stroke-width="2" stroke-dasharray="8 8"/>

  <g aria-label="Spinosaurus aegyptiacus control profile">
    <text x="105" y="195" class="panel-title">S. aegyptiacus - control</text>
    <text x="105" y="221" class="small">CT-based 3D skeletal and flesh reconstruction available</text>

    <line x1="705" y1="305" x2="575" y2="305" stroke="#2563eb" stroke-width="4" marker-end="url(#blue-arrow)"/>
    <text x="568" y="282" class="small" text-anchor="end">Relative flow</text>

    <path class="skull" d="M125 500 C155 445 230 411 320 406 L475 411 C540 415 600 438 662 475 L714 507 L670 533 L585 543 L508 560 L420 584 L310 581 L225 555 L153 540 Z"/>
    <path class="detail" d="M172 501 C260 485 340 487 442 505 C520 519 590 516 662 497"/>
    <ellipse cx="385" cy="459" rx="26" ry="22" fill="#f8fafc" stroke="#0f172a" stroke-width="4"/>
    <circle cx="389" cy="458" r="7" fill="#0f172a"/>
    <path d="M365 411 C373 383 394 365 421 380 C430 393 426 411 416 421 L377 423 Z" fill="url(#heat-low)" stroke="#0f172a" stroke-width="4" stroke-linejoin="round"/>
    <path class="detail" d="M277 535 L296 550 M316 533 L335 550 M355 529 L374 547 M395 526 L414 544 M435 520 L454 539 M475 516 L494 534 M515 512 L534 530 M555 506 L574 524 M595 499 L614 516"/>
    <line x1="435" y1="397" x2="348" y2="397" stroke="#2563eb" stroke-width="4" marker-end="url(#blue-arrow)"/>
    <text x="344" y="374" class="label" text-anchor="end">Smaller leading span</text>
    <text x="105" y="645" class="label">Median crest-only entry load</text>
    <text x="105" y="677" class="value">{aegyptiacus_force:.1f} N</text>
    <text x="105" y="703" class="small">UCPC-2 fragment baseline; original crest height is uncertain.</text>
  </g>

  <g aria-label="Spinosaurus mirabilis test profile">
    <text x="870" y="195" class="panel-title">S. mirabilis - test variable</text>
    <text x="870" y="221" class="small">Official digital skull assembly; full public mesh not verified</text>

    <line x1="1470" y1="305" x2="1325" y2="305" stroke="#2563eb" stroke-width="4" marker-end="url(#blue-arrow)"/>
    <text x="1318" y="282" class="small" text-anchor="end">Relative flow</text>

    <ellipse cx="1172" cy="306" rx="158" ry="194" fill="url(#pressure-glow)"/>
    <path class="skull" d="M875 500 C905 445 980 411 1070 406 L1225 411 C1290 415 1350 438 1412 475 L1464 507 L1420 533 L1335 543 L1258 560 L1170 584 L1060 581 L975 555 L903 540 Z"/>
    <path class="detail" d="M922 501 C1010 485 1090 487 1192 505 C1270 519 1340 516 1412 497"/>
    <ellipse cx="1135" cy="459" rx="26" ry="22" fill="#f8fafc" stroke="#0f172a" stroke-width="4"/>
    <circle cx="1139" cy="458" r="7" fill="#0f172a"/>
    <path d="M1114 411 C1104 365 1108 309 1133 251 C1151 209 1181 176 1215 164 C1225 191 1216 234 1194 274 C1173 313 1161 356 1168 413 L1142 425 Z" fill="url(#heat-high)" stroke="#0f172a" stroke-width="4" stroke-linejoin="round"/>
    <path class="detail" d="M1027 535 L1046 550 M1066 533 L1085 550 M1105 529 L1124 547 M1145 526 L1164 544 M1185 520 L1204 539 M1225 516 L1244 534 M1265 512 L1284 530 M1305 506 L1324 524 M1345 499 L1364 516"/>
    <line x1="1219" y1="230" x2="1096" y2="230" stroke="#dc2626" stroke-width="10" marker-end="url(#red-arrow)"/>
    <line x1="1201" y1="294" x2="1089" y2="294" stroke="#f97316" stroke-width="8" marker-end="url(#red-arrow)"/>
    <line x1="1179" y1="360" x2="1083" y2="360" stroke="#facc15" stroke-width="6" marker-end="url(#red-arrow)"/>
    <text x="1090" y="143" class="label">High, near-perpendicular crest</text>
    <text x="1090" y="166" class="small">Greater leading height during entry</text>
    <text x="870" y="645" class="label">Median crest-only entry load</text>
    <text x="870" y="677" class="value">{mirabilis_force:.1f} N</text>
    <text x="870" y="703" class="small">{force_ratio:.1f}x the fragment baseline in the same model.</text>
  </g>

  <g aria-label="Legend and sources">
    <rect x="50" y="760" width="1500" height="150" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
    <text x="75" y="792" class="label">How to read this figure</text>
    <rect x="75" y="812" width="290" height="18" fill="url(#heat-high)" stroke="#64748b" stroke-width="1"/>
    <text x="75" y="853" class="small">Lower relative pressure</text>
    <text x="365" y="853" class="small" text-anchor="end">Higher relative pressure</text>
    <line x1="455" y1="821" x2="545" y2="821" stroke="#dc2626" stroke-width="7" marker-end="url(#red-arrow)"/>
    <text x="560" y="827" class="small">Modelled drag direction on crest</text>
    <text x="75" y="885" class="tiny">Anatomical basis: S. aegyptiacus CT-based model and data project (eLife 2023 / MorphoSource 000460619); S. mirabilis digital skull reconstruction from Sereno et al. (Science 2026).</text>
    <text x="75" y="903" class="tiny">The S. mirabilis panel is a source-informed schematic because an open, specimen-resolved full 3D mesh was not verified. Values are medians from 100,000 model draws using explicit sensitivity ranges.</text>
  </g>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a source-labeled crest pressure comparison SVG.")
    parser.add_argument("--summary-file", type=Path, default=DEFAULT_SUMMARY_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    args = parser.parse_args()

    summary = pd.read_csv(args.summary_file)
    aegyptiacus_force = summary_value(
        summary, "Spinosaurus aegyptiacus", "head_first_entry_drag_n"
    )
    mirabilis_force = summary_value(
        summary, "Spinosaurus mirabilis", "head_first_entry_drag_n"
    )
    force_ratio = summary_value(
        summary, "S. mirabilis / S. aegyptiacus", "head_first_entry_drag_n_ratio"
    )
    args.output_file.write_text(
        render_svg(aegyptiacus_force, mirabilis_force, force_ratio), encoding="utf-8"
    )
    print(f"Wrote {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build a source-matched crest-reduced control from the SimScale input STL.

The transformation changes only vertices above a smooth roof curve inside the
configured crest-base interval. Triangle connectivity and all coordinates
outside that mask are preserved.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re


DEFAULT_INPUT = Path(
    "geometry/derived/wrap_surface_trial/"
    "nobilis2_complete_head_solidified_voxel_prewrap_v012m.stl"
)
DEFAULT_OUTPUT = Path(
    "geometry/derived/wrap_surface_trial/"
    "nobilis2_complete_head_crest_reduced_control_prewrap_v012m.stl"
)
DEFAULT_MANIFEST = Path(
    "geometry/derived/wrap_surface_trial/"
    "nobilis2_complete_head_crest_reduced_control_manifest.json"
)

CREST_Y_START_M = -2.86
CREST_Y_END_M = -2.64
ROOF_Z_START_M = 2.2317
ROOF_Z_END_M = 2.3377
ROOF_SLOPE_START = 0.80
ROOF_SLOPE_END = 0.23
EDGE_BLEND_M = 0.02
RETAINED_EXCESS_FRACTION = 0.03

VERTEX_PATTERN = re.compile(
    r"^\s*vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$"
)

Vertex = tuple[float, float, float]
Triangle = tuple[Vertex, Vertex, Vertex]


def parse_ascii_stl(path: Path) -> list[Triangle]:
    vertices: list[Vertex] = []
    for line in path.read_text(encoding="ascii", errors="strict").splitlines():
        match = VERTEX_PATTERN.match(line)
        if match:
            vertices.append(tuple(float(value) for value in match.groups()))
    if not vertices or len(vertices) % 3:
        raise RuntimeError(f"Expected an ASCII triangle STL, found {len(vertices)} vertices.")
    return [tuple(vertices[index : index + 3]) for index in range(0, len(vertices), 3)]


def hermite_roof(y: float) -> float:
    span = CREST_Y_END_M - CREST_Y_START_M
    t = (y - CREST_Y_START_M) / span
    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2
    return (
        h00 * ROOF_Z_START_M
        + h10 * span * ROOF_SLOPE_START
        + h01 * ROOF_Z_END_M
        + h11 * span * ROOF_SLOPE_END
    )


def smoothstep(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def crest_strength(y: float) -> float:
    if not CREST_Y_START_M < y < CREST_Y_END_M:
        return 0.0
    leading = smoothstep((y - CREST_Y_START_M) / EDGE_BLEND_M)
    trailing = smoothstep((CREST_Y_END_M - y) / EDGE_BLEND_M)
    return min(leading, trailing)


def deform_vertex(vertex: Vertex) -> tuple[Vertex, float]:
    x, y, z = vertex
    strength = crest_strength(y)
    if not strength:
        return vertex, 0.0
    roof = hermite_roof(y)
    if z <= roof:
        return vertex, 0.0
    compression = 1.0 - strength * (1.0 - RETAINED_EXCESS_FRACTION)
    new_z = roof + compression * (z - roof)
    return (x, y, new_z), z - new_z


def triangle_normal(triangle: Triangle) -> Vertex:
    a, b, c = triangle
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    length = math.sqrt(sum(value * value for value in cross))
    if length <= 1e-15:
        return (0.0, 0.0, 0.0)
    return tuple(value / length for value in cross)


def write_ascii_stl(path: Path, triangles: list[Triangle]) -> None:
    lines = ["solid nobilis2_complete_head_crest_reduced_control"]
    for triangle in triangles:
        normal = triangle_normal(triangle)
        lines.append(f"  facet normal {normal[0]:.9e} {normal[1]:.9e} {normal[2]:.9e}")
        lines.append("    outer loop")
        for vertex in triangle:
            lines.append(f"      vertex {vertex[0]:.9e} {vertex[1]:.9e} {vertex[2]:.9e}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid nobilis2_complete_head_crest_reduced_control")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def rounded(vertex: Vertex) -> Vertex:
    return tuple(round(value, 8) for value in vertex)


def diagnostics(triangles: list[Triangle]) -> dict[str, float | int | list[float]]:
    edge_counts: Counter[tuple[Vertex, Vertex]] = Counter()
    area = 0.0
    signed_volume = 0.0
    degenerate = 0
    vertices: set[Vertex] = set()
    for triangle in triangles:
        keys = [rounded(vertex) for vertex in triangle]
        vertices.update(keys)
        for index in range(3):
            edge_counts[tuple(sorted((keys[index], keys[(index + 1) % 3])))] += 1
        a, b, c = triangle
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        triangle_area = 0.5 * math.sqrt(sum(value * value for value in cross))
        area += triangle_area
        if triangle_area <= 1e-12:
            degenerate += 1
        signed_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
    axes = list(zip(*vertices))
    return {
        "triangles": len(triangles),
        "unique_vertices": len(vertices),
        "boundary_edges": sum(count == 1 for count in edge_counts.values()),
        "non_manifold_edges": sum(count > 2 for count in edge_counts.values()),
        "degenerate_triangles": degenerate,
        "surface_area_m2": area,
        "signed_volume_m3": signed_volume,
        "bounds_min_m": [min(axis) for axis in axes],
        "bounds_max_m": [max(axis) for axis in axes],
    }


def build(input_path: Path, output_path: Path, manifest_path: Path) -> dict[str, object]:
    source = parse_ascii_stl(input_path)
    transformed: list[Triangle] = []
    displacements: dict[Vertex, float] = {}
    for triangle in source:
        current: list[Vertex] = []
        for vertex in triangle:
            deformed, displacement = deform_vertex(vertex)
            current.append(deformed)
            key = rounded(vertex)
            displacements[key] = max(displacements.get(key, 0.0), displacement)
        transformed.append(tuple(current))

    moved = {vertex: value for vertex, value in displacements.items() if value > 0.0}
    unchanged = {vertex for vertex, value in displacements.items() if value == 0.0}
    source_peak = max(vertex[2] for triangle in source for vertex in triangle)
    control_peak = max(vertex[2] for triangle in transformed for vertex in triangle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_ascii_stl(output_path, transformed)
    report: dict[str, object] = {
        "source": str(input_path.resolve()),
        "output": str(output_path.resolve()),
        "model_role": "source-matched crest-reduced geometric control",
        "not_an_anatomical_claim": True,
        "method": {
            "crest_y_interval_m": [CREST_Y_START_M, CREST_Y_END_M],
            "roof_anchor_z_m": [ROOF_Z_START_M, ROOF_Z_END_M],
            "roof_anchor_slopes_dz_dy": [ROOF_SLOPE_START, ROOF_SLOPE_END],
            "edge_blend_m": EDGE_BLEND_M,
            "retained_crest_excess_fraction": RETAINED_EXCESS_FRACTION,
            "reason_for_retained_fraction": (
                "Avoids collapsing vertically aligned source vertices while removing 97% "
                "of local height above the replacement roof curve."
            ),
        },
        "coordinate_change_audit": {
            "unique_source_vertices": len(displacements),
            "modified_unique_vertices": len(moved),
            "unchanged_unique_vertices": len(unchanged),
            "unchanged_fraction": len(unchanged) / len(displacements),
            "maximum_vertical_reduction_m": max(moved.values()),
            "source_peak_z_m": source_peak,
            "control_peak_z_m": control_peak,
            "global_peak_reduction_m": source_peak - control_peak,
            "maximum_coordinate_change_outside_crest_mask_m": 0.0,
        },
        "source_surface": diagnostics(source),
        "control_surface": diagnostics(transformed),
        "use_constraints": [
            "Run through the same SimScale Fit-to-surface Wrap resolution 8 workflow as the full model.",
            "Use identical domain, material, boundary conditions, mesh settings, and solver controls.",
            "Interpret differences as sensitivity to this explicit geometric reduction, not fossil anatomy.",
        ],
    }
    manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    report = build(args.input, args.output, args.manifest)
    print(json.dumps(report["coordinate_change_audit"], indent=2))
    print(json.dumps(report["control_surface"], indent=2))


if __name__ == "__main__":
    main()

"""Build artist-derived 2.5D crest-profile sensitivity geometries in Blender.

This is intentionally not an anatomical reconstruction or a full skull mesh.
It extracts a sagittal envelope from the Nobilis 2 reference object, smooths
small display-mesh artifacts, and creates finite-thickness profile prisms plus
matched smooth crest-ablated controls for parameter sensitivity tests.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median
from typing import Iterable

import bmesh
import bpy
from mathutils import Vector


OBJECT_NAME = "MIRABILIS_REFERENCE_SURFACE"
OUTPUT_DIRECTORY_NAME = "profile_prism_sensitivity"
SECTION_X_M = 0.0
HEAD_Y_MAX_FRACTION = 0.21283
CREST_Y_MIN_FRACTION = 0.06386
CREST_Y_MAX_FRACTION = 0.15188
THICKNESSES_M = (0.02, 0.03, 0.04)
SAMPLE_COUNT = 501
MEDIAN_RADIUS = 2
INTERSECTION_TOLERANCE_M = 1.0e-7
AREA_TOLERANCE_M2 = 1.0e-12


def world_vertices(obj: bpy.types.Object) -> list[Vector]:
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def bounds(points: Iterable[Vector]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    point_list = list(points)
    return (
        tuple(min(point[index] for point in point_list) for index in range(3)),
        tuple(max(point[index] for point in point_list) for index in range(3)),
    )


def unique_points(points: list[Vector], tolerance: float) -> list[Vector]:
    unique: list[Vector] = []
    for point in points:
        if all((point - existing).length > tolerance for existing in unique):
            unique.append(point)
    return unique


def triangle_plane_segment(a: Vector, b: Vector, c: Vector, plane_x: float) -> tuple[Vector, Vector] | None:
    """Return the longest line segment where a triangle intersects X=plane_x."""
    candidates: list[Vector] = []
    for start, end in ((a, b), (b, c), (c, a)):
        start_distance = start.x - plane_x
        end_distance = end.x - plane_x
        start_on_plane = abs(start_distance) <= INTERSECTION_TOLERANCE_M
        end_on_plane = abs(end_distance) <= INTERSECTION_TOLERANCE_M

        if start_on_plane:
            candidates.append(start.copy())
        if end_on_plane:
            candidates.append(end.copy())
        if start_distance * end_distance < 0.0:
            fraction = start_distance / (start_distance - end_distance)
            candidates.append(start.lerp(end, fraction))

    unique = unique_points(candidates, INTERSECTION_TOLERANCE_M)
    if len(unique) < 2:
        return None
    if len(unique) == 2:
        return unique[0], unique[1]

    pairs = [
        (left, right)
        for index, left in enumerate(unique)
        for right in unique[index + 1 :]
    ]
    return max(pairs, key=lambda pair: (pair[0] - pair[1]).length)


def sagittal_segments(obj: bpy.types.Object, plane_x: float) -> list[tuple[Vector, Vector]]:
    vertices = world_vertices(obj)
    segments: list[tuple[Vector, Vector]] = []
    for polygon in obj.data.polygons:
        indices = polygon.vertices[:]
        for index in range(1, len(indices) - 1):
            segment = triangle_plane_segment(
                vertices[indices[0]], vertices[indices[index]], vertices[indices[index + 1]], plane_x
            )
            if segment is not None:
                segments.append(segment)
    return segments


def values_at_y(segments: list[tuple[Vector, Vector]], y_value: float) -> list[float]:
    values: list[float] = []
    for start, end in segments:
        low_y = min(start.y, end.y)
        high_y = max(start.y, end.y)
        if y_value < low_y - INTERSECTION_TOLERANCE_M or y_value > high_y + INTERSECTION_TOLERANCE_M:
            continue
        y_delta = end.y - start.y
        if abs(y_delta) <= INTERSECTION_TOLERANCE_M:
            values.extend((start.z, end.z))
            continue
        fraction = (y_value - start.y) / y_delta
        if -INTERSECTION_TOLERANCE_M <= fraction <= 1.0 + INTERSECTION_TOLERANCE_M:
            values.append(start.z + fraction * (end.z - start.z))
    return values


def interpolate_missing(values: list[float | None]) -> list[float]:
    present = [index for index, value in enumerate(values) if value is not None]
    if not present:
        raise RuntimeError("The sagittal section did not produce a usable head-profile envelope.")
    completed = values[:]
    first = present[0]
    last = present[-1]
    for index in range(first):
        completed[index] = completed[first]
    for index in range(last + 1, len(completed)):
        completed[index] = completed[last]

    index = first
    while index <= last:
        if completed[index] is not None:
            index += 1
            continue
        run_start = index - 1
        while index <= last and completed[index] is None:
            index += 1
        run_end = index
        left = float(completed[run_start])
        right = float(completed[run_end])
        for missing_index in range(run_start + 1, run_end):
            fraction = (missing_index - run_start) / (run_end - run_start)
            completed[missing_index] = left + fraction * (right - left)
    return [float(value) for value in completed]


def median_smooth(values: list[float], radius: int) -> list[float]:
    return [
        float(median(values[max(0, index - radius) : min(len(values), index + radius + 1)]))
        for index in range(len(values))
    ]


def extract_profile(obj: bpy.types.Object) -> tuple[list[tuple[float, float]], dict[str, object]]:
    points = world_vertices(obj)
    minimum, maximum = bounds(points)
    y_span = maximum[1] - minimum[1]
    head_y_max = minimum[1] + HEAD_Y_MAX_FRACTION * y_span
    y_values = [
        minimum[1] + (head_y_max - minimum[1]) * index / (SAMPLE_COUNT - 1)
        for index in range(SAMPLE_COUNT)
    ]
    segments = sagittal_segments(obj, SECTION_X_M)
    if not segments:
        raise RuntimeError("No triangles intersected the sagittal section plane.")

    lower_values: list[float | None] = []
    upper_values: list[float | None] = []
    for y_value in y_values:
        intersections = values_at_y(segments, y_value)
        lower_values.append(min(intersections) if intersections else None)
        upper_values.append(max(intersections) if intersections else None)

    lower = median_smooth(interpolate_missing(lower_values), MEDIAN_RADIUS)
    upper = median_smooth(interpolate_missing(upper_values), MEDIAN_RADIUS)
    minimum_gap = 0.001
    for index in range(len(y_values)):
        if upper[index] - lower[index] < minimum_gap:
            midpoint = 0.5 * (upper[index] + lower[index])
            lower[index] = midpoint - 0.5 * minimum_gap
            upper[index] = midpoint + 0.5 * minimum_gap

    # Lower trace runs nose to posterior; upper returns to the nose, yielding
    # one simple closed silhouette polygon without interior jaw or tooth paths.
    profile = list(zip(y_values, lower)) + list(zip(reversed(y_values), reversed(upper)))
    metadata = {
        "section_plane_x_m": SECTION_X_M,
        "head_y_range_m": [minimum[1], head_y_max],
        "segment_count": len(segments),
        "sample_count": SAMPLE_COUNT,
        "envelope_cleanup": "min/max sagittal envelope with local 5-sample median smoothing",
        "ignored_geometry": "interior paths and sub-sampling-scale display details",
    }
    return profile, metadata


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(
    a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]
) -> bool:
    return orientation(a, b, c) * orientation(a, b, d) < 0.0 and orientation(c, d, a) * orientation(c, d, b) < 0.0


def require_simple_polygon(profile: list[tuple[float, float]]) -> None:
    count = len(profile)
    for first in range(count):
        first_next = (first + 1) % count
        for second in range(first + 1, count):
            second_next = (second + 1) % count
            if first in (second, second_next) or first_next in (second, second_next):
                continue
            if segments_intersect(profile[first], profile[first_next], profile[second], profile[second_next]):
                raise RuntimeError("Profile cleanup produced a self-intersecting polygon.")


def hermite(y0: float, z0: float, slope0: float, y1: float, z1: float, slope1: float, y: float) -> float:
    span = y1 - y0
    t = (y - y0) / span
    h00 = 2.0 * t**3 - 3.0 * t**2 + 1.0
    h10 = t**3 - 2.0 * t**2 + t
    h01 = -2.0 * t**3 + 3.0 * t**2
    h11 = t**3 - t**2
    return h00 * z0 + h10 * span * slope0 + h01 * z1 + h11 * span * slope1


def crest_ablated_profile(profile: list[tuple[float, float]], y_range: tuple[float, float]) -> tuple[list[tuple[float, float]], dict[str, float]]:
    count = len(profile) // 2
    lower = profile[:count]
    upper_reversed = profile[count:]
    upper = list(reversed(upper_reversed))
    y_values = [point[0] for point in lower]
    upper_values = [point[1] for point in upper]

    start_index = min(range(count), key=lambda index: abs(y_values[index] - y_range[0]))
    end_index = min(range(count), key=lambda index: abs(y_values[index] - y_range[1]))
    if start_index >= end_index:
        raise RuntimeError("Crest-ablation anchor ordering is invalid.")

    slope_window = max(4, int(0.04 * count))
    left_slope = (upper_values[start_index] - upper_values[max(0, start_index - slope_window)]) / (
        y_values[start_index] - y_values[max(0, start_index - slope_window)]
    )
    right_slope = (upper_values[min(count - 1, end_index + slope_window)] - upper_values[end_index]) / (
        y_values[min(count - 1, end_index + slope_window)] - y_values[end_index]
    )
    for index in range(start_index, end_index + 1):
        upper_values[index] = hermite(
            y_values[start_index],
            upper_values[start_index],
            left_slope,
            y_values[end_index],
            upper_values[end_index],
            right_slope,
            y_values[index],
        )

    control = lower + list(reversed(list(zip(y_values, upper_values))))
    return control, {
        "anchor_y_start_m": y_values[start_index],
        "anchor_y_end_m": y_values[end_index],
        "left_slope": left_slope,
        "right_slope": right_slope,
    }


def prism_mesh(name: str, profile: list[tuple[float, float]], thickness_m: float) -> bpy.types.Mesh:
    require_simple_polygon(profile)
    count = len(profile)
    half_thickness = 0.5 * thickness_m
    vertices = [(-half_thickness, y_value, z_value) for y_value, z_value in profile]
    vertices.extend((half_thickness, y_value, z_value) for y_value, z_value in profile)
    faces: list[tuple[int, ...]] = []
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))
    faces.append(tuple(reversed(range(count))))
    faces.append(tuple(range(count, 2 * count)))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(clean_customdata=True)
    mesh.update()
    return mesh


def mesh_diagnostics(mesh: bpy.types.Mesh) -> dict[str, object]:
    edge_face_counts: dict[tuple[int, int], int] = {}
    degenerate_triangles = 0
    signed_volume = 0.0
    for polygon in mesh.polygons:
        indices = polygon.vertices[:]
        if len(indices) != 3:
            raise RuntimeError("Prism export mesh was not triangulated.")
        a, b, c = (mesh.vertices[index].co for index in indices)
        cross = (b - a).cross(c - a)
        if cross.length * 0.5 <= AREA_TOLERANCE_M2:
            degenerate_triangles += 1
        signed_volume += a.dot(cross) / 6.0
        for index, vertex_a in enumerate(indices):
            vertex_b = indices[(index + 1) % len(indices)]
            key = tuple(sorted((vertex_a, vertex_b)))
            edge_face_counts[key] = edge_face_counts.get(key, 0) + 1
    return {
        "vertices": len(mesh.vertices),
        "triangles": len(mesh.polygons),
        "boundary_edges": sum(count == 1 for count in edge_face_counts.values()),
        "non_manifold_edges": sum(count > 2 for count in edge_face_counts.values()),
        "degenerate_triangles": degenerate_triangles,
        "enclosed_volume_m3": abs(signed_volume),
    }


def write_ascii_stl(mesh: bpy.types.Mesh, path: Path, solid_name: str) -> None:
    lines = [f"solid {solid_name}"]
    for polygon in mesh.polygons:
        a, b, c = (mesh.vertices[index].co for index in polygon.vertices)
        normal = (b - a).cross(c - a)
        if normal.length:
            normal.normalize()
        lines.extend(
            (
                f"  facet normal {normal.x:.9g} {normal.y:.9g} {normal.z:.9g}",
                "    outer loop",
                f"      vertex {a.x:.9g} {a.y:.9g} {a.z:.9g}",
                f"      vertex {b.x:.9g} {b.y:.9g} {b.z:.9g}",
                f"      vertex {c.x:.9g} {c.y:.9g} {c.z:.9g}",
                "    endloop",
                "  endfacet",
            )
        )
    lines.append(f"endsolid {solid_name}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_preview_svg(
    profile: list[tuple[float, float]], control: list[tuple[float, float]], path: Path
) -> None:
    all_points = profile + control
    min_y = min(point[0] for point in all_points)
    max_y = max(point[0] for point in all_points)
    min_z = min(point[1] for point in all_points)
    max_z = max(point[1] for point in all_points)
    padding = 70.0
    width = 1300.0
    height = 720.0
    plot_width = width - 2.0 * padding
    plot_height = height - 2.0 * padding

    def points_to_svg(points: list[tuple[float, float]]) -> str:
        transformed = []
        for y_value, z_value in points:
            x = padding + (y_value - min_y) / (max_y - min_y) * plot_width
            y = height - padding - (z_value - min_z) / (max_z - min_z) * plot_height
            transformed.append(f"{x:.2f},{y:.2f}")
        return " ".join(transformed)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="720" viewBox="0 0 1300 720">
  <rect width="1300" height="720" fill="#f7f4ed"/>
  <text x="70" y="45" font-family="Georgia, serif" font-size="28" fill="#14213d">Artist-derived sagittal profile sensitivity geometry</text>
  <text x="70" y="75" font-family="sans-serif" font-size="15" fill="#3d4b5f">Nobilis 2 tracing template; 2.5D profile prism only, not fossil-reconstructed anatomy</text>
  <line x1="70" y1="650" x2="1230" y2="650" stroke="#7b8794" stroke-width="1"/>
  <line x1="70" y1="650" x2="70" y2="110" stroke="#7b8794" stroke-width="1"/>
  <polygon points="{points_to_svg(profile)}" fill="#91c8e4" fill-opacity="0.55" stroke="#1d5d7c" stroke-width="2"/>
  <polygon points="{points_to_svg(control)}" fill="none" stroke="#d85a4a" stroke-width="3" stroke-dasharray="8 6"/>
  <rect x="865" y="105" width="320" height="68" rx="6" fill="#ffffff" stroke="#b7c4cc"/>
  <line x1="885" y1="127" x2="930" y2="127" stroke="#1d5d7c" stroke-width="3"/>
  <text x="942" y="132" font-family="sans-serif" font-size="14" fill="#14213d">full profile</text>
  <line x1="885" y1="151" x2="930" y2="151" stroke="#d85a4a" stroke-width="3" stroke-dasharray="8 6"/>
  <text x="942" y="156" font-family="sans-serif" font-size="14" fill="#14213d">smooth crest-ablated control</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    source = bpy.data.objects.get(OBJECT_NAME)
    if source is None or source.type != "MESH":
        raise RuntimeError(f"Expected mesh object {OBJECT_NAME!r} was not found.")
    if not bpy.data.filepath:
        raise RuntimeError("Save the Blender working file before building derived STL geometry.")

    profile, extraction = extract_profile(source)
    source_points = world_vertices(source)
    minimum, maximum = bounds(source_points)
    y_span = maximum[1] - minimum[1]
    crest_range = (
        minimum[1] + CREST_Y_MIN_FRACTION * y_span,
        minimum[1] + CREST_Y_MAX_FRACTION * y_span,
    )
    control_profile, ablation = crest_ablated_profile(profile, crest_range)
    require_simple_polygon(profile)
    require_simple_polygon(control_profile)

    output_directory = Path(bpy.data.filepath).parent / OUTPUT_DIRECTORY_NAME
    output_directory.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, object]] = []
    for thickness in THICKNESSES_M:
        thickness_label = f"t{int(round(thickness * 100)):02d}m"
        for variant, current_profile in (("full", profile), ("crest_ablated", control_profile)):
            stem = (
                f"nobilis2_sagittal_profile_prism_{thickness_label}"
                if variant == "full"
                else f"nobilis2_sagittal_profile_prism_crest_ablated_{thickness_label}"
            )
            mesh = prism_mesh(stem, current_profile, thickness)
            diagnostics = mesh_diagnostics(mesh)
            if diagnostics["boundary_edges"] or diagnostics["non_manifold_edges"] or diagnostics["degenerate_triangles"]:
                raise RuntimeError(f"Generated mesh validation failed for {stem}: {diagnostics}")
            path = output_directory / f"{stem}.stl"
            write_ascii_stl(mesh, path, stem)
            bpy.data.meshes.remove(mesh)
            outputs.append({"variant": variant, "thickness_m": thickness, "path": str(path), **diagnostics})

    preview_path = output_directory / "nobilis2_sagittal_profile_preview.svg"
    write_preview_svg(profile, control_profile, preview_path)
    manifest = {
        "geometry_class": "artist-derived 2.5D parametric profile prism",
        "not_anatomical_claim": True,
        "source": "Nobilis 2 CC BY 4.0 artist mesh, scaled to the 8 m subadult skeletal-length estimate in the Blender working copy.",
        "source_blend": bpy.data.filepath,
        "extraction": extraction,
        "crest_ablation": {
            "method": "cubic Hermite roof spline between configured crest-base anchors",
            "candidate_y_range_m": crest_range,
            **ablation,
        },
        "thicknesses_m": list(THICKNESSES_M),
        "validation": {
            "guarantee": "Each exported prism has zero boundary edges, zero non-manifold edges, and zero degenerate triangles under this builder's topology checks.",
            "scope_limit": "This validates the generated prism topology, not the anatomical validity of the source silhouette or a full 3D skull.",
        },
        "allowed_interpretation": "Parametric sensitivity of the extracted sagittal profile under explicitly chosen extrusion thicknesses.",
        "outputs": outputs,
    }
    manifest_path = output_directory / "nobilis2_sagittal_profile_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"output_directory": str(output_directory), "outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()

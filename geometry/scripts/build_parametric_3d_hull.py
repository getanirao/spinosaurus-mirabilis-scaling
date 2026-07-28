"""Build variable-width 3D hulls from the Nobilis 2 sagittal profile.

The source mesh is not used as a CFD surface.  This script instead combines
its cleaned sagittal envelope with a station-by-station width envelope to make
watertight, explicitly parametric 3D sensitivity geometries.  These are not
anatomical reconstructions or fossil-derived skull meshes.

Run inside Blender after opening ``mirabilis_cfd_prep_v01.blend``.
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
OUTPUT_DIRECTORY_NAME = "parametric_3d_hull_sensitivity"
HEAD_Y_MAX_FRACTION = 0.21283
CREST_Y_MIN_FRACTION = 0.06386
CREST_Y_MAX_FRACTION = 0.15188
SECTION_X_M = 0.0
PROFILE_SAMPLES = 241
RING_SAMPLES = 48
WIDTH_SAMPLE_RADIUS_M = 0.035
WIDTH_SCALES = (0.8, 1.0, 1.2)
NOSE_CLOSURE_LENGTH_M = 0.05
NOSE_CLOSURE_RINGS = 5
NOSE_LEADING_SCALE = 0.60
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
    candidates: list[Vector] = []
    for start, end in ((a, b), (b, c), (c, a)):
        start_distance = start.x - plane_x
        end_distance = end.x - plane_x
        if abs(start_distance) <= INTERSECTION_TOLERANCE_M:
            candidates.append(start.copy())
        if abs(end_distance) <= INTERSECTION_TOLERANCE_M:
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


def sagittal_segments(obj: bpy.types.Object) -> list[tuple[Vector, Vector]]:
    vertices = world_vertices(obj)
    segments: list[tuple[Vector, Vector]] = []
    for polygon in obj.data.polygons:
        indices = polygon.vertices[:]
        for index in range(1, len(indices) - 1):
            segment = triangle_plane_segment(
                vertices[indices[0]], vertices[indices[index]], vertices[indices[index + 1]], SECTION_X_M
            )
            if segment is not None:
                segments.append(segment)
    return segments


def values_at_y(segments: list[tuple[Vector, Vector]], y_value: float) -> list[float]:
    values: list[float] = []
    for start, end in segments:
        low_y = min(start.y, end.y)
        high_y = max(start.y, end.y)
        if not low_y - INTERSECTION_TOLERANCE_M <= y_value <= high_y + INTERSECTION_TOLERANCE_M:
            continue
        delta_y = end.y - start.y
        if abs(delta_y) <= INTERSECTION_TOLERANCE_M:
            values.extend((start.z, end.z))
            continue
        fraction = (y_value - start.y) / delta_y
        if -INTERSECTION_TOLERANCE_M <= fraction <= 1.0 + INTERSECTION_TOLERANCE_M:
            values.append(start.z + fraction * (end.z - start.z))
    return values


def interpolate_missing(values: list[float | None]) -> list[float]:
    present = [index for index, value in enumerate(values) if value is not None]
    if not present:
        raise RuntimeError("No usable sagittal profile values were extracted.")
    completed = values[:]
    first, last = present[0], present[-1]
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
        left, right = float(completed[run_start]), float(completed[run_end])
        for missing in range(run_start + 1, run_end):
            fraction = (missing - run_start) / (run_end - run_start)
            completed[missing] = left + fraction * (right - left)
    return [float(value) for value in completed]


def median_smooth(values: list[float], radius: int = MEDIAN_RADIUS) -> list[float]:
    return [
        float(median(values[max(0, index - radius) : min(len(values), index + radius + 1)]))
        for index in range(len(values))
    ]


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("Quantile requires at least one value.")
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def hermite(y0: float, z0: float, slope0: float, y1: float, z1: float, slope1: float, y: float) -> float:
    span = y1 - y0
    t = (y - y0) / span
    h00 = 2.0 * t**3 - 3.0 * t**2 + 1.0
    h10 = t**3 - 2.0 * t**2 + t
    h01 = -2.0 * t**3 + 3.0 * t**2
    h11 = t**3 - t**2
    return h00 * z0 + h10 * span * slope0 + h01 * z1 + h11 * span * slope1


def profile_data(obj: bpy.types.Object) -> tuple[list[float], list[float], list[float], dict[str, object]]:
    points = world_vertices(obj)
    minimum, maximum = bounds(points)
    head_y_max = minimum[1] + HEAD_Y_MAX_FRACTION * (maximum[1] - minimum[1])
    y_values = [
        minimum[1] + (head_y_max - minimum[1]) * index / (PROFILE_SAMPLES - 1)
        for index in range(PROFILE_SAMPLES)
    ]
    segments = sagittal_segments(obj)
    lower_raw: list[float | None] = []
    upper_raw: list[float | None] = []
    for y_value in y_values:
        intersections = values_at_y(segments, y_value)
        lower_raw.append(min(intersections) if intersections else None)
        upper_raw.append(max(intersections) if intersections else None)
    lower = median_smooth(interpolate_missing(lower_raw))
    upper = median_smooth(interpolate_missing(upper_raw))
    for index, (lower_value, upper_value) in enumerate(zip(lower, upper)):
        if upper_value - lower_value < 0.001:
            midpoint = 0.5 * (lower_value + upper_value)
            lower[index] = midpoint - 0.0005
            upper[index] = midpoint + 0.0005

    head_points = [point for point in points if point.y <= head_y_max]
    raw_widths: list[float | None] = []
    for y_value in y_values:
        nearby = [abs(point.x) for point in head_points if abs(point.y - y_value) <= WIDTH_SAMPLE_RADIUS_M]
        raw_widths.append(quantile(nearby, 0.90) if len(nearby) >= 8 else None)
    widths = median_smooth(interpolate_missing(raw_widths))
    widths = [max(width, 0.006) for width in widths]

    return y_values, lower, upper, {
        "head_y_range_m": [minimum[1], head_y_max],
        "sagittal_segment_count": len(segments),
        "width_sampling_radius_m": WIDTH_SAMPLE_RADIUS_M,
        "width_quantile": 0.90,
        "half_width_range_m": [min(widths), max(widths)],
        "half_widths_m": widths,
    }


def ablated_upper(
    y_values: list[float], upper: list[float], crest_y_range: tuple[float, float]
) -> tuple[list[float], dict[str, float]]:
    start_target, end_target = crest_y_range
    start = min(range(len(y_values)), key=lambda index: abs(y_values[index] - start_target))
    end = min(range(len(y_values)), key=lambda index: abs(y_values[index] - end_target))
    if start >= end:
        raise RuntimeError("Crest-ablation anchors are not ordered.")

    result = upper[:]
    window = max(4, int(0.04 * len(y_values)))
    left_slope = (upper[start] - upper[max(0, start - window)]) / (y_values[start] - y_values[max(0, start - window)])
    right_slope = (upper[min(len(upper) - 1, end + window)] - upper[end]) / (y_values[min(len(upper) - 1, end + window)] - y_values[end])
    for index in range(start, end + 1):
        result[index] = hermite(y_values[start], upper[start], left_slope, y_values[end], upper[end], right_slope, y_values[index])
    return result, {
        "anchor_y_start_m": y_values[start],
        "anchor_y_end_m": y_values[end],
        "left_slope": left_slope,
        "right_slope": right_slope,
    }


def interpolate_at(y_values: list[float], values: list[float], target_y: float) -> float:
    if target_y <= y_values[0]:
        return values[0]
    if target_y >= y_values[-1]:
        return values[-1]
    for index in range(1, len(y_values)):
        if y_values[index] >= target_y:
            fraction = (target_y - y_values[index - 1]) / (y_values[index] - y_values[index - 1])
            return values[index - 1] + fraction * (values[index] - values[index - 1])
    raise RuntimeError("Interpolation target was outside the profile range.")


def source_bounded_nose_stations(
    y_values: list[float], lower: list[float], upper: list[float], half_widths: list[float]
) -> tuple[list[float], list[float], list[float], list[float], tuple[float, float]]:
    """Replace the first source interval with a blunt, source-bounded closure."""
    nose_center = 0.5 * (lower[0] + upper[0])
    nose_tip_y = y_values[0]
    closure_end_y = min(y_values[-1], nose_tip_y + NOSE_CLOSURE_LENGTH_M)
    transition_y: list[float] = []
    transition_lower: list[float] = []
    transition_upper: list[float] = []
    transition_widths: list[float] = []
    for index in range(NOSE_CLOSURE_RINGS + 1):
        fraction = index / NOSE_CLOSURE_RINGS
        radial_scale = NOSE_LEADING_SCALE + (1.0 - NOSE_LEADING_SCALE) * math.sin(0.5 * math.pi * fraction)
        y_value = nose_tip_y + (closure_end_y - nose_tip_y) * fraction
        lower_value = interpolate_at(y_values, lower, y_value)
        upper_value = interpolate_at(y_values, upper, y_value)
        center = 0.5 * (lower_value + upper_value)
        half_height = 0.5 * (upper_value - lower_value)
        transition_y.append(y_value)
        transition_lower.append(center - half_height * radial_scale)
        transition_upper.append(center + half_height * radial_scale)
        transition_widths.append(interpolate_at(y_values, half_widths, y_value) * radial_scale)
    retained_index = next(index for index, y_value in enumerate(y_values) if y_value > closure_end_y)
    return (
        transition_y + y_values[retained_index:],
        transition_lower + lower[retained_index:],
        transition_upper + upper[retained_index:],
        transition_widths + half_widths[retained_index:],
        (nose_tip_y, nose_center),
    )


def loft_mesh(
    name: str,
    y_values: list[float],
    lower: list[float],
    upper: list[float],
    half_widths: list[float],
    width_scale: float,
    nose_tip: tuple[float, float],
) -> bpy.types.Mesh:
    vertices: list[tuple[float, float, float]] = []
    for y_value, lower_value, upper_value, half_width in zip(y_values, lower, upper, half_widths):
        center = 0.5 * (lower_value + upper_value)
        half_height = 0.5 * (upper_value - lower_value)
        for ring_index in range(RING_SAMPLES):
            theta = 2.0 * math.pi * ring_index / RING_SAMPLES
            vertices.append((
                width_scale * half_width * math.sin(theta),
                y_value,
                center + half_height * math.cos(theta),
            ))

    faces: list[tuple[int, ...]] = []
    for station in range(len(y_values) - 1):
        for ring_index in range(RING_SAMPLES):
            next_ring = (ring_index + 1) % RING_SAMPLES
            start = station * RING_SAMPLES + ring_index
            next_station = (station + 1) * RING_SAMPLES
            faces.append((start, station * RING_SAMPLES + next_ring, next_station + next_ring, next_station + ring_index))
    front_center = len(vertices)
    vertices.append((0.0, nose_tip[0], nose_tip[1]))
    rear_center = len(vertices)
    vertices.append((0.0, y_values[-1], 0.5 * (lower[-1] + upper[-1])))
    for ring_index in range(RING_SAMPLES):
        next_ring = (ring_index + 1) % RING_SAMPLES
        faces.append((front_center, next_ring, ring_index))
        rear_start = (len(y_values) - 1) * RING_SAMPLES
        faces.append((rear_center, rear_start + ring_index, rear_start + next_ring))

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
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.update()
    return mesh


def mesh_diagnostics(mesh: bpy.types.Mesh) -> dict[str, object]:
    edge_face_counts: dict[tuple[int, int], int] = {}
    degenerate_triangles = 0
    signed_volume = 0.0
    for polygon in mesh.polygons:
        if len(polygon.vertices) != 3:
            raise RuntimeError("Hull mesh was not triangulated.")
        a, b, c = (mesh.vertices[index].co for index in polygon.vertices)
        cross = (b - a).cross(c - a)
        if cross.length * 0.5 <= AREA_TOLERANCE_M2:
            degenerate_triangles += 1
        signed_volume += a.dot(cross) / 6.0
        for index, first in enumerate(polygon.vertices):
            second = polygon.vertices[(index + 1) % len(polygon.vertices)]
            edge = tuple(sorted((first, second)))
            edge_face_counts[edge] = edge_face_counts.get(edge, 0) + 1
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
        lines.extend((
            f"  facet normal {normal.x:.9g} {normal.y:.9g} {normal.z:.9g}",
            "    outer loop",
            f"      vertex {a.x:.9g} {a.y:.9g} {a.z:.9g}",
            f"      vertex {b.x:.9g} {b.y:.9g} {b.z:.9g}",
            f"      vertex {c.x:.9g} {c.y:.9g} {c.z:.9g}",
            "    endloop",
            "  endfacet",
        ))
    lines.append(f"endsolid {solid_name}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def run() -> dict[str, object]:
    obj = bpy.data.objects.get(OBJECT_NAME)
    if obj is None or obj.type != "MESH":
        raise RuntimeError(f"Expected mesh object {OBJECT_NAME!r} was not found.")
    output_directory = Path(bpy.data.filepath).parent / OUTPUT_DIRECTORY_NAME
    output_directory.mkdir(exist_ok=True)

    y_values, lower, upper, profile_metadata = profile_data(obj)
    source_minimum, source_maximum = bounds(world_vertices(obj))
    source_y_span = source_maximum[1] - source_minimum[1]
    crest_y_range = (
        source_minimum[1] + CREST_Y_MIN_FRACTION * source_y_span,
        source_minimum[1] + CREST_Y_MAX_FRACTION * source_y_span,
    )
    ablated, ablation_metadata = ablated_upper(y_values, upper, crest_y_range)
    half_widths = list(profile_metadata.pop("half_widths_m"))
    variants: list[dict[str, object]] = []
    collection = bpy.data.collections.get("PARAMETRIC_3D_HULLS")
    if collection is None:
        collection = bpy.data.collections.new("PARAMETRIC_3D_HULLS")
        bpy.context.scene.collection.children.link(collection)

    for width_scale in WIDTH_SCALES:
        for morph_name, morph_upper in (("full", upper), ("crest_ablated", ablated)):
            stem = f"nobilis2_parametric_3d_hull_{morph_name}_w{width_scale:.2f}".replace(".", "")
            loft_values = source_bounded_nose_stations(y_values, lower, morph_upper, half_widths)
            mesh = loft_mesh(stem, *loft_values[:-1], width_scale, loft_values[-1])
            diagnostics = mesh_diagnostics(mesh)
            if any(diagnostics[key] for key in ("boundary_edges", "non_manifold_edges", "degenerate_triangles")):
                raise RuntimeError(f"{stem} failed manifold validation: {diagnostics}")
            output_path = output_directory / f"{stem}.stl"
            write_ascii_stl(mesh, output_path, stem)
            existing = bpy.data.objects.get(stem)
            if existing is not None:
                bpy.data.objects.remove(existing, do_unlink=True)
            hull = bpy.data.objects.new(stem, mesh)
            collection.objects.link(hull)
            hull.hide_viewport = True
            hull.hide_render = True
            variants.append({
                "name": stem,
                "morph": morph_name,
                "width_scale": width_scale,
                "path": str(output_path),
                **diagnostics,
            })

    manifest = {
        "method": {
            "name": "artist-derived variable-width parametric 3D hull",
            "source_geometry": "Nobilis 2 CC BY 4.0 artist mesh, used only for profile and width-envelope measurements.",
            "construction": "Sagittal min/max envelope lofted through elliptical cross-sections with source-derived longitudinal half-widths.",
            "interpretation": "Sensitivity geometry only; not an anatomical reconstruction, skull mesh, or fossil-derived surface.",
            "excluded_features": "Teeth, internal cavities, detached artist-mesh parts, soft tissue, and unverified transverse crest anatomy.",
        },
        "parameters": {
            "profile_samples": PROFILE_SAMPLES,
            "ring_samples": RING_SAMPLES,
            "width_scales": list(WIDTH_SCALES),
            "nose_closure": {
                "type": "smooth source-bounded numerical closure shared by all variants",
                "inboard_length_m": NOSE_CLOSURE_LENGTH_M,
                "transition_rings": NOSE_CLOSURE_RINGS,
                "leading_section_scale": NOSE_LEADING_SCALE,
            },
            "crest_ablation": ablation_metadata,
            **profile_metadata,
        },
        "validation": "Surface-topology validation only. Run OpenFOAM surfaceCheck and a volume-mesh quality check before any solver claim.",
        "variants": variants,
    }
    (output_directory / "nobilis2_parametric_3d_hull_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

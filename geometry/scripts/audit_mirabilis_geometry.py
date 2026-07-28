"""Audit an artist-authored mirabilis mesh before CFD preparation.

Run this inside Blender after opening ``mirabilis_cfd_prep_v01.blend``.  The
calculation deliberately reports orientation-weighted surface exposure, not
drag, pressure, or a CFD result.  It helps decide which motions deserve a
proper watertight-mesh and flow-solver study.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


OBJECT_NAME = "MIRABILIS_REFERENCE_SURFACE"
OUTPUT_NAME = "mirabilis_geometry_audit_v01.json"

# These normalized bounds came from the original 14.77-unit source scene.  By
# keeping them dimensionless, the same anatomical cut is used after scaling
# the derived mesh to the 8 m subadult skeletal estimate.
HEAD_Y_MAX_FRACTION = 0.21283
CREST_Y_MIN_FRACTION = 0.06386
CREST_Y_MAX_FRACTION = 0.15188
CREST_Z_FLOOR_FRACTIONS = (0.69486, 0.73317, 0.77148)

AXES = {
    "head_first": Vector((0.0, 1.0, 0.0)),
    "lateral_yaw": Vector((1.0, 0.0, 0.0)),
    "vertical_pitch": Vector((0.0, 0.0, 1.0)),
}


def world_vertices(obj: bpy.types.Object) -> list[Vector]:
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def triangle_area_normal(a: Vector, b: Vector, c: Vector) -> tuple[float, Vector]:
    cross = (b - a).cross(c - a)
    area = cross.length * 0.5
    if area == 0.0:
        return 0.0, Vector((0.0, 0.0, 0.0))
    return area, cross.normalized()


def face_records(obj: bpy.types.Object) -> list[dict[str, object]]:
    vertices = world_vertices(obj)
    records: list[dict[str, object]] = []

    for polygon in obj.data.polygons:
        polygon_vertices = [vertices[index] for index in polygon.vertices]
        centroid = sum(polygon_vertices, Vector()) / len(polygon_vertices)
        area = 0.0
        normal = Vector((0.0, 0.0, 0.0))

        # The source mesh is triangulated, but this also keeps the audit valid
        # if a later working copy contains quads.
        for index in range(1, len(polygon_vertices) - 1):
            triangle_area, triangle_normal = triangle_area_normal(
                polygon_vertices[0], polygon_vertices[index], polygon_vertices[index + 1]
            )
            area += triangle_area
            normal += triangle_normal * triangle_area

        records.append(
            {
                "centroid": centroid,
                "area": area,
                "normal": normal.normalized() if normal.length else normal,
            }
        )
    return records


def exposure(records: list[dict[str, object]], axis: Vector) -> float:
    """Return a geometry proxy, not a projected silhouette or a force."""
    return sum(
        float(record["area"]) * abs(Vector(record["normal"]).dot(axis))
        for record in records
    )


def edge_diagnostics(obj: bpy.types.Object) -> dict[str, int]:
    edge_face_counts: dict[tuple[int, int], int] = {}
    for polygon in obj.data.polygons:
        indices = polygon.vertices[:]
        for index, vertex_a in enumerate(indices):
            vertex_b = indices[(index + 1) % len(indices)]
            key = tuple(sorted((vertex_a, vertex_b)))
            edge_face_counts[key] = edge_face_counts.get(key, 0) + 1
    return {
        "boundary_edges": sum(count == 1 for count in edge_face_counts.values()),
        "non_manifold_edges": sum(count > 2 for count in edge_face_counts.values()),
    }


def audit() -> dict[str, object]:
    obj = bpy.data.objects.get(OBJECT_NAME)
    if obj is None or obj.type != "MESH":
        raise RuntimeError(f"Expected mesh object {OBJECT_NAME!r} was not found.")

    points = world_vertices(obj)
    minimum = tuple(min(point[index] for point in points) for index in range(3))
    maximum = tuple(max(point[index] for point in points) for index in range(3))
    y_span = maximum[1] - minimum[1]
    z_span = maximum[2] - minimum[2]
    head_y_max = minimum[1] + HEAD_Y_MAX_FRACTION * y_span
    crest_y_min = minimum[1] + CREST_Y_MIN_FRACTION * y_span
    crest_y_max = minimum[1] + CREST_Y_MAX_FRACTION * y_span
    crest_z_floors = [minimum[2] + fraction * z_span for fraction in CREST_Z_FLOOR_FRACTIONS]

    records = face_records(obj)
    head_records = [
        record for record in records if Vector(record["centroid"]).y <= head_y_max
    ]
    if not head_records:
        raise RuntimeError("The configured head-region cut selected no faces.")

    variants = []
    for z_floor in crest_z_floors:
        candidate_records = [
            record
            for record in head_records
            if crest_y_min <= Vector(record["centroid"]).y <= crest_y_max
            and Vector(record["centroid"]).z >= z_floor
        ]
        axis_results = {}
        for axis_name, axis in AXES.items():
            head_exposure = exposure(head_records, axis)
            candidate_exposure = exposure(candidate_records, axis)
            axis_results[axis_name] = {
                "head_region_m2": round(head_exposure, 6),
                "crest_candidate_m2": round(candidate_exposure, 6),
                "crest_candidate_share_pct": round(
                    100.0 * candidate_exposure / head_exposure, 4
                )
                if head_exposure
                else None,
            }
        variants.append(
            {
                "crest_candidate_z_floor_m": z_floor,
                "candidate_face_count": len(candidate_records),
                "orientation_weighted_exposure": axis_results,
            }
        )

    return {
        "method": {
            "name": "orientation-weighted surface exposure sensitivity",
            "interpretation": (
                "Geometric proxy used to compare orientation sensitivity. It is not "
                "a silhouette area, pressure calculation, drag estimate, water-entry "
                "simulation, or validated CFD result."
            ),
            "source_geometry": "Artist-authored CC BY 4.0 reference mesh by Nobilis 2.",
        },
        "mesh": {
            "object": obj.name,
            "vertices": len(obj.data.vertices),
            "triangles": sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons),
            "world_bounds_min_m": minimum,
            "world_bounds_max_m": maximum,
            **edge_diagnostics(obj),
        },
        "head_region": {
            "criterion": f"face centroid y <= {head_y_max:.6f} m",
            "face_count": len(head_records),
        },
        "crest_candidate_sensitivity": {
            "y_range_m": [round(crest_y_min, 6), round(crest_y_max, 6)],
            "z_floor_values_m": [round(value, 6) for value in crest_z_floors],
            "variants": variants,
        },
        "next_requirement": (
            "Any hydrodynamic conclusion requires fossil-constrained geometry, a "
            "watertight surface, mesh/time-step convergence, and an appropriate "
            "free-surface CFD model."
        ),
    }


if __name__ == "__main__":
    result = audit()
    output_path = Path(bpy.data.filepath).parent / OUTPUT_NAME
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Wrote {output_path}")

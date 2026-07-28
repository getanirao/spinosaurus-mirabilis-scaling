#!/usr/bin/env bash
# OpenFOAM surface preflight for artist-derived 2.5D profile-prism sensitivity STLs.
#
# Run from a shell where an OpenFOAM environment has already been sourced:
#   bash geometry/scripts/validate_profile_prisms.sh
#
# This script does not repair, re-orient, transform, or overwrite any STL.
set -euo pipefail

FEATURE_ANGLE="${FEATURE_ANGLE:-150}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SURFACE_DIR="${PROJECT_ROOT}/geometry/derived/profile_prism_sensitivity"
REPORT_DIR="${SURFACE_DIR}/openfoam_validation"

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        printf 'Missing required OpenFOAM utility: %s\n' "$1" >&2
        printf 'Source your OpenFOAM environment, then run this script again.\n' >&2
        exit 127
    }
}

require_command surfaceCheck
require_command surfaceFeatureExtract

mkdir -p "${REPORT_DIR}"

surfaces=(
    "${SURFACE_DIR}"/nobilis2_sagittal_profile_prism*.stl
)

if [[ ! -e "${surfaces[0]}" ]]; then
    printf 'No profile-prism STL files found in %s\n' "${SURFACE_DIR}" >&2
    exit 1
fi

printf 'OpenFOAM version: %s\n' "${WM_PROJECT_VERSION:-unknown}" | tee "${REPORT_DIR}/run_metadata.txt"
printf 'Feature included angle: %s degrees\n' "${FEATURE_ANGLE}" | tee -a "${REPORT_DIR}/run_metadata.txt"

for surface in "${surfaces[@]}"; do
    stem="$(basename "${surface}" .stl)"
    log_path="${REPORT_DIR}/${stem}.surfaceCheck.log"
    feature_stem="${REPORT_DIR}/${stem}_features"

    printf '\n=== %s ===\n' "${stem}" | tee "${log_path}"
    sha256sum "${surface}" | tee -a "${log_path}"

    # -checkSelfIntersection is required because a closed surface can still
    # self-intersect. -verbose retains bounding-box, normal, and edge details.
    surfaceCheck \
        -checkSelfIntersection \
        -verbose \
        -outputThreshold 100 \
        "${surface}" 2>&1 | tee -a "${log_path}"

    # The current OpenFOAM utility is surfaceFeatureExtract. A 150 degree
    # included-angle threshold captures the prisms' 90 degree side/cap edges.
    surfaceFeatureExtract \
        -includedAngle "${FEATURE_ANGLE}" \
        "${surface}" \
        "${feature_stem}" 2>&1 | tee "${REPORT_DIR}/${stem}.surfaceFeatureExtract.log"

    printf '\nReview before meshing: %s\n' "${log_path}"
    printf '%s\n' '  - closed/manifold status and self-intersection result'
    printf '%s\n' '  - bounding box against the planned blockMesh domain'
    printf '%s\n' '  - normal-region/orientation diagnostics'
    printf '%s\n' '  - smallest reported edge against the planned local refinement'
done

printf '\nPreflight complete. Feature meshes and logs are in %s\n' "${REPORT_DIR}"
printf '%s\n' 'Do not run snappyHexMesh until every surfaceCheck log has been reviewed.'

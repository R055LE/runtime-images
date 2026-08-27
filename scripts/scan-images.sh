#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
reports_dir="${REPORTS_DIR:-${repo_root}/build/reports}"
severity="CRITICAL,HIGH"

command -v trivy >/dev/null 2>&1 || {
    echo "scan failed: trivy is not installed" >&2
    exit 1
}

mkdir -p "$reports_dir"

for variant in runtime build; do
    if [ "$variant" = runtime ]; then
        image="${RUNTIME_IMAGE:-runtime-python:3.14-local}"
    else
        image="${BUILD_IMAGE:-runtime-python:3.14-build-local}"
    fi
    report="${reports_dir}/python-3.14.${variant}.trivy.json"

    trivy image \
        --format json \
        --output "$report" \
        --severity "$severity" \
        --exit-code 0 \
        "$image"
    trivy image \
        --format table \
        --severity "$severity" \
        --exit-code 0 \
        "$image"
    python3 "${repo_root}/scripts/vulnerability_gate.py" \
        --trivy-report "$report" \
        --register "${repo_root}/docs/known-findings.md"
done

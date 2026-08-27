#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir="${OUTPUT_DIR:-${repo_root}/build}"

# This file is generated from constrained registry names, tags, and sha256 digests.
# shellcheck source=/dev/null
source "${output_dir}/published.env"

promote() {
    local source_ref=$1
    local rolling_ref=$2
    local expected_digest=$3
    local actual_digest

    docker buildx imagetools create --tag "$rolling_ref" "$source_ref"
    actual_digest=$(docker buildx imagetools inspect "$rolling_ref" \
        | awk '$1 == "Digest:" {print $2; exit}')
    [ "$actual_digest" = "$expected_digest" ] || {
        echo "promotion failed: $rolling_ref resolved to $actual_digest" >&2
        exit 1
    }
}

promote "$RUNTIME_REF" "${IMAGE_NAME}:3.14" "$RUNTIME_DIGEST"
promote "$BUILD_REF" "${IMAGE_NAME}:3.14-build" "$BUILD_DIGEST"

printf 'Promoted Python release set %s to rolling tags\n' "$RELEASE_ID"

#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir="${OUTPUT_DIR:-${repo_root}/build}"
image="${IMAGE_NAME:-ghcr.io/r055le/runtime-python}"
release_id=$(<"${output_dir}/release-id")
published_env="${output_dir}/published.env"
runtime_log=$(mktemp)
build_log=$(mktemp)
trap 'rm -f "$runtime_log" "$build_log"' EXIT

[[ "$release_id" =~ ^[0-9a-f]{16}$ ]] || {
    echo "publish failed: invalid release ID" >&2
    exit 1
}
[[ "$image" =~ ^ghcr\.io/[a-z0-9._/-]+$ ]] || {
    echo "publish failed: invalid GHCR image name" >&2
    exit 1
}

runtime_tag="3.14-${release_id}"
build_tag="3.14-build-${release_id}"
runtime_image="${image}:${runtime_tag}"
build_image="${image}:${build_tag}"

docker tag runtime-python:3.14-local "$runtime_image"
docker tag runtime-python:3.14-build-local "$build_image"
docker push "$runtime_image" | tee "$runtime_log"
docker push "$build_image" | tee "$build_log"

runtime_digest=$(awk '$1 == "digest:" {print $2}' "$runtime_log" | tail -n 1)
build_digest=$(awk '$1 == "digest:" {print $2}' "$build_log" | tail -n 1)
[[ "$runtime_digest" =~ ^sha256:[0-9a-f]{64}$ ]] || {
    echo "publish failed: could not resolve runtime digest" >&2
    exit 1
}
[[ "$build_digest" =~ ^sha256:[0-9a-f]{64}$ ]] || {
    echo "publish failed: could not resolve build digest" >&2
    exit 1
}

{
    printf 'RELEASE_ID=%s\n' "$release_id"
    printf 'IMAGE_NAME=%s\n' "$image"
    printf 'RUNTIME_TAG=%s\n' "$runtime_tag"
    printf 'RUNTIME_DIGEST=%s\n' "$runtime_digest"
    printf 'RUNTIME_REF=%s@%s\n' "$runtime_image" "$runtime_digest"
    printf 'BUILD_TAG=%s\n' "$build_tag"
    printf 'BUILD_DIGEST=%s\n' "$build_digest"
    printf 'BUILD_REF=%s@%s\n' "$build_image" "$build_digest"
} >"$published_env"

printf 'Published immutable Python release set %s\n' "$release_id"

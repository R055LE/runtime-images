#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

if [ -n "${BUILD_DATE:-}" ]; then
    printf '%s\n' "$BUILD_DATE"
elif git -C "$repo_root" status --porcelain -- \
    images/python/3.14 tools/apko.Dockerfile | grep -q .; then
    git -C "$repo_root" show -s --format=%cI HEAD
else
    source_revision=$(git -C "$repo_root" log -1 --format=%H -- \
        images/python/3.14 tools/apko.Dockerfile)
    git -C "$repo_root" show -s --format=%cI "${source_revision:-HEAD}"
fi

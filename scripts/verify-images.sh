#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_image="${RUNTIME_IMAGE:-runtime-python:3.14-local}"
build_image="${BUILD_IMAGE:-runtime-python:3.14-build-local}"
release_id=$(<"${repo_root}/build/release-id")

runtime_user=$(docker image inspect --format '{{.Config.User}}' "$runtime_image")
runtime_entrypoint=$(docker image inspect --format '{{json .Config.Entrypoint}}' "$runtime_image")
build_entrypoint=$(docker image inspect --format '{{json .Config.Entrypoint}}' "$build_image")
runtime_release=$(docker image inspect \
    --format '{{index .Config.Labels "io.r055le.runtime.release"}}' "$runtime_image")
build_release=$(docker image inspect \
    --format '{{index .Config.Labels "io.r055le.runtime.release"}}' "$build_image")

[ "$runtime_user" = 65532 ] || {
    echo "runtime contract failed: configured user is ${runtime_user:-root}" >&2
    exit 1
}
[ "$runtime_entrypoint" = '["/usr/bin/python"]' ] || {
    echo "runtime contract failed: entrypoint is $runtime_entrypoint" >&2
    exit 1
}
[ "$build_entrypoint" = '["/usr/bin/python"]' ] || {
    echo "build contract failed: entrypoint is $build_entrypoint" >&2
    exit 1
}
[ "$runtime_release" = "$release_id" ] || {
    echo "runtime contract failed: release annotation is $runtime_release" >&2
    exit 1
}
[ "$build_release" = "$release_id" ] || {
    echo "build contract failed: release annotation is $build_release" >&2
    exit 1
}

docker run --rm \
    --network none \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges:true \
    --tmpfs /tmp:rw,noexec,nosuid,size=16m,uid=65532,gid=65532 \
    --volume "${repo_root}/tests/contracts:/contracts:ro" \
    --entrypoint /usr/bin/python \
    "$runtime_image" /contracts/runtime.py

docker run --rm \
    --network none \
    --cap-drop ALL \
    --security-opt no-new-privileges:true \
    --tmpfs /tmp:rw,exec,nosuid,size=64m \
    --volume "${repo_root}/tests/contracts:/contracts:ro" \
    --entrypoint /usr/bin/python \
    "$build_image" /contracts/build.py

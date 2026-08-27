#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir="${OUTPUT_DIR:-${repo_root}/build}"
cache_dir="${output_dir}/cache"
tool_image="runtime-images-apko:1.2.40"
tool_dockerfile="${repo_root}/tools/apko.Dockerfile"
uid=$(id -u)
gid=$(id -g)
build_date=$("${repo_root}/scripts/release-date.sh")
release_id=$(python3 "${repo_root}/scripts/check_locks.py" \
    "${output_dir}/python-3.14.runtime.lock.json" \
    "${output_dir}/python-3.14.build.lock.json" \
    --input "${repo_root}/images/python/3.14/runtime.apko.yaml" \
    --input "${repo_root}/images/python/3.14/build.apko.yaml" \
    --input "${tool_dockerfile}" \
    --value "build-date=${build_date}")

mkdir -p "${output_dir}/sbom/runtime" "${output_dir}/sbom/build"
printf '%s\n' "$release_id" >"${output_dir}/release-id"

for variant in runtime build; do
    if [ "$variant" = runtime ]; then
        local_tag="runtime-python:3.14-local"
    else
        local_tag="runtime-python:3.14-build-local"
    fi

    docker run --rm \
        --user "${uid}:${gid}" \
        --volume "${repo_root}:/work" \
        "$tool_image" build \
        --arch amd64 \
        --build-date "$build_date" \
        --cache-dir "/work/${cache_dir#"${repo_root}/"}" \
        --lockfile "/work/${output_dir#"${repo_root}/"}/python-3.14.${variant}.lock.json" \
        --sbom-path "/work/${output_dir#"${repo_root}/"}/sbom/${variant}" \
        --annotations "org.opencontainers.image.created:${build_date}" \
        --annotations "org.opencontainers.image.version:${release_id}" \
        --annotations "io.r055le.runtime.release:${release_id}" \
        "/work/images/python/3.14/${variant}.apko.yaml" \
        "$local_tag" \
        "/work/${output_dir#"${repo_root}/"}/python-3.14.${variant}.tar"

    docker load --input "${output_dir}/python-3.14.${variant}.tar"
    docker tag "${local_tag}-amd64" "$local_tag"
done

printf 'Built Python release set %s\n' "$release_id"

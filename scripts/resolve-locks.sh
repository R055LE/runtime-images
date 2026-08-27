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

mkdir -p "$output_dir" "$cache_dir"

docker build --pull --tag "$tool_image" --file "$tool_dockerfile" "${repo_root}/tools"

for variant in runtime build; do
    docker run --rm \
        --user "${uid}:${gid}" \
        --volume "${repo_root}:/work" \
        "$tool_image" lock \
        --arch amd64 \
        --cache-dir "/work/${cache_dir#"${repo_root}/"}" \
        --output "/work/${output_dir#"${repo_root}/"}/python-3.14.${variant}.lock.json" \
        "/work/images/python/3.14/${variant}.apko.yaml"
done

python3 "${repo_root}/scripts/check_locks.py" \
    "${output_dir}/python-3.14.runtime.lock.json" \
    "${output_dir}/python-3.14.build.lock.json" \
    --input "${repo_root}/images/python/3.14/runtime.apko.yaml" \
    --input "${repo_root}/images/python/3.14/build.apko.yaml" \
    --input "${tool_dockerfile}" \
    --value "build-date=${build_date}"

#!/usr/bin/env python3
"""Create the permanent manifest and notes for a Python image release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from check_locks import LockError, load_lock, package_map

DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
RELEASE_RE = re.compile(r"[0-9a-f]{16}")


class ManifestError(Exception):
    pass


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ManifestError(f"could not hash {path}: {exc}") from exc


def packages(path: Path) -> list[dict[str, str]]:
    try:
        records = package_map(load_lock(path), path)
    except LockError as exc:
        raise ManifestError(str(exc)) from exc
    return [
        {
            "architecture": architecture,
            "name": name,
            "version": version,
            "checksum": checksum,
        }
        for (architecture, name), (version, checksum) in sorted(records.items())
    ]


def package_delta(
    current: list[dict[str, str]], previous: list[dict[str, str]] | None
) -> dict[str, list[dict[str, str]]]:
    if previous is None:
        return {"added": current, "removed": [], "updated": []}

    current_by_name = {
        (item["architecture"], item["name"]): item for item in current
    }
    previous_by_name = {
        (item["architecture"], item["name"]): item for item in previous
    }
    added = [
        current_by_name[key]
        for key in sorted(current_by_name.keys() - previous_by_name.keys())
    ]
    removed = [
        previous_by_name[key]
        for key in sorted(previous_by_name.keys() - current_by_name.keys())
    ]
    updated = []
    for key in sorted(current_by_name.keys() & previous_by_name.keys()):
        before = previous_by_name[key]
        after = current_by_name[key]
        if (before["version"], before["checksum"]) != (
            after["version"],
            after["checksum"],
        ):
            updated.append(
                {
                    "architecture": after["architecture"],
                    "name": after["name"],
                    "previous_version": before["version"],
                    "version": after["version"],
                }
            )
    return {"added": added, "removed": removed, "updated": updated}


def load_previous(path: Path | None) -> list[dict[str, str]] | None:
    if path is None or not path.exists():
        return None
    return packages(path)


def artifact(path: Path) -> dict[str, str]:
    return {"name": path.name, "sha256": sha256(path)}


def image_record(
    image: str,
    tag: str,
    digest: str,
    lock_path: Path,
    sbom_path: Path,
    report_path: Path,
    previous_lock_path: Path | None,
) -> dict[str, Any]:
    if not DIGEST_RE.fullmatch(digest):
        raise ManifestError(f"invalid image digest: {digest}")
    current_packages = packages(lock_path)
    previous_packages = load_previous(previous_lock_path)
    return {
        "image": image,
        "tag": tag,
        "digest": digest,
        "immutable_ref": f"{image}:{tag}@{digest}",
        "packages": current_packages,
        "package_delta": package_delta(current_packages, previous_packages),
        "artifacts": {
            "lock": artifact(lock_path),
            "sbom": artifact(sbom_path),
            "trivy_report": artifact(report_path),
        },
    }


def render_notes(manifest: dict[str, Any], initial: bool) -> str:
    release_id = manifest["release_id"]
    lines = [
        f"# Python 3.14 runtime release {release_id}",
        "",
        "Exact images:",
        "",
        f"- Runtime: `{manifest['images']['runtime']['immutable_ref']}`",
        f"- Build: `{manifest['images']['build']['immutable_ref']}`",
        "",
    ]
    if initial:
        lines.append("Initial locked package set:")
        lines.append("")
        for variant in ("runtime", "build"):
            count = len(manifest["images"][variant]["packages"])
            lines.append(f"- {variant.capitalize()}: {count} packages")
    else:
        lines.append("Package changes from the prior release:")
        lines.append("")
        for variant in ("runtime", "build"):
            delta = manifest["images"][variant]["package_delta"]
            lines.append(
                f"- {variant.capitalize()}: {len(delta['added'])} added, "
                f"{len(delta['removed'])} removed, {len(delta['updated'])} updated"
            )
    lines.extend(
        [
            "",
            "The attached manifest contains the full package inventory, package delta,",
            "artifact hashes, source revision, and exact image digests.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, default=Path("build"))
    parser.add_argument("--previous-dir", type=Path)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--runtime-digest", required=True)
    parser.add_argument("--build-digest", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--notes-output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        release_id = (args.build_dir / "release-id").read_text().strip()
        if not RELEASE_RE.fullmatch(release_id):
            raise ManifestError(f"invalid release ID: {release_id!r}")

        runtime_lock = args.build_dir / "python-3.14.runtime.lock.json"
        build_lock = args.build_dir / "python-3.14.build.lock.json"
        previous_runtime = (
            args.previous_dir / runtime_lock.name if args.previous_dir else None
        )
        previous_build = args.previous_dir / build_lock.name if args.previous_dir else None
        previous_runtime_exists = bool(previous_runtime and previous_runtime.exists())
        previous_build_exists = bool(previous_build and previous_build.exists())
        if previous_runtime_exists != previous_build_exists:
            raise ManifestError("previous release must contain both package locks")
        initial = not (previous_runtime_exists and previous_build_exists)

        manifest = {
            "schema_version": 1,
            "release_id": release_id,
            "source_revision": args.source_revision,
            "architecture": "amd64",
            "images": {
                "runtime": image_record(
                    args.image,
                    f"3.14-{release_id}",
                    args.runtime_digest,
                    runtime_lock,
                    args.build_dir / "sbom/runtime/sbom-x86_64.spdx.json",
                    args.build_dir / "reports/python-3.14.runtime.trivy.json",
                    previous_runtime,
                ),
                "build": image_record(
                    args.image,
                    f"3.14-build-{release_id}",
                    args.build_digest,
                    build_lock,
                    args.build_dir / "sbom/build/sbom-x86_64.spdx.json",
                    args.build_dir / "reports/python-3.14.build.trivy.json",
                    previous_build,
                ),
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.notes_output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        args.notes_output.write_text(render_notes(manifest, initial))
    except (ManifestError, OSError) as exc:
        print(f"release manifest failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

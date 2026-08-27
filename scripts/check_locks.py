#!/usr/bin/env python3
"""Check the runtime/build package intersection and identify the release set."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class LockError(Exception):
    pass


def load_lock(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise LockError(f"could not load {path}: {exc}") from exc
    packages = payload.get("contents", {}).get("packages")
    if not isinstance(packages, list) or not packages:
        raise LockError(f"{path}: lock contains no packages")
    return payload


def package_map(payload: dict[str, Any], path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    packages: dict[tuple[str, str], tuple[str, str]] = {}
    for item in payload["contents"]["packages"]:
        if not isinstance(item, dict):
            raise LockError(f"{path}: invalid package record")
        values = [item.get(field) for field in ("name", "architecture", "version", "checksum")]
        if not all(isinstance(value, str) and value for value in values):
            raise LockError(f"{path}: incomplete package record")
        name, architecture, version, checksum = values
        key = (architecture, name)
        if key in packages:
            raise LockError(f"{path}: duplicate package {architecture}/{name}")
        packages[key] = (version, checksum)
    return packages


def release_id(
    runtime_path: Path,
    build_path: Path,
    input_paths: tuple[Path, ...] = (),
    input_values: tuple[str, ...] = (),
) -> str:
    runtime = package_map(load_lock(runtime_path), runtime_path)
    build = package_map(load_lock(build_path), build_path)

    mismatches = [
        f"{architecture}/{name}: runtime={runtime[key]} build={build[key]}"
        for key in sorted(runtime.keys() & build.keys())
        if runtime[key] != build[key]
        for architecture, name in [key]
    ]
    if mismatches:
        raise LockError("shared package mismatch:\n  " + "\n  ".join(mismatches))

    package_set = {
        "runtime": sorted(([*key, *value] for key, value in runtime.items())),
        "build": sorted(([*key, *value] for key, value in build.items())),
        "input_files": [],
        "input_values": list(input_values),
    }
    for path in input_paths:
        try:
            contents = path.read_bytes()
        except OSError as exc:
            raise LockError(f"could not load release input {path}: {exc}") from exc
        package_set["input_files"].append(hashlib.sha256(contents).hexdigest())
    digest = hashlib.sha256(
        json.dumps(package_set, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return digest[:16]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime_lock", type=Path)
    parser.add_argument("build_lock", type=Path)
    parser.add_argument("--input", action="append", default=[], type=Path)
    parser.add_argument("--value", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        print(
            release_id(
                args.runtime_lock,
                args.build_lock,
                tuple(args.input),
                tuple(args.value),
            )
        )
    except LockError as exc:
        print(f"lock check failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

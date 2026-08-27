from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_locks import LockError, release_id  # noqa: E402


def lock(*packages: tuple[str, str, str, str]) -> dict:
    return {
        "contents": {
            "packages": [
                {
                    "name": name,
                    "architecture": architecture,
                    "version": version,
                    "checksum": checksum,
                }
                for name, architecture, version, checksum in packages
            ]
        }
    }


class LockTests(unittest.TestCase):
    def write(self, directory: Path, name: str, payload: dict) -> Path:
        path = directory / name
        path.write_text(json.dumps(payload))
        return path

    def test_shared_packages_match(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            runtime = self.write(
                directory,
                "runtime.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            build = self.write(
                directory,
                "build.json",
                lock(
                    ("compiler", "x86_64", "16.2-r1", "two"),
                    ("python", "x86_64", "3.14.7-r2", "one"),
                ),
            )
            self.assertRegex(release_id(runtime, build), r"^[0-9a-f]{16}$")

    def test_mutation_shared_version_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            runtime = self.write(
                directory,
                "runtime.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            build = self.write(
                directory,
                "build.json",
                lock(("python", "x86_64", "3.14.6-r1", "old")),
            )
            with self.assertRaisesRegex(LockError, "shared package mismatch"):
                release_id(runtime, build)

    def test_mutation_empty_lock_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            runtime = self.write(directory, "runtime.json", {"contents": {"packages": []}})
            build = self.write(
                directory,
                "build.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            with self.assertRaisesRegex(LockError, "contains no packages"):
                release_id(runtime, build)

    def test_release_input_changes_release_id(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            runtime = self.write(
                directory,
                "runtime.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            build = self.write(
                directory,
                "build.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            release_input = directory / "runtime.apko.yaml"
            release_input.write_text("packages: [python-3.14]\n")
            first = release_id(runtime, build, (release_input,))
            release_input.write_text("packages: [python-3.14, ca-certificates-bundle]\n")
            second = release_id(runtime, build, (release_input,))
            self.assertNotEqual(first, second)

    def test_missing_release_input_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            runtime = self.write(
                directory,
                "runtime.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            build = self.write(
                directory,
                "build.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            with self.assertRaisesRegex(LockError, "could not load release input"):
                release_id(runtime, build, (directory / "missing.yaml",))

    def test_release_value_changes_release_id(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            runtime = self.write(
                directory,
                "runtime.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            build = self.write(
                directory,
                "build.json",
                lock(("python", "x86_64", "3.14.7-r2", "one")),
            )
            first = release_id(runtime, build, input_values=("build-date=one",))
            second = release_id(runtime, build, input_values=("build-date=two",))
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()

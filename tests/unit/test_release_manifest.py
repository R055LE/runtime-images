from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from release_manifest import package_delta  # noqa: E402


def package(name: str, version: str, checksum: str = "checksum") -> dict[str, str]:
    return {
        "architecture": "x86_64",
        "name": name,
        "version": version,
        "checksum": checksum,
    }


class ReleaseManifestTests(unittest.TestCase):
    def test_package_delta_reports_each_change_kind(self):
        previous = [
            package("removed", "1"),
            package("same", "1"),
            package("updated", "1"),
        ]
        current = [
            package("added", "1"),
            package("same", "1"),
            package("updated", "2"),
        ]
        delta = package_delta(current, previous)
        self.assertEqual(["added"], [item["name"] for item in delta["added"]])
        self.assertEqual(["removed"], [item["name"] for item in delta["removed"]])
        self.assertEqual(["updated"], [item["name"] for item in delta["updated"]])
        self.assertEqual("1", delta["updated"][0]["previous_version"])
        self.assertEqual("2", delta["updated"][0]["version"])

    def test_initial_release_reports_all_packages_as_added(self):
        current = [package("python", "3.14")]
        delta = package_delta(current, None)
        self.assertEqual(current, delta["added"])
        self.assertEqual([], delta["removed"])
        self.assertEqual([], delta["updated"])


if __name__ == "__main__":
    unittest.main()

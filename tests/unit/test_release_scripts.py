from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class ReleaseScriptTests(unittest.TestCase):
    def test_rolling_tag_preserves_single_platform_manifest_digest(self):
        script = (REPO_ROOT / "scripts" / "promote-images.sh").read_text()
        self.assertIn("--prefer-index=false", script)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from push_digest import extract_digest  # noqa: E402

DIGEST = "sha256:3b4b1a73ee09cdeb7ca8658aa5c3406bd58385eb30a0700f9d74be64aa8e0593"


class PushDigestTests(unittest.TestCase):
    def test_extracts_digest_from_runner_output(self):
        output = (
            "The push refers to repository [ghcr.io/r055le/runtime-python]\n"
            "5808c61d0144: Pushed\n"
            f"3.14-release: digest: {DIGEST} size: 529\n"
        )
        self.assertEqual(DIGEST, extract_digest(output))

    def test_missing_digest_fails(self):
        with self.assertRaisesRegex(ValueError, "no sha256 digest"):
            extract_digest("5808c61d0144: Pushed\n")

    def test_rejects_short_digest(self):
        with self.assertRaisesRegex(ValueError, "no sha256 digest"):
            extract_digest("3.14-release: digest: sha256:1234 size: 529\n")


if __name__ == "__main__":
    unittest.main()

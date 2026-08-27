#!/usr/bin/env python3
"""Extract the content digest from Docker push output."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DIGEST_RE = re.compile(r"\bdigest:\s+(sha256:[0-9a-f]{64})\b")


def extract_digest(text: str) -> str:
    matches = DIGEST_RE.findall(text)
    if not matches:
        raise ValueError("Docker push output contains no sha256 digest")
    return matches[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    try:
        print(extract_digest(args.log.read_text()))
    except (OSError, ValueError) as exc:
        print(f"push digest parse failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

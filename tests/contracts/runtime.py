from __future__ import annotations

import json
import os
import pwd
import sqlite3
import ssl
import sys
from pathlib import Path

assert sys.version_info[:2] == (3, 14), sys.version
assert os.getuid() == 65532
assert os.getgid() == 65532
assert pwd.getpwuid(65532).pw_name == "nonroot"
assert ssl.OPENSSL_VERSION.startswith("OpenSSL ")
assert sqlite3.sqlite_version
assert Path(ssl.get_default_verify_paths().cafile or "").is_file()

for forbidden in (
    "/bin/sh",
    "/bin/bash",
    "/bin/busybox",
    "/sbin/apk",
    "/usr/bin/apk",
    "/usr/bin/cc",
    "/usr/bin/gcc",
    "/usr/bin/pip",
    "/usr/bin/pip3",
):
    assert not Path(forbidden).exists(), forbidden

print(
    json.dumps(
        {
            "gid": os.getgid(),
            "openssl": ssl.OPENSSL_VERSION,
            "python": sys.version.split()[0],
            "sqlite": sqlite3.sqlite_version,
            "uid": os.getuid(),
        },
        sort_keys=True,
    )
)

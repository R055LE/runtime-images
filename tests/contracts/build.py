from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

assert sys.version_info[:2] == (3, 14), sys.version
assert os.getuid() == 0
assert shutil.which("sh")
assert shutil.which("cc")
assert shutil.which("uv")
assert shutil.which("apk") is None
assert shutil.which("pip") is None

include = sysconfig.get_paths()["include"]
suffix = sysconfig.get_config_var("EXT_SUFFIX")
assert suffix
output = Path("/tmp") / f"native_contract{suffix}"
subprocess.run(
    [
        "cc",
        "-shared",
        "-fPIC",
        f"-I{include}",
        "/contracts/native_contract.c",
        "-o",
        str(output),
    ],
    check=True,
)
spec = importlib.util.spec_from_file_location("native_contract", output)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.answer() == 42

print(f"Python {sys.version.split()[0]} compiled and imported {output.name}")

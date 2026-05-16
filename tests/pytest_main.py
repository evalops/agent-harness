from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def main() -> int:
    test_tmp = os.environ.get("TEST_TMPDIR")
    if test_tmp:
        os.chdir(test_tmp)

    runfiles_root = Path(__file__).resolve().parents[1]
    return pytest.main(
        [
            str(runfiles_root / "tests"),
            "-c",
            str(runfiles_root / "pyproject.toml"),
            "-p",
            "no:cacheprovider",
        ]
    )


if __name__ == "__main__":
    sys.exit(main())

"""Configuration for locating external PlanarMap binaries.

This tooling is intended to live inside the koebepy repository while using
PlanarMap from an external checkout/path, so the PlanarMap source itself does
not need to be committed into koebepy.

Set either:
- PLANARMAP_BIN: full path to planarmap executable
- PLANARMAP_ROOT: path to PlanarMap root folder (expects planarmap.exe there)
"""

from __future__ import annotations

import os
from pathlib import Path


def get_planarmap_bin(default_relative: str = "../planarmap.exe") -> str:
    """Return the planarmap executable path as a string.

    Priority:
    1) PLANARMAP_BIN env var
    2) PLANARMAP_ROOT env var + /planarmap.exe
    3) provided default_relative fallback
    """

    planarmap_bin = os.environ.get("PLANARMAP_BIN")
    if planarmap_bin:
        return planarmap_bin

    planarmap_root = os.environ.get("PLANARMAP_ROOT")
    if planarmap_root:
        return str(Path(planarmap_root) / "planarmap.exe")

    return default_relative

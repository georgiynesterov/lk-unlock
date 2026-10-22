"""Tools for unlocking Xiaomi MediaTek bootloaders by patching LK images."""

import os
import sys

__version__ = "1.0"


def resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

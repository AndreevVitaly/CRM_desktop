from __future__ import annotations

import sys
from pathlib import Path


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent.parent


def get_app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    return get_app_base_dir() / "medcrm.db"


def get_resource_path(*parts: str) -> Path:
    return get_runtime_base_dir().joinpath(*parts)

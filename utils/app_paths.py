from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_DATA_DIRECTORY_NAME = "PULSAR"


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent.parent


def get_app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_app_data_dir() -> Path:
    """Возвращает пользовательский каталог для изменяемых данных PULSAR."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data).expanduser().resolve() / APP_DATA_DIRECTORY_NAME
    return Path.home().resolve() / "AppData" / "Local" / APP_DATA_DIRECTORY_NAME


def ensure_app_data_dir() -> Path:
    app_data_dir = get_app_data_dir()
    app_data_dir.mkdir(parents=True, exist_ok=True)
    return app_data_dir


def get_db_path() -> Path:
    return ensure_app_data_dir() / "medcrm.db"


def get_crash_log_path() -> Path:
    return ensure_app_data_dir() / "crash.log"


def migrate_legacy_app_data() -> list[tuple[Path, Path]]:
    """Копирует данные старой установки из каталога программы в профиль.

    Исходники намеренно сохраняются как резервная копия. Временный файл и
    os.replace не позволяют оставить частично скопированную базу после сбоя.
    """
    source_dir = get_app_base_dir()
    destination_dir = ensure_app_data_dir()
    if source_dir == destination_dir:
        return []

    migrated = []
    for file_name in ("medcrm.db", "crash.log"):
        source = source_dir / file_name
        destination = destination_dir / file_name
        if not source.is_file() or destination.exists():
            continue

        temporary = destination.with_name(f".{destination.name}.migrating")
        try:
            shutil.copy2(source, temporary)
            if temporary.stat().st_size != source.stat().st_size:
                raise OSError(f"Не удалось полностью скопировать {source}")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        migrated.append((source, destination))
    return migrated


def get_resource_path(*parts: str) -> Path:
    return get_runtime_base_dir().joinpath(*parts)

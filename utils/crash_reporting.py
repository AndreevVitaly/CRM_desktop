from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from utils.app_paths import APP_DATA_DIRECTORY_NAME, get_crash_log_path


@dataclass(frozen=True)
class CrashReportResult:
    path: Path | None
    errors: tuple[str, ...]


def _fallback_crash_log_paths() -> tuple[Path, ...]:
    return (
        Path(tempfile.gettempdir()).resolve()
        / APP_DATA_DIRECTORY_NAME
        / "crash.log",
        Path.home().resolve() / "PULSAR_crash.log",
    )


def _build_report(error_message: str, occurred_at: datetime) -> str:
    try:
        working_directory = str(Path.cwd())
    except Exception as exc:
        working_directory = f"недоступен ({exc})"
    return (
        "\n"
        + "=" * 80
        + "\n"
        + occurred_at.strftime("%Y-%m-%d %H:%M:%S")
        + "\n"
        + f"Executable: {sys.executable}\n"
        + f"Python: {sys.version}\n"
        + f"Working directory: {working_directory}\n\n"
        + error_message.rstrip()
        + "\n"
    )


def write_crash_report(
    error_message: str,
    *,
    occurred_at: datetime | None = None,
    primary_path: Path | None = None,
    fallback_paths: Iterable[Path] | None = None,
) -> CrashReportResult:
    """Сохраняет отчёт, последовательно пробуя независимые каталоги."""
    errors: list[str] = []
    candidates: list[Path] = []

    if primary_path is not None:
        candidates.append(Path(primary_path))
    else:
        try:
            candidates.append(get_crash_log_path())
        except Exception as exc:
            errors.append(f"Основной каталог журнала: {exc}")

    try:
        fallbacks = (
            fallback_paths if fallback_paths is not None else _fallback_crash_log_paths()
        )
        candidates.extend(Path(path) for path in fallbacks)
    except Exception as exc:
        errors.append(f"Резервные каталоги журнала: {exc}")
    report = _build_report(error_message, occurred_at or datetime.now())

    seen: set[Path] = set()
    for path in candidates:
        try:
            resolved = path.expanduser().resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with resolved.open("a", encoding="utf-8") as log_file:
                log_file.write(report)
                log_file.flush()
                os.fsync(log_file.fileno())
            return CrashReportResult(resolved, tuple(errors))
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    return CrashReportResult(None, tuple(errors))

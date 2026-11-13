from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path


def _quote_pragma(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def has_sqlite_header(db_path: str | Path) -> bool:
    path = Path(db_path)
    if not path.exists():
        return False
    with path.open("rb") as fh:
        return fh.read(16) == b"SQLite format 3\x00"


def is_sqlcipher_available() -> bool:
    try:
        import sqlcipher3  # noqa: F401
    except ImportError:
        return False
    return True


def is_encrypted_database(db_path: str | Path, password: str) -> bool:
    import sqlcipher3

    path = Path(db_path)
    if not path.exists():
        return False
    with path.open("rb") as fh:
        if fh.read(16) == b"SQLite format 3\x00":
            return False

    conn = sqlcipher3.connect(str(path))
    try:
        conn.execute(f"PRAGMA key = {_quote_pragma(password)}")
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def is_plain_sqlite_database(db_path: str | Path) -> bool:
    path = Path(db_path)
    if not path.exists():
        return False
    if not has_sqlite_header(path):
        return False

    conn = sqlite3.connect(str(path))
    try:
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def _fsync_file(path: Path):
    # На Windows FlushFileBuffers требует дескриптор, открытый с правом записи.
    with path.open("r+b") as file_handle:
        os.fsync(file_handle.fileno())


def _unique_backup_path(path: Path, stamp: str) -> Path:
    candidate = path.with_name(f"{path.stem}.plain_backup_{stamp}{path.suffix}")
    sequence = 1
    while candidate.exists():
        candidate = path.with_name(
            f"{path.stem}.plain_backup_{stamp}_{sequence}{path.suffix}"
        )
        sequence += 1
    return candidate


def _table_row_counts(connection) -> dict[str, int]:
    table_names = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    counts = {}
    for table_name in table_names:
        quoted_name = '"' + table_name.replace('"', '""') + '"'
        counts[table_name] = connection.execute(
            f"SELECT COUNT(*) FROM {quoted_name}"
        ).fetchone()[0]
    return counts


def _validate_encrypted_copy(plain_connection, encrypted_path: Path, password: str):
    import sqlcipher3

    source_integrity = plain_connection.execute("PRAGMA integrity_check").fetchone()[0]
    if source_integrity != "ok":
        raise ValueError(f"Исходная база повреждена: {source_integrity}")

    encrypted_connection = sqlcipher3.connect(str(encrypted_path))
    try:
        encrypted_connection.execute(f"PRAGMA key = {_quote_pragma(password)}")
        encrypted_integrity = encrypted_connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        if encrypted_integrity != "ok":
            raise RuntimeError(
                f"Проверка зашифрованной копии не пройдена: {encrypted_integrity}"
            )
        source_counts = _table_row_counts(plain_connection)
        encrypted_counts = _table_row_counts(encrypted_connection)
        if encrypted_counts != source_counts:
            raise RuntimeError(
                "Зашифрованная копия не совпадает с исходной базой по составу "
                "таблиц или количеству записей"
            )
    finally:
        encrypted_connection.close()


def _create_consistent_backup(plain_connection, backup_path: Path):
    backup_connection = sqlite3.connect(str(backup_path))
    try:
        plain_connection.backup(backup_connection)
        backup_connection.commit()
        integrity = backup_connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Резервная копия не прошла проверку: {integrity}")
    except Exception:
        backup_connection.close()
        backup_path.unlink(missing_ok=True)
        raise
    finally:
        try:
            backup_connection.close()
        except Exception:
            pass
    _fsync_file(backup_path)


def _install_encrypted_database(encrypted_path: Path, destination_path: Path):
    """Атомарно заменяет БД; при ошибке исходный файл остаётся на месте."""
    _fsync_file(encrypted_path)
    os.replace(encrypted_path, destination_path)


def encrypt_existing_database(db_path: str | Path, password: str) -> Path:
    import sqlcipher3

    path = Path(db_path)
    if not path.exists():
        return path
    if not password:
        raise ValueError("Пароль базы не может быть пустым")
    if is_encrypted_database(path, password):
        return path
    if not is_plain_sqlite_database(path):
        raise ValueError("База не открывается как SQLite. Возможно, пароль неверный.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = _unique_backup_path(path, stamp)
    encrypted_path = path.with_name(f"{path.stem}.encrypted_tmp_{stamp}{path.suffix}")
    encrypted_path.unlink(missing_ok=True)

    plain_conn = sqlite3.connect(str(path))
    encrypted_conn = sqlcipher3.connect(str(encrypted_path))
    try:
        encrypted_conn.execute(f"PRAGMA key = {_quote_pragma(password)}")
        encrypted_conn.executescript("\n".join(plain_conn.iterdump()))
        encrypted_conn.commit()
        encrypted_conn.close()
        encrypted_conn = None

        _validate_encrypted_copy(plain_conn, encrypted_path, password)
        _create_consistent_backup(plain_conn, backup_path)
        plain_conn.close()
        plain_conn = None

        # os.replace выполняется атомарно в одном каталоге. При его ошибке
        # исходная medcrm.db продолжает находиться по прежнему пути.
        _install_encrypted_database(encrypted_path, path)
    finally:
        if plain_conn is not None:
            plain_conn.close()
        if encrypted_conn is not None:
            encrypted_conn.close()
        encrypted_path.unlink(missing_ok=True)

    return backup_path


def rekey_open_database(database, current_password: str, new_password: str):
    if not new_password:
        raise ValueError("Новый пароль не может быть пустым")
    if not is_encrypted_database(database.db_path, current_password):
        raise ValueError("Текущий пароль базы указан неверно")

    database.execute(f"PRAGMA rekey = {_quote_pragma(new_password)}")
    database.commit()
    database.password = new_password

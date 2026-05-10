from __future__ import annotations

import shutil
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
    backup_path = path.with_name(f"{path.stem}.plain_backup_{stamp}{path.suffix}")
    encrypted_path = path.with_name(f"{path.stem}.encrypted_tmp_{stamp}{path.suffix}")

    plain_conn = sqlite3.connect(str(path))
    encrypted_conn = sqlcipher3.connect(str(encrypted_path))
    try:
        encrypted_conn.execute(f"PRAGMA key = {_quote_pragma(password)}")
        encrypted_conn.executescript("\n".join(plain_conn.iterdump()))
        encrypted_conn.commit()
    except Exception:
        encrypted_conn.close()
        plain_conn.close()
        encrypted_path.unlink(missing_ok=True)
        raise
    finally:
        plain_conn.close()
        encrypted_conn.close()

    shutil.move(str(path), str(backup_path))
    shutil.move(str(encrypted_path), str(path))
    return backup_path


def rekey_open_database(database, current_password: str, new_password: str):
    if not new_password:
        raise ValueError("Новый пароль не может быть пустым")
    if not is_encrypted_database(database.db_path, current_password):
        raise ValueError("Текущий пароль базы указан неверно")

    database.execute(f"PRAGMA rekey = {_quote_pragma(new_password)}")
    database.commit()
    database.password = new_password

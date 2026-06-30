from __future__ import annotations

import json
import base64
import os
import uuid as uuid_lib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from models.db_models import Patient, User, db, hash_password

PACKAGE_VERSION = 1
MANIFEST_NAME = "manifest.json"
DATA_NAME = "data.json"
SECURE_CONTAINER_NAME = "pulsar_secure_package.json"
KDF_ITERATIONS = 390000

APPLICATION_TABLE_IMPORT_ORDER = (
    "departments",
    "users",
    "facilities",
    "patients",
    "encounter_groups",
    "documents",
    "treatment_plan_items",
    "encounters",
    "encounter_informants",
    "notes",
    "diagnoses",
    "prescriptions",
    "attachments",
    "km_records",
    "patient_interactions",
    "events",
    "patient_meeting_schedule",
    "event_report_positions",
    "stats_cache",
    "import_logs",
)

CORE_SYNC_TABLES = (
    "patients",
    "encounter_groups",
    "encounters",
    "documents",
    "treatment_plan_items",
    "km_records",
    "patient_meeting_schedule",
    "events",
    "event_report_positions",
)

NATURAL_KEY_SYNC_TABLES = (
    "departments",
    "attachments",
    "patient_interactions",
)

class CryptoUnavailableError(RuntimeError):
    pass


def _crypto_modules():
    try:
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise CryptoUnavailableError(
            "Для защищенных пакетов установите зависимость cryptography: pip install -r requirements.txt"
        ) from exc
    return Fernet, InvalidToken, hashes, PBKDF2HMAC


def _derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise ValueError("Для защищенного пакета нужен пароль")
    _, _, hashes, PBKDF2HMAC = _crypto_modules()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _encrypt_payload(payload: dict[str, Any], password: str) -> dict[str, Any]:
    Fernet, _, _, _ = _crypto_modules()
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    )
    return {
        "app": "PULSAR",
        "container_version": 1,
        "encrypted": True,
        "kdf": "PBKDF2HMAC-SHA256",
        "iterations": KDF_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "cipher": "Fernet",
        "token": token.decode("ascii"),
    }


def _decrypt_payload(container: dict[str, Any], password: str | None) -> dict[str, Any]:
    if not password:
        raise ValueError("Этот пакет защищен паролем")
    Fernet, InvalidToken, _, _ = _crypto_modules()
    salt = base64.b64decode(container["salt"])
    key = _derive_key(password, salt)
    try:
        decrypted = Fernet(key).decrypt(container["token"].encode("ascii"))
    except InvalidToken as exc:
        raise ValueError("Неверный пароль или пакет был изменен") from exc
    return json.loads(decrypted.decode("utf-8"))


def _rows(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in db.fetchall(query, params)]


def _table_columns(table_name: str) -> list[str]:
    return [row["name"] for row in db.fetchall(f"PRAGMA table_info({table_name})")]


def _application_table_names() -> list[str]:
    existing = [
        row["name"]
        for row in db.fetchall(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
    ]
    existing_set = set(existing)
    ordered = [table for table in APPLICATION_TABLE_IMPORT_ORDER if table in existing_set]
    ordered.extend(table for table in existing if table not in set(ordered))
    return ordered


def _order_by_clause(table_name: str) -> str:
    columns = _table_columns(table_name)
    if "id" in columns:
        return " ORDER BY id"
    if table_name == "departments" and "code" in columns:
        return " ORDER BY code"
    return ""


def _collect_full_database_data() -> dict[str, list[dict[str, Any]]]:
    return {
        table_name: _rows(f"SELECT * FROM {table_name}{_order_by_clause(table_name)}")
        for table_name in _application_table_names()
    }


def _collect_selected_patient_data(patient_ids: set[int]) -> dict[str, list[dict[str, Any]]]:
    table_names = set(_application_table_names())
    selected_ids = {int(patient_id) for patient_id in patient_ids if patient_id is not None}
    data = {
        table_name: []
        for table_name in APPLICATION_TABLE_IMPORT_ORDER
        if table_name in table_names
    }
    if not selected_ids:
        return data

    patients = _select_by_ids("patients", selected_ids)
    actual_patient_ids = {row["id"] for row in patients if row.get("id") is not None}
    encounters = _select_by_column_ids("encounters", "patient_id", actual_patient_ids)
    documents = _select_by_column_ids("documents", "patient_id", actual_patient_ids)
    plan_items = _select_by_column_ids("treatment_plan_items", "patient_id", actual_patient_ids)
    patient_interactions = _select_by_column_ids("patient_interactions", "patient_id", actual_patient_ids)
    meeting_schedule = _select_by_column_ids("patient_meeting_schedule", "patient_id", actual_patient_ids)

    encounter_ids = {row["id"] for row in encounters if row.get("id") is not None}
    document_ids = {row["id"] for row in documents if row.get("id") is not None}
    group_ids = {row["group_id"] for row in encounters if row.get("group_id") is not None}

    encounter_groups = _select_by_ids("encounter_groups", group_ids)
    encounter_informants = _select_by_column_ids("encounter_informants", "encounter_id", encounter_ids)
    notes = _select_by_column_ids("notes", "encounter_id", encounter_ids)
    diagnoses = _select_by_column_ids("diagnoses", "encounter_id", encounter_ids)
    prescriptions = _select_by_column_ids("prescriptions", "encounter_id", encounter_ids)
    attachments = _select_by_column_ids("attachments", "encounter_id", encounter_ids)

    km_records = []
    if "km_records" in table_names:
        conditions = []
        params = []
        if encounter_ids:
            conditions.append("encounter_id IN (" + ",".join("?" for _ in encounter_ids) + ")")
            params.extend(sorted(encounter_ids))
        if document_ids:
            conditions.append("document_id IN (" + ",".join("?" for _ in document_ids) + ")")
            params.extend(sorted(document_ids))

        personal_numbers = {
            str(row.get("personal_number") or "").strip().casefold()
            for row in patients
            if str(row.get("personal_number") or "").strip()
        }
        callsigns = {
            str(row.get("callsign") or "").strip().casefold()
            for row in patients
            if str(row.get("callsign") or "").strip()
        }
        document_numbers = {
            str(row.get("doc_number") or "").strip().casefold()
            for row in documents
            if str(row.get("doc_number") or "").strip()
        }
        if personal_numbers:
            conditions.append(
                "LOWER(TRIM(COALESCE(personal_number, ''))) IN ("
                + ",".join("?" for _ in personal_numbers)
                + ")"
            )
            params.extend(sorted(personal_numbers))
        if callsigns:
            conditions.append(
                "LOWER(TRIM(COALESCE(callsign, ''))) IN ("
                + ",".join("?" for _ in callsigns)
                + ")"
            )
            params.extend(sorted(callsigns))
        if document_numbers:
            conditions.append(
                "LOWER(TRIM(COALESCE(document_number, ''))) IN ("
                + ",".join("?" for _ in document_numbers)
                + ")"
            )
            params.extend(sorted(document_numbers))

        if conditions:
            km_records = _rows(
                "SELECT * FROM km_records WHERE " + " OR ".join(conditions) + " ORDER BY id",
                tuple(params),
            )

        def _norm(value: Any) -> str:
            return str(value or "").strip().casefold()

        seen_km_ids = {row.get("id") for row in km_records}
        for row in _rows("SELECT * FROM km_records ORDER BY id"):
            if row.get("id") in seen_km_ids:
                continue
            if (
                _norm(row.get("personal_number")) in personal_numbers
                or _norm(row.get("callsign")) in callsigns
                or _norm(row.get("document_number")) in document_numbers
            ):
                km_records.append(row)
                seen_km_ids.add(row.get("id"))

    events = []
    event_report_positions = []
    if "events" in table_names:
        event_ids: set[int] = set()
        if document_ids:
            placeholders = ",".join("?" for _ in document_ids)
            event_rows = _rows(
                f"SELECT * FROM events WHERE meeting_document_id IN ({placeholders}) ORDER BY id",
                tuple(sorted(document_ids)),
            )
            events.extend(event_rows)
            event_ids.update(row["id"] for row in event_rows if row.get("id") is not None)
            position_rows = _rows(
                f"SELECT * FROM event_report_positions WHERE document_id IN ({placeholders}) ORDER BY id",
                tuple(sorted(document_ids)),
            )
            event_report_positions.extend(position_rows)
            event_ids.update(row["event_id"] for row in position_rows if row.get("event_id") is not None)
        if event_ids:
            known_event_ids = {row["id"] for row in events if row.get("id") is not None}
            missing_event_ids = event_ids - known_event_ids
            events.extend(_select_by_ids("events", missing_event_ids))
            all_position_rows = _select_by_column_ids("event_report_positions", "event_id", event_ids)
            seen_position_ids = {row.get("id") for row in event_report_positions}
            event_report_positions.extend(
                row for row in all_position_rows if row.get("id") not in seen_position_ids
            )

    facility_ids = {row["facility_id"] for row in patients if row.get("facility_id") is not None}
    user_ids = set()
    user_ids.update(row["doctor_id"] for row in patients if row.get("doctor_id") is not None)
    user_ids.update(row["doctor_id"] for row in encounters if row.get("doctor_id") is not None)
    user_ids.update(row["author_id"] for row in documents if row.get("author_id") is not None)
    user_ids.update(row["created_by_id"] for row in encounter_groups if row.get("created_by_id") is not None)
    user_ids.update(row["author_id"] for row in notes if row.get("author_id") is not None)
    user_ids.update(row["user_id"] for row in patient_interactions if row.get("user_id") is not None)
    user_ids.update(row["doctor_id"] for row in meeting_schedule if row.get("doctor_id") is not None)
    user_ids.update(row["created_by_id"] for row in meeting_schedule if row.get("created_by_id") is not None)
    user_ids.update(row["responsible_id"] for row in events if row.get("responsible_id") is not None)
    user_ids.update(row["created_by_id"] for row in events if row.get("created_by_id") is not None)
    user_ids.update(row["created_by_id"] for row in event_report_positions if row.get("created_by_id") is not None)

    data.update(
        {
            "departments": _rows("SELECT * FROM departments ORDER BY code") if "departments" in table_names else [],
            "users": _public_users(user_ids),
            "facilities": _select_by_ids("facilities", facility_ids),
            "patients": patients,
            "encounter_groups": encounter_groups,
            "documents": documents,
            "treatment_plan_items": plan_items,
            "encounters": encounters,
            "encounter_informants": encounter_informants,
            "notes": notes,
            "diagnoses": diagnoses,
            "prescriptions": prescriptions,
            "attachments": attachments,
            "km_records": km_records,
            "patient_interactions": patient_interactions,
            "events": events,
            "patient_meeting_schedule": meeting_schedule,
            "event_report_positions": event_report_positions,
        }
    )
    return data

def _insert_or_replace_rows(table_name: str, rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = _empty_import_summary()
    table_columns = _table_columns(table_name)
    if not table_columns:
        summary["skipped_unmapped_reference"] += len(rows)
        return summary

    for row in rows:
        columns = [column for column in table_columns if column in row]
        if not columns:
            summary["skipped_unmapped_reference"] += 1
            continue
        db.execute(
            f"INSERT OR REPLACE INTO {table_name} ("
            + ", ".join(columns)
            + ") VALUES ("
            + ", ".join("?" for _ in columns)
            + ")",
            tuple(row.get(column) for column in columns),
        )
        summary["updated"] += 1
    return summary

def _select_by_ids(table_name: str, ids: set[int]) -> list[dict[str, Any]]:
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    return _rows(
        f"SELECT * FROM {table_name} WHERE id IN ({placeholders}) ORDER BY id",
        tuple(sorted(ids)),
    )


def _select_by_column_ids(
    table_name: str, column_name: str, ids: set[int]
) -> list[dict[str, Any]]:
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    return _rows(
        f"SELECT * FROM {table_name} WHERE {column_name} IN ({placeholders}) ORDER BY id",
        tuple(sorted(ids)),
    )


def _public_users(user_ids: set[int]) -> list[dict[str, Any]]:
    users = _select_by_ids("users", user_ids)
    for user in users:
        user.pop("password_hash", None)
    return users


def _patient_scope_label(user: User) -> str:
    if user.role == User.ROLE_DOCTOR:
        return "doctor"
    if user.role == User.ROLE_LEAD:
        return "department"
    if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
        return "all"
    return "none"


def _collect_package_data(
    user: User, patient_ids: set[int] | None = None
) -> dict[str, Any]:
    if patient_ids is not None:
        return _collect_selected_patient_data(patient_ids)
    return _collect_full_database_data()


def build_export_filename(user: User) -> str:
    safe_username = "".join(ch for ch in user.username if ch.isalnum() or ch in ("-", "_"))
    if not safe_username:
        safe_username = "user"
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"pulsar_export_{safe_username}_{stamp}.pulsarzip"


def export_sync_package(
    user: User,
    file_path: str | Path,
    password: str | None = None,
    patient_ids: set[int] | list[int] | tuple[int, ...] | None = None,
) -> dict[str, Any]:
    path = Path(file_path)
    if path.suffix.lower() != ".pulsarzip":
        path = path.with_suffix(".pulsarzip")

    selected_patient_ids = set(patient_ids) if patient_ids is not None else None
    data = _collect_package_data(user, selected_patient_ids)
    counts = {key: len(value) for key, value in data.items()}
    exported_at = datetime.now().isoformat(timespec="seconds")
    manifest = {
        "app": "PULSAR",
        "package_version": PACKAGE_VERSION,
        "encrypted": True,
        "exported_at": exported_at,
        "scope": _patient_scope_label(user),
        "data_scope": "selected_patients" if selected_patient_ids is not None else "full_workspace",
        "exported_by": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
        },
        "counts": counts,
        "schema": {
            table_name: _table_columns(table_name)
            for table_name in data.keys()
        },
    }

    payload = {"manifest": manifest, "data": data}
    secure_container = _encrypt_payload(payload, password or "")
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            SECURE_CONTAINER_NAME,
            json.dumps(secure_container, ensure_ascii=False, indent=2),
        )

    return {"path": str(path), "manifest": manifest}


def inspect_sync_package(
    file_path: str | Path, password: str | None = None
) -> dict[str, Any]:
    manifest, payload = _read_package(file_path, password)

    data = payload.get("data", {})
    counts = {key: len(value) for key, value in data.items() if isinstance(value, list)}
    return {"manifest": manifest, "counts": counts}


def _read_package(
    file_path: str | Path, password: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(file_path)
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        if SECURE_CONTAINER_NAME in names:
            container = json.loads(
                archive.read(SECURE_CONTAINER_NAME).decode("utf-8")
            )
            payload = _decrypt_payload(container, password)
            manifest = payload.get("manifest", {})
        elif MANIFEST_NAME in names and DATA_NAME in names:
            manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
            payload = json.loads(archive.read(DATA_NAME).decode("utf-8"))
            manifest["encrypted"] = False
        else:
            raise ValueError("Файл не похож на пакет обмена PULSAR")

    if manifest.get("app") != "PULSAR":
        raise ValueError("Пакет создан не приложением PULSAR")
    if manifest.get("package_version") != PACKAGE_VERSION:
        raise ValueError("Версия пакета пока не поддерживается")
    return manifest, payload


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _find_event_by_natural_key(event: dict[str, Any]):
    return db.fetchone(
        """
        SELECT id FROM events
        WHERE title = ?
          AND COALESCE(event_date, '') = COALESCE(?, '')
          AND COALESCE(event_time, '') = COALESCE(?, '')
          AND COALESCE(department, '') = COALESCE(?, '')
          AND COALESCE(created_at, '') = COALESCE(?, '')
        LIMIT 1
        """,
        (
            event.get("title") or "",
            event.get("event_date"),
            event.get("event_time"),
            event.get("department") or "",
            event.get("created_at"),
        ),
    )

def preview_sync_import(
    file_path: str | Path, password: str | None = None
) -> dict[str, Any]:
    manifest, payload = _read_package(file_path, password)
    data = payload.get("data", {})
    preview = {}
    for table_name, incoming_rows in data.items():
        if not isinstance(incoming_rows, list):
            continue
        preview[table_name] = {
            "incoming": len(incoming_rows),
            "without_uuid": sum(1 for row in incoming_rows if not row.get("uuid")),
            "new": 0,
            "package_newer": 0,
            "local_newer": 0,
            "same_or_unknown": len(incoming_rows),
        }
    return {"manifest": manifest, "preview": preview}

def _user_id_map(package_users: list[dict[str, Any]]) -> dict[int, int | None]:
    result = {}
    for package_user in package_users:
        remote_id = package_user.get("id")
        username = package_user.get("username")
        if remote_id is None:
            continue
        local_user = None
        if username:
            local_user = db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
        result[remote_id] = local_user["id"] if local_user else None
    return result


def _facility_id_map(package_facilities: list[dict[str, Any]]) -> dict[int, int | None]:
    result = {}
    for facility in package_facilities:
        remote_id = facility.get("id")
        name = facility.get("name")
        if remote_id is None:
            continue
        local_facility = None
        if name:
            local_facility = db.fetchone("SELECT id FROM facilities WHERE name = ?", (name,))
        result[remote_id] = local_facility["id"] if local_facility else None
    return result


def _prepare_patient_row(
    row: dict[str, Any],
    user_map: dict[int, int | None],
    facility_map: dict[int, int | None],
) -> dict[str, Any]:
    prepared = dict(row)
    doctor_id = prepared.get("doctor_id")
    facility_id = prepared.get("facility_id")
    if doctor_id is not None:
        prepared["doctor_id"] = user_map.get(doctor_id)
    if facility_id is not None:
        prepared["facility_id"] = facility_map.get(facility_id)
    return prepared


def apply_patient_import(
    file_path: str | Path, current_user: User, password: str | None = None
) -> dict[str, Any]:
    if current_user.role not in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
        raise PermissionError("Импорт доступен только ADMIN, REG и LEAD")

    manifest, payload = _read_package(file_path, password)
    data = payload.get("data", {})
    incoming_patients = data.get("patients", [])
    patient_columns = set(_table_columns("patients"))
    insert_columns = [
        column
        for column in _table_columns("patients")
        if column != "id"
    ]
    writable_columns = [column for column in insert_columns if column != "uuid"]

    user_map = _user_id_map(data.get("users", []))
    facility_map = _facility_id_map(data.get("facilities", []))
    summary = {
        "new": 0,
        "updated": 0,
        "skipped_local_newer": 0,
        "skipped_same_or_unknown": 0,
        "skipped_without_uuid": 0,
        "skipped_unmapped_doctor": 0,
    }

    conn = db.connect()
    try:
        for incoming in incoming_patients:
            if not incoming.get("uuid"):
                summary["skipped_without_uuid"] += 1
                continue

            prepared = _prepare_patient_row(incoming, user_map, facility_map)
            if incoming.get("doctor_id") is not None and prepared.get("doctor_id") is None:
                summary["skipped_unmapped_doctor"] += 1
                continue

            local = db.fetchone(
                "SELECT id, updated_at FROM patients WHERE uuid = ?",
                (prepared["uuid"],),
            )
            if local:
                incoming_ts = _parse_timestamp(prepared.get("updated_at"))
                local_ts = _parse_timestamp(local["updated_at"])
                if incoming_ts and local_ts and incoming_ts > local_ts:
                    set_columns = [
                        column
                        for column in writable_columns
                        if column in patient_columns and column in prepared
                    ]
                    values = [prepared.get(column) for column in set_columns]
                    values.append(local["id"])
                    db.execute(
                        "UPDATE patients SET "
                        + ", ".join(f"{column} = ?" for column in set_columns)
                        + " WHERE id = ?",
                        tuple(values),
                    )
                    summary["updated"] += 1
                elif local_ts and incoming_ts and local_ts > incoming_ts:
                    summary["skipped_local_newer"] += 1
                else:
                    summary["skipped_same_or_unknown"] += 1
                continue

            columns = [
                column
                for column in insert_columns
                if column in patient_columns and column in prepared
            ]
            db.execute(
                "INSERT INTO patients ("
                + ", ".join(columns)
                + ") VALUES ("
                + ", ".join("?" for _ in columns)
                + ")",
                tuple(prepared.get(column) for column in columns),
            )
            summary["new"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return {"manifest": manifest, "summary": summary}


def _empty_import_summary() -> dict[str, int]:
    return {
        "new": 0,
        "updated": 0,
        "skipped_local_newer": 0,
        "skipped_same_or_unknown": 0,
        "skipped_without_uuid": 0,
        "skipped_unmapped_reference": 0,
    }


def _apply_users(package_users: list[dict[str, Any]]) -> dict[str, int]:
    summary = _empty_import_summary()
    for package_user in package_users:
        username = (package_user.get("username") or "").strip()
        if not username:
            summary["skipped_unmapped_reference"] += 1
            continue
        existing = db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            summary["skipped_same_or_unknown"] += 1
            continue
        db.execute(
            """
            INSERT INTO users
            (username, first_name, last_name, middle_name, email, password_hash, role, department, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                username,
                package_user.get("first_name", ""),
                package_user.get("last_name", ""),
                package_user.get("middle_name", ""),
                package_user.get("email", ""),
                hash_password(str(uuid_lib.uuid4())),
                package_user.get("role", User.ROLE_DOCTOR),
                package_user.get("department"),
            ),
        )
        summary["new"] += 1
    return summary


def _apply_facilities(package_facilities: list[dict[str, Any]]) -> dict[str, int]:
    summary = _empty_import_summary()
    for facility in package_facilities:
        name = (facility.get("name") or "").strip()
        if not name:
            summary["skipped_unmapped_reference"] += 1
            continue
        existing = db.fetchone("SELECT id FROM facilities WHERE name = ?", (name,))
        if existing:
            summary["skipped_same_or_unknown"] += 1
            continue
        db.execute(
            "INSERT INTO facilities (name, type, address) VALUES (?, ?, ?)",
            (
                name,
                facility.get("type") or "hospital",
                facility.get("address") or "",
            ),
        )
        summary["new"] += 1
    return summary


def _remote_to_local_id_map(table_name: str, incoming_rows: list[dict[str, Any]]) -> dict[int, int]:
    result = {}
    for row in incoming_rows:
        remote_id = row.get("id")
        row_uuid = row.get("uuid")
        if remote_id is None or not row_uuid:
            continue
        local = db.fetchone(f"SELECT id FROM {table_name} WHERE uuid = ?", (row_uuid,))
        if local:
            result[remote_id] = local["id"]
    return result


def _insert_or_update_by_uuid(
    table_name: str,
    prepared: dict[str, Any],
    columns: list[str],
    summary: dict[str, int],
):
    if not prepared.get("uuid"):
        summary["skipped_without_uuid"] += 1
        return

    local = db.fetchone(
        f"SELECT id, updated_at FROM {table_name} WHERE uuid = ?",
        (prepared["uuid"],),
    )
    insert_columns = [column for column in columns if column != "id"]
    writable_columns = [
        column
        for column in insert_columns
        if column != "uuid" and column in prepared
    ]

    if local:
        incoming_ts = _parse_timestamp(prepared.get("updated_at"))
        local_ts = _parse_timestamp(local["updated_at"])
        if incoming_ts and local_ts and incoming_ts > local_ts:
            values = [prepared.get(column) for column in writable_columns]
            values.append(local["id"])
            db.execute(
                f"UPDATE {table_name} SET "
                + ", ".join(f"{column} = ?" for column in writable_columns)
                + " WHERE id = ?",
                tuple(values),
            )
            summary["updated"] += 1
        elif local_ts and incoming_ts and local_ts > incoming_ts:
            summary["skipped_local_newer"] += 1
        else:
            summary["skipped_same_or_unknown"] += 1
        return

    columns_to_insert = [
        column for column in insert_columns if column in prepared
    ]
    db.execute(
        f"INSERT INTO {table_name} ("
        + ", ".join(columns_to_insert)
        + ") VALUES ("
        + ", ".join("?" for _ in columns_to_insert)
        + ")",
        tuple(prepared.get(column) for column in columns_to_insert),
    )
    summary["new"] += 1


def _apply_documents(
    documents: list[dict[str, Any]],
    patient_map: dict[int, int],
    encounter_map: dict[int, int],
    user_map: dict[int, int | None],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("documents")
    for row in documents:
        prepared = dict(row)
        patient_id = prepared.get("patient_id")
        author_id = prepared.get("author_id")
        if patient_id not in patient_map or author_id not in user_map or user_map[author_id] is None:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["patient_id"] = patient_map[patient_id]
        prepared["author_id"] = user_map[author_id]
        remote_encounter_id = prepared.get("encounter_id")
        prepared["encounter_id"] = encounter_map.get(remote_encounter_id)
        _insert_or_update_by_uuid("documents", prepared, columns, summary)
    return summary


def _apply_treatment_plan_items(
    plan_items: list[dict[str, Any]],
    patient_map: dict[int, int],
    document_map: dict[int, int],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("treatment_plan_items")
    for row in plan_items:
        prepared = dict(row)
        patient_id = prepared.get("patient_id")
        if patient_id not in patient_map:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["patient_id"] = patient_map[patient_id]
        remote_doc_id = prepared.get("plan_document_id")
        prepared["plan_document_id"] = document_map.get(remote_doc_id)
        _insert_or_update_by_uuid("treatment_plan_items", prepared, columns, summary)
    return summary


def _apply_encounters(
    encounters: list[dict[str, Any]],
    patient_map: dict[int, int],
    user_map: dict[int, int | None],
    document_map: dict[int, int],
    plan_item_map: dict[int, int],
    group_map: dict[int, int],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("encounters")
    for row in encounters:
        prepared = dict(row)
        patient_id = prepared.get("patient_id")
        doctor_id = prepared.get("doctor_id")
        if patient_id not in patient_map or doctor_id not in user_map or user_map[doctor_id] is None:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["patient_id"] = patient_map[patient_id]
        prepared["doctor_id"] = user_map[doctor_id]
        prepared["document_id"] = document_map.get(prepared.get("document_id"))
        prepared["treatment_plan_item_id"] = plan_item_map.get(
            prepared.get("treatment_plan_item_id")
        )
        prepared["group_id"] = group_map.get(prepared.get("group_id"))
        _insert_or_update_by_uuid("encounters", prepared, columns, summary)
    return summary


def _apply_encounter_groups(
    groups: list[dict[str, Any]],
    user_map: dict[int, int | None],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("encounter_groups")
    for row in groups:
        prepared = dict(row)
        created_by_id = prepared.get("created_by_id")
        if created_by_id is not None:
            prepared["created_by_id"] = user_map.get(created_by_id)
        _insert_or_update_by_uuid("encounter_groups", prepared, columns, summary)
    return summary


def _apply_km_records(
    km_records: list[dict[str, Any]],
    encounter_map: dict[int, int],
    document_map: dict[int, int],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("km_records")
    for row in km_records:
        prepared = dict(row)
        remote_encounter_id = prepared.get("encounter_id")
        remote_document_id = prepared.get("document_id")
        if remote_encounter_id is not None:
            prepared["encounter_id"] = encounter_map.get(remote_encounter_id)
        if remote_document_id is not None:
            prepared["document_id"] = document_map.get(remote_document_id)
        if remote_encounter_id is not None and prepared.get("encounter_id") is None:
            summary["skipped_unmapped_reference"] += 1
            continue
        if remote_document_id is not None and prepared.get("document_id") is None:
            summary["skipped_unmapped_reference"] += 1
            continue
        _insert_or_update_by_uuid("km_records", prepared, columns, summary)
    return summary


def _apply_departments(departments: list[dict[str, Any]]) -> dict[str, int]:
    summary = _empty_import_summary()
    for row in departments:
        code = (row.get("code") or "").strip()
        name = (row.get("name") or "").strip()
        if not code or not name:
            summary["skipped_unmapped_reference"] += 1
            continue
        existing = db.fetchone("SELECT code FROM departments WHERE code = ?", (code,))
        if existing:
            db.execute(
                "UPDATE departments SET name = ?, is_active = ? WHERE code = ?",
                (name, row.get("is_active", 1), code),
            )
            summary["updated"] += 1
        else:
            db.execute(
                "INSERT INTO departments (code, name, is_active) VALUES (?, ?, ?)",
                (code, name, row.get("is_active", 1)),
            )
            summary["new"] += 1
    return summary


def _apply_patient_meeting_schedule(
    schedule_rows: list[dict[str, Any]],
    patient_map: dict[int, int],
    user_map: dict[int, int | None],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("patient_meeting_schedule")
    for row in schedule_rows:
        prepared = dict(row)
        patient_id = prepared.get("patient_id")
        doctor_id = prepared.get("doctor_id")
        created_by_id = prepared.get("created_by_id")
        if patient_id not in patient_map or doctor_id not in user_map or user_map[doctor_id] is None:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["patient_id"] = patient_map[patient_id]
        prepared["doctor_id"] = user_map[doctor_id]
        if created_by_id is not None:
            prepared["created_by_id"] = user_map.get(created_by_id)

        existing_uuid = None
        if prepared.get("uuid"):
            existing_uuid = db.fetchone(
                "SELECT id FROM patient_meeting_schedule WHERE uuid = ?",
                (prepared["uuid"],),
            )
        existing_slot = None
        if not existing_uuid:
            existing_slot = db.fetchone(
                """
                SELECT id FROM patient_meeting_schedule
                WHERE patient_id = ? AND doctor_id = ? AND meeting_date = ?
                LIMIT 1
                """,
                (
                    prepared["patient_id"],
                    prepared["doctor_id"],
                    prepared.get("meeting_date"),
                ),
            )
        if existing_slot:
            writable_columns = [
                column
                for column in columns
                if column not in ("id", "uuid") and column in prepared
            ]
            db.execute(
                "UPDATE patient_meeting_schedule SET "
                + ", ".join(f"{column} = ?" for column in writable_columns)
                + " WHERE id = ?",
                tuple([prepared.get(column) for column in writable_columns] + [existing_slot["id"]]),
            )
            summary["updated"] += 1
            continue

        _insert_or_update_by_uuid("patient_meeting_schedule", prepared, columns, summary)
    return summary


def _apply_events(
    events: list[dict[str, Any]],
    user_map: dict[int, int | None],
    document_map: dict[int, int],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = [column for column in _table_columns("events") if column != "id"]
    for row in events:
        prepared = dict(row)
        responsible_id = prepared.get("responsible_id")
        created_by_id = prepared.get("created_by_id")
        meeting_document_id = prepared.get("meeting_document_id")
        if responsible_id is not None:
            prepared["responsible_id"] = user_map.get(responsible_id)
            if prepared["responsible_id"] is None:
                summary["skipped_unmapped_reference"] += 1
                continue
        if created_by_id is not None:
            prepared["created_by_id"] = user_map.get(created_by_id)
        if meeting_document_id is not None:
            prepared["meeting_document_id"] = document_map.get(meeting_document_id)
            if prepared["meeting_document_id"] is None:
                summary["skipped_unmapped_reference"] += 1
                continue

        existing = _find_event_by_natural_key(prepared)
        values = [prepared.get(column) for column in columns if column in prepared]
        used_columns = [column for column in columns if column in prepared]
        if existing:
            db.execute(
                "UPDATE events SET "
                + ", ".join(f"{column} = ?" for column in used_columns)
                + " WHERE id = ?",
                tuple(values + [existing["id"]]),
            )
            summary["updated"] += 1
        else:
            db.execute(
                "INSERT INTO events ("
                + ", ".join(used_columns)
                + ") VALUES ("
                + ", ".join("?" for _ in used_columns)
                + ")",
                tuple(values),
            )
            summary["new"] += 1
    return summary


def _event_id_map(events: list[dict[str, Any]]) -> dict[int, int]:
    result = {}
    for event in events:
        remote_id = event.get("id")
        if remote_id is None:
            continue
        local = _find_event_by_natural_key(event)
        if local:
            result[remote_id] = local["id"]
    return result


def _apply_event_report_positions(
    positions: list[dict[str, Any]],
    event_map: dict[int, int],
    document_map: dict[int, int],
    user_map: dict[int, int | None],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = _table_columns("event_report_positions")
    for row in positions:
        prepared = dict(row)
        event_id = prepared.get("event_id")
        document_id = prepared.get("document_id")
        created_by_id = prepared.get("created_by_id")
        if event_id not in event_map:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["event_id"] = event_map[event_id]
        if document_id is not None:
            prepared["document_id"] = document_map.get(document_id)
            if prepared["document_id"] is None:
                summary["skipped_unmapped_reference"] += 1
                continue
        if created_by_id is not None:
            prepared["created_by_id"] = user_map.get(created_by_id)
        _insert_or_update_by_uuid("event_report_positions", prepared, columns, summary)
    return summary


def _apply_attachments(
    attachments: list[dict[str, Any]], encounter_map: dict[int, int]
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = [column for column in _table_columns("attachments") if column != "id"]
    for row in attachments:
        prepared = dict(row)
        encounter_id = prepared.get("encounter_id")
        if encounter_id not in encounter_map:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["encounter_id"] = encounter_map[encounter_id]
        existing = db.fetchone(
            """
            SELECT id FROM attachments
            WHERE encounter_id = ? AND file_path = ?
              AND COALESCE(title, '') = COALESCE(?, '')
              AND COALESCE(uploaded_at, '') = COALESCE(?, '')
            LIMIT 1
            """,
            (
                prepared["encounter_id"],
                prepared.get("file_path"),
                prepared.get("title") or "",
                prepared.get("uploaded_at"),
            ),
        )
        if existing:
            summary["skipped_same_or_unknown"] += 1
            continue
        used_columns = [column for column in columns if column in prepared]
        db.execute(
            "INSERT INTO attachments ("
            + ", ".join(used_columns)
            + ") VALUES ("
            + ", ".join("?" for _ in used_columns)
            + ")",
            tuple(prepared.get(column) for column in used_columns),
        )
        summary["new"] += 1
    return summary


def _apply_patient_interactions(
    interactions: list[dict[str, Any]],
    patient_map: dict[int, int],
    user_map: dict[int, int | None],
) -> dict[str, int]:
    summary = _empty_import_summary()
    columns = [column for column in _table_columns("patient_interactions") if column != "id"]
    for row in interactions:
        prepared = dict(row)
        patient_id = prepared.get("patient_id")
        user_id = prepared.get("user_id")
        if patient_id not in patient_map:
            summary["skipped_unmapped_reference"] += 1
            continue
        prepared["patient_id"] = patient_map[patient_id]
        if user_id is not None:
            prepared["user_id"] = user_map.get(user_id)
        existing = db.fetchone(
            """
            SELECT id FROM patient_interactions
            WHERE patient_id = ?
              AND COALESCE(user_id, 0) = COALESCE(?, 0)
              AND action = ?
              AND COALESCE(description, '') = COALESCE(?, '')
              AND COALESCE(created_at, '') = COALESCE(?, '')
            LIMIT 1
            """,
            (
                prepared["patient_id"],
                prepared.get("user_id"),
                prepared.get("action"),
                prepared.get("description") or "",
                prepared.get("created_at"),
            ),
        )
        if existing:
            summary["skipped_same_or_unknown"] += 1
            continue
        used_columns = [column for column in columns if column in prepared]
        db.execute(
            "INSERT INTO patient_interactions ("
            + ", ".join(used_columns)
            + ") VALUES ("
            + ", ".join("?" for _ in used_columns)
            + ")",
            tuple(prepared.get(column) for column in used_columns),
        )
        summary["new"] += 1
    return summary

def _find_existing_mapped_row(table_name: str, prepared: dict[str, Any], columns: list[str]):
    if not columns:
        return None
    where = " AND ".join(f"{column} IS ?" for column in columns)
    return db.fetchone(
        f"SELECT id FROM {table_name} WHERE {where} LIMIT 1",
        tuple(prepared.get(column) for column in columns),
    )


def _apply_mapped_rows(
    table_name: str,
    rows: list[dict[str, Any]],
    column_maps: dict[str, dict[int, int | None]],
) -> dict[str, int]:
    summary = _empty_import_summary()
    table_columns = _table_columns(table_name)
    for row in rows:
        prepared = dict(row)
        skip = False
        for column, id_map in column_maps.items():
            remote_id = prepared.get(column)
            if remote_id is None:
                continue
            local_id = id_map.get(remote_id)
            if local_id is None:
                summary["skipped_unmapped_reference"] += 1
                skip = True
                break
            prepared[column] = local_id
        if skip:
            continue

        if "uuid" in table_columns and prepared.get("uuid"):
            _insert_or_update_by_uuid(table_name, prepared, table_columns, summary)
            continue

        insert_columns = [
            column for column in table_columns if column != "id" and column in prepared
        ]
        existing = _find_existing_mapped_row(table_name, prepared, insert_columns)
        if existing:
            summary["skipped_same_or_unknown"] += 1
            continue
        db.execute(
            f"INSERT INTO {table_name} ("
            + ", ".join(insert_columns)
            + ") VALUES ("
            + ", ".join("?" for _ in insert_columns)
            + ")",
            tuple(prepared.get(column) for column in insert_columns),
        )
        summary["new"] += 1
    return summary


def _apply_selected_patient_import(
    file_path: str | Path,
    current_user: User,
    manifest: dict[str, Any],
    data: dict[str, Any],
    password: str | None = None,
) -> dict[str, Any]:
    conn = db.connect()
    try:
        summaries = {
            "departments": _apply_departments(data.get("departments", [])),
            "users": _apply_users(data.get("users", [])),
            "facilities": _apply_facilities(data.get("facilities", [])),
        }
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    patient_result = apply_patient_import(file_path, current_user, password)
    summaries["patients"] = patient_result["summary"]
    user_map = _user_id_map(data.get("users", []))

    conn = db.connect()
    try:
        patients = data.get("patients", [])
        documents = data.get("documents", [])
        plan_items = data.get("treatment_plan_items", [])
        encounter_groups = data.get("encounter_groups", [])
        encounters = data.get("encounters", [])
        event_rows = data.get("events", [])

        patient_map = _remote_to_local_id_map("patients", patients)
        encounter_map = _remote_to_local_id_map("encounters", encounters)

        summaries["documents"] = _apply_documents(
            documents,
            patient_map,
            encounter_map,
            user_map,
        )
        document_map = _remote_to_local_id_map("documents", documents)

        summaries["treatment_plan_items"] = _apply_treatment_plan_items(
            plan_items,
            patient_map,
            document_map,
        )
        plan_item_map = _remote_to_local_id_map("treatment_plan_items", plan_items)

        summaries["encounter_groups"] = _apply_encounter_groups(
            encounter_groups,
            user_map,
        )
        group_map = _remote_to_local_id_map("encounter_groups", encounter_groups)

        summaries["encounters"] = _apply_encounters(
            encounters,
            patient_map,
            user_map,
            document_map,
            plan_item_map,
            group_map,
        )
        encounter_map = _remote_to_local_id_map("encounters", encounters)
        summaries["relinked_documents"] = _relink_document_encounters(documents, encounter_map)
        document_map = _remote_to_local_id_map("documents", documents)

        summaries["encounter_informants"] = _apply_mapped_rows(
            "encounter_informants",
            data.get("encounter_informants", []),
            {"encounter_id": encounter_map},
        )
        summaries["notes"] = _apply_mapped_rows(
            "notes",
            data.get("notes", []),
            {"encounter_id": encounter_map, "author_id": user_map},
        )
        summaries["diagnoses"] = _apply_mapped_rows(
            "diagnoses",
            data.get("diagnoses", []),
            {"encounter_id": encounter_map},
        )
        summaries["prescriptions"] = _apply_mapped_rows(
            "prescriptions",
            data.get("prescriptions", []),
            {"encounter_id": encounter_map},
        )
        summaries["attachments"] = _apply_attachments(
            data.get("attachments", []),
            encounter_map,
        )
        summaries["km_records"] = _apply_km_records(
            data.get("km_records", []),
            encounter_map,
            document_map,
        )
        summaries["patient_interactions"] = _apply_patient_interactions(
            data.get("patient_interactions", []),
            patient_map,
            user_map,
        )
        summaries["patient_meeting_schedule"] = _apply_patient_meeting_schedule(
            data.get("patient_meeting_schedule", []),
            patient_map,
            user_map,
        )
        summaries["events"] = _apply_events(
            event_rows,
            user_map,
            document_map,
        )
        event_map = _event_id_map(event_rows)
        summaries["event_report_positions"] = _apply_event_report_positions(
            data.get("event_report_positions", []),
            event_map,
            document_map,
            user_map,
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    aggregate = _empty_import_summary()
    aggregate["skipped_unmapped_doctor"] = 0
    for table_summary in summaries.values():
        if isinstance(table_summary, dict):
            for key, value in table_summary.items():
                aggregate[key] = aggregate.get(key, 0) + value
    aggregate["details"] = summaries
    aggregate["relinked_documents"] = summaries.get("relinked_documents", 0)
    _write_import_log(file_path, current_user, manifest, aggregate)
    return {"manifest": manifest, "summary": aggregate}

def _relink_document_encounters(
    documents: list[dict[str, Any]], encounter_map: dict[int, int]
) -> int:
    updated = 0
    for document in documents:
        remote_encounter_id = document.get("encounter_id")
        if not remote_encounter_id or remote_encounter_id not in encounter_map:
            continue
        local_doc = db.fetchone(
            "SELECT id, encounter_id FROM documents WHERE uuid = ?",
            (document.get("uuid"),),
        )
        if not local_doc or local_doc["encounter_id"] == encounter_map[remote_encounter_id]:
            continue
        db.execute(
            "UPDATE documents SET encounter_id = ? WHERE id = ?",
            (encounter_map[remote_encounter_id], local_doc["id"]),
        )
        updated += 1
    return updated


def apply_sync_import(
    file_path: str | Path, current_user: User, password: str | None = None
) -> dict[str, Any]:
    if current_user.role not in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
        raise PermissionError("РРјРїРѕСЂС‚ РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ ADMIN, REG Рё LEAD")

    manifest, payload = _read_package(file_path, password)
    data = payload.get("data", {})
    if manifest.get("data_scope") == "selected_patients":
        return _apply_selected_patient_import(file_path, current_user, manifest, data, password)

    existing_tables = set(_application_table_names())
    ordered_tables = [table for table in APPLICATION_TABLE_IMPORT_ORDER if table in data]
    ordered_tables.extend(table for table in data.keys() if table not in set(ordered_tables))

    summaries: dict[str, Any] = {}
    conn = db.connect()
    try:
        db.execute("PRAGMA foreign_keys = OFF")
        for table_name in ordered_tables:
            rows = data.get(table_name, [])
            if not isinstance(rows, list):
                continue
            if table_name not in existing_tables:
                summary = _empty_import_summary()
                summary["skipped_unmapped_reference"] = len(rows)
                summaries[table_name] = summary
                continue
            summaries[table_name] = _insert_or_replace_rows(table_name, rows)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    aggregate = _empty_import_summary()
    aggregate["skipped_unmapped_doctor"] = 0
    for table_summary in summaries.values():
        if not isinstance(table_summary, dict):
            continue
        for key, value in table_summary.items():
            aggregate[key] = aggregate.get(key, 0) + value
    aggregate["details"] = summaries
    aggregate["relinked_documents"] = 0
    if "import_logs" not in data:
        _write_import_log(file_path, current_user, manifest, aggregate)
    return {"manifest": manifest, "summary": aggregate}

def _write_import_log(
    file_path: str | Path,
    current_user: User,
    manifest: dict[str, Any],
    summary: dict[str, Any],
):
    exported_by = manifest.get("exported_by", {})
    db.execute(
        """
        INSERT INTO import_logs
        (imported_by_id, package_author, package_role, package_exported_at, package_path, summary_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            current_user.id,
            exported_by.get("full_name", ""),
            exported_by.get("role", ""),
            manifest.get("exported_at", ""),
            str(file_path),
            json.dumps(summary, ensure_ascii=False, default=str),
        ),
    )
    db.commit()


def get_import_logs(limit: int = 20) -> list[dict[str, Any]]:
    rows = db.fetchall(
        """
        SELECT l.*, u.username AS imported_by_username
        FROM import_logs l
        LEFT JOIN users u ON u.id = l.imported_by_id
        ORDER BY l.imported_at DESC, l.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(row) for row in rows]

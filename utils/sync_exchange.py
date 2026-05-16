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


def _collect_package_data(user: User) -> dict[str, Any]:
    patients = [vars(patient) for patient in Patient.get_all(user, include_inactive=True)]
    patient_ids = {patient["id"] for patient in patients if patient.get("id") is not None}

    encounters = _select_by_column_ids("encounters", "patient_id", patient_ids)
    documents = _select_by_column_ids("documents", "patient_id", patient_ids)
    plan_items = _select_by_column_ids("treatment_plan_items", "patient_id", patient_ids)

    table_names = {row["name"] for row in db.fetchall("SELECT name FROM sqlite_master WHERE type = 'table'")}
    km_records = []
    if "km_records" in table_names:
        document_ids = {row["id"] for row in documents if row.get("id") is not None}
        encounter_ids = {row["id"] for row in encounters if row.get("id") is not None}
        conditions = []
        params = []
        if document_ids:
            conditions.append(
                "document_id IN (" + ",".join("?" for _ in document_ids) + ")"
            )
            params.extend(sorted(document_ids))
        if encounter_ids:
            conditions.append(
                "encounter_id IN (" + ",".join("?" for _ in encounter_ids) + ")"
            )
            params.extend(sorted(encounter_ids))
        if conditions:
            km_records = _rows(
                "SELECT * FROM km_records WHERE "
                + " OR ".join(conditions)
                + " ORDER BY id",
                tuple(params),
            )

    facility_ids = {row["facility_id"] for row in patients if row.get("facility_id") is not None}
    user_ids = {user.id} if user.id is not None else set()
    user_ids.update(row["doctor_id"] for row in patients if row.get("doctor_id") is not None)
    user_ids.update(row["doctor_id"] for row in encounters if row.get("doctor_id") is not None)
    user_ids.update(row["author_id"] for row in documents if row.get("author_id") is not None)

    return {
        "users": _public_users(user_ids),
        "facilities": _select_by_ids("facilities", facility_ids),
        "patients": patients,
        "encounters": encounters,
        "documents": documents,
        "treatment_plan_items": plan_items,
        "km_records": km_records,
    }


def build_export_filename(user: User) -> str:
    safe_username = "".join(ch for ch in user.username if ch.isalnum() or ch in ("-", "_"))
    if not safe_username:
        safe_username = "user"
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"pulsar_export_{safe_username}_{stamp}.pulsarzip"


def export_sync_package(
    user: User, file_path: str | Path, password: str | None = None
) -> dict[str, Any]:
    path = Path(file_path)
    if path.suffix.lower() != ".pulsarzip":
        path = path.with_suffix(".pulsarzip")

    data = _collect_package_data(user)
    counts = {key: len(value) for key, value in data.items()}
    exported_at = datetime.now().isoformat(timespec="seconds")
    manifest = {
        "app": "PULSAR",
        "package_version": PACKAGE_VERSION,
        "encrypted": True,
        "exported_at": exported_at,
        "scope": _patient_scope_label(user),
        "exported_by": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
        },
        "counts": counts,
        "schema": {
            "users": _table_columns("users"),
            "facilities": _table_columns("facilities"),
            "patients": _table_columns("patients"),
            "encounters": _table_columns("encounters"),
            "documents": _table_columns("documents"),
            "treatment_plan_items": _table_columns("treatment_plan_items"),
            "km_records": _table_columns("km_records"),
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


def preview_sync_import(
    file_path: str | Path, password: str | None = None
) -> dict[str, Any]:
    manifest, payload = _read_package(file_path, password)
    data = payload.get("data", {})
    preview = {}
    for table_name in (
        "patients",
        "encounters",
        "documents",
        "treatment_plan_items",
        "km_records",
    ):
        incoming_rows = data.get(table_name, [])
        incoming_with_uuid = [row for row in incoming_rows if row.get("uuid")]
        incoming_uuids = {row["uuid"] for row in incoming_with_uuid}
        local_rows = {}
        if incoming_uuids:
            placeholders = ",".join("?" for _ in incoming_uuids)
            for row in db.fetchall(
                f"SELECT uuid, updated_at FROM {table_name} WHERE uuid IN ({placeholders})",
                tuple(sorted(incoming_uuids)),
            ):
                local_rows[row["uuid"]] = dict(row)

        table_preview = {
            "incoming": len(incoming_rows),
            "without_uuid": len(incoming_rows) - len(incoming_with_uuid),
            "new": 0,
            "package_newer": 0,
            "local_newer": 0,
            "same_or_unknown": 0,
        }
        for incoming in incoming_with_uuid:
            local = local_rows.get(incoming["uuid"])
            if not local:
                table_preview["new"] += 1
                continue

            incoming_ts = _parse_timestamp(incoming.get("updated_at"))
            local_ts = _parse_timestamp(local.get("updated_at"))
            if incoming_ts and local_ts:
                if incoming_ts > local_ts:
                    table_preview["package_newer"] += 1
                elif local_ts > incoming_ts:
                    table_preview["local_newer"] += 1
                else:
                    table_preview["same_or_unknown"] += 1
            else:
                table_preview["same_or_unknown"] += 1

        preview[table_name] = table_preview

    package_users = data.get("users", [])
    preview["users"] = {
        "incoming": len(package_users),
        "without_uuid": 0,
        "new": sum(
            1
            for user in package_users
            if user.get("username")
            and not db.fetchone(
                "SELECT id FROM users WHERE username = ?", (user["username"],)
            )
        ),
        "package_newer": 0,
        "local_newer": 0,
        "same_or_unknown": 0,
    }
    package_facilities = data.get("facilities", [])
    preview["facilities"] = {
        "incoming": len(package_facilities),
        "without_uuid": 0,
        "new": sum(
            1
            for facility in package_facilities
            if facility.get("name")
            and not db.fetchone(
                "SELECT id FROM facilities WHERE name = ?", (facility["name"],)
            )
        ),
        "package_newer": 0,
        "local_newer": 0,
        "same_or_unknown": 0,
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
        _insert_or_update_by_uuid("encounters", prepared, columns, summary)
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
        raise PermissionError("Импорт доступен только ADMIN, REG и LEAD")

    manifest, payload = _read_package(file_path, password)
    data = payload.get("data", {})

    conn = db.connect()
    try:
        users_summary = _apply_users(data.get("users", []))
        facilities_summary = _apply_facilities(data.get("facilities", []))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    patient_result = apply_patient_import(file_path, current_user, password)
    user_map = _user_id_map(data.get("users", []))

    summaries = {
        "users": users_summary,
        "facilities": facilities_summary,
        "patients": patient_result["summary"],
        "documents": _empty_import_summary(),
        "treatment_plan_items": _empty_import_summary(),
        "encounters": _empty_import_summary(),
        "km_records": _empty_import_summary(),
        "relinked_documents": 0,
    }

    conn = db.connect()
    try:
        patients = data.get("patients", [])
        documents = data.get("documents", [])
        plan_items = data.get("treatment_plan_items", [])
        encounters = data.get("encounters", [])
        km_records = data.get("km_records", [])

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

        summaries["encounters"] = _apply_encounters(
            encounters,
            patient_map,
            user_map,
            document_map,
            plan_item_map,
        )
        encounter_map = _remote_to_local_id_map("encounters", encounters)
        summaries["relinked_documents"] = _relink_document_encounters(
            documents, encounter_map
        )
        document_map = _remote_to_local_id_map("documents", documents)
        summaries["km_records"] = _apply_km_records(
            km_records,
            encounter_map,
            document_map,
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    aggregate = _empty_import_summary()
    aggregate["skipped_unmapped_doctor"] = 0
    for table_name in (
        "users",
        "facilities",
        "patients",
        "documents",
        "treatment_plan_items",
        "encounters",
        "km_records",
    ):
        table_summary = summaries.get(table_name, {})
        for key, value in table_summary.items():
            aggregate[key] = aggregate.get(key, 0) + value
    aggregate["details"] = summaries
    aggregate["relinked_documents"] = summaries["relinked_documents"]
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

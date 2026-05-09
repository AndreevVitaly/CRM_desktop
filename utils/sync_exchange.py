from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from models.db_models import Patient, User, db

PACKAGE_VERSION = 1
MANIFEST_NAME = "manifest.json"
DATA_NAME = "data.json"


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
        km_records = _select_by_column_ids("km_records", "document_id", document_ids)

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


def export_sync_package(user: User, file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)
    if path.suffix.lower() != ".pulsarzip":
        path = path.with_suffix(".pulsarzip")

    data = _collect_package_data(user)
    counts = {key: len(value) for key, value in data.items()}
    exported_at = datetime.now().isoformat(timespec="seconds")
    manifest = {
        "app": "PULSAR",
        "package_version": PACKAGE_VERSION,
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
            "patients": _table_columns("patients"),
            "encounters": _table_columns("encounters"),
            "documents": _table_columns("documents"),
            "treatment_plan_items": _table_columns("treatment_plan_items"),
        },
    }

    payload = {"manifest": manifest, "data": data}
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            MANIFEST_NAME,
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        archive.writestr(
            DATA_NAME,
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        )

    return {"path": str(path), "manifest": manifest}


def inspect_sync_package(file_path: str | Path) -> dict[str, Any]:
    manifest, payload = _read_package(file_path)

    data = payload.get("data", {})
    counts = {key: len(value) for key, value in data.items() if isinstance(value, list)}
    return {"manifest": manifest, "counts": counts}


def _read_package(file_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(file_path)
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        if MANIFEST_NAME not in names or DATA_NAME not in names:
            raise ValueError("Файл не похож на пакет обмена PULSAR")
        manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
        payload = json.loads(archive.read(DATA_NAME).decode("utf-8"))

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


def preview_sync_import(file_path: str | Path) -> dict[str, Any]:
    manifest, payload = _read_package(file_path)
    data = payload.get("data", {})
    preview = {}
    for table_name in (
        "patients",
        "encounters",
        "documents",
        "treatment_plan_items",
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


def apply_patient_import(file_path: str | Path, current_user: User) -> dict[str, Any]:
    if current_user.role not in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
        raise PermissionError("Импорт доступен только ADMIN, REG и LEAD")

    manifest, payload = _read_package(file_path)
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

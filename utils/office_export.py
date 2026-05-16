"""
Экспорт встреч пациента в офисные форматы.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from models.db_models import (
    DOCUMENT_TYPE_MEETING,
    Document,
    Encounter,
    EncounterInformant,
    Patient,
    User,
)


def safe_export_name(value: str, fallback: str = "export") -> str:
    name = re.sub(r"[^\w\-]+", "_", value.strip(), flags=re.UNICODE).strip("_")
    return name or fallback


def build_encounter_docx_filename(patient: Patient, encounter: Encounter) -> str:
    date_part = _format_date_for_filename(encounter.started_at)
    return f"pulsar_meeting_{safe_export_name(patient.callsign, 'patient')}_{date_part}.docx"


def build_patient_encounters_xlsx_filename(patient: Patient) -> str:
    return f"pulsar_meetings_{safe_export_name(patient.callsign, 'patient')}.xlsx"


def export_encounter_to_docx(
    patient: Patient,
    encounter: Encounter,
    file_path: str | Path,
):
    try:
        from docx import Document as WordDocument
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt
    except ImportError as exc:
        raise RuntimeError(
            "Для экспорта в Word нужен пакет python-docx. "
            "Установите зависимости из requirements.txt."
        ) from exc

    document = _document_for_encounter(encounter)
    doctor = encounter.doctor
    informants = EncounterInformant.get_by_encounter(encounter.id) if encounter.id else []

    doc = WordDocument()
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Встреча с пациентом")
    run.bold = True
    run.font.size = Pt(16)

    _add_key_value_table(
        doc,
        [
            ("Пациент", patient.callsign or "—"),
            ("Личный номер", patient.personal_number or "—"),
            ("Дата встречи", _format_datetime(encounter.started_at)),
            ("Врач", doctor.full_name if doctor else "—"),
            ("Статус", encounter.status_display),
            ("Результат", encounter.meeting_result_display or "—"),
            ("Документ", _document_number(document)),
            ("Причина", encounter.reason or (document.summary if document else "") or "—"),
        ],
    )

    _add_section(doc, "Информация от пациента", encounter.patient_info)
    _add_section(doc, "Описание встречи", encounter.meeting_description)
    _add_section(doc, "Мероприятия для исполнения пациентом", encounter.patient_tasks)
    _add_section(doc, "Мероприятия в отношении пациента", encounter.patient_measures)
    _add_section(doc, "Мероприятия общего формата", encounter.general_measures)

    if informants:
        doc.add_heading("О ком сообщил пациент", level=2)
        table = doc.add_table(rows=1, cols=5)
        table.style = "Table Grid"
        headers = [
            "ФИО",
            "Должность",
            "Дата рождения",
            "Место работы",
            "Суть информации / меры",
        ]
        for index, header in enumerate(headers):
            table.rows[0].cells[index].text = header
        for informant in informants:
            row = table.add_row().cells
            row[0].text = informant.full_name or "—"
            row[1].text = informant.position or "—"
            row[2].text = _format_date(informant.birth_date)
            row[3].text = informant.workplace or "—"
            row[4].text = _join_lines(informant.info_essence, informant.measures_taken)

    doc.save(str(file_path))


def export_patient_encounters_to_xlsx(
    patient: Patient,
    file_path: str | Path,
):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError(
            "Для экспорта в Excel нужен пакет openpyxl. "
            "Установите зависимости из requirements.txt."
        ) from exc

    rows = collect_patient_encounter_rows(patient)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Встречи"

    title = f"Встречи пациента: {patient.callsign or '—'}"
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=10)
    title_cell = sheet.cell(row=1, column=1, value=title)
    title_cell.font = Font(bold=True, size=14)

    headers = [
        "Дата",
        "Пациент",
        "Личный номер",
        "Врач",
        "Результат",
        "Причина",
        "Статус",
        "Информация от пациента",
        "Документ",
        "Заметки",
    ]
    sheet.append(headers)
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    for cell in sheet[2]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    for item in rows:
        sheet.append(
            [
                item["date"],
                patient.callsign or "—",
                patient.personal_number or "—",
                item["doctor"],
                item["result"],
                item["reason"],
                item["status"],
                item["patient_info"],
                item["document_number"],
                item["notes"],
            ]
        )

    for row in sheet.iter_rows(min_row=3):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    widths = [14, 18, 16, 24, 22, 34, 16, 42, 16, 28]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "A3"
    workbook.save(str(file_path))


def collect_patient_encounter_rows(patient: Patient) -> list[dict[str, Any]]:
    documents = Document.get_by_patient(patient.id)
    meeting_docs = [doc for doc in documents if doc.doc_type == DOCUMENT_TYPE_MEETING]
    rows = []
    for document in meeting_docs:
        encounter = document.encounter
        doctor = encounter.doctor if encounter else document.author
        rows.append(
            {
                "date": _format_date(document.doc_date),
                "doctor": doctor.full_name if doctor else "—",
                "result": (
                    encounter.meeting_result_display
                    if encounter and encounter.meeting_result
                    else "—"
                ),
                "reason": (
                    encounter.reason if encounter and encounter.reason else document.summary
                )
                or "—",
                "status": encounter.status_display if encounter else "Завершен",
                "patient_info": encounter.patient_info if encounter else "",
                "document_number": _document_number(document),
                "notes": encounter.general_measures if encounter else "",
                "sort_key": document.doc_date,
            }
        )
    rows.sort(key=lambda item: _sort_value(item["sort_key"]))
    return rows


def _document_for_encounter(encounter: Encounter) -> Document | None:
    if encounter.document_id:
        return Document.get_by_id(encounter.document_id)
    return None


def _add_key_value_table(doc, rows: list[tuple[str, str]]):
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    for label, value in rows:
        cells = table.add_row().cells
        cells[0].text = label
        cells[1].text = str(value or "—")


def _add_section(doc, title: str, text: str):
    doc.add_heading(title, level=2)
    doc.add_paragraph(text.strip() if text else "—")


def _join_lines(*values: str) -> str:
    return "\n".join(value for value in values if value) or "—"


def _document_number(document: Document | None) -> str:
    if not document:
        return "—"
    return str(document.doc_number or f"#{document.id}")


def _format_date(value) -> str:
    if not value:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")
    return str(value)


def _format_datetime(value) -> str:
    if not value:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


def _format_date_for_filename(value) -> str:
    if not value:
        return "date"
    if hasattr(value, "strftime"):
        return value.strftime("%Y%m%d")
    return safe_export_name(str(value), "date")


def _sort_value(value) -> str:
    if not value:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)

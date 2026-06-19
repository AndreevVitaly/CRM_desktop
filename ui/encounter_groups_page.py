from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.db_models import Encounter, EncounterGroup, User
from ui.styles import FONTS, RADIUS, get_colors, get_main_stylesheet


class EncounterGroupDetailDialog(QDialog):
    def __init__(self, parent, user: User, group: EncounterGroup, on_changed=None):
        super().__init__(parent)
        self.user = user
        self.group = group
        self.on_changed = on_changed
        self._encounters: list[Encounter] = []
        self.setWindowTitle(f"Признак: {group.name}")
        self.setMinimumSize(980, 640)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(self.group.name or "Без наименования")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        category = QLabel(f"Признак: {self.group.category_display}")
        category.setObjectName("muted")
        layout.addWidget(category)

        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("card")
        stats_layout = QGridLayout(self.stats_frame)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setHorizontalSpacing(24)
        stats_layout.setVerticalSpacing(8)

        self.total_label = QLabel()
        self.patients_label = QLabel()
        self.finished_label = QLabel()
        self.active_label = QLabel()
        self.latest_label = QLabel()
        for index, (caption, value_label) in enumerate(
            (
                ("Встреч всего", self.total_label),
                ("Пациентов", self.patients_label),
                ("Завершено", self.finished_label),
                ("В работе", self.active_label),
                ("Последняя встреча", self.latest_label),
            )
        ):
            caption_label = QLabel(caption)
            caption_label.setObjectName("muted")
            value_label.setObjectName("statValue")
            stats_layout.addWidget(caption_label, 0, index)
            stats_layout.addWidget(value_label, 1, index)
        layout.addWidget(self.stats_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Дата",
                "Пациент",
                "Личный номер",
                "Врач",
                "Результат",
                "Статус",
                "Информация",
                "Документ",
            ]
        )
        header = self.table.horizontalHeader()
        for column in (0, 1, 2, 3, 4, 5, 7):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_selected_encounter)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondaryBtn")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        self.setStyleSheet(get_main_stylesheet())
        self._load_encounters()

    @staticmethod
    def _encounter_date(encounter: Encounter):
        document = encounter.document
        return document.doc_date if document and document.doc_date else encounter.started_at

    @staticmethod
    def _format_datetime(value) -> str:
        if not value:
            return "—"
        return value.strftime("%d.%m.%Y") if hasattr(value, "strftime") else str(value)

    def _load_encounters(self):
        self._encounters = [
            encounter
            for encounter in Encounter.get_all(self.user, include_inactive=False)
            if encounter.group_id == self.group.id
        ]
        self._encounters.sort(
            key=lambda encounter: self._encounter_date(encounter) or datetime.min,
            reverse=True,
        )
        self._render_stats()
        self._render_rows()

    def _render_stats(self):
        patient_ids = {
            encounter.patient_id
            for encounter in self._encounters
            if encounter.patient_id is not None
        }
        finished = sum(
            1
            for encounter in self._encounters
            if encounter.status == Encounter.STATUS_FINISHED
        )
        active = len(self._encounters) - finished
        latest = self._encounter_date(self._encounters[0]) if self._encounters else None

        self.total_label.setText(str(len(self._encounters)))
        self.patients_label.setText(str(len(patient_ids)))
        self.finished_label.setText(str(finished))
        self.active_label.setText(str(active))
        self.latest_label.setText(self._format_datetime(latest))

    def _render_rows(self):
        colors = get_colors()
        status_colors = {
            Encounter.STATUS_PLANNED: colors["accent"],
            Encounter.STATUS_INPROGRESS: colors["warning"],
            Encounter.STATUS_FINISHED: colors["success"],
        }

        self.table.setRowCount(0)
        for encounter in self._encounters:
            row = self.table.rowCount()
            self.table.insertRow(row)
            patient = encounter.patient
            doctor = encounter.doctor
            document = encounter.document
            values = [
                self._format_datetime(self._encounter_date(encounter)),
                patient.callsign if patient else "—",
                patient.personal_number if patient and patient.personal_number else "—",
                doctor.full_name if doctor else "—",
                encounter.meeting_result_display if encounter.meeting_result else "—",
                encounter.status_display,
                encounter.patient_info or encounter.reason or "—",
                str(document.doc_number or f"#{document.id}") if document else "—",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, encounter.id)
                if column == 5:
                    item.setForeground(
                        QColor(status_colors.get(encounter.status, colors["text"]))
                    )
                self.table.setItem(row, column, item)

    def _selected_encounter(self) -> Encounter | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        if row < 0 or row >= len(self._encounters):
            return None
        return self._encounters[row]

    def _edit_selected_encounter(self, _index=None):
        encounter = self._selected_encounter()
        if not encounter or not encounter.patient:
            return

        from ui.encounter_edit_form import EncounterEditDialog

        dialog = EncounterEditDialog(self.user, encounter.patient, encounter)
        if dialog.exec():
            self._load_encounters()
            if self.on_changed:
                self.on_changed()


class EncounterGroupsPage(QWidget):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._visible_rows: list[dict] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        filters = QFrame()
        filters.setObjectName("card")
        filter_layout = QHBoxLayout(filters)
        filter_layout.setContentsMargins(12, 12, 12, 12)
        filter_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(
            "Поиск по условному наименованию, пациенту или личному номеру"
        )
        self.search_input.setMinimumWidth(320)
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._load_groups)
        filter_layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.setObjectName("filterCombo")
        self.category_filter.setFrame(False)
        self.category_filter.addItem("Все признаки", "")
        for value, label in EncounterGroup.CATEGORY_CHOICES:
            self.category_filter.addItem(label, value)
        self.category_filter.setFixedHeight(34)
        self.category_filter.setFixedWidth(260)
        self.category_filter.setStyleSheet(self._filter_combo_style())
        self.category_filter.currentIndexChanged.connect(self._load_groups)
        filter_layout.addWidget(self.category_filter)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setObjectName("filterButton")
        refresh_btn.setFixedHeight(34)
        refresh_btn.setMinimumWidth(92)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(self._filter_button_style())
        refresh_btn.clicked.connect(self._load_groups)
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filters)

        self.count_label = QLabel()
        self.count_label.setObjectName("muted")
        layout.addWidget(self.count_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Условное наименование",
                "Признак",
                "Встреч",
                "Последняя встреча",
                "Пациенты",
                "Личные номера",
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._open_selected_group)
        layout.addWidget(self.table, 1)

        self.setStyleSheet(get_main_stylesheet())
        self._load_groups()

    def _filter_combo_style(self) -> str:
        colors = get_colors()
        return f"""
            QComboBox#filterCombo {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                padding: 4px 30px 4px 12px;
                color: {colors['text']};
                font-size: {FONTS['size_small']}pt;
                min-width: 0px;
            }}
            QComboBox#filterCombo:hover {{
                border: 1px solid {colors['accent']};
            }}
            QComboBox#filterCombo:focus {{
                border: 1px solid {colors['accent']};
                background-color: {colors['accent_light']};
            }}
            QComboBox#filterCombo::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox#filterCombo::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {colors['text_muted']};
                margin-right: 10px;
            }}
            QComboBox#filterCombo QAbstractItemView {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                selection-background-color: {colors['accent_light']};
                selection-color: {colors['text']};
                outline: none;
            }}
        """

    def _filter_button_style(self) -> str:
        colors = get_colors()
        return f"""
            QPushButton#filterButton {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                padding: 4px 12px;
                min-height: 0px;
                font-weight: 500;
                font-size: {FONTS['size_xs']}pt;
                color: {colors['text']};
            }}
            QPushButton#filterButton:hover {{
                background-color: {colors['accent_light']};
                border: 1px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#filterButton:pressed {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                color: #FFFFFF;
            }}
        """

    @staticmethod
    def _format_date(value: str | None) -> str:
        if not value:
            return "—"
        for fmt in (
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(value, fmt).strftime("%d.%m.%Y")
            except ValueError:
                continue
        return str(value)

    @staticmethod
    def _short_list(value: str | None) -> str:
        if not value:
            return "—"
        items = []
        for raw in value.split(","):
            item = raw.strip()
            if item and item not in items:
                items.append(item)
        if len(items) <= 4:
            return ", ".join(items) if items else "—"
        return ", ".join(items[:4]) + f" (+{len(items) - 4})"

    def _load_groups(self):
        search = self.search_input.text().strip().casefold()
        category = self.category_filter.currentData() or ""

        rows = []
        for row in EncounterGroup.get_summary(self.user):
            if category and row.get("category") != category:
                continue
            haystack = " ".join(
                [
                    row.get("name") or "",
                    row.get("description") or "",
                    row.get("patient_names") or "",
                    row.get("patient_numbers") or "",
                ]
            ).casefold()
            if search and search not in haystack:
                continue
            rows.append(row)

        self._visible_rows = rows
        self._render_rows()

    def _render_rows(self):
        self.table.setRowCount(0)
        category_labels = dict(EncounterGroup.CATEGORY_CHOICES)
        for data in self._visible_rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                data.get("name") or "—",
                category_labels.get(data.get("category"), data.get("category") or "—"),
                str(data.get("encounters_count") or 0),
                self._format_date(data.get("last_encounter_at")),
                self._short_list(data.get("patient_names")),
                self._short_list(data.get("patient_numbers")),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, data.get("id"))
                self.table.setItem(row, column, item)

        self.count_label.setText(f"Признаков: {len(self._visible_rows)}")

    def _selected_group_id(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _open_selected_group(self, _index=None):
        group_id = self._selected_group_id()
        if not group_id:
            return
        group = EncounterGroup.get_by_id(group_id)
        if not group:
            return
        dialog = EncounterGroupDetailDialog(
            self,
            self.user,
            group,
            on_changed=self._load_groups,
        )
        dialog.exec()

    def update_theme(self):
        self.setStyleSheet(get_main_stylesheet())
        self.category_filter.setStyleSheet(self._filter_combo_style())
        for button in self.findChildren(QPushButton, "filterButton"):
            button.setStyleSheet(self._filter_button_style())
        self._render_rows()

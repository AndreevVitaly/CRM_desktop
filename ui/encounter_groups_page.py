from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.db_models import Encounter, EncounterGroup, User
from ui.styles import FONTS, RADIUS, get_colors, get_main_stylesheet



class EncounterGroupSummaryDialog(QDialog):
    """Полноэкранная сводка по всем встречам выбранного признака."""

    def __init__(self, parent, user: User, group: EncounterGroup):
        super().__init__(parent)
        self.user = user
        self.group = group
        self.colors = get_colors()
        self._encounters = self._load_group_encounters()
        self.setWindowTitle(f"Сводка по признаку: {group.name}")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(1100, 760)
        self._init_ui()
        self.showMaximized()

    @staticmethod
    def _encounter_date(encounter: Encounter):
        document = encounter.document
        return document.doc_date if document and document.doc_date else encounter.started_at

    @staticmethod
    def _format_date(value) -> str:
        if not value:
            return "—"
        return value.strftime("%d.%m.%Y") if hasattr(value, "strftime") else str(value)

    def _load_group_encounters(self) -> list[Encounter]:
        encounters = [
            encounter
            for encounter in Encounter.get_all(self.user, include_inactive=False)
            if encounter.group_id == self.group.id
        ]
        encounters.sort(
            key=lambda encounter: self._encounter_date(encounter) or datetime.min,
            reverse=True,
        )
        return encounters

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        title = QLabel(self.group.name or "Без наименования")
        title.setObjectName("summaryTitle")
        layout.addWidget(title)

        category = QLabel(f"Признак: {self.group.category_display}")
        category.setObjectName("muted")
        layout.addWidget(category)

        stats = self._stats_panel()
        layout.addWidget(stats)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(12)
        right = QVBoxLayout()
        right.setSpacing(12)

        left.addWidget(self._text_panel("Категории АА", self._patients_text()))
        left.addWidget(self._text_panel("Даты и документы", self._documents_text()))
        left.addWidget(self._text_panel("Информация", self._field_text("patient_info", fallback_attr="reason")))
        left.addWidget(self._text_panel("Описание встреч", self._field_text("meeting_description")))
        left.addStretch()

        right.addWidget(self._text_panel("Результаты", self._counter_text("meeting_result_display")))
        right.addWidget(self._text_panel("Статусы", self._counter_text("status_display")))
        right.addWidget(self._text_panel("Работники", self._doctors_text()))
        right.addWidget(self._text_panel("Мероприятия", self._measures_text()))
        right.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left)
        right_widget = QWidget()
        right_widget.setLayout(right)
        grid.addWidget(left_widget, 0, 0)
        grid.addWidget(right_widget, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondaryBtn")
        close_btn.setFixedHeight(40)
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        self.setStyleSheet(self._style())

    def _stats_panel(self) -> QFrame:
        patients = {
            encounter.patient_id
            for encounter in self._encounters
            if encounter.patient_id is not None
        }
        finished = sum(1 for encounter in self._encounters if encounter.status == Encounter.STATUS_FINISHED)
        active = len(self._encounters) - finished
        latest = self._encounter_date(self._encounters[0]) if self._encounters else None
        values = [
            ("Встреч всего", str(len(self._encounters))),
            ("Категорий АА", str(len(patients))),
            ("Завершено", str(finished)),
            ("В работе", str(active)),
            ("Последняя встреча", self._format_date(latest)),
        ]
        frame = QFrame()
        frame.setObjectName("summaryPanel")
        layout = QGridLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setHorizontalSpacing(28)
        layout.setVerticalSpacing(8)
        for column, (caption, value) in enumerate(values):
            caption_label = QLabel(caption)
            caption_label.setObjectName("muted")
            value_label = QLabel(value)
            value_label.setObjectName("statValue")
            layout.addWidget(caption_label, 0, column)
            layout.addWidget(value_label, 1, column)
        return frame

    @staticmethod
    def _unique_lines(lines: list[str]) -> str:
        unique = []
        for line in lines:
            clean = line.strip()
            if clean and clean != "—" and clean not in unique:
                unique.append(clean)
        return "\n".join(unique) if unique else "—"

    def _patients_text(self) -> str:
        lines = []
        for encounter in self._encounters:
            patient = encounter.patient
            if not patient:
                continue
            number = f" л.н. {patient.personal_number}" if patient.personal_number else ""
            lines.append(f"{patient.callsign or patient.full_name}{number}")
        return self._unique_lines(lines)

    def _documents_text(self) -> str:
        lines = []
        for encounter in self._encounters:
            patient = encounter.patient
            document = encounter.document
            date_text = self._format_date(self._encounter_date(encounter))
            patient_text = patient.callsign if patient else "—"
            doc_text = str(document.doc_number or f"#{document.id}") if document else "—"
            lines.append(f"{date_text} • {patient_text} • {doc_text}")
        return "\n".join(lines) if lines else "—"

    def _doctors_text(self) -> str:
        lines = []
        for encounter in self._encounters:
            if encounter.doctor:
                lines.append(encounter.doctor.full_name)
        return self._unique_lines(lines)

    def _counter_text(self, attr_name: str) -> str:
        counts: dict[str, int] = {}
        for encounter in self._encounters:
            value = getattr(encounter, attr_name, "") or "—"
            counts[str(value)] = counts.get(str(value), 0) + 1
        if not counts:
            return "—"
        return "\n".join(f"{name}: {count}" for name, count in counts.items())

    def _field_text(self, attr_name: str, fallback_attr: str | None = None) -> str:
        lines = []
        for encounter in self._encounters:
            value = getattr(encounter, attr_name, "") or ""
            if not value and fallback_attr:
                value = getattr(encounter, fallback_attr, "") or ""
            if not value:
                continue
            patient = encounter.patient
            date_text = self._format_date(self._encounter_date(encounter))
            patient_text = patient.callsign if patient else "—"
            lines.append(f"{date_text} • {patient_text}\n{value}")
        return "\n\n".join(lines) if lines else "—"

    def _measures_text(self) -> str:
        sections = []
        fields = [
            ("Для исполнения источником", "patient_tasks"),
            ("В отношении категории АА", "patient_measures"),
            ("Общего формата", "general_measures"),
        ]
        for title, attr_name in fields:
            value = self._field_text(attr_name)
            if value != "—":
                sections.append(f"{title}\n{value}")
        return "\n\n".join(sections) if sections else "—"

    def _text_panel(self, title: str, text: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("summaryPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(text or "—")
        editor.setMinimumHeight(120)
        editor.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(label)
        layout.addWidget(editor)
        return frame

    def _style(self) -> str:
        colors = self.colors
        return get_main_stylesheet() + f"""
            QDialog {{ background-color: {colors['bg']}; color: {colors['text']}; }}
            QLabel#summaryTitle {{
                color: {colors['text']};
                font-size: {FONTS['size_header']}pt;
                font-weight: 700;
                background-color: transparent;
            }}
            QLabel#sectionTitle {{
                color: {colors['text']};
                font-size: {FONTS['size_medium']}pt;
                font-weight: 700;
                background-color: transparent;
            }}
            QFrame#summaryPanel {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
            }}
            QFrame#summaryPanel QLabel {{ background-color: transparent; border: none; }}
            QScrollArea {{ border: none; background-color: {colors['bg']}; }}
            QScrollArea QWidget {{ background-color: {colors['bg']}; }}
            QTextEdit {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: none;
                selection-background-color: {colors['accent']};
                selection-color: #FFFFFF;
            }}
        """


class EncounterGroupDetailDialog(QDialog):
    def __init__(self, parent, user: User, group: EncounterGroup, on_changed=None):
        super().__init__(parent)
        self.user = user
        self.group = group
        self.on_changed = on_changed
        self._encounters: list[Encounter] = []
        self.setWindowTitle(f"Признак: {group.name}")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(980, 640)
        self._init_ui()
        self.showMaximized()

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
                ("Категорий АА", self.patients_label),
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
                "Категория АА",
                "Личный номер",
                "Работник",
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
        summary_btn = QPushButton("Сводка")
        summary_btn.setObjectName("secondaryBtn")
        summary_btn.setFixedHeight(40)
        summary_btn.clicked.connect(self._open_summary)
        buttons.addWidget(summary_btn)

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

    def _open_summary(self):
        dialog = EncounterGroupSummaryDialog(self, self.user, self.group)
        dialog.exec()

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
            "Поиск по условному наименованию, категории АА или личному номеру"
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

        summary_btn = QPushButton("СВОДКА")
        summary_btn.setObjectName("filterButton")
        summary_btn.setFixedHeight(34)
        summary_btn.setMinimumWidth(92)
        summary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        summary_btn.setStyleSheet(self._filter_button_style())
        summary_btn.clicked.connect(self._open_selected_group_summary)
        filter_layout.addWidget(summary_btn)

        word_btn = QPushButton("WORD")
        word_btn.setObjectName("filterButton")
        word_btn.setFixedHeight(34)
        word_btn.setMinimumWidth(92)
        word_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        word_btn.setStyleSheet(self._filter_button_style())
        word_btn.clicked.connect(self._export_selected_group_word)
        filter_layout.addWidget(word_btn)

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
                "Категории АА",
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
                padding: 4px 12px;
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
                width: 0px;
            }}
            QComboBox#filterCombo::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border: none;
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

    def _open_selected_group_summary(self):
        group_id = self._selected_group_id()
        if not group_id:
            QMessageBox.information(self, "Сводка", "Выберите признак в таблице")
            return
        group = EncounterGroup.get_by_id(group_id)
        if not group:
            QMessageBox.warning(self, "Сводка", "Не удалось найти выбранный признак")
            return
        dialog = EncounterGroupSummaryDialog(self, self.user, group)
        dialog.exec()

    def _export_selected_group_word(self):
        group_id = self._selected_group_id()
        if not group_id:
            QMessageBox.information(self, "Экспорт Word", "Выберите признак в таблице")
            return
        group = EncounterGroup.get_by_id(group_id)
        if not group:
            QMessageBox.warning(self, "Экспорт Word", "Не удалось найти выбранный признак")
            return

        encounters = [
            encounter
            for encounter in Encounter.get_all(self.user, include_inactive=False)
            if encounter.group_id == group.id
        ]
        encounters.sort(
            key=lambda encounter: EncounterGroupSummaryDialog._encounter_date(encounter)
            or datetime.min,
            reverse=True,
        )

        from utils.office_export import (
            build_encounter_group_summary_docx_filename,
            export_encounter_group_summary_to_docx,
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить сводку признака в Word",
            build_encounter_group_summary_docx_filename(group),
            "Word (*.docx)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".docx"):
            file_path += ".docx"

        try:
            export_encounter_group_summary_to_docx(group, encounters, file_path)
        except RuntimeError as exc:
            QMessageBox.warning(self, "Экспорт Word", str(exc))
            return
        except PermissionError:
            QMessageBox.warning(
                self,
                "Экспорт Word",
                "Не удалось заменить файл. Закройте его в Word и попробуйте снова.",
            )
            return
        except Exception as exc:
            QMessageBox.critical(self, "Экспорт Word", f"Не удалось создать файл:\n{exc}")
            return

        QMessageBox.information(self, "Экспорт Word", "Сводка сохранена в Word")

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

"""
Patient meeting schedule page.
"""

import calendar
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.db_models import (
    DOCUMENT_TYPE_MEETING,
    Document,
    Facility,
    Patient,
    PatientMeetingSchedule,
    User,
    get_department_choices,
)
from ui.styles import FONTS, RADIUS, get_colors, get_main_stylesheet

SCHEDULE_ROW_HEIGHT = 40
SCHEDULE_STATUS_MARKER_WIDTH = 38
SCHEDULE_STATUS_MARKER_HEIGHT = 34
SCHEDULE_STATUS_MARKER_RADIUS = 8
PATIENT_COLUMN_WIDTH = 230
SCHEDULE_TOTAL_COLUMN_WIDTH = 70
SCHEDULE_STATUS_COLORS = {
    PatientMeetingSchedule.STATUS_PLANNED: "#059669",
    PatientMeetingSchedule.STATUS_COMPLETED: "#2563EB",
}
SCHEDULE_STATUS_COLOR_ROLE = Qt.ItemDataRole.UserRole.value + 1
SCHEDULE_DOCUMENTED_ROLE = Qt.ItemDataRole.UserRole.value + 2
SCHEDULE_DOCUMENTED_COLOR = "#7C3AED"


class ScheduleStatusDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        color = index.data(SCHEDULE_STATUS_COLOR_ROLE)
        has_documented_meeting = bool(index.data(SCHEDULE_DOCUMENTED_ROLE))
        if not color and not has_documented_meeting:
            return

        rect = option.rect
        marker_width = max(14, min(SCHEDULE_STATUS_MARKER_WIDTH, rect.width() - 6))
        marker_height = max(14, min(SCHEDULE_STATUS_MARKER_HEIGHT, rect.height() - 6))
        marker_x = rect.x() + max(0, (rect.width() - marker_width) // 2)
        marker_y = rect.y() + max(0, (rect.height() - marker_height) // 2)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        if color:
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(
                marker_x,
                marker_y,
                marker_width,
                marker_height,
                SCHEDULE_STATUS_MARKER_RADIUS,
                SCHEDULE_STATUS_MARKER_RADIUS,
            )
        if has_documented_meeting:
            badge_size = 12 if color else 18
            badge_x = (
                marker_x + marker_width - badge_size - 4
                if color
                else rect.x() + max(0, (rect.width() - badge_size) // 2)
            )
            badge_y = (
                marker_y + 4
                if color
                else rect.y() + max(0, (rect.height() - badge_size) // 2)
            )
            painter.setPen(QColor(SCHEDULE_DOCUMENTED_COLOR if color else "#FFFFFF"))
            painter.setBrush(QColor("#FFFFFF" if color else SCHEDULE_DOCUMENTED_COLOR))
            painter.drawRoundedRect(
                badge_x,
                badge_y,
                badge_size,
                badge_size,
                4,
                4,
            )
        painter.restore()


class MeetingSchedulePage(QWidget):
    """Monthly patient meeting matrix for one doctor."""

    MONTHS = [
        ("Январь", 1),
        ("Февраль", 2),
        ("Март", 3),
        ("Апрель", 4),
        ("Май", 5),
        ("Июнь", 6),
        ("Июль", 7),
        ("Август", 8),
        ("Сентябрь", 9),
        ("Октябрь", 10),
        ("Ноябрь", 11),
        ("Декабрь", 12),
    ]

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        today = date.today()
        self.selected_month = today.month
        self.selected_year = today.year
        self.current_filter = ""
        self.type_filter = ""
        self.facility_filter = 0
        self.department_filter = ""
        self.doctor_filter = user.id if user.role == User.ROLE_DOCTOR else 0
        self.status_filter = ""
        self.patients: list[Patient] = []
        self.schedule = {}
        self.documented_meetings: set[tuple[int, date]] = set()
        self._syncing_selection = False
        self._init_ui()

    def _init_ui(self):
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._create_filter_panel())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")

        self.patient_table = self._create_patient_table()
        self.schedule_table = self._create_schedule_table()
        splitter.addWidget(self.patient_table)
        splitter.addWidget(self.schedule_table)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([PATIENT_COLUMN_WIDTH, 1200])
        layout.addWidget(splitter, 1)

        bottom_layout = QHBoxLayout()
        self.legend_label = QLabel(
            "<span style='font-size:17pt; color:#059669;'>■</span> "
            "Запланировано&nbsp;&nbsp;&nbsp;"
            "<span style='font-size:17pt; color:#2563EB;'>■</span> "
            "Исполнено&nbsp;&nbsp;&nbsp;"
            "<span style='font-size:17pt; color:#7C3AED;'>■</span> "
            "Документирована"
        )
        self.legend_label.setTextFormat(Qt.TextFormat.RichText)
        self.legend_label.setStyleSheet(
            f"color: {colors['text_muted']}; font-size: {FONTS['size_small']}pt;"
        )
        bottom_layout.addWidget(self.legend_label)
        bottom_layout.addStretch()
        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        bottom_layout.addWidget(self.count_label)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)
        self.setStyleSheet(get_main_stylesheet())
        self._apply_filter_styles()
        self._load_data()

    def _create_filter_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("scheduleFilterPanel")
        panel.setFixedHeight(128)
        panel.setStyleSheet(self._filter_panel_style())

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.setSpacing(12)
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(
            "Поиск по позывному, личному номеру, документу..."
        )
        self.search_input.setFixedWidth(310)
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._on_search_changed)
        top.addWidget(self.search_input)

        self.month_combo = QComboBox()
        self.month_combo.setFrame(False)
        self.month_combo.setObjectName("filterCombo")
        for label, value in self.MONTHS:
            self.month_combo.addItem(label, value)
        self.month_combo.setCurrentIndex(self.selected_month - 1)
        self.month_combo.setFixedWidth(140)
        self.month_combo.setFixedHeight(34)
        self.month_combo.setStyleSheet(self._filter_combo_style())
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        top.addWidget(self.month_combo)

        self.year_combo = QComboBox()
        self.year_combo.setFrame(False)
        self.year_combo.setObjectName("filterCombo")
        for year in range(self.selected_year - 5, self.selected_year + 6):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentText(str(self.selected_year))
        self.year_combo.setFixedWidth(110)
        self.year_combo.setFixedHeight(34)
        self.year_combo.setStyleSheet(self._filter_combo_style())
        self.year_combo.currentIndexChanged.connect(self._on_month_changed)
        top.addWidget(self.year_combo)

        self.department_combo = QComboBox()
        self.department_combo.setFrame(False)
        self.department_combo.setObjectName("filterCombo")
        self.department_combo.addItem("Все отделения", "")
        if self.user.role in (User.ROLE_LEAD, User.ROLE_NURSE):
            self.department_combo.addItem(self.user.department_display, self.user.department)
            self.department_combo.setCurrentIndex(1)
            self.department_combo.setEnabled(False)
        else:
            for dept_code, dept_name in get_department_choices(include_inactive=False):
                self.department_combo.addItem(dept_name, dept_code)
        self.department_combo.setFixedWidth(190)
        self.department_combo.setFixedHeight(34)
        self.department_combo.setStyleSheet(self._filter_combo_style())
        self.department_combo.currentIndexChanged.connect(self._on_department_changed)
        top.addWidget(self.department_combo)

        self.doctor_combo = QComboBox()
        self.doctor_combo.setFrame(False)
        self.doctor_combo.setObjectName("filterCombo")
        self.doctor_combo.setFixedWidth(220)
        self.doctor_combo.setFixedHeight(34)
        self.doctor_combo.setStyleSheet(self._filter_combo_style())
        self.doctor_combo.currentIndexChanged.connect(self._on_filter_changed)
        top.addWidget(self.doctor_combo)
        self._populate_doctor_filter()

        top.addStretch()

        self.type_combo = QComboBox()
        self.type_combo.setFrame(False)
        self.type_combo.setObjectName("filterCombo")
        self.type_combo.addItem("Все типы", "")
        self.type_combo.addItem("Категория А", "adult")
        self.type_combo.addItem("Категория Д", "child")
        self.type_combo.addItem("Категория К", "undefined")
        self.type_combo.setFixedWidth(150)
        self.type_combo.setFixedHeight(34)
        self.type_combo.setStyleSheet(self._filter_combo_style())
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        bottom.addWidget(self.type_combo)

        self.facility_combo = QComboBox()
        self.facility_combo.setFrame(False)
        self.facility_combo.setObjectName("filterCombo")
        self.facility_combo.addItem("Все места", 0)
        for facility in Facility.get_all():
            self.facility_combo.addItem(facility.name, facility.id)
        self.facility_combo.setFixedWidth(210)
        self.facility_combo.setFixedHeight(34)
        self.facility_combo.setStyleSheet(self._filter_combo_style())
        self.facility_combo.currentIndexChanged.connect(self._on_filter_changed)
        bottom.addWidget(self.facility_combo)

        self.status_combo = QComboBox()
        self.status_combo.setFrame(False)
        self.status_combo.setObjectName("filterCombo")
        self.status_combo.addItem("Все отметки", "")
        self.status_combo.addItem("Запланировано", PatientMeetingSchedule.STATUS_PLANNED)
        self.status_combo.addItem("Исполнено", PatientMeetingSchedule.STATUS_COMPLETED)
        self.status_combo.addItem("Без отметок", "EMPTY")
        self.status_combo.setFixedWidth(170)
        self.status_combo.setFixedHeight(34)
        self.status_combo.setStyleSheet(self._filter_combo_style())
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        bottom.addWidget(self.status_combo)

        reset_btn = QPushButton("Сброс")
        reset_btn.setObjectName("filterButton")
        reset_btn.setFixedHeight(34)
        reset_btn.setMinimumWidth(70)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(self._filter_button_style())
        reset_btn.clicked.connect(self._reset_filters)
        bottom.addWidget(reset_btn)
        bottom.addStretch()

        layout.addLayout(top)
        layout.addLayout(bottom)
        return panel

    def _filter_panel_style(self) -> str:
        colors = get_colors()
        return f"""
            QFrame#scheduleFilterPanel {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 12px;
            }}
        """

    def _filter_combo_style(self) -> str:
        colors = get_colors()
        return f"""
            QComboBox#filterCombo {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                padding: 4px 12px;
                min-height: 0px;
                font-weight: 500;
                font-size: {FONTS['size_small']}pt;
                color: {colors['text']};
            }}
            QComboBox#filterCombo:hover {{
                border: 1px solid {colors['accent']};
            }}
            QComboBox#filterCombo:focus {{
                border: 1px solid {colors['accent']};
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
                selection-color: {colors['accent']};
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

    def _apply_filter_styles(self):
        panel = self.findChild(QFrame, "scheduleFilterPanel")
        if panel:
            panel.setStyleSheet(self._filter_panel_style())
        for combo in self.findChildren(QComboBox, "filterCombo"):
            combo.setStyleSheet(self._filter_combo_style())
        for button in self.findChildren(QPushButton, "filterButton"):
            button.setStyleSheet(self._filter_button_style())

    def _create_patient_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["Категории АА"])
        table.setMinimumWidth(170)
        table.setMaximumWidth(PATIENT_COLUMN_WIDTH)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.doubleClicked.connect(self._open_patient)
        table.itemSelectionChanged.connect(self._sync_selection_from_patients)
        return table

    def _create_schedule_table(self) -> QTableWidget:
        table = QTableWidget()
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        table.setItemDelegate(ScheduleStatusDelegate(table))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_cell_menu)
        table.itemSelectionChanged.connect(self._sync_selection_from_schedule)
        table.verticalScrollBar().valueChanged.connect(
            self.patient_table.verticalScrollBar().setValue
        )
        self.patient_table.verticalScrollBar().valueChanged.connect(
            table.verticalScrollBar().setValue
        )
        return table

    def _populate_doctor_filter(self):
        selected_dept = (
            self.department_combo.currentData()
            if hasattr(self, "department_combo")
            else ""
        )
        current_doctor = (
            self.doctor_combo.currentData() if hasattr(self, "doctor_combo") else 0
        )
        if self.user.role == User.ROLE_DOCTOR:
            current_doctor = self.user.id

        self.doctor_combo.blockSignals(True)
        self.doctor_combo.clear()
        if self.user.role != User.ROLE_DOCTOR:
            self.doctor_combo.addItem("Все работники", 0)

        doctors = User.get_by_role(User.ROLE_DOCTOR)
        if selected_dept:
            doctors = [doctor for doctor in doctors if doctor.department == selected_dept]
        if self.user.role in (User.ROLE_LEAD, User.ROLE_NURSE):
            doctors = [doctor for doctor in doctors if doctor.department == self.user.department]
        elif self.user.role == User.ROLE_DOCTOR:
            doctors = [doctor for doctor in doctors if doctor.id == self.user.id]

        for doctor in doctors:
            self.doctor_combo.addItem(doctor.full_name or doctor.username, doctor.id)

        index = self.doctor_combo.findData(current_doctor)
        self.doctor_combo.setCurrentIndex(index if index >= 0 else 0)
        self.doctor_combo.setEnabled(self.user.role != User.ROLE_DOCTOR)
        self.doctor_combo.blockSignals(False)
        self.doctor_filter = self.doctor_combo.currentData() or 0

    def _load_data(self):
        self.doctor_filter = self.doctor_combo.currentData() or 0
        self.selected_month = self.month_combo.currentData()
        self.selected_year = self.year_combo.currentData()
        self.type_filter = self.type_combo.currentData() or ""
        self.facility_filter = self.facility_combo.currentData() or 0
        self.department_filter = self.department_combo.currentData() or ""
        self.status_filter = self.status_combo.currentData() or ""

        self.schedule = PatientMeetingSchedule.get_for_month(
            self.doctor_filter or None, self.selected_year, self.selected_month
        )
        self.documented_meetings = self._load_documented_meetings()

        self.patients = Patient.get_all(
            user=self.user,
            include_inactive=False,
            patient_type=self.type_filter,
            facility_id=self.facility_filter,
        )

        if self.department_filter:
            self.patients = [
                patient for patient in self.patients if patient.department == self.department_filter
            ]
        if self.doctor_filter:
            doctor_activity_patient_ids = self._doctor_activity_patient_ids()
            self.patients = [
                patient
                for patient in self.patients
                if patient.doctor_id == self.doctor_filter
                or patient.id in doctor_activity_patient_ids
            ]
        if self.current_filter:
            search = self.current_filter.lower()
            self.patients = [
                patient
                for patient in self.patients
                if (patient.callsign and patient.callsign.lower().startswith(search))
                or (
                    patient.personal_number
                    and patient.personal_number.lower().startswith(search)
                )
                or (patient.document_id and patient.document_id.lower().startswith(search))
            ]
        if self.status_filter:
            self.patients = self._filter_patients_by_status(self.patients)

        self._render_tables()

    def _doctor_activity_patient_ids(self) -> set[int]:
        return {patient_id for patient_id, _ in self.schedule.keys()}

    def _filter_patients_by_status(self, patients: list[Patient]) -> list[Patient]:
        result = []
        days_in_month = calendar.monthrange(self.selected_year, self.selected_month)[1]
        month_dates = [
            date(self.selected_year, self.selected_month, day)
            for day in range(1, days_in_month + 1)
        ]
        for patient in patients:
            statuses = [
                self.schedule.get((patient.id, meeting_date)).status
                for meeting_date in month_dates
                if self.schedule.get((patient.id, meeting_date))
            ]
            has_documented_meetings = any(
                (patient.id, meeting_date) in self.documented_meetings
                for meeting_date in month_dates
            )
            if self.status_filter == "EMPTY" and not statuses and not has_documented_meetings:
                result.append(patient)
            elif self.status_filter in statuses:
                result.append(patient)
        return result

    def _render_tables(self):
        days_in_month = calendar.monthrange(self.selected_year, self.selected_month)[1]
        headers = [str(day) for day in range(1, days_in_month + 1)] + ["Итого"]

        self.patient_table.setRowCount(0)
        self.schedule_table.setRowCount(0)
        self.schedule_table.setColumnCount(days_in_month + 1)
        self.schedule_table.setHorizontalHeaderLabels(headers)

        header = self.schedule_table.horizontalHeader()
        for col in range(days_in_month):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        total_col = days_in_month
        header.setSectionResizeMode(total_col, QHeaderView.ResizeMode.Fixed)
        self.schedule_table.setColumnWidth(total_col, SCHEDULE_TOTAL_COLUMN_WIDTH)

        for patient in self.patients:
            row = self.patient_table.rowCount()
            self.patient_table.insertRow(row)
            self.schedule_table.insertRow(row)
            self.patient_table.setRowHeight(row, SCHEDULE_ROW_HEIGHT)
            self.schedule_table.setRowHeight(row, SCHEDULE_ROW_HEIGHT)

            patient_item = QTableWidgetItem(patient.callsign or "")
            patient_item.setData(Qt.ItemDataRole.UserRole, patient.id)
            patient_item.setToolTip(self._patient_tooltip(patient))
            self.patient_table.setItem(row, 0, patient_item)

            for day in range(1, days_in_month + 1):
                meeting_date = date(self.selected_year, self.selected_month, day)
                item = self._create_schedule_item(patient.id, meeting_date)
                col = day - 1
                self.schedule_table.setItem(row, col, item)
            self.schedule_table.setItem(
                row, total_col, self._create_total_item(patient.id, days_in_month)
            )

        self.count_label.setText(f"Категорий АА: {len(self.patients)}")

    def _create_total_item(self, patient_id: int, days_in_month: int) -> QTableWidgetItem:
        month_dates = [
            date(self.selected_year, self.selected_month, day)
            for day in range(1, days_in_month + 1)
        ]
        completed_count = sum(
            1
            for meeting_date in month_dates
            if (
                self.schedule.get((patient_id, meeting_date))
                and self.schedule[(patient_id, meeting_date)].status
                == PatientMeetingSchedule.STATUS_COMPLETED
            )
        )
        documented_count = sum(
            1
            for meeting_date in month_dates
            if (patient_id, meeting_date) in self.documented_meetings
        )

        item = QTableWidgetItem(f"{completed_count}/{documented_count}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setToolTip(
            f"Исполненных встреч: {completed_count}\n"
            f"Задокументированных встреч: {documented_count}"
        )
        return item

    def _create_schedule_item(self, patient_id: int, meeting_date: date) -> QTableWidgetItem:
        item = QTableWidgetItem("")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setData(Qt.ItemDataRole.UserRole, meeting_date)
        schedule_item = self.schedule.get((patient_id, meeting_date))
        has_documented_meeting = (patient_id, meeting_date) in self.documented_meetings
        tooltip_parts = []

        if schedule_item:
            color = SCHEDULE_STATUS_COLORS.get(schedule_item.status, "#059669")
            item.setData(SCHEDULE_STATUS_COLOR_ROLE, color)
            if schedule_item.status == PatientMeetingSchedule.STATUS_COMPLETED:
                tooltip_parts.append("Исполнено")
            else:
                tooltip_parts.append("Запланировано")

        if has_documented_meeting:
            item.setData(SCHEDULE_DOCUMENTED_ROLE, True)
            tooltip_parts.append("Есть документированная встреча")

        if tooltip_parts:
            item.setToolTip("\n".join(tooltip_parts))
        return item

    def _load_documented_meetings(self) -> set[tuple[int, date]]:
        result: set[tuple[int, date]] = set()
        documents = Document.get_all(self.user)
        for document in documents:
            if document.doc_type != DOCUMENT_TYPE_MEETING or not document.doc_date:
                continue
            if (
                document.doc_date.year != self.selected_year
                or document.doc_date.month != self.selected_month
            ):
                continue
            result.add((document.patient_id, document.doc_date))
        return result

    def _patient_tooltip(self, patient: Patient) -> str:
        lines = [patient.callsign or ""]
        if patient.personal_number:
            lines.append(f"Личный номер: {patient.personal_number}")
        if patient.facility:
            lines.append(f"Место: {patient.facility.name}")
        return "\n".join(lines)

    def _show_cell_menu(self, pos):
        if not self.doctor_filter:
            QMessageBox.information(self, "График встреч", "Сначала выберите работника.")
            return

        row = self.schedule_table.rowAt(pos.y())
        col = self.schedule_table.columnAt(pos.x())
        if row < 0 or col < 0 or row >= len(self.patients):
            return

        patient = self.patients[row]
        meeting_date = date(self.selected_year, self.selected_month, col + 1)

        menu = QMenu(self)
        planned_action = menu.addAction("Запланировано")
        completed_action = menu.addAction("Исполнено")
        clear_action = menu.addAction("Очистить отметку")
        menu.addSeparator()
        open_action = menu.addAction("Открыть карточку категории АА")

        planned_action.triggered.connect(
            lambda: self._set_cell_status(
                patient.id, meeting_date, PatientMeetingSchedule.STATUS_PLANNED
            )
        )
        completed_action.triggered.connect(
            lambda: self._set_cell_status(
                patient.id, meeting_date, PatientMeetingSchedule.STATUS_COMPLETED
            )
        )
        clear_action.triggered.connect(lambda: self._clear_cell(patient.id, meeting_date))
        open_action.triggered.connect(lambda: self._open_patient_by_id(patient.id))

        menu.exec(self.schedule_table.viewport().mapToGlobal(pos))

    def _set_cell_status(self, patient_id: int, meeting_date: date, status: str):
        PatientMeetingSchedule.set_status(
            patient_id=patient_id,
            doctor_id=self.doctor_filter,
            meeting_date=meeting_date,
            status=status,
            created_by_id=self.user.id,
        )
        self._load_data()

    def _clear_cell(self, patient_id: int, meeting_date: date):
        PatientMeetingSchedule.clear(patient_id, self.doctor_filter, meeting_date)
        self._load_data()

    def _sync_selection_from_patients(self):
        if self._syncing_selection:
            return
        row = self.patient_table.currentRow()
        if row < 0:
            return
        self._syncing_selection = True
        self.schedule_table.selectRow(row)
        self._syncing_selection = False

    def _sync_selection_from_schedule(self):
        if self._syncing_selection:
            return
        row = self.schedule_table.currentRow()
        if row < 0:
            return
        self._syncing_selection = True
        self.patient_table.selectRow(row)
        self._syncing_selection = False

    def _on_search_changed(self, text: str):
        self.current_filter = text
        self._load_data()

    def _on_filter_changed(self):
        self._load_data()

    def _on_department_changed(self):
        self.department_filter = self.department_combo.currentData() or ""
        self._populate_doctor_filter()
        self._load_data()

    def _on_month_changed(self):
        self._load_data()

    def _reset_filters(self):
        self.search_input.clear()
        self.month_combo.setCurrentIndex(date.today().month - 1)
        year_index = self.year_combo.findData(date.today().year)
        self.year_combo.setCurrentIndex(year_index if year_index >= 0 else 0)
        if self.department_combo.isEnabled():
            self.department_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.facility_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self._populate_doctor_filter()
        self.current_filter = ""
        self._load_data()

    def _open_patient(self, index):
        if index.row() < 0 or index.row() >= len(self.patients):
            return
        self._open_patient_by_id(self.patients[index.row()].id)

    def _open_patient_by_id(self, patient_id: int):
        from ui.patient_detail import PatientDetailDialog

        dialog = PatientDetailDialog(self.user, patient_id)
        dialog.exec()
        self._load_data()

    def update_styles(self):
        self.setStyleSheet(get_main_stylesheet())
        self._apply_filter_styles()
        self._render_tables()

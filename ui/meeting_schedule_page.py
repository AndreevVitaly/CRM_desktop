"""
Patient meeting schedule page.
"""

import calendar
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.db_models import (
    Facility,
    Patient,
    PatientMeetingSchedule,
    User,
    get_department_choices,
)
from ui.styles import FONTS, RADIUS, get_colors, get_main_stylesheet


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
        splitter.setSizes([340, 900])
        layout.addWidget(splitter, 1)

        bottom_layout = QHBoxLayout()
        self.legend_label = QLabel("● Запланировано   ● Исполнено")
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
        self._load_data()

    def _create_filter_panel(self) -> QFrame:
        colors = get_colors()
        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedHeight(128)
        panel.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 12px;
            }}
            """
        )

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
        self.search_input.textChanged.connect(self._on_search_changed)
        top.addWidget(self.search_input)

        self.month_combo = QComboBox()
        self.month_combo.setFrame(False)
        for label, value in self.MONTHS:
            self.month_combo.addItem(label, value)
        self.month_combo.setCurrentIndex(self.selected_month - 1)
        self.month_combo.setFixedWidth(140)
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        top.addWidget(self.month_combo)

        self.year_combo = QComboBox()
        self.year_combo.setFrame(False)
        for year in range(self.selected_year - 5, self.selected_year + 6):
            self.year_combo.addItem(str(year), year)
        self.year_combo.setCurrentText(str(self.selected_year))
        self.year_combo.setFixedWidth(110)
        self.year_combo.currentIndexChanged.connect(self._on_month_changed)
        top.addWidget(self.year_combo)

        self.department_combo = QComboBox()
        self.department_combo.setFrame(False)
        self.department_combo.addItem("Все отделения", "")
        if self.user.role in (User.ROLE_LEAD, User.ROLE_NURSE):
            self.department_combo.addItem(self.user.department_display, self.user.department)
            self.department_combo.setCurrentIndex(1)
            self.department_combo.setEnabled(False)
        else:
            for dept_code, dept_name in get_department_choices(include_inactive=False):
                self.department_combo.addItem(dept_name, dept_code)
        self.department_combo.setFixedWidth(190)
        self.department_combo.currentIndexChanged.connect(self._on_department_changed)
        top.addWidget(self.department_combo)

        self.doctor_combo = QComboBox()
        self.doctor_combo.setFrame(False)
        self.doctor_combo.setFixedWidth(220)
        self.doctor_combo.currentIndexChanged.connect(self._on_filter_changed)
        top.addWidget(self.doctor_combo)
        self._populate_doctor_filter()

        top.addStretch()

        self.type_combo = QComboBox()
        self.type_combo.setFrame(False)
        self.type_combo.addItem("Все типы", "")
        self.type_combo.addItem("Взрослые", "adult")
        self.type_combo.addItem("Дети", "child")
        self.type_combo.addItem("Неопределенные", "undefined")
        self.type_combo.setFixedWidth(150)
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        bottom.addWidget(self.type_combo)

        self.facility_combo = QComboBox()
        self.facility_combo.setFrame(False)
        self.facility_combo.addItem("Все места", 0)
        for facility in Facility.get_all():
            self.facility_combo.addItem(facility.name, facility.id)
        self.facility_combo.setFixedWidth(210)
        self.facility_combo.currentIndexChanged.connect(self._on_filter_changed)
        bottom.addWidget(self.facility_combo)

        self.status_combo = QComboBox()
        self.status_combo.setFrame(False)
        self.status_combo.addItem("Все отметки", "")
        self.status_combo.addItem("Запланировано", PatientMeetingSchedule.STATUS_PLANNED)
        self.status_combo.addItem("Исполнено", PatientMeetingSchedule.STATUS_COMPLETED)
        self.status_combo.addItem("Без отметок", "EMPTY")
        self.status_combo.setFixedWidth(170)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        bottom.addWidget(self.status_combo)

        reset_btn = QPushButton("Сброс")
        reset_btn.setObjectName("actionButton")
        reset_btn.setFixedHeight(36)
        reset_btn.clicked.connect(self._reset_filters)
        bottom.addWidget(reset_btn)
        bottom.addStretch()

        layout.addLayout(top)
        layout.addLayout(bottom)
        return panel

    def _create_patient_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["Пациенты"])
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
            self.doctor_combo.addItem("Выберите врача", 0)

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
        if current_doctor == 0 and self.doctor_combo.count() > 1:
            index = 1
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

        self.schedule = {}
        if self.doctor_filter:
            self.schedule = PatientMeetingSchedule.get_for_month(
                self.doctor_filter, self.selected_year, self.selected_month
            )

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
            self.patients = [
                patient for patient in self.patients if patient.doctor_id == self.doctor_filter
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
            if self.status_filter == "EMPTY" and not statuses:
                result.append(patient)
            elif self.status_filter in statuses:
                result.append(patient)
        return result

    def _render_tables(self):
        days_in_month = calendar.monthrange(self.selected_year, self.selected_month)[1]
        headers = [str(day) for day in range(1, days_in_month + 1)]

        self.patient_table.setRowCount(0)
        self.schedule_table.setRowCount(0)
        self.schedule_table.setColumnCount(days_in_month)
        self.schedule_table.setHorizontalHeaderLabels(headers)

        for col in range(days_in_month):
            self.schedule_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.Fixed
            )
            self.schedule_table.setColumnWidth(col, 44)

        for patient in self.patients:
            row = self.patient_table.rowCount()
            self.patient_table.insertRow(row)
            self.schedule_table.insertRow(row)
            self.patient_table.setRowHeight(row, 34)
            self.schedule_table.setRowHeight(row, 34)

            patient_item = QTableWidgetItem(patient.callsign or "")
            patient_item.setData(Qt.ItemDataRole.UserRole, patient.id)
            patient_item.setToolTip(self._patient_tooltip(patient))
            self.patient_table.setItem(row, 0, patient_item)

            for day in range(1, days_in_month + 1):
                meeting_date = date(self.selected_year, self.selected_month, day)
                item = self._create_schedule_item(patient.id, meeting_date)
                self.schedule_table.setItem(row, day - 1, item)

        self.count_label.setText(f"Пациентов: {len(self.patients)}")

    def _create_schedule_item(self, patient_id: int, meeting_date: date) -> QTableWidgetItem:
        item = QTableWidgetItem("")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setData(Qt.ItemDataRole.UserRole, meeting_date)
        schedule_item = self.schedule.get((patient_id, meeting_date))
        if not schedule_item:
            return item

        item.setText("●")
        if schedule_item.status == PatientMeetingSchedule.STATUS_COMPLETED:
            item.setForeground(QBrush(QColor("#2563EB")))
            item.setToolTip("Исполнено")
        else:
            item.setForeground(QBrush(QColor("#059669")))
            item.setToolTip("Запланировано")
        return item

    def _patient_tooltip(self, patient: Patient) -> str:
        lines = [patient.callsign or ""]
        if patient.personal_number:
            lines.append(f"Личный номер: {patient.personal_number}")
        if patient.facility:
            lines.append(f"Место: {patient.facility.name}")
        return "\n".join(lines)

    def _show_cell_menu(self, pos):
        if not self.doctor_filter:
            QMessageBox.information(self, "График встреч", "Сначала выберите врача.")
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
        open_action = menu.addAction("Открыть карточку пациента")

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
        self._render_tables()

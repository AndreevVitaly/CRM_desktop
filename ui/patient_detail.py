"""
Детальная карточка пациента
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QDateEdit,
    QTimeEdit,
    QSpinBox,
    QGroupBox,
    QGridLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont

from models.db_models import (
    User,
    Patient,
    Encounter,
    Note,
    Prescription,
    Diagnosis,
    TreatmentPlanItem,
    PatientInteraction,
    Facility,
    DEPARTMENTS,
    Document,
    DOCUMENT_CLASSIFICATION_CHOICES,
)
from ui.styles import get_colors, FONTS, RADIUS


class PatientDetailDialog(QDialog):
    """Диалог детальной информации о пациенте"""

    def __init__(self, user: User, patient_id: int):
        super().__init__()
        self.user = user
        self.patient = Patient.get_by_id(patient_id)
        self.setWindowTitle(f"Пациент: {self.patient.full_name}")
        self.setMinimumSize(1000, 700)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        try:
            colors = get_colors()

            layout = QVBoxLayout()
            layout.setSpacing(16)
            layout.setContentsMargins(20, 20, 20, 20)

            # Заголовок
            header = self._create_header()
            layout.addWidget(header)

            # Вкладки
            tabs = QTabWidget()
            tabs.addTab(self._create_info_tab(), "Информация")
            tabs.addTab(self._create_encounters_tab(), "Визиты")
            tabs.addTab(self._create_plan_tab(), "План лечения")
            tabs.addTab(self._create_documents_tab(), "Документы")
            tabs.addTab(self._create_log_tab(), "Журнал")

            layout.addWidget(tabs, 1)

            # Кнопки
            buttons_layout = QHBoxLayout()
            buttons_layout.addStretch()

            if self.user.role in (User.ROLE_REGISTRAR, User.ROLE_LEAD):
                edit_btn = QPushButton("Редактировать")
                edit_btn.setObjectName("secondaryBtn")
                edit_btn.setFixedHeight(40)
                edit_btn.clicked.connect(self._edit_patient)
                buttons_layout.addWidget(edit_btn)

            close_btn = QPushButton("Закрыть")
            close_btn.setObjectName("secondaryBtn")
            close_btn.setFixedHeight(40)
            close_btn.clicked.connect(self.accept)
            buttons_layout.addWidget(close_btn)

            layout.addLayout(buttons_layout)

            self.setLayout(layout)
            self.setStyleSheet(
                f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
            )
        except Exception as e:
            import traceback

            error_msg = (
                f"Ошибка при создании интерфейса:\n{str(e)}\n\n{traceback.format_exc()}"
            )
            print(error_msg)
            QMessageBox.critical(None, "Ошибка", error_msg)
            raise

    def _create_header(self) -> QFrame:
        """Заголовок с информацией о пациенте"""
        colors = get_colors()

        header = QFrame()
        header.setObjectName("card")
        header.setFixedHeight(100)
        header.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 16px;
            }}
        """
        )

        layout = QHBoxLayout(header)

        # Информация
        info_layout = QVBoxLayout()

        name_label = QLabel(self.patient.full_name)
        name_label.setStyleSheet(
            f"font-size: {FONTS['size_xlarge']}pt; font-weight: bold; color: {colors['text']}; background-color: transparent;"
        )
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        info_layout.addWidget(name_label)

        details = f"{self.patient.age} лет • {'Мужской' if self.patient.gender == 'M' else 'Женский'}"
        details += f" • {self.patient.department_display}"
        if self.patient.doctor:
            details += f" • Врач: {self.patient.doctor.full_name}"

        details_label = QLabel(details)
        details_label.setObjectName("muted")
        details_label.setStyleSheet(
            f"color: {colors['text_muted']}; background-color: transparent;"
        )
        details_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        info_layout.addWidget(details_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Статус
        status_label = QLabel("Активен" if self.patient.is_active else "Скрыт")
        status_label.setStyleSheet(
            f"""
            font-weight: bold;
            color: {colors['success'] if self.patient.is_active else colors['warning']};
            background-color: transparent;
        """
        )
        status_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(status_label)

        return header

    def _create_info_tab(self) -> QWidget:
        """Вкладка информации"""
        colors = get_colors()

        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Скролл для контента
        from PyQt6.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content_widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        row = 0

        # Личные данные (левая колонка)
        fields = [
            (
                "Тип пациента:",
                {
                    "adult": "Взрослый",
                    "child": "Детский",
                    "undefined": "Неопределённый",
                }.get(self.patient.patient_type, "—"),
            ),
            ("Позывной:", self.patient.callsign or "—"),
            ("Личный номер:", self.patient.personal_number or "—"),
            ("Дата рождения:", self.patient.birth_date.strftime("%d.%m.%Y")),
            ("Возраст:", f"{self.patient.age} лет"),
            (
                "Пол:",
                {"M": "Мужской", "F": "Женский"}.get(self.patient.gender, "—"),
            ),
            ("Отделение:", self.patient.department_display or "—"),
            (
                "Лечащий врач:",
                self.patient.doctor.full_name if self.patient.doctor else "Не назначен",
            ),
        ]

        for label, value in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; background-color: transparent;")
            layout.addWidget(lbl, row, 0)

            val = QLabel(value)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            val.setStyleSheet(
                f"color: {colors['text']}; background-color: transparent;"
            )
            layout.addWidget(val, row, 1)
            row += 1

        # Контакты (правая колонка)
        row_contacts = 0
        col = 2
        contact_fields = [
            ("Телефон:", self.patient.phone or "—"),
            ("Email:", self.patient.email or "—"),
            ("Адрес:", self.patient.address or "—"),
            ("Контакт для связи:", self.patient.emergency_contact or "—"),
        ]

        for label, value in contact_fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; background-color: transparent;")
            layout.addWidget(lbl, row_contacts, col)

            val = QLabel(value)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            val.setStyleSheet(
                f"color: {colors['text']}; background-color: transparent;"
            )
            layout.addWidget(val, row_contacts, col + 1)
            row_contacts += 1

        # Документы и место размещения (продолжение левой колонки)
        row = len(fields)
        doc_fields = [
            ("Полис ОМС:", self.patient.insurance_number or "—"),
            ("Место работы:", self.patient.employer or "—"),
        ]

        for label, value in doc_fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; background-color: transparent;")
            layout.addWidget(lbl, row, 0)

            val = QLabel(value)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            val.setStyleSheet(
                f"color: {colors['text']}; background-color: transparent;"
            )
            layout.addWidget(val, row, 1)
            row += 1

        # Место размещения
        if self.patient.facility:
            facility_text = (
                f"{self.patient.facility.name} ({self.patient.facility.type_display})"
            )
            lbl = QLabel("Место размещения:")
            lbl.setStyleSheet("font-weight: bold; background-color: transparent;")
            layout.addWidget(lbl, row, 0)

            val = QLabel(facility_text)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            val.setStyleSheet(
                f"color: {colors['text']}; background-color: transparent;"
            )
            layout.addWidget(val, row, 1)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        # Новая строка для документов
        row = max(row, row_contacts)

        # Справка об изучении
        row += 1
        study_group = QGroupBox("Справка об изучении")
        study_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid """
            + colors["line"]
            + """;
                border-radius: """
            + str(RADIUS["md"])
            + """px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """
        )
        study_layout = QGridLayout()
        study_layout.setSpacing(8)
        study_layout.setContentsMargins(12, 16, 12, 12)

        study_layout.addWidget(QLabel("Номер дела:"), 0, 0)
        study_case_label = QLabel(self.patient.study_case_number or "—")
        study_case_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        study_case_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        study_layout.addWidget(study_case_label, 0, 1)

        study_layout.addWidget(QLabel("Номера листов:"), 1, 0)
        study_sheets_label = QLabel(self.patient.study_sheet_numbers or "—")
        study_sheets_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        study_sheets_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        study_layout.addWidget(study_sheets_label, 1, 1)

        study_group.setLayout(study_layout)
        layout.addWidget(study_group, row, 0, 1, 4)

        # Рапорт на поступление
        row += 1
        admission_group = QGroupBox("Рапорт на поступление")
        admission_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid """
            + colors["line"]
            + """;
                border-radius: """
            + str(RADIUS["md"])
            + """px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """
        )
        admission_layout = QGridLayout()
        admission_layout.setSpacing(8)
        admission_layout.setContentsMargins(12, 16, 12, 12)

        admission_layout.addWidget(QLabel("Номер документа:"), 0, 0)
        admission_number_label = QLabel(self.patient.admission_report_number or "—")
        admission_number_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        admission_number_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        admission_layout.addWidget(admission_number_label, 0, 1)

        admission_layout.addWidget(QLabel("Дата документа:"), 1, 0)
        admission_date_label = QLabel(
            self.patient.admission_report_date.strftime("%d.%m.%Y")
            if self.patient.admission_report_date
            else "—"
        )
        admission_date_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        admission_date_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        admission_layout.addWidget(admission_date_label, 1, 1)

        admission_layout.addWidget(QLabel("Дата санкции:"), 2, 0)
        admission_sanction_label = QLabel(
            self.patient.admission_sanction_date.strftime("%d.%m.%Y")
            if self.patient.admission_sanction_date
            else "—"
        )
        admission_sanction_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        admission_sanction_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        admission_layout.addWidget(admission_sanction_label, 2, 1)

        admission_group.setLayout(admission_layout)
        layout.addWidget(admission_group, row, 0, 1, 4)

        # Рапорт о поступлении
        row += 1
        arrival_group = QGroupBox("Рапорт о поступлении")
        arrival_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid """
            + colors["line"]
            + """;
                border-radius: """
            + str(RADIUS["md"])
            + """px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """
        )
        arrival_layout = QGridLayout()
        arrival_layout.setSpacing(8)
        arrival_layout.setContentsMargins(12, 16, 12, 12)

        arrival_layout.addWidget(QLabel("Номер документа:"), 0, 0)
        arrival_number_label = QLabel(self.patient.arrival_report_number or "—")
        arrival_number_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        arrival_number_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        arrival_layout.addWidget(arrival_number_label, 0, 1)

        arrival_layout.addWidget(QLabel("Дата документа:"), 1, 0)
        arrival_date_label = QLabel(
            self.patient.arrival_report_date.strftime("%d.%m.%Y")
            if self.patient.arrival_report_date
            else "—"
        )
        arrival_date_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        arrival_date_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        arrival_layout.addWidget(arrival_date_label, 1, 1)

        arrival_layout.addWidget(QLabel("Дата санкции:"), 2, 0)
        arrival_sanction_label = QLabel(
            self.patient.arrival_sanction_date.strftime("%d.%m.%Y")
            if self.patient.arrival_sanction_date
            else "—"
        )
        arrival_sanction_label.setStyleSheet(
            f"color: {colors['text']}; background-color: transparent;"
        )
        arrival_sanction_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        arrival_layout.addWidget(arrival_sanction_label, 2, 1)

        arrival_group.setLayout(arrival_layout)
        layout.addWidget(arrival_group, row, 0, 1, 4)

        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        widget.setLayout(main_layout)
        return widget

    def _create_encounters_tab(self) -> QWidget:
        """Вкладка визитов"""
        colors = get_colors()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Кнопка добавления визита
        if self.user.role in (
            User.ROLE_ADMIN,
            User.ROLE_REGISTRAR,
            User.ROLE_LEAD,
            User.ROLE_DOCTOR,
            User.ROLE_NURSE,
        ):
            add_btn = QPushButton("Добавить визит")
            add_btn.setFixedHeight(36)
            add_btn.clicked.connect(self._add_encounter)
            layout.addWidget(add_btn)

        # Таблица визитов
        self.encounters_table = QTableWidget()
        self.encounters_table.setColumnCount(5)
        self.encounters_table.setHorizontalHeaderLabels(
            ["Дата", "Врач", "Причина", "Статус", "Заметки"]
        )

        header = self.encounters_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.encounters_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.encounters_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.encounters_table.verticalHeader().setVisible(False)
        self.encounters_table.setShowGrid(False)
        self.encounters_table.doubleClicked.connect(self._open_encounter)

        layout.addWidget(self.encounters_table, 1)

        self._load_encounters()

        widget.setLayout(layout)
        return widget

    def _load_encounters(self):
        """Загрузка визитов"""
        self.encounters_table.setRowCount(0)
        encounters = Encounter.get_by_patient(self.patient.id)

        for encounter in encounters:
            row = self.encounters_table.rowCount()
            self.encounters_table.insertRow(row)

            date_str = encounter.started_at.strftime("%d.%m.%Y %H:%M")
            self.encounters_table.setItem(row, 0, QTableWidgetItem(date_str))

            doctor_name = encounter.doctor.full_name if encounter.doctor else "—"
            self.encounters_table.setItem(row, 1, QTableWidgetItem(doctor_name))

            self.encounters_table.setItem(
                row, 2, QTableWidgetItem(encounter.reason or "—")
            )

            status_item = QTableWidgetItem(encounter.status_display)
            status_item.setForeground(
                Qt.GlobalColor.darkGreen
                if encounter.status == Encounter.STATUS_FINISHED
                else Qt.GlobalColor.darkBlue
            )
            self.encounters_table.setItem(row, 3, status_item)

            notes_count = len(Note.get_by_encounter(encounter.id))
            rx_count = len(Prescription.get_by_encounter(encounter.id))
            notes_info = f"Заметки: {notes_count}" if notes_count else ""
            if rx_count:
                notes_info += (
                    f", Назначения: {rx_count}"
                    if notes_info
                    else f"Назначения: {rx_count}"
                )
            self.encounters_table.setItem(row, 4, QTableWidgetItem(notes_info or "—"))

    def _create_plan_tab(self) -> QWidget:
        """Вкладка плана лечения"""
        colors = get_colors()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Кнопка добавления пункта
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            add_btn = QPushButton("Добавить пункт плана")
            add_btn.setFixedHeight(36)
            add_btn.clicked.connect(self._add_plan_item)
            layout.addWidget(add_btn)

        # Таблица пунктов плана
        self.plan_table = QTableWidget()
        self.plan_table.setColumnCount(4)
        self.plan_table.setHorizontalHeaderLabels(
            ["✓", "Мероприятие", "Срок исполнения", "Статус"]
        )

        header = self.plan_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.plan_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plan_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plan_table.verticalHeader().setVisible(False)
        self.plan_table.setShowGrid(False)

        layout.addWidget(self.plan_table)

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)

        toggle_btn = QPushButton("Переключить статус")
        toggle_btn.setObjectName("secondaryBtn")
        toggle_btn.setFixedHeight(36)
        toggle_btn.clicked.connect(self._toggle_plan_item)
        buttons_layout.addWidget(toggle_btn)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("dangerBtn")
            delete_btn.setFixedHeight(36)
            delete_btn.clicked.connect(self._delete_plan_item)
            buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self._load_plan_items()

        widget.setLayout(layout)
        return widget

    def _load_plan_items(self):
        """Загрузка пунктов плана"""
        self.plan_table.setRowCount(0)
        plan_items = TreatmentPlanItem.get_by_patient(self.patient.id)

        for item in plan_items:
            row = self.plan_table.rowCount()
            self.plan_table.insertRow(row)

            # Чекбокс
            check_item = QTableWidgetItem("✓" if item.is_completed else "")
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.plan_table.setItem(row, 0, check_item)

            # Мероприятие
            self.plan_table.setItem(row, 1, QTableWidgetItem(item.event))

            # Срок
            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            self.plan_table.setItem(row, 2, QTableWidgetItem(due_date))

            # Статус
            status = "Выполнено" if item.is_completed else "В ожидании"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                Qt.GlobalColor.darkGreen
                if item.is_completed
                else Qt.GlobalColor.darkBlue
            )
            self.plan_table.setItem(row, 3, status_item)

    def _create_documents_tab(self) -> QWidget:
        """Вкладка документов"""
        colors = get_colors()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Кнопка добавления документа
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_REGISTRAR):
            add_btn = QPushButton("Добавить документ")
            add_btn.setFixedHeight(36)
            add_btn.clicked.connect(self._add_document)
            layout.addWidget(add_btn)

        # Таблица документов
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(6)
        self.documents_table.setHorizontalHeaderLabels(
            [
                "№",
                "Гриф",
                "Дата",
                "Вид документа",
                "Краткое содержание",
                "Куда приобщён",
            ]
        )

        header = self.documents_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.documents_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.documents_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.documents_table.verticalHeader().setVisible(False)
        self.documents_table.setShowGrid(False)
        self.documents_table.doubleClicked.connect(self._open_document)

        layout.addWidget(self.documents_table, 1)

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_REGISTRAR):
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("dangerBtn")
            delete_btn.setFixedHeight(36)
            delete_btn.clicked.connect(self._delete_document)
            buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self._load_documents()

        widget.setLayout(layout)
        return widget

    def _load_documents(self):
        """Загрузка документов"""
        try:
            self.documents_table.setRowCount(0)
            documents = Document.get_by_patient(self.patient.id)

            for doc in documents:
                row = self.documents_table.rowCount()
                self.documents_table.insertRow(row)

                # Номер по порядку
                self.documents_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

                # Гриф секретности
                class_item = QTableWidgetItem(doc.classification_display)
                class_item.setForeground(
                    Qt.GlobalColor.darkRed
                    if doc.classification in ("S", "SS")
                    else Qt.GlobalColor.darkBlue
                )
                self.documents_table.setItem(row, 1, class_item)

                # Дата
                date_str = doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"
                self.documents_table.setItem(row, 2, QTableWidgetItem(date_str))

                # Вид документа
                self.documents_table.setItem(
                    row, 3, QTableWidgetItem(doc.doc_type or "—")
                )

                # Краткое содержание
                self.documents_table.setItem(
                    row, 4, QTableWidgetItem(doc.summary or "—")
                )

                # Куда приобщён
                self.documents_table.setItem(
                    row, 5, QTableWidgetItem(doc.location or "—")
                )
        except Exception as e:
            import traceback

            print(f"Ошибка при загрузке документов: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(
                self, "Ошибка", f"Не удалось загрузить документы: {str(e)}"
            )

    def _add_document(self):
        """Добавление документа"""
        from ui.document_form import DocumentFormDialog

        dialog = DocumentFormDialog(self.user, self.patient, None)
        if dialog.exec():
            self._load_documents()
            self._log_interaction("document_add", "Добавлен документ")

    def _open_document(self, index):
        """Открытие документа"""
        selected = self.documents_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        documents = Document.get_by_patient(self.patient.id)
        if row >= len(documents):
            return

        doc = documents[row]

        # Диалог просмотра документа
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QFrame,
            QPushButton,
            QFormLayout,
        )
        from PyQt6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Документ №{doc.id}")
        dialog.setMinimumSize(600, 400)

        colors = get_colors()
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel(f"Документ №{doc.id}")
        title.setStyleSheet(f"font-size: {FONTS['size_title']}pt; font-weight: bold;")
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(title)

        # Информация о документе
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors['surface_muted']};
                border-radius: {RADIUS['md']}px;
                padding: 12px;
            }}
        """
        )
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(8)

        fields = [
            ("Номер по порядку:", str(doc.id)),
            ("Гриф секретности:", doc.classification_display),
            ("Дата:", doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"),
            ("Автор:", doc.author.full_name if doc.author else "—"),
            ("Вид документа:", doc.doc_type or "—"),
            ("Краткое содержание:", doc.summary or "—"),
            ("Куда приобщён:", doc.location or "—"),
            ("Личный номер пациента:", doc.patient_personal_number or "—"),
        ]

        for label, value in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {colors['text']};")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            info_layout.addRow(lbl, val)

        layout.addWidget(info_frame)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondaryBtn")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )
        dialog.exec()

    def _delete_document(self):
        """Удаление документа"""
        selected = self.documents_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите документ")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранный документ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            documents = Document.get_by_patient(self.patient.id)
            if row < len(documents):
                doc = documents[row]
                doc.delete()
                self._load_documents()
                self._log_interaction("document_delete", f"Удалён документ №{doc.id}")

    def _create_log_tab(self) -> QWidget:
        """Вкладка журнала взаимодействий"""
        colors = get_colors()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Таблица лога
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(
            ["Дата", "Действие", "Пользователь", "Описание"]
        )

        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setShowGrid(False)

        layout.addWidget(self.log_table, 1)

        self._load_log()

        widget.setLayout(layout)
        return widget

    def _load_log(self):
        """Загрузка журнала"""
        self.log_table.setRowCount(0)
        interactions = PatientInteraction.get_by_patient(self.patient.id)

        for interaction in interactions:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)

            date_str = interaction.created_at.strftime("%d.%m.%Y %H:%M")
            self.log_table.setItem(row, 0, QTableWidgetItem(date_str))

            self.log_table.setItem(row, 1, QTableWidgetItem(interaction.action_display))

            user_name = interaction.user.full_name if interaction.user else "—"
            self.log_table.setItem(row, 2, QTableWidgetItem(user_name))

            self.log_table.setItem(
                row, 3, QTableWidgetItem(interaction.description or "—")
            )

    def _add_encounter(self):
        """Добавление визита"""
        from ui.encounter_form import EncounterFormDialog

        dialog = EncounterFormDialog(self.user, self.patient, None)
        if dialog.exec():
            self._load_encounters()
            self._log_interaction("visit_created", "Создан новый визит")

    def _open_encounter(self, index):
        """Открытие визита"""
        selected = self.encounters_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите визит")
            return

        row = selected[0].row()
        encounters = Encounter.get_by_patient(self.patient.id)
        if row >= len(encounters):
            return

        encounter = encounters[row]

        # Диалог просмотра визита
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QFrame,
            QPushButton,
            QTextEdit,
            QFormLayout,
        )
        from PyQt6.QtCore import Qt
        from datetime import datetime

        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Визит от {encounter.started_at.strftime('%d.%m.%Y %H:%M')}"
        )
        dialog.setMinimumSize(600, 500)

        colors = get_colors()
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel(f"Визит пациента")
        title.setStyleSheet(f"font-size: {FONTS['size_title']}pt; font-weight: bold;")
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(title)

        # Информация о визите
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors['surface_muted']};
                border-radius: {RADIUS['md']}px;
                padding: 12px;
            }}
        """
        )
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(8)

        date_val = QLabel(encounter.started_at.strftime("%d.%m.%Y %H:%M"))
        date_val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        doctor_val = QLabel(encounter.doctor.full_name if encounter.doctor else "—")
        doctor_val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        reason_val = QLabel(encounter.reason or "—")
        reason_val.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        info_layout.addRow("Дата:", date_val)
        info_layout.addRow("Врач:", doctor_val)
        info_layout.addRow("Причина:", reason_val)

        status_label = QLabel(encounter.status_display)
        status_label.setStyleSheet(
            "font-weight: bold; color: {};".format(
                colors["success"]
                if encounter.status == Encounter.STATUS_FINISHED
                else colors["warning"]
            )
        )
        status_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        info_layout.addRow("Статус:", status_label)

        layout.addWidget(info_frame)

        # Заметки
        notes_label = QLabel("Заметки:")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        notes_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(notes_label)

        notes = Note.get_by_encounter(encounter.id)
        if notes:
            for note in notes:
                note_frame = QFrame()
                note_frame.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: {colors['surface']};
                        border: 1px solid {colors['line']};
                        border-radius: {RADIUS['sm']}px;
                        padding: 8px;
                    }}
                """
                )
                note_layout = QVBoxLayout(note_frame)

                note_header = QLabel(
                    f"<b>{note.author.full_name}</b> • {note.created_at.strftime('%d.%m.%Y %H:%M') if note.created_at else ''}"
                )
                note_header.setStyleSheet(
                    "color: {}; font-size: {}pt;".format(
                        colors["text_muted"], FONTS["size_small"]
                    )
                )
                note_header.setTextInteractionFlags(
                    Qt.TextInteractionFlag.NoTextInteraction
                )
                note_layout.addWidget(note_header)

                note_text = QLabel(note.text)
                note_text.setWordWrap(True)
                note_text.setStyleSheet(f"color: {colors['text']};")
                note_text.setTextInteractionFlags(
                    Qt.TextInteractionFlag.NoTextInteraction
                )
                note_layout.addWidget(note_text)

                layout.addWidget(note_frame)
        else:
            no_notes = QLabel("Нет заметок")
            no_notes.setObjectName("muted")
            no_notes.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            layout.addWidget(no_notes)

        # Назначения
        rx_label = QLabel("Назначения:")
        rx_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        rx_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(rx_label)

        prescriptions = Prescription.get_by_encounter(encounter.id)
        if prescriptions:
            for rx in prescriptions:
                rx_frame = QFrame()
                rx_frame.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: {colors['surface']};
                        border: 1px solid {colors['line']};
                        border-radius: {RADIUS['sm']}px;
                        padding: 8px;
                    }}
                """
                )
                rx_layout = QVBoxLayout(rx_frame)

                rx_title = QLabel(f"<b>{rx.medication}</b> ({rx.dosage})")
                rx_title.setStyleSheet(f"color: {colors['accent']};")
                rx_title.setTextInteractionFlags(
                    Qt.TextInteractionFlag.NoTextInteraction
                )
                rx_layout.addWidget(rx_title)

                rx_details = QLabel(
                    f"Частота: {rx.frequency} • Длительность: {rx.duration_days} дн."
                )
                rx_details.setObjectName("muted")
                rx_details.setTextInteractionFlags(
                    Qt.TextInteractionFlag.NoTextInteraction
                )
                rx_layout.addWidget(rx_details)

                if rx.notes:
                    rx_notes = QLabel(rx.notes)
                    rx_notes.setObjectName("muted")
                    rx_notes.setTextInteractionFlags(
                        Qt.TextInteractionFlag.NoTextInteraction
                    )
                    rx_layout.addWidget(rx_notes)

                layout.addWidget(rx_frame)
        else:
            no_rx = QLabel("Нет назначений")
            no_rx.setObjectName("muted")
            no_rx.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            layout.addWidget(no_rx)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("secondaryBtn")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Устанавливаем layout через виджет
        content_widget = QWidget()
        content_widget.setLayout(layout)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(content_widget)

        dialog.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )
        dialog.exec()

    def _add_plan_item(self):
        """Добавление пункта плана"""
        from ui.plan_item_form import PlanItemFormDialog

        dialog = PlanItemFormDialog(self.user, self.patient, None)
        if dialog.exec():
            self._load_plan_items()
            self._log_interaction("plan_item_add", "Добавлен пункт плана лечения")

    def _toggle_plan_item(self):
        """Переключение статуса пункта плана"""
        selected = self.plan_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите пункт плана")
            return

        row = selected[0].row()
        plan_items = TreatmentPlanItem.get_by_patient(self.patient.id)
        if row < len(plan_items):
            item = plan_items[row]
            item.toggle()
            self._load_plan_items()
            self._log_interaction(
                "plan_item_toggle",
                f"{'Выполнен' if item.is_completed else 'Отменён'} пункт: {item.event}",
            )

    def _delete_plan_item(self):
        """Удаление пункта плана"""
        selected = self.plan_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите пункт плана")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранный пункт плана?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            plan_items = TreatmentPlanItem.get_by_patient(self.patient.id)
            if row < len(plan_items):
                item = plan_items[row]
                item.delete()
                self._load_plan_items()
                self._log_interaction("plan_item_delete", f"Удалён пункт: {item.event}")

    def _edit_patient(self):
        """Редактирование пациента"""
        from ui.patient_form import PatientFormDialog

        dialog = PatientFormDialog(self.user, self.patient)
        if dialog.exec():
            self.patient = Patient.get_by_id(self.patient.id)
            self._init_ui()

    def _log_interaction(self, action: str, description: str):
        """Логирование взаимодействия"""
        interaction = PatientInteraction(
            patient_id=self.patient.id,
            user_id=self.user.id,
            action=action,
            description=description,
        )
        interaction.save()

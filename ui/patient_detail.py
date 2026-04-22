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
    QMenu,
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QCursor
from datetime import datetime

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
    DOCUMENT_TYPE_PLAN,
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
        self.showMaximized()

    def _init_ui(self):
        """Инициализация интерфейса"""
        try:
            colors = get_colors()
            self._colors = colors

            layout = QVBoxLayout()
            layout.setSpacing(16)
            layout.setContentsMargins(20, 20, 20, 20)

            # Заголовок
            header = self._create_header()
            layout.addWidget(header)

            # Вкладки
            self.tabs = QTabWidget()
            self.tabs.addTab(self._create_info_tab(), "Информация")
            self.tabs.addTab(self._create_encounters_tab(), "Встречи")
            self.plan_tab_index = 2  # Индекс вкладки "План лечения"
            self.tabs.addTab(self._create_plan_tab(), "План лечения")
            self.tabs.addTab(self._create_documents_tab(), "Документы")
            self.tabs.addTab(self._create_log_tab(), "Журнал")

            layout.addWidget(self.tabs, 1)

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

    def _get_status_color(self, is_completed):
        """Получить цвет статуса выполнения"""
        if is_completed:
            return Qt.GlobalColor.darkGreen
        # Для "В ожидании" — цвет текста текущей темы
        from PyQt6.QtGui import QColor

        text_color = self._colors.get("text", Qt.GlobalColor.black)
        return QColor(text_color)

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
        """Вкладка встреч"""
        colors = get_colors()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Таблица встреч
        self.encounters_table = QTableWidget()
        self.encounters_table.setColumnCount(8)
        self.encounters_table.setHorizontalHeaderLabels(
            [
                "Дата",
                "Врач",
                "Результат",
                "Причина",
                "Статус",
                "Информация",
                "Документ",
                "Заметки",
            ]
        )

        header = self.encounters_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.encounters_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.encounters_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.encounters_table.verticalHeader().setVisible(False)
        self.encounters_table.setShowGrid(False)
        self.encounters_table.doubleClicked.connect(self._edit_encounter)

        layout.addWidget(self.encounters_table, 1)

        self._load_encounters()

        widget.setLayout(layout)
        return widget

    def _load_encounters(self):
        """Загрузка встреч из документов типа "Встреча" с данными из Encounter"""
        self.encounters_table.setRowCount(0)

        from models.db_models import Document, DOCUMENT_TYPE_MEETING, Encounter

        # Получаем все документы типа "Встреча" пациента
        documents = Document.get_by_patient(self.patient.id)
        encounter_docs = [d for d in documents if d.doc_type == DOCUMENT_TYPE_MEETING]

        for doc in encounter_docs:
            row = self.encounters_table.rowCount()
            self.encounters_table.insertRow(row)

            # Дата документа
            date_str = doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"
            self.encounters_table.setItem(row, 0, QTableWidgetItem(date_str))

            # Автор документа (врач)
            author_name = doc.author.full_name if doc.author else "—"
            self.encounters_table.setItem(row, 1, QTableWidgetItem(author_name))

            # Результат встречи (из Encounter)
            result_display = "—"
            encounter = None
            if doc.encounter_id:
                encounter = Encounter.get_by_id(doc.encounter_id)
                if encounter and encounter.meeting_result:
                    result_display = encounter.meeting_result_display
            self.encounters_table.setItem(row, 2, QTableWidgetItem(result_display))

            # Краткое содержание как причина
            self.encounters_table.setItem(row, 3, QTableWidgetItem(doc.summary or "—"))

            # Статус (из Encounter или по умолчанию завершён)
            status_display = "Завершен"
            if encounter and encounter.status:
                status_display = encounter.status_display
            status_item = QTableWidgetItem(status_display)
            status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.encounters_table.setItem(row, 4, status_item)

            # Информация от пациента (кратко)
            patient_info_short = "—"
            if encounter and encounter.patient_info:
                patient_info_short = encounter.patient_info[:50] + (
                    "..." if len(encounter.patient_info) > 50 else ""
                )
            self.encounters_table.setItem(row, 5, QTableWidgetItem(patient_info_short))

            # Номер документа
            doc_number_str = str(doc.doc_number) if doc.doc_number else f"#{doc.id}"
            self.encounters_table.setItem(row, 6, QTableWidgetItem(doc_number_str))

            # Заметки (пустая колонка)
            self.encounters_table.setItem(row, 7, QTableWidgetItem("—"))

    def _create_plan_tab(self) -> QWidget:
        """Вкладка плана лечения"""
        colors = get_colors()

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Кнопка добавления плана
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            add_btn = QPushButton("Создать план работы")
            add_btn.setFixedHeight(36)
            add_btn.clicked.connect(self._add_plan_item)
            layout.addWidget(add_btn)

        # Таблица планов (документов)
        plans_label = QLabel("Планы работы:")
        plans_label.setStyleSheet(
            f"font-weight: bold; font-size: {FONTS['size_normal']}pt;"
        )
        layout.addWidget(plans_label)

        self.plans_table = QTableWidget()
        self.plans_table.setColumnCount(5)
        self.plans_table.setHorizontalHeaderLabels(
            ["№", "№ плана", "Дата", "Описание", "Пунктов"]
        )

        header = self.plans_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.plans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plans_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plans_table.verticalHeader().setVisible(False)
        self.plans_table.setShowGrid(False)
        self.plans_table.setMaximumHeight(200)
        self.plans_table.selectionModel().selectionChanged.connect(
            self._on_plan_selected
        )
        self.plans_table.doubleClicked.connect(self._open_plan_work_from_double_click)

        layout.addWidget(self.plans_table)

        # Таблица пунктов выбранного плана
        items_label = QLabel("Пункты плана:")
        items_label.setStyleSheet(
            f"font-weight: bold; font-size: {FONTS['size_normal']}pt;"
        )
        layout.addWidget(items_label)

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

        layout.addWidget(self.plan_table, 1)

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            edit_plan_btn = QPushButton("Редактировать пункты")
            edit_plan_btn.setFixedHeight(36)
            edit_plan_btn.clicked.connect(self._edit_plan)
            buttons_layout.addWidget(edit_plan_btn)

        toggle_btn = QPushButton("Переключить статус пункта")
        toggle_btn.setObjectName("secondaryBtn")
        toggle_btn.setFixedHeight(36)
        toggle_btn.clicked.connect(self._toggle_plan_item)
        buttons_layout.addWidget(toggle_btn)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            delete_btn = QPushButton("Удалить пункт")
            delete_btn.setObjectName("dangerBtn")
            delete_btn.setFixedHeight(36)
            delete_btn.clicked.connect(self._delete_plan_item)
            buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self._load_plans()
        self._load_plan_items()

        widget.setLayout(layout)
        return widget

    def _open_plan_work_from_double_click(self, index):
        """Открытие окна работы с планом по двойному клику"""
        row = index.row()
        doc_id_item = self.plans_table.item(row, 0)
        if not doc_id_item:
            return

        doc_id = doc_id_item.data(Qt.ItemDataRole.UserRole)
        if not doc_id:
            return

        doc = Document.get_by_id(doc_id)
        if not doc:
            return

        from ui.plan_work_items_form import PlanWorkItemsFormDialog

        dialog = PlanWorkItemsFormDialog(self.user, self.patient, doc)
        if dialog.exec():
            self._load_plans()
            # Восстанавливаем выделение и обновляем пункты
            for r in range(self.plans_table.rowCount()):
                item = self.plans_table.item(r, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == doc.id:
                    self.plans_table.selectRow(r)
                    self._refresh_plan_items()
                    break
            self._load_documents()

    def _on_plan_selected(self, selected, deselected):
        """При выборе плана загружаем его пункты и запоминаем id"""
        selected_indexes = self.plans_table.selectionModel().selectedRows()
        if selected_indexes:
            row = selected_indexes[0].row()
            doc_id_item = self.plans_table.item(row, 0)
            if doc_id_item:
                self._selected_plan_id = doc_id_item.data(Qt.ItemDataRole.UserRole)
            self._load_plan_items_for_row(row)
        else:
            self._selected_plan_id = None

    def _load_plans(self):
        """Загрузка документов-планов"""
        saved_plan_id = self._get_selected_plan_id()
        self.plans_table.setRowCount(0)
        self._selected_plan_id = None

        plans = Document.get_by_patient(self.patient.id)
        plan_docs = [d for d in plans if d.doc_type == DOCUMENT_TYPE_PLAN]

        for doc in plan_docs:
            row = self.plans_table.rowCount()
            self.plans_table.insertRow(row)

            # Сохраняем id документа в скрытой роли
            id_item = QTableWidgetItem(str(doc.id))
            id_item.setData(Qt.ItemDataRole.UserRole, doc.id)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.plans_table.setItem(row, 0, id_item)

            doc_number = str(doc.doc_number) if doc.doc_number else "—"
            self.plans_table.setItem(row, 1, QTableWidgetItem(doc_number))

            date_str = doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"
            self.plans_table.setItem(row, 2, QTableWidgetItem(date_str))

            summary = doc.summary or "—"
            self.plans_table.setItem(row, 3, QTableWidgetItem(summary))

            items_count = len(TreatmentPlanItem.get_by_plan(doc.id))
            self.plans_table.setItem(row, 4, QTableWidgetItem(str(items_count)))

        # Восстанавливаем выделение
        if saved_plan_id:
            for r in range(self.plans_table.rowCount()):
                item = self.plans_table.item(r, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == saved_plan_id:
                    self.plans_table.selectRow(r)
                    self._selected_plan_id = saved_plan_id
                    break

    def _load_plan_items_for_row(self, plan_row):
        """Загрузка пунктов плана для выбранной строки плана"""
        if plan_row < 0 or plan_row >= self.plans_table.rowCount():
            self.plan_table.setRowCount(0)
            return

        doc_id_item = self.plans_table.item(plan_row, 0)
        if not doc_id_item:
            self.plan_table.setRowCount(0)
            return

        doc_id = doc_id_item.data(Qt.ItemDataRole.UserRole)
        if not doc_id:
            self.plan_table.setRowCount(0)
            return

        self.plan_table.setRowCount(0)
        plan_items = TreatmentPlanItem.get_by_plan(doc_id)

        for item in plan_items:
            row = self.plan_table.rowCount()
            self.plan_table.insertRow(row)

            check_item = QTableWidgetItem("✓" if item.is_completed else "")
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.plan_table.setItem(row, 0, check_item)

            self.plan_table.setItem(row, 1, QTableWidgetItem(item.event))

            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            self.plan_table.setItem(row, 2, QTableWidgetItem(due_date))

            status = "Выполнено" if item.is_completed else "В ожидании"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                Qt.GlobalColor.darkGreen
                if item.is_completed
                else self._get_status_color(False)
            )
            self.plan_table.setItem(row, 3, status_item)

    def _load_plan_items(self):
        """Загрузка пунктов плана из всех документов-планов"""
        self.plan_table.setRowCount(0)

        # Загружаем все документы-планы пациента
        plans = Document.get_by_patient(self.patient.id)
        plan_docs = [d for d in plans if d.doc_type == DOCUMENT_TYPE_PLAN]

        # Загружаем все пункты из всех планов
        all_items = []
        for plan_doc in plan_docs:
            items = TreatmentPlanItem.get_by_plan(plan_doc.id)
            all_items.extend(items)

        # Сортируем по order_num и дате создания
        all_items.sort(key=lambda x: (x.order_num, x.created_at or datetime.min))

        for item in all_items:
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
                else self._get_status_color(False)
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
        self.documents_table.setColumnCount(7)
        self.documents_table.setHorizontalHeaderLabels(
            [
                "№",
                "№ док.",
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
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.documents_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.documents_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.documents_table.verticalHeader().setVisible(False)
        self.documents_table.setShowGrid(False)
        self.documents_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.documents_table.customContextMenuRequested.connect(
            self._show_document_context_menu
        )
        self.documents_table.doubleClicked.connect(self._open_document)

        layout.addWidget(self.documents_table, 1)

        # Кнопки действий
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_REGISTRAR):
            edit_btn = QPushButton("Редактировать")
            edit_btn.setObjectName("secondaryBtn")
            edit_btn.setFixedHeight(36)
            edit_btn.clicked.connect(self._edit_document)
            buttons_layout.addWidget(edit_btn)

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

                # Номер документа
                doc_number_str = str(doc.doc_number) if doc.doc_number else "—"
                self.documents_table.setItem(row, 1, QTableWidgetItem(doc_number_str))

                # Гриф секретности
                class_item = QTableWidgetItem(doc.classification_display)
                self.documents_table.setItem(row, 2, class_item)

                # Дата
                date_str = doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"
                self.documents_table.setItem(row, 3, QTableWidgetItem(date_str))

                # Вид документа
                if doc.doc_type == DOCUMENT_TYPE_PLAN:
                    # Для плана показываем количество пунктов
                    items_count = len(TreatmentPlanItem.get_by_plan(doc.id))
                    doc_type_display = f"План работы ({items_count} п.)"
                else:
                    doc_type_display = doc.doc_type or "—"
                self.documents_table.setItem(row, 4, QTableWidgetItem(doc_type_display))

                # Краткое содержание
                self.documents_table.setItem(
                    row, 5, QTableWidgetItem(doc.summary or "—")
                )

                # Куда приобщён
                self.documents_table.setItem(
                    row, 6, QTableWidgetItem(doc.location or "—")
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

    def _edit_document(self):
        """Редактирование документа"""
        selected = self.documents_table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите документ для редактирования"
            )
            return

        row = selected[0].row()
        documents = Document.get_by_patient(self.patient.id)
        if row >= len(documents):
            return

        doc = documents[row]

        # Для плана работы — открываем специальную форму
        if doc.doc_type == DOCUMENT_TYPE_PLAN:
            from ui.plan_work_form import PlanWorkFormDialog

            dialog = PlanWorkFormDialog(self.user, self.patient, doc)
        else:
            from ui.document_form import DocumentFormDialog

            dialog = DocumentFormDialog(self.user, self.patient, doc)

        if dialog.exec():
            self._load_documents()
            self._load_plans()
            # Если редактировали план, обновляем и пункты
            if doc.doc_type == DOCUMENT_TYPE_PLAN:
                selected = self.plans_table.selectionModel().selectedRows()
                if selected:
                    self._load_plan_items_for_row(selected[0].row())
            self._log_interaction("document_edit", f"Изменён документ №{doc.id}")

    def _open_document(self, index):
        """Открытие документа"""
        selected = self.documents_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        self._open_document_at_row(row)

    def _delete_document(self):
        """Удаление документа"""
        selected = self.documents_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите документ")
            return

        row = selected[0].row()
        self._delete_document_at_row(row)

    def _show_document_context_menu(self, position):
        """Показать контекстное меню для документов"""
        row = self.documents_table.rowAt(position.y())
        if row is None:
            return

        # Определяем тип документа
        documents = Document.get_by_patient(self.patient.id)
        if row >= len(documents):
            return
        doc = documents[row]

        menu = QMenu(self)

        # Действия для просмотра
        view_action = menu.addAction("Просмотр")
        view_action.triggered.connect(lambda: self._open_document_at_row(row))

        # Действия для редактирования (только для авторизованных ролей)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_REGISTRAR):
            edit_action = menu.addAction("Редактировать")
            edit_action.triggered.connect(lambda: self._edit_document_at_row(row))

            menu.addSeparator()

            delete_action = menu.addAction("Удалить")
            delete_action.triggered.connect(lambda: self._delete_document_at_row(row))

        menu.exec(self.documents_table.viewport().mapToGlobal(position))

    def _open_document_at_row(self, row):
        """Открыть документ по строке"""
        documents = Document.get_by_patient(self.patient.id)
        if row >= len(documents):
            return

        doc = documents[row]

        # Для плана работы — переключаемся на вкладку "План лечения" и выбираем план
        if doc.doc_type == DOCUMENT_TYPE_PLAN:
            self.tabs.setCurrentIndex(self.plan_tab_index)
            # Находим строку плана в таблице
            for r in range(self.plans_table.rowCount()):
                item = self.plans_table.item(r, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == doc.id:
                    self.plans_table.selectRow(r)
                    break
            return

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
            ("Номер документа:", str(doc.doc_number) if doc.doc_number else "—"),
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

    def _edit_document_at_row(self, row):
        """Редактировать документ по строке"""
        documents = Document.get_by_patient(self.patient.id)
        if row >= len(documents):
            return

        doc = documents[row]

        from ui.document_form import DocumentFormDialog

        dialog = DocumentFormDialog(self.user, self.patient, doc)

        if dialog.exec():
            self._load_documents()
            self._load_plans()
            self._log_interaction("document_edit", f"Изменён документ №{doc.id}")

    def _delete_document_at_row(self, row):
        """Удалить документ по строке"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранный документ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            documents = Document.get_by_patient(self.patient.id)
            if row < len(documents):
                doc = documents[row]
                # Если это план, сначала удаляем его пункты
                if doc.doc_type == DOCUMENT_TYPE_PLAN:
                    items = TreatmentPlanItem.get_by_plan(doc.id)
                    for item in items:
                        item.delete()
                doc.delete()
                self._load_documents()
                self._load_plans()
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
        """Добавление встречи (через создание документа типа "Встреча" + создание записи Encounter)"""
        from ui.document_form import DocumentFormDialog
        from models.db_models import DOCUMENT_TYPE_MEETING, Encounter

        dialog = DocumentFormDialog(self.user, self.patient, None)
        if dialog.exec():
            doc = dialog.document
            if doc and doc.doc_type == DOCUMENT_TYPE_MEETING:
                # Автоматически создаём запись Encounter
                encounter = Encounter()
                encounter.patient_id = self.patient.id
                encounter.doctor_id = (
                    self.user.id if self.user.role == User.ROLE_DOCTOR else 0
                )
                encounter.started_at = doc.doc_date
                encounter.reason = doc.summary or ""
                encounter.status = Encounter.STATUS_FINISHED
                encounter.document_id = doc.id
                encounter.save()

                # Связываем документ с встречей
                doc.encounter_id = encounter.id
                doc.save()

                self._load_encounters()
                self._load_documents()
                self._log_interaction("visit_created", "Создана новая встреча")

    def _edit_encounter(self, index):
        """Редактирование встречи (двойной клик) - открывает расширенную форму встречи"""
        selected = self.encounters_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите встречу")
            return

        row = selected[0].row()

        from models.db_models import Document, DOCUMENT_TYPE_MEETING, Encounter

        # Получаем документы типа "Встреча"
        documents = Document.get_by_patient(self.patient.id)
        encounter_docs = [d for d in documents if d.doc_type == DOCUMENT_TYPE_MEETING]

        if row >= len(encounter_docs):
            return

        doc = encounter_docs[row]

        # Получаем или создаём запись Encounter
        encounter = None
        if doc.encounter_id:
            encounter = Encounter.get_by_id(doc.encounter_id)

        if not encounter:
            # Создаём запись Encounter, если её нет
            encounter = Encounter()
            encounter.patient_id = self.patient.id
            encounter.doctor_id = (
                self.user.id if self.user.role == User.ROLE_DOCTOR else 0
            )
            encounter.started_at = doc.doc_date
            encounter.reason = doc.summary or ""
            encounter.status = Encounter.STATUS_FINISHED
            encounter.document_id = doc.id
            encounter.save()

            # Связываем документ с встречей
            doc.encounter_id = encounter.id
            doc.save()

        # Открываем расширенную форму редактирования встречи
        from ui.encounter_edit_form import EncounterEditDialog

        dialog = EncounterEditDialog(self.user, self.patient, encounter)
        if dialog.exec():
            self._load_encounters()
            self._load_documents()
            self._log_interaction(
                "visit_edit", f"Отредактирована встреча (док. №{doc.id})"
            )

    def _add_plan_item(self):
        """Создание плана работы (документ + пункты)"""
        from ui.document_form import DocumentFormDialog

        dialog = DocumentFormDialog(self.user, self.patient, None)
        if dialog.exec():
            doc = dialog.document
            if doc and doc.doc_type == DOCUMENT_TYPE_PLAN:
                self._load_plans()
                self._load_documents()
                # Переключаемся на вкладку "План лечения" и выбираем новый план
                self.tabs.setCurrentIndex(self.plan_tab_index)
                for r in range(self.plans_table.rowCount()):
                    item = self.plans_table.item(r, 0)
                    if item and item.data(Qt.ItemDataRole.UserRole) == doc.id:
                        self.plans_table.selectRow(r)
                        break
                self._log_interaction("plan_item_add", "Создан план работы")

    def _edit_plan(self):
        """Переключение на вкладку плана лечения для редактирования пунктов"""
        plan_id = self._get_selected_plan_id()
        if not plan_id:
            QMessageBox.information(
                self,
                "Информация",
                "Выберите план работы для редактирования",
            )
            return

        doc = Document.get_by_id(plan_id)
        if not doc or doc.doc_type != DOCUMENT_TYPE_PLAN:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти план")
            return

        # Переключаемся на вкладку "План лечения"
        self.tabs.setCurrentIndex(self.plan_tab_index)

    def _get_all_plan_items(self):
        """Получение всех пунктов плана из всех документов-планов"""
        plans = Document.get_by_patient(self.patient.id)
        plan_docs = [d for d in plans if d.doc_type == DOCUMENT_TYPE_PLAN]

        all_items = []
        for plan_doc in plan_docs:
            items = TreatmentPlanItem.get_by_plan(plan_doc.id)
            all_items.extend(items)

        all_items.sort(key=lambda x: (x.order_num, x.created_at or datetime.min))
        return all_items

    def _get_selected_plan_id(self):
        """Получение id выбранного плана"""
        return getattr(self, "_selected_plan_id", None)

    def _refresh_plan_items(self):
        """Обновление пунктов выбранного плана без сброса выделения"""
        plan_id = self._get_selected_plan_id()
        if not plan_id:
            self.plan_table.setRowCount(0)
            return

        self.plan_table.setRowCount(0)
        plan_items = TreatmentPlanItem.get_by_plan(plan_id)

        for item in plan_items:
            row = self.plan_table.rowCount()
            self.plan_table.insertRow(row)

            check_item = QTableWidgetItem("✓" if item.is_completed else "")
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.plan_table.setItem(row, 0, check_item)

            self.plan_table.setItem(row, 1, QTableWidgetItem(item.event))

            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            self.plan_table.setItem(row, 2, QTableWidgetItem(due_date))

            status = "Выполнено" if item.is_completed else "В ожидании"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                Qt.GlobalColor.darkGreen
                if item.is_completed
                else self._get_status_color(False)
            )
            self.plan_table.setItem(row, 3, status_item)

    def _toggle_plan_item(self):
        """Переключение статуса пункта плана"""
        selected = self.plan_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите пункт плана")
            return

        plan_id = self._get_selected_plan_id()
        if not plan_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите план работы")
            return

        row = selected[0].row()
        plan_items = TreatmentPlanItem.get_by_plan(plan_id)
        if row < len(plan_items):
            item = plan_items[row]
            item.toggle()
            self._refresh_plan_items()
            self._load_plans()  # Обновляем счётчик пунктов
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

        plan_id = self._get_selected_plan_id()
        if not plan_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите план работы")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранный пункт плана?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            plan_items = TreatmentPlanItem.get_by_plan(plan_id)
            if row < len(plan_items):
                item = plan_items[row]
                item.delete()
                self._refresh_plan_items()
                self._load_plans()  # Обновляем счётчик пунктов
                self._load_documents()
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

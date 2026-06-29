"""
Окно редактирования встречи (Encounter Edit Form)
Расширенная форма с полями: результат встречи, информация от категории АА,
описание встречи, мероприятия, информация от информатора
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
    QLineEdit,
    QInputDialog,
    QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from models.db_models import (
    User,
    Patient,
    Encounter,
    EncounterGroup,
    EncounterInformant,
    TreatmentPlanItem,
    KmRecord,
    Document,
)
from ui.styles import get_colors, FONTS, RADIUS


class EncounterInformantDialog(QDialog):
    """Диалог добавления/редактирования информатора"""

    def __init__(self, informant: EncounterInformant = None):
        super().__init__()
        self.informant = informant
        self.setWindowTitle("Информатор")
        self.setMinimumSize(560, 520)
        self._init_ui()

    def _init_ui(self):
        colors = get_colors()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Должность
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Введите должность")
        form_layout.addRow("Должность", self.position_input)

        # ФИО
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Введите ФИО")
        form_layout.addRow("ФИО", self.full_name_input)

        # Дата рождения
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate())
        self.birth_date_input.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Дата рождения", self.birth_date_input)

        # Место работы
        self.workplace_input = QLineEdit()
        self.workplace_input.setPlaceholderText("Введите место работы")
        form_layout.addRow("Место работы", self.workplace_input)

        # Суть информации
        self.info_essence_input = QTextEdit()
        self.info_essence_input.setPlaceholderText("Введите суть информации")
        self.info_essence_input.setMaximumHeight(100)
        form_layout.addRow("Суть информации", self.info_essence_input)

        # Принятые меры
        self.measures_taken_input = QTextEdit()
        self.measures_taken_input.setPlaceholderText("Введите принятые меры")
        self.measures_taken_input.setMaximumHeight(100)
        form_layout.addRow("Принятые меры", self.measures_taken_input)

        layout.addLayout(form_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

        # Заполнение при редактировании
        if self.informant:
            self._fill_data()

    def _fill_data(self):
        """Заполнение данными информатора"""
        self.position_input.setText(self.informant.position or "")
        self.full_name_input.setText(self.informant.full_name or "")
        if self.informant.birth_date:
            self.birth_date_input.setDate(
                QDate(
                    self.informant.birth_date.year,
                    self.informant.birth_date.month,
                    self.informant.birth_date.day,
                )
            )
        self.workplace_input.setText(self.informant.workplace or "")
        self.info_essence_input.setPlainText(self.informant.info_essence or "")
        self.measures_taken_input.setPlainText(self.informant.measures_taken or "")

    def _save(self):
        """Сохранение информатора"""
        if not self.full_name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите ФИО")
            return

        if not self.informant:
            self.informant = EncounterInformant()

        self.informant.position = self.position_input.text().strip()
        self.informant.full_name = self.full_name_input.text().strip()
        self.informant.birth_date = self.birth_date_input.date().toPyDate()
        self.informant.workplace = self.workplace_input.text().strip()
        self.informant.info_essence = self.info_essence_input.toPlainText().strip()
        self.informant.measures_taken = self.measures_taken_input.toPlainText().strip()

        self.accept()

    def get_informant(self) -> EncounterInformant:
        """Получение информатора"""
        return self.informant


class EncounterEditDialog(QDialog):
    """Расширенное окно редактирования встречи"""

    def __init__(self, user: User, patient: Patient, encounter: Encounter):
        super().__init__()
        self.user = user
        self.patient = patient
        self.encounter = encounter
        # Загружаем информаторов из БД или используем пустой список
        self.informants = []
        if encounter.id:
            self.informants = EncounterInformant.get_by_encounter(encounter.id)
        self.deleted_informant_ids = []
        # Флаг для отслеживания изменений в информаторах
        self.informants_modified = False

        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(800, 700)
        self._init_ui()

    def _get_window_title(self) -> str:
        doc_number = "б/н"
        if self.encounter.document_id:
            doc = Document.get_by_id(self.encounter.document_id)
            if doc and doc.doc_number:
                doc_number = str(doc.doc_number)

        date_text = (
            self.encounter.started_at.strftime("%d.%m.%Y %H:%M")
            if self.encounter.started_at
            else "без даты"
        )
        return f"Редактирование встречи № {doc_number} от {date_text}"

    def _init_ui(self):
        colors = get_colors()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Скролл для контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.Box)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Группа 1: Результат встречи
        result_group = QGroupBox("Результат встречи")
        result_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        result_layout = QFormLayout()
        result_layout.setSpacing(10)

        # Выпадающий список результата встречи
        self.meeting_result_combo = QComboBox()
        self.meeting_result_combo.setFrame(False)
        self.meeting_result_combo.setMinimumHeight(36)
        self.meeting_result_combo.setMaximumWidth(420)
        self.meeting_result_combo.setMaxVisibleItems(4)
        self.meeting_result_combo.addItem("Выберите результат", "")
        for value, label in self._get_meeting_result_choices():
            self.meeting_result_combo.addItem(label, value)
        if self.patient.patient_type != "adult":
            certificate_index = self.meeting_result_combo.findData("certificate")
            if certificate_index >= 0:
                self.meeting_result_combo.setCurrentIndex(certificate_index)
        result_layout.addRow("Результат встречи*", self.meeting_result_combo)

        self.status_combo = QComboBox()
        self.status_combo.setFrame(False)
        self.status_combo.setMinimumHeight(36)
        self.status_combo.setMaximumWidth(420)
        self.status_combo.setMaxVisibleItems(3)
        self.status_combo.addItem("Запланирован", Encounter.STATUS_PLANNED)
        self.status_combo.addItem("В процессе", Encounter.STATUS_INPROGRESS)
        self.status_combo.addItem("Завершен", Encounter.STATUS_FINISHED)
        result_layout.addRow("Статус", self.status_combo)

        group_row = QHBoxLayout()
        group_row.setSpacing(8)
        self.group_combo = QComboBox()
        self.group_combo.setFrame(False)
        self.group_combo.setMinimumHeight(36)
        self.group_combo.setMaximumWidth(420)
        self.group_combo.setMaxVisibleItems(12)
        group_row.addWidget(self.group_combo, 1)

        new_group_btn = QPushButton("Новый")
        new_group_btn.setObjectName("secondaryBtn")
        new_group_btn.setFixedHeight(36)
        new_group_btn.setFixedWidth(86)
        new_group_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_group_btn.clicked.connect(self._create_encounter_group)
        self.group_new_btn = new_group_btn
        group_row.addWidget(new_group_btn)

        clear_group_btn = QPushButton("Очистить")
        clear_group_btn.setObjectName("secondaryBtn")
        clear_group_btn.setFixedHeight(36)
        clear_group_btn.setFixedWidth(96)
        clear_group_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_group_btn.clicked.connect(lambda: self.group_combo.setCurrentIndex(0))
        self.group_clear_btn = clear_group_btn
        group_row.addWidget(clear_group_btn)
        result_layout.addRow("Признак встречи", group_row)

        # Позывной и личный номер (автозаполнение из категории АА)
        callsign_label = QLabel(f"Позывной: {self.patient.callsign}")
        callsign_label.setStyleSheet("background-color: transparent;")
        result_layout.addRow("", callsign_label)

        personal_number_label = QLabel(
            f"Личный номер: {self.patient.personal_number or 'Не присвоен'}"
        )
        personal_number_label.setStyleSheet("background-color: transparent;")
        result_layout.addRow("", personal_number_label)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # Группа 2: Информация от категории АА
        patient_info_group = QGroupBox("Информация от категории АА")
        patient_info_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        patient_info_layout = QVBoxLayout()
        patient_info_layout.setSpacing(8)

        self.patient_info_input = QTextEdit()
        self.patient_info_input.setPlaceholderText("Введите информацию от категории АА")
        self.patient_info_input.setMinimumHeight(92)
        self.patient_info_input.setMaximumHeight(120)
        patient_info_layout.addWidget(self.patient_info_input)

        patient_info_group.setLayout(patient_info_layout)
        layout.addWidget(patient_info_group)

        # Группа 3: Описание встречи
        description_group = QGroupBox("Описание встречи")
        description_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        description_layout = QVBoxLayout()
        description_layout.setSpacing(8)

        self.meeting_description_input = QTextEdit()
        self.meeting_description_input.setPlaceholderText("Введите описание встречи")
        self.meeting_description_input.setMinimumHeight(92)
        self.meeting_description_input.setMaximumHeight(120)
        description_layout.addWidget(self.meeting_description_input)

        information_quality_layout = QFormLayout()
        information_quality_layout.setSpacing(10)

        self.information_relevance_input = QLineEdit()
        self.information_relevance_input.setMinimumHeight(36)
        self.information_relevance_input.setMaximumWidth(420)
        self.information_relevance_input.setPlaceholderText(
            "Введите относимость информации"
        )
        information_quality_layout.addRow(
            "Относимость информации", self.information_relevance_input
        )

        self.information_importance_input = QLineEdit()
        self.information_importance_input.setMinimumHeight(36)
        self.information_importance_input.setMaximumWidth(420)
        self.information_importance_input.setPlaceholderText(
            "Введите важность информации"
        )
        information_quality_layout.addRow(
            "Важность информации", self.information_importance_input
        )

        self.information_timeliness_combo = self._create_information_combo(
            Encounter.INFORMATION_TIMELINESS_CHOICES
        )
        information_quality_layout.addRow(
            "Своевременность информации", self.information_timeliness_combo
        )

        self.information_completeness_combo = self._create_information_combo(
            Encounter.INFORMATION_COMPLETENESS_CHOICES
        )
        information_quality_layout.addRow(
            "Полнота информации", self.information_completeness_combo
        )

        self.information_novelty_combo = self._create_information_combo(
            Encounter.INFORMATION_NOVELTY_CHOICES
        )
        information_quality_layout.addRow(
            "Новизна информации", self.information_novelty_combo
        )

        self.information_reliability_combo = self._create_information_combo(
            Encounter.INFORMATION_RELIABILITY_CHOICES
        )
        information_quality_layout.addRow(
            "Достоверность информации", self.information_reliability_combo
        )
        description_layout.addLayout(information_quality_layout)

        description_group.setLayout(description_layout)
        layout.addWidget(description_group)

        # Группа 4: Мероприятия для исполнения категорией АА
        patient_tasks_group = QGroupBox("Мероприятия для исполнения категорией АА")
        patient_tasks_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        patient_tasks_layout = QFormLayout()
        patient_tasks_layout.setSpacing(10)

        self.patient_tasks_input = QTextEdit()
        self.patient_tasks_input.setPlaceholderText("Мероприятия и способ исполнения")
        self.patient_tasks_input.setMinimumHeight(92)
        self.patient_tasks_input.setMaximumHeight(120)
        patient_tasks_layout.addRow(
            "Мероприятия и способ исполнения", self.patient_tasks_input
        )

        patient_tasks_group.setLayout(patient_tasks_layout)
        layout.addWidget(patient_tasks_group)

        # Группа 5: Мероприятия в отношении категории АА (из плана)
        patient_measures_group = QGroupBox(
            "Мероприятия в отношении категории АА (из плана)"
        )
        patient_measures_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        patient_measures_layout = QVBoxLayout()
        patient_measures_layout.setSpacing(8)

        plan_items_header_layout = QHBoxLayout()
        plan_items_header_layout.setSpacing(8)

        self.plan_items_count_label = QLabel("")
        self.plan_items_count_label.setObjectName("muted")
        plan_items_header_layout.addWidget(self.plan_items_count_label)
        plan_items_header_layout.addStretch()

        self.change_plan_item_btn = QPushButton("Изменить")
        self.change_plan_item_btn.setObjectName("secondaryBtn")
        self.change_plan_item_btn.setFixedHeight(32)
        self.change_plan_item_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.change_plan_item_btn.clicked.connect(self._show_all_plan_items)
        self.change_plan_item_btn.hide()
        self.change_plan_item_btn.setStyleSheet(
            f"""
            QPushButton#secondaryBtn {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 4px 14px;
                font-weight: 600;
                color: {colors['text']};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {colors['surface_muted']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#secondaryBtn:pressed {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
                color: #FFFFFF;
            }}
            """
        )
        plan_items_header_layout.addWidget(self.change_plan_item_btn)
        patient_measures_layout.addLayout(plan_items_header_layout)

        # Таблица пунктов плана
        self.plan_items_table = QTableWidget()
        self.plan_items_table.setColumnCount(4)
        self.plan_items_table.setHorizontalHeaderLabels(
            ["Выбор", "Мероприятие", "Срок", "Статус"]
        )
        self.plan_items_table.setAlternatingRowColors(True)
        self.plan_items_table.setShowGrid(True)
        self.plan_items_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.plan_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plan_items_table.doubleClicked.connect(self._toggle_plan_item_selection)
        self.plan_items_table.verticalHeader().setVisible(False)
        self.plan_items_table.setMinimumHeight(220)
        self.plan_items_table.setMaximumHeight(320)
        plan_header = self.plan_items_table.horizontalHeader()
        plan_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        plan_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        plan_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        plan_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.plan_items_table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {colors['surface']};
                alternate-background-color: {colors['surface_muted']};
                color: {colors['text']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                gridline-color: {colors['line']};
                selection-background-color: {colors['accent_light']};
                selection-color: {colors['text']};
            }}
            QHeaderView::section {{
                background-color: {colors['surface_muted']};
                color: {colors['text']};
                border: none;
                border-bottom: 1px solid {colors['line']};
                padding: 8px;
                font-weight: 600;
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {colors['text']};
            }}
            """
        )
        patient_measures_layout.addWidget(self.plan_items_table)

        # Загрузка пунктов плана
        self._load_plan_items()
        self._load_encounter_groups()

        patient_measures_group.setLayout(patient_measures_layout)
        layout.addWidget(patient_measures_group)

        # Группа 6: Мероприятия общего формата
        general_measures_group = QGroupBox("Мероприятия общего формата")
        general_measures_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        general_measures_layout = QVBoxLayout()
        general_measures_layout.setSpacing(8)

        self.general_measures_input = QTextEdit()
        self.general_measures_input.setPlaceholderText(
            "Введите мероприятия общего формата"
        )
        self.general_measures_input.setMinimumHeight(92)
        self.general_measures_input.setMaximumHeight(120)
        general_measures_layout.addWidget(self.general_measures_input)

        general_measures_group.setLayout(general_measures_layout)
        layout.addWidget(general_measures_group)

        # Группа 7: О ком сообщила категория АА (Информаторы)
        informants_group = QGroupBox("О ком сообщила категория АА")
        informants_group.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """
        )
        informants_layout = QVBoxLayout()
        informants_layout.setContentsMargins(8, 8, 8, 10)
        informants_layout.setSpacing(10)

        # Таблица информаторов
        self.informants_table = QTableWidget()
        self.informants_table.setColumnCount(6)
        self.informants_table.setHorizontalHeaderLabels(
            [
                "Должность",
                "ФИО",
                "Дата рождения",
                "Место работы",
                "Суть информации",
                "Принятые меры",
            ]
        )
        self.informants_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.informants_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.informants_table.verticalHeader().setVisible(False)
        self.informants_table.setMinimumHeight(200)
        self.informants_table.setMaximumHeight(400)
        informants_header = self.informants_table.horizontalHeader()
        informants_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        informants_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        informants_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        informants_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        informants_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        informants_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        # Кнопки управления информаторами
        informants_buttons = QHBoxLayout()
        informants_buttons.setContentsMargins(0, 6, 0, 2)
        informants_buttons.setSpacing(8)
        informants_button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: {FONTS['size_small']}pt;
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['accent_light']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton:pressed {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
                color: #FFFFFF;
            }}
        """
        informants_danger_button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {colors['danger']};
                border-radius: {RADIUS['md']}px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: {FONTS['size_small']}pt;
                color: {colors['danger']};
            }}
            QPushButton:hover {{
                background-color: {colors['danger_bg']};
                border: 2px solid {colors['danger']};
                color: {colors['danger']};
            }}
            QPushButton:pressed {{
                background-color: {colors['danger']};
                border: 2px solid {colors['danger']};
                color: #FFFFFF;
            }}
        """
        add_informant_btn = QPushButton("Добавить лицо")
        add_informant_btn.setObjectName("actionButton")
        add_informant_btn.setFixedHeight(36)
        add_informant_btn.setFixedWidth(128)
        add_informant_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_informant_btn.setStyleSheet(informants_button_style)
        add_informant_btn.clicked.connect(self._add_informant)
        informants_buttons.addSpacing(4)
        informants_buttons.addWidget(add_informant_btn)

        edit_informant_btn = QPushButton("Редактировать")
        edit_informant_btn.setObjectName("secondaryBtn")
        edit_informant_btn.setFixedHeight(36)
        edit_informant_btn.setFixedWidth(132)
        edit_informant_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_informant_btn.setStyleSheet(informants_button_style)
        edit_informant_btn.clicked.connect(self._edit_informant)
        informants_buttons.addWidget(edit_informant_btn)

        delete_informant_btn = QPushButton("Удалить")
        delete_informant_btn.setObjectName("dangerBtn")
        delete_informant_btn.setFixedHeight(36)
        delete_informant_btn.setFixedWidth(96)
        delete_informant_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_informant_btn.setStyleSheet(informants_danger_button_style)
        delete_informant_btn.clicked.connect(self._delete_informant)
        informants_buttons.addWidget(delete_informant_btn)
        informants_buttons.addStretch()

        informants_layout.addWidget(self.informants_table)
        informants_layout.addLayout(informants_buttons)

        # Загрузка информаторов
        self._load_informants()

        informants_group.setLayout(informants_layout)
        layout.addWidget(informants_group)

        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Кнопки сохранения/отмены
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setFixedHeight(40)
        save_btn.setObjectName("secondaryBtn")
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self._polish_controls(colors)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

        # Заполнение при редактировании
        self._fill_data()

    def _get_meeting_result_choices(self):
        if self.patient.patient_type == "adult":
            return Encounter.MEETING_RESULT_CHOICES
        return [
            (value, label)
            for value, label in Encounter.MEETING_RESULT_CHOICES
            if value == "certificate"
        ]

    @staticmethod
    def _create_information_combo(choices):
        combo = QComboBox()
        combo.setFrame(False)
        combo.setMinimumHeight(36)
        combo.setMaximumWidth(420)
        combo.addItem("Не указано", "")
        for value, label in choices:
            combo.addItem(label, value)
        return combo

    def _normalize_meeting_result_for_patient_type(self, meeting_result: str) -> str:
        if self.patient.patient_type == "adult":
            return meeting_result
        return "certificate"

    def _polish_controls(self, colors):
        input_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 10px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """
        combo_style = input_style + f"""
            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: 1px solid {colors['line']};
                selection-background-color: {colors['accent_light']};
                selection-color: {colors['text']};
                padding: 4px;
                outline: none;
            }}
        """
        text_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 8px 10px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """
        table_style = f"""
            QTableWidget {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                gridline-color: {colors['line_light']};
                selection-background-color: {colors['table_row_selected']};
                selection-color: {colors['text']};
            }}
            QHeaderView::section {{
                background-color: {colors['table_header_bg']};
                color: {colors['text_muted']};
                border: none;
                border-bottom: 1px solid {colors['line']};
                padding: 8px;
                font-weight: 600;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
            }}
        """

        self.meeting_result_combo.setStyleSheet(combo_style)
        self.status_combo.setStyleSheet(combo_style)
        self.group_combo.setStyleSheet(combo_style)
        group_button_style = f"""
            QPushButton#secondaryBtn {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 6px 12px;
                font-weight: 600;
                color: {colors['text']};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {colors['surface_muted']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#secondaryBtn:pressed {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
                color: #FFFFFF;
            }}
        """
        self.group_new_btn.setStyleSheet(group_button_style)
        self.group_clear_btn.setStyleSheet(group_button_style)
        for combo in (
            self.information_timeliness_combo,
            self.information_completeness_combo,
            self.information_novelty_combo,
            self.information_reliability_combo,
        ):
            combo.setStyleSheet(combo_style)
        self.information_relevance_input.setStyleSheet(input_style)
        self.information_importance_input.setStyleSheet(input_style)
        for text_edit in (
            self.patient_info_input,
            self.meeting_description_input,
            self.patient_tasks_input,
            self.general_measures_input,
        ):
            text_edit.setStyleSheet(text_style)

        self.plan_items_table.setStyleSheet(table_style)
        self.informants_table.setStyleSheet(table_style)

    def _load_encounter_groups(self, selected_group_id: int | None = None):
        current_group_id = (
            selected_group_id
            if selected_group_id is not None
            else self.encounter.group_id
        )
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        self.group_combo.addItem("Без признака", None)
        for group in EncounterGroup.get_all():
            self.group_combo.addItem(
                f"{group.name} · {group.category_display}",
                group.id,
            )
        if current_group_id:
            index = self.group_combo.findData(current_group_id)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)
        self.group_combo.blockSignals(False)

    def _create_encounter_group(self):
        name, ok = QInputDialog.getText(
            self,
            "Новый признак",
            "Условное наименование:",
        )
        name = name.strip()
        if not ok or not name:
            return

        category_labels = [label for _, label in EncounterGroup.CATEGORY_CHOICES]
        category_label, ok = QInputDialog.getItem(
            self,
            "Тип признака",
            "Признак:",
            category_labels,
            0,
            False,
        )
        if not ok:
            return
        category_by_label = {
            label: value for value, label in EncounterGroup.CATEGORY_CHOICES
        }
        group = EncounterGroup.create_quick(
            name=name,
            category=category_by_label.get(
                category_label, EncounterGroup.CATEGORY_PERSONAL
            ),
            created_by_id=self.user.id,
        )
        self._load_encounter_groups(group.id)

    def _load_plan_items(self):
        """Загрузка пунктов плана лечения категории АА"""
        self.plan_items_table.setRowCount(0)

        from models.db_models import Document, DOCUMENT_TYPE_PLAN

        current_year = QDate.currentDate().year()
        plans = {
            d.id: d
            for d in Document.get_by_patient(self.patient.id)
            if d.id is not None and d.doc_type == DOCUMENT_TYPE_PLAN
        }

        all_items = []
        seen_item_ids = set()
        for item in TreatmentPlanItem.get_by_patient(self.patient.id):
            if item.id in seen_item_ids:
                continue

            plan_doc = plans.get(item.plan_document_id)
            is_current_year_plan_item = (
                plan_doc is not None
                and item.due_date is not None
                and item.due_date.year == current_year
            )

            if is_current_year_plan_item:
                all_items.append(item)
                if item.id is not None:
                    seen_item_ids.add(item.id)

        all_items.sort(
            key=lambda item: (
                item.due_date is None,
                item.due_date or QDate.currentDate().toPyDate(),
                item.order_num,
                item.id or 0,
            )
        )

        if not all_items:
            self.plan_items_count_label.setText(
                "Мероприятия плана за текущий год не найдены"
            )
            self.plan_items_table.insertRow(0)
            empty_item = QTableWidgetItem("Нет мероприятий плана за текущий год")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.plan_items_table.setSpan(0, 0, 1, 4)
            self.plan_items_table.setItem(0, 0, empty_item)
            return

        self.plan_items_count_label.setText(
            f"Найдено мероприятий: {len(all_items)}. Двойной клик выбирает или снимает выбор."
        )
        selected_events = {
            line.strip()
            for line in (self.encounter.patient_measures or "").splitlines()
            if line.strip()
        }
        selected_row = None

        for item in all_items:
            row = self.plan_items_table.rowCount()
            self.plan_items_table.insertRow(row)

            is_selected = item.event in selected_events and selected_row is None
            if is_selected and selected_row is None:
                selected_row = row
            select_item = QTableWidgetItem("✓" if is_selected else "")
            select_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            select_item.setData(Qt.ItemDataRole.UserRole, is_selected)
            self.plan_items_table.setItem(row, 0, select_item)

            event_item = QTableWidgetItem(item.event)
            event_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.plan_items_table.setItem(row, 1, event_item)

            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            self.plan_items_table.setItem(row, 2, QTableWidgetItem(due_date))

            status = "Выполнено" if item.is_completed else "В ожидании"
            self.plan_items_table.setItem(row, 3, QTableWidgetItem(status))
            self._apply_plan_item_row_selection(row, is_selected)

        if selected_row is not None:
            self._collapse_plan_items_to_row(selected_row)

    def _toggle_plan_item_selection(self, index):
        """Выбор одного пункта плана двойным кликом."""
        row = index.row()
        check_item = self.plan_items_table.item(row, 0)
        event_item = self.plan_items_table.item(row, 1)
        if not check_item or not event_item:
            return

        for current_row in range(self.plan_items_table.rowCount()):
            current_check_item = self.plan_items_table.item(current_row, 0)
            if current_check_item:
                current_check_item.setText("")
                current_check_item.setData(Qt.ItemDataRole.UserRole, False)
                self._apply_plan_item_row_selection(current_row, False)

        check_item.setText("✓")
        check_item.setData(Qt.ItemDataRole.UserRole, True)
        self._apply_plan_item_row_selection(row, True)
        self._collapse_plan_items_to_row(row)

    def _collapse_plan_items_to_row(self, selected_row: int):
        """Показывает только выбранное мероприятие."""
        for row in range(self.plan_items_table.rowCount()):
            self.plan_items_table.setRowHidden(row, row != selected_row)
        self.plan_items_count_label.setText("Выбрано мероприятие плана")
        self.change_plan_item_btn.show()

    def _show_all_plan_items(self):
        """Возвращает на экран все мероприятия для изменения выбора."""
        visible_count = 0
        for row in range(self.plan_items_table.rowCount()):
            self.plan_items_table.setRowHidden(row, False)
            visible_count += 1
        self.plan_items_count_label.setText(
            f"Найдено мероприятий: {visible_count}. Двойной клик выбирает мероприятие."
        )
        self.change_plan_item_btn.hide()

    def _apply_plan_item_row_selection(self, row: int, is_selected: bool):
        """Визуальная отметка выбранной строки мероприятий плана."""
        colors = get_colors()
        bg_color = colors["accent_light"] if is_selected else colors["surface"]
        text_color = colors["accent"] if is_selected else colors["text"]
        for col in range(self.plan_items_table.columnCount()):
            item = self.plan_items_table.item(row, col)
            if item:
                item.setBackground(QColor(bg_color))
                item.setForeground(QColor(text_color))
                item.setToolTip(
                    "Двойной клик снимет выбор"
                    if is_selected
                    else "Двойной клик выберет мероприятие"
                )

    def _load_informants(self):
        """Загрузка информаторов в таблицу"""
        self.informants_table.setRowCount(0)

        for informant in self.informants:
            row = self.informants_table.rowCount()
            self.informants_table.insertRow(row)

            self.informants_table.setItem(
                row, 0, QTableWidgetItem(informant.position or "—")
            )
            self.informants_table.setItem(
                row, 1, QTableWidgetItem(informant.full_name or "—")
            )

            birth_date = (
                informant.birth_date.strftime("%d.%m.%Y")
                if informant.birth_date
                else "—"
            )
            self.informants_table.setItem(row, 2, QTableWidgetItem(birth_date))

            self.informants_table.setItem(
                row, 3, QTableWidgetItem(informant.workplace or "—")
            )
            self.informants_table.setItem(
                row, 4, QTableWidgetItem(informant.info_essence or "—")
            )
            self.informants_table.setItem(
                row, 5, QTableWidgetItem(informant.measures_taken or "—")
            )

    def _add_informant(self):
        """Добавление информатора (сохраняется только при общем сохранении встречи)"""
        dialog = EncounterInformantDialog()
        if dialog.exec():
            informant = dialog.get_informant()
            # НЕ сохраняем в БД сразу - добавляем в список
            self.informants.append(informant)
            self.informants_modified = True
            self._load_informants()

    def _edit_informant(self):
        """Редактирование информатора"""
        selected = self.informants_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите информатора")
            return

        row = selected[0].row()
        if row >= len(self.informants):
            return

        informant = self.informants[row]
        dialog = EncounterInformantDialog(informant)
        if dialog.exec():
            self.informants_modified = True
            self._load_informants()

    def _delete_informant(self):
        """Удаление информатора"""
        selected = self.informants_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите информатора")
            return

        row = selected[0].row()
        if row >= len(self.informants):
            return

        informant = self.informants[row]
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить информатора {informant.full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if informant.id:
                self.deleted_informant_ids.append(informant.id)
            self.informants.pop(row)
            self.informants_modified = True
            self._load_informants()

    def _fill_data(self):
        """Заполнение данными встречи"""
        # Результат встречи
        if self.encounter.meeting_result:
            meeting_result = self._normalize_meeting_result_for_patient_type(
                self.encounter.meeting_result
            )
            index = self.meeting_result_combo.findData(meeting_result)
            if index >= 0:
                self.meeting_result_combo.setCurrentIndex(index)

        status_index = self.status_combo.findData(
            self.encounter.status or Encounter.STATUS_FINISHED
        )
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)
        if self.encounter.group_id:
            group_index = self.group_combo.findData(self.encounter.group_id)
            if group_index >= 0:
                self.group_combo.setCurrentIndex(group_index)

        # Информация от категории АА
        self.patient_info_input.setPlainText(self.encounter.patient_info or "")

        # Описание встречи
        self.meeting_description_input.setPlainText(
            self.encounter.meeting_description or ""
        )
        self.information_relevance_input.setText(
            self.encounter.information_relevance or ""
        )
        self.information_importance_input.setText(
            self.encounter.information_importance or ""
        )
        information_combos = (
            (
                self.information_timeliness_combo,
                self.encounter.information_timeliness,
            ),
            (
                self.information_completeness_combo,
                self.encounter.information_completeness,
            ),
            (self.information_novelty_combo, self.encounter.information_novelty),
            (
                self.information_reliability_combo,
                self.encounter.information_reliability,
            ),
        )
        for combo, value in information_combos:
            index = combo.findData(value or "")
            if index >= 0:
                combo.setCurrentIndex(index)

        # Мероприятия для исполнения категорией АА
        self.patient_tasks_input.setPlainText(self.encounter.patient_tasks or "")

        # Мероприятия в отношении категории АА (из выбранных пунктов плана)
        # Здесь можно добавить логику выделения пунктов
        # Пока просто загружаем все пункты

        # Мероприятия общего формата
        self.general_measures_input.setPlainText(self.encounter.general_measures or "")

    def _save(self):
        """Сохранение встречи"""
        # Валидация
        meeting_result = self._normalize_meeting_result_for_patient_type(
            self.meeting_result_combo.currentData()
        )
        if not meeting_result:
            QMessageBox.warning(self, "Ошибка", "Выберите результат встречи")
            return

        # Сохранение основных полей
        self.encounter.meeting_result = meeting_result
        self.encounter.status = self.status_combo.currentData()
        self.encounter.group_id = self.group_combo.currentData()
        self.encounter.patient_info = self.patient_info_input.toPlainText().strip()
        self.encounter.meeting_description = (
            self.meeting_description_input.toPlainText().strip()
        )
        self.encounter.information_relevance = (
            self.information_relevance_input.text().strip()
        )
        self.encounter.information_importance = (
            self.information_importance_input.text().strip()
        )
        self.encounter.information_timeliness = (
            self.information_timeliness_combo.currentData() or ""
        )
        self.encounter.information_completeness = (
            self.information_completeness_combo.currentData() or ""
        )
        self.encounter.information_novelty = (
            self.information_novelty_combo.currentData() or ""
        )
        self.encounter.information_reliability = (
            self.information_reliability_combo.currentData() or ""
        )
        self.encounter.patient_tasks = self.patient_tasks_input.toPlainText().strip()

        # Собираем выбранные пункты плана
        selected_plan_items = []
        for row in range(self.plan_items_table.rowCount()):
            check_item = self.plan_items_table.item(row, 0)
            if check_item and check_item.text() == "✓":
                event_item = self.plan_items_table.item(row, 1)
                if event_item:
                    selected_plan_items.append(event_item.text())
        self.encounter.patient_measures = "\n".join(selected_plan_items)

        self.encounter.general_measures = (
            self.general_measures_input.toPlainText().strip()
        )

        # Сначала сохраняем встречу (чтобы получить id если его не было)
        self.encounter.save()

        # Теперь сохраняем всех информаторов с правильным encounter_id
        self._save_informants()

        # Создание/обновление записи КМ
        self._save_km_record()

        QMessageBox.information(self, "Успешно", "Встреча сохранена")
        self.accept()

    def _save_informants(self):
        """Сохранение всех информаторов после сохранения встречи"""
        for informant_id in self.deleted_informant_ids:
            existing_informant = EncounterInformant.get_by_id(informant_id)
            if existing_informant:
                existing_informant.delete()

        for informant in self.informants:
            informant.encounter_id = self.encounter.id
            informant.save()

        self.deleted_informant_ids.clear()
        self.informants_modified = False

    def _save_km_record(self):
        """Синхронизация записей в таблице КМ по текущим информаторам"""
        from models.db_models import Document, KmRecord

        # Получаем номер документа, если он есть
        doc_number = ""
        if self.encounter.document_id:
            doc = Document.get_by_id(self.encounter.document_id)
            if doc and doc.doc_number:
                doc_number = str(doc.doc_number)

        KmRecord.delete_by_encounter(self.encounter.id)

        for informant in self.informants:
            km_record = KmRecord()
            km_record.callsign = self.patient.callsign
            km_record.personal_number = self.patient.personal_number or ""
            km_record.document_number = doc_number
            km_record.position = informant.position or ""
            km_record.full_name = informant.full_name or ""
            km_record.birth_date = informant.birth_date
            km_record.workplace = informant.workplace or ""
            km_record.info_essence = informant.info_essence or ""
            km_record.measures_taken = informant.measures_taken or ""
            km_record.encounter_id = self.encounter.id
            km_record.document_id = self.encounter.document_id
            km_record.save()

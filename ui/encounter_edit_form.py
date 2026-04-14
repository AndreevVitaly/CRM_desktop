"""
Окно редактирования встречи (Encounter Edit Form)
Расширенная форма с полями: результат встречи, информация от пациента,
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
    QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from models.db_models import (
    User,
    Patient,
    Encounter,
    EncounterInformant,
    TreatmentPlanItem,
    KmRecord,
)
from ui.styles import get_colors, FONTS, RADIUS


class EncounterInformantDialog(QDialog):
    """Диалог добавления/редактирования информатора"""

    def __init__(self, informant: EncounterInformant = None):
        super().__init__()
        self.informant = informant
        self.setWindowTitle("Информатор")
        self.setMinimumSize(450, 400)
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
        # Флаг для отслеживания изменений в информаторах
        self.informants_modified = False

        title = f"Редактирование встречи от {encounter.started_at.strftime('%d.%m.%Y %H:%M')}"
        self.setWindowTitle(title)
        self.setMinimumSize(800, 700)
        self._init_ui()

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
        self.meeting_result_combo.addItem("Выберите результат", "")
        for value, label in Encounter.MEETING_RESULT_CHOICES:
            self.meeting_result_combo.addItem(label, value)
        result_layout.addRow("Результат встречи*", self.meeting_result_combo)

        # Позывной и личный номер (автозаполнение из пациента)
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

        # Группа 2: Информация от пациента
        patient_info_group = QGroupBox("Информация от пациента")
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
        self.patient_info_input.setPlaceholderText("Введите информацию от пациента")
        self.patient_info_input.setMaximumHeight(100)
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
        self.meeting_description_input.setMaximumHeight(100)
        description_layout.addWidget(self.meeting_description_input)

        description_group.setLayout(description_layout)
        layout.addWidget(description_group)

        # Группа 4: Мероприятия для исполнения пациентом
        patient_tasks_group = QGroupBox("Мероприятия для исполнения пациентом")
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
        self.patient_tasks_input.setMaximumHeight(100)
        patient_tasks_layout.addRow(
            "Мероприятия и способ исполнения", self.patient_tasks_input
        )

        patient_tasks_group.setLayout(patient_tasks_layout)
        layout.addWidget(patient_tasks_group)

        # Группа 5: Мероприятия в отношении пациента (из плана)
        patient_measures_group = QGroupBox(
            "Мероприятия в отношении пациента (из плана)"
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

        # Таблица пунктов плана
        self.plan_items_table = QTableWidget()
        self.plan_items_table.setColumnCount(3)
        self.plan_items_table.setHorizontalHeaderLabels(["✓", "Мероприятие", "Срок"])
        self.plan_items_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.plan_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plan_items_table.verticalHeader().setVisible(False)
        self.plan_items_table.setMaximumHeight(150)
        patient_measures_layout.addWidget(self.plan_items_table)

        # Загрузка пунктов плана
        self._load_plan_items()

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
        self.general_measures_input.setMaximumHeight(100)
        general_measures_layout.addWidget(self.general_measures_input)

        general_measures_group.setLayout(general_measures_layout)
        layout.addWidget(general_measures_group)

        # Группа 7: О ком сообщил пациент (Информаторы)
        informants_group = QGroupBox("О ком сообщил пациент")
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
        informants_layout.setSpacing(8)

        # Таблица информаторов
        self.informants_table = QTableWidget()
        self.informants_table.setColumnCount(4)
        self.informants_table.setHorizontalHeaderLabels(
            ["Должность", "ФИО", "Дата рождения", "Место работы"]
        )
        self.informants_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.informants_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.informants_table.verticalHeader().setVisible(False)
        self.informants_table.setMinimumHeight(200)
        self.informants_table.setMaximumHeight(400)
        informants_layout.addWidget(self.informants_table)

        # Кнопки управления информаторами
        informants_buttons = QHBoxLayout()
        add_informant_btn = QPushButton("Добавить информатора")
        add_informant_btn.setFixedHeight(32)
        add_informant_btn.clicked.connect(self._add_informant)
        informants_buttons.addWidget(add_informant_btn)

        edit_informant_btn = QPushButton("Редактировать")
        edit_informant_btn.setObjectName("secondaryBtn")
        edit_informant_btn.setFixedHeight(32)
        edit_informant_btn.clicked.connect(self._edit_informant)
        informants_buttons.addWidget(edit_informant_btn)

        delete_informant_btn = QPushButton("Удалить")
        delete_informant_btn.setObjectName("dangerBtn")
        delete_informant_btn.setFixedHeight(32)
        delete_informant_btn.clicked.connect(self._delete_informant)
        informants_buttons.addWidget(delete_informant_btn)

        informants_buttons.addStretch()
        informants_layout.addLayout(informants_buttons)

        # Загрузка информаторов
        self._load_informants()

        informants_group.setLayout(informants_layout)
        layout.addWidget(informants_group)

        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Кнопки сохранения/отмены
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

        # Заполнение при редактировании
        self._fill_data()

    def _load_plan_items(self):
        """Загрузка пунктов плана лечения пациента"""
        self.plan_items_table.setRowCount(0)

        # Получаем все планы пациента
        from models.db_models import Document, DOCUMENT_TYPE_PLAN

        plans = Document.get_by_patient(self.patient.id)
        plan_docs = [d for d in plans if d.doc_type == DOCUMENT_TYPE_PLAN]

        # Загружаем все пункты из всех планов
        all_items = []
        for plan_doc in plan_docs:
            items = TreatmentPlanItem.get_by_plan(plan_doc.id)
            all_items.extend(items)

        for item in all_items:
            row = self.plan_items_table.rowCount()
            self.plan_items_table.insertRow(row)

            check_item = QTableWidgetItem("✓" if item.is_completed else "")
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.plan_items_table.setItem(row, 0, check_item)

            self.plan_items_table.setItem(row, 1, QTableWidgetItem(item.event))

            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            self.plan_items_table.setItem(row, 2, QTableWidgetItem(due_date))

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
            informant.save()
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
            informant.delete()
            self.informants.pop(row)
            self._load_informants()

    def _fill_data(self):
        """Заполнение данными встречи"""
        # Результат встречи
        if self.encounter.meeting_result:
            index = self.meeting_result_combo.findData(self.encounter.meeting_result)
            if index >= 0:
                self.meeting_result_combo.setCurrentIndex(index)

        # Информация от пациента
        self.patient_info_input.setPlainText(self.encounter.patient_info or "")

        # Описание встречи
        self.meeting_description_input.setPlainText(
            self.encounter.meeting_description or ""
        )

        # Мероприятия для исполнения пациентом
        self.patient_tasks_input.setPlainText(self.encounter.patient_tasks or "")

        # Мероприятия в отношении пациента (из выбранных пунктов плана)
        # Здесь можно добавить логику выделения пунктов
        # Пока просто загружаем все пункты

        # Мероприятия общего формата
        self.general_measures_input.setPlainText(self.encounter.general_measures or "")

    def _save(self):
        """Сохранение встречи"""
        # Валидация
        meeting_result = self.meeting_result_combo.currentData()
        if not meeting_result:
            QMessageBox.warning(self, "Ошибка", "Выберите результат встречи")
            return

        # Сохранение основных полей
        self.encounter.meeting_result = meeting_result
        self.encounter.patient_info = self.patient_info_input.toPlainText().strip()
        self.encounter.meeting_description = (
            self.meeting_description_input.toPlainText().strip()
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
        for informant in self.informants:
            informant.encounter_id = self.encounter.id
            informant.save()

    def _save_km_record(self):
        """Сохранение/обновление записи в таблицу КМ"""
        from models.db_models import KmRecord

        # Получаем номер документа, если он есть
        doc_number = ""
        if self.encounter.document_id:
            from models.db_models import Document

            doc = Document.get_by_id(self.encounter.document_id)
            if doc and doc.doc_number:
                doc_number = str(doc.doc_number)

        # Берем данные из информатора (если есть)
        informant_position = ""
        informant_full_name = ""
        informant_birth_date = None
        informant_workplace = ""
        if self.informants:
            informant = self.informants[0]
            informant_position = informant.position or ""
            informant_full_name = informant.full_name or ""
            informant_birth_date = informant.birth_date
            informant_workplace = informant.workplace or ""

        # Проверяем, есть ли уже запись КМ для этой встречи
        existing_records = KmRecord.get_by_encounter(self.encounter.id)

        if existing_records:
            # Обновляем существующую запись
            km_record = existing_records[0]
        else:
            # Создаём новую запись
            km_record = KmRecord()

        km_record.callsign = self.patient.callsign
        km_record.personal_number = self.patient.personal_number or ""
        km_record.document_number = doc_number
        km_record.position = informant_position
        km_record.full_name = informant_full_name
        km_record.birth_date = informant_birth_date
        km_record.workplace = informant_workplace
        # Суть информации берём из "Информация от пациента" встречи
        km_record.info_essence = self.encounter.patient_info or ""
        km_record.measures_taken = ""
        km_record.encounter_id = self.encounter.id
        km_record.document_id = self.encounter.document_id
        km_record.save()

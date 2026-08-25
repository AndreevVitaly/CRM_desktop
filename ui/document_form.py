"""
Форма добавления/редактирования документа
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QMessageBox,
    QTextEdit,
    QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from models.db_models import (
    User,
    Patient,
    Document,
    EncounterGroup,
    DOCUMENT_CLASSIFICATION_CHOICES,
    DOCUMENT_TYPE_PLAN,
    DOCUMENT_TYPE_MEETING,
)
from ui.styles import get_colors, FONTS, RADIUS


class DocumentFormDialog(QDialog):
    """Диалог формы документа"""

    def __init__(
        self,
        user: User,
        patient: Patient | None,
        document: Document = None,
        allow_patient_select: bool = False,
    ):
        super().__init__()
        self.user = user
        self.patient = patient
        self.document = document
        self.allow_patient_select = allow_patient_select
        self.is_edit = document is not None and document.id is not None

        title = "Редактирование документа" if self.is_edit else "Новый документ"
        self.setWindowTitle(title)
        self.setMinimumSize(800, 700)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()
        compact_font = QFont("Segoe UI", 9)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.Box)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Основная форма
        form_group = QGroupBox("Информация о документе")
        form_group.setStyleSheet(self._get_group_style(colors))
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        if self.allow_patient_select:
            self.patient_combo = QComboBox()
            self.patient_combo.setFrame(False)
            self.patient_combo.setFont(compact_font)
            self.patient_combo.setMinimumHeight(34)
            self.patient_combo.addItem("Без категории АА", None)
            for patient in Patient.get_all(user=self.user, include_inactive=False):
                number = f" · {patient.personal_number}" if patient.personal_number else ""
                self.patient_combo.addItem(f"{patient.callsign}{number}", patient.id)
            form_layout.addRow("Категория АА", self.patient_combo)

        self.group_combo = QComboBox()
        self.group_combo.setFrame(False)
        self.group_combo.setFont(compact_font)
        self.group_combo.setMinimumHeight(34)
        self.group_combo.addItem("Без признака", None)
        for group in EncounterGroup.get_all():
            self.group_combo.addItem(
                f"{group.name} · {group.category_display}",
                group.id,
            )
        form_layout.addRow("Признак", self.group_combo)

        # Гриф секретности
        self.classification_combo = QComboBox()
        self.classification_combo.setFrame(False)
        self.classification_combo.setFont(compact_font)
        self.classification_combo.setMinimumHeight(34)
        for value, label in DOCUMENT_CLASSIFICATION_CHOICES:
            self.classification_combo.addItem(label, value)
        form_layout.addRow("Гриф секретности*", self.classification_combo)

        # Дата документа
        self.doc_date_input = QDateEdit()
        self.doc_date_input.setCalendarPopup(True)
        self.doc_date_input.setDate(QDate.currentDate())
        self.doc_date_input.setDisplayFormat("dd.MM.yyyy")
        self.doc_date_input.setFont(compact_font)
        self.doc_date_input.setMinimumHeight(34)
        form_layout.addRow("Дата*", self.doc_date_input)

        # Номер документа
        self.doc_number_input = QLineEdit()
        self.doc_number_input.setFont(compact_font)
        self.doc_number_input.setMinimumHeight(34)
        self.doc_number_input.setPlaceholderText("Введите номер документа")
        form_layout.addRow("Номер документа", self.doc_number_input)

        # Тип документа (выпадающий список)
        self.doc_type_selector = QComboBox()
        self.doc_type_selector.setFont(compact_font)
        self.doc_type_selector.setMinimumHeight(34)
        self.doc_type_selector.setFrame(False)
        self.doc_type_selector.addItem("Выберите тип документа", "")
        self.doc_type_selector.addItem("План работы с категорией АА", DOCUMENT_TYPE_PLAN)
        self.doc_type_selector.addItem("Встреча", DOCUMENT_TYPE_MEETING)
        self.doc_type_selector.addItem("Иной документ (ручной ввод)", "custom")
        form_layout.addRow("Тип документа*", self.doc_type_selector)

        # Поле для ручного ввода вида документа (скрыто по умолчанию)
        self.doc_type_input = QLineEdit()
        self.doc_type_input.setFont(compact_font)
        self.doc_type_input.setMinimumHeight(34)
        self.doc_type_input.setPlaceholderText("Введите вид документа")
        self.doc_type_input.setVisible(False)
        form_layout.addRow("Вид документа*", self.doc_type_input)

        # Подключение сигнала для показа/скрытия поля ручного ввода
        self.doc_type_selector.currentIndexChanged.connect(self._on_doc_type_changed)

        # Краткое содержание
        self.summary_input = QTextEdit()
        self.summary_input.setFont(compact_font)
        self.summary_input.document().setDocumentMargin(6)
        self.summary_input.setMinimumHeight(72)
        self.summary_input.setPlaceholderText("Введите краткое содержание")
        self.summary_input.setMaximumHeight(100)
        form_layout.addRow("Краткое содержание", self.summary_input)

        # Куда приобщён
        self.location_input = QTextEdit()
        self.location_input.setFont(compact_font)
        self.location_input.document().setDocumentMargin(6)
        self.location_input.setMinimumHeight(72)
        self.location_input.setMaximumHeight(100)
        self.location_input.setPlaceholderText("Введите, куда приобщён документ")
        form_layout.addRow("Куда приобщён", self.location_input)

        self._apply_form_styles(colors)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        layout.addStretch()

        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("secondaryBtn")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(self._get_dialog_button_style(colors))
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(self._get_dialog_button_style(colors))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(
            f"""
            background-color: {colors['bg']};
            color: {colors['text']};
            QGroupBox {{
                color: {colors['text']};
            }}
            QLabel {{
                font-size: 9pt;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                font-size: 9pt;
                padding: 4px 8px;
                min-height: 24px;
            }}
            QTextEdit {{
                font-size: 9pt;
                padding: 6px 8px;
            }}
            """
        )

        # Заполнение данными при редактировании
        if self.is_edit:
            self._fill_data()

    def _get_group_style(self, colors) -> str:
        return f"""
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

    def _apply_form_styles(self, colors):
        """Локально фиксирует читаемость полей формы документа."""
        input_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 4px 8px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """
        text_edit_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 8px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """

        for widget in (
            getattr(self, "patient_combo", None),
            self.group_combo,
            self.classification_combo,
            self.doc_date_input,
            self.doc_number_input,
            self.doc_type_selector,
            self.doc_type_input,
            self.location_input,
        ):
            if widget is not None:
                widget.setStyleSheet(input_style)

        self.summary_input.setStyleSheet(text_edit_style)

    def _get_dialog_button_style(self, colors) -> str:
        return f"""
            QPushButton#secondaryBtn {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 8px 18px;
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

    def _on_doc_type_changed(self, index):
        """Обработка изменения типа документа"""
        selected_type = self.doc_type_selector.currentData()
        # Показываем поле ручного ввода только при выборе "Иной документ"
        self.doc_type_input.setVisible(selected_type == "custom")

    def _fill_data(self):
        """Заполнение данными документа"""
        if not self.document:
            return

        if self.allow_patient_select and hasattr(self, "patient_combo"):
            patient_index = self.patient_combo.findData(self.document.patient_id)
            if patient_index >= 0:
                self.patient_combo.setCurrentIndex(patient_index)

        group_index = self.group_combo.findData(self.document.group_id)
        if group_index >= 0:
            self.group_combo.setCurrentIndex(group_index)

        # Гриф секретности
        class_index = self.classification_combo.findData(self.document.classification)
        if class_index >= 0:
            self.classification_combo.setCurrentIndex(class_index)

        # Дата
        if self.document.doc_date:
            self.doc_date_input.setDate(
                QDate(
                    self.document.doc_date.year,
                    self.document.doc_date.month,
                    self.document.doc_date.day,
                )
            )

        # Номер документа
        if self.document.doc_number is not None:
            self.doc_number_input.setText(str(self.document.doc_number))
        else:
            self.doc_number_input.setText("")

        # Тип документа
        if self.document.doc_type == DOCUMENT_TYPE_PLAN:
            selector_index = self.doc_type_selector.findData(DOCUMENT_TYPE_PLAN)
            self.doc_type_selector.setCurrentIndex(selector_index)
        elif self.document.doc_type == DOCUMENT_TYPE_MEETING:
            selector_index = self.doc_type_selector.findData(DOCUMENT_TYPE_MEETING)
            self.doc_type_selector.setCurrentIndex(selector_index)
        else:
            selector_index = self.doc_type_selector.findData("custom")
            self.doc_type_selector.setCurrentIndex(selector_index)
            self.doc_type_input.setVisible(True)
            self.doc_type_input.setText(self.document.doc_type or "")

        # Краткое содержание
        self.summary_input.setPlainText(self.document.summary or "")

        # Куда приобщён
        self.location_input.setPlainText(self.document.location or "")

    def _save(self):
        """Сохранение документа"""
        # Валидация типа документа
        selected_type = self.doc_type_selector.currentData()
        if not selected_type:
            QMessageBox.warning(self, "Ошибка", "Выберите тип документа")
            return

        # Определяем вид документа
        if selected_type == "custom":
            doc_type = self.doc_type_input.text().strip()
            if not doc_type:
                QMessageBox.warning(self, "Ошибка", "Введите вид документа")
                return
        else:
            doc_type = selected_type

        # Создание/обновление документа
        if not self.document:
            self.document = Document()

        selected_patient = self.patient
        if self.allow_patient_select and hasattr(self, "patient_combo"):
            selected_patient_id = self.patient_combo.currentData()
            selected_patient = (
                Patient.get_by_id(selected_patient_id) if selected_patient_id else None
            )

        self.patient = selected_patient
        self.document.patient_id = selected_patient.id if selected_patient else 0
        self.document.group_id = self.group_combo.currentData()
        self.document.classification = self.classification_combo.currentData()
        self.document.doc_date = self.doc_date_input.date().toPyDate()
        self.document.author_id = self.user.id
        self.document.doc_type = doc_type
        self.document.summary = self.summary_input.toPlainText().strip()
        self.document.location = self.location_input.toPlainText().strip()
        self.document.patient_personal_number = (
            selected_patient.personal_number if selected_patient else ""
        ) or ""

        # Номер документа (пустая строка сохраняется как None)
        doc_number_str = self.doc_number_input.text().strip()
        self.document.doc_number = doc_number_str if doc_number_str else None

        if not self.is_edit:
            self.document.encounter_id = None

        self.document.save()

        QMessageBox.information(self, "Успешно", f"Документ сохранён")
        self.accept()

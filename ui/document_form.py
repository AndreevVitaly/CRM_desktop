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
)
from PyQt6.QtCore import Qt, QDate

from models.db_models import (
    User,
    Patient,
    Document,
    DOCUMENT_CLASSIFICATION_CHOICES,
    DOCUMENT_TYPE_PLAN,
)
from ui.styles import get_colors, FONTS, RADIUS


class DocumentFormDialog(QDialog):
    """Диалог формы документа"""

    def __init__(self, user: User, patient: Patient, document: Document = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.document = document
        self.is_edit = document is not None and document.id is not None

        title = "Редактирование документа" if self.is_edit else "Новый документ"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 500)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Основная форма
        form_group = QGroupBox("Информация о документе")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        # Гриф секретности
        self.classification_combo = QComboBox()
        self.classification_combo.setFrame(False)
        for value, label in DOCUMENT_CLASSIFICATION_CHOICES:
            self.classification_combo.addItem(label, value)
        form_layout.addRow("Гриф секретности*", self.classification_combo)

        # Дата документа
        self.doc_date_input = QDateEdit()
        self.doc_date_input.setCalendarPopup(True)
        self.doc_date_input.setDate(QDate.currentDate())
        self.doc_date_input.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Дата*", self.doc_date_input)

        # Номер документа
        self.doc_number_input = QLineEdit()
        self.doc_number_input.setPlaceholderText("Введите номер документа")
        form_layout.addRow("Номер документа", self.doc_number_input)

        # Тип документа (выпадающий список)
        self.doc_type_selector = QComboBox()
        self.doc_type_selector.setFrame(False)
        self.doc_type_selector.addItem("Выберите тип документа", "")
        self.doc_type_selector.addItem("План работы с пациентом", DOCUMENT_TYPE_PLAN)
        self.doc_type_selector.addItem("Иной документ (ручной ввод)", "custom")
        form_layout.addRow("Тип документа*", self.doc_type_selector)

        # Поле для ручного ввода вида документа (скрыто по умолчанию)
        self.doc_type_input = QLineEdit()
        self.doc_type_input.setPlaceholderText("Введите вид документа")
        self.doc_type_input.setVisible(False)
        form_layout.addRow("Вид документа*", self.doc_type_input)

        # Подключение сигнала для показа/скрытия поля ручного ввода
        self.doc_type_selector.currentIndexChanged.connect(self._on_doc_type_changed)

        # Краткое содержание
        self.summary_input = QTextEdit()
        self.summary_input.setPlaceholderText("Введите краткое содержание")
        self.summary_input.setMaximumHeight(100)
        form_layout.addRow("Краткое содержание", self.summary_input)

        # Куда приобщён
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Введите, куда приобщён документ")
        form_layout.addRow("Куда приобщён*", self.location_input)

        # Личный номер пациента (автозаполнение из карточки пациента)
        self.patient_personal_number_input = QLineEdit()
        self.patient_personal_number_input.setReadOnly(True)
        if self.patient.personal_number:
            self.patient_personal_number_input.setText(self.patient.personal_number)
        else:
            self.patient_personal_number_input.setText("Не присвоен")
        form_layout.addRow("Личный номер пациента", self.patient_personal_number_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("secondaryBtn")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

        # Заполнение данными при редактировании
        if self.is_edit:
            self._fill_data()

    def _on_doc_type_changed(self, index):
        """Обработка изменения типа документа"""
        selected_type = self.doc_type_selector.currentData()
        # Показываем поле ручного ввода только при выборе "Иной документ"
        self.doc_type_input.setVisible(selected_type == "custom")

    def _fill_data(self):
        """Заполнение данными документа"""
        if not self.document:
            return

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
        else:
            selector_index = self.doc_type_selector.findData("custom")
            self.doc_type_selector.setCurrentIndex(selector_index)
            self.doc_type_input.setVisible(True)
            self.doc_type_input.setText(self.document.doc_type or "")

        # Краткое содержание
        self.summary_input.setPlainText(self.document.summary or "")

        # Куда приобщён
        self.location_input.setText(self.document.location or "")

        # Личный номер пациента (всегда из карточки пациента)
        if self.patient.personal_number:
            self.patient_personal_number_input.setText(self.patient.personal_number)
        else:
            self.patient_personal_number_input.setText("Не присвоен")

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

        if not self.location_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите, куда приобщён документ")
            return

        # Создание/обновление документа
        if not self.document:
            self.document = Document()

        self.document.patient_id = self.patient.id
        self.document.classification = self.classification_combo.currentData()
        self.document.doc_date = self.doc_date_input.date().toPyDate()
        self.document.author_id = self.user.id
        self.document.doc_type = doc_type
        self.document.summary = self.summary_input.toPlainText().strip()
        self.document.location = self.location_input.text().strip()
        self.document.patient_personal_number = self.patient.personal_number or ""

        # Номер документа (пустая строка сохраняется как None)
        doc_number_str = self.doc_number_input.text().strip()
        self.document.doc_number = doc_number_str if doc_number_str else None

        self.document.save()

        QMessageBox.information(self, "Успешно", f"Документ сохранён")
        self.accept()

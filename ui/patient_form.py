"""
Форма добавления/редактирования пациента
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
    QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from models.db_models import (
    User,
    Patient,
    Facility,
    DEPARTMENTS,
    GENDER_CHOICES,
    PATIENT_TYPE_CHOICES,
)
from ui.styles import get_colors, FONTS, RADIUS


class PatientFormDialog(QDialog):
    """Диалог формы пациента"""

    def __init__(self, user: User, patient: Patient = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.is_edit = patient is not None and patient.id is not None

        title = "Редактирование пациента" if self.is_edit else "Новый пациент"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 700)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        scroll.setWidget(content_widget)

        form_layout = QVBoxLayout(content_widget)
        form_layout.setSpacing(12)

        # Личные данные
        personal_group = self._create_personal_group()
        form_layout.addWidget(personal_group)

        # Контакты
        contact_group = self._create_contact_group()
        form_layout.addWidget(contact_group)

        # Документы
        doc_group = self._create_document_group()
        form_layout.addWidget(doc_group)

        # Размещение
        facility_group = self._create_facility_group()
        form_layout.addWidget(facility_group)

        layout.addWidget(scroll)

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

    def _create_personal_group(self) -> QGroupBox:
        """Группа личных данных"""
        group = QGroupBox("Личные данные")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        # Позывной
        self.callsign_input = QLineEdit()
        self.callsign_input.setPlaceholderText("Позывной")
        layout.addRow("Позывной*", self.callsign_input)

        # Личный номер
        self.personal_number_input = QLineEdit()
        self.personal_number_input.setPlaceholderText("Личный номер")
        self.personal_number_input.setInputMethodHints(
            Qt.InputMethodHint.ImhDigitsOnly | Qt.InputMethodHint.ImhPreferNumbers
        )
        layout.addRow("Личный номер", self.personal_number_input)

        # Дата рождения
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate().addYears(-18))
        self.birth_date_input.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Дата рождения*", self.birth_date_input)

        # Пол
        self.gender_combo = QComboBox()
        self.gender_combo.setFrame(False)
        for value, label in GENDER_CHOICES:
            self.gender_combo.addItem(label, value)
        layout.addRow("Пол*", self.gender_combo)

        # Тип пациента
        self.type_combo = QComboBox()
        self.type_combo.setFrame(False)
        for value, label in PATIENT_TYPE_CHOICES:
            self.type_combo.addItem(label, value)
        layout.addRow("Тип пациента*", self.type_combo)

        # Отделение
        self.dept_combo = QComboBox()
        self.dept_combo.setFrame(False)
        for value, label in DEPARTMENTS:
            self.dept_combo.addItem(label, value)

        # Ограничение по отделению для LEAD
        if self.user.role == User.ROLE_LEAD:
            self.dept_combo.setCurrentText(self.user.department_display)
            self.dept_combo.setEnabled(False)

        layout.addRow("Отделение*", self.dept_combo)

        group.setLayout(layout)
        return group

    def _create_contact_group(self) -> QGroupBox:
        """Группа контактов"""
        group = QGroupBox("Контакты")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7 (___) ___-__-__")
        layout.addRow("Телефон", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        layout.addRow("Email", self.email_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Адрес проживания")
        layout.addRow("Адрес", self.address_input)

        self.emergency_input = QLineEdit()
        self.emergency_input.setPlaceholderText("ФИО, телефон")
        layout.addRow("Контакт для связи", self.emergency_input)

        group.setLayout(layout)
        return group

    def _create_document_group(self) -> QGroupBox:
        """Группа документов"""
        group = QGroupBox("Документы")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.document_id_input = QLineEdit()
        self.document_id_input.setPlaceholderText("Личный номер")
        layout.addRow("Личный номер", self.document_id_input)

        self.insurance_input = QLineEdit()
        self.insurance_input.setPlaceholderText("Номер полиса")
        layout.addRow("Полис", self.insurance_input)

        self.employer_input = QLineEdit()
        self.employer_input.setPlaceholderText("Место работы")
        layout.addRow("Место работы", self.employer_input)

        group.setLayout(layout)
        return group

    def _create_facility_group(self) -> QGroupBox:
        """Группа размещения"""
        group = QGroupBox("Место размещения")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.facility_combo = QComboBox()
        self.facility_combo.setFrame(False)
        self.facility_combo.addItem("Не выбрано", 0)
        facilities = Facility.get_all()
        for f in facilities:
            self.facility_combo.addItem(f.name, f.id)
        layout.addRow("Учреждение", self.facility_combo)

        # Врач (только для ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            self.doctor_combo = QComboBox()
            self.doctor_combo.setFrame(False)
            self.doctor_combo.addItem("Не назначен", 0)

            # Получаем врачей
            if self.user.role == User.ROLE_LEAD:
                doctors = User.get_doctors_by_department(self.user.department)
            else:
                doctors = User.get_by_role(User.ROLE_DOCTOR)

            for doc in doctors:
                self.doctor_combo.addItem(doc.full_name, doc.id)

            layout.addRow("Лечащий врач", self.doctor_combo)

        group.setLayout(layout)
        return group

    def _fill_data(self):
        """Заполнение данными пациента"""
        if not self.patient:
            return

        # Личные данные
        self.callsign_input.setText(self.patient.callsign or "")
        self.personal_number_input.setText(self.patient.personal_number or "")
        self.birth_date_input.setDate(
            QDate(
                self.patient.birth_date.year,
                self.patient.birth_date.month,
                self.patient.birth_date.day,
            )
        )
        self.gender_combo.setCurrentText(
            "Мужской" if self.patient.gender == "M" else "Женский"
        )
        type_display = {"adult": "Взрослый", "child": "Детский", "undefined": "Неопределённый"}
        self.type_combo.setCurrentText(
            type_display.get(self.patient.patient_type, "Взрослый")
        )

        # Найти отделение в списке
        dept_index = self.dept_combo.findData(self.patient.department)
        if dept_index >= 0:
            self.dept_combo.setCurrentIndex(dept_index)

        # Контакты
        self.phone_input.setText(self.patient.phone or "")
        self.email_input.setText(self.patient.email or "")
        self.address_input.setText(self.patient.address or "")
        self.emergency_input.setText(self.patient.emergency_contact or "")

        # Документы
        self.document_id_input.setText(self.patient.document_id or "")
        self.insurance_input.setText(self.patient.insurance_number or "")
        self.employer_input.setText(self.patient.employer or "")

        # Размещение
        if self.patient.facility_id:
            facility_index = self.facility_combo.findData(self.patient.facility_id)
            if facility_index >= 0:
                self.facility_combo.setCurrentIndex(facility_index)

        # Врач
        if hasattr(self, "doctor_combo") and self.patient.doctor_id:
            doctor_index = self.doctor_combo.findData(self.patient.doctor_id)
            if doctor_index >= 0:
                self.doctor_combo.setCurrentIndex(doctor_index)

    def _save(self):
        """Сохранение пациента"""
        # Валидация
        if not self.callsign_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите позывной")
            return

        # Создание/обновление пациента
        if not self.patient:
            self.patient = Patient()

        self.patient.callsign = self.callsign_input.text().strip()
        self.patient.personal_number = self.personal_number_input.text().strip()
        self.patient.birth_date = self.birth_date_input.date().toPyDate()
        self.patient.gender = self.gender_combo.currentData()
        self.patient.patient_type = self.type_combo.currentData()
        self.patient.department = self.dept_combo.currentData()

        self.patient.phone = self.phone_input.text().strip()
        self.patient.email = self.email_input.text().strip()
        self.patient.address = self.address_input.text().strip()
        self.patient.emergency_contact = self.emergency_input.text().strip()

        self.patient.document_id = self.document_id_input.text().strip()
        self.patient.insurance_number = self.insurance_input.text().strip()
        self.patient.employer = self.employer_input.text().strip()

        facility_id = self.facility_combo.currentData()
        self.patient.facility_id = facility_id if facility_id else None

        if hasattr(self, "doctor_combo"):
            doctor_id = self.doctor_combo.currentData()
            self.patient.doctor_id = doctor_id if doctor_id else None

        # Проверка прав
        if self.user.role == User.ROLE_LEAD:
            if self.patient.department != self.user.department:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Вы можете создавать пациентов только своего отделения",
                )
                return

        self.patient.save()

        QMessageBox.information(
            self, "Успешно", f"Пациент {self.patient.full_name} сохранён"
        )
        self.accept()

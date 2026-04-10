"""
Форма визита (Encounter)
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
    QDateTimeEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from models.db_models import (
    User,
    Patient,
    Encounter,
    Note,
    Prescription,
    PatientInteraction,
)
from ui.styles import get_colors, FONTS, RADIUS


class EncounterFormDialog(QDialog):
    """Диалог формы визита"""

    def __init__(self, user: User, patient: Patient, encounter: Encounter = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.encounter = encounter
        self.is_edit = encounter is not None and encounter.id is not None

        title = "Редактирование визита" if self.is_edit else "Новый визит"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Форма
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Дата и время начала
        self.started_at_input = QDateTimeEdit()
        self.started_at_input.setDateTime(QDateTime.currentDateTime())
        self.started_at_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.started_at_input.setCalendarPopup(True)
        form_layout.addRow("Дата и время начала*", self.started_at_input)

        # Врач
        self.doctor_combo = QComboBox()
        self.doctor_combo.setFrame(False)
        if self.user.role == User.ROLE_DOCTOR:
            self.doctor_combo.addItem(self.user.full_name, self.user.id)
            self.doctor_combo.setEnabled(False)
        else:
            self.doctor_combo.addItem("Не выбран", 0)
            doctors = User.get_by_role(User.ROLE_DOCTOR)
            for doc in doctors:
                self.doctor_combo.addItem(doc.full_name, doc.id)
        form_layout.addRow("Врач*", self.doctor_combo)

        # Причина
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Причина визита, жалобы")
        self.reason_input.setMaximumHeight(100)
        form_layout.addRow("Причина визита", self.reason_input)

        # Статус
        self.status_combo = QComboBox()
        self.status_combo.setFrame(False)
        self.status_combo.addItem("Запланирован", Encounter.STATUS_PLANNED)
        self.status_combo.addItem("В процессе", Encounter.STATUS_INPROGRESS)
        self.status_combo.addItem("Завершен", Encounter.STATUS_FINISHED)
        form_layout.addRow("Статус", self.status_combo)

        layout.addLayout(form_layout)

        # Заметка (опционально)
        note_group = QLabel("📝 Заметка (необязательно)")
        note_group.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(note_group)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Текст заметки")
        self.note_input.setMaximumHeight(80)
        layout.addWidget(self.note_input)

        # Назначение (опционально, для ADMIN, DOC, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            rx_group = QLabel("💊 Назначение (необязательно)")
            rx_group.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(rx_group)

            rx_layout = QFormLayout()
            rx_layout.setSpacing(8)

            self.medication_input = QLineEdit()
            self.medication_input.setPlaceholderText("Название препарата")
            rx_layout.addRow("Препарат", self.medication_input)

            self.dosage_input = QLineEdit()
            self.dosage_input.setPlaceholderText("Дозировка")
            rx_layout.addRow("Дозировка", self.dosage_input)

            self.frequency_input = QLineEdit()
            self.frequency_input.setPlaceholderText("Частота приёма")
            rx_layout.addRow("Частота", self.frequency_input)

            self.duration_input = QSpinBox()
            self.duration_input.setRange(1, 365)
            self.duration_input.setValue(7)
            self.duration_input.setSuffix(" дн.")
            rx_layout.addRow("Длительность", self.duration_input)

            layout.addLayout(rx_layout)

        layout.addStretch()

        # Кнопки
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

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

        # Заполнение при редактировании
        if self.is_edit:
            self._fill_data()

    def _fill_data(self):
        """Заполнение данными визита"""
        if not self.encounter:
            return

        self.started_at_input.setDateTime(
            QDateTime(
                self.encounter.started_at.year,
                self.encounter.started_at.month,
                self.encounter.started_at.day,
                self.encounter.started_at.hour,
                self.encounter.started_at.minute,
            )
        )

        if self.encounter.doctor_id:
            index = self.doctor_combo.findData(self.encounter.doctor_id)
            if index >= 0:
                self.doctor_combo.setCurrentIndex(index)

        index = self.status_combo.findData(self.encounter.status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        self.reason_input.setText(self.encounter.reason or "")

    def _save(self):
        """Сохранение визита"""
        # Валидация
        doctor_id = self.doctor_combo.currentData()
        if not doctor_id:
            QMessageBox.warning(self, "Ошибка", "Выберите врача")
            return

        # Создание/обновление визита
        if not self.encounter:
            self.encounter = Encounter()
            self.encounter.patient_id = self.patient.id

        self.encounter.doctor_id = doctor_id
        self.encounter.started_at = self.started_at_input.dateTime().toPyDateTime()
        self.encounter.reason = self.reason_input.toPlainText().strip()
        self.encounter.status = self.status_combo.currentData()

        self.encounter.save()

        # Сохранение заметки
        note_text = self.note_input.toPlainText().strip()
        if note_text:
            note = Note(
                encounter_id=self.encounter.id, author_id=self.user.id, text=note_text
            )
            note.save()

        # Сохранение назначения
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            if (
                hasattr(self, "medication_input")
                and self.medication_input.text().strip()
            ):
                rx = Prescription(
                    encounter_id=self.encounter.id,
                    medication=self.medication_input.text().strip(),
                    dosage=self.dosage_input.text().strip(),
                    frequency=self.frequency_input.text().strip(),
                    duration_days=self.duration_input.value(),
                    notes="",
                )
                rx.save()

        # Логирование
        interaction = PatientInteraction(
            patient_id=self.patient.id,
            user_id=self.user.id,
            action="visit_created",
            description="Создан новый визит",
        )
        interaction.save()

        QMessageBox.information(self, "Успешно", "Визит сохранён")
        self.accept()


# Импорты для формы назначения
from PyQt6.QtWidgets import QLineEdit, QSpinBox

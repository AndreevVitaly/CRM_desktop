"""
Форма визита (Encounter)
"""

from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from models.db_models import (
    Encounter,
    Note,
    Patient,
    PatientInteraction,
    Prescription,
    User,
)
from ui.styles import RADIUS, get_colors


class EncounterFormDialog(QDialog):
    """Диалог формы визита"""

    def __init__(self, user: User, patient: Patient, encounter: Encounter = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.encounter = encounter
        self.is_edit = encounter is not None and encounter.id is not None

        title = "Редактирование встречи" if self.is_edit else "Новая встреча"
        self.setWindowTitle(title)
        self.setMinimumSize(520, 500)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()
        compact_font = QFont("Segoe UI", 9)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form_group = QGroupBox("Информация о встрече")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.started_at_input = QDateTimeEdit()
        self.started_at_input.setDateTime(QDateTime.currentDateTime())
        self.started_at_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.started_at_input.setCalendarPopup(True)
        self.started_at_input.setFont(compact_font)
        self.started_at_input.setMinimumHeight(34)
        form_layout.addRow("Дата и время начала*", self.started_at_input)

        self.doctor_combo = QComboBox()
        self.doctor_combo.setFrame(False)
        self.doctor_combo.setFont(compact_font)
        self.doctor_combo.setMinimumHeight(34)
        if self.user.role == User.ROLE_DOCTOR:
            self.doctor_combo.addItem(self.user.full_name, self.user.id)
            self.doctor_combo.setEnabled(False)
        else:
            self.doctor_combo.addItem("Не выбран", 0)
            for doctor in User.get_by_role(User.ROLE_DOCTOR):
                self.doctor_combo.addItem(doctor.full_name, doctor.id)
        form_layout.addRow("Врач*", self.doctor_combo)

        self.reason_input = QTextEdit()
        self.reason_input.setFont(compact_font)
        self.reason_input.document().setDocumentMargin(6)
        self.reason_input.setMinimumHeight(72)
        self.reason_input.setMaximumHeight(100)
        self.reason_input.setPlaceholderText("Причина встречи, жалобы")
        form_layout.addRow("Причина встречи", self.reason_input)

        self.status_combo = QComboBox()
        self.status_combo.setFrame(False)
        self.status_combo.setFont(compact_font)
        self.status_combo.setMinimumHeight(34)
        self.status_combo.addItem("Запланирован", Encounter.STATUS_PLANNED)
        self.status_combo.addItem("В процессе", Encounter.STATUS_INPROGRESS)
        self.status_combo.addItem("Завершен", Encounter.STATUS_FINISHED)
        form_layout.addRow("Статус", self.status_combo)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        note_group = QGroupBox("Заметка")
        note_layout = QVBoxLayout()
        note_layout.setContentsMargins(0, 4, 0, 0)

        self.note_input = QTextEdit()
        self.note_input.setFont(compact_font)
        self.note_input.document().setDocumentMargin(6)
        self.note_input.setMinimumHeight(72)
        self.note_input.setMaximumHeight(100)
        self.note_input.setPlaceholderText("Текст заметки")
        note_layout.addWidget(self.note_input)

        note_group.setLayout(note_layout)
        layout.addWidget(note_group)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_LEAD, User.ROLE_DOCTOR):
            rx_group = QGroupBox("Назначение")
            rx_layout = QFormLayout()
            rx_layout.setSpacing(10)
            rx_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            rx_layout.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )

            self.medication_input = QLineEdit()
            self.medication_input.setFrame(False)
            self.medication_input.setFont(compact_font)
            self.medication_input.setMinimumHeight(34)
            self.medication_input.setPlaceholderText("Название препарата")
            rx_layout.addRow("Препарат", self.medication_input)

            self.dosage_input = QLineEdit()
            self.dosage_input.setFrame(False)
            self.dosage_input.setFont(compact_font)
            self.dosage_input.setMinimumHeight(34)
            self.dosage_input.setPlaceholderText("Дозировка")
            rx_layout.addRow("Дозировка", self.dosage_input)

            self.frequency_input = QLineEdit()
            self.frequency_input.setFrame(False)
            self.frequency_input.setFont(compact_font)
            self.frequency_input.setMinimumHeight(34)
            self.frequency_input.setPlaceholderText("Частота приёма")
            rx_layout.addRow("Частота", self.frequency_input)

            self.duration_input = QSpinBox()
            self.duration_input.setFont(compact_font)
            self.duration_input.setMinimumHeight(34)
            self.duration_input.setRange(1, 365)
            self.duration_input.setValue(7)
            self.duration_input.setSuffix(" дн.")
            rx_layout.addRow("Длительность", self.duration_input)

            rx_group.setLayout(rx_layout)
            layout.addWidget(rx_group)

        layout.addStretch()

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
        self._apply_form_styles(colors)
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
            QLineEdit, QComboBox, QDateTimeEdit, QSpinBox {{
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

        if self.is_edit:
            self._fill_data()

    def _apply_form_styles(self, colors):
        """Локально фиксирует стиль полей формы встречи."""
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

        widgets = [
            self.started_at_input,
            self.doctor_combo,
            self.status_combo,
        ]
        if hasattr(self, "medication_input"):
            widgets.extend(
                [
                    self.medication_input,
                    self.dosage_input,
                    self.frequency_input,
                    self.duration_input,
                ]
            )

        for widget in widgets:
            widget.setStyleSheet(input_style)

        self.reason_input.setStyleSheet(text_edit_style)
        self.note_input.setStyleSheet(text_edit_style)

    def _fill_data(self):
        """Заполнение данными встречи"""
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

        self.reason_input.setPlainText(self.encounter.reason or "")

    def _save(self):
        """Сохранение встречи"""
        doctor_id = self.doctor_combo.currentData()
        if not doctor_id:
            QMessageBox.warning(self, "Ошибка", "Выберите врача")
            return

        if not self.encounter:
            self.encounter = Encounter()
            self.encounter.patient_id = self.patient.id

        self.encounter.doctor_id = doctor_id
        self.encounter.started_at = self.started_at_input.dateTime().toPyDateTime()
        self.encounter.reason = self.reason_input.toPlainText().strip()
        self.encounter.status = self.status_combo.currentData()
        self.encounter.save()

        note_text = self.note_input.toPlainText().strip()
        if note_text:
            note = Note(
                encounter_id=self.encounter.id,
                author_id=self.user.id,
                text=note_text,
            )
            note.save()

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

        interaction = PatientInteraction(
            patient_id=self.patient.id,
            user_id=self.user.id,
            action="visit_created",
            description="Создана новая встреча",
        )
        interaction.save()

        QMessageBox.information(self, "Успешно", "Встреча сохранена")
        self.accept()

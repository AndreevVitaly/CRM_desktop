"""
Форма пункта плана лечения
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QTextEdit,
    QDateEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from models.db_models import User, Patient, TreatmentPlanItem
from ui.styles import get_colors, FONTS, RADIUS


class PlanItemFormDialog(QDialog):
    """Диалог формы пункта плана лечения"""

    def __init__(self, user: User, patient: Patient, item: TreatmentPlanItem = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.item = item
        self.is_edit = item is not None and item.id is not None

        title = "Редактирование пункта плана" if self.is_edit else "Новый пункт плана"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
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

        # Мероприятие
        self.event_input = QTextEdit()
        self.event_input.setPlaceholderText("Описание мероприятия")
        self.event_input.setMaximumHeight(100)
        form_layout.addRow("Мероприятие*", self.event_input)

        # Срок исполнения
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate())
        self.due_date_input.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Срок исполнения", self.due_date_input)

        layout.addLayout(form_layout)
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
        """Заполнение данными"""
        if not self.item:
            return

        self.event_input.setText(self.item.event)

        if self.item.due_date:
            self.due_date_input.setDate(
                QDate(
                    self.item.due_date.year,
                    self.item.due_date.month,
                    self.item.due_date.day,
                )
            )

    def _save(self):
        """Сохранение пункта плана"""
        # Валидация
        if not self.event_input.toPlainText().strip():
            QMessageBox.warning(self, "Ошибка", "Введите описание мероприятия")
            return

        # Создание/обновление
        if not self.item:
            self.item = TreatmentPlanItem()
            self.item.patient_id = self.patient.id

        self.item.event = self.event_input.toPlainText().strip()
        self.item.due_date = self.due_date_input.date().toPyDate()

        self.item.save()

        QMessageBox.information(self, "Успешно", "Пункт плана сохранён")
        self.accept()

"""
Форма мероприятия (Event)
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate, QTime
from datetime import datetime, time

from models.db_models import User, Event, DEPARTMENTS, EVENT_TYPES
from ui.styles import get_colors, FONTS, RADIUS


class EventFormDialog(QDialog):
    """Диалог формы мероприятия"""

    def __init__(self, user: User, event: Event = None, default_year: int = 0):
        super().__init__()
        self.user = user
        self.event = event
        self.default_year = default_year
        self.is_edit = event is not None and event.id is not None

        title = "Редактирование мероприятия" if self.is_edit else "Новое мероприятие"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 500)
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

        # Название
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название мероприятия")
        form_layout.addRow("Название*", self.title_input)

        # Описание
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Описание")
        self.desc_input.setMaximumHeight(80)
        form_layout.addRow("Описание", self.desc_input)

        # Тип
        self.type_combo = QComboBox()
        for value, label in EVENT_TYPES:
            self.type_combo.addItem(label, value)
        form_layout.addRow("Тип*", self.type_combo)

        # Год
        self.year_combo = QComboBox()
        current_year = (
            self.default_year if self.default_year else QDate.currentDate().year()
        )
        for y in range(current_year - 5, current_year + 6):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))
        form_layout.addRow("Год*", self.year_combo)

        # Заголовок с годом
        if self.is_edit and self.event and self.event.year:
            self.setWindowTitle(f"{self.windowTitle()} ({self.event.year})")
        elif self.default_year:
            self.setWindowTitle(f"{self.windowTitle()} ({self.default_year})")

        # Дата
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Дата проведения*", self.date_input)

        # Время
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime(9, 0))
        self.time_input.setDisplayFormat("HH:mm")
        form_layout.addRow("Время начала", self.time_input)

        # Отделение
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Общее", "")

        # Ограничение по отделению
        if self.user.role == User.ROLE_LEAD:
            self.dept_combo.addItem(self.user.department_display, self.user.department)
            self.dept_combo.setCurrentIndex(1)
            self.dept_combo.setEnabled(False)
        elif self.user.role in (User.ROLE_DOCTOR, User.ROLE_NURSE):
            self.dept_combo.addItem(self.user.department_display, self.user.department)
        else:
            for value, label in DEPARTMENTS:
                self.dept_combo.addItem(label, value)

        form_layout.addRow("Отделение", self.dept_combo)

        # Ответственный
        self.responsible_combo = QComboBox()
        self.responsible_combo.addItem("Не назначен", 0)

        # Получаем пользователей
        if self.user.role == User.ROLE_LEAD:
            users = User.get_all()
            users = [u for u in users if u.department == self.user.department]
        else:
            users = User.get_all()

        for u in users:
            self.responsible_combo.addItem(u.full_name, u.id)

        form_layout.addRow("Ответственный", self.responsible_combo)

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
        if not self.event:
            return

        self.title_input.setText(self.event.title)
        self.desc_input.setText(self.event.description or "")

        index = self.type_combo.findData(self.event.event_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        if self.event.year:
            year_index = self.year_combo.findData(self.event.year)
            if year_index >= 0:
                self.year_combo.setCurrentIndex(year_index)

        self.date_input.setDate(
            QDate(
                self.event.event_date.year,
                self.event.event_date.month,
                self.event.event_date.day,
            )
        )

        if self.event.event_time:
            self.time_input.setTime(
                QTime(self.event.event_time.hour, self.event.event_time.minute)
            )

        if self.event.department:
            dept_index = self.dept_combo.findData(self.event.department)
            if dept_index >= 0:
                self.dept_combo.setCurrentIndex(dept_index)

        if self.event.responsible_id:
            resp_index = self.responsible_combo.findData(self.event.responsible_id)
            if resp_index >= 0:
                self.responsible_combo.setCurrentIndex(resp_index)

    def _save(self):
        """Сохранение мероприятия"""
        # Валидация
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return

        # Создание/обновление
        if not self.event:
            self.event = Event()

        self.event.title = self.title_input.text().strip()
        self.event.description = self.desc_input.toPlainText().strip()
        self.event.event_type = self.type_combo.currentData()
        self.event.year = self.year_combo.currentData()
        self.event.event_date = self.date_input.date().toPyDate()

        time_val = self.time_input.time().toPyTime()
        if time_val.hour != 0 or time_val.minute != 0:
            self.event.event_time = datetime.combine(self.event.event_date, time_val)
        else:
            self.event.event_time = None

        self.event.department = self.dept_combo.currentData() or None
        self.event.responsible_id = self.responsible_combo.currentData()
        if self.event.responsible_id == 0:
            self.event.responsible_id = None

        self.event.save(user=self.user)

        QMessageBox.information(self, "Успешно", "Мероприятие сохранено")
        self.accept()

"""
Форма добавления/редактирования пользователя
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
    QCheckBox,
    QMessageBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt

from models.db_models import User, DEPARTMENTS, hash_password
from ui.styles import get_colors, FONTS, RADIUS


class UserFormDialog(QDialog):
    """Диалог формы пользователя"""

    def __init__(self, current_user: User, user: User = None):
        super().__init__()
        self.current_user = current_user
        self.user = user
        self.is_edit = user is not None and user.id is not None

        title = "Редактирование пользователя" if self.is_edit else "Новый пользователь"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 500)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Основные данные
        main_group = QGroupBox("📋 Основная информация")
        main_layout = QFormLayout()
        main_layout.setSpacing(12)

        # Логин
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин для входа")
        if self.is_edit:
            self.username_input.setEnabled(False)  # Логин нельзя менять
        main_layout.addRow("Логин*", self.username_input)

        # Пароль
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Придумайте пароль"
            if not self.is_edit
            else "Оставьте пустым для сохранения"
        )
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        main_layout.addRow(
            "Пароль*" if not self.is_edit else "Пароль", self.password_input
        )

        # ФИО
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Имя")
        main_layout.addRow("Имя*", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Фамилия")
        main_layout.addRow("Фамилия*", self.last_name_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        main_layout.addRow("Email", self.email_input)

        main_group.setLayout(main_layout)
        layout.addWidget(main_group)

        # Роль и отделение
        role_group = QGroupBox("👔 Должность")
        role_layout = QFormLayout()
        role_layout.setSpacing(12)

        # Роль
        self.role_combo = QComboBox()
        self.role_combo.setFrame(False)

        # Ограничение доступных ролей
        if self.current_user.role == User.ROLE_ADMIN:
            self.role_combo.addItem("Администратор", User.ROLE_ADMIN)

        self.role_combo.addItem("Регистратор", User.ROLE_REGISTRAR)
        self.role_combo.addItem("Начальник отделения", User.ROLE_LEAD)
        self.role_combo.addItem("Врач", User.ROLE_DOCTOR)
        self.role_combo.addItem("Медсестра", User.ROLE_NURSE)

        # REG не может создавать ADMIN и REG
        if self.current_user.role == User.ROLE_REGISTRAR:
            # Убираем админов и регистраторов из списка
            for i in range(self.role_combo.count()):
                role_data = self.role_combo.itemData(i)
                if role_data in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
                    self.role_combo.removeItem(i)
                    i -= 1

        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        role_layout.addRow("Роль*", self.role_combo)

        # Отделение
        self.dept_combo = QComboBox()
        self.dept_combo.setFrame(False)
        self.dept_combo.addItem("Не выбрано", "")
        for value, label in DEPARTMENTS:
            self.dept_combo.addItem(label, value)

        # LEAD видит только своё отделение
        if self.current_user.role == User.ROLE_LEAD:
            self.dept_combo.setCurrentText(self.current_user.department_display)
            self.dept_combo.setEnabled(False)

        role_layout.addRow("Отделение", self.dept_combo)

        role_group.setLayout(role_layout)
        layout.addWidget(role_group)

        # Статус
        self.active_check = QCheckBox("Активен")
        self.active_check.setChecked(True)
        layout.addWidget(self.active_check)

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

    def _on_role_changed(self, index):
        """Изменение роли"""
        role = self.role_combo.currentData()

        # Показываем отделение только для клинических ролей
        show_dept = role in (User.ROLE_LEAD, User.ROLE_DOCTOR, User.ROLE_NURSE)
        self.dept_combo.setEnabled(show_dept)

    def _fill_data(self):
        """Заполнение данными"""
        if not self.user:
            return

        self.username_input.setText(self.user.username)
        self.first_name_input.setText(self.user.first_name)
        self.last_name_input.setText(self.user.last_name)
        self.email_input.setText(self.user.email or "")

        # Роль
        index = self.role_combo.findData(self.user.role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)

        # Отделение
        if self.user.department:
            dept_index = self.dept_combo.findData(self.user.department)
            if dept_index >= 0:
                self.dept_combo.setCurrentIndex(dept_index)

        # Статус
        self.active_check.setChecked(self.user.is_active)

    def _save(self):
        """Сохранение пользователя"""
        # Валидация
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите логин")
            return

        if not self.is_edit and not self.password_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите пароль")
            return

        if not self.first_name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите имя")
            return

        if not self.last_name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите фамилию")
            return

        # Создание/обновление
        if not self.user:
            self.user = User()

        self.user.username = self.username_input.text().strip()
        self.user.first_name = self.first_name_input.text().strip()
        self.user.last_name = self.last_name_input.text().strip()
        self.user.email = self.email_input.text().strip()
        self.user.role = self.role_combo.currentData()
        self.user.department = self.dept_combo.currentData() or None
        self.user.is_active = self.active_check.isChecked()

        # Пароль
        password = self.password_input.text().strip()
        if password:
            self.user.password_hash = hash_password(password)
        elif not self.is_edit:
            QMessageBox.warning(self, "Ошибка", "Пароль обязателен")
            return

        # Проверка прав
        if self.current_user.role == User.ROLE_REGISTRAR:
            # REG не может создавать/редактировать ADMIN
            if self.user.role == User.ROLE_ADMIN:
                QMessageBox.warning(
                    self, "Ошибка", "Регистратор не может создавать администраторов"
                )
                return

        if self.current_user.role == User.ROLE_LEAD:
            # LEAD может создавать только своё отделение
            if self.user.department != self.current_user.department:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Вы можете создавать пользователей только своего отделения",
                )
                return

        self.user.save()

        QMessageBox.information(
            self, "Успешно", f"Пользователь {self.user.full_name} сохранён"
        )
        self.accept()

"""
Диалог регистрации нового пользователя
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.db_models import User, DEPARTMENTS, hash_password
from ui.styles import get_colors, FONTS, RADIUS


class RegistrationDialog(QDialog):
    """Диалог регистрации нового пользователя"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Регистрация нового пользователя")
        self.setMinimumSize(500, 600)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Заголовок
        title_label = QLabel("📝 Регистрация")
        title_label.setObjectName("title")
        title_label.setStyleSheet(
            f"font-size: {FONTS['size_title']}pt; font-weight: bold;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Создание учётной записи")
        subtitle_label.setObjectName("muted")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # Форма регистрации
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Фамилия
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Иванов")
        self.last_name_input.setFixedHeight(44)
        form_layout.addRow("Фамилия*", self.last_name_input)

        # Имя
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Иван")
        self.first_name_input.setFixedHeight(44)
        form_layout.addRow("Имя*", self.first_name_input)

        # Отчество
        self.middle_name_input = QLineEdit()
        self.middle_name_input.setPlaceholderText("Иванович")
        self.middle_name_input.setFixedHeight(44)
        form_layout.addRow("Отчество", self.middle_name_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        self.email_input.setFixedHeight(44)
        form_layout.addRow("Email", self.email_input)

        # Логин
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Придумайте логин")
        self.username_input.setFixedHeight(44)
        form_layout.addRow("Логин*", self.username_input)

        # Пароль
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Минимум 6 символов")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(44)
        form_layout.addRow("Пароль*", self.password_input)

        # Подтверждение пароля
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Повторите пароль")
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setFixedHeight(44)
        form_layout.addRow("Подтверждение пароля*", self.password_confirm_input)

        # Роль
        self.role_combo = QComboBox()
        self.role_combo.addItem("Регистратор", User.ROLE_REGISTRAR)
        self.role_combo.addItem("Врач", User.ROLE_DOCTOR)
        self.role_combo.addItem("Медсестра", User.ROLE_NURSE)
        self.role_combo.addItem("Начальник отделения", User.ROLE_LEAD)
        self.role_combo.setFixedHeight(44)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        form_layout.addRow("Роль*", self.role_combo)

        # Отделение (для врачей, медсестёр, начальников)
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Не выбрано", "")
        for value, label in DEPARTMENTS:
            self.dept_combo.addItem(label, value)
        self.dept_combo.setFixedHeight(44)
        self.dept_combo.setVisible(False)
        form_layout.addRow("Отделение", self.dept_combo)

        layout.addLayout(form_layout)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        register_btn = QPushButton("✅ Зарегистрироваться")
        register_btn.setFixedHeight(44)
        register_btn.clicked.connect(self._register)
        buttons_layout.addWidget(register_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(44)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

    def _on_role_changed(self, index):
        """Изменение роли - показ/скрытие отделения"""
        role = self.role_combo.itemData(index)
        show_dept = role in (User.ROLE_DOCTOR, User.ROLE_NURSE, User.ROLE_LEAD)
        self.dept_combo.setVisible(show_dept)

    def _register(self):
        """Регистрация пользователя"""
        # Сбор данных
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        middle_name = self.middle_name_input.text().strip()
        email = self.email_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        role = self.role_combo.currentData()
        department = (
            self.dept_combo.currentData() if self.dept_combo.isVisible() else None
        )

        # Валидация
        errors = []

        if not last_name:
            errors.append("Введите фамилию")
        if not first_name:
            errors.append("Введите имя")
        if not username:
            errors.append("Введите логин")
        if not password:
            errors.append("Введите пароль")
        if len(password) < 6:
            errors.append("Пароль должен быть не менее 6 символов")
        if password != password_confirm:
            errors.append("Пароли не совпадают")

        # Проверка уникальности логина
        if username:
            existing_user = User.get_by_username(username)
            if existing_user:
                errors.append("Пользователь с таким логином уже существует")

        if errors:
            QMessageBox.warning(self, "Ошибка регистрации", "\n".join(errors))
            return

        # Создание пользователя
        try:
            from models.db_models import db, init_db

            # Убеждаемся, что БД инициализирована
            init_db("medcrm.db")

            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                email=email,
                role=role,
                department=department,
                password_hash=hash_password(password),
                is_active=True,
            )

            user.save()

            # Проверяем, что пользователь сохранён
            saved_user = User.get_by_username(username)
            if saved_user:
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Пользователь создан, но не найден в базе. Попробуйте ещё раз.",
                )
        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось создать пользователя: {str(e)}\n\n{error_details}",
            )

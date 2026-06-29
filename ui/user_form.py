"""
Форма добавления/редактирования пользователя
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.db_models import User, get_department_choices, hash_password
from ui.styles import RADIUS, get_colors


class UserFormDialog(QDialog):
    """Диалог формы пользователя"""

    def __init__(self, current_user: User, user: User = None):
        super().__init__()
        self.current_user = current_user
        self.user = user
        self.is_edit = user is not None and user.id is not None

        title = "Редактирование пользователя" if self.is_edit else "Новый пользователь"
        self.setWindowTitle(title)
        self.setMinimumSize(560, 620)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()
        compact_font = QFont("Segoe UI", 9)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content_widget = QWidget()
        scroll.setWidget(content_widget)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 0, 0)

        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout()
        main_layout.setSpacing(12)
        main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.username_input = QLineEdit()
        self.username_input.setFrame(False)
        self.username_input.setFont(compact_font)
        self.username_input.setPlaceholderText("Логин для входа")
        self.username_input.setMinimumHeight(34)
        if self.is_edit:
            self.username_input.setEnabled(False)
        main_layout.addRow("Логин*", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setFrame(False)
        self.password_input.setFont(compact_font)
        self.password_input.setPlaceholderText(
            "Придумайте пароль"
            if not self.is_edit
            else "Оставьте пустым для сохранения текущего пароля"
        )
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(34)
        main_layout.addRow(
            "Пароль*" if not self.is_edit else "Пароль", self.password_input
        )

        self.first_name_input = QLineEdit()
        self.first_name_input.setFrame(False)
        self.first_name_input.setFont(compact_font)
        self.first_name_input.setPlaceholderText("Имя")
        self.first_name_input.setMinimumHeight(34)
        main_layout.addRow("Имя*", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setFrame(False)
        self.last_name_input.setFont(compact_font)
        self.last_name_input.setPlaceholderText("Фамилия")
        self.last_name_input.setMinimumHeight(34)
        main_layout.addRow("Фамилия*", self.last_name_input)

        self.email_input = QLineEdit()
        self.email_input.setFrame(False)
        self.email_input.setFont(compact_font)
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.setMinimumHeight(34)
        main_layout.addRow("Email", self.email_input)

        main_group.setLayout(main_layout)
        content_layout.addWidget(main_group)

        role_group = QGroupBox("Должность")
        role_layout = QFormLayout()
        role_layout.setSpacing(12)
        role_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        role_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.role_combo = QComboBox()
        self.role_combo.setFrame(False)
        self.role_combo.setFont(compact_font)
        self.role_combo.setMinimumHeight(34)

        if self.current_user.role == User.ROLE_ADMIN:
            self.role_combo.addItem("Администратор", User.ROLE_ADMIN)

        self.role_combo.addItem("Регистратор", User.ROLE_REGISTRAR)
        self.role_combo.addItem("Начальник отделения", User.ROLE_LEAD)
        self.role_combo.addItem("Работник", User.ROLE_DOCTOR)
        self.role_combo.addItem("Делопроизводитель", User.ROLE_NURSE)

        if self.current_user.role == User.ROLE_REGISTRAR:
            removable_indexes = []
            for idx in range(self.role_combo.count()):
                role_data = self.role_combo.itemData(idx)
                if role_data in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
                    removable_indexes.append(idx)
            for idx in reversed(removable_indexes):
                self.role_combo.removeItem(idx)

        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        role_layout.addRow("Роль*", self.role_combo)

        self.dept_combo = QComboBox()
        self.dept_combo.setFrame(False)
        self.dept_combo.setFont(compact_font)
        self.dept_combo.setMinimumHeight(34)
        self.dept_combo.addItem("Не выбрано", "")
        for value, label in get_department_choices():
            self.dept_combo.addItem(label, value)

        if self.current_user.role == User.ROLE_LEAD:
            dept_index = self.dept_combo.findData(self.current_user.department)
            if dept_index >= 0:
                self.dept_combo.setCurrentIndex(dept_index)
            self.dept_combo.setEnabled(False)

        role_layout.addRow("Отделение", self.dept_combo)
        role_group.setLayout(role_layout)
        content_layout.addWidget(role_group)

        self.active_check = QCheckBox("Активен")
        self.active_check.setFont(compact_font)
        self.active_check.setChecked(True)
        content_layout.addWidget(self.active_check)

        content_layout.addStretch()
        layout.addWidget(scroll)

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
                font-weight: 600;
            }}
            QLabel {{
                font-size: 9pt;
            }}
            QLineEdit:disabled, QComboBox:disabled {{
                color: {colors['text_muted']};
                background-color: {colors['surface_muted']};
            }}
            QCheckBox {{
                font-size: 9pt;
                color: {colors['text']};
                spacing: 8px;
            }}
            """
        )

        if self.is_edit:
            self._fill_data()
        else:
            self._on_role_changed(self.role_combo.currentIndex())

    def _apply_form_styles(self, colors):
        """Локально выравнивает поля формы пользователя под стиль формы документа."""
        input_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 4px 8px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """

        for widget in (
            self.username_input,
            self.password_input,
            self.first_name_input,
            self.last_name_input,
            self.email_input,
            self.role_combo,
            self.dept_combo,
        ):
            widget.setStyleSheet(input_style)

    def _on_role_changed(self, index):
        """Изменение роли"""
        role = self.role_combo.currentData()
        show_dept = role in (User.ROLE_LEAD, User.ROLE_DOCTOR, User.ROLE_NURSE)

        role_parent_layout = self.dept_combo.parentWidget().layout()
        if isinstance(role_parent_layout, QFormLayout):
            role_parent_layout.setRowVisible(self.dept_combo, show_dept)

        self.dept_combo.setVisible(show_dept)
        if self.current_user.role == User.ROLE_LEAD and show_dept:
            self.dept_combo.setEnabled(False)
        else:
            self.dept_combo.setEnabled(show_dept)

    def _fill_data(self):
        """Заполнение данными"""
        if not self.user:
            return

        self.username_input.setText(self.user.username)
        self.first_name_input.setText(self.user.first_name)
        self.last_name_input.setText(self.user.last_name)
        self.email_input.setText(self.user.email or "")

        index = self.role_combo.findData(self.user.role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)

        if self.user.department:
            dept_index = self.dept_combo.findData(self.user.department)
            if dept_index >= 0:
                self.dept_combo.setCurrentIndex(dept_index)

        self.active_check.setChecked(self.user.is_active)

    def _save(self):
        """Сохранение пользователя"""
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

        if not self.user:
            self.user = User()

        self.user.username = self.username_input.text().strip()
        self.user.first_name = self.first_name_input.text().strip()
        self.user.last_name = self.last_name_input.text().strip()
        self.user.email = self.email_input.text().strip()
        self.user.role = self.role_combo.currentData()
        self.user.department = self.dept_combo.currentData() or None
        self.user.is_active = self.active_check.isChecked()

        password = self.password_input.text().strip()
        if password:
            self.user.password_hash = hash_password(password)
        elif not self.is_edit:
            QMessageBox.warning(self, "Ошибка", "Пароль обязателен")
            return

        if self.current_user.role == User.ROLE_REGISTRAR:
            if self.user.role == User.ROLE_ADMIN:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Регистратор не может создавать администраторов",
                )
                return

        if self.current_user.role == User.ROLE_LEAD:
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

"""
Страница управления пользователями
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from models.db_models import User, get_department_choices
from ui.styles import get_colors, FONTS, RADIUS


class UsersPage(QWidget):
    """Страница пользователей"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.role_filter = ""
        self.dept_filter = ""
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Фильтры
        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)

        # Таблица
        self.table = self._create_table()
        layout.addWidget(self.table, 1)

        # Кнопки
        actions_panel = self._create_actions_panel()
        layout.addWidget(actions_panel)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        self._load_users()

    def _create_filter_panel(self) -> QFrame:
        """Панель фильтров"""
        panel = QFrame()
        panel.setObjectName("usersFilterPanel")
        panel.setFixedHeight(80)
        panel.setStyleSheet(self._filter_panel_style())

        layout = QHBoxLayout(panel)
        layout.setSpacing(12)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Поиск по ФИО...")
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._load_users)
        layout.addWidget(self.search_input)

        # Фильтр по роли
        self.role_combo = QComboBox()
        self.role_combo.setObjectName("filterCombo")
        self.role_combo.setFrame(False)
        self.role_combo.addItem("Все роли", "")
        self.role_combo.addItem("Администратор", User.ROLE_ADMIN)
        self.role_combo.addItem("Регистратор", User.ROLE_REGISTRAR)
        self.role_combo.addItem("Начальник отделения", User.ROLE_LEAD)
        self.role_combo.addItem("Врач", User.ROLE_DOCTOR)
        self.role_combo.addItem("Медсестра", User.ROLE_NURSE)
        self.role_combo.setFixedWidth(180)
        self.role_combo.setFixedHeight(34)
        self.role_combo.setStyleSheet(self._filter_combo_style())
        self.role_combo.currentIndexChanged.connect(self._load_users)
        layout.addWidget(self.role_combo)

        # Фильтр по отделению
        self.dept_combo = QComboBox()
        self.dept_combo.setObjectName("filterCombo")
        self.dept_combo.setFrame(False)
        self.dept_combo.addItem("Все отделения", "")
        for value, label in get_department_choices():
            self.dept_combo.addItem(label, value)
        if self.user.role == User.ROLE_LEAD:
            dept_index = self.dept_combo.findData(self.user.department)
            if dept_index >= 0:
                self.dept_combo.setCurrentIndex(dept_index)
            self.dept_combo.setEnabled(False)
        self.dept_combo.setFixedWidth(180)
        self.dept_combo.setFixedHeight(34)
        self.dept_combo.setStyleSheet(self._filter_combo_style())
        self.dept_combo.currentIndexChanged.connect(self._load_users)
        layout.addWidget(self.dept_combo)

        layout.addStretch()

        return panel

    def _filter_panel_style(self) -> str:
        colors = get_colors()
        return f"""
            QFrame#usersFilterPanel {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 12px;
            }}
        """

    def _filter_combo_style(self) -> str:
        colors = get_colors()
        return f"""
            QComboBox#filterCombo {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                padding: 4px 30px 4px 12px;
                color: {colors['text']};
                font-size: {FONTS['size_small']}pt;
                min-width: 0px;
            }}
            QComboBox#filterCombo:hover {{
                border: 1px solid {colors['accent']};
            }}
            QComboBox#filterCombo:focus {{
                border: 1px solid {colors['accent']};
                background-color: {colors['accent_light']};
            }}
            QComboBox#filterCombo::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox#filterCombo::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {colors['text_muted']};
                margin-right: 10px;
            }}
            QComboBox#filterCombo QAbstractItemView {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                selection-background-color: {colors['accent_light']};
                selection-color: {colors['text']};
                outline: none;
            }}
        """

    def _create_table(self) -> QTableWidget:
        """Таблица пользователей"""
        colors = get_colors()

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["ФИО", "Логин", "Роль", "Отделение", "Email", "Статус"]
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_context_menu)

        return table

    def _create_actions_panel(self) -> QFrame:
        """Панель действий"""
        colors = get_colors()

        panel = QFrame()
        panel.setFixedHeight(50)
        panel.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            add_btn = QPushButton("Добавить пользователя")
            add_btn.setObjectName("filterButton")
            add_btn.setFixedHeight(34)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet(self._filter_button_style())
            add_btn.clicked.connect(self._add_user)
            layout.addWidget(add_btn)

        layout.addStretch()

        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        layout.addWidget(self.count_label)

        return panel

    def _filter_button_style(self) -> str:
        colors = get_colors()
        return f"""
            QPushButton#filterButton {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                padding: 4px 12px;
                min-height: 0px;
                font-weight: 500;
                font-size: {FONTS['size_xs']}pt;
                color: {colors['text']};
            }}
            QPushButton#filterButton:hover {{
                background-color: {colors['accent_light']};
                border: 1px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#filterButton:pressed {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                color: #FFFFFF;
            }}
        """

    def _load_users(self):
        """Загрузка пользователей"""
        self.table.setRowCount(0)

        users = User.get_all(include_inactive=True)
        if self.user.role == User.ROLE_LEAD:
            users = [u for u in users if u.department == self.user.department]

        # Фильтры
        search = self.search_input.text().strip().lower()
        role = self.role_combo.currentData()
        dept = self.dept_combo.currentData()

        filtered = []
        for u in users:
            if role and u.role != role:
                continue
            if dept and u.department != dept:
                continue
            if search and not u.full_name.lower().startswith(search):
                continue
            filtered.append(u)

        colors = get_colors()

        active_text_color = colors["text"]
        inactive_color = colors["text_muted"]

        for u in filtered:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ФИО
            name_item = QTableWidgetItem(u.full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, u.id)
            name_item.setForeground(
                QColor(active_text_color if u.is_active else inactive_color)
            )
            self.table.setItem(row, 0, name_item)

            # Логин
            login_item = QTableWidgetItem(u.username)
            login_item.setForeground(
                QColor(active_text_color if u.is_active else inactive_color)
            )
            self.table.setItem(row, 1, login_item)

            # Роль
            role_item = QTableWidgetItem(u.role_display)
            role_item.setForeground(
                QColor(self._get_role_color(u.role) if u.is_active else inactive_color)
            )
            self.table.setItem(row, 2, role_item)

            # Отделение
            dept_item = QTableWidgetItem(u.department_display or "—")
            dept_item.setForeground(
                QColor(active_text_color if u.is_active else inactive_color)
            )
            self.table.setItem(row, 3, dept_item)

            # Email
            email_item = QTableWidgetItem(u.email or "—")
            email_item.setForeground(
                QColor(active_text_color if u.is_active else inactive_color)
            )
            self.table.setItem(row, 4, email_item)

            # Статус
            status = "✅ Активен" if u.is_active else "⏸️ Заблокирован"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                QColor(active_text_color if u.is_active else inactive_color)
            )
            self.table.setItem(row, 5, status_item)

        self.count_label.setText(f"Найдено: {len(filtered)}")

    def _can_manage_user(self, target_user: User) -> bool:
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            return True
        if self.user.role == User.ROLE_LEAD:
            return target_user.department == self.user.department
        return False

    def _get_role_color(self, role: str) -> str:
        """Цвет роли"""
        colors = get_colors()
        role_colors = {
            User.ROLE_ADMIN: colors["role_admin"],
            User.ROLE_REGISTRAR: colors["role_reg"],
            User.ROLE_LEAD: colors["role_lead"],
            User.ROLE_DOCTOR: colors["role_doc"],
            User.ROLE_NURSE: colors["role_nur"],
        }
        return role_colors.get(role, colors["text"])

    def _show_context_menu(self, pos):
        """Контекстное меню"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        target_user = User.get_by_id(user_id)

        if not target_user:
            return

        menu = QMenu()

        # Редактировать
        edit_action = menu.addAction("✏️ Редактировать")
        edit_action.triggered.connect(lambda: self._edit_user(user_id))

        # Заблокировать/Разблокировать (ADMIN, REG)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            if target_user.id != self.user.id:  # Нельзя заблокировать себя
                if target_user.is_active:
                    block_action = menu.addAction("🚫 Заблокировать")
                    block_action.triggered.connect(
                        lambda: self._toggle_user_status(user_id, False)
                    )
                else:
                    unblock_action = menu.addAction("✅ Разблокировать")
                    unblock_action.triggered.connect(
                        lambda: self._toggle_user_status(user_id, True)
                    )

        # Удалить (только ADMIN)
        if self.user.role == User.ROLE_ADMIN:
            if target_user.id != self.user.id:
                delete_action = menu.addAction("🗑️ Удалить")
                delete_action.triggered.connect(lambda: self._delete_user(user_id))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _add_user(self):
        """Добавление пользователя"""
        from ui.user_form import UserFormDialog

        dialog = UserFormDialog(self.user, None)
        if dialog.exec():
            self._load_users()

    def _edit_user(self, user_id: int):
        """Редактирование пользователя"""
        from ui.user_form import UserFormDialog

        user = User.get_by_id(user_id)
        if not user or not self._can_manage_user(user):
            QMessageBox.warning(self, "Ошибка", "Нет доступа к этому пользователю")
            return
        dialog = UserFormDialog(self.user, user)
        if dialog.exec():
            self._load_users()

    def _toggle_user_status(self, user_id: int, is_active: bool):
        """Переключение статуса"""
        user = User.get_by_id(user_id)
        status_text = "активировать" if is_active else "заблокировать"

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"{status_text.capitalize()} пользователя {user.full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            user.is_active = is_active
            user.save()
            self._load_users()

    def _delete_user(self, user_id: int):
        """Удаление пользователя"""
        user = User.get_by_id(user_id)

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить пользователя {user.full_name}?\nЭто действие необратимо!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            user.delete()
            self._load_users()

    def update_styles(self):
        """Обновление стилей при смене темы"""
        from PyQt6.QtWidgets import (
            QLabel,
            QPushButton,
            QLineEdit,
            QComboBox,
            QTableWidget,
            QFrame,
        )

        colors = get_colors()
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )
        panel = self.findChild(QFrame, "usersFilterPanel")
        if panel:
            panel.setStyleSheet(self._filter_panel_style())
        if hasattr(self, "role_combo"):
            self.role_combo.setStyleSheet(self._filter_combo_style())
        if hasattr(self, "dept_combo"):
            self.dept_combo.setStyleSheet(self._filter_combo_style())
        for button in self.findChildren(QPushButton, "filterButton"):
            button.setStyleSheet(self._filter_button_style())

        for widget in self.findChildren(QLabel):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        for widget in self.findChildren(QPushButton):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        for widget in self.findChildren(QLineEdit):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        for widget in self.findChildren(QComboBox):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        for widget in self.findChildren(QTableWidget):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        for widget in self.findChildren(QFrame):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._load_users()

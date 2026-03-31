"""
Страница управления пользователями
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QComboBox, QLineEdit, QMenu, QMessageBox)
from PyQt6.QtCore import Qt

from models.db_models import User, DEPARTMENTS
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
        self.setStyleSheet(f"background-color: {colors['bg']};")
        
        self._load_users()
    
    def _create_filter_panel(self) -> QFrame:
        """Панель фильтров"""
        colors = get_colors()
        
        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedHeight(70)
        panel.setStyleSheet(f"""
            QFrame#card {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 12px;
            }}
        """)
        
        layout = QHBoxLayout(panel)
        layout.setSpacing(12)
        
        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по ФИО...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._load_users)
        layout.addWidget(self.search_input)
        
        # Фильтр по роли
        self.role_combo = QComboBox()
        self.role_combo.addItem("Все роли", "")
        self.role_combo.addItem("Администратор", User.ROLE_ADMIN)
        self.role_combo.addItem("Регистратор", User.ROLE_REGISTRAR)
        self.role_combo.addItem("Начальник отделения", User.ROLE_LEAD)
        self.role_combo.addItem("Врач", User.ROLE_DOCTOR)
        self.role_combo.addItem("Медсестра", User.ROLE_NURSE)
        self.role_combo.setFixedWidth(180)
        self.role_combo.currentIndexChanged.connect(self._load_users)
        layout.addWidget(self.role_combo)
        
        # Фильтр по отделению
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Все отделения", "")
        for value, label in DEPARTMENTS:
            self.dept_combo.addItem(label, value)
        self.dept_combo.setFixedWidth(180)
        self.dept_combo.currentIndexChanged.connect(self._load_users)
        layout.addWidget(self.dept_combo)
        
        layout.addStretch()
        
        return panel
    
    def _create_table(self) -> QTableWidget:
        """Таблица пользователей"""
        colors = get_colors()
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "ФИО", "Логин", "Роль", "Отделение", "Email", "Статус"
        ])
        
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
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
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
        
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            add_btn = QPushButton("➕ Добавить пользователя")
            add_btn.setFixedHeight(40)
            add_btn.clicked.connect(self._add_user)
            layout.addWidget(add_btn)
        
        layout.addStretch()
        
        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        layout.addWidget(self.count_label)
        
        return panel
    
    def _load_users(self):
        """Загрузка пользователей"""
        self.table.setRowCount(0)
        
        users = User.get_all(include_inactive=True)
        
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
            if search and search not in u.full_name.lower():
                continue
            filtered.append(u)
        
        for u in filtered:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ФИО
            name_item = QTableWidgetItem(u.full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, u.id)
            name_item.setForeground(Qt.GlobalColor.color1 if u.is_active else Qt.GlobalColor.gray)
            self.table.setItem(row, 0, name_item)
            
            # Логин
            self.table.setItem(row, 1, QTableWidgetItem(u.username))
            
            # Роль
            role_item = QTableWidgetItem(u.role_display)
            role_label = QLabel(f"● {u.role_display}")
            role_label.setStyleSheet(f"color: {self._get_role_color(u.role)}; font-weight: bold;")
            role_label.setStyleSheet(f"color: {self._get_role_color(u.role)};")
            self.table.setCellWidget(row, 2, role_label)
            
            # Отделение
            self.table.setItem(row, 3, QTableWidgetItem(u.department_display or "—"))
            
            # Email
            self.table.setItem(row, 4, QTableWidgetItem(u.email or "—"))
            
            # Статус
            status = "✅ Активен" if u.is_active else "⏸️ Заблокирован"
            status_item = QTableWidgetItem(status)
            if not u.is_active:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 5, status_item)
        
        self.count_label.setText(f"Найдено: {len(filtered)}")
    
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
                    block_action.triggered.connect(lambda: self._toggle_user_status(user_id, False))
                else:
                    unblock_action = menu.addAction("✅ Разблокировать")
                    unblock_action.triggered.connect(lambda: self._toggle_user_status(user_id, True))
        
        # Удалить (только ADMIN)
        if self.user.role == User.ROLE_ADMIN:
            if target_user.id != self.user.id:
                delete_action = menu.addAction("🗑️ Удалить")
                delete_action.triggered.connect(lambda: self._delete_user(user_id))
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    
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
        dialog = UserFormDialog(self.user, user)
        if dialog.exec():
            self._load_users()
    
    def _toggle_user_status(self, user_id: int, is_active: bool):
        """Переключение статуса"""
        user = User.get_by_id(user_id)
        status_text = "активировать" if is_active else "заблокировать"
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"{status_text.capitalize()} пользователя {user.full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            user.is_active = is_active
            user.save()
            self._load_users()
    
    def _delete_user(self, user_id: int):
        """Удаление пользователя"""
        user = User.get_by_id(user_id)
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить пользователя {user.full_name}?\nЭто действие необратимо!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            user.delete()
            self._load_users()

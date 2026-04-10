"""
Страница планирования мероприятий
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
    QDateEdit,
    QCheckBox,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from models.db_models import User, Event, DEPARTMENTS, EVENT_TYPES
from ui.styles import get_colors, FONTS, RADIUS
from datetime import date


class PlanningPage(QWidget):
    """Страница планирования"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.dept_filter = ""
        self.type_filter = ""
        self.show_completed = True
        self.selected_year = date.today().year
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

        self._load_events()

    def _create_filter_panel(self) -> QFrame:
        """Панель фильтров"""
        colors = get_colors()

        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedHeight(80)
        panel.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 12px;
            }}
        """
        )

        layout = QHBoxLayout(panel)
        layout.setSpacing(12)

        # Год
        year_label = QLabel("Год:")
        year_label.setStyleSheet("font-weight: bold; background-color: transparent;")
        layout.addWidget(year_label)

        self.year_combo = QComboBox()
        self.year_combo.setFrame(False)
        current_year = date.today().year
        for y in range(current_year - 5, current_year + 6):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(self.selected_year))
        self.year_combo.setFixedWidth(110)
        self.year_combo.setFixedHeight(42)
        self.year_combo.setStyleSheet(f"font-size: {FONTS['size_medium']}pt;")
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        layout.addWidget(self.year_combo)

        # Тип мероприятия
        self.type_combo = QComboBox()
        self.type_combo.setFrame(False)
        self.type_combo.addItem("Все типы", "")
        for value, label in EVENT_TYPES:
            self.type_combo.addItem(label, value)
        self.type_combo.setFixedWidth(160)
        self.type_combo.setFixedHeight(42)
        self.type_combo.setStyleSheet(f"font-size: {FONTS['size_medium']}pt;")
        self.type_combo.currentIndexChanged.connect(self._load_events)
        layout.addWidget(self.type_combo)

        # Отделение
        self.dept_combo = QComboBox()
        self.dept_combo.setFrame(False)
        self.dept_combo.addItem("Все отделения", "")

        # Ограничение по отделению
        if self.user.role == User.ROLE_LEAD:
            self.dept_combo.addItem(self.user.department_display, self.user.department)
            self.dept_combo.setEnabled(False)
        elif self.user.role in (User.ROLE_DOCTOR, User.ROLE_NURSE):
            self.dept_combo.addItem(self.user.department_display, self.user.department)
        else:
            for value, label in DEPARTMENTS:
                self.dept_combo.addItem(label, value)

        self.dept_combo.setFixedWidth(180)
        self.dept_combo.setFixedHeight(40)
        self.dept_combo.currentIndexChanged.connect(self._load_events)
        layout.addWidget(self.dept_combo)

        # Показать выполненные
        self.show_completed_check = QCheckBox("Показать выполненные")
        self.show_completed_check.setChecked(True)
        self.show_completed_check.setStyleSheet("background-color: transparent;")
        self.show_completed_check.stateChanged.connect(self._load_events)
        layout.addWidget(self.show_completed_check)

        layout.addStretch()

        return panel

    def _create_table(self) -> QTableWidget:
        """Таблица мероприятий"""
        colors = get_colors()

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Дата", "Название", "Тип", "Отделение", "Ответственный"]
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

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

        add_btn = QPushButton("Создать мероприятие")
        add_btn.setObjectName("actionButton")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 6px 16px;
                font-weight: 600;
                font-size: {FONTS['size_small']}pt;
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['accent_light']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton:pressed {{
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                color: #FFFFFF;
            }}
        """
        )
        add_btn.clicked.connect(self._add_event)
        layout.addWidget(add_btn)

        layout.addStretch()

        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        layout.addWidget(self.count_label)

        return panel

    def _load_events(self):
        """Загрузка мероприятий"""
        self.table.setRowCount(0)

        dept = self.dept_combo.currentData() or ""
        event_type = self.type_combo.currentData() or ""
        show_completed = self.show_completed_check.isChecked()
        year = self.year_combo.currentData()

        events = Event.get_all(
            user=self.user,
            department=dept,
            include_completed=show_completed,
            year=year,
        )

        # Фильтрация по типу
        filtered_events = events
        if event_type:
            filtered_events = [e for e in events if e.event_type == event_type]

        for event in filtered_events:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Дата
            date_str = event.event_date.strftime("%d.%m.%Y")
            self.table.setItem(row, 0, QTableWidgetItem(date_str))

            # Название
            name_item = QTableWidgetItem(event.title)
            if event.is_completed:
                name_item.setForeground(Qt.GlobalColor.gray)
            name_item.setData(Qt.ItemDataRole.UserRole, event.id)
            self.table.setItem(row, 1, name_item)

            # Тип
            self.table.setItem(row, 2, QTableWidgetItem(event.event_type_display))

            # Отделение
            self.table.setItem(row, 3, QTableWidgetItem(event.department_display))

            # Ответственный
            responsible = event.responsible.full_name if event.responsible else "—"
            self.table.setItem(row, 4, QTableWidgetItem(responsible))

        self.count_label.setText(f"Найдено: {len(filtered_events)}")

    def _on_year_changed(self):
        """Изменение года"""
        self.selected_year = self.year_combo.currentData()
        self._load_events()

    def _show_context_menu(self, pos):
        """Контекстное меню"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        item = self.table.item(row, 1)  # Колонка "Название"
        if not item:
            return

        event_id = item.data(Qt.ItemDataRole.UserRole)
        event = Event.get_by_id(event_id)

        if not event:
            return

        menu = QMenu()

        # Переключить статус
        if event:
            status_action = menu.addAction(
                "✅ Выполнено" if not event.is_completed else "↩️ Не выполнено"
            )
            status_action.triggered.connect(lambda: self._toggle_event(event_id))

        # Редактировать/Удалить (только свои)
        can_edit = self.user.role == User.ROLE_ADMIN or (
            event.created_by_id == self.user.id
        )

        if can_edit:
            delete_action = menu.addAction("🗑️ Удалить")
            delete_action.triggered.connect(lambda: self._delete_event(event_id))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _add_event(self):
        """Добавление мероприятия"""
        from ui.event_form import EventFormDialog

        dialog = EventFormDialog(self.user, None, default_year=self.selected_year)
        if dialog.exec():
            self._load_events()

    def _toggle_event(self, event_id: int):
        """Переключение статуса"""
        event = Event.get_by_id(event_id)
        if event:
            event.toggle()
            self._load_events()

    def _delete_event(self, event_id: int):
        """Удаление мероприятия"""
        event = Event.get_by_id(event_id)

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f'Удалить мероприятие "{event.title}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.delete()
            self._load_events()

    def update_styles(self):
        """Обновление стилей при смене темы"""
        from PyQt6.QtWidgets import (
            QLabel,
            QPushButton,
            QComboBox,
            QTableWidget,
            QFrame,
            QCheckBox,
        )

        colors = get_colors()
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        for widget in self.findChildren(QLabel):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        for widget in self.findChildren(QPushButton):
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
        for widget in self.findChildren(QCheckBox):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

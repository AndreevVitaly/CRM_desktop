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
    QDialog,
    QLineEdit,
    QInputDialog,
    QCalendarWidget,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QPen

from models.db_models import (
    DOCUMENT_TYPE_MEETING,
    Document,
    Encounter,
    User,
    Event,
    EVENT_TYPES,
    get_department_choices,
)
from ui.styles import get_colors, FONTS, RADIUS, scaled
from datetime import date, timedelta


class PeriodCalendarWidget(QCalendarWidget):
    def __init__(self):
        super().__init__()
        self.period_mode = "week"
        self.reference_date = date.today()
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setGridVisible(False)

    def set_period_context(self, mode: str, qdate: QDate):
        self.period_mode = mode or "year"
        self.reference_date = qdate.toPyDate()
        self.setSelectedDate(qdate)
        self.updateCells()

    def paintCell(self, painter, rect, qdate):
        day = qdate.toPyDate()
        selected = self.reference_date
        week_start = selected - timedelta(days=selected.weekday())
        week_end = week_start + timedelta(days=6)
        in_selected_week = week_start <= day <= week_end
        is_selected_day = day == selected
        is_visible_month = (
            day.month == self.monthShown() and day.year == self.yearShown()
        )

        if is_selected_day:
            bg = QColor("#93C5FD")
            fg = QColor("#0F172A")
            border = QColor("#2563EB")
            weight = QFont.Weight.Bold
        elif self.period_mode == "week" and in_selected_week:
            bg = QColor("#DBEAFE")
            fg = QColor("#0F172A")
            border = QColor("#DBEAFE")
            weight = QFont.Weight.DemiBold
        elif is_visible_month:
            bg = QColor("#FFFFFF")
            fg = QColor("#111827")
            border = QColor("#E5E7EB")
            weight = QFont.Weight.Normal
        else:
            bg = QColor("#F8FAFC")
            fg = QColor("#64748B")
            border = QColor("#EEF2F7")
            weight = QFont.Weight.Normal

        painter.save()
        painter.fillRect(rect, bg)
        painter.setPen(QPen(border, 1))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        font = painter.font()
        font.setWeight(weight)
        painter.setFont(font)
        painter.setPen(fg)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(day.day))
        painter.restore()


class MeetingDocumentPickerDialog(QDialog):
    def __init__(self, user: User, selected_document_id: int | None = None):
        super().__init__()
        self.user = user
        self.selected_document_id = selected_document_id
        self.documents: list[Document] = []
        self.selected_document: Document | None = None
        self.setWindowTitle("Выбор документа встречи")
        self.setMinimumSize(860, 520)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Поиск по пациенту, личному номеру, врачу или номеру документа"
        )
        self.search_input.textChanged.connect(self._load_documents)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Дата", "Пациент", "Личный номер", "Врач", "Документ"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.accept)
        layout.addWidget(self.table, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        select_btn = QPushButton("Выбрать")
        select_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(select_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)
        self.setStyleSheet(
            f"background-color: {get_colors()['bg']}; color: {get_colors()['text']};"
        )
        self._load_documents()

    def _load_documents(self):
        search = self.search_input.text().strip().casefold()
        self.documents = []
        self.table.setRowCount(0)

        for document in Document.get_all(self.user):
            if document.doc_type != DOCUMENT_TYPE_MEETING:
                continue

            encounter = document.encounter
            if encounter and encounter.status != Encounter.STATUS_FINISHED:
                continue

            patient = document.patient
            if not patient:
                continue

            doctor = (
                (encounter.doctor if encounter and encounter.doctor_id else None)
                or patient.doctor
                or document.author
            )
            doctor_name = doctor.full_name if doctor else "-"
            document_number = str(document.doc_number or f"#{document.id}")
            date_text = document.doc_date.strftime("%d.%m.%Y") if document.doc_date else "-"
            haystack = " ".join(
                [
                    patient.callsign or "",
                    patient.personal_number or "",
                    doctor_name,
                    document_number,
                    date_text,
                ]
            ).casefold()
            if search and search not in haystack:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.documents.append(document)
            values = [
                date_text,
                patient.callsign or "-",
                patient.personal_number or "-",
                doctor_name,
                document_number,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, document.id)
                self.table.setItem(row, column, item)
            if document.id == self.selected_document_id:
                self.table.selectRow(row)

    def accept(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Выбор документа", "Выберите документ встречи")
            return
        row = selected[0].row()
        if row < 0 or row >= len(self.documents):
            return
        self.selected_document = self.documents[row]
        super().accept()


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
        layout.setContentsMargins(20, 20, 20, scaled(38, 24))

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
        panel.setFixedHeight(96)
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

        period_label = QLabel("Период:")
        period_label.setStyleSheet("font-weight: bold; background-color: transparent;")
        layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.setFrame(False)
        self.period_combo.addItem("Год", "year")
        self.period_combo.addItem("Месяц", "month")
        self.period_combo.addItem("Неделя", "week")
        self.period_combo.addItem("День", "day")
        self.period_combo.setFixedWidth(120)
        self.period_combo.setFixedHeight(42)
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        layout.addWidget(self.period_combo)

        self.month_combo = QComboBox()
        self.month_combo.setFrame(False)
        for month_number, month_name in enumerate(
            [
                "Январь",
                "Февраль",
                "Март",
                "Апрель",
                "Май",
                "Июнь",
                "Июль",
                "Август",
                "Сентябрь",
                "Октябрь",
                "Ноябрь",
                "Декабрь",
            ],
            start=1,
        ):
            self.month_combo.addItem(month_name, month_number)
        self.month_combo.setCurrentIndex(date.today().month - 1)
        self.month_combo.setFixedWidth(135)
        self.month_combo.setFixedHeight(42)
        self.month_combo.currentIndexChanged.connect(self._load_events)
        layout.addWidget(self.month_combo)

        self.period_date_input = QDateEdit()
        self.period_date_input.setCalendarPopup(True)
        self.period_calendar = PeriodCalendarWidget()
        self.period_date_input.setCalendarWidget(self.period_calendar)
        self.period_date_input.setDate(QDate.currentDate())
        self.period_date_input.setDisplayFormat("dd.MM.yyyy")
        self.period_date_input.setFixedWidth(160)
        self.period_date_input.setFixedHeight(42)
        self.period_calendar.setMinimumSize(320, 260)
        self.period_date_input.setStyleSheet(
            f"""
            QDateEdit {{
                color: {colors['accent_strong']};
                font-weight: 600;
                padding-left: 14px;
                padding-right: 32px;
            }}
            QDateEdit:focus {{
                color: {colors['accent_strong']};
            }}
            """
        )
        self.period_date_input.calendarWidget().setStyleSheet(
            f"""
            QCalendarWidget QWidget {{
                color: {colors['text']};
                background-color: {colors['surface']};
            }}
            QCalendarWidget QToolButton {{
                color: {colors['accent_strong']};
                background-color: transparent;
                font-weight: 600;
                padding: 4px;
            }}
            QCalendarWidget QMenu {{
                background-color: #FFFFFF;
                color: #111827;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }}
            """
        )
        self._style_period_calendar()
        self.period_date_input.dateChanged.connect(self._on_period_date_changed)
        layout.addWidget(self.period_date_input)

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
            for value, label in get_department_choices():
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

        self._update_period_controls()

        layout.addStretch()

        return panel

    def _create_table(self) -> QTableWidget:
        """Таблица мероприятий"""
        colors = get_colors()

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            [
                "Дата",
                "Название",
                "Тип",
                "Отделение",
                "Ответственный",
                "Отчетная позиция",
            ]
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
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
        panel.setFixedHeight(scaled(58, 50))
        panel.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, scaled(10, 8))
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

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
        date_from, date_to = self._get_period_dates()
        query_year = year if date_from is None and date_to is None else 0

        events = Event.get_all(
            user=self.user,
            department=dept,
            include_completed=show_completed,
            year=query_year,
            date_from=date_from,
            date_to=date_to,
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

            report_position = event.report_position_display or "-"
            self.table.setItem(row, 5, QTableWidgetItem(report_position))

        self.count_label.setText(f"Найдено: {len(filtered_events)}")

    def _update_period_controls(self):
        mode = self.period_combo.currentData() if hasattr(self, "period_combo") else "year"
        self.month_combo.setVisible(mode == "month")
        self.period_date_input.setVisible(mode in ("week", "day"))
        if hasattr(self, "period_date_input"):
            self._style_period_calendar()

    def _style_period_calendar(self):
        if not hasattr(self, "period_date_input"):
            return

        mode = self.period_combo.currentData() if hasattr(self, "period_combo") else "year"
        calendar = self.period_date_input.calendarWidget()
        if isinstance(calendar, PeriodCalendarWidget):
            calendar.set_period_context(mode, self.period_date_input.date())

    def _get_period_dates(self) -> tuple[date | None, date | None]:
        mode = self.period_combo.currentData() or "year"
        year = self.year_combo.currentData()

        if mode == "month":
            month = self.month_combo.currentData() or 1
            start = date(year, month, 1)
            if month == 12:
                end = date(year, 12, 31)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
            return start, end

        selected = self.period_date_input.date().toPyDate()
        if mode == "week":
            start = selected - timedelta(days=selected.weekday())
            end = start + timedelta(days=6)
            return start, end

        if mode == "day":
            return selected, selected

        return None, None

    def _on_period_changed(self):
        self._update_period_controls()
        self._load_events()

    def _on_period_date_changed(self):
        self._style_period_calendar()
        self._load_events()

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
        manual_action = menu.addAction("Добавить запись")
        manual_action.triggered.connect(lambda: self._add_report_position(event_id))

        meeting_action = menu.addAction("Выбрать встречу")
        meeting_action.triggered.connect(lambda: self._select_meeting_document(event_id))

        if event.meeting_document_id or event.report_position_text:
            clear_meeting_action = menu.addAction("Очистить отчетную позицию")
            clear_meeting_action.triggered.connect(
                lambda: self._clear_report_position(event_id)
            )

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

    def _select_meeting_document(self, event_id: int):
        event = Event.get_by_id(event_id)
        if not event:
            return

        dialog = MeetingDocumentPickerDialog(self.user, event.meeting_document_id)
        if dialog.exec() and dialog.selected_document:
            event.meeting_document_id = dialog.selected_document.id
            event.report_position_text = ""
            event.is_completed = True
            event.save()
            self._load_events()

    def _add_report_position(self, event_id: int):
        event = Event.get_by_id(event_id)
        if not event:
            return

        text, ok = QInputDialog.getMultiLineText(
            self,
            "Отчетная позиция",
            "Введите отчетные данные:",
            event.report_position_text or event.meeting_document_number,
        )
        if not ok:
            return

        text = text.strip()
        if not text:
            return

        event.report_position_text = text
        event.meeting_document_id = None
        event.is_completed = True
        event.save()
        self._load_events()

    def _clear_report_position(self, event_id: int):
        event = Event.get_by_id(event_id)
        if not event:
            return

        event.meeting_document_id = None
        event.report_position_text = ""
        event.save()
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
        if hasattr(self, "period_calendar"):
            self.period_calendar.updateCells()
        if hasattr(self, "period_date_input"):
            self._style_period_calendar()

    def update_theme(self):
        self.update_styles()

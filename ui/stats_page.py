"""
Страница статистики
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from models.db_models import User, Patient, Encounter, DEPARTMENTS
from ui.styles import get_colors, FONTS, RADIUS
from datetime import datetime, timedelta


class StatsPage(QWidget):
    """Страница статистики"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.selected_month = QDate.currentDate().month()
        self.selected_year = QDate.currentDate().year()
        self.selected_dept = ""
        self.kpi_cards = []  # Ссылки на KPI карточки для обновления темы
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        scroll.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Фильтры
        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)

        # KPI карточки
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(16)

        self.kpi_cards = []
        kpi_cards = self._get_kpi_data()
        for i, (icon, title, value, subtitle) in enumerate(kpi_cards):
            card = self._create_kpi_card(icon, title, value, subtitle)
            self.kpi_cards.append(card)
            row = i // 4
            col = i % 4
            kpi_layout.addWidget(card, row, col)

        layout.addLayout(kpi_layout)

        # Таблица по дням
        table_label = QLabel("Посещения по дням месяца")
        table_label.setObjectName("title")
        layout.addWidget(table_label)

        self.stats_table = self._create_stats_table()
        layout.addWidget(self.stats_table)

        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {colors['bg']};")

        self._load_stats()

    def _create_filter_panel(self) -> QFrame:
        """Панель фильтров"""
        colors = get_colors()

        panel = QFrame()
        panel.setObjectName("card")
        panel.setFixedHeight(70)
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

        # Месяц
        month_label = QLabel("Месяц:")
        month_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(month_label)

        self.month_combo = QComboBox()
        months = [
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
        ]
        for i, m in enumerate(months):
            self.month_combo.addItem(m, i + 1)
        self.month_combo.setCurrentIndex(self.selected_month - 1)
        self.month_combo.setFixedWidth(150)
        self.month_combo.currentIndexChanged.connect(self._load_stats)
        layout.addWidget(self.month_combo)

        # Год
        self.year_input = QDateEdit()
        self.year_input.setDate(QDate(self.selected_year, 1, 1))
        self.year_input.setDisplayFormat("yyyy")
        self.year_input.setFixedWidth(100)
        self.year_input.dateChanged.connect(self._on_year_changed)
        layout.addWidget(self.year_input)

        # Отделение
        dept_label = QLabel("Отделение:")
        dept_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(dept_label)

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Все отделения", "")

        # Ограничение по отделению
        if self.user.role == User.ROLE_LEAD:
            self.dept_combo.addItem(self.user.department_display, self.user.department)
            self.dept_combo.setEnabled(False)
        else:
            for value, label in DEPARTMENTS:
                self.dept_combo.addItem(label, value)

        self.dept_combo.setFixedWidth(180)
        self.dept_combo.currentIndexChanged.connect(self._load_stats)
        layout.addWidget(self.dept_combo)

        layout.addStretch()

        return panel

    def _on_year_changed(self, date):
        """Изменение года"""
        self.selected_year = date.year()
        self._load_stats()

    def _get_kpi_data(self) -> list:
        """KPI данные"""
        dept = self.dept_combo.currentData() or ""

        # Получаем пациентов
        patients = Patient.get_all(user=self.user if dept else None)

        # Фильтр по отделению
        if dept:
            patients = [p for p in patients if p.department == dept]

        total_patients = len(patients)
        adult_patients = len([p for p in patients if p.patient_type == "adult"])
        child_patients = len([p for p in patients if p.patient_type == "child"])

        # Посещения за месяц
        from_date = datetime(self.selected_year, self.selected_month, 1)
        if self.selected_month == 12:
            to_date = datetime(self.selected_year + 1, 1, 1)
        else:
            to_date = datetime(self.selected_year, self.selected_month + 1, 1)

        # Подсчёт визитов за месяц
        visits = Encounter.get_all(
            user=(
                self.user
                if self.user.role not in (User.ROLE_ADMIN, User.ROLE_REGISTRAR)
                else None
            ),
            start_date=from_date,
            end_date=to_date,
        )
        visits_count = len(visits)

        if self.user.role == User.ROLE_ADMIN:
            return [
                ("", "Всего пациентов", str(total_patients), ""),
                ("", "Взрослых", str(adult_patients), ""),
                ("", "Детей", str(child_patients), ""),
                ("", "Визитов за месяц", str(visits_count), ""),
            ]
        elif self.user.role == User.ROLE_LEAD:
            dept_patients = [
                p for p in patients if p.department == self.user.department
            ]
            return [
                ("", "Пациентов отделения", str(len(dept_patients)), ""),
                (
                    "",
                    "Взрослых",
                    str(len([p for p in dept_patients if p.patient_type == "adult"])),
                    "",
                ),
                (
                    "",
                    "Детей",
                    str(len([p for p in dept_patients if p.patient_type == "child"])),
                    "",
                ),
                ("", "Визитов за месяц", str(visits_count), "отделение"),
            ]
        else:
            return [
                ("", "Пациентов", str(total_patients), ""),
                ("", "Взрослых", str(adult_patients), ""),
                ("", "Детей", str(child_patients), ""),
                ("", "Визитов", str(visits_count), ""),
            ]

    def _create_kpi_card(
        self, icon: str, title: str, value: str, subtitle: str
    ) -> QFrame:
        """KPI карточка"""
        colors = get_colors()

        card = QFrame()
        card.setObjectName("kpiCard")
        card.setFixedHeight(120)
        card.setStyleSheet(
            f"""
            QFrame#kpiCard {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 16px;
            }}
            QFrame#kpiCard:hover {{
                border: 2px solid {colors['accent']};
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        top_layout = QHBoxLayout()

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            top_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("muted")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"""
            font-size: 32px;
            font-weight: bold;
            color: {colors['accent']};
        """
        )
        layout.addWidget(value_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("muted")
            layout.addWidget(subtitle_label)

        return card

    def _create_stats_table(self) -> QTableWidget:
        """Таблица статистики"""
        colors = get_colors()

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["День", "Количество посещений"])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)

        return table

    def _load_stats(self):
        """Загрузка статистики"""
        self.selected_month = self.month_combo.currentData()
        dept = self.dept_combo.currentData() or ""

        self.stats_table.setRowCount(0)

        # Дни месяца
        import calendar

        days_in_month = calendar.monthrange(self.selected_year, self.selected_month)[1]

        # Получаем визиты за месяц
        from_date = datetime(self.selected_year, self.selected_month, 1)
        if self.selected_month == 12:
            to_date = datetime(self.selected_year + 1, 1, 1)
        else:
            to_date = datetime(self.selected_year, self.selected_month + 1, 1)

        visits = Encounter.get_all(
            user=(
                self.user
                if self.user.role not in (User.ROLE_ADMIN, User.ROLE_REGISTRAR)
                else None
            ),
            start_date=from_date,
            end_date=to_date,
        )

        # Подсчёт по дням
        visits_by_day = {}
        for visit in visits:
            if visit.started_at:
                day = visit.started_at.day
                visits_by_day[day] = visits_by_day.get(day, 0) + 1

        for day in range(1, days_in_month + 1):
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)

            date_str = f"{day:02d}.{self.selected_month:02d}.{self.selected_year}"
            self.stats_table.setItem(row, 0, QTableWidgetItem(date_str))

            count = visits_by_day.get(day, 0)
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 1, count_item)

    def update_theme(self):
        """Обновление стилей при смене темы"""
        colors = get_colors()

        # Обновляем фон страницы
        self.setStyleSheet(f"background-color: {colors['bg']};")

        # Обновляем фильтр-панель
        filter_panel = self.findChild(QFrame)
        if filter_panel:
            filter_panel.setStyleSheet(
                f"""
                QFrame#card {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['line']};
                    border-radius: {RADIUS['lg']}px;
                    padding: 12px;
                }}
            """
            )

        # Обновляем KPI карточки
        for card in self.kpi_cards:
            card.setStyleSheet(
                f"""
                QFrame#kpiCard {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['line']};
                    border-radius: {RADIUS['lg']}px;
                    padding: 16px;
                }}
                QFrame#kpiCard:hover {{
                    border: 2px solid {colors['accent']};
                }}
            """
            )

            # Обновляем значение в карточке
            for child in card.findChildren(QLabel):
                if child.styleSheet() and "font-size: 32px" in child.styleSheet():
                    child.setStyleSheet(
                        f"""
                        font-size: 32px;
                        font-weight: bold;
                        color: {colors['accent']};
                    """
                    )

        # Обновляем таблицу
        if hasattr(self, "stats_table"):
            self.stats_table.setStyleSheet(
                f"""
                QTableWidget {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['table_border']};
                    border-radius: {RADIUS['md']}px;
                    selection-background-color: {colors['table_row_selected']};
                    gridline-color: {colors['line_light']};
                    color: {colors['text']};
                }}
                QTableWidget::item {{
                    padding: 12px;
                    border-radius: {RADIUS['sm']}px;
                }}
                QTableWidget::item:hover {{
                    background-color: {colors['table_row_hover']};
                }}
                QHeaderView::section {{
                    background-color: {colors['surface']};
                    color: {colors['text_muted']};
                    padding: 14px 12px;
                    border: none;
                    border-bottom: 1px solid {colors['line']};
                    font-weight: 600;
                    font-size: {FONTS['size_xs']}pt;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}
            """
            )

    def update_styles(self):
        """Алиас для update_theme"""
        self.update_theme()

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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QScrollArea,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from models.db_models import User, Patient, Encounter, DEPARTMENTS, StatsCache
from ui.styles import get_colors, FONTS, RADIUS
from datetime import datetime


class StatsPage(QWidget):
    """Страница статистики"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.selected_month = QDate.currentDate().month()
        self.selected_year = QDate.currentDate().year()
        self.selected_dept = ""
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

        # Основной контейнер со всей статистикой
        main_card = QFrame()
        main_card.setObjectName("statsMainCard")
        main_card.setStyleSheet(
            f"""
            QFrame#statsMainCard {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 20px;
            }}
        """
        )

        main_card_layout = QVBoxLayout(main_card)
        main_card_layout.setSpacing(20)
        main_card_layout.setContentsMargins(20, 20, 20, 20)

        # Таблица показателей по отделениям
        self.dept_stats_table = self._create_dept_stats_table()
        main_card_layout.addWidget(self.dept_stats_table)

        # Разделительная линия
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"color: {colors['line']};")
        main_card_layout.addWidget(line)

        # Таблица по дням
        table_label = QLabel("Посещения по дням месяца")
        table_label.setObjectName("title")
        main_card_layout.addWidget(table_label)

        self.stats_table = self._create_stats_table()
        main_card_layout.addWidget(self.stats_table)

        layout.addWidget(main_card)
        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        self._load_stats()

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

        # Месяц
        month_label = QLabel("Месяц:")
        month_label.setStyleSheet("font-weight: bold; background-color: transparent;")
        layout.addWidget(month_label)

        self.month_combo = QComboBox()
        self.month_combo.setFrame(False)
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
        self.month_combo.setFixedWidth(160)
        self.month_combo.setFixedHeight(42)
        self.month_combo.setStyleSheet(f"font-size: {FONTS['size_medium']}pt;")
        self.month_combo.currentIndexChanged.connect(self._load_stats)
        layout.addWidget(self.month_combo)

        # Год
        self.year_combo = QComboBox()
        self.year_combo.setFrame(False)
        current_year = QDate.currentDate().year()
        for y in range(current_year - 5, current_year + 6):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(self.selected_year))
        self.year_combo.setFixedWidth(110)
        self.year_combo.setFixedHeight(42)
        self.year_combo.setStyleSheet(f"font-size: {FONTS['size_medium']}pt;")
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        layout.addWidget(self.year_combo)

        # Отделение
        dept_label = QLabel("Отделение:")
        dept_label.setStyleSheet(
            "font-weight: bold; font-size: 11pt; background-color: transparent;"
        )
        layout.addWidget(dept_label)

        self.dept_combo = QComboBox()
        self.dept_combo.setFrame(False)
        self.dept_combo.addItem("Все отделения", "")

        # Ограничение по отделению
        if self.user.role == User.ROLE_LEAD:
            self.dept_combo.addItem(self.user.department_display, self.user.department)
            self.dept_combo.setEnabled(False)
        else:
            for value, label in DEPARTMENTS:
                self.dept_combo.addItem(label, value)

        self.dept_combo.setFixedWidth(200)
        self.dept_combo.setFixedHeight(42)
        self.dept_combo.setStyleSheet(f"font-size: {FONTS['size_medium']}pt;")
        self.dept_combo.currentIndexChanged.connect(self._load_stats)
        layout.addWidget(self.dept_combo)

        layout.addStretch()

        return panel

    def _on_year_changed(self):
        """Изменение года"""
        self.selected_year = self.year_combo.currentData()
        self._load_stats()

    def _create_dept_stats_table(self) -> QTableWidget:
        """Таблица статистики по отделениям"""
        colors = get_colors()

        table = QTableWidget()
        # Колонки: Показатель + каждое отделение + Всего
        num_cols = 1 + len(DEPARTMENTS) + 1  # Показатель + отделения + Всего
        table.setColumnCount(num_cols)

        # Заголовки
        headers = ["Показатель"]
        for dept_code, dept_name in DEPARTMENTS:
            headers.append(dept_name)
        headers.append("Всего")
        table.setHorizontalHeaderLabels(headers)

        # Настройка колонок
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, num_cols):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setAlternatingRowColors(False)
        table.setFrameShape(QTableWidget.Shape.NoFrame)

        return table

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
        table.setShowGrid(True)
        table.setAlternatingRowColors(False)
        table.setFrameShape(QTableWidget.Shape.NoFrame)

        return table

    def _load_stats(self):
        """Загрузка статистики"""
        self.selected_month = self.month_combo.currentData()
        self.selected_year = self.year_combo.currentData()

        # Пересчитываем кэш для актуальных данных
        StatsCache.rebuild_all()

        # Загрузка таблицы по отделениям
        self._load_dept_stats()

        # Загрузка таблицы по дням
        self._load_daily_stats()

    def _load_dept_stats(self):
        """Загрузка статистики по отделениям из кэша"""
        colors = get_colors()
        table = self.dept_stats_table
        table.setRowCount(0)

        # Показатели для строк
        rows_data = [
            ("Пациентов", "patients_total"),
            ("Взрослых", "patients_adult"),
            ("Детей", "patients_child"),
            ("Неопределённых", "patients_undefined"),
            ("Встреч за месяц", "visits"),
        ]

        # Добавляем строки
        for row_label, metric_key in rows_data:
            row = table.rowCount()
            table.insertRow(row)

            # Название показателя
            item_label = QTableWidgetItem(row_label)
            item_label.setForeground(QColor(colors["text_muted"]))
            table.setItem(row, 0, item_label)

            # Данные по каждому отделению
            total = 0
            for col_idx, (dept_code, dept_name) in enumerate(DEPARTMENTS, start=1):
                # Берём из кэша
                cached_value = StatsCache.get(
                    metric_key, dept_code, self.selected_month, self.selected_year
                )
                count = cached_value if cached_value is not None else 0
                total += count

                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col_idx, item)

            # Итого — берём из кэша для пустого department
            total_cached = StatsCache.get(
                metric_key, "", self.selected_month, self.selected_year
            )
            total = total_cached if total_cached is not None else total

            total_item = QTableWidgetItem(str(total))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            accent_color = QColor(colors["accent"])
            total_item.setForeground(accent_color)
            font = total_item.font()
            font.setBold(True)
            total_item.setFont(font)
            table.setItem(row, table.columnCount() - 1, total_item)

        # Применяем стили
        self._apply_dept_table_styles()

    def _apply_dept_table_styles(self):
        """Применение стилей к таблице отделений"""
        colors = get_colors()
        table = self.dept_stats_table

        table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                selection-background-color: {colors['table_row_selected']};
                selection-color: {colors['text']};
                gridline-color: {colors['line']};
                color: {colors['text']};
                font-size: 11pt;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {colors['line_light']};
            }}
            QTableWidget::item:selected {{
                background-color: {colors['table_row_selected']};
                color: {colors['text']};
                border: 1px solid {colors['accent']};
                outline: none;
            }}
            QTableWidget::item:hover {{
                background-color: {colors['table_row_hover']};
            }}
            QHeaderView::section {{
                background-color: transparent;
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

        # Выделяем первый столбец жирным
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item:
                font = item.font() if item.font() else QFont()
                font.setBold(True)
                font.setPointSize(11)
                item.setFont(font)

    def _load_daily_stats(self):
        """Загрузка статистики по дням"""
        colors = get_colors()
        self.stats_table.setRowCount(0)

        # Дни месяца
        import calendar

        days_in_month = calendar.monthrange(self.selected_year, self.selected_month)[1]

        # Получаем встречи за месяц
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
                # Если started_at — строка, конвертируем в datetime
                if isinstance(visit.started_at, str):
                    from datetime import datetime as dt

                    try:
                        started_dt = dt.strptime(visit.started_at, "%Y-%m-%d")
                    except ValueError:
                        continue
                elif hasattr(visit.started_at, "day"):
                    started_dt = visit.started_at
                else:
                    continue

                day = started_dt.day
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
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        # Обновляем основной контейнер
        main_card = self.findChild(QFrame, "statsMainCard")
        if main_card:
            main_card.setStyleSheet(
                f"""
                QFrame#statsMainCard {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['line']};
                    border-radius: {RADIUS['lg']}px;
                    padding: 20px;
                }}
            """
            )

        # Обновляем фильтр-панель
        filter_panel = self.findChild(QFrame, "card")
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

        # Обновляем таблицу по отделениям
        if hasattr(self, "dept_stats_table"):
            self._apply_dept_table_styles()

        # Обновляем таблицу по дням
        if hasattr(self, "stats_table"):
            self.stats_table.setStyleSheet(
                f"""
                QTableWidget {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['table_border']};
                    border-radius: {RADIUS['md']}px;
                    selection-background-color: {colors['table_row_selected']};
                    selection-color: {colors['text']};
                    gridline-color: {colors['line']};
                    color: {colors['text']};
                    outline: none;
                }}
                QTableWidget::item {{
                    padding: 12px;
                    border-bottom: 1px solid {colors['line_light']};
                }}
                QTableWidget::item:selected {{
                    background-color: {colors['table_row_selected']};
                    color: {colors['text']};
                    border: 1px solid {colors['accent']};
                    outline: none;
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

        # Обновляем шрифты фильтров
        if hasattr(self, "month_combo"):
            self.month_combo.setStyleSheet(
                f"font-size: {FONTS['size_medium']}pt; color: {colors['text']};"
            )
        if hasattr(self, "dept_combo"):
            self.dept_combo.setStyleSheet(
                f"font-size: {FONTS['size_medium']}pt; color: {colors['text']};"
            )
        if hasattr(self, "year_combo"):
            self.year_combo.setStyleSheet(
                f"font-size: {FONTS['size_medium']}pt; color: {colors['text']};"
            )

    def update_styles(self):
        """Алиас для update_theme"""
        self.update_theme()

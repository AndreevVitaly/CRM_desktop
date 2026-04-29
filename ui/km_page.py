"""
Страница КМ (Комиссионные Мероприятия)
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
    QLineEdit,
)
from PyQt6.QtCore import Qt

from models.db_models import User, KmRecord
from ui.styles import get_colors, FONTS, RADIUS


class KmPage(QWidget):
    """Страница таблицы КМ"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Панель фильтров
        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)

        # Таблица КМ
        self.table = self._create_table()
        layout.addWidget(self.table, 1)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        self._load_km_records()

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

        # Поиск по позывному/ФИО/личному номеру
        search_label = QLabel("Поиск:")
        search_label.setStyleSheet("font-weight: bold; background-color: transparent;")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Позывной, личный номер или ФИО")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(42)
        self.search_input.textChanged.connect(self._load_km_records)
        layout.addWidget(self.search_input)

        layout.addStretch()

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setFixedHeight(42)
        refresh_btn.clicked.connect(self._load_km_records)
        layout.addWidget(refresh_btn)

        return panel

    def _create_table(self) -> QTableWidget:
        """Таблица КМ"""
        colors = get_colors()

        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels(
            [
                "№",
                "Позывной",
                "Личный номер",
                "№ документа",
                "Должность",
                "ФИО",
                "Дата рождения",
                "Место работы",
                "Суть информации",
                "Принятые меры",
            ]
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)

        return table

    def _load_km_records(self):
        """Загрузка записей КМ"""
        self.table.setRowCount(0)

        records = KmRecord.get_all(self.user)

        # Фильтрация
        search_text = self.search_input.text().lower()

        filtered_records = []
        for record in records:
            # Фильтр по поиску
            if search_text:
                if not (
                    (record.callsign and search_text in record.callsign.lower())
                    or (
                        record.personal_number
                        and search_text in record.personal_number.lower()
                    )
                    or (record.full_name and search_text in record.full_name.lower())
                ):
                    continue

            filtered_records.append(record)

        for idx, record in enumerate(filtered_records):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Номер по порядку
            self.table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))

            # Позывной
            self.table.setItem(row, 1, QTableWidgetItem(record.callsign or "—"))

            # Личный номер
            self.table.setItem(row, 2, QTableWidgetItem(record.personal_number or "—"))

            # Номер документа
            self.table.setItem(row, 3, QTableWidgetItem(record.document_number or "—"))

            # Должность
            self.table.setItem(row, 4, QTableWidgetItem(record.position or "—"))

            # ФИО
            self.table.setItem(row, 5, QTableWidgetItem(record.full_name or "—"))

            # Дата рождения
            birth_date = record.birth_date.strftime("%d.%m.%Y") if record.birth_date else "—"
            self.table.setItem(row, 6, QTableWidgetItem(birth_date))

            # Место работы
            self.table.setItem(row, 7, QTableWidgetItem(record.workplace or "—"))

            # Суть информации
            info_essence = record.info_essence or "—"
            if len(info_essence) > 50:
                info_essence = info_essence[:50] + "..."
            self.table.setItem(row, 8, QTableWidgetItem(info_essence))

            # Принятые меры
            measures = record.measures_taken or "—"
            if len(measures) > 50:
                measures = measures[:50] + "..."
            self.table.setItem(row, 9, QTableWidgetItem(measures))

        self.update_count_label(len(filtered_records))

    def update_count_label(self, count: int):
        """Обновление метки с количеством записей"""
        # Найдем или создадим метку
        if not hasattr(self, 'count_label'):
            from PyQt6.QtWidgets import QLabel
            self.count_label = QLabel("")
            self.count_label.setObjectName("muted")
            self.layout().addWidget(self.count_label)
        
        self.count_label.setText(f"Найдено записей: {count}")

    def update_styles(self):
        """Обновление стилей при смене темы"""
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

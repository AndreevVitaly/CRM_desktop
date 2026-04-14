"""
Форма работы с планом - добавление/редактирование пунктов плана работы с пациентом
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from models.db_models import (
    User,
    Patient,
    Document,
    TreatmentPlanItem,
)
from ui.styles import get_colors, FONTS, RADIUS


class PlanWorkItemsFormDialog(QDialog):
    """Диалог формы работы с пунктами плана работы"""

    def __init__(self, user: User, patient: Patient, document: Document):
        super().__init__()
        self.user = user
        self.patient = patient
        self.document = document

        plan_number = self.document.doc_number or str(self.document.id)
        self.setWindowTitle(f"Работа по плану №{plan_number}")
        self.setMinimumSize(700, 500)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        plan_number = self.document.doc_number or str(self.document.id)
        # Заголовок
        title = QLabel(f"План работы №{plan_number}")
        title.setStyleSheet(f"font-size: {FONTS['size_title']}pt; font-weight: bold;")
        layout.addWidget(title)

        # Информация о плане
        info_label = QLabel(
            f"Дата: {self.document.doc_date.strftime('%d.%m.%Y') if self.document.doc_date else '—'} | "
            f"Описание: {self.document.summary or '—'}"
        )
        info_label.setStyleSheet(f"color: {colors['text_muted']};")
        layout.addWidget(info_label)

        # Таблица пунктов плана
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(
            ["№", "Мероприятие", "Срок исполнения", "Статус"]
        )

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)

        layout.addWidget(self.items_table, 1)

        # Кнопки управления пунктами
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить пункт")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_item)
        buttons_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.setObjectName("secondaryBtn")
        edit_btn.setFixedHeight(36)
        edit_btn.clicked.connect(self._edit_item)
        buttons_layout.addWidget(edit_btn)

        toggle_btn = QPushButton("Переключить статус")
        toggle_btn.setObjectName("secondaryBtn")
        toggle_btn.setFixedHeight(36)
        toggle_btn.clicked.connect(self._toggle_item)
        buttons_layout.addWidget(toggle_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.setFixedHeight(36)
        delete_btn.clicked.connect(self._delete_item)
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        self._load_items()

    def _load_items(self):
        """Загрузка пунктов плана"""
        self.items_table.setRowCount(0)
        items = TreatmentPlanItem.get_by_plan(self.document.id)

        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            # Номер
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item.order_num)))

            # Мероприятие
            self.items_table.setItem(row, 1, QTableWidgetItem(item.event))

            # Срок
            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            self.items_table.setItem(row, 2, QTableWidgetItem(due_date))

            # Статус
            status = "Выполнено" if item.is_completed else "В ожидании"
            status_item = QTableWidgetItem(status)
            colors = get_colors()
            status_item.setForeground(
                Qt.GlobalColor.darkGreen
                if item.is_completed
                else QColor(colors["text"])
            )
            self.items_table.setItem(row, 3, status_item)

    def _add_item(self):
        """Добавление пункта плана"""
        dialog = PlanItemEditDialog(self, None)
        if dialog.exec():
            self._load_items()

    def _edit_item(self):
        """Редактирование пункта плана"""
        selected = self.items_table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите пункт для редактирования"
            )
            return

        row = selected[0].row()
        items = TreatmentPlanItem.get_by_plan(self.document.id)
        if row >= len(items):
            return

        item = items[row]
        dialog = PlanItemEditDialog(self, item)
        if dialog.exec():
            self._load_items()

    def _toggle_item(self):
        """Переключение статуса пункта плана"""
        selected = self.items_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите пункт")
            return

        row = selected[0].row()
        items = TreatmentPlanItem.get_by_plan(self.document.id)
        if row < len(items):
            item = items[row]
            item.toggle()
            self._load_items()

    def _delete_item(self):
        """Удаление пункта плана"""
        selected = self.items_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите пункт для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранный пункт плана?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            items = TreatmentPlanItem.get_by_plan(self.document.id)
            if row < len(items):
                item = items[row]
                item.delete()
                self._load_items()


class PlanItemEditDialog(QDialog):
    """Диалог редактирования отдельного пункта плана"""

    def __init__(self, parent: PlanWorkItemsFormDialog, item: TreatmentPlanItem = None):
        super().__init__(parent)
        self.parent_dialog = parent
        self.item = item
        self.is_edit = item is not None and item.id is not None

        title = "Редактирование пункта" if self.is_edit else "Новый пункт плана"
        self.setWindowTitle(title)
        self.setMinimumSize(450, 250)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Мероприятие
        layout.addWidget(QLabel("Мероприятие*:"))
        from PyQt6.QtWidgets import QTextEdit

        self.event_input = QTextEdit()
        self.event_input.setPlaceholderText("Описание мероприятия")
        self.event_input.setMaximumHeight(80)
        layout.addWidget(self.event_input)

        # Срок исполнения
        layout.addWidget(QLabel("Срок исполнения:"))
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addMonths(1))
        self.due_date_input.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(self.due_date_input)

        layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        # Заполнение при редактировании
        if self.is_edit:
            self.event_input.setText(self.item.event)
            if self.item.due_date:
                self.due_date_input.setDate(
                    QDate(
                        self.item.due_date.year,
                        self.item.due_date.month,
                        self.item.due_date.day,
                    )
                )

    def _save(self):
        """Сохранение пункта плана"""
        event = self.event_input.toPlainText().strip()
        if not event:
            QMessageBox.warning(self, "Ошибка", "Введите описание мероприятия")
            return

        if not self.item:
            self.item = TreatmentPlanItem()
            self.item.patient_id = self.parent_dialog.patient.id
            self.item.plan_document_id = self.parent_dialog.document.id
            # Определяем следующий order_num
            existing_items = TreatmentPlanItem.get_by_plan(
                self.parent_dialog.document.id
            )
            self.item.order_num = len(existing_items) + 1

        self.item.event = event
        self.item.due_date = self.due_date_input.date().toPyDate()

        self.item.save()
        self.accept()

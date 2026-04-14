"""
Форма создания/редактирования плана работы с пациентом (документ-план + пункты)
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QTextEdit,
    QDateEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QDate
from datetime import date

from models.db_models import (
    User,
    Patient,
    Document,
    TreatmentPlanItem,
    DOCUMENT_TYPE_PLAN,
    DOCUMENT_CLASSIFICATION_CHOICES,
)
from ui.styles import get_colors, FONTS, RADIUS


class PlanWorkFormDialog(QDialog):
    """Диалог формы плана работы с пациентом (документ + пункты плана)"""

    def __init__(self, user: User, patient: Patient, document: Document = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.document = document
        self.is_edit = document is not None and document.id is not None
        self.plan_items = []  # Список пунктов плана

        title = "Редактирование плана работы" if self.is_edit else "Новый план работы"
        self.setWindowTitle(title)
        self.setMinimumSize(700, 600)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # === Группа: Информация о документе-плане ===
        doc_group = QGroupBox("Информация о плане")
        doc_layout = QFormLayout()
        doc_layout.setSpacing(12)

        # Гриф секретности
        self.classification_combo = QTextEdit()
        self.classification_combo.setReadOnly(True)
        self.classification_combo.setMaximumHeight(40)
        self.classification_combo.setText("НС")  # По умолчанию

        # Дата документа
        self.doc_date_input = QDateEdit()
        self.doc_date_input.setCalendarPopup(True)
        self.doc_date_input.setDate(QDate.currentDate())
        self.doc_date_input.setDisplayFormat("dd.MM.yyyy")
        doc_layout.addRow("Дата плана*", self.doc_date_input)

        # Номер документа
        self.doc_number_input = QTextEdit()
        self.doc_number_input.setPlaceholderText("Номер плана")
        self.doc_number_input.setMaximumHeight(40)
        doc_layout.addRow("№ плана", self.doc_number_input)

        # Краткое содержание / Описание
        self.summary_input = QTextEdit()
        self.summary_input.setPlaceholderText("Общее описание плана работы")
        self.summary_input.setMaximumHeight(80)
        doc_layout.addRow("Описание*", self.summary_input)

        doc_group.setLayout(doc_layout)
        layout.addWidget(doc_group)

        # === Группа: Пункты плана ===
        items_group = QGroupBox("Пункты плана")
        items_layout = QVBoxLayout()
        items_layout.setSpacing(8)

        # Кнопка добавления пункта
        add_item_btn = QPushButton("Добавить пункт")
        add_item_btn.setFixedHeight(32)
        add_item_btn.clicked.connect(self._add_plan_item_row)
        items_layout.addWidget(add_item_btn)

        # Таблица пунктов
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(
            ["Мероприятие", "Срок исполнения", ""]
        )

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)

        items_layout.addWidget(self.items_table)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)

        layout.addStretch()

        # === Кнопки ===
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("💾 Сохранить")
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
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']}; QGroupBox {{ color: {colors['text']}; }}"
        )

        # Заполнение при редактировании
        if self.is_edit:
            self._fill_data()

    def _fill_data(self):
        """Заполнение данными при редактировании"""
        if not self.document:
            return

        self.doc_date_input.setDate(
            QDate(
                self.document.doc_date.year,
                self.document.doc_date.month,
                self.document.doc_date.day,
            )
        )

        if self.document.doc_number:
            self.doc_number_input.setText(self.document.doc_number)

        self.summary_input.setText(self.document.summary or "")

        # Загрузка пунктов плана
        self.plan_items = TreatmentPlanItem.get_by_plan(self.document.id)
        self.items_table.setRowCount(0)
        for item in self.plan_items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            event_item = QTableWidgetItem(item.event)
            self.items_table.setItem(row, 0, event_item)

            due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else "—"
            due_item = QTableWidgetItem(due_date)
            due_item.setData(Qt.ItemDataRole.UserRole, item.due_date)
            self.items_table.setItem(row, 1, due_item)

            # Кнопка удаления
            delete_btn = QPushButton("✕")
            delete_btn.setFixedWidth(30)
            delete_btn.clicked.connect(lambda checked, r=row: self._remove_item_row(r))
            self.items_table.setCellWidget(row, 2, delete_btn)

    def _add_plan_item_row(self):
        """Добавление строки пункта плана"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        event_item = QTableWidgetItem("")
        self.items_table.setItem(row, 0, event_item)

        # Дата по умолчанию — сегодня + 1 месяц
        default_date = QDate.currentDate().addMonths(1)
        due_item = QTableWidgetItem(default_date.toString("dd.MM.yyyy"))
        due_item.setData(Qt.ItemDataRole.UserRole, default_date.toPyDate())
        self.items_table.setItem(row, 1, due_item)

        # Кнопка удаления
        delete_btn = QPushButton("✕")
        delete_btn.setFixedWidth(30)
        delete_btn.clicked.connect(lambda checked, r=row: self._remove_item_row(r))
        self.items_table.setCellWidget(row, 2, delete_btn)

        # Прокрутка к новой строке
        self.items_table.scrollToBottom()

    def _remove_item_row(self, row):
        """Удаление строки пункта плана"""
        self.items_table.removeRow(row)

    def _save(self):
        """Сохранение плана работы"""
        # Валидация
        summary = self.summary_input.toPlainText().strip()
        if not summary:
            QMessageBox.warning(self, "Ошибка", "Введите описание плана")
            return

        # Валидация пунктов плана
        items_data = []
        for row in range(self.items_table.rowCount()):
            event_item = self.items_table.item(row, 0)
            due_item = self.items_table.item(row, 1)

            event_text = event_item.text().strip() if event_item else ""
            if not event_text:
                QMessageBox.warning(
                    self, "Ошибка", f"В пункте плана №{row + 1} введите описание"
                )
                return

            due_date = due_item.data(Qt.ItemDataRole.UserRole)
            items_data.append(
                {"event": event_text, "due_date": due_date, "order_num": row + 1}
            )

        if not items_data:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один пункт плана")
            return

        # Создание/обновление документа-плана
        if not self.document:
            self.document = Document()
            self.document.patient_id = self.patient.id
            self.document.doc_type = DOCUMENT_TYPE_PLAN
            self.document.author_id = self.user.id

        self.document.doc_date = self.doc_date_input.date().toPyDate()
        self.document.doc_number = self.doc_number_input.toPlainText().strip() or None
        self.document.summary = summary
        self.document.classification = "NS"  # По умолчанию НС

        self.document.save()

        # Удаление старых пунктов при редактировании
        if self.is_edit:
            old_items = TreatmentPlanItem.get_by_plan(self.document.id)
            for old_item in old_items:
                old_item.delete()

        # Создание пунктов плана
        for item_data in items_data:
            plan_item = TreatmentPlanItem()
            plan_item.patient_id = self.patient.id
            plan_item.plan_document_id = self.document.id
            plan_item.order_num = item_data["order_num"]
            plan_item.event = item_data["event"]
            plan_item.due_date = item_data["due_date"]
            plan_item.save()

        QMessageBox.information(self, "Успешно", "План работы сохранён")
        self.accept()

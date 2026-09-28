"""Страница таблицы «Модель»."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QColor, QCursor

from models.db_models import ModelRecord, Patient, User
from ui.styles import FONTS, RADIUS, get_colors, get_main_stylesheet


class ModelRecordDialog(QDialog):
    def __init__(self, user: User, record: ModelRecord | None = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.record = record
        self.setWindowTitle("Редактирование модели" if record else "Новая запись модели")
        self.setMinimumWidth(980)

        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 14, 16, 24)

        self.threat_input = QLineEdit(record.threat if record else "")
        self.threat_input.setPlaceholderText("Введите угрозу")
        layout.addRow("Угрозы:", self.threat_input)

        aa_widget = QWidget()
        aa_layout = QHBoxLayout(aa_widget)
        aa_layout.setContentsMargins(0, 0, 0, 0)
        aa_layout.setSpacing(12)

        self.patient_lists = {}
        self.required_count_inputs = {}
        selected_patient_ids = set(record.patient_ids if record else [])
        patients = Patient.get_all(user=user, include_inactive=False)
        category_types = (
            ("adult", "Категория А"),
            ("child", "Категория Д"),
            ("undefined", "Категория К"),
        )
        for patient_type, category_title in category_types:
            group = QGroupBox(category_title)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(8)

            required_count_layout = QHBoxLayout()
            required_count_layout.addWidget(QLabel("Необходимое количество:"))
            required_count_input = QSpinBox()
            required_count_input.setRange(0, 999999)
            field_name = {
                "adult": "required_a_count",
                "child": "required_d_count",
                "undefined": "required_k_count",
            }[patient_type]
            required_count_input.setValue(
                getattr(record, field_name, 0) if record else 0
            )
            self.required_count_inputs[patient_type] = required_count_input
            required_count_layout.addWidget(required_count_input)
            group_layout.addLayout(required_count_layout)

            patient_list = QListWidget()
            patient_list.setMinimumHeight(190)
            for patient in patients:
                if patient.patient_type != patient_type:
                    continue
                item = QListWidgetItem(patient.callsign)
                item.setData(Qt.ItemDataRole.UserRole, patient.id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked
                    if patient.id in selected_patient_ids
                    else Qt.CheckState.Unchecked
                )
                patient_list.addItem(item)
            self.patient_lists[patient_type] = patient_list
            group_layout.addWidget(patient_list)

            selection_buttons = QHBoxLayout()
            select_all_button = QPushButton("Выбрать всех")
            select_all_button.setObjectName("actionButton")
            select_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
            select_all_button.clicked.connect(
                lambda _checked=False, value=patient_type: self._set_category_checked(
                    value, True
                )
            )
            selection_buttons.addWidget(select_all_button)

            clear_button = QPushButton("Снять выбор")
            clear_button.setObjectName("actionButton")
            clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_button.clicked.connect(
                lambda _checked=False, value=patient_type: self._set_category_checked(
                    value, False
                )
            )
            selection_buttons.addWidget(clear_button)
            group_layout.addLayout(selection_buttons)
            aa_layout.addWidget(group, 1)
        layout.addRow("Наличие АА:", aa_widget)

        self.setStyleSheet(get_main_stylesheet())

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        buttons_layout.addStretch()

        save_button = QPushButton("Сохранить")
        save_button.setObjectName("secondaryBtn")
        save_button.setFixedHeight(40)
        save_button.setMinimumWidth(118)
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self._accept)
        save_button.setDefault(True)
        buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("secondaryBtn")
        cancel_button.setFixedHeight(40)
        cancel_button.setMinimumWidth(118)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addRow(buttons_layout)

    def _accept(self):
        if not self.threat_input.text().strip():
            QMessageBox.warning(self, "Проверка данных", "Заполните поле «Угрозы».")
            self.threat_input.setFocus()
            return
        self.accept()

    def _set_category_checked(self, patient_type: str, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        patient_list = self.patient_lists[patient_type]
        for index in range(patient_list.count()):
            patient_list.item(index).setCheckState(state)

    def selected_patient_ids(self) -> list[int]:
        selected_ids = []
        for patient_list in self.patient_lists.values():
            selected_ids.extend(
                patient_list.item(index).data(Qt.ItemDataRole.UserRole)
                for index in range(patient_list.count())
                if patient_list.item(index).checkState() == Qt.CheckState.Checked
            )
        return selected_ids

    def apply_to(self, record: ModelRecord):
        record.threat = self.threat_input.text().strip()
        record.required_a_count = self.required_count_inputs["adult"].value()
        record.required_d_count = self.required_count_inputs["child"].value()
        record.required_k_count = self.required_count_inputs["undefined"].value()


class ModelPage(QWidget):
    """Просмотр и редактирование таблицы «Модель»."""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        panel = QFrame()
        panel.setObjectName("modelActionsPanel")
        panel_layout = QHBoxLayout(panel)
        title = QLabel("Модель")
        title.setStyleSheet(f"font-size: {FONTS['size_large']}pt; font-weight: 700;")
        panel_layout.addWidget(title)
        panel_layout.addStretch()

        add_button = self._button("Добавить", "actionButton")
        add_button.clicked.connect(self._add_record)
        panel_layout.addWidget(add_button)

        edit_button = self._button("Редактировать", "actionButton")
        edit_button.clicked.connect(self._edit_selected)
        panel_layout.addWidget(edit_button)

        delete_button = self._button("Удалить", "dangerBtn")
        delete_button.clicked.connect(self._delete_selected)
        panel_layout.addWidget(delete_button)

        refresh_button = self._button("Обновить", "actionButton")
        refresh_button.clicked.connect(self._load_records)
        panel_layout.addWidget(refresh_button)
        layout.addWidget(panel)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Порядковый номер",
                "Угрозы",
                "Необходимо А",
                "Категория А",
                "Необходимо Д",
                "Категория Д",
                "Необходимо К",
                "Категория К",
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in (2, 4, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        for column in (3, 5, 7):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._open_patient_from_cell)
        self.table.doubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table, 1)

        self.count_label = QLabel()
        self.count_label.setObjectName("muted")
        layout.addWidget(self.count_label)

        self.setStyleSheet(get_main_stylesheet())
        self.update_styles()
        self._load_records()

    def _button(self, text: str, object_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setFixedHeight(40)
        button.setMinimumWidth(110)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _selected_record(self) -> ModelRecord | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Модель", "Выберите строку таблицы.")
            return None
        item = self.table.item(row, 0)
        return ModelRecord.get_by_id(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _load_records(self):
        records = ModelRecord.get_all()
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            number_item = QTableWidgetItem(str(record.id))
            number_item.setData(Qt.ItemDataRole.UserRole, record.id)
            number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, number_item)
            self.table.setItem(row, 1, QTableWidgetItem(record.threat))
            category_data = (
                (2, 3, record.required_a_count, "adult"),
                (4, 5, record.required_d_count, "child"),
                (6, 7, record.required_k_count, "undefined"),
            )
            for count_column, callsign_column, required_count, patient_type in category_data:
                count_item = QTableWidgetItem(str(required_count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, count_column, count_item)
                callsigns = record.callsigns_by_type(patient_type)
                callsign_item = QTableWidgetItem(", ".join(callsigns) if callsigns else "—")
                callsign_item.setData(Qt.ItemDataRole.UserRole, patient_type)
                if callsigns:
                    callsign_item.setForeground(QColor(get_colors()["accent"]))
                    font = callsign_item.font()
                    font.setUnderline(True)
                    callsign_item.setFont(font)
                    callsign_item.setToolTip("Нажмите, чтобы открыть карточку категории АА")
                self.table.setItem(row, callsign_column, callsign_item)
        self.count_label.setText(f"Записей: {len(records)}")

    def _open_patient_from_cell(self, row: int, column: int):
        if column not in (3, 5, 7):
            return
        record_item = self.table.item(row, 0)
        type_item = self.table.item(row, column)
        if not record_item or not type_item:
            return
        record = ModelRecord.get_by_id(
            record_item.data(Qt.ItemDataRole.UserRole)
        )
        if not record:
            return
        patient_type = type_item.data(Qt.ItemDataRole.UserRole)
        patients = []
        for patient_id in record.patient_ids:
            patient = Patient.get_by_id(patient_id)
            if patient and patient.patient_type == patient_type:
                patients.append(patient)
        patients.sort(key=lambda patient: patient.callsign.lower())
        if not patients:
            return
        if len(patients) == 1:
            self._open_patient_card(patients[0].id)
            return

        menu = QMenu(self)
        for patient in patients:
            action = menu.addAction(patient.callsign)
            action.setData(patient.id)
        selected_action = menu.exec(QCursor.pos())
        if selected_action:
            self._open_patient_card(selected_action.data())

    def _open_patient_card(self, patient_id: int):
        from ui.patient_detail import PatientDetailDialog

        dialog = PatientDetailDialog(self.user, patient_id)
        dialog.exec()
        self._load_records()

    def _add_record(self):
        dialog = ModelRecordDialog(self.user, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        record = ModelRecord()
        dialog.apply_to(record)
        record.save()
        record.set_patients(dialog.selected_patient_ids())
        self._load_records()

    def _edit_selected(self, *_args):
        if _args and hasattr(_args[0], "column") and _args[0].column() in (3, 5, 7):
            return
        record = self._selected_record()
        if not record:
            return
        dialog = ModelRecordDialog(self.user, record, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        dialog.apply_to(record)
        record.save()
        record.set_patients(dialog.selected_patient_ids())
        self._load_records()

    def _delete_selected(self):
        record = self._selected_record()
        if not record:
            return
        answer = QMessageBox.question(
            self,
            "Удаление записи",
            f"Удалить запись № {record.id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            record.delete()
            self._load_records()

    def update_styles(self):
        colors = get_colors()
        panel = self.findChild(QFrame, "modelActionsPanel")
        if panel:
            panel.setStyleSheet(
                f"QFrame#modelActionsPanel {{ background-color: {colors['surface']}; "
                f"border: 1px solid {colors['line']}; border-radius: {RADIUS['lg']}px; "
                "padding: 12px; }}"
            )

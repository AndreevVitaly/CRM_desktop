"""
Страница списка пациентов
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QMenu,
    QFileDialog,
    QInputDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from models.db_models import User, Patient, Facility, get_department_choices
from ui.styles import get_colors, FONTS, RADIUS, get_main_stylesheet


class PatientsPage(QWidget):
    """Страница пациентов"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.current_filter = ""
        self.type_filter = ""
        self.facility_filter = 0
        self.department_filter = ""
        self.doctor_filter = 0
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя панель с фильтрами
        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)

        # Таблица пациентов
        self.table = self._create_table()
        layout.addWidget(self.table, 1)

        self.setLayout(layout)
        self.setStyleSheet(get_main_stylesheet())

        panel = self.findChild(QFrame, "patientsFilterPanel")
        if panel:
            panel.setStyleSheet(self._filter_panel_style())

        for combo in self.findChildren(QComboBox, "filterCombo"):
            combo.setStyleSheet(self._filter_combo_style())
        for button in self.findChildren(QPushButton, "filterButton"):
            button.setStyleSheet(self._filter_button_style())

        # Загрузка данных
        self._load_patients()

    def _safe_load_patients(self):
        """Безопасная загрузка данных с проверкой существования таблицы"""
        if hasattr(self, "table") and self.table is not None:
            try:
                self._load_patients()
            except RuntimeError:
                pass  # Таблица уже удалена

    def _create_filter_panel(self) -> QFrame:
        """Панель фильтров"""
        panel = QFrame()
        panel.setObjectName("patientsFilterPanel")
        panel.setFixedHeight(128)
        panel.setStyleSheet(self._filter_panel_style())

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(12)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Поиск по позывному, личному номеру...")
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._on_search_changed)
        filters_layout.addWidget(self.search_input)

        # Тип пациента
        self.type_combo = QComboBox()
        self.type_combo.setFrame(False)
        self.type_combo.setObjectName("filterCombo")
        self.type_combo.addItem("Все типы", "")
        self.type_combo.addItem("Взрослые", "adult")
        self.type_combo.addItem("Дети", "child")
        self.type_combo.addItem("Неопределённые", "undefined")
        self.type_combo.setFixedWidth(140)
        self.type_combo.setFixedHeight(34)
        self.type_combo.setStyleSheet(self._filter_combo_style())
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.type_combo)

        # Место размещения
        self.facility_combo = QComboBox()
        self.facility_combo.setFrame(False)
        self.facility_combo.setObjectName("filterCombo")
        self.facility_combo.addItem("Все места", 0)
        facilities = Facility.get_all()
        for f in facilities:
            self.facility_combo.addItem(f.name, f.id)
        self.facility_combo.setFixedWidth(180)
        self.facility_combo.setFixedHeight(34)
        self.facility_combo.setStyleSheet(self._filter_combo_style())
        self.facility_combo.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.facility_combo)

        self.department_combo = QComboBox()
        self.department_combo.setFrame(False)
        self.department_combo.setObjectName("filterCombo")
        self.department_combo.addItem("Все отделения", "")
        for dept_code, dept_name in get_department_choices(include_inactive=False):
            self.department_combo.addItem(dept_name, dept_code)
        self.department_combo.setFixedWidth(190)
        self.department_combo.setFixedHeight(34)
        self.department_combo.setStyleSheet(self._filter_combo_style())
        self.department_combo.currentIndexChanged.connect(self._on_department_changed)
        filters_layout.addWidget(self.department_combo)

        self.doctor_combo = QComboBox()
        self.doctor_combo.setFrame(False)
        self.doctor_combo.setObjectName("filterCombo")
        self.doctor_combo.setFixedWidth(210)
        self.doctor_combo.setFixedHeight(34)
        self.doctor_combo.setStyleSheet(self._filter_combo_style())
        self.doctor_combo.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.doctor_combo)
        self._populate_doctor_filter()

        # Отделение (для LEAD, NUR)
        if self.user.role == User.ROLE_LEAD:
            dept_label = QLabel(self.user.department_display)
            dept_label.setStyleSheet("font-weight: bold;")
            filters_layout.addWidget(dept_label)

        filters_layout.addStretch()

        # Кнопка добавления (ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            add_btn = QPushButton("Добавить пациента")
            add_btn.setObjectName("filterButton")
            add_btn.setFixedHeight(34)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet(self._filter_button_style())
            add_btn.clicked.connect(self._add_patient)
            actions_layout.addWidget(add_btn)

        # Кнопка справки (ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            cert_btn = QPushButton("Справка")
            cert_btn.setObjectName("filterButton")
            cert_btn.setFixedHeight(34)
            cert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cert_btn.setStyleSheet(self._filter_button_style())
            cert_btn.clicked.connect(self._generate_certificate_selected)
            actions_layout.addWidget(cert_btn)

        if self.user.role in (
            User.ROLE_ADMIN,
            User.ROLE_REGISTRAR,
            User.ROLE_LEAD,
            User.ROLE_DOCTOR,
        ):
            export_btn = QPushButton("Экспорт выбранных")
            export_btn.setObjectName("filterButton")
            export_btn.setFixedHeight(34)
            export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            export_btn.setStyleSheet(self._filter_button_style())
            export_btn.clicked.connect(self._export_selected_patients)
            actions_layout.addWidget(export_btn)

        # Кнопка сброса
        reset_btn = QPushButton("Сброс")
        reset_btn.setObjectName("filterButton")
        reset_btn.setFixedHeight(34)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(self._filter_button_style())
        reset_btn.clicked.connect(self._reset_filters)
        actions_layout.addWidget(reset_btn)
        actions_layout.addStretch()

        layout.addLayout(filters_layout)
        layout.addLayout(actions_layout)

        return panel

    def _filter_panel_style(self) -> str:
        colors = get_colors()
        return f"""
            QFrame#patientsFilterPanel {{
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
                padding: 4px 12px;
                min-height: 0px;
                font-weight: 500;
                font-size: {FONTS['size_small']}pt;
                color: {colors['text']};
            }}
            QComboBox#filterCombo:hover {{
                border: 1px solid {colors['accent']};
            }}
            QComboBox#filterCombo:focus {{
                border: 1px solid {colors['accent']};
            }}
            QComboBox#filterCombo::drop-down {{
                border: none;
                width: 0px;
            }}
            QComboBox#filterCombo::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border: none;
            }}
            QComboBox#filterCombo QAbstractItemView {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                selection-background-color: {colors['accent_light']};
                selection-color: {colors['accent']};
                outline: none;
            }}
        """

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

    def _create_table(self) -> QTableWidget:
        """Таблица пациентов"""
        colors = get_colors()

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(
            [
                "Позывной",
                "Личный номер",
                "Дата рождения",
                "Пол",
                "Тип",
                "Отделение",
                "Врач",
                "Телефон",
            ]
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)

        # Контекстное меню
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_context_menu)

        # Двойной клик для открытия
        table.doubleClicked.connect(self._open_patient)

        return table

    def _load_patients(self):
        """Загрузка пациентов"""
        self.table.setRowCount(0)

        patients = Patient.get_all(
            user=self.user,
            include_inactive=False,
            search_query="",
            patient_type=self.type_filter,
            facility_id=self.facility_filter,
        )

        # Фильтрация на уровне Python (SQLite не работает с кириллицей в LIKE)
        if self.current_filter:
            search_lower = self.current_filter.lower()
            patients = [
                p
                for p in patients
                if (p.callsign and p.callsign.lower().startswith(search_lower))
                or (
                    p.personal_number
                    and p.personal_number.lower().startswith(search_lower)
                )
                or (p.document_id and p.document_id.lower().startswith(search_lower))
            ]

        if self.department_filter:
            patients = [p for p in patients if p.department == self.department_filter]

        if self.doctor_filter:
            patients = [p for p in patients if p.doctor_id == self.doctor_filter]

        for patient in patients:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Позывной
            name_item = QTableWidgetItem(patient.callsign or "")
            name_item.setData(Qt.ItemDataRole.UserRole, patient.id)
            self.table.setItem(row, 0, name_item)

            # Личный номер
            self.table.setItem(row, 1, QTableWidgetItem(patient.personal_number or "—"))

            # Дата рождения
            self.table.setItem(
                row, 2, QTableWidgetItem(patient.birth_date.strftime("%d.%m.%Y"))
            )

            # Пол
            gender_dict = {"M": "М", "F": "Ж"}
            self.table.setItem(
                row, 3, QTableWidgetItem(gender_dict.get(patient.gender, ""))
            )

            # Тип
            type_dict = {
                "adult": "Взрослый",
                "child": "Детский",
                "undefined": "Неопределённый",
            }
            self.table.setItem(
                row, 4, QTableWidgetItem(type_dict.get(patient.patient_type, ""))
            )

            # Отделение
            self.table.setItem(row, 5, QTableWidgetItem(patient.department_display))

            # Врач
            doctor_name = patient.doctor.full_name if patient.doctor else "—"
            self.table.setItem(row, 6, QTableWidgetItem(doctor_name))

            # Телефон
            self.table.setItem(row, 7, QTableWidgetItem(patient.phone or "—"))

    def _on_search_changed(self, text: str):
        """Изменение поиска"""
        self.current_filter = text
        self._load_patients()

    def _on_filter_changed(self):
        """Изменение фильтра"""
        self.type_filter = self.type_combo.currentData()
        self.facility_filter = self.facility_combo.currentData()
        self.department_filter = self.department_combo.currentData()
        self.doctor_filter = self.doctor_combo.currentData()
        self._load_patients()

    def _on_department_changed(self):
        self.department_filter = self.department_combo.currentData()
        self._populate_doctor_filter()
        self.doctor_filter = self.doctor_combo.currentData()
        self._load_patients()

    def _populate_doctor_filter(self):
        selected_dept = (
            self.department_combo.currentData()
            if hasattr(self, "department_combo")
            else ""
        )
        current_doctor = (
            self.doctor_combo.currentData() if hasattr(self, "doctor_combo") else 0
        )

        self.doctor_combo.blockSignals(True)
        self.doctor_combo.clear()
        self.doctor_combo.addItem("Все врачи", 0)

        doctors = User.get_by_role(User.ROLE_DOCTOR)
        if selected_dept:
            doctors = [d for d in doctors if d.department == selected_dept]
        if self.user.role in (User.ROLE_LEAD, User.ROLE_NURSE):
            doctors = [d for d in doctors if d.department == self.user.department]
        elif self.user.role == User.ROLE_DOCTOR:
            doctors = [d for d in doctors if d.id == self.user.id]

        for doctor in doctors:
            self.doctor_combo.addItem(doctor.full_name or doctor.username, doctor.id)

        index = self.doctor_combo.findData(current_doctor)
        self.doctor_combo.setCurrentIndex(index if index >= 0 else 0)
        self.doctor_combo.blockSignals(False)

    def _reset_filters(self):
        """Сброс фильтров"""
        self.search_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.facility_combo.setCurrentIndex(0)
        self.department_combo.setCurrentIndex(0)
        self._populate_doctor_filter()
        self.doctor_combo.setCurrentIndex(0)
        self.current_filter = ""
        self.type_filter = ""
        self.facility_filter = 0
        self.department_filter = ""
        self.doctor_filter = 0
        self._load_patients()

    def _show_context_menu(self, pos):
        """Контекстное меню"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        patient_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        patient = Patient.get_by_id(patient_id)
        if not patient:
            return

        menu = QMenu()

        # Открыть
        open_action = menu.addAction("Открыть карточку")
        open_action.triggered.connect(lambda: self._open_patient_by_id(patient_id))

        # Редактировать (ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            if (
                self.user.role == User.ROLE_LEAD
                and patient.department != self.user.department
            ):
                pass  # LEAD не может редактировать пациентов другого отделения
            else:
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self._edit_patient(patient_id))

        # Скрыть/Восстановить (ADMIN, REG)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            if patient.is_active:
                hide_action = menu.addAction("Скрыть")
                hide_action.triggered.connect(lambda: self._hide_patient(patient_id))
            else:
                restore_action = menu.addAction("Восстановить")
                restore_action.triggered.connect(
                    lambda: self._restore_patient(patient_id)
                )

        # Справка (ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            cert_action = menu.addAction("Справка")
            cert_action.triggered.connect(
                lambda: self._generate_certificate(patient_id)
            )

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _get_selected_patient_id(self) -> int:
        """Получение ID выбранного пациента"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        selected = self.table.selectedItems()
        if not selected:
            return None
        return selected[0].data(Qt.ItemDataRole.UserRole)

    def _get_selected_patient_ids(self) -> list[int]:
        rows = {
            index.row()
            for index in self.table.selectionModel().selectedRows()
            if index.row() >= 0
        }
        if not rows and self.table.currentRow() >= 0:
            rows.add(self.table.currentRow())

        patient_ids = []
        for row in sorted(rows):
            item = self.table.item(row, 0)
            if not item:
                continue
            patient_id = item.data(Qt.ItemDataRole.UserRole)
            if patient_id is not None:
                patient_ids.append(patient_id)
        return patient_ids

    def _export_selected_patients(self):
        patient_ids = self._get_selected_patient_ids()
        if not patient_ids:
            QMessageBox.information(
                self,
                "Экспорт выбранных",
                "Выберите одного или нескольких пациентов в таблице",
            )
            return

        from utils.sync_exchange import build_export_filename, export_sync_package

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт выбранных пациентов",
            build_export_filename(self.user),
            "Пакет обмена PULSAR (*.pulsarzip)",
        )
        if not file_path:
            return

        password, ok = QInputDialog.getText(
            self,
            "Пароль пакета",
            "Введите пароль для шифрования пакета:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if not password:
            QMessageBox.warning(
                self, "Экспорт выбранных", "Пароль не может быть пустым"
            )
            return

        password_repeat, ok = QInputDialog.getText(
            self,
            "Пароль пакета",
            "Повторите пароль:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if password != password_repeat:
            QMessageBox.warning(self, "Экспорт выбранных", "Пароли не совпадают")
            return

        try:
            result = export_sync_package(
                self.user, file_path, password, patient_ids=patient_ids
            )
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка экспорта", str(exc))
            return

        counts = result["manifest"]["counts"]
        QMessageBox.information(
            self,
            "Экспорт завершен",
            (
                f"Пакет сохранен:\n{result['path']}\n\n"
                f"Пациенты: {counts.get('patients', 0)}\n"
                f"Документы: {counts.get('documents', 0)}\n"
                f"Встречи: {counts.get('encounters', 0)}\n"
                f"Пункты планов: {counts.get('treatment_plan_items', 0)}\n"
                f"КМ: {counts.get('km_records', 0)}"
            ),
        )

    def _open_patient(self, index):
        """Открытие пациента (двойной клик)"""
        patient_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self._open_patient_by_id(patient_id)

    def _open_patient_by_id(self, patient_id: int):
        """Открытие карточки пациента"""
        from ui.patient_detail import PatientDetailDialog

        dialog = PatientDetailDialog(self.user, patient_id)
        dialog.exec()

        # Безопасное обновление данных
        self._safe_load_patients()

    def _add_patient(self):
        """Добавление пациента"""
        from ui.patient_form import PatientFormDialog

        dialog = PatientFormDialog(self.user, None)
        if dialog.exec():
            self._safe_load_patients()

    def _edit_patient(self, patient_id: int):
        """Редактирование пациента"""
        from ui.patient_form import PatientFormDialog

        patient = Patient.get_by_id(patient_id)
        dialog = PatientFormDialog(self.user, patient)
        if dialog.exec():
            self._safe_load_patients()

    def _hide_patient(self, patient_id: int):
        """Скрытие пациента"""
        patient = Patient.get_by_id(patient_id)
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Скрыть пациента {patient.full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            patient.delete()
            self._safe_load_patients()

    def _restore_patient(self, patient_id: int):
        """Восстановление пациента"""
        patient = Patient.get_by_id(patient_id)
        patient.restore()
        self._safe_load_patients()

    def _generate_certificate_selected(self):
        """Генерация справки для выбранного пациента"""
        patient_id = self._get_selected_patient_id()
        if not patient_id:
            QMessageBox.information(self, "Информация", "Выберите пациента из таблицы")
            return
        self._generate_certificate(patient_id)

    def _generate_certificate(self, patient_id: int):
        """Генерация справки"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
        from datetime import datetime

        patient = Patient.get_by_id(patient_id)

        if not patient:
            QMessageBox.warning(self, "Ошибка", "Пациент не найден")
            return

        # Генерация текста справки
        certificate_text = f"""
СПРАВКА
о прохождении лечения

Выдана {patient.full_name}

Дата рождения: {patient.birth_date.strftime("%d.%m.%Y")}
Пол: {"Мужской" if patient.gender == "M" else "Женский"}
Отделение: {patient.department_display}
{f"Лечащий врач: {patient.doctor.full_name}" if patient.doctor else ""}
{f"Место размещения: {patient.facility.name}" if patient.facility else ""}

Дана в том, что пациент действительно проходит лечение в нашем учреждении.

Справка действительна в течение 30 дней с даты выдачи.
Дата выдачи: {datetime.now().strftime("%d.%m.%Y")}
        """.strip()

        # Показ справки
        dialog = QDialog()
        dialog.setWindowTitle("Справка")
        dialog.setMinimumSize(500, 400)
        dialog.setModal(True)

        dialog_layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(certificate_text)
        text_edit.setReadOnly(True)
        text_edit.setFontPointSize(11)
        dialog_layout.addWidget(text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        dialog_layout.addWidget(buttons)

        dialog.exec()

    def update_styles(self):
        """Обновление стилей при смене темы"""
        self.setStyleSheet(get_main_stylesheet())

        panel = self.findChild(QFrame, "patientsFilterPanel")
        if panel:
            panel.setStyleSheet(self._filter_panel_style())

        # Обновляем все виджеты на странице
        for combo in self.findChildren(QComboBox, "filterCombo"):
            combo.setStyleSheet(self._filter_combo_style())
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

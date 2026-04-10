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
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from models.db_models import User, Patient, Facility, DEPARTMENTS
from ui.styles import get_colors, FONTS, RADIUS, get_main_stylesheet


class PatientsPage(QWidget):
    """Страница пациентов"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.current_filter = ""
        self.type_filter = ""
        self.facility_filter = 0
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

        # Загрузка данных
        self._load_patients()

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

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Поиск по позывному, личному номеру...")
        self.search_input.setFixedWidth(350)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Тип пациента
        self.type_combo = QComboBox()
        self.type_combo.setFrame(False)
        self.type_combo.setObjectName("filterCombo")
        self.type_combo.addItem("Все типы", "")
        self.type_combo.addItem("Взрослые", "adult")
        self.type_combo.addItem("Дети", "child")
        self.type_combo.addItem("Неопределённые", "undefined")
        self.type_combo.setFixedWidth(150)
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.type_combo)

        # Место размещения
        self.facility_combo = QComboBox()
        self.facility_combo.setFrame(False)
        self.facility_combo.addItem("Все места", 0)
        facilities = Facility.get_all()
        for f in facilities:
            self.facility_combo.addItem(f.name, f.id)
        self.facility_combo.setFixedWidth(200)
        self.facility_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.facility_combo)

        # Отделение (для LEAD, NUR)
        if self.user.role == User.ROLE_LEAD:
            dept_label = QLabel(self.user.department_display)
            dept_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(dept_label)

        layout.addStretch()

        # Кнопка добавления (ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            add_btn = QPushButton("Добавить пациента")
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
            add_btn.clicked.connect(self._add_patient)
            layout.addWidget(add_btn)

        # Кнопка справки (ADMIN, REG, LEAD)
        if self.user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            cert_btn = QPushButton("Справка")
            cert_btn.setObjectName("actionButton")
            cert_btn.setFixedHeight(36)
            cert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cert_btn.setStyleSheet(
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
            cert_btn.clicked.connect(self._generate_certificate_selected)
            layout.addWidget(cert_btn)

        # Кнопка сброса
        reset_btn = QPushButton("🔄 Сброс")
        reset_btn.setObjectName("actionButton")
        reset_btn.setFixedHeight(36)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_filters)
        layout.addWidget(reset_btn)

        return panel

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
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
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
                p for p in patients
                if (p.callsign and p.callsign.lower().startswith(search_lower))
                or (p.personal_number and p.personal_number.lower().startswith(search_lower))
                or (p.document_id and p.document_id.lower().startswith(search_lower))
            ]

        for patient in patients:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Позывной
            name_item = QTableWidgetItem(patient.callsign or "")
            name_item.setData(Qt.ItemDataRole.UserRole, patient.id)
            self.table.setItem(row, 0, name_item)

            # Личный номер
            self.table.setItem(
                row, 1, QTableWidgetItem(patient.personal_number or "—")
            )

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
            type_dict = {"adult": "Взрослый", "child": "Детский", "undefined": "Неопределённый"}
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
        self._load_patients()

    def _reset_filters(self):
        """Сброс фильтров"""
        self.search_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.facility_combo.setCurrentIndex(0)
        self.current_filter = ""
        self.type_filter = ""
        self.facility_filter = 0
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

        # Редактировать (REG, LEAD)
        if self.user.role in (User.ROLE_REGISTRAR, User.ROLE_LEAD):
            if (
                self.user.role == User.ROLE_LEAD
                and patient.department != self.user.department
            ):
                pass  # LEAD не может редактировать пациентов другого отделения
            else:
                edit_action = menu.addAction("Редактировать")
                edit_action.triggered.connect(lambda: self._edit_patient(patient_id))

        # Скрыть/Восстановить (только REG)
        if self.user.role == User.ROLE_REGISTRAR:
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
        selected = self.table.selectedItems()
        if not selected:
            return None
        return selected[0].data(Qt.ItemDataRole.UserRole)

    def _open_patient(self, index):
        """Открытие пациента (двойной клик)"""
        patient_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self._open_patient_by_id(patient_id)

    def _open_patient_by_id(self, patient_id: int):
        """Открытие карточки пациента"""
        from ui.patient_detail import PatientDetailDialog

        dialog = PatientDetailDialog(self.user, patient_id)
        dialog.exec()
        self._load_patients()  # Обновить данные

    def _add_patient(self):
        """Добавление пациента"""
        from ui.patient_form import PatientFormDialog

        dialog = PatientFormDialog(self.user, None)
        if dialog.exec():
            self._load_patients()

    def _edit_patient(self, patient_id: int):
        """Редактирование пациента"""
        from ui.patient_form import PatientFormDialog

        patient = Patient.get_by_id(patient_id)
        dialog = PatientFormDialog(self.user, patient)
        if dialog.exec():
            self._load_patients()

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
            self._load_patients()

    def _restore_patient(self, patient_id: int):
        """Восстановление пациента"""
        patient = Patient.get_by_id(patient_id)
        patient.restore()
        self._load_patients()

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

        # Обновляем все виджеты на странице
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

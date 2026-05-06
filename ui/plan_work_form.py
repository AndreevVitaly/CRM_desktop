"""
Форма создания/редактирования реквизитов документа-плана.
Пункты плана редактируются отдельно, не в этом окне.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QMessageBox,
    QGroupBox,
    QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt, QDate

from models.db_models import User, Patient, Document, DOCUMENT_TYPE_PLAN
from ui.styles import get_colors, RADIUS


class PlanWorkFormDialog(QDialog):
    """Окно редактирования реквизитов документа-плана."""

    def __init__(self, user: User, patient: Patient, document: Document = None):
        super().__init__()
        self.user = user
        self.patient = patient
        self.document = document
        self.is_edit = document is not None and document.id is not None

        title = "Редактирование плана работы" if self.is_edit else "Новый план работы"
        self.setWindowTitle(title)
        self.setMinimumSize(800, 700)
        self._init_ui()

    def _init_ui(self):
        colors = get_colors()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.Box)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 0, 0)

        doc_group = QGroupBox("Информация о плане")
        doc_group.setStyleSheet(self._get_group_style(colors))

        doc_layout = QFormLayout()
        doc_layout.setSpacing(12)
        doc_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        doc_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.doc_date_input = QDateEdit()
        self.doc_date_input.setCalendarPopup(True)
        self.doc_date_input.setDate(QDate.currentDate())
        self.doc_date_input.setDisplayFormat("dd.MM.yyyy")
        self.doc_date_input.setMinimumHeight(36)
        doc_layout.addRow("Дата плана*", self.doc_date_input)

        self.doc_number_input = QLineEdit()
        self.doc_number_input.setPlaceholderText("Номер плана")
        self.doc_number_input.setMinimumHeight(36)
        doc_layout.addRow("№ плана", self.doc_number_input)

        self.summary_input = QTextEdit()
        self.summary_input.setPlaceholderText("Общее описание плана работы")
        self.summary_input.setMinimumHeight(120)
        doc_layout.addRow("Описание*", self.summary_input)

        self._apply_form_styles(colors)

        doc_group.setLayout(doc_layout)
        content_layout.addWidget(doc_group)
        content_layout.addStretch()

        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("secondaryBtn")
        save_btn.setFixedHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(self._get_dialog_button_style(colors))
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(self._get_dialog_button_style(colors))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self.setStyleSheet(
            f"""
            background-color: {colors['bg']};
            color: {colors['text']};
            QLabel {{
                font-size: 9pt;
            }}
            QDateEdit, QLineEdit, QTextEdit {{
                font-size: 9pt;
            }}
            """
        )

        if self.is_edit:
            self._fill_data()

    def _get_group_style(self, colors) -> str:
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """

    def _apply_form_styles(self, colors):
        input_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 10px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """
        text_edit_style = f"""
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
            padding: 8px 10px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['surface']};
        """
        self.doc_date_input.setStyleSheet(input_style)
        self.doc_number_input.setStyleSheet(input_style)
        self.summary_input.setStyleSheet(text_edit_style)

    def _get_dialog_button_style(self, colors) -> str:
        return f"""
            QPushButton#secondaryBtn {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 8px 18px;
                font-weight: 600;
                color: {colors['text']};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {colors['surface_muted']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#secondaryBtn:pressed {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
                color: #FFFFFF;
            }}
        """

    def _fill_data(self):
        if not self.document:
            return

        if self.document.doc_date:
            self.doc_date_input.setDate(
                QDate(
                    self.document.doc_date.year,
                    self.document.doc_date.month,
                    self.document.doc_date.day,
                )
            )

        self.doc_number_input.setText(str(self.document.doc_number or ""))
        self.summary_input.setPlainText(self.document.summary or "")

    def _save(self):
        summary = self.summary_input.toPlainText().strip()
        if not summary:
            QMessageBox.warning(self, "Ошибка", "Введите описание плана")
            return

        if not self.document:
            self.document = Document()
            self.document.patient_id = self.patient.id
            self.document.doc_type = DOCUMENT_TYPE_PLAN
            self.document.author_id = self.user.id

        self.document.doc_date = self.doc_date_input.date().toPyDate()
        self.document.doc_number = self.doc_number_input.text().strip() or None
        self.document.summary = summary
        self.document.classification = "NS"
        self.document.patient_personal_number = self.patient.personal_number or ""
        self.document.save()

        QMessageBox.information(self, "Успешно", "План работы сохранён")
        self.accept()

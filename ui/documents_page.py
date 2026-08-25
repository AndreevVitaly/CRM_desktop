"""
Страница общего реестра документов
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
    QMessageBox,
    QDialog,
    QFormLayout,
    QScrollArea,
)
from PyQt6.QtCore import Qt

from models.db_models import User, Document, DOCUMENT_TYPE_PLAN, DOCUMENT_TYPE_MEETING
from ui.styles import get_colors, RADIUS, FONTS, get_main_stylesheet


class DocumentsPage(QWidget):
    """Единый реестр документов по всем категориям АА"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.filtered_documents = []
        self._init_ui()

    def _init_ui(self):
        colors = get_colors()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        filter_panel = self._create_filter_panel()
        layout.addWidget(filter_panel)

        self.table = self._create_table()
        layout.addWidget(self.table, 1)

        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        layout.addWidget(self.count_label)

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        self._load_documents()

    def _create_filter_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("documentsFilterPanel")
        panel.setFixedHeight(80)
        panel.setStyleSheet(self._filter_panel_style())

        layout = QHBoxLayout(panel)
        layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(
            "Поиск по категории АА, номеру документа, типу, содержанию, месту приобщения..."
        )
        self.search_input.setFixedWidth(520)
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._load_documents)
        layout.addWidget(self.search_input)

        layout.addStretch()

        if self.user.role != User.ROLE_NURSE:
            add_btn = QPushButton("Новый документ")
            add_btn.setObjectName("filterButton")
            add_btn.setFixedHeight(34)
            add_btn.setMinimumWidth(122)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet(self._filter_button_style())
            add_btn.clicked.connect(self._add_document)
            layout.addWidget(add_btn)

            edit_btn = QPushButton("Редактировать")
            edit_btn.setObjectName("filterButton")
            edit_btn.setFixedHeight(34)
            edit_btn.setMinimumWidth(118)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet(self._filter_button_style())
            edit_btn.clicked.connect(self._edit_selected_document)
            layout.addWidget(edit_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setObjectName("filterButton")
        refresh_btn.setFixedHeight(34)
        refresh_btn.setMinimumWidth(92)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(self._filter_button_style())
        refresh_btn.clicked.connect(self._load_documents)
        layout.addWidget(refresh_btn)

        return panel

    def _filter_panel_style(self) -> str:
        colors = get_colors()
        return f"""
            QFrame#documentsFilterPanel {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 12px;
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
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels(
            [
                "ID",
                "Категория АА",
                "Личный номер",
                "№ док.",
                "Признак",
                "Гриф",
                "Дата",
                "Вид документа",
                "Краткое содержание",
                "Куда приобщён",
                "Автор",
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
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        if self.user.role == User.ROLE_NURSE:
            table.doubleClicked.connect(lambda *_: self._open_selected_document())
        else:
            table.doubleClicked.connect(lambda *_: self._edit_selected_document())

        return table

    def _load_documents(self):
        self.table.setRowCount(0)

        documents = Document.get_all(self.user)
        search_text = self.search_input.text().strip().lower()

        self.filtered_documents = []
        for doc in documents:
            patient = doc.patient
            author = doc.author
            group = doc.group

            search_blob = " ".join(
                str(part or "")
                for part in [
                    doc.id,
                    patient.callsign if patient else "",
                    patient.personal_number if patient else "",
                    doc.patient_personal_number,
                    doc.doc_number,
                    group.name if group else "",
                    group.category_display if group else "",
                    doc.classification_display,
                    self._get_doc_type_display(doc),
                    doc.summary,
                    doc.location,
                    author.full_name if author else "",
                ]
            ).lower()

            if search_text and search_text not in search_blob:
                continue

            self.filtered_documents.append(doc)

        for row, doc in enumerate(self.filtered_documents):
            patient = doc.patient
            author = doc.author
            group = doc.group

            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(doc.id))
            id_item.setData(Qt.ItemDataRole.UserRole, doc.id)
            self.table.setItem(row, 0, id_item)
            self.table.setItem(
                row, 1, QTableWidgetItem(patient.callsign if patient else "—")
            )
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    (patient.personal_number if patient else "")
                    or doc.patient_personal_number
                    or "—"
                ),
            )
            self.table.setItem(row, 3, QTableWidgetItem(doc.doc_number or "—"))
            self.table.setItem(row, 4, QTableWidgetItem(group.name if group else "—"))
            self.table.setItem(row, 5, QTableWidgetItem(doc.classification_display))
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(
                    doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"
                ),
            )
            self.table.setItem(row, 7, QTableWidgetItem(self._get_doc_type_display(doc)))
            self.table.setItem(row, 8, QTableWidgetItem(doc.summary or "—"))
            self.table.setItem(row, 9, QTableWidgetItem(doc.location or "—"))
            self.table.setItem(
                row, 10, QTableWidgetItem(author.full_name if author else "—")
            )

        self.count_label.setText(f"Документов найдено: {len(self.filtered_documents)}")

    def _get_doc_type_display(self, doc: Document) -> str:
        if doc.doc_type == DOCUMENT_TYPE_PLAN:
            return "План работы с категорией АА"
        if doc.doc_type == DOCUMENT_TYPE_MEETING:
            return "Встреча"
        return doc.doc_type or "—"

    def _get_selected_document(self):
        selected = self.table.selectedItems()
        if not selected:
            return None

        row = selected[0].row()
        if row < 0 or row >= len(self.filtered_documents):
            return None

        return self.filtered_documents[row]

    def _add_document(self):
        if self.user.role == User.ROLE_NURSE:
            return

        from ui.document_form import DocumentFormDialog

        dialog = DocumentFormDialog(
            self.user,
            None,
            None,
            allow_patient_select=True,
        )
        if dialog.exec():
            self._load_documents()

    def _edit_selected_document(self):
        if self.user.role == User.ROLE_NURSE:
            self._open_selected_document()
            return

        doc = self._get_selected_document()
        if not doc:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите документ в таблице"
            )
            return

        from ui.document_form import DocumentFormDialog

        dialog = DocumentFormDialog(
            self.user,
            doc.patient,
            doc,
            allow_patient_select=True,
        )

        if dialog.exec():
            self._load_documents()

    def _open_selected_document(self):
        doc = self._get_selected_document()
        if not doc:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите документ в таблице"
            )
            return

        self._open_document_dialog(doc)

    def _open_document_dialog(self, doc: Document):
        patient = doc.patient
        author = doc.author
        group = doc.group

        dialog = QDialog(self)
        doc_title_number = doc.doc_number or f"ID {doc.id}"
        dialog.setWindowTitle(f"Документ №{doc_title_number}")
        dialog.resize(700, 520)
        dialog.setMinimumSize(600, 420)

        colors = get_colors()
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"Документ №{doc_title_number}")
        layout.addWidget(title)

        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors['surface_muted']};
                border-radius: {RADIUS['md']}px;
                padding: 12px;
            }}
        """
        )
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(4)
        info_layout.setHorizontalSpacing(12)
        info_layout.setVerticalSpacing(4)
        info_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )

        current_patient_number = (
            (patient.personal_number if patient else "")
            or doc.patient_personal_number
            or "—"
        )

        fields = [
            ("Категория АА:", patient.callsign if patient else "—"),
            ("Признак:", group.name if group else "—"),
            ("Номер документа:", str(doc.doc_number) if doc.doc_number else "—"),
            ("Гриф секретности:", doc.classification_display),
            ("Дата:", doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"),
            ("Автор:", author.full_name if author else "—"),
            ("Вид документа:", self._get_doc_type_display(doc)),
            ("Краткое содержание:", doc.summary or "—"),
            ("Куда приобщён:", doc.location or "—"),
            ("Личный номер категории АА:", current_patient_number),
        ]

        for label, value in fields:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            val = QLabel(value)
            val.setWordWrap(True)
            val.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addRow(lbl, val)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setWidget(info_frame)
        layout.addWidget(scroll, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("actionButton")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.exec()

    def update_styles(self):
        colors = get_colors()
        self.setStyleSheet(get_main_stylesheet())
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        panel = self.findChild(QFrame, "documentsFilterPanel")
        if panel:
            panel.setStyleSheet(self._filter_panel_style())
        for button in self.findChildren(QPushButton, "filterButton"):
            button.setStyleSheet(self._filter_button_style())

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
)
from PyQt6.QtCore import Qt

from models.db_models import User, Document, DOCUMENT_TYPE_PLAN, DOCUMENT_TYPE_MEETING
from ui.styles import get_colors, RADIUS, get_main_stylesheet


class DocumentsPage(QWidget):
    """Единый реестр документов по всем пациентам"""

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

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(
            "Поиск по пациенту, номеру документа, типу, содержанию, месту приобщения..."
        )
        self.search_input.setFixedWidth(520)
        self.search_input.textChanged.connect(self._load_documents)
        layout.addWidget(self.search_input)

        layout.addStretch()

        edit_btn = QPushButton("Редактировать")
        edit_btn.setObjectName("actionButton")
        edit_btn.setFixedHeight(36)
        edit_btn.clicked.connect(self._edit_selected_document)
        layout.addWidget(edit_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setObjectName("actionButton")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self._load_documents)
        layout.addWidget(refresh_btn)

        return panel

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels(
            [
                "ID",
                "Пациент",
                "Личный номер",
                "№ док.",
                "Гриф",
                "Дата",
                "Вид документа",
                "Краткое содержание",
                "Куда приобщён",
                "Автор",
                "Связанная встреча",
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
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
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
            encounter = doc.encounter

            search_blob = " ".join(
                [
                    str(doc.id or ""),
                    patient.callsign if patient else "",
                    patient.personal_number if patient else "",
                    doc.patient_personal_number or "",
                    doc.doc_number or "",
                    doc.classification_display or "",
                    self._get_doc_type_display(doc),
                    doc.summary or "",
                    doc.location or "",
                    author.full_name if author else "",
                    encounter.started_at.strftime("%d.%m.%Y %H:%M")
                    if encounter and encounter.started_at
                    else "",
                ]
            ).lower()

            if search_text and search_text not in search_blob:
                continue

            self.filtered_documents.append(doc)

        for row, doc in enumerate(self.filtered_documents):
            patient = doc.patient
            author = doc.author
            encounter = doc.encounter

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
            self.table.setItem(row, 4, QTableWidgetItem(doc.classification_display))
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(
                    doc.doc_date.strftime("%d.%m.%Y") if doc.doc_date else "—"
                ),
            )
            self.table.setItem(row, 6, QTableWidgetItem(self._get_doc_type_display(doc)))
            self.table.setItem(row, 7, QTableWidgetItem(doc.summary or "—"))
            self.table.setItem(row, 8, QTableWidgetItem(doc.location or "—"))
            self.table.setItem(
                row, 9, QTableWidgetItem(author.full_name if author else "—")
            )
            self.table.setItem(
                row,
                10,
                QTableWidgetItem(self._get_encounter_display(encounter)),
            )

        self.count_label.setText(f"Документов найдено: {len(self.filtered_documents)}")

    def _get_doc_type_display(self, doc: Document) -> str:
        if doc.doc_type == DOCUMENT_TYPE_PLAN:
            return "План работы с пациентом"
        if doc.doc_type == DOCUMENT_TYPE_MEETING:
            return "Встреча"
        return doc.doc_type or "—"

    def _get_encounter_display(self, encounter) -> str:
        if not encounter or not encounter.started_at:
            return "—"
        doctor_name = encounter.doctor.full_name if encounter.doctor else "без врача"
        return f"{encounter.started_at.strftime('%d.%m.%Y %H:%M')} | {doctor_name}"

    def _get_selected_document(self):
        selected = self.table.selectedItems()
        if not selected:
            return None

        row = selected[0].row()
        if row < 0 or row >= len(self.filtered_documents):
            return None

        return self.filtered_documents[row]

    def _edit_selected_document(self):
        doc = self._get_selected_document()
        if not doc:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите документ в таблице"
            )
            return

        patient = doc.patient
        if not patient:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не удалось открыть документ: пациент, связанный с документом, не найден",
            )
            return

        if doc.doc_type == DOCUMENT_TYPE_PLAN:
            from ui.plan_work_form import PlanWorkFormDialog

            dialog = PlanWorkFormDialog(self.user, patient, doc)
        else:
            from ui.document_form import DocumentFormDialog

            dialog = DocumentFormDialog(self.user, patient, doc)

        if dialog.exec():
            self._load_documents()

    def update_styles(self):
        colors = get_colors()
        self.setStyleSheet(get_main_stylesheet())
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

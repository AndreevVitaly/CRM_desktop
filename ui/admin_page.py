from __future__ import annotations

import shutil
import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from models.db_models import User, db
from ui.styles import FONTS, RADIUS, get_colors, scaled
from utils.app_paths import get_db_path
from utils.db_encryption import (
    has_sqlite_header,
    is_sqlcipher_available,
    rekey_open_database,
)
from utils.sync_exchange import get_import_logs


class AdminPage(QWidget):
    def __init__(self, user: User, on_export=None, on_import=None):
        super().__init__()
        self.user = user
        self.on_export = on_export
        self.on_import = on_import
        self._init_ui()

    def _init_ui(self):
        colors = get_colors()
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(scaled(20), scaled(20), scaled(20), scaled(20))
        layout.setSpacing(scaled(16))

        title = QLabel("Администрирование")
        title.setStyleSheet(
            f"font-size: {FONTS['size_header']}pt; font-weight: 700; color: {colors['text']};"
        )
        layout.addWidget(title)

        layout.addWidget(self._create_database_card())
        layout.addWidget(self._create_exchange_card())
        layout.addWidget(self._create_import_log_card(), 1)
        layout.addStretch()

        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        colors = get_colors()
        card = QFrame()
        card.setObjectName("adminCard")
        card.setStyleSheet(
            f"""
            QFrame#adminCard {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(scaled(16), scaled(14), scaled(16), scaled(16))
        layout.setSpacing(scaled(12))

        label = QLabel(title)
        label.setStyleSheet(
            f"font-size: {FONTS['size_large']}pt; font-weight: 700; color: {colors['text']};"
        )
        layout.addWidget(label)
        return card, layout

    def _button(self, text: str) -> QPushButton:
        colors = get_colors()
        btn = QPushButton(text)
        btn.setFixedHeight(scaled(28, 24))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['sm']}px;
                padding: {scaled(3)}px {scaled(10)}px;
                font-weight: 600;
                font-size: {FONTS['size_xs']}pt;
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['accent_light']};
                border: 1px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton:pressed {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                color: #FFFFFF;
            }}
            """
        )
        return btn

    def _create_database_card(self) -> QFrame:
        card, layout = self._card("База данных")
        card.setMinimumHeight(scaled(136, 116))
        colors = get_colors()
        db_path = get_db_path()
        encrypted = db_path.exists() and not has_sqlite_header(db_path)
        status = "зашифрована" if encrypted else "обычная SQLite"

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(scaled(16))
        grid.setVerticalSpacing(scaled(8))
        rows = [
            ("Статус", status),
            (
                "SQLCipher",
                "доступен" if is_sqlcipher_available() else "не установлен",
            ),
            ("Путь", str(db_path)),
        ]
        for row, (name, value) in enumerate(rows):
            grid.setRowMinimumHeight(row, scaled(22, 18))

            name_label = QLabel(name)
            name_label.setFixedWidth(scaled(110, 92))
            name_label.setMinimumHeight(scaled(22, 18))
            name_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            name_label.setStyleSheet(
                f"color: {colors['text_muted']}; font-size: {FONTS['size_small']}pt; font-weight: 600; background-color: transparent;"
            )

            value_label = QLabel(str(value))
            value_label.setMinimumHeight(scaled(22, 18))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            value_label.setStyleSheet(
                f"color: {colors['text']}; font-size: {FONTS['size_medium']}pt; font-weight: 500; background-color: transparent;"
            )

            grid.addWidget(name_label, row, 0)
            grid.addWidget(value_label, row, 1)
        layout.addLayout(grid)
        layout.addSpacing(scaled(6))

        actions = QHBoxLayout()
        backup_btn = self._button("Создать резервную копию")
        backup_btn.clicked.connect(self._backup_database)
        actions.addWidget(backup_btn)

        rekey_btn = self._button("Сменить пароль БД")
        rekey_btn.clicked.connect(self._change_database_password)
        actions.addWidget(rekey_btn)
        actions.addStretch()
        layout.addLayout(actions)
        return card

    def _create_import_log_card(self) -> QFrame:
        card, layout = self._card("Журнал импортов")

        actions = QHBoxLayout()
        refresh_btn = self._button("Обновить")
        refresh_btn.clicked.connect(self._load_import_logs)
        actions.addWidget(refresh_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.import_log_table = QTableWidget()
        self.import_log_table.setColumnCount(8)
        self.import_log_table.setHorizontalHeaderLabels(
            [
                "Дата",
                "Импортировал",
                "Автор пакета",
                "Роль",
                "Польз./места",
                "Пациенты",
                "Документы/встречи/планы/КМ",
                "Файл",
            ]
        )
        self.import_log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.import_log_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.import_log_table.verticalHeader().setVisible(False)
        header = self.import_log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.import_log_table)

        self._load_import_logs()
        return card

    def _load_import_logs(self):
        if not hasattr(self, "import_log_table"):
            return
        self.import_log_table.setRowCount(0)
        for log in get_import_logs(30):
            summary = {}
            try:
                summary = json.loads(log.get("summary_json") or "{}")
            except json.JSONDecodeError:
                pass
            details = summary.get("details", {})
            users = details.get("users", {})
            facilities = details.get("facilities", {})
            patients = details.get("patients", {})
            documents = details.get("documents", {})
            encounters = details.get("encounters", {})
            plans = details.get("treatment_plan_items", {})
            km_records = details.get("km_records", {})

            row = self.import_log_table.rowCount()
            self.import_log_table.insertRow(row)
            values = [
                log.get("imported_at", ""),
                log.get("imported_by_username", "") or "",
                log.get("package_author", "") or "",
                log.get("package_role", "") or "",
                (
                    f"П: {self._summary_short(users)}; "
                    f"М: {self._summary_short(facilities)}"
                ),
                self._summary_short(patients),
                (
                    f"Д: {self._summary_short(documents)}; "
                    f"В: {self._summary_short(encounters)}; "
                    f"П: {self._summary_short(plans)}; "
                    f"КМ: {self._summary_short(km_records)}"
                ),
                log.get("package_path", "") or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.import_log_table.setItem(row, col, item)

    def _summary_short(self, item: dict) -> str:
        return f"+{item.get('new', 0)} / ~{item.get('updated', 0)}"

    def _create_exchange_card(self) -> QFrame:
        card, layout = self._card("Обмен данными")
        colors = get_colors()
        note = QLabel(
            "Экспорт создает защищенный пакет. Импорт сейчас применяет только пациентов после подтверждения."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {colors['text_muted']};")
        layout.addWidget(note)

        actions = QHBoxLayout()
        export_btn = self._button("Экспорт")
        export_btn.setEnabled(self.on_export is not None)
        if self.on_export:
            export_btn.clicked.connect(self.on_export)
        actions.addWidget(export_btn)

        import_btn = self._button("Импорт")
        import_btn.setEnabled(self.on_import is not None)
        if self.on_import:
            import_btn.clicked.connect(self.on_import)
        actions.addWidget(import_btn)
        actions.addStretch()
        layout.addLayout(actions)
        return card

    def _backup_database(self):
        source = get_db_path()
        if not source.exists():
            QMessageBox.warning(self, "Резервная копия", "Файл базы данных не найден")
            return

        default_name = f"medcrm_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Создать резервную копию",
            default_name,
            "SQLite DB (*.db)",
        )
        if not file_path:
            return

        try:
            shutil.copy2(source, Path(file_path))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка резервной копии", str(exc))
            return
        QMessageBox.information(self, "Резервная копия", "Резервная копия создана")

    def _change_database_password(self):
        current_password, ok = QInputDialog.getText(
            self,
            "Смена пароля БД",
            "Введите текущий пароль базы:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return

        new_password, ok = QInputDialog.getText(
            self,
            "Смена пароля БД",
            "Введите новый пароль базы:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return

        repeat_password, ok = QInputDialog.getText(
            self,
            "Смена пароля БД",
            "Повторите новый пароль:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if new_password != repeat_password:
            QMessageBox.warning(self, "Смена пароля БД", "Новые пароли не совпадают")
            return

        try:
            rekey_open_database(db, current_password, new_password)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка смены пароля БД", str(exc))
            return

        QMessageBox.information(
            self,
            "Смена пароля БД",
            "Пароль базы данных изменен. При следующем запуске используйте новый пароль.",
        )

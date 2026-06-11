"""
Главное окно приложения
"""

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMenu,
    QToolButton,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    pyqtProperty,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
)
from PyQt6.QtGui import QAction, QFont, QPainter, QColor, QBrush, QPixmap, QPainterPath
import os

from models.db_models import User
from ui.brand_title import BrandTitleLabel
from ui.native_window_theme import apply_native_theme_to_app, apply_native_window_theme
from ui.styles import FONTS, RADIUS, get_colors, get_main_stylesheet, scaled
from utils.app_paths import get_resource_path


class ThemeSwitch(QWidget):
    """Переключатель темы (toggle switch) - современный дизайн"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(scaled(52, 44), scaled(28, 24))
        self.current_theme_light = True
        self._offset = 0
        self.animation = QPropertyAnimation(self, b"offset")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @pyqtProperty(float)
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value
        self.update()

    def set_theme(self, is_light: bool):
        """Установить тему"""
        self.current_theme_light = is_light
        target = 0 if is_light else max(0, self.width() - scaled(28, 24))
        self.animation.setStartValue(self._offset)
        self.animation.setEndValue(target)
        self.animation.start()

    def toggle(self):
        """Переключить тему"""
        self.current_theme_light = not self.current_theme_light
        target = 0 if self.current_theme_light else max(0, self.width() - scaled(28, 24))
        self.animation.setStartValue(self._offset)
        self.animation.setEndValue(target)
        self.animation.start()

    def mousePressEvent(self, event):
        """Обработка клика"""
        self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_y = self.height() // 2
        radius = max(8, (self.height() - 6) // 2)
        left_x = center_y
        right_x = self.width() - center_y

        # Фон переключателя
        bg_color = QColor("#E2E8F0" if self.current_theme_light else "#334155")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, center_y, center_y)

        # Тень под кружком
        shadow_color = QColor(0, 0, 0, 40 if self.current_theme_light else 80)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(QPoint(int(left_x + self._offset), center_y), radius + 1, radius + 1)

        # Кружок переключателя
        dot_color = QColor("#FFFFFF")
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(QPoint(int(left_x + self._offset), center_y), radius, radius)


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    theme_toggled = pyqtSignal(bool)  # Сигнал при переключении темы

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.current_theme_light = True

        self.setWindowTitle(f"PULSAR - {user.full_name}")
        self._apply_adaptive_minimum_size()
        self.setStyleSheet(get_main_stylesheet())

        self._init_ui()

    def _apply_adaptive_minimum_size(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            self.setMinimumSize(scaled(1200), scaled(800))
            return
        geometry = screen.availableGeometry()
        width = min(scaled(1200), int(geometry.width() * 0.92))
        height = min(scaled(800), int(geometry.height() * 0.9))
        self.setMinimumSize(max(900, width), max(620, height))

    def _update_logo(self, logo_path: str, colors: dict):
        """Обновление логотипа (PNG) со скруглёнными углами"""
        if not logo_path or not os.path.exists(logo_path):
            return
        try:
            pixmap = QPixmap(logo_path)
            if pixmap.isNull():
                return

            max_logo_size = scaled(78, 56)
            pixmap = pixmap.scaled(
                max_logo_size,
                max_logo_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            w, h = pixmap.width(), pixmap.height()
            rounded = QPixmap(w, h)
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            radius = 14
            path_mask = QPainterPath()
            path_mask.addRoundedRect(0, 0, w, h, radius, radius)
            painter.setClipPath(path_mask)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            self.logo_label.setPixmap(rounded)
            self.logo_label.setFixedSize(rounded.size())
            self.logo_label.update()
        except Exception:
            pass

    def _get_logo_path(self) -> str:
        """Путь к логотипу"""
        path = str(get_resource_path("assets", "logo_light.png"))
        if os.path.exists(path):
            return path
        return ""

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout - вертикальный
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя панель (навигация + заголовок + тема + выход)
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Основная область контента
        content_area = QWidget()
        content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Область страниц
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )
        content_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(content_area, 1)  # Stretch factor 1

    def _get_nav_items(self) -> dict:
        """Получение элементов навигации для текущей роли"""
        user = self.user

        # Базовые элементы для всех
        items = {
            "dashboard": ("Главный экран", True),
        }

        # Пациенты
        if user.role in (
            User.ROLE_ADMIN,
            User.ROLE_REGISTRAR,
            User.ROLE_LEAD,
            User.ROLE_DOCTOR,
        ):
            items["patients"] = ("Пациенты", True)
            items["meeting_schedule"] = ("График встреч", True)
            items["encounters"] = ("Встречи", True)

        # Пользователи
        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            items["users"] = ("Пользователи", True)

        # Планирование
        items["planning"] = ("Планирование", True)

        # КМ (Комиссионные Мероприятия)
        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            items["km"] = ("КМ", True)

        # Статистика
        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            items["stats"] = ("Статистика", True)
            items["documents"] = ("Документы", True)

        if user.role == User.ROLE_DOCTOR:
            items["km"] = ("КМ", True)
            items["stats"] = ("Статистика", True)

        if user.role in (User.ROLE_DOCTOR, User.ROLE_NURSE):
            items["documents"] = ("Документы", True)

        if user.role == User.ROLE_ADMIN:
            items["admin"] = ("Администрирование", True)

        return items

    def _create_nav_button(self, text: str, nav_id: str, enabled: bool) -> QPushButton:
        """Создание кнопки навигации"""
        colors = get_colors()

        btn = QPushButton(text)
        btn.setObjectName("navButton")
        btn.setFixedHeight(scaled(34, 28))
        btn.setMinimumWidth(scaled(112, 92))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"""
            QPushButton#navButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: {RADIUS['md']}px;
                padding: 5px 14px;
                font-size: {FONTS['size_xs']}pt;
                font-weight: 600;
                color: {colors['text']};
            }}
            QPushButton#navButton:hover {{
                background-color: {colors['surface_muted']};
                border: 1px solid {colors['line']};
                color: {colors['accent']};
            }}
            QPushButton#navButton[active="true"] {{
                background-color: transparent;
                border: 1px solid transparent;
                color: {colors['text']};
                font-weight: 600;
            }}
            QPushButton#navButton:pressed {{
                background-color: #3B82F6;
                border: 1px solid #3B82F6;
                color: #FFFFFF;
            }}
            QPushButton#navButton:disabled {{
                background-color: transparent;
                border: 1px solid {colors['line']};
                color: {colors['text_muted']};
            }}
        """
        )

        if not enabled:
            btn.setEnabled(False)

        btn.clicked.connect(lambda: self._navigate(nav_id))
        btn.setProperty("nav_id", nav_id)

        return btn

    def _get_navigation_menu_style(self) -> str:
        colors = get_colors()
        return f"""
            QToolButton#navigationMenuButton {{
                background-color: transparent;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 6px 14px;
                font-size: {FONTS['size_medium']}pt;
                font-weight: 600;
                color: {colors['text']};
            }}
            QToolButton#navigationMenuButton:hover {{
                background-color: {colors['surface_muted']};
                border: 1px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QToolButton#navigationMenuButton::menu-indicator {{
                image: none;
            }}
            QMenu {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 6px;
                color: {colors['text']};
            }}
            QMenu::item {{
                padding: 8px 28px 8px 14px;
                border-radius: {RADIUS['sm']}px;
                font-size: {FONTS['size_medium']}pt;
            }}
            QMenu::item:selected {{
                background-color: {colors['accent_light']};
                color: {colors['accent_strong']};
            }}
            QMenu::item:disabled {{
                color: {colors['text_muted']};
            }}
        """

    def _create_navigation_menu(self) -> QToolButton:
        button = QToolButton()
        button.setObjectName("navigationMenuButton")
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(scaled(34, 28))
        button.setMinimumWidth(scaled(190, 150))
        button.setStyleSheet(self._get_navigation_menu_style())

        self.nav_menu = QMenu(button)
        self.nav_menu.setStyleSheet(self._get_navigation_menu_style())
        button.setMenu(self.nav_menu)
        self.nav_menu_button = button
        self.nav_actions = {}
        self._rebuild_navigation_menu()
        return button

    def _rebuild_navigation_menu(self):
        if not hasattr(self, "nav_menu"):
            return
        self.nav_menu.clear()
        self.nav_actions = {}
        for nav_id, (text, enabled) in self._get_nav_items().items():
            action = QAction(text, self)
            action.setCheckable(True)
            action.setEnabled(enabled)
            action.triggered.connect(
                lambda checked=False, page_id=nav_id: self._navigate(page_id)
            )
            self.nav_menu.addAction(action)
            self.nav_actions[nav_id] = action
        self._set_active_navigation(getattr(self, "current_page_id", "dashboard"))

    def _set_active_navigation(self, page_id: str):
        self.current_page_id = page_id
        nav_items = self._get_nav_items()
        current_text = nav_items.get(page_id, ("Разделы", True))[0]
        if hasattr(self, "nav_menu_button"):
            self.nav_menu_button.setText(current_text)
        if hasattr(self, "nav_actions"):
            for nav_id, action in self.nav_actions.items():
                action.setChecked(nav_id == page_id)

    def _get_sync_button_style(self) -> str:
        colors = get_colors()
        return f"""
            QPushButton#syncButton {{
                background-color: transparent;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 0px 14px;
                min-height: 0px;
                max-height: {scaled(34, 28)}px;
                font-size: {FONTS['size_medium']}pt;
                font-weight: 600;
                color: {colors['text']};
            }}
            QPushButton#syncButton:hover {{
                background-color: {colors['accent_light']};
                border: 1px solid {colors['accent']};
                color: {colors['accent_strong']};
            }}
            QPushButton#syncButton:pressed {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                color: #FFFFFF;
            }}
            QPushButton#syncButton:disabled {{
                background-color: transparent;
                border: 1px solid {colors['line']};
                color: {colors['text_muted']};
            }}
        """

    def _create_sync_button(self, text: str, enabled: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("syncButton")
        btn.setFixedHeight(scaled(34, 28))
        btn.setMinimumWidth(scaled(190, 150))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._get_sync_button_style())
        btn.setEnabled(enabled)
        return btn

    def _create_top_bar(self) -> QFrame:
        """Создание верхней панели"""
        colors = get_colors()

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(scaled(108, 88))
        top_bar.setStyleSheet(
            f"""
            QFrame#topBar {{
                background-color: {colors['nav_bg']};
                border-bottom: 1px solid {colors['line']};
            }}
        """
        )

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(scaled(16), scaled(10), scaled(16), scaled(10))
        layout.setSpacing(scaled(16))

        # Логотип и название слева
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(scaled(12))

        # Логотип
        logo_path = self._get_logo_path()
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setProperty("logoLabel", True)
        self._update_logo(logo_path, colors)
        logo_layout.addWidget(self.logo_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = BrandTitleLabel("PULSAR")
        title_label.setObjectName("title")
        title_layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Фундамент стабильной работы")
        subtitle_label.setObjectName("muted")
        subtitle_label.setStyleSheet(
            f"font-size: {FONTS['size_xs']}pt; color: {colors['text_muted']};"
        )
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()

        logo_layout.addLayout(title_layout)

        layout.addLayout(logo_layout)

        layout.addSpacing(scaled(20))

        self.nav_buttons = {}
        self.current_page_id = "dashboard"
        layout.addStretch()
        layout.addWidget(self._create_navigation_menu())

        can_export = self.user.role in (
            User.ROLE_ADMIN,
            User.ROLE_REGISTRAR,
            User.ROLE_LEAD,
            User.ROLE_DOCTOR,
        )
        can_import = self.user.role in (
            User.ROLE_ADMIN,
            User.ROLE_REGISTRAR,
            User.ROLE_LEAD,
        )

        self.export_btn = self._create_sync_button("Экспорт", can_export)
        self.export_btn.setToolTip("Выгрузить пакет данных для объединения")
        self.export_btn.clicked.connect(self._export_data)
        layout.addWidget(self.export_btn)

        self.import_btn = self._create_sync_button("Импорт", can_import)
        self.import_btn.setToolTip("Загрузить пакет данных от другого пользователя")
        self.import_btn.clicked.connect(self._import_data)
        layout.addWidget(self.import_btn)

        layout.addSpacing(scaled(12))

        # Переключатель темы (toggle switch)
        self.theme_switch = ThemeSwitch(self)
        self.theme_switch.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_switch)

        layout.addSpacing(scaled(16))

        # Кнопка выхода в общем стиле
        logout_btn = QPushButton("Выход")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedSize(scaled(190, 150), scaled(34, 28))
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet(
            f"""
            QPushButton#logoutBtn {{
                background-color: transparent;
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 0px 14px;
                min-height: 0px;
                min-width: {scaled(190, 150)}px;
                max-width: {scaled(190, 150)}px;
                max-height: {scaled(34, 28)}px;
                font-weight: 600;
                font-size: {FONTS['size_medium']}pt;
                color: {colors['text_muted']};
            }}
            QPushButton#logoutBtn:hover {{
                background-color: {colors['danger_bg']};
                border: 1px solid {colors['danger']};
                color: {colors['danger']};
            }}
            QPushButton#logoutBtn:pressed {{
                background-color: {colors['danger']};
                color: #FFFFFF;
            }}
        """
        )
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)

        return top_bar

    def _export_data(self):
        from utils.sync_exchange import build_export_filename, export_sync_package

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт данных",
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
            QMessageBox.warning(self, "Экспорт", "Пароль не может быть пустым")
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
            QMessageBox.warning(self, "Экспорт", "Пароли не совпадают")
            return

        try:
            result = export_sync_package(self.user, file_path, password)
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
                f"Пункты планов: {counts.get('treatment_plan_items', 0)}"
            ),
        )

    def _import_data(self):
        from utils.sync_exchange import apply_sync_import, preview_sync_import

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт данных",
            "",
            "Пакет обмена PULSAR (*.pulsarzip)",
        )
        if not file_path:
            return

        password, ok = QInputDialog.getText(
            self,
            "Пароль пакета",
            "Введите пароль пакета:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return

        try:
            result = preview_sync_import(file_path, password)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка импорта", str(exc))
            return

        manifest = result["manifest"]
        preview = result["preview"]
        exported_by = manifest.get("exported_by", {})
        labels = {
            "users": "Пользователи",
            "facilities": "Места размещения",
            "km_records": "КМ-записи",
            "patients": "Пациенты",
            "documents": "Документы",
            "encounters": "Встречи",
            "treatment_plan_items": "Пункты планов",
        }
        preview_lines = []
        for table_name in ("users", "facilities", "patients", "documents", "encounters", "treatment_plan_items", "km_records"):
            item = preview.get(table_name, {})
            preview_lines.append(
                f"{labels[table_name]}: всего {item.get('incoming', 0)}, "
                f"новых {item.get('new', 0)}, "
                f"свежее в пакете {item.get('package_newer', 0)}, "
                f"свежее локально {item.get('local_newer', 0)}"
            )
        QMessageBox.information(
            self,
            "Пакет проверен",
            (
                "Пакет прочитан, запись в базу пока не выполнялась.\n\n"
                f"Автор: {exported_by.get('full_name', '')}\n"
                f"Роль: {exported_by.get('role', '')}\n"
                f"Дата экспорта: {manifest.get('exported_at', '')}\n\n"
                + "\n".join(preview_lines)
            ),
        )

        apply_count = 0
        for table_name in ("users", "facilities", "patients", "documents", "encounters", "treatment_plan_items", "km_records"):
            item = preview.get(table_name, {})
            apply_count += item.get("new", 0) + item.get("package_newer", 0)
        if apply_count <= 0:
            return

        patient_preview = {
            "new": apply_count,
            "package_newer": 0,
        }
        reply = QMessageBox.question(
            self,
            "Применить импорт пациентов?",
            (
                "Сейчас будут импортированы только пациенты.\n\n"
                f"Новых: {patient_preview.get('new', 0)}\n"
                f"Обновлений: {patient_preview.get('package_newer', 0)}\n\n"
                "Документы, встречи и планы пока не записываются."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            import_result = apply_sync_import(file_path, self.user, password)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка импорта", str(exc))
            return

        summary = import_result["summary"]
        QMessageBox.information(
            self,
            "Импорт пациентов завершен",
            (
                f"Добавлено: {summary.get('new', 0)}\n"
                f"Обновлено: {summary.get('updated', 0)}\n"
                f"Пропущено, локально свежее: {summary.get('skipped_local_newer', 0)}\n"
                f"Пропущено без изменений: {summary.get('skipped_same_or_unknown', 0)}\n"
                f"Пропущено без uuid: {summary.get('skipped_without_uuid', 0)}\n"
                f"Пропущено без врача в локальной базе: {summary.get('skipped_unmapped_doctor', 0)}"
            ),
        )
        current_page = self.stacked_widget.currentWidget()
        if hasattr(current_page, "_safe_load_patients"):
            current_page._safe_load_patients()
        elif hasattr(current_page, "_load_patients"):
            current_page._load_patients()
        if hasattr(current_page, "_load_import_logs"):
            current_page._load_import_logs()

    def _navigate(self, page_id: str):
        """Навигация к странице"""
        if self.user is None:
            return

        # Обновляем активную кнопку
        self._set_active_navigation(page_id)

        # Загружаем страницу
        self._load_page(page_id)

    def _load_page(self, page_id: str):
        """Загрузка страницы"""
        from ui.dashboard_page import DashboardPage
        from ui.patients_page import PatientsPage
        from ui.meeting_schedule_page import MeetingSchedulePage
        from ui.encounters_page import EncountersPage
        from ui.users_page import UsersPage
        from ui.planning_page import PlanningPage
        from ui.km_page import KmPage
        from ui.stats_page import StatsPage
        from ui.documents_page import DocumentsPage
        from ui.admin_page import AdminPage

        # Очищаем текущий виджет
        widget = self.stacked_widget.currentWidget()
        if widget:
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()

        # Создаём новую страницу
        if page_id == "dashboard":
            page = DashboardPage(self.user)
        elif page_id == "patients":
            page = PatientsPage(self.user)
        elif page_id == "meeting_schedule":
            page = MeetingSchedulePage(self.user)
        elif page_id == "encounters":
            page = EncountersPage(self.user)
        elif page_id == "users":
            page = UsersPage(self.user)
        elif page_id == "planning":
            page = PlanningPage(self.user)
        elif page_id == "km":
            page = KmPage(self.user)
        elif page_id == "stats":
            page = StatsPage(self.user)
        elif page_id == "documents":
            page = DocumentsPage(self.user)
        elif page_id == "admin":
            page = AdminPage(
                self.user,
                on_export=self._export_data,
                on_import=self._import_data,
            )
        else:
            page = DashboardPage(self.user)

        self.stacked_widget.addWidget(page)
        self.stacked_widget.setCurrentWidget(page)

    def _toggle_theme(self):
        """Переключение темы"""
        from ui.styles import (
            toggle_theme,
            get_main_stylesheet,
            get_colors,
            RADIUS,
            FONTS,
            scaled,
        )
        from PyQt6.QtWidgets import QPushButton, QLabel, QApplication
        from PyQt6.QtGui import QPalette, QColor

        new_theme = toggle_theme()
        self.current_theme_light = new_theme == "light"
        colors = get_colors()

        # Обновляем переключатель
        self.theme_switch.toggle()

        # Обновляем логотип (после смены темы)
        if hasattr(self, "logo_label"):
            logo_path = self._get_logo_path()
            self._update_logo(logo_path, colors)

        # Обновляем стили приложения
        app = QApplication.instance()
        app.setStyleSheet(get_main_stylesheet())

        # Обновляем палитру приложения
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
        palette.setColor(
            QPalette.ColorRole.AlternateBase, QColor(colors["surface_muted"])
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["accent"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["text"]))
        app.setPalette(palette)
        apply_native_theme_to_app(app)

        self.setStyleSheet(get_main_stylesheet())

        # Обновляем стили текущей страницы
        current_page = self.stacked_widget.currentWidget()
        if hasattr(current_page, "update_theme"):
            current_page.update_theme()
        self._update_open_window_themes()

        # Обновляем стили верхней панели
        top_bar = self.findChild(QFrame, "topBar")
        if top_bar:
            top_bar.setStyleSheet(
                f"""
                QFrame#topBar {{
                    background-color: {colors['nav_bg']};
                    border-bottom: 1px solid {colors['line']};
                }}
            """
            )
            # Обновляем логотип
            title_label = top_bar.findChild(QLabel, "title")
            if title_label:
                title_label.update()
            if hasattr(self, "logo_label"):
                self._update_logo(self._get_logo_path(), colors)
            # Обновляем кнопку выхода
            logout_btn = top_bar.findChild(QPushButton, "logoutBtn")
            if logout_btn:
                logout_btn.setFixedSize(scaled(190, 150), scaled(34, 28))
                logout_btn.setStyleSheet(
                    f"""
                    QPushButton#logoutBtn {{
                        background-color: transparent;
                        border: 1px solid {colors['line']};
                        border-radius: {RADIUS['md']}px;
                        padding: 0px 14px;
                        min-height: 0px;
                        min-width: {scaled(190, 150)}px;
                        max-width: {scaled(190, 150)}px;
                        max-height: {scaled(34, 28)}px;
                        font-weight: 600;
                        font-size: {FONTS['size_medium']}pt;
                        color: {colors['text_muted']};
                    }}
                    QPushButton#logoutBtn:hover {{
                        background-color: {colors['danger_bg']};
                        border: 1px solid {colors['danger']};
                        color: {colors['danger']};
                    }}
                    QPushButton#logoutBtn:pressed {{
                        background-color: {colors['danger']};
                        color: #FFFFFF;
                    }}
                """
                )

            for sync_btn_name in ("export_btn", "import_btn"):
                if hasattr(self, sync_btn_name):
                    getattr(self, sync_btn_name).setStyleSheet(
                        self._get_sync_button_style()
                    )

        # Обновляем стили области контента
        content_area = self.findChild(QWidget, "contentArea")
        if content_area:
            content_area.setStyleSheet(
                f"background-color: {colors['bg']}; color: {colors['text']};"
            )

        # Обновляем стили stacked widget
        self.stacked_widget.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        # Обновляем стили навигационных кнопок
        for btn in self.nav_buttons.values():
            btn.setStyleSheet(
                f"""
                QPushButton#navButton {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: {RADIUS['md']}px;
                    padding: 6px 12px;
                    font-size: {FONTS['size_small']}pt;
                    font-weight: 600;
                    color: {colors['text']};
                }}
                QPushButton#navButton:hover {{
                    background-color: {colors['surface_muted']};
                    border: 1px solid {colors['line']};
                    color: {colors['accent']};
                }}
                QPushButton#navButton#active {{
                    background-color: #3B82F6;
                    border: 1px solid #3B82F6;
                    color: #FFFFFF;
                    font-weight: 700;
                }}
                QPushButton#navButton:pressed {{
                    background-color: #3B82F6;
                    border: 1px solid #3B82F6;
                    color: #FFFFFF;
                }}
                QPushButton#navButton:disabled {{
                    background-color: transparent;
                    border: 1px solid {colors['line']};
                    color: {colors['text_muted']};
                }}
            """
            )

        # Обновляем все страницы
        # Сохраняем текущий page_id
        if hasattr(self, "nav_menu_button"):
            self.nav_menu_button.setStyleSheet(self._get_navigation_menu_style())
        if hasattr(self, "nav_menu"):
            self.nav_menu.setStyleSheet(self._get_navigation_menu_style())
        current_page_id = getattr(self, "current_page_id", "dashboard")

        # Пересоздаём все страницы для полного обновления стилей
        if self.user is not None:
            old_widgets = []
            while self.stacked_widget.count() > 0:
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
                old_widgets.append(widget)

            # Создаём новые страницы
            pages = {
                "dashboard": lambda: __import__(
                    "ui.dashboard_page", fromlist=["DashboardPage"]
                ).DashboardPage(self.user),
                "patients": lambda: __import__(
                    "ui.patients_page", fromlist=["PatientsPage"]
                ).PatientsPage(self.user),
                "meeting_schedule": lambda: __import__(
                    "ui.meeting_schedule_page", fromlist=["MeetingSchedulePage"]
                ).MeetingSchedulePage(self.user),
                "encounters": lambda: __import__(
                    "ui.encounters_page", fromlist=["EncountersPage"]
                ).EncountersPage(self.user),
                "users": lambda: __import__(
                    "ui.users_page", fromlist=["UsersPage"]
                ).UsersPage(self.user),
                "planning": lambda: __import__(
                    "ui.planning_page", fromlist=["PlanningPage"]
                ).PlanningPage(self.user),
                "km": lambda: __import__("ui.km_page", fromlist=["KmPage"]).KmPage(
                    self.user
                ),
                "stats": lambda: __import__(
                    "ui.stats_page", fromlist=["StatsPage"]
                ).StatsPage(self.user),
                "documents": lambda: __import__(
                    "ui.documents_page", fromlist=["DocumentsPage"]
                ).DocumentsPage(self.user),
                "admin": lambda: __import__(
                    "ui.admin_page", fromlist=["AdminPage"]
                ).AdminPage(
                    self.user,
                    on_export=self._export_data,
                    on_import=self._import_data,
                ),
            }

            for nav_id, page_factory in pages.items():
                page = page_factory()
                self.stacked_widget.addWidget(page)
                if nav_id == current_page_id:
                    self.stacked_widget.setCurrentWidget(page)

            # Удаляем старые страницы
            for widget in old_widgets:
                widget.deleteLater()

            # Обновляем активную кнопку
            self._set_active_navigation(current_page_id)

        # Принудительная перерисовка главного окна
        self.update()

    def _update_open_window_themes(self):
        """Обновляет тему в уже открытых диалогах и отдельных окнах."""
        app = QApplication.instance()
        if app is None:
            return

        for widget in app.topLevelWidgets():
            if widget is self or not widget.isVisible():
                continue
            apply_native_window_theme(widget)
            update_theme = getattr(widget, "update_theme", None)
            if callable(update_theme):
                update_theme()

    def _logout(self):
        """Выход из системы"""
        from ui.login_window import LoginWindow
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt

        # Удаляем все страницы из stacked_widget
        old_widgets = []
        while self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            old_widgets.append(widget)
        for widget in old_widgets:
            widget.deleteLater()

        # Отключаем все кнопки навигации
        if hasattr(self, "nav_menu_button"):
            self.nav_menu_button.setEnabled(False)

        # Сбрасываем заголовок
        self.setWindowTitle("PULSAR - Вход")

        # Создаём модальное окно входа поверх главного
        login_window = LoginWindow()
        login_window.setParent(self)
        login_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        login_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        login_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        login_window.login_successful.connect(self._on_login_success)

        # Сохраняем ссылку
        self._login_window = login_window

        # Центрируем и показываем
        login_window.show()
        self._center_login_window()

    def _center_login_window(self):
        """Центрирование окна авторизации"""
        if hasattr(self, "_login_window"):
            login_geo = self._login_window.frameGeometry()
            main_center = self.geometry().center()
            login_geo.moveCenter(main_center)
            self._login_window.move(login_geo.topLeft())

    def _on_login_success(self, user: User):
        """Успешный вход - обновление пользователя"""
        self.user = user
        self.setWindowTitle(f"PULSAR - {user.full_name}")
        self._login_window.close()

        # Обновляем навигацию для нового пользователя
        self._rebuild_navigation()

        # Обновляем активную кнопку
        # Загружаем главную страницу
        self._navigate("dashboard")

    def _rebuild_navigation(self):
        if hasattr(self, "nav_menu_button"):
            self.nav_menu_button.setEnabled(True)
        self._rebuild_navigation_menu()
        return
        """Обновление навигации для текущего пользователя"""
        nav_items = self._get_nav_items()

        # Скрываем все текущие кнопки
        for btn in self.nav_buttons.values():
            btn.setVisible(False)

        # Показываем нужные и обновляем
        for nav_id, (text, enabled) in nav_items.items():
            if nav_id in self.nav_buttons:
                # Кнопка уже существует — показываем
                btn = self.nav_buttons[nav_id]
                btn.setVisible(True)
                btn.setEnabled(enabled)
                btn.setText(text)
            else:
                # Кнопки нет — создаём новую
                btn = self._create_nav_button(text, nav_id, enabled)
                btn.setFixedHeight(40)
                self.nav_buttons[nav_id] = btn

                # Вставляем перед logoutBtn
                top_bar = self.findChild(QFrame, "topBar")
                if top_bar:
                    layout = top_bar.layout()
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if (
                            item
                            and item.widget()
                            and item.widget().objectName() == "logoutBtn"
                        ):
                            layout.insertWidget(i, btn)
                            break

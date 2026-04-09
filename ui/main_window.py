"""
Главное окно приложения
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    pyqtProperty,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
)
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QPixmap, QPainterPath
import os

from models.db_models import User
from ui.styles import get_colors, FONTS, RADIUS, get_main_stylesheet


class ThemeSwitch(QWidget):
    """Переключатель темы (toggle switch) - современный дизайн"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 28)
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
        target = 0 if is_light else 24
        self.animation.setStartValue(self._offset)
        self.animation.setEndValue(target)
        self.animation.start()

    def toggle(self):
        """Переключить тему"""
        self.current_theme_light = not self.current_theme_light
        target = 0 if self.current_theme_light else 24
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

        # Фон переключателя
        bg_color = QColor("#E2E8F0" if self.current_theme_light else "#334155")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 14, 14)

        # Тень под кружком
        shadow_color = QColor(0, 0, 0, 40 if self.current_theme_light else 80)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(QPoint(int(14 + self._offset), 14), 11, 11)

        # Кружок переключателя
        dot_color = QColor("#FFFFFF")
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(QPoint(int(14 + self._offset), 14), 10, 10)

        # Иконки
        if self.current_theme_light:
            # Солнце (жёлтое)
            painter.setPen(QPen(QColor("#F59E0B"), 1.5))
            center = QPoint(8, 14)
            # Лучи солнца
            painter.drawLine(
                QPoint(center.x() - 4, center.y()), QPoint(center.x() - 2, center.y())
            )
            painter.drawLine(
                QPoint(center.x() + 4, center.y()), QPoint(center.x() + 2, center.y())
            )
            painter.drawLine(
                QPoint(center.x(), center.y() - 4), QPoint(center.x(), center.y() - 2)
            )
            painter.drawLine(
                QPoint(center.x(), center.y() + 4), QPoint(center.x(), center.y() + 2)
            )
            # Круг солнца
            painter.drawEllipse(center, 3, 3)
        else:
            # Луна (белая)
            painter.setPen(QPen(QColor("#94A3B8"), 1.5))
            center = QPoint(44, 14)
            painter.drawEllipse(center, 3, 3)


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    theme_toggled = pyqtSignal(bool)  # Сигнал при переключении темы

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.current_theme_light = True

        self.setWindowTitle(f"LUX - {user.full_name}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(get_main_stylesheet())

        self._init_ui()

    def _update_logo(self, logo_path: str, colors: dict):
        """Обновление логотипа (PNG) со скруглёнными углами"""
        if not logo_path or not os.path.exists(logo_path):
            return
        try:
            pixmap = QPixmap(logo_path)
            if pixmap.isNull():
                return

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
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        logo = "logo_light.png"
        path = os.path.join(assets_dir, logo)
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
            User.ROLE_NURSE,
        ):
            items["patients"] = ("Пациенты", True)

        # Пользователи
        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            items["users"] = ("Пользователи", True)

        # Планирование
        items["planning"] = ("Планирование", True)

        # Статистика
        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            items["stats"] = ("Статистика", True)

        return items

    def _create_nav_button(self, text: str, nav_id: str, enabled: bool) -> QPushButton:
        """Создание кнопки навигации"""
        colors = get_colors()

        btn = QPushButton(text)
        btn.setObjectName("navButton")
        btn.setFixedHeight(48)
        btn.setMinimumWidth(120)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"""
            QPushButton#navButton {{
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: {RADIUS['md']}px;
                padding: 10px 20px;
                font-size: {FONTS['size_medium']}pt;
                font-weight: 600;
                color: {colors['text']};
            }}
            QPushButton#navButton:hover {{
                background-color: {colors['surface_muted']};
                border: 2px solid {colors['line']};
                color: {colors['accent']};
            }}
            QPushButton#navButton#active {{
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                color: #FFFFFF;
                font-weight: 700;
            }}
            QPushButton#navButton:pressed {{
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                color: #FFFFFF;
            }}
            QPushButton#navButton:disabled {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                color: {colors['text_muted']};
            }}
        """
        )

        if not enabled:
            btn.setEnabled(False)

        btn.clicked.connect(lambda: self._navigate(nav_id))
        btn.setProperty("nav_id", nav_id)

        return btn

    def _create_top_bar(self) -> QFrame:
        """Создание верхней панели"""
        colors = get_colors()

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(88)
        top_bar.setStyleSheet(
            f"""
            QFrame#topBar {{
                background-color: {colors['nav_bg']};
                border-bottom: 1px solid {colors['line']};
            }}
        """
        )

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        # Логотип и название слева
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(12)

        # Логотип
        logo_path = self._get_logo_path()
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setProperty("logoLabel", True)
        self._update_logo(logo_path, colors)
        logo_layout.addWidget(self.logo_label)

        title_label = QLabel("LUX")
        title_label.setObjectName("title")
        title_label.setStyleSheet(
            f"font-size: {FONTS['size_xlarge']}pt; font-weight: 700; color: {colors['accent']};"
        )
        logo_layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Ясность процессов. Свет решений.")
        subtitle_label.setObjectName("muted")
        subtitle_label.setStyleSheet(
            f"font-size: {FONTS['size_xs']}pt; color: {colors['text_muted']};"
        )
        logo_layout.addWidget(subtitle_label)

        layout.addLayout(logo_layout)

        layout.addSpacing(24)

        layout.addStretch()

        # Кнопки навигации (в обратном порядке)
        self.nav_buttons = {}
        nav_items = list(self._get_nav_items().items())
        for nav_id, (text, enabled) in nav_items:
            btn = self._create_nav_button(text, nav_id, enabled)
            btn.setFixedHeight(48)
            self.nav_buttons[nav_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Переключатель темы (toggle switch)
        self.theme_switch = ThemeSwitch(self)
        self.theme_switch.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_switch)

        layout.addSpacing(16)

        # Кнопка выхода в общем стиле
        logout_btn = QPushButton("Выход")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFixedHeight(40)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet(
            f"""
            QPushButton#logoutBtn {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: {FONTS['size_medium']}pt;
                color: {colors['text_muted']};
            }}
            QPushButton#logoutBtn:hover {{
                background-color: {colors['danger_bg']};
                border: 2px solid {colors['danger']};
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

    def _navigate(self, page_id: str):
        """Навигация к странице"""
        if self.user is None:
            return

        # Обновляем активную кнопку
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == page_id:
                btn.setProperty("active", True)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            else:
                btn.setProperty("active", False)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        # Загружаем страницу
        self._load_page(page_id)

    def _load_page(self, page_id: str):
        """Загрузка страницы"""
        from ui.dashboard_page import DashboardPage
        from ui.patients_page import PatientsPage
        from ui.users_page import UsersPage
        from ui.planning_page import PlanningPage
        from ui.stats_page import StatsPage

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
        elif page_id == "users":
            page = UsersPage(self.user)
        elif page_id == "planning":
            page = PlanningPage(self.user)
        elif page_id == "stats":
            page = StatsPage(self.user)
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

        self.setStyleSheet(get_main_stylesheet())

        # Обновляем стили текущей страницы
        current_page = self.stacked_widget.currentWidget()
        if hasattr(current_page, "update_theme"):
            current_page.update_theme()

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
                title_label.setStyleSheet(
                    f"font-size: {FONTS['size_xlarge']}pt; font-weight: 700; color: {colors['accent']};"
                )
            if hasattr(self, "logo_label"):
                self._update_logo(self._get_logo_path(), colors)
            # Обновляем кнопку выхода
            logout_btn = top_bar.findChild(QPushButton, "logoutBtn")
            if logout_btn:
                logout_btn.setStyleSheet(
                    f"""
                    QPushButton#logoutBtn {{
                        background-color: transparent;
                        border: 2px solid {colors['line']};
                        border-radius: {RADIUS['md']}px;
                        padding: 8px 16px;
                        font-weight: 600;
                        font-size: {FONTS['size_medium']}pt;
                        color: {colors['text_muted']};
                    }}
                    QPushButton#logoutBtn:hover {{
                        background-color: {colors['danger_bg']};
                        border: 2px solid {colors['danger']};
                        color: {colors['danger']};
                    }}
                    QPushButton#logoutBtn:pressed {{
                        background-color: {colors['danger']};
                        color: #FFFFFF;
                    }}
                """
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
                    border: 2px solid transparent;
                    border-radius: {RADIUS['md']}px;
                    padding: 10px 20px;
                    font-size: {FONTS['size_medium']}pt;
                    font-weight: 600;
                    color: {colors['text']};
                }}
                QPushButton#navButton:hover {{
                    background-color: {colors['surface_muted']};
                    border: 2px solid {colors['line']};
                    color: {colors['accent']};
                }}
                QPushButton#navButton#active {{
                    background-color: #3B82F6;
                    border: 2px solid #3B82F6;
                    color: #FFFFFF;
                    font-weight: 700;
                }}
                QPushButton#navButton:pressed {{
                    background-color: #3B82F6;
                    border: 2px solid #3B82F6;
                    color: #FFFFFF;
                }}
                QPushButton#navButton:disabled {{
                    background-color: transparent;
                    border: 2px solid {colors['line']};
                    color: {colors['text_muted']};
                }}
            """
            )

        # Обновляем все страницы
        # Сохраняем текущий page_id
        current_page_id = "dashboard"
        for nav_id, btn in self.nav_buttons.items():
            if btn.property("active"):
                current_page_id = nav_id
                break

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
                "users": lambda: __import__(
                    "ui.users_page", fromlist=["UsersPage"]
                ).UsersPage(self.user),
                "planning": lambda: __import__(
                    "ui.planning_page", fromlist=["PlanningPage"]
                ).PlanningPage(self.user),
                "stats": lambda: __import__(
                    "ui.stats_page", fromlist=["StatsPage"]
                ).StatsPage(self.user),
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
            for btn_id, btn in self.nav_buttons.items():
                btn.setProperty("active", btn_id == current_page_id)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        # Принудительная перерисовка главного окна
        self.update()

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
        for btn in self.nav_buttons.values():
            btn.setEnabled(False)
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Сбрасываем заголовок
        self.setWindowTitle("LUX - Вход")

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
        self.setWindowTitle(f"LUX - {user.full_name}")
        self._login_window.close()

        # Включаем кнопки навигации согласно роли
        nav_items = self._get_nav_items()
        for nav_id, btn in self.nav_buttons.items():
            enabled = nav_items.get(nav_id, ("", False))[1]
            btn.setEnabled(enabled)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Загружаем главную страницу
        self._navigate("dashboard")

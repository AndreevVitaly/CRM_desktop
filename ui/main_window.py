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
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen

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

    @property
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
        painter.drawEllipse(QPoint(14 + self._offset, 14), 11, 11)

        # Кружок переключателя
        dot_color = QColor("#FFFFFF")
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(QPoint(14 + self._offset, 14), 10, 10)

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

        self.setWindowTitle(f"MED_Desktop - {user.full_name}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(get_main_stylesheet())

        self._init_ui()

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
        self.stacked_widget.setStyleSheet(f"background-color: {colors['bg']};")
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
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"""
            QPushButton#navButton {{
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: {RADIUS['md']}px;
                padding: 8px 16px;
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
        top_bar.setFixedHeight(64)
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
        title_label = QLabel("MED_Desktop")
        title_label.setObjectName("title")
        title_label.setStyleSheet(
            f"font-size: {FONTS['size_large']}pt; font-weight: 700; color: {colors['accent']};"
        )
        logo_layout.addWidget(title_label)
        layout.addLayout(logo_layout)

        layout.addSpacing(24)

        layout.addStretch()

        # Кнопки навигации (в обратном порядке)
        self.nav_buttons = {}
        nav_items = list(self._get_nav_items().items())
        for nav_id, (text, enabled) in nav_items:
            btn = self._create_nav_button(text, nav_id, enabled)
            btn.setFixedHeight(40)
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

        self.current_theme_light = toggle_theme()
        colors = get_colors()

        # Обновляем переключатель
        self.theme_switch.toggle()

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
                    f"font-size: {FONTS['size_large']}pt; font-weight: 700; color: {colors['accent']};"
                )
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
            content_area.setStyleSheet(f"background-color: {colors['bg']};")

        # Обновляем стили stacked widget
        self.stacked_widget.setStyleSheet(f"background-color: {colors['bg']};")

        # Обновляем стили навигационных кнопок
        for btn in self.nav_buttons.values():
            btn.setStyleSheet(
                f"""
                QPushButton#navButton {{
                    background-color: transparent;
                    border: 2px solid transparent;
                    border-radius: {RADIUS['md']}px;
                    padding: 8px 16px;
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

        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget:
                # Для dashboard пересоздаём страницу для полного обновления стилей
                if hasattr(widget, "update_styles"):
                    # Пересоздаём dashboard страницу
                    from ui.dashboard_page import DashboardPage

                    new_dashboard = DashboardPage(self.user)
                    self.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
                    self.stacked_widget.addWidget(new_dashboard)
                    self.stacked_widget.setCurrentWidget(new_dashboard)
                    # Обновляем активную кнопку
                    for btn_id, btn in self.nav_buttons.items():
                        btn.setProperty("active", btn_id == current_page_id)
                        btn.style().unpolish(btn)
                        btn.style().polish(btn)
                else:
                    widget.setStyleSheet(get_main_stylesheet())

        # Принудительная перерисовка главного окна
        self.update()

    def _logout(self):
        """Выход из системы"""
        from ui.login_window import LoginWindow

        self.close()
        login_window = LoginWindow()
        login_window.login_successful.connect(self._on_login_success)
        login_window.show()

    def _on_login_success(self, user: User):
        """Успешный вход - перезапуск главного окна"""
        self.user = user
        self._init_ui()
        self.show()

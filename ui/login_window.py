"""
Экран входа в приложение
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QApplication,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QColor, QLinearGradient, QPen

from models.db_models import User, init_db
from ui.styles import get_colors, FONTS, RADIUS


class LoginWindow(QWidget):
    """Окно входа"""

    login_successful = pyqtSignal(object)  # Сигнал с объектом пользователя

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PULSAR - Вход")
        self.setFixedSize(420, 520)
        # Убираем рамку для закруглённых углов
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(self._get_login_style())
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Заголовок
        title_label = QLabel("PULSAR")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        title_label.setStyleSheet(
            f"""
            font-size: {FONTS['size_xlarge']}pt;
            font-weight: bold;
            color: {colors['accent']};
        """
        )
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Фундамент стабильной работы")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("muted")
        subtitle_label.setStyleSheet(
            f"font-size: {FONTS['size_xs']}pt; color: {colors['text_muted']};"
        )
        main_layout.addWidget(subtitle_label)

        main_layout.addSpacing(20)

        # Поле логина
        login_label = QLabel("Логин")
        login_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(login_label)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        self.login_input.setFixedHeight(44)
        self.login_input.returnPressed.connect(self._do_login)
        main_layout.addWidget(self.login_input)

        # Поле пароля
        password_label = QLabel("Пароль")
        password_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.returnPressed.connect(self._do_login)
        main_layout.addWidget(self.password_input)

        main_layout.addSpacing(10)

        # Кнопка регистрации
        self.register_button = QPushButton("Пройти регистрацию")
        self.register_button.setObjectName("secondaryBtn")
        self.register_button.setFixedHeight(44)
        self.register_button.clicked.connect(self._open_registration)
        main_layout.addWidget(self.register_button)

        # Сообщение об ошибке
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet(f"color: {colors['danger']}; font-weight: bold;")
        self.error_label.setWordWrap(True)
        main_layout.addWidget(self.error_label)

        self.setLayout(main_layout)

    def _get_login_style(self) -> str:
        """Стили для окна входа (Modern Design)"""
        colors = get_colors()
        return f"""
            QWidget {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
            QLineEdit {{
                background-color: {colors['surface']};
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 12px 16px;
                font-size: {FONTS['size_medium']}pt;
                color: {colors['text']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['text']};
            }}
            QLineEdit:hover {{
                border: 2px solid {colors['accent']};
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['accent']};
                padding: 11px 15px;
                outline: none;
                background-color: {colors['accent_light']};
            }}
            QLineEdit::placeholder {{
                color: {colors['text_muted']};
            }}
            QPushButton {{
                background-color: transparent;
                border: 2px solid {colors['accent']};
                border-radius: {RADIUS['md']}px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: {FONTS['size_medium']}pt;
                color: {colors['accent']};
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
            QPushButton:disabled {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                color: {colors['text_muted']};
            }}
            QPushButton#secondaryBtn {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                color: {colors['text']};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {colors['surface_muted']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#secondaryBtn:pressed {{
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                color: #FFFFFF;
            }}
        """

    def _do_login(self):
        """Попытка входа"""
        username = self.login_input.text().strip()
        password = self.password_input.text()

        if not username:
            self.error_label.setText("Введите логин")
            return

        if not password:
            self.error_label.setText("Введите пароль")
            return

        # Аутентификация
        user = User.authenticate(username, password)

        if user:
            if not user.is_active:
                self.error_label.setText("Учётная запись заблокирована")
                return

            self.error_label.setText("")
            self.login_successful.emit(user)
        else:
            self.error_label.setText("Неверный логин или пароль")
            self.password_input.clear()
            self.password_input.setFocus()

    def _open_registration(self):
        """Открытие диалога регистрации"""
        from ui.registration_dialog import RegistrationDialog

        # Создаём диалог без родителя, чтобы он не закрывал окно входа
        dialog = RegistrationDialog(None)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog_result = dialog.exec()

        # После успешной регистрации показываем сообщение
        if dialog_result:
            QMessageBox.information(
                self,
                "Регистрация успешна",
                "Ваша учётная запись создана. Теперь вы можете войти.",
            )

        # Возвращаем фокус на поле логина
        self.login_input.setFocus()

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        """Отрисовка закруглённых углов с градиентной рамкой"""
        colors = get_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        radius = RADIUS["lg"]

        # Путь для фона
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, radius, radius)
        painter.fillPath(bg_path, QColor(colors["bg"]))

        # Градиентная рамка — более заметная
        pen = QPen()

        if colors["bg"] == "#0A0A0A":
            # Тёмная тема: яркий синий градиент, тоньше
            pen.setWidth(3)
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, QColor("#60A5FA"))
            grad.setColorAt(0.5, QColor("#3B82F6"))
            grad.setColorAt(1, QColor("#2563EB"))
            pen.setBrush(grad)
        else:
            # Светлая тема: светло-серый градиент
            pen.setWidth(3)
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, QColor("#D4D4D4"))
            grad.setColorAt(1, QColor("#A3A3A3"))
            pen.setBrush(grad)

        painter.setPen(pen)
        inner = rect.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.drawRoundedRect(inner, radius, radius)

    def mousePressEvent(self, event):
        """Начало перетаскивания окна"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Перетаскивание окна"""
        if hasattr(self, "_old_pos"):
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.pos() + delta)
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Завершение перетаскивания"""
        if hasattr(self, "_old_pos"):
            del self._old_pos

"""
Экран входа в приложение
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QApplication, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from models.db_models import User, init_db
from ui.styles import get_colors, FONTS, RADIUS


class LoginWindow(QWidget):
    """Окно входа"""
    
    login_successful = pyqtSignal(object)  # Сигнал с объектом пользователя
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MED_Desktop - Вход")
        self.setFixedSize(420, 520)
        self.setStyleSheet(self._get_login_style())
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Логотип / Заголовок
        logo_label = QLabel("🏥")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 48px;")
        main_layout.addWidget(logo_label)
        
        title_label = QLabel("MED_Desktop")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        title_label.setStyleSheet(f"""
            font-size: {FONTS['size_xlarge']}pt;
            font-weight: bold;
            color: {colors['accent']};
        """)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Система управления больницей")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("muted")
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

        # Кнопка входа
        self.login_button = QPushButton("Войти")
        self.login_button.setFixedHeight(48)
        self.login_button.clicked.connect(self._do_login)
        main_layout.addWidget(self.login_button)

        # Кнопка регистрации
        self.register_button = QPushButton("📝 Пройти регистрацию")
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
                "Ваша учётная запись создана. Теперь вы можете войти."
            )
        
        # Возвращаем фокус на поле логина
        self.login_input.setFocus()

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

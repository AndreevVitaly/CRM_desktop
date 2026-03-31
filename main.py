"""
MED_Desktop - Десктопная CRM для больницы
Главный файл запуска
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.db_models import init_db, db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.styles import get_main_stylesheet


def main():
    """Точка входа в приложение"""
    
    # Инициализация БД
    init_db("medcrm.db")
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("MED_Desktop")
    app.setOrganizationName("Hospital CRM")
    
    # Установка шрифта
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Применение стилей
    app.setStyleSheet(get_main_stylesheet())
    
    # Настройка тёмной темы для тёмных элементов
    app.setStyle("Fusion")
    
    # Окно входа
    login_window = LoginWindow()
    login_window.login_successful.connect(lambda user: on_login_success(user, login_window))
    login_window.show()
    
    sys.exit(app.exec())


def on_login_success(user, login_window):
    """Успешный вход"""
    login_window.close()

    # Главное окно
    main_window = MainWindow(user)
    main_window.showMaximized()  # Открываем на весь экран

    # Загрузка дашборда
    main_window._navigate("dashboard")


if __name__ == "__main__":
    main()

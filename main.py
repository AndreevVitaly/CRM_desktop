"""
PULSAR - Десктопная CRM для работы с отделениями
Главный файл запуска
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.db_models import init_db, db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.styles import get_main_stylesheet

app_state = {
    "login_window": None,
    "main_window": None,
}


def exception_hook(exctype, value, tb):
    """Глобальный обработчик исключений"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(f"Uncaught exception: {error_msg}", flush=True)

    # Показываем сообщение об ошибке
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Ошибка")
    msg.setText(f"Произошла ошибка: {value}")
    msg.setDetailedText(error_msg)
    msg.exec()


def main():
    """Точка входа в приложение"""

    # Устанавливаем глобальный обработчик исключений
    sys.excepthook = exception_hook

    # Инициализация БД
    init_db("medcrm.db")

    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("PULSAR")
    app.setOrganizationName("PULSAR")

    # Установка шрифта
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Применение стилей
    app.setStyleSheet(get_main_stylesheet())

    # Настройка тёмной темы для тёмных элементов
    app.setStyle("Fusion")

    # Обработка исключений в событийном цикле
    app.setStyleSheet(get_main_stylesheet())

    # Окно входа
    login_window = LoginWindow()
    app_state["login_window"] = login_window
    login_window.login_successful.connect(
        lambda user: on_login_success(user, login_window)
    )
    login_window.show()

    sys.exit(app.exec())


def on_login_success(user, login_window):
    """Успешный вход"""
    login_window.close()

    # Главное окно
    main_window = MainWindow(user)
    app_state["main_window"] = main_window
    app_state["login_window"] = None
    main_window.showMaximized()  # Открываем на весь экран

    # Загрузка дашборда
    main_window._navigate("dashboard")


if __name__ == "__main__":
    main()

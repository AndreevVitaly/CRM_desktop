"""
PULSAR - Десктопная CRM для работы с отделениями
Главный файл запуска
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.db_models import init_db, db
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.styles import get_main_stylesheet
from utils.app_paths import get_db_path
from utils.db_encryption import (
    encrypt_existing_database,
    is_encrypted_database,
    is_plain_sqlite_database,
    is_sqlcipher_available,
)

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

    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("PULSAR")
    app.setOrganizationName("PULSAR")

    db_password = request_database_password()
    if db_password is None:
        sys.exit(0)

    db_path = get_db_path()
    if not prepare_database(db_path, db_password):
        sys.exit(1)

    # Инициализация БД
    init_db(str(db_path), db_password)

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


def request_database_password() -> str | None:
    if not is_sqlcipher_available():
        QMessageBox.critical(
            None,
            "SQLCipher",
            "SQLCipher не установлен. Установите зависимости из requirements.txt.",
        )
        return None

    while True:
        password, ok = QInputDialog.getText(
            None,
            "Пароль базы данных",
            "Введите пароль базы данных PULSAR:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return None
        if password:
            return password
        QMessageBox.warning(None, "Пароль базы данных", "Пароль не может быть пустым")


def prepare_database(db_path, password: str) -> bool:
    if not db_path.exists():
        return True

    if is_encrypted_database(db_path, password):
        return True

    if is_plain_sqlite_database(db_path):
        reply = QMessageBox.question(
            None,
            "Шифрование базы данных",
            (
                "Текущая база medcrm.db еще не зашифрована.\n\n"
                "Зашифровать ее сейчас с введенным паролем?\n"
                "Перед заменой будет создана резервная копия."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False
        try:
            backup_path = encrypt_existing_database(db_path, password)
        except Exception as exc:
            QMessageBox.critical(None, "Ошибка шифрования базы", str(exc))
            return False
        QMessageBox.information(
            None,
            "База зашифрована",
            f"База данных зашифрована.\nРезервная копия: {backup_path}",
        )
        return True

    QMessageBox.critical(
        None,
        "Ошибка базы данных",
        "База не открывается. Возможно, введен неверный пароль.",
    )
    return False


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

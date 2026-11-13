import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication, QDateEdit, QDialog, QWidget

from ui.native_window_theme import (
    NativeWindowThemeFilter,
    _is_decorated_window,
    apply_native_window_theme,
)


class NativeWindowThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_calendar_popup_does_not_schedule_native_theme(self):
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        popup = date_edit.calendarWidget().window()
        theme_filter = NativeWindowThemeFilter()
        with patch('ui.native_window_theme.QTimer.singleShot') as schedule:
            for event_type in (QEvent.Type.Show, QEvent.Type.WinIdChange):
                theme_filter.eventFilter(popup, QEvent(event_type))
            schedule.assert_not_called()
        with patch('ui.native_window_theme._is_windows', return_value=True), patch(
            'ui.native_window_theme._set_dwm_attribute'
        ) as set_attribute:
            apply_native_window_theme(popup)
            set_attribute.assert_not_called()

    def test_only_decorated_windows_receive_native_theme(self):
        window = QWidget()
        dialog = QDialog()
        child = QWidget(window)
        frameless = QWidget(None, Qt.WindowType.FramelessWindowHint)
        tooltip = QWidget(None, Qt.WindowType.ToolTip)
        self.assertTrue(_is_decorated_window(window))
        self.assertTrue(_is_decorated_window(dialog))
        for widget in (child, frameless, tooltip):
            self.assertFalse(_is_decorated_window(widget))


if __name__ == '__main__':
    unittest.main()

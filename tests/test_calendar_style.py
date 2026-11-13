import unittest

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QDateEdit, QDialog, QTableView, QVBoxLayout

from ui.calendar_style import configure_date_edit, PulsarCalendarWidget
from ui.styles import get_main_stylesheet, set_theme


class CalendarStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion')

    def tearDown(self):
        set_theme('light')
        self.app.setStyleSheet('')

    def test_every_date_is_visible_under_form_styles_in_both_themes(self):
        for theme in ('light', 'dark'):
            with self.subTest(theme=theme):
                set_theme(theme)
                self.app.setStyleSheet(get_main_stylesheet())
                dialog = QDialog()
                # Forms apply unqualified rules that propagate into the popup.
                dialog.setStyleSheet('background-color: white; color: white;')
                edit = QDateEdit(dialog)
                QVBoxLayout(dialog).addWidget(edit)
                edit.setCalendarPopup(True)
                configure_date_edit(edit)
                edit.setDate(QDate(2026, 11, 13))
                calendar = edit.calendarWidget()
                self.assertIsInstance(calendar, PulsarCalendarWidget)
                calendar.window().show()
                self.app.processEvents()
                view = calendar.findChild(QTableView)
                picture = calendar.grab().toImage()
                # Every date cell must contain contrasting text, including the
                # selected day and dates from the neighbouring months.
                for row in range(1, 7):
                    for column in range(7):
                        rect = view.visualRect(view.model().index(row, column))
                        origin = view.viewport().mapTo(calendar, rect.topLeft())
                        cell = picture.copy(origin.x() + 5, origin.y() + 5,
                                            rect.width() - 10, rect.height() - 10)
                        values = [QColor(cell.pixel(x, y)).lightness()
                                  for x in range(cell.width())
                                  for y in range(cell.height())]
                        self.assertGreater(max(values) - min(values), 40,
                                           (theme, row, column))
                calendar.window().hide()
                dialog.close()

    def test_configuring_existing_calendar_preserves_selection_and_bounds(self):
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDateRange(QDate(2020, 1, 1), QDate(2030, 12, 31))
        edit.setDate(QDate(2026, 11, 13))
        configure_date_edit(edit)
        calendar = edit.calendarWidget()
        configure_date_edit(edit)
        self.assertIs(edit.calendarWidget(), calendar)
        self.assertEqual(calendar.selectedDate(), edit.date())
        self.assertEqual(calendar.minimumDate(), edit.minimumDate())
        self.assertEqual(calendar.maximumDate(), edit.maximumDate())


if __name__ == '__main__':
    unittest.main()

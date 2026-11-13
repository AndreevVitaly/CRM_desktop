from __future__ import annotations

from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QColor, QIcon, QPalette, QTextCharFormat
from PyQt6.QtWidgets import QCalendarWidget, QToolButton

from ui.styles import FONTS, RADIUS, get_colors, scaled


def get_calendar_stylesheet() -> str:
    colors = get_colors()
    return f"""
        QCalendarWidget {{
            background-color: {colors['surface']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {colors['surface']};
            border-bottom: 1px solid {colors['line']};
            padding: {scaled(6)}px;
        }}
        QCalendarWidget QToolButton {{
            color: {colors['accent_strong']};
            background-color: transparent;
            border: none;
            border-radius: {RADIUS['sm']}px;
            min-height: {scaled(28)}px;
            padding: {scaled(4)}px {scaled(8)}px;
            font-weight: 600;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: {colors['accent_light']};
        }}
        QCalendarWidget QToolButton:pressed {{
            background-color: {colors['table_row_selected']};
        }}
        QCalendarWidget QMenu {{
            color: {colors['text']};
            background-color: {colors['surface']};
            border: 1px solid {colors['line']};
        }}
        QCalendarWidget QSpinBox {{
            color: {colors['text']};
            background-color: {colors['surface']};
            selection-background-color: {colors['accent']};
            selection-color: #FFFFFF;
        }}
        QCalendarWidget QTableView {{
            color: {colors['text']};
            background-color: {colors['surface']};
            alternate-background-color: {colors['surface_muted']};
            selection-background-color: {colors['accent']};
            selection-color: #FFFFFF;
            gridline-color: {colors['line_light']};
            border: none;
            outline: none;
            font-size: {FONTS['size_normal']}pt;
        }}
        QCalendarWidget QTableView::item:hover {{
            background-color: {colors['accent_light']};
            color: {colors['accent_strong']};
        }}
        QCalendarWidget QTableView::item:selected {{
            background-color: {colors['accent']};
            color: #FFFFFF;
        }}
    """


def apply_pulsar_calendar_style(calendar: QCalendarWidget):
    """Применяет единый читаемый стиль ко всем календарям PULSAR."""
    colors = get_colors()
    calendar.setMinimumSize(scaled(360), scaled(300))
    calendar.setLocale(QLocale(QLocale.Language.Russian, QLocale.Country.Russia))
    calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
    calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
    calendar.setGridVisible(True)
    calendar.setStyleSheet(get_calendar_stylesheet())

    palette = calendar.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["surface"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["surface_muted"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["accent_strong"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(colors["text_secondary"]),
    )
    calendar.setPalette(palette)

    weekday_format = QTextCharFormat()
    weekday_format.setForeground(QColor(colors["text"]))
    weekend_format = QTextCharFormat()
    weekend_format.setForeground(QColor(colors["danger"]))
    for day in (
        Qt.DayOfWeek.Monday,
        Qt.DayOfWeek.Tuesday,
        Qt.DayOfWeek.Wednesday,
        Qt.DayOfWeek.Thursday,
        Qt.DayOfWeek.Friday,
    ):
        calendar.setWeekdayTextFormat(day, weekday_format)
    calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
    calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)

    navigation_buttons = (
        ("qt_calendar_prevmonth", "‹"),
        ("qt_calendar_nextmonth", "›"),
    )
    for object_name, text in navigation_buttons:
        button = calendar.findChild(QToolButton, object_name)
        if button is not None:
            button.setIcon(QIcon())
            button.setText(text)
            button.setToolTip(
                "Предыдущий месяц" if object_name.endswith("prevmonth") else "Следующий месяц"
            )
    calendar.adjustSize()


def configure_date_edit(date_edit):
    """Безопасно оформляет календарь до открытия popup."""
    apply_pulsar_calendar_style(date_edit.calendarWidget())

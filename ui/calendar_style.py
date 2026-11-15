from __future__ import annotations

from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette, QTextCharFormat
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from ui.styles import FONTS, RADIUS, get_colors, scaled


def get_calendar_colors() -> dict:
    colors = dict(get_colors())
    dark = QColor(colors['surface']).lightness() < 128
    colors['calendar_selected'] = '#1D4ED8'
    colors['calendar_muted'] = '#B8B8B8' if dark else '#595959'
    colors['calendar_link'] = '#93C5FD' if dark else '#1E40AF'
    return colors


class PulsarCalendarWidget(QCalendarWidget):
    def paintCell(self, painter, rect, day):
        # Paint both foreground and background: ancestor styles for table items
        # otherwise override Qt's calendar delegate, hiding selected dates.
        colors = get_calendar_colors()
        enabled = self.isEnabled() and self.minimumDate() <= day <= self.maximumDate()
        selected = enabled and day == self.selectedDate()
        current_month = day.month() == self.monthShown() and day.year() == self.yearShown()
        background = colors['surface'] if current_month else colors['surface_muted']
        foreground = colors['text']
        if not enabled or not current_month:
            foreground = colors['calendar_muted']
        elif day.dayOfWeek() >= 6:
            foreground = colors['danger']
        if selected:
            background, foreground = colors['calendar_selected'], '#FFFFFF'
        painter.save()
        painter.fillRect(rect, QColor(background))
        painter.setPen(QColor(colors['line_light']))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        font = painter.font()
        font.setBold(selected)
        painter.setFont(font)
        painter.setPen(QColor(foreground))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(day.day()))
        if enabled and day == day.currentDate() and not selected:
            painter.setPen(QColor(colors['calendar_link']))
            painter.drawRect(rect.adjusted(1, 1, -2, -2))
        painter.restore()


def get_calendar_stylesheet() -> str:
    colors = get_calendar_colors()
    return f"""
        QCalendarWidget {{
            background-color: {colors['surface']};
            border: 1px solid {colors['line']};
            border-radius: {RADIUS['md']}px;
        }}
        QCalendarWidget QWidget {{
            color: {colors['text']};
            background-color: {colors['surface']};
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {colors['surface']};
            border-bottom: 1px solid {colors['line']};
            padding: {scaled(6)}px;
        }}
        QCalendarWidget QToolButton {{
            color: {colors['calendar_link']};
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
        QCalendarWidget QMenu::item:selected {{
            background-color: {colors['calendar_selected']};
            color: #FFFFFF;
        }}
        QCalendarWidget QSpinBox {{
            color: {colors['text']};
            background-color: {colors['surface']};
            selection-background-color: {colors['calendar_selected']};
            selection-color: #FFFFFF;
        }}
        QCalendarWidget QTableView {{
            color: {colors['text']};
            background-color: {colors['surface']};
            alternate-background-color: {colors['surface_muted']};
            selection-background-color: {colors['calendar_selected']};
            selection-color: #FFFFFF;
            gridline-color: {colors['line_light']};
            border: none;
            outline: none;
            font-size: {FONTS['size_normal']}pt;
        }}
        QCalendarWidget QTableView::item {{
            padding: 0px;
            border: none;
        }}
        QCalendarWidget QTableView::item:hover {{
            background-color: {colors['accent_light']};
            color: {colors['accent_strong']};
        }}
        QCalendarWidget QTableView::item:selected {{
            background-color: {colors['calendar_selected']};
            color: #FFFFFF;
        }}
    """


def apply_pulsar_calendar_style(calendar: QCalendarWidget):
    """Применяет единый читаемый стиль ко всем календарям PULSAR."""
    colors = get_calendar_colors()
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
    palette.setColor(QPalette.ColorRole.Button, QColor(colors['surface']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["calendar_link"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["calendar_selected"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(colors["calendar_muted"]),
    )
    calendar.setPalette(palette)

    weekday_format = QTextCharFormat()
    weekday_format.setForeground(QColor(colors["text"]))
    weekday_format.setBackground(QColor(colors['surface_muted']))
    weekday_format.setFontWeight(QFont.Weight.DemiBold)
    weekend_format = QTextCharFormat()
    weekend_format.setForeground(QColor(colors["danger"]))
    weekend_format.setBackground(QColor(colors['surface_muted']))
    weekend_format.setFontWeight(QFont.Weight.DemiBold)
    calendar.setHeaderTextFormat(weekday_format)
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
    calendar = date_edit.calendarWidget()
    if type(calendar) is QCalendarWidget:
        calendar = PulsarCalendarWidget(date_edit)
        date_edit.setCalendarWidget(calendar)
    apply_pulsar_calendar_style(calendar)


class _SafeCalendarMixin:
    """Заменяет нестабильный Windows popup на обычный модальный диалог."""

    def _init_safe_calendar(self):
        self._pulsar_calendar = QCalendarWidget(self)
        self._pulsar_calendar_dialog = None
        super().setCalendarPopup(False)

    def setCalendarPopup(self, enabled: bool):
        # Qt 6.7 на Windows может падать при уничтожении активного popup.
        super().setCalendarPopup(False)

    def setCalendarWidget(self, calendar: QCalendarWidget):
        if self._pulsar_calendar_dialog is not None:
            raise RuntimeError("Календарь нельзя заменять после первого открытия")
        self._pulsar_calendar = calendar
        calendar.setParent(self)

    def calendarWidget(self) -> QCalendarWidget:
        return self._pulsar_calendar

    def _ensure_calendar_dialog(self) -> QDialog:
        if self._pulsar_calendar_dialog is not None:
            return self._pulsar_calendar_dialog

        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор даты")
        dialog.setModal(True)
        dialog.setMinimumSize(scaled(390), scaled(370))

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(scaled(14), scaled(14), scaled(14), scaled(14))
        layout.setSpacing(scaled(12))
        layout.addWidget(self._pulsar_calendar)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_button = QPushButton("Отмена")
        select_button = QPushButton("Выбрать")
        select_button.setObjectName("primaryBtn")
        cancel_button.clicked.connect(dialog.reject)
        select_button.clicked.connect(dialog.accept)
        buttons.addWidget(cancel_button)
        buttons.addWidget(select_button)
        layout.addLayout(buttons)

        self._pulsar_calendar.activated.connect(dialog.accept)
        self._pulsar_calendar_dialog = dialog
        return dialog

    def showCalendarDialog(self):
        dialog = self._ensure_calendar_dialog()
        apply_pulsar_calendar_style(self._pulsar_calendar)
        self._pulsar_calendar.setSelectedDate(self.date())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.setDate(self._pulsar_calendar.selectedDate())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().x() >= self.width() - scaled(42):
            event.accept()
            self.showCalendarDialog()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_F4, Qt.Key.Key_Down) and (
            event.key() == Qt.Key.Key_F4
            or event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            event.accept()
            self.showCalendarDialog()
            return
        super().keyPressEvent(event)


class PulsarDateEdit(_SafeCalendarMixin, QDateEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_safe_calendar()


class PulsarDateTimeEdit(_SafeCalendarMixin, QDateTimeEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_safe_calendar()

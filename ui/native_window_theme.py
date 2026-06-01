"""
Нативная тема рамок окон Windows.

Qt stylesheet не управляет системной шапкой окна. На Windows просим DWM
окрасить заголовки открытых окон в текущую тему приложения.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys

from PyQt6.QtCore import QEvent, QObject, QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from ui.styles import get_colors


DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36


class NativeWindowThemeFilter(QObject):
    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget) and event.type() in (
            QEvent.Type.Show,
            QEvent.Type.WinIdChange,
        ):
            QTimer.singleShot(0, lambda widget=obj: apply_native_window_theme(widget))
        return super().eventFilter(obj, event)


def install_native_theme_filter(app: QApplication):
    if not _is_windows():
        return
    if getattr(app, "_pulsar_native_theme_filter", None):
        return
    theme_filter = NativeWindowThemeFilter(app)
    app.installEventFilter(theme_filter)
    app._pulsar_native_theme_filter = theme_filter


def apply_native_theme_to_app(app: QApplication | None = None):
    if not _is_windows():
        return
    app = app or QApplication.instance()
    if app is None:
        return
    for widget in app.topLevelWidgets():
        apply_native_window_theme(widget)


def apply_native_window_theme(widget: QWidget | None):
    if not _is_windows() or widget is None:
        return
    try:
        if not widget.isWindow():
            return
        win_id = widget.winId()
        if win_id is None:
            return
        hwnd = int(win_id)
    except (RuntimeError, TypeError, ValueError):
        return

    colors = get_colors()
    is_dark = colors["bg"].lower() == "#0a0a0a"
    dark_value = ctypes.c_int(1 if is_dark else 0)

    _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, dark_value)
    _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, dark_value)

    caption_color = _colorref(colors["bg"] if is_dark else colors["nav_bg"])
    text_color = _colorref(colors["text"])
    border_color = _colorref(colors["line"])
    _set_dwm_color(hwnd, DWMWA_CAPTION_COLOR, caption_color)
    _set_dwm_color(hwnd, DWMWA_TEXT_COLOR, text_color)
    _set_dwm_color(hwnd, DWMWA_BORDER_COLOR, border_color)


def _set_dwm_attribute(hwnd: int, attribute: int, value: ctypes.c_int):
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.wintypes.HWND(hwnd),
            ctypes.c_uint(attribute),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        pass


def _set_dwm_color(hwnd: int, attribute: int, colorref: int):
    value = ctypes.c_int(colorref)
    _set_dwm_attribute(hwnd, attribute, value)


def _colorref(hex_color: str) -> int:
    color = hex_color.lstrip("#")
    if len(color) != 6:
        return 0
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return red | (green << 8) | (blue << 16)


def _is_windows() -> bool:
    return sys.platform.startswith("win")

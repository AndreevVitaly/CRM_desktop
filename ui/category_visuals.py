"""Единое оформление позывных и категорий АА."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate

from ui.styles import get_colors


CATEGORY_ROLE = Qt.ItemDataRole.UserRole + 1


def mark_category_item(item, category: str | None) -> None:
    """Помечает элемент таблицы типом категории для делегата."""
    item.setData(CATEGORY_ROLE, category)


class CategoryUnderlineDelegate(QStyledItemDelegate):
    """Рисует цветное подчёркивание, оставляя текст нейтральным."""

    def __init__(self, parent=None):
        super().__init__(parent)
        colors = get_colors()
        self._colors = {
            "adult": QColor(colors["danger"]),
            "child": QColor(colors["info"]),
            "undefined": QColor(colors["success"]),
        }

    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)
        color = self._colors.get(index.data(CATEGORY_ROLE))
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not color or not text:
            return
        text_rect = (
            option.widget.style().subElementRect(
                QStyle.SubElement.SE_ItemViewItemText, option, option.widget
            )
            if option.widget
            else option.rect
        )
        width = min(option.fontMetrics.horizontalAdvance(str(text)), text_rect.width())
        painter.save()
        painter.setPen(color)
        painter.drawLine(text_rect.left(), option.rect.bottom() - 4,
                         text_rect.left() + width, option.rect.bottom() - 4)
        painter.restore()

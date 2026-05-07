import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QLabel

from ui.styles import FONTS, get_colors


class BrandTitleLabel(QLabel):
    def __init__(self, text="PULSAR", parent=None, point_size=None):
        super().__init__(text, parent)
        self._point_size = point_size or FONTS["size_xlarge"]

        font = QFont()
        font.setPointSize(self._point_size)
        font.setWeight(QFont.Weight.Black)
        self.setFont(font)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        metrics = QFontMetricsF(self.font())
        self.setMinimumHeight(int(metrics.height()) + 10)
        self.setMinimumWidth(int(metrics.horizontalAdvance(text)) + 30)

    def paintEvent(self, event):
        colors = get_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        font = self.font()
        metrics = QFontMetricsF(font)
        rect = self.contentsRect()
        text = self.text()
        text_width = metrics.horizontalAdvance(text)
        star_gap = max(7.0, self._point_size * 0.52)
        star_radius = max(7.0, self._point_size * 0.58)
        group_width = text_width + star_gap + star_radius * 2

        alignment = self.alignment()
        if alignment & Qt.AlignmentFlag.AlignHCenter:
            x = rect.left() + (rect.width() - group_width) / 2
        elif alignment & Qt.AlignmentFlag.AlignRight:
            x = rect.right() - group_width
        else:
            x = rect.left()

        y = rect.top() + (rect.height() + metrics.ascent() - metrics.descent()) / 2
        path = QPainterPath()
        path.addText(QPointF(x, y), font, text)
        bounds = path.boundingRect()

        dark_theme = colors["bg"] == "#0A0A0A"
        shadow_color = QColor(0, 20, 60, 82 if dark_theme else 46)
        glow_color = QColor(colors["accent_soft"])
        glow_color.setAlpha(34 if dark_theme else 24)
        highlight_color = QColor(255, 255, 255, 135 if dark_theme else 185)

        shadow_path = QPainterPath(path)
        shadow_path.translate(1.1, 1.4)
        painter.fillPath(shadow_path, shadow_color)

        glow_path = QPainterPath(path)
        glow_path.translate(0.0, 0.5)
        painter.strokePath(glow_path, QPen(glow_color, 1.0))

        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
        if dark_theme:
            gradient.setColorAt(0.0, QColor("#93C5FD"))
            gradient.setColorAt(0.42, QColor(colors["accent_hover"]))
            gradient.setColorAt(1.0, QColor(colors["accent_strong"]))
        else:
            gradient.setColorAt(0.0, QColor("#60A5FA"))
            gradient.setColorAt(0.45, QColor(colors["accent"]))
            gradient.setColorAt(1.0, QColor(colors["accent_strong"]))
        painter.fillPath(path, gradient)

        highlight_path = QPainterPath(path)
        highlight_path.translate(-0.45, -0.55)
        painter.strokePath(highlight_path, QPen(highlight_color, 0.5))

        star_center = QPointF(
            x + text_width + star_gap + star_radius,
            y - metrics.ascent() * 0.31,
        )
        self._paint_star(painter, star_center, star_radius, gradient, shadow_color, highlight_color)

    def _paint_star(self, painter, center, radius, gradient, shadow_color, highlight_color):
        shadow_pen = QPen(shadow_color, 1.55)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(shadow_pen)
        shadow_center = QPointF(center.x() + 0.8, center.y() + 1.0)
        for index in range(8):
            angle = math.radians(index * 45)
            inner = radius * 0.62
            outer = radius
            start = QPointF(
                shadow_center.x() + math.cos(angle) * inner,
                shadow_center.y() + math.sin(angle) * inner,
            )
            end = QPointF(
                shadow_center.x() + math.cos(angle) * outer,
                shadow_center.y() + math.sin(angle) * outer,
            )
            painter.drawLine(start, end)
        painter.setBrush(shadow_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(shadow_center, radius * 0.3, radius * 0.3)

        ray_pen = QPen()
        ray_pen.setBrush(gradient)
        ray_pen.setWidthF(1.45)
        ray_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(ray_pen)
        for index in range(8):
            angle = math.radians(index * 45)
            inner = radius * 0.62
            outer = radius
            start = QPointF(
                center.x() + math.cos(angle) * inner,
                center.y() + math.sin(angle) * inner,
            )
            end = QPointF(
                center.x() + math.cos(angle) * outer,
                center.y() + math.sin(angle) * outer,
            )
            painter.drawLine(start, end)

        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 0.32, radius * 0.32)

        highlight_pen = QPen(highlight_color, 0.55)
        highlight_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(highlight_pen)
        painter.drawLine(
            QPointF(center.x() - radius * 0.34, center.y() - radius * 0.34),
            QPointF(center.x() + radius * 0.08, center.y() - radius * 0.08),
        )

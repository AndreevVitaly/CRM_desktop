"""
Страница дашборда
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QScrollArea,
    QPushButton,
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont, QEnterEvent
from datetime import datetime, timedelta

from models.db_models import User, Patient, Encounter, Event, Facility
from ui.styles import get_colors, FONTS, RADIUS


class KPICard(QFrame):
    """KPI карточка с обработкой наведения"""

    def __init__(self, title: str, value: str, subtitle: str = ""):
        super().__init__()
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._is_hovered = False
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setObjectName("kpiCard")
        self.setFixedHeight(140)
        self.setStyleSheet(self._get_stylesheet())

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Заголовок
        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("kpiCardTitle")
        self.title_label.setStyleSheet(self._get_title_stylesheet())
        layout.addWidget(self.title_label)

        # Значение
        self.value_label = QLabel(self._value)
        self.value_label.setObjectName("kpiCardValue")
        self.value_label.setStyleSheet(self._get_value_stylesheet())
        layout.addWidget(self.value_label)

        # Подзаголовок
        self.subtitle_label = None
        if self._subtitle:
            self.subtitle_label = QLabel(self._subtitle)
            self.subtitle_label.setObjectName("kpiCardSubtitle")
            self.subtitle_label.setStyleSheet(self._get_subtitle_stylesheet())
            layout.addWidget(self.subtitle_label)

    def _get_stylesheet(self) -> str:
        """Получить стили для карточки"""
        colors = get_colors()
        # Фиксируем border в 2px всегда, чтобы layout не прыгал
        # Меняем только цвет рамки при наведении
        if self._is_hovered:
            return f"""
                QFrame#kpiCard {{
                    background-color: {colors['accent_light']};
                    border: 2px solid {colors['accent']};
                    border-radius: {RADIUS['lg']}px;
                    padding: 19px;
                }}
            """
        return f"""
            QFrame#kpiCard {{
                background-color: {colors['surface']};
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
                padding: 19px;
            }}
        """

    def _get_title_stylesheet(self) -> str:
        """Получить стили для заголовка"""
        colors = get_colors()
        return f"font-size: {FONTS['size_medium']}pt; color: {colors['text_muted']}; font-weight: 600; background-color: transparent;"

    def _get_value_stylesheet(self) -> str:
        """Получить стили для значения"""
        colors = get_colors()
        return f"""
            font-size: 36px;
            font-weight: 700;
            color: {colors['accent']};
            background-color: transparent;
        """

    def _get_subtitle_stylesheet(self) -> str:
        """Получить стили для подзаголовка"""
        colors = get_colors()
        return f"font-size: {FONTS['size_small']}pt; color: {colors['text_muted']}; background-color: transparent;"

    def enterEvent(self, event: QEnterEvent):
        """Обработка наведения мыши"""
        self._is_hovered = True
        self.setStyleSheet(self._get_stylesheet())
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        """Обработка ухода мыши"""
        self._is_hovered = False
        self.setStyleSheet(self._get_stylesheet())
        super().leaveEvent(event)

    def update_styles(self):
        """Обновить стили при смене темы"""
        self.setStyleSheet(self._get_stylesheet())
        self.title_label.setStyleSheet(self._get_title_stylesheet())
        self.value_label.setStyleSheet(self._get_value_stylesheet())
        if self.subtitle_label:
            self.subtitle_label.setStyleSheet(self._get_subtitle_stylesheet())


class DashboardPage(QWidget):
    """Страница дашборда"""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        colors = get_colors()

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )
        scroll.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Приветствие
        greeting = self._create_greeting()
        greeting.setAutoFillBackground(False)
        layout.addWidget(greeting)

        # KPI карточки
        stats_list = self._create_stats_list(self._get_kpi_data())
        layout.addWidget(stats_list)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        quick_actions = self._get_quick_actions()
        for text, callback in quick_actions:
            btn = self._create_action_button(text)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

    def _create_greeting(self) -> QLabel:
        """Приветствие пользователя"""
        colors = get_colors()

        greeting = QLabel(f"Добрый день, {self.user.first_name}!")
        greeting.setObjectName("greeting")
        greeting.setStyleSheet(
            f"""
            font-size: {FONTS['size_xlarge']}pt;
            font-weight: 700;
            color: {colors['text']};
            background-color: transparent;
        """
        )
        return greeting

    def _get_kpi_data(self) -> list:
        """Получение KPI данных для роли"""
        user = self.user

        if user.role == User.ROLE_ADMIN:
            total_patients = Patient.get_all(include_inactive=False)
            total_doctors = len(User.get_by_role(User.ROLE_DOCTOR))
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            visits_today = len(
                Encounter.get_unique_meetings(
                    start_date=today,
                    end_date=today + timedelta(days=1),
                )
            )
            events_today = len(Event.get_all(include_completed=False))

            return [
                ("Всего категорий АА", str(len(total_patients)), "активных"),
                ("Работников", str(total_doctors), "в системе"),
                ("Встреч", str(visits_today), "сегодня"),
                ("Мероприятий", str(events_today), "запланировано"),
            ]

        elif user.role == User.ROLE_REGISTRAR:
            total_patients = Patient.get_all(include_inactive=False)
            total_users = len(User.get_all())

            return [
                ("Всего категорий АА", str(len(total_patients)), "активных"),
                ("Пользователей", str(total_users), "в системе"),
                ("Встреч", "—", "сегодня"),
                ("Мероприятий", "—", "запланировано"),
            ]

        elif user.role == User.ROLE_LEAD:
            dept_patients = Patient.get_all(user=user)
            dept_doctors = User.get_by_role(User.ROLE_DOCTOR)
            dept_doctors = [d for d in dept_doctors if d.department == user.department]

            return [
                ("Категорий АА отделения", str(len(dept_patients)), ""),
                ("Работников в отделении", str(len(dept_doctors)), ""),
                ("Встреч", "—", "сегодня"),
                ("Мероприятий", "—", "отделение"),
            ]

        elif user.role == User.ROLE_DOCTOR:
            my_patients = Patient.get_all(user=user)
            my_encounters = Encounter.get_unique_meetings(user=user)

            return [
                ("Моих категорий АА", str(len(my_patients)), ""),
                ("Встреч", str(len(my_encounters)), "всего"),
                ("Планов", "—", "лечения"),
                ("Мероприятий", "—", ""),
            ]

        elif user.role == User.ROLE_NURSE:
            dept_patients = Patient.get_all(user=user)

            return [
                ("Категорий АА отделения", str(len(dept_patients)), ""),
                ("Встреч", "—", "сегодня"),
                ("Процедур", "—", "запланировано"),
                ("Мероприятий", "—", ""),
            ]

        return [
            ("Категорий АА", "0", ""),
            ("Встреч", "0", ""),
            ("Планов", "0", ""),
            ("Мероприятий", "0", ""),
        ]

    def _create_kpi_card(self, title: str, value: str, subtitle: str) -> KPICard:
        """Создание KPI карточки"""
        return KPICard(title, value, subtitle)

    def _create_stats_list(self, items: list) -> QWidget:
        colors = get_colors()

        container = QWidget()
        container.setObjectName("statsList")
        container.setMaximumWidth(520)
        container.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(0)

        for title, value, subtitle in items:
            row = QWidget()
            row.setObjectName("statsRow")
            row.setStyleSheet("background-color: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 7, 0, 7)
            row_layout.setSpacing(18)

            label_text = f"{title} {str(subtitle).lower()}" if subtitle else title
            title_label = QLabel(label_text)
            title_label.setObjectName("statsLabel")
            title_label.setStyleSheet(
                f"font-size: {FONTS['size_medium']}pt; color: {colors['text_muted']}; background-color: transparent;"
            )

            value_label = QLabel(value)
            value_label.setObjectName("statsValue")
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            value_label.setMinimumWidth(70)
            value_label.setStyleSheet(
                f"font-size: {FONTS['size_large']}pt; font-weight: 700; color: {colors['accent']}; background-color: transparent;"
            )

            row_layout.addWidget(title_label, 1)
            row_layout.addWidget(value_label)
            layout.addWidget(row)

        return container

    def update_styles(self):
        """Обновить стили при смене темы"""
        colors = get_colors()

        # Обновляем общий фон
        self.setStyleSheet(
            f"background-color: {colors['bg']}; color: {colors['text']};"
        )

        # Обновляем фон content_widget внутри scroll area
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.setStyleSheet("background-color: transparent; border: none;")
            content_widget = scroll_area.widget()
            if content_widget:
                content_widget.setStyleSheet(
                    f"background-color: {colors['bg']}; color: {colors['text']};"
                )

        # Обновляем все QLabel в виджете
        for label in self.findChildren(QLabel):
            if label.objectName() == "greeting":
                label.setStyleSheet(
                    f"""
                    font-size: {FONTS['size_xlarge']}pt;
                    font-weight: 700;
                    color: {colors['text']};
                    background-color: transparent;
                """
                )
            elif label.objectName() == "sectionTitle":
                label.setStyleSheet(
                    f"font-size: {FONTS['size_title']}pt; font-weight: 700; color: {colors['text']}; margin: 10px 0; background-color: transparent;"
                )
            elif label.objectName() == "statsLabel":
                label.setStyleSheet(
                    f"font-size: {FONTS['size_medium']}pt; color: {colors['text_muted']}; background-color: transparent;"
                )
            elif label.objectName() == "statsValue":
                label.setStyleSheet(
                    f"font-size: {FONTS['size_large']}pt; font-weight: 700; color: {colors['accent']}; background-color: transparent;"
                )

        # Обновляем все KPI карточки
        for card in self.findChildren(KPICard):
            card.update_styles()

        # Обновляем кнопки быстрых действий
        for btn in self.findChildren(QPushButton, "actionButton"):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    border: 2px solid {colors['line']};
                    border-radius: {RADIUS['md']}px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: {FONTS['size_medium']}pt;
                    color: {colors['text']};
                }}
                QPushButton:hover {{
                    background-color: {colors['accent_light']};
                    border: 2px solid {colors['accent']};
                    color: {colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: #3B82F6;
                    border: 2px solid #3B82F6;
                    color: #FFFFFF;
                }}
            """
            )

        # Обновляем список мероприятий
        events_card = self.findChild(QFrame, "card")
        if events_card:
            events_card.setStyleSheet(
                f"""
                QFrame#card {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['line']};
                    border-radius: {RADIUS['lg']}px;
                }}
            """
            )
            # Обновляем элементы мероприятий
            for event_frame in events_card.findChildren(QFrame):
                if event_frame != events_card:
                    event_frame.setStyleSheet(
                        f"""
                        QFrame {{
                            background-color: {colors['surface_muted']};
                            border-radius: {RADIUS['md']}px;
                            padding: 12px;
                            margin-bottom: 8px;
                        }}
                    """
                    )

    def _get_quick_actions(self) -> list:
        """Получение быстрых действий для роли"""
        user = self.user
        actions = []

        # Кнопки быстрых действий пока не нужны для регистратора
        # Добавление пользователя доступно в разделе "Пользователи"

        return actions

    def _create_action_button(self, text: str) -> QPushButton:
        """Создание кнопки быстрого действия"""
        colors = get_colors()

        btn = QPushButton(text)
        btn.setObjectName("actionButton")
        btn.setFixedHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: {FONTS['size_medium']}pt;
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['accent_light']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton:pressed {{
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                color: #FFFFFF;
            }}
        """
        )
        return btn

    def _add_user(self):
        """Добавить пользователя"""
        from ui.user_form import UserFormDialog

        dialog = UserFormDialog(self.user, None)
        if dialog.exec():
            pass

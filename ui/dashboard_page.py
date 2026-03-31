"""
Страница дашборда
"""

from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QGridLayout, QScrollArea, QPushButton)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont, QEnterEvent

from models.db_models import User, Patient, Encounter, Event, Facility
from models.db_models import DEPARTMENTS
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
        content_widget.setStyleSheet(f"background-color: {colors['bg']};")
        scroll.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Приветствие
        greeting = self._create_greeting()
        greeting.setAutoFillBackground(False)
        layout.addWidget(greeting)
        
        # KPI карточки
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(16)
        
        kpi_cards = self._get_kpi_data()
        for i, (title, value, subtitle) in enumerate(kpi_cards):
            card = self._create_kpi_card(title, value, subtitle)
            row = i // 4
            col = i % 4
            kpi_layout.addWidget(card, row, col)
        
        layout.addLayout(kpi_layout)
        
        # Быстрые действия
        actions_label = QLabel("Быстрые действия")
        actions_label.setObjectName("sectionTitle")
        actions_label.setStyleSheet(f"font-size: {FONTS['size_title']}pt; font-weight: 700; color: {colors['text']}; margin: 10px 0;")
        layout.addWidget(actions_label)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        quick_actions = self._get_quick_actions()
        for text, callback in quick_actions:
            btn = self._create_action_button(text)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Мероприятия сегодня
        events_label = QLabel("Мероприятия сегодня")
        events_label.setObjectName("sectionTitle")
        events_label.setStyleSheet(f"font-size: {FONTS['size_title']}pt; font-weight: 700; color: {colors['text']}; margin: 10px 0;")
        layout.addWidget(events_label)
        
        events_widget = self._create_events_list()
        layout.addWidget(events_widget)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {colors['bg']};")
    
    def _create_greeting(self) -> QLabel:
        """Приветствие пользователя"""
        colors = get_colors()

        greeting = QLabel(f"Добрый день, {self.user.first_name}!")
        greeting.setObjectName("greeting")
        greeting.setStyleSheet(f"""
            font-size: {FONTS['size_xlarge']}pt;
            font-weight: 700;
            color: {colors['text']};
            background-color: transparent;
        """)
        return greeting

    def _get_kpi_data(self) -> list:
        """Получение KPI данных для роли"""
        user = self.user

        if user.role == User.ROLE_ADMIN:
            total_patients = Patient.get_all(include_inactive=False)
            total_doctors = len(User.get_by_role(User.ROLE_DOCTOR))
            visits_today = len(Encounter.get_all())
            events_today = len(Event.get_all(include_completed=False))

            return [
                ("Всего пациентов", str(len(total_patients)), "активных"),
                ("Врачей", str(total_doctors), "в системе"),
                ("Визитов", str(visits_today), "сегодня"),
                ("Мероприятий", str(events_today), "запланировано"),
            ]

        elif user.role == User.ROLE_REGISTRAR:
            total_patients = Patient.get_all(include_inactive=False)
            total_users = len(User.get_all())

            return [
                ("Всего пациентов", str(len(total_patients)), "активных"),
                ("Пользователей", str(total_users), "в системе"),
                ("Визитов", "—", "сегодня"),
                ("Мероприятий", "—", "запланировано"),
            ]

        elif user.role == User.ROLE_LEAD:
            dept_patients = Patient.get_all(user=user)
            dept_doctors = User.get_by_role(User.ROLE_DOCTOR)
            dept_doctors = [d for d in dept_doctors if d.department == user.department]

            return [
                ("Пациентов отделения", str(len(dept_patients)), ""),
                ("Врачей в отделении", str(len(dept_doctors)), ""),
                ("Визитов", "—", "сегодня"),
                ("Мероприятий", "—", "отделение"),
            ]

        elif user.role == User.ROLE_DOCTOR:
            my_patients = Patient.get_all(user=user)
            my_encounters = Encounter.get_by_patient(my_patients[0].id) if my_patients else []

            return [
                ("Моих пациентов", str(len(my_patients)), ""),
                ("Визитов", str(len(my_encounters)), "всего"),
                ("Планов", "—", "лечения"),
                ("Мероприятий", "—", ""),
            ]

        elif user.role == User.ROLE_NURSE:
            dept_patients = Patient.get_all(user=user)

            return [
                ("Пациентов отделения", str(len(dept_patients)), ""),
                ("Визитов", "—", "сегодня"),
                ("Процедур", "—", "запланировано"),
                ("Мероприятий", "—", ""),
            ]

        return [
            ("Пациентов", "0", ""),
            ("Визитов", "0", ""),
            ("Планов", "0", ""),
            ("Мероприятий", "0", ""),
        ]
    
    def _create_kpi_card(self, title: str, value: str, subtitle: str) -> KPICard:
        """Создание KPI карточки"""
        return KPICard(title, value, subtitle)

    def update_styles(self):
        """Обновить стили при смене темы"""
        colors = get_colors()

        # Обновляем общий фон
        self.setStyleSheet(f"background-color: {colors['bg']};")

        # Обновляем фон content_widget внутри scroll area
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.setStyleSheet("background-color: transparent; border: none;")
            content_widget = scroll_area.widget()
            if content_widget:
                content_widget.setStyleSheet(f"background-color: {colors['bg']};")

        # Обновляем все QLabel в виджете
        for label in self.findChildren(QLabel):
            if label.objectName() == "greeting":
                label.setStyleSheet(f"""
                    font-size: {FONTS['size_xlarge']}pt;
                    font-weight: 700;
                    color: {colors['text']};
                    background-color: transparent;
                """)
            elif label.objectName() == "sectionTitle":
                label.setStyleSheet(f"font-size: {FONTS['size_title']}pt; font-weight: 700; color: {colors['text']}; margin: 10px 0; background-color: transparent;")

        # Обновляем все KPI карточки
        for card in self.findChildren(KPICard):
            card.update_styles()

        # Обновляем кнопки быстрых действий
        for btn in self.findChildren(QPushButton, "actionButton"):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['surface']};
                    border: 2px solid {colors['line']};
                    border-radius: {RADIUS['md']}px;
                    padding: 8px 20px;
                    font-weight: 600;
                    font-size: {FONTS['size_medium']}pt;
                    color: {colors['text']};
                }}
                QPushButton:hover {{
                    background-color: {colors['accent_light']};
                    border: 2px solid {colors['accent']};
                    color: {colors['accent']};
                }}
            """)

        # Обновляем список мероприятий
        events_card = self.findChild(QFrame, "card")
        if events_card:
            events_card.setStyleSheet(f"""
                QFrame#card {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['line']};
                    border-radius: {RADIUS['lg']}px;
                }}
            """)
            # Обновляем элементы мероприятий
            for event_frame in events_card.findChildren(QFrame):
                if event_frame != events_card:
                    event_frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: {colors['surface_muted']};
                            border-radius: {RADIUS['md']}px;
                            padding: 12px;
                            margin-bottom: 8px;
                        }}
                    """)
    
    def _get_quick_actions(self) -> list:
        """Получение быстрых действий для роли"""
        user = self.user
        actions = []

        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            actions.append(("Добавить пациента", self._add_patient))

        if user.role == User.ROLE_REGISTRAR:
            actions.append(("Добавить пользователя", self._add_user))

        if user.role in (User.ROLE_ADMIN, User.ROLE_REGISTRAR, User.ROLE_LEAD):
            actions.append(("Справка", self._generate_certificate))

        actions.append(("Создать мероприятие", self._add_event))

        return actions

    def _create_action_button(self, text: str) -> QPushButton:
        """Создание кнопки быстрого действия"""
        colors = get_colors()

        btn = QPushButton(text)
        btn.setObjectName("actionButton")
        btn.setFixedHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['surface']};
                border: 2px solid {colors['line']};
                border-radius: {RADIUS['md']}px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: {FONTS['size_medium']}pt;
                color: {colors['text']};
            }}
            QPushButton:hover {{
                background-color: {colors['accent_light']};
                border: 2px solid {colors['accent']};
                color: {colors['accent']};
            }}
        """)
        return btn
    
    def _create_events_list(self) -> QFrame:
        """Создание списка мероприятий"""
        colors = get_colors()
        
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {colors['surface']};
                border: 1px solid {colors['line']};
                border-radius: {RADIUS['lg']}px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        
        events = Event.get_all(user=self.user, include_completed=False)
        today_events = [e for e in events if e.event_date == Event().event_date]
        
        if today_events:
            for event in today_events[:5]:
                event_widget = self._create_event_item(event)
                layout.addWidget(event_widget)
        else:
            no_events = QLabel("Нет мероприятий на сегодня")
            no_events.setObjectName("muted")
            no_events.setStyleSheet(f"padding: 20px; color: {colors['text_muted']};")
            layout.addWidget(no_events)
        
        return card
    
    def _create_event_item(self, event) -> QFrame:
        """Создание элемента мероприятия"""
        colors = get_colors()
        
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['surface_muted']};
                border-radius: {RADIUS['md']}px;
                padding: 12px;
                margin-bottom: 8px;
            }}
        """)
        
        layout = QVBoxLayout(item)
        layout.setSpacing(4)
        
        title = QLabel(f"📌 {event.title}")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        details = QLabel(f"{event.event_type_display} • {event.department_display}")
        details.setObjectName("muted")
        layout.addWidget(details)
        
        if event.responsible:
            responsible = QLabel(f"Ответственный: {event.responsible.full_name}")
            responsible.setObjectName("muted")
            layout.addWidget(responsible)
        
        return item
    
    def _add_patient(self):
        """Добавить пациента"""
        from ui.patient_form import PatientFormDialog
        dialog = PatientFormDialog(self.user, None)
        if dialog.exec():
            pass  # Пациент сохранён
    
    def _add_user(self):
        """Добавить пользователя"""
        from ui.user_form import UserFormDialog
        dialog = UserFormDialog(self.user, None)
        if dialog.exec():
            pass
    
    def _generate_certificate(self):
        """Сгенерировать справку"""
        from PyQt6.QtWidgets import QMessageBox, QInputDialog
        
        # Диалог выбора пациента по ID
        patient_id, ok = QInputDialog.getInt(
            self,
            "Генерация справки",
            "Введите ID пациента для генерации справки:"
        )
        
        if not ok or not patient_id:
            return
        
        from models.db_models import Patient
        patient = Patient.get_by_id(patient_id)
        
        if not patient:
            QMessageBox.warning(self, "Ошибка", f"Пациент с ID {patient_id} не найден")
            return
        
        # Генерация текста справки
        certificate_text = f"""
СПРАВКА
о прохождении лечения

Выдана {patient.full_name}

Дата рождения: {patient.birth_date.strftime("%d.%m.%Y")}
Пол: {"Мужской" if patient.gender == "M" else "Женский"}
Отделение: {patient.department_display}
{f"Лечащий врач: {patient.doctor.full_name}" if patient.doctor else ""}

Дана в том, что пациент действительно проходит лечение в нашем учреждении.

Справка действительна в течение 30 дней с даты выдачи.
Дата выдачи: {datetime.now().strftime("%d.%m.%Y")}
        """.strip()
        
        # Показ справки
        from PyQt6.QtWidgets import QTextEdit, QDialog, QDialogButtonBox, QVBoxLayout
        from PyQt6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Справка")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(certificate_text)
        text_edit.setReadOnly(True)
        text_edit.setFontPointSize(11)
        layout.addWidget(text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
    
    def _add_event(self):
        """Добавить мероприятие"""
        from ui.event_form import EventFormDialog
        dialog = EventFormDialog(self.user, None)
        if dialog.exec():
            pass

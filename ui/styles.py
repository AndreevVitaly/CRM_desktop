"""
Современные стили для MED_Desktop
Стиль: Modern Clean Design 2024
"""

# ============================================================================
# ЦВЕТОВАЯ ПАЛИТРА (Светлая тема)
# ============================================================================

COLORS_LIGHT = {
    # Основные цвета (Minimal Gray Scale)
    "bg": "#FAFAFA",              # Очень светлый серый фон
    "surface": "#FFFFFF",          # Чистый белый
    "surface_muted": "#F5F5F5",    # Светлый серый
    "text": "#1A1A1A",             # Тёмный серый (мягкий чёрный)
    "text_muted": "#737373",       # Средний серый
    "text_secondary": "#A3A3A3",   # Светлый серый

    # Границы и разделители
    "line": "#E5E5E5",             # Тонкая светлая граница
    "line_light": "#F0F0F0",       # Едва заметная граница

    # Акцентные цвета (приглушённые)
    "accent": "#2563EB",           # Спокойный синий
    "accent_hover": "#1D4ED8",     # Темнее при наведении
    "accent_strong": "#1E40AF",    # Тёмный синий
    "accent_light": "#EFF6FF",     # Очень светлый синий фон
    "accent_soft": "#60A5FA",      # Мягкий синий

    # Градиенты (убраны, используются однотонные цвета)
    "gradient_start": "#2563EB",
    "gradient_end": "#2563EB",

    # Цвета состояний (мягкие)
    "success": "#059669",          # Изумруд
    "success_bg": "#ECFDF5",
    "warning": "#D97706",          # Янтарь
    "warning_bg": "#FFFBEB",
    "danger": "#DC2626",           # Красный
    "danger_bg": "#FEF2F2",
    "info": "#2563EB",             # Синий
    "info_bg": "#EFF6FF",

    # Роли (приглушённые)
    "role_admin": "#7C3AED",       # Фиолетовый
    "role_reg": "#0891B2",         # Циан
    "role_lead": "#059669",        # Изумруд
    "role_doc": "#2563EB",         # Синий
    "role_nur": "#DB2777",         # Розовый

    # Таблицы
    "table_header_bg": "#FAFAFA",
    "table_row_hover": "#F5F5F5",
    "table_row_selected": "#F0F7FF",
    "table_border": "#E5E5E5",

    # Навигация
    "nav_bg": "#FFFFFF",

    # Переключатель темы
    "switch_bg": "#E5E5E5",
    "switch_dot": "#FFFFFF",

    # Тени (едва заметные)
    "shadow_sm": "0 1px 2px rgba(0, 0, 0, 0.04)",
    "shadow": "0 2px 4px rgba(0, 0, 0, 0.06)",
    "shadow_lg": "0 4px 8px rgba(0, 0, 0, 0.08)",
    "shadow_xl": "0 8px 16px rgba(0, 0, 0, 0.1)",
    "shadow_glow": "0 0 12px rgba(37, 99, 235, 0.15)",
}

# ============================================================================
# ЦВЕТОВАЯ ПАЛИТРА (Тёмная тема)
# ============================================================================

COLORS_DARK = {
    # Основные цвета (Minimal Dark)
    "bg": "#0A0A0A",              # Глубокий чёрный
    "surface": "#171717",          # Тёмный серый
    "surface_muted": "#262626",    # Серый
    "text": "#EDEDED",             # Светлый серый
    "text_muted": "#A3A3A3",       # Средний серый
    "text_secondary": "#737373",   # Тёмный серый

    # Границы
    "line": "#262626",             # Тонкая граница
    "line_light": "#333333",       # Светлая граница

    # Акцентные цвета (приглушённые)
    "accent": "#3B82F6",           # Светлый синий
    "accent_hover": "#60A5FA",     # Ещё светлее при наведении
    "accent_strong": "#2563EB",    # Синий
    "accent_light": "#1E3A5F",     # Тёмный синий фон
    "accent_soft": "#60A5FA",      # Мягкий синий

    # Градиенты
    "gradient_start": "#3B82F6",
    "gradient_end": "#3B82F6",

    # Цвета состояний (мягкие)
    "success": "#34D399",          # Изумруд
    "success_bg": "#064E3B",
    "warning": "#FBBF24",          # Янтарь
    "warning_bg": "#451A03",
    "danger": "#F87171",           # Красный
    "danger_bg": "#450A0A",
    "info": "#60A5FA",             # Синий
    "info_bg": "#1E3A5F",

    # Роли (приглушённые)
    "role_admin": "#A78BFA",       # Фиолетовый
    "role_reg": "#22D3EE",         # Циан
    "role_lead": "#34D399",        # Изумруд
    "role_doc": "#60A5FA",         # Синий
    "role_nur": "#F472B6",         # Розовый

    # Таблицы
    "table_header_bg": "#171717",
    "table_row_hover": "#262626",
    "table_row_selected": "#1E3A5F",
    "table_border": "#262626",

    # Навигация
    "nav_bg": "#0A0A0A",

    # Переключатель темы
    "switch_bg": "#333333",
    "switch_dot": "#EDEDED",

    # Тени (едва заметные)
    "shadow_sm": "0 1px 2px rgba(0, 0, 0, 0.3)",
    "shadow": "0 2px 4px rgba(0, 0, 0, 0.4)",
    "shadow_lg": "0 4px 8px rgba(0, 0, 0, 0.5)",
    "shadow_xl": "0 8px 16px rgba(0, 0, 0, 0.6)",
    "shadow_glow": "0 0 12px rgba(59, 130, 246, 0.2)",
}

# ============================================================================
# ШРИФТЫ И РАЗМЕРЫ
# ============================================================================

FONTS = {
    "family": "Segoe UI Variable",  # Современный шрифт Windows 11
    "family_fallback": "Segoe UI, Inter, system-ui, sans-serif",
    "size_xs": 8,
    "size_small": 9,
    "size_normal": 10,
    "size_medium": 11,
    "size_large": 12,
    "size_xlarge": 14,
    "size_title": 16,
    "size_header": 20,
    "size_display": 24,
}

# Радиусы скругления (Modern Rounded)
RADIUS = {
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "pill": 999,
}

# ============================================================================
# ТЕКУЩАЯ ТЕМА
# ============================================================================

current_theme = "light"

def get_colors() -> dict:
    """Получить цвета текущей темы"""
    global current_theme
    return COLORS_LIGHT if current_theme == "light" else COLORS_DARK


def set_theme(theme: str):
    """Установить тему (light/dark)"""
    global current_theme
    current_theme = theme


def toggle_theme() -> str:
    """Переключить тему и вернуть новое значение"""
    global current_theme
    current_theme = "dark" if current_theme == "light" else "light"
    return current_theme


# ============================================================================
# QSS СТИЛИ (Qt Style Sheets)
# ============================================================================

def get_main_stylesheet() -> str:
    """Современный stylesheet для приложения"""
    colors = get_colors()

    return f"""
/* ============================================
   ОБЩИЕ СТИЛИ
   ============================================ */

QWidget {{
    font-family: "{FONTS['family']}", {FONTS['family_fallback']};
    font-size: {FONTS['size_normal']}pt;
    color: {colors['text']};
    background-color: {colors['bg']};
}}

/* ============================================
   ОКНА И ДИАЛОГИ
   ============================================ */

QMainWindow {{
    background-color: {colors['bg']};
}}

QDialog {{
    background-color: {colors['surface']};
    border-radius: {RADIUS['lg']}px;
}}

/* ============================================
   КНОПКИ
   ============================================ */

QPushButton {{
    background-color: {colors['accent']};
    color: white;
    border: none;
    border-radius: {RADIUS['sm']}px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: {FONTS['size_medium']}pt;
}}

QPushButton:hover {{
    background-color: {colors['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {colors['accent_strong']};
    padding: 11px 19px 9px 21px;
}}

QPushButton:disabled {{
    background-color: {colors['line']};
    color: {colors['text_muted']};
}}

QPushButton::menu-indicator {{
    image: none;
}}

/* Вторичная кнопка */
QPushButton#secondaryBtn {{
    background-color: transparent;
    border: 1px solid {colors['line']};
    color: {colors['text']};
}}

QPushButton#secondaryBtn:hover {{
    background-color: {colors['surface_muted']};
    border-color: {colors['accent']};
}}

/* Опасная кнопка */
QPushButton#dangerBtn {{
    background-color: {colors['danger']};
}}

QPushButton#dangerBtn:hover {{
    background-color: #DC2626;
}}

/* Кнопка-призрак (ghost) */
QPushButton#ghostBtn {{
    background-color: transparent;
    border: 1px solid {colors['line']};
    color: {colors['text_muted']};
}}

QPushButton#ghostBtn:hover {{
    color: {colors['text']};
    border-color: {colors['accent']};
}}

/* Акцентная кнопка (outline) */
QPushButton#accentBtn {{
    background-color: transparent;
    border: 1px solid {colors['accent']};
    color: {colors['accent']};
}}

QPushButton#accentBtn:hover {{
    background-color: {colors['accent']};
    color: white;
}}

/* ============================================
   ПОЛЯ ВВОДА
   ============================================ */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['sm']}px;
    padding: 10px 12px;
    color: {colors['text']};
    selection-background-color: {colors['accent_light']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {colors['accent']};
    outline: none;
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {colors['surface_muted']};
    color: {colors['text_muted']};
}}

QPlainTextEdit {{
    border-radius: {RADIUS['sm']}px;
}}

/* ============================================
   ВЫПАДАЮЩИЕ СПИСКИ
   ============================================ */

QComboBox {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['sm']}px;
    padding: 10px 12px;
    min-width: 140px;
    color: {colors['text']};
}}

QComboBox:hover {{
    border: 1px solid {colors['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 32px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {colors['text_muted']};
    margin-right: 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['sm']}px;
    selection-background-color: {colors['accent_light']};
    selection-color: {colors['text']};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    min-height: 32px;
    padding: 6px 10px;
    border-radius: {RADIUS['sm']}px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {colors['table_row_hover']};
}}

/* ============================================
   ТАБЛИЦЫ
   ============================================ */

QTableWidget, QTableView {{
    background-color: {colors['surface']};
    border: 1px solid {colors['table_border']};
    border-radius: {RADIUS['md']}px;
    selection-background-color: {colors['table_row_selected']};
    gridline-color: {colors['line_light']};
    color: {colors['text']};
}}

QTableWidget::item, QTableView::item {{
    padding: 12px;
    border-radius: {RADIUS['sm']}px;
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {colors['table_row_hover']};
}}

QHeaderView::section {{
    background-color: {colors['surface']};
    color: {colors['text_muted']};
    padding: 14px 12px;
    border: none;
    border-bottom: 1px solid {colors['line']};
    font-weight: 600;
    font-size: {FONTS['size_xs']}pt;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

QHeaderView::section:first {{
    border-top-left-radius: {RADIUS['md']}px;
}}

QHeaderView::section:last {{
    border-top-right-radius: {RADIUS['md']}px;
}}

/* ============================================
   СКРОЛЛБАРЫ
   ============================================ */

QScrollBar:vertical {{
    background-color: {colors['bg']};
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['line']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {colors['bg']};
    height: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['line']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors['text_muted']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ============================================
   НАВИГАЦИЯ (SIDEBAR)
   ============================================ */

QFrame#sidebar {{
    background-color: {colors['nav_bg']};
    border-right: 1px solid {colors['line']};
}}

/* Кнопки навигации */
QPushButton#navButton {{
    background-color: transparent;
    border: none;
    border-radius: {RADIUS['sm']}px;
    padding: 12px 16px;
    text-align: left;
    font-size: {FONTS['size_medium']}pt;
    font-weight: 500;
    color: {colors['text']};
}}

QPushButton#navButton:hover {{
    background-color: {colors['surface_muted']};
    color: {colors['accent']};
}}

QPushButton#navButton#active {{
    background-color: {colors['accent_light']};
    color: {colors['accent']};
    font-weight: 600;
}}

QPushButton#navButton:disabled {{
    color: {colors['text_muted']};
}}

/* ============================================
   КАРТОЧКИ
   ============================================ */

QFrame#card {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
}}

QFrame#card.flat {{
    border: none;
    background-color: {colors['surface_muted']};
}}

QFrame#cardHeader {{
    background-color: transparent;
    border-bottom: 1px solid {colors['line_light']};
    border-top-left-radius: {RADIUS['md']}px;
    border-top-right-radius: {RADIUS['md']}px;
    padding: 16px;
}}

QFrame#cardContent {{
    background-color: transparent;
    padding: 16px;
}}

/* ============================================
   ВКЛАДКИ (TABS)
   ============================================ */

QTabWidget::pane {{
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
    background-color: {colors['surface']};
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {colors['text_muted']};
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    font-weight: 500;
    border-top-left-radius: {RADIUS['sm']}px;
    border-top-right-radius: {RADIUS['sm']}px;
}}

QTabBar::tab:hover {{
    color: {colors['text']};
    background-color: {colors['surface_muted']};
}}

QTabBar::tab:selected {{
    color: {colors['accent']};
    border-bottom: 2px solid {colors['accent']};
    background-color: {colors['surface']};
}}

/* ============================================
   ЧЕКБОКСЫ И РАДИОКНОПКИ
   ============================================ */

QCheckBox, QRadioButton {{
    color: {colors['text']};
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {colors['line']};
    background-color: {colors['surface']};
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border: 1px solid {colors['accent']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['accent']};
    border: 1px solid {colors['accent']};
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QRadioButton::indicator:checked {{
    background-color: {colors['accent']};
    border: 1px solid {colors['accent']};
}}

/* ============================================
   ПРОГРЕСС БАР
   ============================================ */

QProgressBar {{
    background-color: {colors['surface_muted']};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {colors['accent']};
    border-radius: 4px;
}}

/* ============================================
   LABELS
   ============================================ */

QLabel {{
    color: {colors['text']};
    background-color: transparent;
}}

QLabel#muted {{
    color: {colors['text_muted']};
}}

QLabel#title {{
    font-size: {FONTS['size_title']}pt;
    font-weight: 700;
}}

QLabel#header {{
    font-size: {FONTS['size_header']}pt;
    font-weight: 700;
}}

QLabel#display {{
    font-size: {FONTS['size_display']}pt;
    font-weight: 700;
}}

QLabel#accent {{
    color: {colors['accent']};
}}

QLabel#pageSubtitle {{
    color: {colors['text_muted']};
    margin-top: 6px;
    font-size: {FONTS['size_medium']}pt;
}}

/* ============================================
   SCROLL AREA
   ============================================ */

QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ============================================
   GROUP BOX
   ============================================ */

QGroupBox {{
    background-color: transparent;
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: {colors['text_muted']};
    text-transform: uppercase;
    font-size: {FONTS['size_xs']}pt;
    letter-spacing: 0.05em;
    font-weight: 600;
}}

/* ============================================
   DATE/TIME EDIT
   ============================================ */

QDateEdit, QTimeEdit, QDateTimeEdit {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['sm']}px;
    padding: 10px 12px;
    color: {colors['text']};
}}

QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
    border: 1px solid {colors['accent']};
    outline: none;
}}

QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {{
    border: none;
    width: 32px;
}}

QDateEdit::down-arrow, QTimeEdit::down-arrow, QDateTimeEdit::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {colors['text_muted']};
    margin-right: 12px;
}}

/* ============================================
   КАЛЕНДАРЬ
   ============================================ */

QCalendarWidget QToolButton {{
    color: {colors['text']};
    background-color: transparent;
    border: none;
    border-radius: {RADIUS['md']}px;
    padding: 10px;
    font-weight: 600;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {colors['surface_muted']};
}}

QCalendarWidget QMenu {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {colors['surface']};
    border-bottom: 1px solid {colors['line']};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {colors['surface']};
    selection-background-color: {colors['accent']};
    selection-color: white;
    border: none;
}}

/* ============================================
   СПЕЦИАЛЬНЫЕ ЦВЕТА РОЛЕЙ
   ============================================ */

QLabel#role_ADMIN {{
    color: {colors['role_admin']};
    font-weight: 700;
}}

QLabel#role_REGISTRAR {{
    color: {colors['role_reg']};
    font-weight: 700;
}}

QLabel#role_LEAD {{
    color: {colors['role_lead']};
    font-weight: 700;
}}

QLabel#role_DOC {{
    color: {colors['role_doc']};
    font-weight: 700;
}}

QLabel#role_NUR {{
    color: {colors['role_nur']};
    font-weight: 700;
}}

/* ============================================
   STATUS INDICATORS
   ============================================ */

QLabel#status_PLANNED {{
    color: {colors['info']};
    background-color: {colors['info_bg']};
    padding: 4px 10px;
    border-radius: {RADIUS['pill']}px;
    font-weight: 600;
    font-size: {FONTS['size_xs']}pt;
}}

QLabel#status_INPROGRESS {{
    color: {colors['warning']};
    background-color: {colors['warning_bg']};
    padding: 4px 10px;
    border-radius: {RADIUS['pill']}px;
    font-weight: 600;
    font-size: {FONTS['size_xs']}pt;
}}

QLabel#status_FINISHED {{
    color: {colors['success']};
    background-color: {colors['success_bg']};
    padding: 4px 10px;
    border-radius: {RADIUS['pill']}px;
    font-weight: 600;
    font-size: {FONTS['size_xs']}pt;
}}

/* ============================================
   KPI CARDS
   ============================================ */

QFrame#kpiCard {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
    padding: 20px;
    min-height: 120px;
}}

QFrame#kpiCard:hover {{
    border: 1px solid {colors['accent']};
}}

/* ============================================
   PILL BADGE
   ============================================ */

QLabel#pill {{
    padding: 6px 14px;
    border-radius: {RADIUS['pill']}px;
    background-color: {colors['surface_muted']};
    color: {colors['text_muted']};
    font-size: {FONTS['size_xs']}pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ============================================
   BADGES
   ============================================ */

QLabel#badge {{
    padding: 6px 12px;
    border-radius: {RADIUS['pill']}px;
    font-weight: 600;
    font-size: {FONTS['size_xs']}pt;
}}

QLabel#badgePrimary {{
    background-color: {colors['accent_light']};
    color: {colors['accent']};
}}

QLabel#badgeSuccess {{
    background-color: {colors['success_bg']};
    color: {colors['success']};
}}

QLabel#badgeWarning {{
    background-color: {colors['warning_bg']};
    color: {colors['warning']};
}}

QLabel#badgeDanger {{
    background-color: {colors['danger_bg']};
    color: {colors['danger']};
}}

QLabel#badgeInfo {{
    background-color: {colors['info_bg']};
    color: {colors['info']};
}}

/* ============================================
   MODERN GRADIENT CARD
   ============================================ */

QFrame#gradientCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {colors['gradient_start']},
        stop:1 {colors['gradient_end']});
    border: none;
    border-radius: {RADIUS['xl']}px;
    color: white;
}}

QFrame#gradientCard QLabel {{
    color: white;
}}

/* ============================================
   INPUT WITH ICON
   ============================================ */

QLineEdit#searchInput {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['sm']}px;
    padding: 10px 12px 10px 36px;
    color: {colors['text']};
}}

QLineEdit#searchInput:focus {{
    border: 1px solid {colors['accent']};
}}

QLineEdit#searchInput::placeholder {{
    color: {colors['text_muted']};
}}
"""


def get_role_color(role: str) -> str:
    """Получить цвет для роли"""
    colors = get_colors()
    role_colors = {
        "ADMIN": colors["role_admin"],
        "REGISTRAR": colors["role_reg"],
        "LEAD": colors["role_lead"],
        "DOC": colors["role_doc"],
        "NUR": colors["role_nur"],
    }
    return role_colors.get(role, colors["text"])

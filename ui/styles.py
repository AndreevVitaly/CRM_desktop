"""
Современные стили для MED_Desktop
Стиль: Modern Clean Design 2024
"""

# ============================================================================
# ЦВЕТОВАЯ ПАЛИТРА (Светлая тема)
# ============================================================================

COLORS_LIGHT = {
    # Основные цвета (Modern Gray Scale)
    "bg": "#F5F7FA",              # Светлый серо-голубой фон
    "surface": "#FFFFFF",          # Чистый белый
    "surface_muted": "#F1F5F9",    # Светлый серый (контрастный)
    "text": "#0F172A",             # Очень тёмный серый (почти чёрный)
    "text_muted": "#475569",       # Средний серый (контрастный)
    "text_secondary": "#64748B",   # Светлый серый
    
    # Границы и разделители
    "line": "#CBD5E1",             # Контрастная граница
    "line_light": "#E2E8F0",       # Светлая граница
    
    # Акцентные цвета (Modern Indigo)
    "accent": "#4F46E5",           # Индиго (основной акцент)
    "accent_hover": "#4338CA",     # Индиго при наведении
    "accent_strong": "#3730A3",    # Тёмный индиго
    "accent_light": "#E0E7FF",     # Светлый индиго фон
    "accent_soft": "#818CF8",      # Мягкий индиго
    
    # Градиенты
    "gradient_start": "#4F46E5",
    "gradient_end": "#7C3AED",
    
    # Цвета состояний (Modern Palette)
    "success": "#059669",          # Тёмный изумруд
    "success_bg": "#D1FAE5",
    "warning": "#D97706",          # Тёмный янтарь
    "warning_bg": "#FEF3C7",
    "danger": "#DC2626",           # Тёмный красный
    "danger_bg": "#FEE2E2",
    "info": "#2563EB",             # Тёмный синий
    "info_bg": "#DBEAFE",
    
    # Роли (Modern Vibrant)
    "role_admin": "#7C3AED",       # Тёмный фиолетовый
    "role_reg": "#0891B2",         # Тёмный циан
    "role_lead": "#059669",        # Тёмный изумруд
    "role_doc": "#2563EB",         # Тёмный синий
    "role_nur": "#DB2777",         # Тёмный розовый
    
    # Таблицы
    "table_header_bg": "#F1F5F9",
    "table_row_hover": "#E2E8F0",
    "table_row_selected": "#C7D2FE",
    "table_border": "#CBD5E1",
    
    # Навигация
    "nav_bg": "rgba(255, 255, 255, 0.95)",
    
    # Переключатель темы
    "switch_bg": "#CBD5E1",
    "switch_dot": "#FFFFFF",
    
    # Тени (Modern Soft Shadows)
    "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)",
    "shadow_xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
    "shadow_glow": "0 0 20px rgba(99, 102, 241, 0.3)",
}

# ============================================================================
# ЦВЕТОВАЯ ПАЛИТРА (Тёмная тема)
# ============================================================================

COLORS_DARK = {
    # Основные цвета (Modern Dark)
    "bg": "#0F172A",              # Глубокий синий (slate 900)
    "surface": "#1E293B",          # Slate 800
    "surface_muted": "#334155",    # Slate 700
    "text": "#F8FAFC",             # Почти белый
    "text_muted": "#94A3B8",       # Светлый серый
    "text_secondary": "#64748B",   # Средний серый
    
    # Границы
    "line": "#334155",             # Slate 700
    "line_light": "#475569",       # Slate 600
    
    # Акцентные цвета (Bright Indigo)
    "accent": "#818CF8",           # Светлый индиго
    "accent_hover": "#6366F1",     # Индиго
    "accent_strong": "#4F46E5",    # Тёмный индиго
    "accent_light": "#312E81",     # Тёмный индиго фон
    "accent_soft": "#6366F1",      # Индиго
    
    # Градиенты
    "gradient_start": "#818CF8",
    "gradient_end": "#A78BFA",
    
    # Цвета состояний (Neon)
    "success": "#34D399",          # Светлый изумруд
    "success_bg": "#064E3B",
    "warning": "#FBBF24",          # Светлый янтарь
    "warning_bg": "#451A03",
    "danger": "#F87171",           # Светлый красный
    "danger_bg": "#450A0A",
    "info": "#60A5FA",             # Светлый синий
    "info_bg": "#1E3A8A",
    
    # Роли (Neon Vibrant)
    "role_admin": "#A78BFA",       # Светлый фиолетовый
    "role_reg": "#22D3EE",         # Светлый циан
    "role_lead": "#34D399",        # Светлый изумруд
    "role_doc": "#60A5FA",         # Светлый синий
    "role_nur": "#F472B6",         # Светлый розовый
    
    # Таблицы
    "table_header_bg": "#1E293B",
    "table_row_hover": "#334155",
    "table_row_selected": "#312E81",
    "table_border": "#475569",
    
    # Навигация
    "nav_bg": "rgba(15, 23, 42, 0.95)",
    
    # Переключатель темы
    "switch_bg": "#475569",
    "switch_dot": "#F8FAFC",
    
    # Тени (Dark Soft)
    "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
    "shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3)",
    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.3)",
    "shadow_xl": "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4)",
    "shadow_glow": "0 0 20px rgba(129, 140, 248, 0.4)",
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
    background: linear-gradient(135deg, {colors['gradient_start']}, {colors['gradient_end']});
    color: white;
    border: none;
    border-radius: {RADIUS['pill']}px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: {FONTS['size_medium']}pt;
}}

QPushButton:hover {{
    background: linear-gradient(135deg, {colors['accent_hover']}, {colors['gradient_end']});
}}

QPushButton:pressed {{
    background: {colors['accent_hover']};
    padding: 11px 19px 9px 21px;
}}

QPushButton:disabled {{
    background: {colors['line']};
    color: {colors['text_muted']};
}}

QPushButton::menu-indicator {{
    image: none;
}}

/* Вторичная кнопка */
QPushButton#secondaryBtn {{
    background: {colors['surface']};
    border: 1px solid {colors['line']};
    color: {colors['text']};
}}

QPushButton#secondaryBtn:hover {{
    background: {colors['surface_muted']};
    border-color: {colors['accent']};
}}

/* Опасная кнопка */
QPushButton#dangerBtn {{
    background: {colors['danger']};
}}

QPushButton#dangerBtn:hover {{
    background: #DC2626;
}}

/* Кнопка-призрак (ghost) */
QPushButton#ghostBtn {{
    background: transparent;
    border: 1px solid {colors['line']};
    color: {colors['text_muted']};
}}

QPushButton#ghostBtn:hover {{
    color: {colors['text']};
    border-color: {colors['accent']};
}}

/* Акцентная кнопка (outline) */
QPushButton#accentBtn {{
    background: transparent;
    border: 2px solid {colors['accent']};
    color: {colors['accent']};
}}

QPushButton#accentBtn:hover {{
    background: {colors['accent']};
    color: white;
}}

/* ============================================
   ПОЛЯ ВВОДА
   ============================================ */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
    padding: 10px 14px;
    color: {colors['text']};
    selection-background-color: {colors['accent_light']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {colors['accent']};
    padding: 9px 13px;
    outline: none;
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {colors['surface_muted']};
    color: {colors['text_muted']};
}}

QPlainTextEdit {{
    border-radius: {RADIUS['md']}px;
}}

/* ============================================
   ВЫПАДАЮЩИЕ СПИСКИ
   ============================================ */

QComboBox {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['md']}px;
    padding: 10px 14px;
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
    border-radius: {RADIUS['md']}px;
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
    alternate-background-color: {colors['surface_muted']};
    border: 1px solid {colors['table_border']};
    border-radius: {RADIUS['lg']}px;
    selection-background-color: {colors['table_row_selected']};
    gridline-color: {colors['line_light']};
    color: {colors['text']};
}}

QTableWidget::item, QTableView::item {{
    padding: 10px;
    border-radius: {RADIUS['sm']}px;
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {colors['table_row_hover']};
}}

QHeaderView::section {{
    background-color: {colors['table_header_bg']};
    color: {colors['text_muted']};
    padding: 12px;
    border: none;
    border-bottom: 2px solid {colors['line']};
    border-right: 1px solid {colors['line_light']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: {FONTS['size_xs']}pt;
    letter-spacing: 0.05em;
}}

QHeaderView::section:first {{
    border-top-left-radius: {RADIUS['lg']}px;
}}

QHeaderView::section:last {{
    border-top-right-radius: {RADIUS['lg']}px;
    border-right: none;
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

/* ============================================
   КАРТОЧКИ
   ============================================ */

QFrame#card {{
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['xl']}px;
    box-shadow: {colors['shadow']};
}}

QFrame#card.flat {{
    box-shadow: none;
    background-color: {colors['surface_muted']};
}}

QFrame#cardHeader {{
    background-color: transparent;
    border-bottom: 1px solid {colors['line_light']};
    border-top-left-radius: {RADIUS['xl']}px;
    border-top-right-radius: {RADIUS['xl']}px;
    padding: 20px;
}}

QFrame#cardContent {{
    background-color: transparent;
    padding: 20px;
}}

/* ============================================
   ВКЛАДКИ (TABS)
   ============================================ */

QTabWidget::pane {{
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['lg']}px;
    background-color: {colors['surface']};
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {colors['text_muted']};
    padding: 12px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    font-weight: 600;
    border-top-left-radius: {RADIUS['md']}px;
    border-top-right-radius: {RADIUS['md']}px;
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
    spacing: 10px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 2px solid {colors['line']};
    background-color: {colors['surface']};
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border: 2px solid {colors['accent']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['accent']};
    border: 2px solid {colors['accent']};
}}

QRadioButton::indicator {{
    border-radius: 10px;
}}

QRadioButton::indicator:checked {{
    background-color: {colors['accent']};
    border: 2px solid {colors['accent']};
}}

/* ============================================
   ПРОГРЕСС БАР
   ============================================ */

QProgressBar {{
    background-color: {colors['surface_muted']};
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: linear-gradient(90deg, {colors['gradient_start']}, {colors['gradient_end']});
    border-radius: 6px;
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
    background-color: {colors['surface']};
    border: 1px solid {colors['line']};
    border-radius: {RADIUS['lg']}px;
    margin-top: 16px;
    padding-top: 20px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 10px;
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
    border-radius: {RADIUS['md']}px;
    padding: 10px 14px;
    color: {colors['text']};
}}

QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
    border: 2px solid {colors['accent']};
    padding: 9px 13px;
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
    border-radius: {RADIUS['xl']}px;
    box-shadow: {colors['shadow']};
    padding: 24px;
    min-height: 140px;
}}

QFrame#kpiCard:hover {{
    border: 1px solid {colors['accent']};
    box-shadow: {colors['shadow_lg']};
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
    border-radius: {RADIUS['pill']}px;
    padding: 10px 16px 10px 40px;
    color: {colors['text']};
}}

QLineEdit#searchInput:focus {{
    border: 2px solid {colors['accent']};
    padding: 9px 15px 9px 39px;
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

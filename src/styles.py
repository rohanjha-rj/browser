"""
Dynamic Multi-Theme and Accent Color QSS Generator
High-legibility, modern layout and contrast styling
"""

THEME_PALETTES = {
    "dark": {
        "bg_main": "#0f1117",
        "bg_navbar": "#181a24",
        "bg_bookmarks": "#13151f",
        "bg_input": "#222536",
        "bg_tab": "#151722",
        "bg_tab_active": "#222536",
        "bg_tab_hover": "#1d2030",
        "text_main": "#f8fafc",
        "text_muted": "#cbd5e1",
        "border": "#2c3046",
        "border_light": "rgba(255, 255, 255, 0.12)",
        "bookmark_btn_bg": "#1e2235",
        "bookmark_btn_hover": "#2a304a",
    },
    "oled": {
        "bg_main": "#000000",
        "bg_navbar": "#0a0a0e",
        "bg_bookmarks": "#050508",
        "bg_input": "#14141c",
        "bg_tab": "#08080c",
        "bg_tab_active": "#161622",
        "bg_tab_hover": "#101018",
        "text_main": "#ffffff",
        "text_muted": "#94a3b8",
        "border": "#222230",
        "border_light": "rgba(255, 255, 255, 0.08)",
        "bookmark_btn_bg": "#111118",
        "bookmark_btn_hover": "#1c1c28",
    },
    "light": {
        "bg_main": "#f1f5f9",
        "bg_navbar": "#ffffff",
        "bg_bookmarks": "#f8fafc",
        "bg_input": "#e2e8f0",
        "bg_tab": "#e2e8f0",
        "bg_tab_active": "#ffffff",
        "bg_tab_hover": "#edeef4",
        "text_main": "#0f172a",
        "text_muted": "#475569",
        "border": "#cbd5e1",
        "border_light": "rgba(0, 0, 0, 0.08)",
        "bookmark_btn_bg": "#e2e8f0",
        "bookmark_btn_hover": "#cbd5e1",
    },
    "neon": {
        "bg_main": "#070b14",
        "bg_navbar": "#0c1322",
        "bg_bookmarks": "#090f1c",
        "bg_input": "#162238",
        "bg_tab": "#0d172a",
        "bg_tab_active": "#182744",
        "bg_tab_hover": "#121e34",
        "text_main": "#38bdf8",
        "text_muted": "#bae6fd",
        "border": "#1e3a5f",
        "border_light": "rgba(56, 189, 248, 0.25)",
        "bookmark_btn_bg": "#13233c",
        "bookmark_btn_hover": "#1d355c",
    },
    "beige": {
        "bg_main": "#f7f4ed",
        "bg_navbar": "#ffffff",
        "bg_bookmarks": "#faf8f4",
        "bg_input": "#ede7db",
        "bg_tab": "#ede7db",
        "bg_tab_active": "#ffffff",
        "bg_tab_hover": "#f3eee4",
        "text_main": "#26211c",
        "text_muted": "#6b6055",
        "border": "#e6dfd1",
        "border_light": "rgba(0, 0, 0, 0.06)",
        "bookmark_btn_bg": "#ffffff",
        "bookmark_btn_hover": "#ede7db",
    }
}

ACCENT_COLORS = {
    "bronze": "#9e6b43",
    "indigo": "#6366f1",
    "cyan": "#06b6d4",
    "emerald": "#10b981",
    "rose": "#f43f5e",
    "sunset": "#f59e0b",
    "purple": "#a855f7"
}


def get_theme_qss(theme_name="dark", accent_name="indigo") -> str:
    palette = THEME_PALETTES.get(theme_name, THEME_PALETTES["dark"])
    accent = ACCENT_COLORS.get(accent_name, ACCENT_COLORS["indigo"])

    return f"""
    QMainWindow {{
        background-color: {palette["bg_main"]};
        color: {palette["text_main"]};
    }}
    
    /* Navigation Bar */
    QToolBar#NavBar {{
        background-color: {palette["bg_navbar"]};
        border: none;
        border-bottom: 1px solid {palette["border"]};
        padding: 4px 8px;
        spacing: 6px;
        min-height: 42px;
    }}
    
    /* Dedicated Bookmarks Bar */
    QToolBar#BookmarksBar {{
        background-color: {palette["bg_bookmarks"]};
        border: none;
        border-bottom: 1px solid {palette["border"]};
        padding: 3px 10px;
        spacing: 8px;
        min-height: 32px;
    }}
    
    /* Navigation buttons */
    QToolBar#NavBar QToolButton {{
        color: {palette["text_muted"]};
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 5px 9px;
        font-size: 13px;
        font-weight: 600;
    }}
    QToolBar#NavBar QToolButton:hover {{
        background-color: {palette["border_light"]};
        color: {palette["text_main"]};
        border: 1px solid {palette["border"]};
    }}
    QToolBar#NavBar QToolButton:pressed {{
        background-color: {accent};
        color: #ffffff;
    }}
    
    /* Bookmarks Bar Buttons (Pill shape & High contrast text) */
    QToolBar#BookmarksBar QToolButton {{
        color: {palette["text_main"]};
        background-color: {palette["bookmark_btn_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 12px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 500;
    }}
    QToolBar#BookmarksBar QToolButton:hover {{
        background-color: {palette["bookmark_btn_hover"]};
        border-color: {accent};
        color: #ffffff;
    }}

    /* Omnibox / URL Bar */
    QLineEdit#UrlBar {{
        background-color: {palette["bg_input"]};
        border: 1px solid {palette["border"]};
        border-radius: 16px;
        padding: 6px 14px;
        color: {palette["text_main"]};
        font-size: 13px;
        font-weight: 500;
        selection-background-color: {accent};
    }}
    QLineEdit#UrlBar:focus {{
        border: 1.5px solid {accent};
        background-color: {palette["bg_input"]};
    }}

    /* Tab Widget & Tabs */
    QTabWidget {{
        background-color: {palette["bg_main"]};
        border: none;
    }}
    QTabWidget::pane {{
        border: none;
        background-color: {palette["bg_main"]};
    }}
    QTabBar {{
        background-color: {palette["bg_main"]};
        qproperty-drawBase: 0;
        border: none;
    }}
    QTabBar::tab {{
        background-color: {palette["bg_tab"]};
        color: {palette["text_muted"]};
        border: 1px solid {palette["border"]};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 7px 14px;
        margin-right: 3px;
        margin-top: 3px;
        min-width: 100px;
        max-width: 220px;
        font-size: 12px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background-color: {palette["bg_tab_active"]};
        color: {palette["text_main"]};
        border: 1px solid {palette["border"]};
        border-top: 2px solid {accent};
        border-bottom: 1px solid {palette["bg_tab_active"]};
        font-weight: 600;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {palette["bg_tab_hover"]};
        color: {palette["text_main"]};
    }}
    QTabBar::close-button {{
        image: none;
        subcontrol-position: right;
        padding: 2px;
        margin-left: 6px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: transparent;
        border: none;
        max-height: 2px;
    }}
    QProgressBar::chunk {{
        background-color: {accent};
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {palette["bg_main"]};
        color: {palette["text_muted"]};
        font-size: 11px;
        border-top: 1px solid {palette["border"]};
        padding: 2px 6px;
    }}

    /* Context Menus */
    QMenu {{
        background-color: {palette["bg_navbar"]};
        color: {palette["text_main"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        padding: 5px;
    }}
    QMenu::item {{
        padding: 6px 22px;
        border-radius: 4px;
        font-size: 12px;
    }}
    QMenu::item:selected {{
        background-color: {accent};
        color: #ffffff;
    }}

    /* Dialogs & Lists */
    QDialog {{
        background-color: {palette["bg_navbar"]};
        color: {palette["text_main"]};
    }}
    QListWidget {{
        background-color: {palette["bg_main"]};
        border: 1px solid {palette["border"]};
        border-radius: 8px;
        color: {palette["text_main"]};
        padding: 6px;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 2px;
    }}
    QListWidget::item:selected {{
        background-color: {accent};
        color: #ffffff;
    }}
    QPushButton {{
        background-color: {palette["bg_input"]};
        color: {palette["text_main"]};
        border: 1px solid {palette["border"]};
        border-radius: 7px;
        padding: 6px 14px;
        font-weight: 500;
        font-size: 12px;
    }}
    QPushButton:hover {{
        background-color: {accent};
        border-color: {accent};
        color: #ffffff;
    }}
    QComboBox {{
        background-color: {palette["bg_input"]};
        color: {palette["text_main"]};
        border: 1px solid {palette["border"]};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    QComboBox:hover {{
        border-color: {accent};
    }}
    QComboBox QAbstractItemView {{
        background-color: {palette["bg_navbar"]};
        color: {palette["text_main"]};
        border: 1px solid {palette["border"]};
        selection-background-color: {accent};
        selection-color: #ffffff;
    }}
    QLabel {{
        color: {palette["text_main"]};
    }}
    QSplitter::handle {{
        background-color: {palette["border"]};
        width: 3px;
    }}
    """

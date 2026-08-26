import os
import sys
import re
from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QCursor, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QToolBar, QAction, QLineEdit, QProgressBar,
    QStatusBar, QPushButton, QMessageBox, QFileDialog,
    QMenu, QShortcut, QSplitter, QLabel, QComboBox
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
)

from .config import get_start_page_html
from .storage import BookmarkManager, HistoryManager, SettingsManager, SessionManager
from .styles import get_theme_qss
from .adblocker import AdBlockInterceptor
from .dialogs import (
    HistoryDialog, BookmarksDialog, CommandPaletteDialog,
    FindInPageWidget, DownloadsDrawer, ThemeSelectorDialog,
    AISummarizerDialog, PreferencesDialog, SessionManagerDialog
)


# ==========================================
# Floating Picture-in-Picture Player Window
# ==========================================
class FloatingPiPWindow(QMainWindow):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("📺 Picture-in-Picture Player")
        self.resize(480, 270)
        
        self.browser = QWebEngineView(self)
        self.browser.setUrl(QUrl(url))
        self.setCentralWidget(self.browser)
        self.show()


class MainWindow(QMainWindow):
    def __init__(self, is_incognito=False):
        super(MainWindow, self).__init__()
        self.is_incognito = is_incognito
        self.closed_tabs_history = []
        self.downloads_history = []
        self.pinned_tabs = set()
        self.active_workspace = "All"
        self.pip_windows = []

        # Load Settings
        self.settings = SettingsManager.load()
        if self.is_incognito:
            self.current_theme = "oled"
            self.current_accent = "purple"
            self.profile = QWebEngineProfile()  # In-memory off-the-record profile
        else:
            self.current_theme = self.settings.get("theme", "beige")
            self.current_accent = self.settings.get("accent", "bronze")
            self.profile = QWebEngineProfile.defaultProfile()

        # Ad-Blocker Request Interceptor
        self.ad_interceptor = AdBlockInterceptor(self)
        self.ad_interceptor.on_blocked_callback = self.on_ad_blocked
        self.profile.setUrlRequestInterceptor(self.ad_interceptor)
        self.profile.downloadRequested.connect(self.handle_download_requested)

        # Profile Configuration
        web_settings = self.profile.settings()
        web_settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        web_settings.setAttribute(QWebEngineSettings.PdfViewerEnabled, True)

        self.init_ui()
        self.setup_shortcuts()
        
        # Restore session or open default tab
        if not self.is_incognito and self.settings.get("restore_session_on_startup", True):
            last_tabs = SessionManager.get_last_session()
            if last_tabs:
                self.restore_tabs(last_tabs)
            else:
                self.add_new_tab(label="New Tab")
        else:
            self.add_new_tab(label="New Tab")

        self.showMaximized()

    def _start_html(self):
        return get_start_page_html(self.current_theme, self.current_accent)

    def init_ui(self):
        title = "🛡️ Incognito - My Cool Browser" if self.is_incognito else "My Cool Browser Pro"
        self.setWindowTitle(title)
        self.setMinimumSize(850, 600)

        # Central Widget & Main Layout
        self.central_container = QWidget()
        self.setCentralWidget(self.central_container)
        self.main_layout = QVBoxLayout(self.central_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. Navigation Toolbar
        # -------------------------------------------------------------
        self.navbar = QToolBar("Navigation")
        self.navbar.setObjectName("NavBar")
        self.navbar.setMovable(False)
        self.navbar.setFloatable(False)
        self.addToolBar(self.navbar)

        # Back / Forward / Reload / Home
        self.back_btn = QAction("◀", self)
        self.back_btn.setToolTip("Back (Alt+Left)")
        self.back_btn.triggered.connect(self.navigate_back)
        self.navbar.addAction(self.back_btn)

        self.forward_btn = QAction("▶", self)
        self.forward_btn.setToolTip("Forward (Alt+Right)")
        self.forward_btn.triggered.connect(self.navigate_forward)
        self.navbar.addAction(self.forward_btn)

        self.reload_btn = QAction("🔄", self)
        self.reload_btn.setToolTip("Reload (Ctrl+R / F5)")
        self.reload_btn.triggered.connect(self.navigate_reload)
        self.navbar.addAction(self.reload_btn)

        self.home_btn = QAction("🏠", self)
        self.home_btn.setToolTip("Home")
        self.home_btn.triggered.connect(self.navigate_home)
        self.navbar.addAction(self.home_btn)

        # Omnibox (Address & Search Bar)
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("UrlBar")
        self.url_bar.setPlaceholderText("Search with Google, keywords (yt, gh, w), math, or enter URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.textChanged.connect(self.on_url_bar_text_changed)

        # Lock / Favicon Icon
        self.lock_action = self.url_bar.addAction(QIcon(), QLineEdit.LeadingPosition)
        self.lock_action.setToolTip("Security status")
        self.update_url_lock_icon(False)

        # Shield & Bookmark Icons
        self.shield_action = self.url_bar.addAction(QIcon(), QLineEdit.TrailingPosition)
        self.shield_action.setText("🛡️")
        self.shield_action.setToolTip("Ad-Blocker: Active (0 blocked)")
        self.shield_action.triggered.connect(self.toggle_adblocker)

        self.star_action = self.url_bar.addAction(QIcon(), QLineEdit.TrailingPosition)
        self.star_action.setToolTip("Bookmark this page (Ctrl+D)")
        self.star_action.triggered.connect(self.toggle_bookmark)
        self.update_star_icon(False)

        self.navbar.addWidget(self.url_bar)

        # AI Assistant Button
        self.ai_btn = QAction("🤖 AI", self)
        self.ai_btn.setToolTip("AI Page Assistant & Summarizer (Ctrl+Shift+A)")
        self.ai_btn.triggered.connect(self.open_ai_summarizer)
        self.navbar.addAction(self.ai_btn)

        # Screenshot Tool Button
        self.shot_btn = QAction("📸", self)
        self.shot_btn.setToolTip("Capture Page Screenshot (Ctrl+Shift+S)")
        self.shot_btn.triggered.connect(self.take_page_screenshot)
        self.navbar.addAction(self.shot_btn)

        # Split View Button
        self.split_btn = QAction("🔲 Split", self)
        self.split_btn.setToolTip("Split-Screen Dual View (Ctrl+Alt+S)")
        self.split_btn.triggered.connect(self.toggle_split_view)
        self.navbar.addAction(self.split_btn)

        # Command Palette Button
        self.palette_btn = QAction("⚡", self)
        self.palette_btn.setToolTip("Command Palette (Ctrl+K)")
        self.palette_btn.triggered.connect(self.show_command_palette)
        self.navbar.addAction(self.palette_btn)

        # More Menu
        self.menu_btn = QAction("⋮", self)
        self.menu_btn.setToolTip("Settings & Preferences")
        self.menu_btn.triggered.connect(self.show_more_menu)
        self.navbar.addAction(self.menu_btn)

        # -------------------------------------------------------------
        # 2. Dedicated Bookmarks Bar & Workspaces
        # -------------------------------------------------------------
        if not self.is_incognito:
            self.addToolBarBreak()
            self.bookmarks_bar = QToolBar("Bookmarks Bar")
            self.bookmarks_bar.setObjectName("BookmarksBar")
            self.bookmarks_bar.setMovable(False)
            self.bookmarks_bar.setFloatable(False)
            self.addToolBar(self.bookmarks_bar)

            # Workspace Selector
            ws_label = QLabel(" 🗂️ ")
            ws_label.setStyleSheet("color: #9e6b43; font-weight: bold;")
            self.bookmarks_bar.addWidget(ws_label)

            self.ws_combo = QComboBox()
            self.ws_combo.addItems(["All", "General", "Work", "Personal", "Dev"])
            self.ws_combo.currentTextChanged.connect(self.on_workspace_changed)
            self.ws_combo.setFixedWidth(90)
            self.bookmarks_bar.addWidget(self.ws_combo)

            self.bookmarks_bar.addSeparator()
            self.load_bookmarks_bar()

        # -------------------------------------------------------------
        # 3. Thin Loading Progress Bar
        # -------------------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)

        # In-Page Find Bar (Ctrl+F)
        self.find_widget = FindInPageWidget(self, self.current_browser)
        self.find_widget.hide()
        self.main_layout.addWidget(self.find_widget)

        # -------------------------------------------------------------
        # 4. Tab Widget & Splitter
        # -------------------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setIconSize(QSize(16, 16))
        self.tab_widget.tabBar().setExpanding(False)
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.current_tab_changed)
        self.tab_widget.tabBarDoubleClicked.connect(self.tab_bar_double_clicked)

        # Clean "+" Button for Tab Bar
        self.new_tab_btn = QPushButton(" ＋ ")
        self.new_tab_btn.setObjectName("NewTabBtn")
        self.new_tab_btn.setToolTip("Open New Tab (Ctrl+T)")
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        self.tab_widget.setCornerWidget(self.new_tab_btn, Qt.TopRightCorner)

        # Content Splitter
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.content_splitter.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.content_splitter)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        incognito_text = " • 🕶️ Incognito Mode" if self.is_incognito else ""
        self.status.showMessage(f"Ready{incognito_text}", 3000)

        # Apply Global Theme
        self.apply_theme()

    def apply_theme(self):
        qss = get_theme_qss(self.current_theme, self.current_accent)
        self.setStyleSheet(qss)

    def setup_shortcuts(self):
        # AI Summarizer: Ctrl+Shift+A
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, self.open_ai_summarizer)
        # Screenshot: Ctrl+Shift+S
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.take_page_screenshot)
        # Open Local File / PDF: Ctrl+O
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_local_file)
        # Session Manager: Ctrl+Shift+O
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.open_session_manager)
        # Pin Tab: Ctrl+P
        QShortcut(QKeySequence("Ctrl+P"), self, self.toggle_pin_current_tab)
        # Picture-in-Picture: Ctrl+Shift+P
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, self.open_pip_player)
        # Command Palette: Ctrl+K
        QShortcut(QKeySequence("Ctrl+K"), self, self.show_command_palette)
        # Find in Page: Ctrl+F
        QShortcut(QKeySequence("Ctrl+F"), self, self.show_find_widget)
        # Downloads: Ctrl+J
        QShortcut(QKeySequence("Ctrl+J"), self, self.show_downloads_drawer)
        # Incognito: Ctrl+Shift+N
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self.open_incognito_window)
        # Split View: Ctrl+Alt+S
        QShortcut(QKeySequence("Ctrl+Alt+S"), self, self.toggle_split_view)
        # New Tab: Ctrl+T
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_new_tab())
        # Close Tab: Ctrl+W
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tab_widget.currentIndex()))
        # Reopen Closed Tab: Ctrl+Shift+T
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.reopen_closed_tab)
        # Reload: Ctrl+R / F5
        QShortcut(QKeySequence("Ctrl+R"), self, self.navigate_reload)
        QShortcut(QKeySequence("F5"), self, self.navigate_reload)
        # Hard Reload: Ctrl+Shift+R
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, lambda: self.navigate_reload(bypass_cache=True))
        # Focus Address Bar: Ctrl+L / Alt+D
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        QShortcut(QKeySequence("Alt+D"), self, lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        # History: Ctrl+H
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_history_dialog)
        # Bookmarks Bar: Ctrl+B
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_bookmarks_bar)
        # Add Bookmark: Ctrl+D
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_bookmark)
        # Zoom: Ctrl+Plus, Ctrl+Minus, Ctrl+0
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)
        # Fullscreen: F11
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        # Tab cycling
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.prev_tab)

        # Tab jumps Ctrl+1 to Ctrl+9
        for num in range(1, 10):
            QShortcut(QKeySequence(f"Ctrl+{num}"), self, lambda n=num-1: self.tab_widget.setCurrentIndex(n) if n < self.tab_widget.count() else None)

    # ==========================================
    # Tab Management & Workspaces
    # ==========================================
    def current_browser(self):
        return self.tab_widget.currentWidget()

    def add_new_tab(self, qurl=None, label="New Tab", workspace="General"):
        page = QWebEnginePage(self.profile, self)
        browser = QWebEngineView()
        browser.setPage(page)
        browser.setProperty("workspace", workspace)
        browser.setProperty("is_muted", False)

        page.linkHovered.connect(lambda url: self.status.showMessage(url, 2000) if url else self.status.clearMessage())

        browser.urlChanged.connect(lambda url, b=browser: self.on_url_changed(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.on_title_changed(title, b))
        browser.iconChanged.connect(lambda icon, b=browser: self.on_icon_changed(icon, b))
        browser.loadProgress.connect(lambda progress, b=browser: self.on_load_progress(progress, b))
        browser.loadFinished.connect(lambda ok, b=browser: self.on_load_finished(ok, b))

        i = self.tab_widget.addTab(browser, label)
        self.tab_widget.setCurrentIndex(i)

        if qurl is None:
            browser.setHtml(self._start_html(), QUrl("about:blank"))
        elif isinstance(qurl, str):
            browser.setUrl(QUrl(qurl))
        else:
            browser.setUrl(qurl)

        return browser

    def tab_bar_double_clicked(self, index):
        if index == -1:
            self.add_new_tab()

    def close_tab(self, index):
        if self.tab_widget.count() < 1 or index < 0 or index >= self.tab_widget.count():
            return
        
        # Don't close pinned tabs directly
        if index in self.pinned_tabs:
            self.status.showMessage("📌 This tab is pinned. Unpin it first to close.", 3000)
            return

        browser = self.tab_widget.widget(index)
        if browser:
            current_url = browser.url().toString()
            if current_url and current_url != "about:blank" and not self.is_incognito:
                self.closed_tabs_history.append(current_url)

        if self.tab_widget.count() == 1:
            browser.setHtml(self._start_html(), QUrl("about:blank"))
            self.tab_widget.setTabText(0, "New Tab")
            self.tab_widget.setTabIcon(0, QIcon())
            self.url_bar.clear()
            return

        self.tab_widget.removeTab(index)
        browser.deleteLater()

    def show_tab_context_menu(self, pos):
        index = self.tab_widget.tabBar().tabAt(pos)
        if index == -1:
            return

        menu = QMenu(self)
        is_pinned = index in self.pinned_tabs
        pin_act = menu.addAction("📌 Unpin Tab" if is_pinned else "📌 Pin Tab")
        pin_act.triggered.connect(lambda: self.toggle_pin_tab(index))

        browser = self.tab_widget.widget(index)
        is_muted = browser.property("is_muted") if browser else False
        mute_act = menu.addAction("🔊 Unmute Tab" if is_muted else "🔇 Mute Tab")
        mute_act.triggered.connect(lambda: self.toggle_mute_tab(index))

        menu.addSeparator()

        pip_act = menu.addAction("📺 Open in Picture-in-Picture")
        pip_act.triggered.connect(lambda: self.open_pip_player(index))

        dup_act = menu.addAction("📑 Duplicate Tab")
        dup_act.triggered.connect(lambda: self.duplicate_tab(index))

        menu.addSeparator()

        close_act = menu.addAction("✕ Close Tab")
        close_act.triggered.connect(lambda: self.close_tab(index))

        menu.exec_(self.tab_widget.tabBar().mapToGlobal(pos))

    def toggle_pin_current_tab(self):
        self.toggle_pin_tab(self.tab_widget.currentIndex())

    def toggle_pin_tab(self, index):
        if index in self.pinned_tabs:
            self.pinned_tabs.remove(index)
            title = self.tab_widget.widget(index).title() or "Tab"
            self.tab_widget.setTabText(index, title[:16])
            self.status.showMessage("Tab unpinned", 2000)
        else:
            self.pinned_tabs.add(index)
            self.tab_widget.setTabText(index, "📌")
            self.status.showMessage("Tab pinned", 2000)

    def toggle_mute_current_tab(self):
        self.toggle_mute_tab(self.tab_widget.currentIndex())

    def toggle_mute_tab(self, index):
        browser = self.tab_widget.widget(index)
        if browser:
            curr_muted = browser.property("is_muted") or False
            new_muted = not curr_muted
            browser.setProperty("is_muted", new_muted)
            browser.page().setAudioMuted(new_muted)
            status_text = "Muted 🔇" if new_muted else "Unmuted 🔊"
            self.status.showMessage(f"Tab audio: {status_text}", 2000)

    def duplicate_tab(self, index):
        browser = self.tab_widget.widget(index)
        if browser:
            self.add_new_tab(browser.url())

    def on_workspace_changed(self, ws_name):
        self.active_workspace = ws_name
        self.status.showMessage(f"Workspace: {ws_name}", 2000)

    def get_all_tabs_data(self):
        tabs = []
        for i in range(self.tab_widget.count()):
            b = self.tab_widget.widget(i)
            if b:
                url_str = b.url().toString()
                if url_str and url_str != "about:blank":
                    tabs.append({"title": b.title(), "url": url_str, "workspace": b.property("workspace") or "General"})
        return tabs

    def restore_tabs(self, tabs_data):
        self.tab_widget.clear()
        for tab_info in tabs_data:
            url = tab_info.get("url")
            title = tab_info.get("title", "Restored Tab")
            ws = tab_info.get("workspace", "General")
            self.add_new_tab(qurl=url, label=title[:16], workspace=ws)
        if self.tab_widget.count() == 0:
            self.add_new_tab()

    def reopen_closed_tab(self):
        if self.closed_tabs_history:
            last_url = self.closed_tabs_history.pop()
            self.add_new_tab(QUrl(last_url))

    def current_tab_changed(self, index):
        browser = self.current_browser()
        if browser:
            url = browser.url()
            url_str = url.toString()
            if url_str == "about:blank":
                self.url_bar.clear()
                self.update_star_icon(False)
                self.update_url_lock_icon(False)
            else:
                self.url_bar.setText(url_str)
                self.update_star_icon(BookmarkManager.is_bookmarked(url_str))
                self.update_url_lock_icon(url_str.startswith("https://"))
            
            title = browser.title()
            self.update_window_title(title)
            self.update_nav_buttons()

    def next_tab(self):
        if self.tab_widget.count() > 0:
            idx = (self.tab_widget.currentIndex() + 1) % self.tab_widget.count()
            self.tab_widget.setCurrentIndex(idx)

    def prev_tab(self):
        if self.tab_widget.count() > 0:
            idx = (self.tab_widget.currentIndex() - 1) % self.tab_widget.count()
            self.tab_widget.setCurrentIndex(idx)

    def toggle_tabs_orientation(self):
        is_vert = self.tab_widget.tabPosition() == QTabWidget.West
        if is_vert:
            self.tab_widget.setTabPosition(QTabWidget.North)
            self.status.showMessage("Horizontal Tabs enabled", 2000)
        else:
            self.tab_widget.setTabPosition(QTabWidget.West)
            self.status.showMessage("Vertical Sidebar Tabs enabled", 2000)

    # ==========================================
    # Split-Screen & Picture-in-Picture
    # ==========================================
    def toggle_split_view(self):
        if self.content_splitter.count() > 1:
            widget = self.content_splitter.widget(1)
            widget.setParent(None)
            widget.deleteLater()
            self.status.showMessage("Split-Screen closed", 2000)
        else:
            split_browser = QWebEngineView()
            split_browser.setPage(QWebEnginePage(self.profile, self))
            split_browser.setUrl(QUrl("https://www.google.com"))
            self.content_splitter.addWidget(split_browser)
            self.content_splitter.setSizes([self.width() // 2, self.width() // 2])
            self.status.showMessage("Split-Screen enabled", 2000)

    def open_pip_player(self, index=None):
        idx = index if index is not None else self.tab_widget.currentIndex()
        browser = self.tab_widget.widget(idx)
        if browser:
            url_str = browser.url().toString()
            if url_str and url_str != "about:blank":
                pip_win = FloatingPiPWindow(url_str, self)
                self.pip_windows.append(pip_win)
                self.status.showMessage("Picture-in-Picture window opened", 3000)

    # ==========================================
    # Full-Page Screenshot & Local Files
    # ==========================================
    def take_page_screenshot(self):
        browser = self.current_browser()
        if not browser:
            return

        pixmap = browser.grab()
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "screenshot.png")
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", default_path, "PNG Image (*.png);;JPEG Image (*.jpg)")
        if file_path:
            pixmap.save(file_path)
            self.status.showMessage(f"📸 Screenshot saved: {os.path.basename(file_path)}", 4000)

    def open_local_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File / PDF", "", "Supported Files (*.html *.htm *.pdf *.txt *.png *.jpg);;All Files (*.*)"
        )
        if file_path:
            self.add_new_tab(QUrl.fromLocalFile(file_path), label=os.path.basename(file_path))

    # ==========================================
    # Omnibox & Keyword Search Prefixes
    # ==========================================
    def on_url_bar_text_changed(self, text):
        t = text.strip()
        # Live math preview in status bar
        if t and re.match(r'^[0-9\.\+\-\*\/\(\)\%\s\^]+$', t):
            try:
                res = eval(t.replace('^', '**'), {"__builtins__": None}, {})
                self.status.showMessage(f"🔢 Calculation = {res}", 1500)
            except Exception:
                pass

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        
        browser = self.current_browser()
        if not browser:
            return

        # 1. Keyword search prefixes
        keyword_map = {
            "yt ": "https://www.youtube.com/results?search_query=",
            "gh ": "https://github.com/search?q=",
            "w ": "https://en.wikipedia.org/wiki/Special:Search?search=",
            "r ": "https://www.reddit.com/search/?q=",
            "ddg ": "https://duckduckgo.com/?q=",
            "g ": "https://www.google.com/search?q="
        }
        for prefix, target_url in keyword_map.items():
            if text.lower().startswith(prefix):
                query = text[len(prefix):].strip()
                browser.setUrl(QUrl(f"{target_url}{query}"))
                return

        # 2. Math calculations check
        if re.match(r'^[0-9\.\+\-\*\/\(\)\%\s\^]+$', text):
            try:
                res = eval(text.replace('^', '**'), {"__builtins__": None}, {})
                self.status.showMessage(f"Calculation Result: {res}", 5000)
                self.url_bar.setText(f"{res}")
                return
            except Exception:
                pass

        # 3. Standard URL / Search evaluation
        is_ip = all(part.isdigit() and 0 <= int(part) <= 255 for part in text.split('.') if part) and len(text.split('.')) == 4
        is_localhost = text.startswith("localhost") or text.startswith("127.0.0.1")
        has_tld = '.' in text and ' ' not in text and not text.endswith('.')

        if text.startswith("http://") or text.startswith("https://") or text.startswith("file:///"):
            qurl = QUrl(text)
        elif is_ip or is_localhost or has_tld:
            qurl = QUrl("https://" + text)
        else:
            qurl = QUrl(f"https://www.google.com/search?q={text}")

        browser.setUrl(qurl)

    def navigate_home(self):
        browser = self.current_browser()
        if browser:
            browser.setHtml(self._start_html(), QUrl("about:blank"))
            self.url_bar.clear()

    def navigate_back(self):
        browser = self.current_browser()
        if browser:
            browser.back()

    def navigate_forward(self):
        browser = self.current_browser()
        if browser:
            browser.forward()

    def navigate_reload(self, bypass_cache=False):
        browser = self.current_browser()
        if browser:
            if bypass_cache:
                browser.page().action(QWebEnginePage.ReloadAndBypassCache).trigger()
            else:
                browser.reload()

    def update_nav_buttons(self):
        browser = self.current_browser()
        if browser and browser.history():
            self.back_btn.setEnabled(browser.history().canGoBack())
            self.forward_btn.setEnabled(browser.history().canGoForward())

    # ==========================================
    # Events & Favicons
    # ==========================================
    def on_url_changed(self, url, browser):
        if browser == self.current_browser():
            url_str = url.toString()
            if url_str == "about:blank":
                self.url_bar.clear()
                self.update_star_icon(False)
                self.update_url_lock_icon(False)
            else:
                self.url_bar.setText(url_str)
                self.update_star_icon(BookmarkManager.is_bookmarked(url_str))
                self.update_url_lock_icon(url_str.startswith("https://"))
            self.update_nav_buttons()

    def on_title_changed(self, title, browser):
        index = self.tab_widget.indexOf(browser)
        if index != -1:
            if index in self.pinned_tabs:
                self.tab_widget.setTabText(index, "📌")
            else:
                display_title = title if title else "Untitled"
                short_title = (display_title[:16] + '...') if len(display_title) > 18 else display_title
                self.tab_widget.setTabText(index, short_title)
            self.tab_widget.setTabToolTip(index, title)

        if browser == self.current_browser():
            self.update_window_title(title)

    def on_icon_changed(self, icon, browser):
        index = self.tab_widget.indexOf(browser)
        if index != -1 and not icon.isNull():
            self.tab_widget.setTabIcon(index, icon)
            if browser == self.current_browser():
                self.lock_action.setIcon(icon)

    def update_url_lock_icon(self, is_https):
        if is_https:
            self.lock_action.setText("🔒")
            self.lock_action.setToolTip("Secure HTTPS connection")
        else:
            self.lock_action.setText("🌐")
            self.lock_action.setToolTip("Web page")

    def update_window_title(self, title):
        prefix = "🕶️ Private - " if self.is_incognito else ""
        if title and title != "about:blank":
            self.setWindowTitle(f"{prefix}{title} - My Cool Browser Pro")
        else:
            self.setWindowTitle(f"{prefix}My Cool Browser Pro")

    def on_load_progress(self, progress, browser):
        if browser == self.current_browser():
            self.progress_bar.show()
            self.progress_bar.setValue(progress)

    def on_load_finished(self, ok, browser):
        if browser == self.current_browser():
            self.progress_bar.hide()
            self.update_nav_buttons()

        url_str = browser.url().toString()
        title = browser.title()
        if ok and url_str and url_str != "about:blank" and not self.is_incognito:
            HistoryManager.add(title, url_str)

    def on_ad_blocked(self, count):
        self.shield_action.setToolTip(f"Ad-Blocker: Active ({count} blocked)")

    # ==========================================
    # Dialogs & Features
    # ==========================================
    def open_ai_summarizer(self):
        dialog = AISummarizerDialog(self, browser_view=self.current_browser())
        dialog.exec_()

    def open_session_manager(self):
        dialog = SessionManagerDialog(self, browser_window=self)
        dialog.exec_()

    def open_preferences_dialog(self):
        dialog = PreferencesDialog(self, on_settings_changed=self.on_preferences_saved)
        dialog.exec_()

    def on_preferences_saved(self, settings):
        self.settings = settings
        self.status.showMessage("Preferences saved successfully!", 3000)

    def show_command_palette(self):
        palette = CommandPaletteDialog(self, browser_window=self)
        palette.exec_()

    def show_find_widget(self):
        self.find_widget.show()
        self.find_widget.input.setFocus()
        self.find_widget.input.selectAll()

    def show_downloads_drawer(self):
        drawer = DownloadsDrawer(self, downloads_list=self.downloads_history)
        drawer.exec_()

    def show_theme_dialog(self):
        dialog = ThemeSelectorDialog(
            self,
            current_theme=self.current_theme,
            current_accent=self.current_accent,
            on_theme_change=self.set_theme
        )
        dialog.exec_()

    def set_theme(self, theme_key, accent_key):
        self.current_theme = theme_key
        self.current_accent = accent_key
        self.apply_theme()
        for i in range(self.tab_widget.count()):
            tab_browser = self.tab_widget.widget(i)
            if tab_browser and tab_browser.url().toString() == "about:blank":
                tab_browser.setHtml(self._start_html(), QUrl("about:blank"))
        self.status.showMessage(f"Theme updated: {theme_key} / {accent_key}", 3000)

    def open_incognito_window(self):
        incognito_win = MainWindow(is_incognito=True)
        self.incognito_windows.append(incognito_win)

    def toggle_adblocker(self):
        is_enabled = self.ad_interceptor.toggle()
        if is_enabled:
            self.shield_action.setText("🛡️")
            self.shield_action.setToolTip(f"Ad-Blocker: Active ({self.ad_interceptor.blocked_count} blocked)")
            self.status.showMessage("Ad-Blocker Enabled", 2000)
        else:
            self.shield_action.setText("⚪")
            self.shield_action.setToolTip("Ad-Blocker: Disabled")
            self.status.showMessage("Ad-Blocker Disabled", 2000)

    def update_star_icon(self, is_bookmarked):
        if is_bookmarked:
            self.star_action.setText("★")
            self.star_action.setToolTip("Remove bookmark (Ctrl+D)")
        else:
            self.star_action.setText("☆")
            self.star_action.setToolTip("Bookmark this page (Ctrl+D)")

    def toggle_bookmark(self):
        browser = self.current_browser()
        if not browser or self.is_incognito:
            return
        
        url_str = browser.url().toString()
        title = browser.title()
        if not url_str or url_str == "about:blank":
            return

        if BookmarkManager.is_bookmarked(url_str):
            BookmarkManager.remove(url_str)
            self.update_star_icon(False)
            self.status.showMessage("Bookmark removed", 3000)
        else:
            BookmarkManager.add(title, url_str)
            self.update_star_icon(True)
            self.status.showMessage("Bookmark added!", 3000)

        if hasattr(self, "bookmarks_bar"):
            self.load_bookmarks_bar()

    def toggle_bookmarks_bar(self):
        if hasattr(self, "bookmarks_bar"):
            self.bookmarks_bar.setVisible(not self.bookmarks_bar.isVisible())

    def load_bookmarks_bar(self):
        if not hasattr(self, "bookmarks_bar"):
            return
        
        bookmarks = BookmarkManager.load()
        for bm in bookmarks:
            title = bm.get("title", "Bookmark")
            url = bm.get("url", "")
            action = QAction(f"{title}", self)
            action.setToolTip(url)
            action.triggered.connect(lambda checked, u=url: self.open_url_in_current_tab(u))
            self.bookmarks_bar.addAction(action)

    def open_url_in_current_tab(self, url):
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))

    def show_bookmarks_dialog(self):
        dialog = BookmarksDialog(
            self,
            on_open_url=self.open_url_in_current_tab,
            on_bookmarks_changed=self.load_bookmarks_bar
        )
        dialog.exec_()

    def show_history_dialog(self):
        dialog = HistoryDialog(self, on_open_url=self.open_url_in_current_tab)
        dialog.exec_()

    def handle_download_requested(self, download_item):
        filename = download_item.suggestedFileName()
        default_path = os.path.join(
            os.path.expanduser("~"), "Downloads", filename
        )
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save File", default_path
        )
        if filepath:
            download_item.setPath(filepath)
            download_item.accept()
            download_record = {
                "filename": filename,
                "path": filepath,
                "status": "Downloading..."
            }
            self.downloads_history.append(download_record)
            self.status.showMessage(f"Downloading: {filename}...", 5000)

            def on_finished():
                download_record["status"] = "Completed"
                self.status.showMessage(f"Download complete: {filename}", 6000)

            download_item.finished.connect(on_finished)
        else:
            download_item.cancel()

    def show_more_menu(self):
        menu = QMenu(self)
        
        ai_act = menu.addAction("🤖 AI Page Summarizer (Ctrl Shift A)")
        ai_act.triggered.connect(self.open_ai_summarizer)

        shot_act = menu.addAction("📸 Capture Screenshot (Ctrl Shift S)")
        shot_act.triggered.connect(self.take_page_screenshot)

        pip_act = menu.addAction("📺 Picture-in-Picture (Ctrl Shift P)")
        pip_act.triggered.connect(lambda: self.open_pip_player())

        file_act = menu.addAction("📂 Open File / PDF (Ctrl O)")
        file_act.triggered.connect(self.open_local_file)

        session_act = menu.addAction("🗂️ Manage Saved Sessions (Ctrl Shift O)")
        session_act.triggered.connect(self.open_session_manager)

        pref_act = menu.addAction("⚙️ Preferences & Privacy Settings")
        pref_act.triggered.connect(self.open_preferences_dialog)

        menu.addSeparator()

        palette_act = menu.addAction("⚡ Command Palette (Ctrl K)")
        palette_act.triggered.connect(self.show_command_palette)

        find_act = menu.addAction("🔍 Find in Page (Ctrl F)")
        find_act.triggered.connect(self.show_find_widget)

        downloads_act = menu.addAction("📥 Downloads Hub (Ctrl J)")
        downloads_act.triggered.connect(self.show_downloads_drawer)

        incognito_act = menu.addAction("🕶️ New Incognito Window (Ctrl Shift N)")
        incognito_act.triggered.connect(self.open_incognito_window)

        theme_act = menu.addAction("🎨 Theme & Accent Customizer")
        theme_act.triggered.connect(self.show_theme_dialog)

        menu.addSeparator()

        history_act = menu.addAction("🕒 History (Ctrl H)")
        history_act.triggered.connect(self.show_history_dialog)

        bm_act = menu.addAction("⭐ Bookmarks (Ctrl B)")
        bm_act.triggered.connect(self.show_bookmarks_dialog)

        menu.exec_(QCursor.pos())

    def zoom_in(self):
        browser = self.current_browser()
        if browser:
            factor = round(browser.zoomFactor() + 0.1, 2)
            if factor <= 3.0:
                browser.setZoomFactor(factor)
                self.status.showMessage(f"Zoom: {int(factor * 100)}%", 2000)

    def zoom_out(self):
        browser = self.current_browser()
        if browser:
            factor = round(browser.zoomFactor() - 0.1, 2)
            if factor >= 0.25:
                browser.setZoomFactor(factor)
                self.status.showMessage(f"Zoom: {int(factor * 100)}%", 2000)

    def zoom_reset(self):
        browser = self.current_browser()
        if browser:
            browser.setZoomFactor(1.0)
            self.status.showMessage("Zoom: 100%", 2000)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        # Auto-save session
        if not self.is_incognito:
            tabs_data = self.get_all_tabs_data()
            SessionManager.save_last_session(tabs_data)

            # Auto-clear on exit if enabled in settings
            if self.settings.get("auto_clear_on_exit", False):
                HistoryManager.clear()

        event.accept()

import os
import sys
from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QCursor, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QToolBar, QAction, QLineEdit, QProgressBar,
    QStatusBar, QPushButton, QMessageBox, QFileDialog,
    QMenu, QShortcut, QSplitter, QLabel
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
)

from .config import get_start_page_html
from .storage import BookmarkManager, HistoryManager
from .styles import get_theme_qss
from .adblocker import AdBlockInterceptor
from .dialogs import (
    HistoryDialog, BookmarksDialog, CommandPaletteDialog,
    FindInPageWidget, DownloadsDrawer, ThemeSelectorDialog
)


class MainWindow(QMainWindow):
    def __init__(self, is_incognito=False):
        super(MainWindow, self).__init__()
        self.is_incognito = is_incognito
        self.closed_tabs_history = []
        self.downloads_history = []
        self.current_theme = "dark"
        self.current_accent = "indigo"
        self.is_vertical_tabs = False
        self.is_split_view = False
        self.incognito_windows = []

        # Setup Profile (Normal or Private/Off-the-Record)
        if self.is_incognito:
            self.profile = QWebEngineProfile()  # Off the record profile
            self.current_theme = "oled"
            self.current_accent = "purple"
        else:
            self.profile = QWebEngineProfile.defaultProfile()

        # Ad-Blocker Request Interceptor
        self.ad_interceptor = AdBlockInterceptor(self)
        self.ad_interceptor.on_blocked_callback = self.on_ad_blocked
        self.profile.setUrlRequestInterceptor(self.ad_interceptor)
        self.profile.downloadRequested.connect(self.handle_download_requested)

        # Profile Settings
        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)

        self.init_ui()
        self.setup_shortcuts()
        self.add_new_tab(label="New Tab")
        self.showMaximized()

    def init_ui(self):
        title = "🛡️ Incognito - My Cool Browser" if self.is_incognito else "My Cool Browser"
        self.setWindowTitle(title)
        self.setMinimumSize(850, 600)

        # Central Widget & Main Layout
        self.central_container = QWidget()
        self.setCentralWidget(self.central_container)
        self.main_layout = QVBoxLayout(self.central_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. Navigation Toolbar (Dedicated Top Row)
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
        self.url_bar.setPlaceholderText("Search with Google or enter URL (Ctrl+L)...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        # Lock / Favicon Icon in URL Bar
        self.lock_action = self.url_bar.addAction(QIcon(), QLineEdit.LeadingPosition)
        self.lock_action.setToolTip("Security status")
        self.update_url_lock_icon(False)

        # Shield & Bookmark Icons in URL Bar
        self.shield_action = self.url_bar.addAction(QIcon(), QLineEdit.TrailingPosition)
        self.shield_action.setText("🛡️")
        self.shield_action.setToolTip("Ad-Blocker: Active (0 blocked)")
        self.shield_action.triggered.connect(self.toggle_adblocker)

        self.star_action = self.url_bar.addAction(QIcon(), QLineEdit.TrailingPosition)
        self.star_action.setToolTip("Bookmark this page (Ctrl+D)")
        self.star_action.triggered.connect(self.toggle_bookmark)
        self.update_star_icon(False)

        self.navbar.addWidget(self.url_bar)

        # Power Feature Actions in Navbar
        self.palette_btn = QAction("⚡", self)
        self.palette_btn.setToolTip("Command Palette (Ctrl+K)")
        self.palette_btn.triggered.connect(self.show_command_palette)
        self.navbar.addAction(self.palette_btn)

        self.split_btn = QAction("🔲 Split", self)
        self.split_btn.setToolTip("Split-Screen Dual View (Ctrl+Alt+S)")
        self.split_btn.triggered.connect(self.toggle_split_view)
        self.navbar.addAction(self.split_btn)

        self.vtab_btn = QAction("📑 Sidebar", self)
        self.vtab_btn.setToolTip("Toggle Vertical Sidebar Tabs")
        self.vtab_btn.triggered.connect(self.toggle_tabs_orientation)
        self.navbar.addAction(self.vtab_btn)

        self.menu_btn = QAction("⋮", self)
        self.menu_btn.setToolTip("Settings & Menus")
        self.menu_btn.triggered.connect(self.show_more_menu)
        self.navbar.addAction(self.menu_btn)

        # -------------------------------------------------------------
        # 2. Dedicated Bookmarks Bar (Separate Row below Navigation)
        # -------------------------------------------------------------
        if not self.is_incognito:
            self.addToolBarBreak()  # Force bookmarks bar onto its own distinct row!
            self.bookmarks_bar = QToolBar("Bookmarks Bar")
            self.bookmarks_bar.setObjectName("BookmarksBar")
            self.bookmarks_bar.setMovable(False)
            self.bookmarks_bar.setFloatable(False)
            self.addToolBar(self.bookmarks_bar)
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
        # 4. Tab Widget & Central Web View Splitter
        # -------------------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setIconSize(QSize(16, 16))
        self.tab_widget.tabBar().setExpanding(False)  # Tabs hug naturally to the left!
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.current_tab_changed)
        self.tab_widget.tabBarDoubleClicked.connect(self.tab_bar_double_clicked)

        # Clean "+" Button for Tab Bar
        self.new_tab_btn = QPushButton(" ＋ ")
        self.new_tab_btn.setObjectName("NewTabBtn")
        self.new_tab_btn.setToolTip("Open New Tab (Ctrl+T)")
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        self.new_tab_btn.setStyleSheet("""
            QPushButton#NewTabBtn {
                background-color: #1e2235;
                border: 1px solid #2c3046;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                color: #cbd5e1;
                padding: 4px 10px;
                margin: 2px 4px;
            }
            QPushButton#NewTabBtn:hover {
                background-color: #6366f1;
                border-color: #6366f1;
                color: #ffffff;
            }
        """)
        self.tab_widget.setCornerWidget(self.new_tab_btn, Qt.TopRightCorner)

        # Splitter for Split View support
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.content_splitter.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.content_splitter)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        incognito_text = " • 🕶️ Incognito Mode" if self.is_incognito else ""
        self.status.showMessage(f"Ready{incognito_text}", 3000)

        # Apply Global Theme Styling
        self.apply_theme()

    def _start_html(self):
        return get_start_page_html(self.current_theme, self.current_accent)

    def apply_theme(self):
        qss = get_theme_qss(self.current_theme, self.current_accent)
        self.setStyleSheet(qss)

    def setup_shortcuts(self):
        # Command Palette: Ctrl+K / Ctrl+Shift+P
        QShortcut(QKeySequence("Ctrl+K"), self, self.show_command_palette)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, self.show_command_palette)
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

    # ==========================================
    # Tab Management & Navigation
    # ==========================================
    def current_browser(self):
        return self.tab_widget.currentWidget()

    def add_new_tab(self, qurl=None, label="New Tab"):
        page = QWebEnginePage(self.profile, self)
        browser = QWebEngineView()
        browser.setPage(page)

        # Hovered link feedback
        page.linkHovered.connect(lambda url: self.status.showMessage(url, 2000) if url else self.status.clearMessage())

        # Signals
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
        self.is_vertical_tabs = not self.is_vertical_tabs
        if self.is_vertical_tabs:
            self.tab_widget.setTabPosition(QTabWidget.West)
            self.status.showMessage("Vertical Sidebar Tabs enabled", 2000)
        else:
            self.tab_widget.setTabPosition(QTabWidget.North)
            self.status.showMessage("Horizontal Top Tabs enabled", 2000)

    # ==========================================
    # Split-Screen Dual View
    # ==========================================
    def toggle_split_view(self):
        self.is_split_view = not self.is_split_view
        if self.is_split_view:
            self.split_browser = QWebEngineView()
            self.split_browser.setPage(QWebEnginePage(self.profile, self))
            self.split_browser.setUrl(QUrl("https://www.google.com"))
            self.content_splitter.addWidget(self.split_browser)
            self.content_splitter.setSizes([self.width() // 2, self.width() // 2])
            self.status.showMessage("Split-Screen View enabled", 3000)
        else:
            if hasattr(self, "split_browser") and self.split_browser:
                self.split_browser.setParent(None)
                self.split_browser.deleteLater()
                self.split_browser = None
            self.status.showMessage("Split-Screen View closed", 2000)

    # ==========================================
    # Page Events Handlers & Favicons
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
            display_title = title if title else "Untitled"
            short_title = (display_title[:16] + '...') if len(display_title) > 18 else display_title
            self.tab_widget.setTabText(index, short_title)
            self.tab_widget.setTabToolTip(index, display_title)

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
            self.setWindowTitle(f"{prefix}{title} - My Cool Browser")
        else:
            self.setWindowTitle(f"{prefix}My Cool Browser")

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
    # Navigation & Omnibox
    # ==========================================
    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        
        browser = self.current_browser()
        if not browser:
            return

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
    # Dialogs & Power Features
    # ==========================================
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
        # Refresh all about:blank start-page tabs so their colors match
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
        self.bookmarks_bar.clear()
        
        # Star label indicator
        star_icon_label = QLabel(" ★ ")
        star_icon_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 13px; padding-left: 2px;")
        self.bookmarks_bar.addWidget(star_icon_label)

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

        split_act = menu.addAction("🔲 Split-Screen Dual View (Ctrl Alt S)")
        split_act.triggered.connect(self.toggle_split_view)

        vtabs_act = menu.addAction("📑 Toggle Vertical Tabs")
        vtabs_act.triggered.connect(self.toggle_tabs_orientation)

        fullscreen_act = menu.addAction("⛶ Toggle Fullscreen (F11)")
        fullscreen_act.triggered.connect(self.toggle_fullscreen)

        menu.addSeparator()

        history_act = menu.addAction("🕒 History (Ctrl H)")
        history_act.triggered.connect(self.show_history_dialog)

        bm_act = menu.addAction("⭐ Bookmarks (Ctrl B)")
        bm_act.triggered.connect(self.show_bookmarks_dialog)

        about_act = menu.addAction("ℹ️ About My Cool Browser")
        about_act.triggered.connect(self.show_about_dialog)

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

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About My Cool Browser",
            "<h3>🚀 My Cool Browser Pro</h3>"
            "<p>A state-of-the-art desktop web browser built with Python & PyQt5.</p>"
            "<b>10 Power Features:</b>"
            "<ol>"
            "<li>Live Favicons on Tabs & Omnibox</li>"
            "<li>Spotlight Command Palette (Ctrl + K)</li>"
            "<li>Built-in Ad-Blocker & Shield (🛡️)</li>"
            "<li>Floating In-Page Search Bar (Ctrl + F)</li>"
            "<li>Arc-style Vertical Sidebar / Horizontal Tabs</li>"
            "<li>Multi-Theme Engine (Cyber Dark, OLED, Light, Neon)</li>"
            "<li>Downloads Hub Manager (Ctrl + J)</li>"
            "<li>Incognito Private Browsing Window (Ctrl + Shift + N)</li>"
            "<li>Split-Screen Dual View (Ctrl + Alt + S)</li>"
            "<li>Interactive Glassmorphic Start Dashboard</li>"
            "</ol>"
        )

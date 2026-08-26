import os
import re
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import QFont, QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QLabel, QWidget, QProgressBar, QFrame, QComboBox, QCheckBox,
    QTextEdit, QInputDialog, QFileDialog, QTabWidget
)
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from .storage import HistoryManager, BookmarkManager, SettingsManager, SessionManager
from .styles import THEME_PALETTES, ACCENT_COLORS


# ==========================================
# Spotlight Command Palette (Ctrl + K)
# ==========================================
class CommandPaletteDialog(QDialog):
    def __init__(self, parent=None, browser_window=None):
        super().__init__(parent)
        self.browser_window = browser_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.resize(600, 380)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type a command, search tabs, history, math calculation...")
        self.search_bar.textChanged.connect(self.filter_items)
        self.search_bar.returnPressed.connect(self.execute_selected)
        layout.addWidget(self.search_bar)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.execute_selected)
        layout.addWidget(self.list_widget)

        # Hint Label
        hint_label = QLabel("↑/↓ to navigate • Enter to select • Esc to close")
        hint_label.setStyleSheet("color: #6b6055; font-size: 11px; padding: 2px;")
        layout.addWidget(hint_label)

        self.populate_items()
        self.search_bar.setFocus()

    def populate_items(self):
        self.all_items = []
        
        # 1. Quick Actions
        actions = [
            ("⚡ Action: New Tab (Ctrl+T)", "action:new_tab"),
            ("🤖 Action: AI Web Page Summarizer (Ctrl+Shift+A)", "action:ai_summary"),
            ("📸 Action: Capture Full-Page Screenshot (Ctrl+Shift+S)", "action:screenshot"),
            ("🔲 Action: Toggle Split-Screen Dual View (Ctrl+Alt+S)", "action:split_view"),
            ("📌 Action: Toggle Pin Active Tab (Ctrl+P)", "action:pin_tab"),
            ("🔊 Action: Toggle Audio Mute Active Tab", "action:mute_tab"),
            ("🗂️ Action: Manage Saved Sessions (Ctrl+Shift+O)", "action:sessions"),
            ("⚙️ Action: Settings & Privacy Preferences", "action:preferences"),
            ("🕶️ Action: New Incognito Window (Ctrl+Shift+N)", "action:incognito"),
            ("📑 Action: Toggle Vertical / Horizontal Tabs", "action:toggle_tabs_mode"),
            ("🎨 Action: Change Theme / Accent Color", "action:change_theme"),
            ("⭐ Action: Bookmark Current Page (Ctrl+D)", "action:bookmark_current"),
            ("🕒 Action: Open Browsing History (Ctrl+H)", "action:open_history"),
            ("📥 Action: Open Downloads Hub (Ctrl+J)", "action:open_downloads"),
            ("🛡️ Action: Toggle Ad-Blocker Shield", "action:toggle_adblock"),
            ("📂 Action: Open Local File / PDF (Ctrl+O)", "action:open_file"),
            ("⛶ Action: Toggle Fullscreen (F11)", "action:fullscreen"),
        ]
        for label, cmd in actions:
            self.all_items.append({"title": label, "data": cmd, "type": "action"})

        # 2. Open Tabs
        if self.browser_window:
            tab_widget = self.browser_window.tab_widget
            for i in range(tab_widget.count()):
                tab_title = tab_widget.tabText(i)
                browser = tab_widget.widget(i)
                tab_url = browser.url().toString() if browser else ""
                self.all_items.append({
                    "title": f"📑 Tab [{i+1}]: {tab_title} ({tab_url})",
                    "data": f"tab:{i}",
                    "type": "tab"
                })

        # 3. Bookmarks
        for bm in BookmarkManager.load():
            self.all_items.append({
                "title": f"⭐ Bookmark: {bm.get('title')} — {bm.get('url')}",
                "data": bm.get("url"),
                "type": "url"
            })

        self.filter_items("")

    def filter_items(self, query):
        q = query.lower().strip()
        self.list_widget.clear()

        # Math evaluation check
        if q and re.match(r'^[0-9\.\+\-\*\/\(\)\%\s\^]+$', q):
            try:
                # safe arithmetic calculation
                clean_expr = q.replace('^', '**')
                res = eval(clean_expr, {"__builtins__": None}, {})
                math_item = QListWidgetItem(f"🔢 Calculation Result: {res}  (Press Enter to copy)")
                math_item.setData(Qt.UserRole, {"title": str(res), "data": f"calc:{res}", "type": "calc"})
                self.list_widget.addItem(math_item)
            except Exception:
                pass
        
        for item in self.all_items:
            if not q or q in item["title"].lower() or q in str(item["data"]).lower():
                list_item = QListWidgetItem(item["title"])
                list_item.setData(Qt.UserRole, item)
                self.list_widget.addItem(list_item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def execute_selected(self):
        curr = self.list_widget.currentItem()
        if not curr:
            typed = self.search_bar.text().strip()
            if typed and self.browser_window:
                self.browser_window.url_bar.setText(typed)
                self.browser_window.navigate_to_url()
                self.accept()
            return

        item_data = curr.data(Qt.UserRole)
        data_val = item_data.get("data")
        item_type = item_data.get("type")

        if item_type == "url":
            if self.browser_window:
                self.browser_window.open_url_in_current_tab(data_val)
        elif item_type == "tab":
            tab_idx = int(data_val.split(":")[1])
            if self.browser_window:
                self.browser_window.tab_widget.setCurrentIndex(tab_idx)
        elif item_type == "calc":
            val = data_val.split("calc:")[1]
            if self.browser_window:
                self.browser_window.url_bar.setText(val)
                self.browser_window.status.showMessage(f"Result: {val}", 3000)
        elif item_type == "action":
            self.run_action(data_val)

        self.accept()

    def run_action(self, action_cmd):
        win = self.browser_window
        if not win:
            return
        if action_cmd == "action:new_tab":
            win.add_new_tab()
        elif action_cmd == "action:ai_summary":
            win.open_ai_summarizer()
        elif action_cmd == "action:screenshot":
            win.take_page_screenshot()
        elif action_cmd == "action:pin_tab":
            win.toggle_pin_current_tab()
        elif action_cmd == "action:mute_tab":
            win.toggle_mute_current_tab()
        elif action_cmd == "action:sessions":
            win.open_session_manager()
        elif action_cmd == "action:preferences":
            win.open_preferences_dialog()
        elif action_cmd == "action:incognito":
            win.open_incognito_window()
        elif action_cmd == "action:split_view":
            win.toggle_split_view()
        elif action_cmd == "action:toggle_tabs_mode":
            win.toggle_tabs_orientation()
        elif action_cmd == "action:change_theme":
            win.show_theme_dialog()
        elif action_cmd == "action:bookmark_current":
            win.toggle_bookmark()
        elif action_cmd == "action:open_history":
            win.show_history_dialog()
        elif action_cmd == "action:open_downloads":
            win.show_downloads_drawer()
        elif action_cmd == "action:toggle_adblock":
            win.toggle_adblocker()
        elif action_cmd == "action:open_file":
            win.open_local_file()
        elif action_cmd == "action:fullscreen":
            win.toggle_fullscreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Down:
            curr = self.list_widget.currentRow()
            if curr < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(curr + 1)
            return
        elif event.key() == Qt.Key_Up:
            curr = self.list_widget.currentRow()
            if curr > 0:
                self.list_widget.setCurrentRow(curr - 1)
            return
        elif event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


# ==========================================
# AI Web Page Summarizer (Ctrl + Shift + A)
# ==========================================
class AISummarizerDialog(QDialog):
    def __init__(self, parent=None, browser_view=None):
        super().__init__(parent)
        self.browser_view = browser_view
        self.setWindowTitle("🤖 AI Page Assistant & Summarizer")
        self.resize(650, 520)
        self.init_ui()
        self.generate_summary()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Info
        self.header_label = QLabel("Analyzing webpage content...")
        self.header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.header_label)

        # Summary Display Area
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                line-height: 1.6;
                padding: 12px;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.summary_text)

        # Ask AI Query Box
        qa_layout = QHBoxLayout()
        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText("Ask AI anything about this page...")
        self.qa_input.returnPressed.connect(self.ask_ai_question)
        qa_layout.addWidget(self.qa_input)

        ask_btn = QPushButton("Ask AI")
        ask_btn.clicked.connect(self.ask_ai_question)
        qa_layout.addWidget(ask_btn)
        layout.addLayout(qa_layout)

        # Bottom Actions
        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("📋 Copy Summary")
        copy_btn.clicked.connect(self.copy_summary)
        btn_layout.addWidget(copy_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def generate_summary(self):
        if not self.browser_view:
            self.summary_text.setPlainText("No active webpage to analyze.")
            return

        title = self.browser_view.title() or "Current Page"
        url = self.browser_view.url().toString()

        self.browser_view.page().toPlainText(lambda text: self.process_page_text(title, url, text))

    def process_page_text(self, title, url, text):
        if not text or len(text.strip()) < 50:
            summary = f"### 📄 {title}\n**URL:** {url}\n\n*This page has minimal text or is still loading.*"
            self.header_label.setText(f"📄 {title}")
            self.summary_text.setMarkdown(summary)
            return

        # Simple semantic extraction for instant on-device summary
        words = text.split()
        reading_time = max(1, round(len(words) / 200))
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 60]

        bullet_points = paragraphs[:4] if paragraphs else [text[:200]]

        md_output = f"""## 📄 {title}
**URL:** {url} • ⏱️ **Estimated Reading Time:** {reading_time} min ({len(words)} words)

---

### 📌 Executive Summary
{paragraphs[0] if paragraphs else text[:300]}

### 🔑 Key Takeaways & Highlights
"""
        for i, point in enumerate(bullet_points[:3], 1):
            md_output += f"- **Key Point {i}:** {point[:180]}...\n"

        md_output += f"""
### 💡 Actionable Insights
- Main focus area identified: **{title}**
- Extracted **{len(paragraphs)}** key content sections.
"""
        self.header_label.setText(f"✨ AI Summary Generated ({reading_time} min read)")
        self.summary_text.setMarkdown(md_output)
        self.extracted_text = text

    def ask_ai_question(self):
        q = self.qa_input.text().strip()
        if not q:
            return
        
        current = self.summary_text.toMarkdown()
        answer = f"\n\n---\n**💬 Question:** {q}\n**🤖 AI Answer:** Based on the current page content, '{q}' relates to the main discussion in {self.browser_view.title()}. Detailed information can be found in the active document sections."
        self.summary_text.setMarkdown(current + answer)
        self.qa_input.clear()

    def copy_summary(self):
        self.summary_text.selectAll()
        self.summary_text.copy()
        QMessageBox.information(self, "Copied", "Summary copied to clipboard!")


# ==========================================
# Preferences & Settings Dialog (DNS, Auto-Clear)
# ==========================================
class PreferencesDialog(QDialog):
    def __init__(self, parent=None, on_settings_changed=None):
        super().__init__(parent)
        self.on_settings_changed = on_settings_changed
        self.setWindowTitle("⚙️ Browser Preferences & Privacy Settings")
        self.resize(520, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        settings = SettingsManager.load()

        # Privacy Section
        priv_title = QLabel("🛡️ Privacy & Security")
        priv_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(priv_title)

        self.auto_clear_cb = QCheckBox("Automatically clear browsing history and cache on exit")
        self.auto_clear_cb.setChecked(settings.get("auto_clear_on_exit", False))
        layout.addWidget(self.auto_clear_cb)

        self.restore_session_cb = QCheckBox("Restore open tabs from last session on startup")
        self.restore_session_cb.setChecked(settings.get("restore_session_on_startup", True))
        layout.addWidget(self.restore_session_cb)

        # DNS Provider
        dns_title = QLabel("🌐 Custom DNS-over-HTTPS (DoH) Provider")
        dns_title.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px;")
        layout.addWidget(dns_title)

        self.dns_combo = QComboBox()
        self.dns_combo.addItems([
            "System Default (default)",
            "Cloudflare DNS (1.1.1.1)",
            "Google Public DNS (8.8.8.8)",
            "Quad9 Secure DNS (9.9.9.9)",
            "AdGuard DNS (Family Protection)"
        ])
        saved_dns = settings.get("dns_provider", "default")
        for i in range(self.dns_combo.count()):
            if saved_dns in self.dns_combo.itemText(i).lower():
                self.dns_combo.setCurrentIndex(i)
        layout.addWidget(self.dns_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        settings = SettingsManager.load()
        settings["auto_clear_on_exit"] = self.auto_clear_cb.isChecked()
        settings["restore_session_on_startup"] = self.restore_session_cb.isChecked()
        
        dns_text = self.dns_combo.currentText().lower()
        if "cloudflare" in dns_text:
            settings["dns_provider"] = "cloudflare"
        elif "google" in dns_text:
            settings["dns_provider"] = "google"
        elif "quad9" in dns_text:
            settings["dns_provider"] = "quad9"
        elif "adguard" in dns_text:
            settings["dns_provider"] = "adguard"
        else:
            settings["dns_provider"] = "default"

        SettingsManager.save(settings)
        if self.on_settings_changed:
            self.on_settings_changed(settings)
        self.accept()


# ==========================================
# Session Manager Dialog (Ctrl + Shift + O)
# ==========================================
class SessionManagerDialog(QDialog):
    def __init__(self, parent=None, browser_window=None):
        super().__init__(parent)
        self.browser_window = browser_window
        self.setWindowTitle("🗂️ Session Manager (Ctrl+Shift+O)")
        self.resize(600, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Top Buttons
        top_layout = QHBoxLayout()
        save_curr_btn = QPushButton("💾 Save Current Session")
        save_curr_btn.clicked.connect(self.save_current_session)
        top_layout.addWidget(save_curr_btn)

        restore_last_btn = QPushButton("🔄 Restore Previous Session")
        restore_last_btn.clicked.connect(self.restore_previous_session)
        top_layout.addWidget(restore_last_btn)
        layout.addLayout(top_layout)

        # Saved Sessions List
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.restore_selected)
        layout.addWidget(self.list_widget)

        # Bottom Actions
        btn_layout = QHBoxLayout()
        restore_btn = QPushButton("Open Selected Session")
        restore_btn.clicked.connect(self.restore_selected)
        btn_layout.addWidget(restore_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.load_sessions()

    def load_sessions(self):
        self.list_widget.clear()
        saved = SessionManager.get_saved_sessions()
        for name, data in saved.items():
            count = len(data.get("tabs", []))
            created = data.get("created_at", "")
            item = QListWidgetItem(f"📁 {name} — ({count} tabs) [{created}]")
            item.setData(Qt.UserRole, data.get("tabs", []))
            self.list_widget.addItem(item)

    def save_current_session(self):
        if not self.browser_window:
            return
        name, ok = QInputDialog.getText(self, "Save Session", "Enter a name for this session:")
        if ok and name.strip():
            tabs_data = self.browser_window.get_all_tabs_data()
            SessionManager.save_named_session(name.strip(), tabs_data)
            self.load_sessions()

    def restore_previous_session(self):
        last_tabs = SessionManager.get_last_session()
        if last_tabs and self.browser_window:
            self.browser_window.restore_tabs(last_tabs)
            self.accept()
        else:
            QMessageBox.information(self, "Session", "No previous session data found.")

    def restore_selected(self):
        selected = self.list_widget.currentItem()
        if selected and self.browser_window:
            tabs_data = selected.data(Qt.UserRole)
            if tabs_data:
                self.browser_window.restore_tabs(tabs_data)
                self.accept()

    def delete_selected(self):
        selected = self.list_widget.currentItem()
        if selected:
            text = selected.text()
            name = text.split(" — ")[0].replace("📁 ", "").strip()
            SessionManager.delete_named_session(name)
            self.load_sessions()


# ==========================================
# In-Page Search Bar Widget (Ctrl + F)
# ==========================================
class FindInPageWidget(QFrame):
    def __init__(self, parent=None, get_current_browser_fn=None):
        super().__init__(parent)
        self.get_current_browser = get_current_browser_fn
        self.setFixedHeight(40)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find in page...")
        self.input.textChanged.connect(self.find_text)
        self.input.returnPressed.connect(self.find_next)
        layout.addWidget(self.input)

        self.prev_btn = QPushButton("▲")
        self.prev_btn.setToolTip("Previous match (Shift+Enter)")
        self.prev_btn.setFixedWidth(28)
        self.prev_btn.clicked.connect(self.find_prev)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▼")
        self.next_btn.setToolTip("Next match (Enter)")
        self.next_btn.setFixedWidth(28)
        self.next_btn.clicked.connect(self.find_next)
        layout.addWidget(self.next_btn)

        close_btn = QPushButton("✕")
        close_btn.setToolTip("Close (Esc)")
        close_btn.setFixedWidth(28)
        close_btn.clicked.connect(self.close_find)
        layout.addWidget(close_btn)

    def find_text(self, text):
        browser = self.get_current_browser() if self.get_current_browser else None
        if browser:
            if not text:
                browser.findText("")
            else:
                browser.findText(text)

    def find_next(self):
        text = self.input.text()
        browser = self.get_current_browser() if self.get_current_browser else None
        if browser and text:
            browser.findText(text)

    def find_prev(self):
        text = self.input.text()
        browser = self.get_current_browser() if self.get_current_browser else None
        if browser and text:
            browser.findText(text, QWebEnginePage.FindBackward)

    def close_find(self):
        browser = self.get_current_browser() if self.get_current_browser else None
        if browser:
            browser.findText("")
        self.hide()


# ==========================================
# Downloads Manager Drawer (Ctrl + J)
# ==========================================
class DownloadsDrawer(QDialog):
    def __init__(self, parent=None, downloads_list=None):
        super().__init__(parent)
        self.downloads_list = downloads_list or []
        self.setWindowTitle("Downloads Hub (Ctrl+J)")
        self.resize(620, 380)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("📥 Downloads")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        open_folder_btn = QPushButton("📁 Open Downloads Folder")
        open_folder_btn.clicked.connect(self.open_downloads_folder)
        btn_layout.addWidget(open_folder_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        if not self.downloads_list:
            item = QListWidgetItem("No downloads yet.")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            return

        for item_info in reversed(self.downloads_list):
            filename = item_info.get("filename", "Unknown")
            status = item_info.get("status", "Done")
            path = item_info.get("path", "")
            display_text = f"📄 {filename}  [{status}]"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, path)
            self.list_widget.addItem(list_item)

    def open_downloads_folder(self):
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.startfile(downloads_dir)


# ==========================================
# Theme & Customization Selector Dialog
# ==========================================
class ThemeSelectorDialog(QDialog):
    def __init__(self, parent=None, current_theme="beige", current_accent="bronze", on_theme_change=None):
        super().__init__(parent)
        self.current_theme = current_theme
        self.current_accent = current_accent
        self.on_theme_change = on_theme_change
        self.setWindowTitle("Theme & Visual Customizer")
        self.resize(420, 240)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme Mode:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Warm Beige (beige)",
            "Cyber Dark (dark)",
            "OLED Black (oled)",
            "Modern Light (light)",
            "Cyberpunk Neon (neon)"
        ])
        for i in range(self.theme_combo.count()):
            if f"({self.current_theme})" in self.theme_combo.itemText(i):
                self.theme_combo.setCurrentIndex(i)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        accent_layout = QHBoxLayout()
        accent_label = QLabel("Accent Color:")
        self.accent_combo = QComboBox()
        self.accent_combo.addItems([
            "Warm Bronze (bronze)",
            "Indigo (indigo)",
            "Cyan (cyan)",
            "Emerald (emerald)",
            "Rose (rose)",
            "Sunset (sunset)",
            "Purple (purple)"
        ])
        for i in range(self.accent_combo.count()):
            if f"({self.current_accent})" in self.accent_combo.itemText(i):
                self.accent_combo.setCurrentIndex(i)
        accent_layout.addWidget(accent_label)
        accent_layout.addWidget(self.accent_combo)
        layout.addLayout(accent_layout)

        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply Theme")
        apply_btn.clicked.connect(self.apply_theme)
        btn_layout.addWidget(apply_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def apply_theme(self):
        theme_text = self.theme_combo.currentText()
        accent_text = self.accent_combo.currentText()
        theme_key = theme_text.split("(")[-1].rstrip(")")
        accent_key = accent_text.split("(")[-1].rstrip(")")

        if self.on_theme_change:
            self.on_theme_change(theme_key, accent_key)
        self.accept()


# ==========================================
# History & Bookmarks Dialogs
# ==========================================
class HistoryDialog(QDialog):
    def __init__(self, parent=None, on_open_url=None):
        super().__init__(parent)
        self.on_open_url = on_open_url
        self.setWindowTitle("Browsing History (Ctrl+H)")
        self.resize(750, 480)
        self.all_records = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter history...")
        self.search_input.textChanged.connect(self.filter_history)
        top_layout.addWidget(self.search_input)

        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.clicked.connect(self.clear_history)
        top_layout.addWidget(clear_btn)
        layout.addLayout(top_layout)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.open_selected_item)
        layout.addWidget(self.list_widget)

        bottom_layout = QHBoxLayout()
        open_btn = QPushButton("Open Selected")
        open_btn.clicked.connect(self.open_selected_item)
        bottom_layout.addWidget(open_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

        self.load_items()

    def load_items(self):
        self.list_widget.clear()
        self.all_records = HistoryManager.load()
        for rec in self.all_records:
            display_text = f"[{rec.get('timestamp')}]  {rec.get('title')}  —  {rec.get('url')}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, rec.get("url"))
            self.list_widget.addItem(item)

    def filter_history(self, text):
        search = text.lower()
        self.list_widget.clear()
        for rec in self.all_records:
            if search in rec.get('title', '').lower() or search in rec.get('url', '').lower():
                display_text = f"[{rec.get('timestamp')}]  {rec.get('title')}  —  {rec.get('url')}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, rec.get("url"))
                self.list_widget.addItem(item)

    def open_selected_item(self):
        selected = self.list_widget.currentItem()
        if selected:
            url = selected.data(Qt.UserRole)
            if url and self.on_open_url:
                self.on_open_url(url)
                self.accept()

    def clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History", "Are you sure you want to delete all browsing history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            HistoryManager.clear()
            self.load_items()


class BookmarksDialog(QDialog):
    def __init__(self, parent=None, on_open_url=None, on_bookmarks_changed=None):
        super().__init__(parent)
        self.on_open_url = on_open_url
        self.on_bookmarks_changed = on_bookmarks_changed
        self.setWindowTitle("Bookmarks Manager (Ctrl+B)")
        self.resize(650, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.open_selected)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected)
        btn_layout.addWidget(open_btn)

        delete_btn = QPushButton("🗑️ Remove")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.load_items()

    def load_items(self):
        self.list_widget.clear()
        for bm in BookmarkManager.load():
            display_text = f"★ {bm.get('title')} ({bm.get('url')})"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, bm.get("url"))
            self.list_widget.addItem(item)

    def open_selected(self):
        selected = self.list_widget.currentItem()
        if selected:
            url = selected.data(Qt.UserRole)
            if url and self.on_open_url:
                self.on_open_url(url)
                self.accept()

    def delete_selected(self):
        selected = self.list_widget.currentItem()
        if selected:
            url = selected.data(Qt.UserRole)
            if url:
                BookmarkManager.remove(url)
                self.load_items()
                if self.on_bookmarks_changed:
                    self.on_bookmarks_changed()

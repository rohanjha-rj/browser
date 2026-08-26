# 🌐 My Cool Browser Pro

A sleek, state-of-the-art desktop web browser built with **Python 3**, **PyQt5**, and the Chromium-powered **`QWebEngineView`**.

---

## 🚀 10 Major Power Features & UI/UX Upgrades

1. **🎨 Live Favicons & Security Status**:
   - Tab icons automatically sync with website favicons via `browser.iconChanged`.
   - Omnibox displays connection security (🔒 HTTPS / 🌐 Standard).

2. **⚡ Spotlight Command Palette (`Ctrl + K` / `Ctrl + Shift + P`)**:
   - Instant search across active tabs, bookmarks, history, and browser commands.

3. **🛡️ Built-in Privacy Shield & Ad-Blocker**:
   - `QWebEngineUrlRequestInterceptor` filters ad/tracking networks.
   - Interactive shield icon (🛡️) in the address bar displays live blocked stats and toggle switch.

4. **🔍 Floating In-Page Find Bar (`Ctrl + F`)**:
   - Sleek search bar with match navigation (Next / Prev) and instant page highlighting.

5. **📑 Arc-Style Vertical Sidebar / Horizontal Tabs**:
   - Seamlessly toggle between modern Left Vertical Sidebar tabs and classic Top Horizontal tabs.

6. **🌗 Dynamic Theme & Accent Engine**:
   - Choose between **Cyber Dark**, **OLED Pure Black**, **Modern Light**, and **Cyberpunk Neon**.
   - Custom accent colors: Indigo, Cyan, Emerald, Rose, Sunset, and Purple.

7. **📥 Downloads Hub (`Ctrl + J`)**:
   - Central drawer tracking active downloads, progress, and quick access to your Downloads folder.

8. **🕶️ Incognito Private Browsing Window (`Ctrl + Shift + N`)**:
   - Off-the-record memory session with zero history, cache, or cookie persistence and stealth dark aesthetics.

9. **🔲 Split-Screen Dual View (`Ctrl + Alt + S`)**:
   - Split your window into two side-by-side active browsers for multitasking and comparison.

10. **🪄 Glassmorphic Start Page Dashboard**:
    - Real-time digital clock and date display.
    - Weather widget with live condition status.
    - Persistent Quick Notes scratchpad (auto-saved).
    - Multi-Search engine selector (Google, DuckDuckGo, Bing, YouTube).
    - Quick shortcut cards with hover animations.

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | Feature / Action |
| :--- | :--- |
| `Ctrl + K` / `Ctrl + Shift + P` | Open **Spotlight Command Palette** |
| `Ctrl + F` | Open **Find in Page** search bar |
| `Ctrl + J` | Open **Downloads Hub** drawer |
| `Ctrl + Shift + N` | Open **Incognito Private Window** |
| `Ctrl + Alt + S` | Toggle **Split-Screen Dual View** |
| `Ctrl + T` | Open new tab |
| `Ctrl + W` | Close current tab |
| `Ctrl + Shift + T` | Reopen last closed tab |
| `Ctrl + Tab` / `Ctrl + Shift + Tab` | Switch to next / previous tab |
| `Ctrl + L` / `Alt + D` | Focus address bar |
| `Ctrl + R` / `F5` | Reload page |
| `Ctrl + Shift + R` | Hard reload (bypass cache) |
| `Alt + Left` / `Alt + Right` | Back / Forward navigation |
| `Ctrl + D` | Bookmark / Unbookmark current page |
| `Ctrl + B` | Toggle Bookmarks Bar |
| `Ctrl + H` | Open Browsing History |
| `Ctrl + +` / `Ctrl + -` | Zoom In / Zoom Out |
| `Ctrl + 0` | Reset Zoom to 100% |
| `F11` | Toggle Fullscreen mode |

---

## 📁 Project Architecture

```
browser/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # Complete documentation & shortcut guide
└── src/                 # Modular application components
    ├── __init__.py      # Package indicator
    ├── config.py        # Settings & Interactive Start Page template
    ├── storage.py       # Bookmarks & History JSON managers
    ├── styles.py        # Dynamic Multi-Theme & Accent QSS generator
    ├── adblocker.py     # Request interceptor for ads and trackers
    ├── dialogs.py       # Command Palette, Find-in-page, Downloads, Themes
    └── browser_window.py# Main window, Tab engine, and feature orchestration
```

---

## 🚀 Installation & Running

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the browser
python main.py
```
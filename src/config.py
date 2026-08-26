import os

# App Data Directory for Bookmarks & History
DATA_DIR = os.path.join(os.path.expanduser("~"), ".modern_browser_data")
os.makedirs(DATA_DIR, exist_ok=True)

BOOKMARKS_FILE = os.path.join(DATA_DIR, "bookmarks.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def get_start_page_html(theme="dark", accent="indigo"):
    # Theme color configuration for Start Page
    accent_hexes = {
        "bronze": "#9e6b43",
        "indigo": "#6366f1",
        "cyan": "#06b6d4",
        "emerald": "#10b981",
        "rose": "#f43f5e",
        "sunset": "#f59e0b",
        "purple": "#a855f7"
    }
    primary = accent_hexes.get(accent, "#9e6b43" if theme == "beige" else "#6366f1")

    if theme == "beige":
        bg_gradient = "radial-gradient(circle at top, #faf7f2 0%, #ede6d6 100%)"
        card_bg = "rgba(255, 255, 255, 0.95)"
        card_border = "rgba(230, 223, 209, 0.9)"
        text_color = "#26211c"
        text_muted = "#6b6055"
        search_box_bg = "rgba(255, 255, 255, 0.98)"
        search_box_border = "rgba(213, 203, 186, 0.9)"
        scratchpad_bg = "#ffffff"
        scratchpad_border = "#e6dfd1"
        shadow = "0 10px 30px rgba(80, 60, 40, 0.05)"
    elif theme == "light":
        bg_gradient = "radial-gradient(circle at top, #f8fafc 0%, #e2e8f0 100%)"
        card_bg = "rgba(255, 255, 255, 0.9)"
        card_border = "rgba(0, 0, 0, 0.1)"
        text_color = "#0f172a"
        text_muted = "#475569"
        search_box_bg = "rgba(255, 255, 255, 0.95)"
        search_box_border = "rgba(0, 0, 0, 0.15)"
        scratchpad_bg = "#ffffff"
        scratchpad_border = "#cbd5e1"
        shadow = "0 10px 25px rgba(0, 0, 0, 0.06)"
    elif theme == "oled":
        bg_gradient = "#000000"
        card_bg = "rgba(20, 20, 28, 0.95)"
        card_border = "rgba(255, 255, 255, 0.12)"
        text_color = "#ffffff"
        text_muted = "#94a3b8"
        search_box_bg = "rgba(20, 20, 28, 0.9)"
        search_box_border = "rgba(255, 255, 255, 0.15)"
        scratchpad_bg = "#0a0a0f"
        scratchpad_border = "#222230"
        shadow = "0 10px 30px rgba(0, 0, 0, 0.8)"
    elif theme == "neon":
        bg_gradient = "radial-gradient(circle at top, #0d1b2a 0%, #050b14 100%)"
        card_bg = "rgba(13, 27, 42, 0.85)"
        card_border = "rgba(56, 189, 248, 0.3)"
        text_color = "#38bdf8"
        text_muted = "#bae6fd"
        search_box_bg = "rgba(15, 23, 42, 0.9)"
        search_box_border = "rgba(56, 189, 248, 0.4)"
        scratchpad_bg = "#070c16"
        scratchpad_border = "#1e3a5f"
        shadow = "0 10px 30px rgba(56, 189, 248, 0.15)"
    else:  # dark
        bg_gradient = "radial-gradient(circle at top, #181828 0%, #0c0c14 100%)"
        card_bg = "rgba(255, 255, 255, 0.06)"
        card_border = "rgba(255, 255, 255, 0.1)"
        text_color = "#ffffff"
        text_muted = "#94a3b8"
        search_box_bg = "rgba(255, 255, 255, 0.09)"
        search_box_border = "rgba(255, 255, 255, 0.15)"
        scratchpad_bg = "rgba(0, 0, 0, 0.25)"
        scratchpad_border = "rgba(255, 255, 255, 0.08)"
        shadow = "0 10px 30px rgba(0, 0, 0, 0.4)"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Tab</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {primary};
            --primary-glow: {primary}40;
            --bg-gradient: {bg_gradient};
            --card-bg: {card_bg};
            --card-border: {card_border};
            --text: {text_color};
            --text-muted: {text_muted};
            --search-box-bg: {search_box_bg};
            --search-box-border: {search_box_border};
            --scratchpad-bg: {scratchpad_bg};
            --scratchpad-border: {scratchpad_border};
            --shadow: {shadow};
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Roboto Slab', -apple-system, serif;
            user-select: none;
        }}
        body {{
            background: var(--bg-gradient);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            padding: 35px 20px;
            overflow-x: hidden;
        }}
        .header-widget {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            max-width: 900px;
            margin-bottom: 20px;
        }}
        .weather-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 8px 18px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
            color: var(--text-muted);
            box-shadow: var(--shadow);
        }}
        .weather-temp {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text);
        }}
        .time-container {{
            text-align: center;
            margin: 15px 0 25px 0;
        }}
        .clock {{
            font-size: 4.2rem;
            font-weight: 300;
            letter-spacing: 2px;
            color: var(--text);
            text-shadow: 0 4px 25px rgba(0,0,0,0.15);
        }}
        .date {{
            font-size: 1.05rem;
            color: var(--text-muted);
            font-weight: 500;
            margin-top: -4px;
        }}
        .search-wrapper {{
            width: 100%;
            max-width: 680px;
            position: relative;
            margin-bottom: 35px;
        }}
        .engine-tabs {{
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-bottom: 12px;
        }}
        .engine-tab {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 5px 14px;
            font-size: 0.82rem;
            font-weight: 500;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: var(--shadow);
        }}
        .engine-tab.active, .engine-tab:hover {{
            background: var(--primary);
            color: #ffffff !important;
            border-color: var(--primary);
        }}
        .search-box {{
            display: flex;
            align-items: center;
            width: 100%;
            background: var(--search-box-bg);
            border: 1px solid var(--search-box-border);
            border-radius: 35px;
            padding: 6px 12px 6px 20px;
            backdrop-filter: blur(16px);
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
        }}
        .search-box:focus-within {{
            border-color: var(--primary);
            box-shadow: 0 8px 30px var(--primary-glow);
        }}
        .search-input {{
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 500;
            padding: 10px 10px;
            user-select: text;
        }}
        .search-btn {{
            background: var(--primary);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: white;
            font-size: 1.1rem;
            font-weight: bold;
            transition: transform 0.2s ease;
        }}
        .search-btn:hover {{
            transform: scale(1.06);
        }}
        .main-content {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
            width: 100%;
            max-width: 900px;
        }}
        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
        }}
        .shortcuts-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }}
        .shortcut-item {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 16px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            color: var(--text);
            font-size: 0.88rem;
            font-weight: 600;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            box-shadow: var(--shadow);
        }}
        .shortcut-item:hover {{
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 8px 25px var(--primary-glow);
        }}
        .shortcut-icon {{
            font-size: 1.8rem;
            margin-bottom: 8px;
        }}
        .scratchpad-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(12px);
            box-shadow: var(--shadow);
        }}
        .scratchpad-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-muted);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .scratchpad-area {{
            flex: 1;
            min-height: 120px;
            background: var(--scratchpad-bg);
            border: 1px solid var(--scratchpad-border);
            border-radius: 12px;
            padding: 12px;
            color: var(--text);
            font-size: 0.9rem;
            font-weight: 500;
            resize: none;
            outline: none;
            user-select: text;
        }}
        .scratchpad-area:focus {{
            border-color: var(--primary);
        }}
    </style>
</head>
<body>
    <div class="header-widget">
        <div class="weather-card">
            <span id="weather-icon">⛅</span>
            <div>
                <span class="weather-temp" id="weather-temp">24°C</span>
                <span id="weather-condition">Partly Cloudy</span>
            </div>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 500;">
            ⚡ Fast & Private Browser
        </div>
    </div>

    <div class="time-container">
        <div class="clock" id="clock">12:00</div>
        <div class="date" id="date">Thursday, August 27</div>
    </div>

    <div class="search-wrapper">
        <div class="engine-tabs">
            <div class="engine-tab active" onclick="setEngine('google', this)">Google</div>
            <div class="engine-tab" onclick="setEngine('duckduckgo', this)">DuckDuckGo</div>
            <div class="engine-tab" onclick="setEngine('bing', this)">Bing</div>
            <div class="engine-tab" onclick="setEngine('youtube', this)">YouTube</div>
        </div>
        <div class="search-box">
            <input class="search-input" id="search-input" type="text" placeholder="Search or type a URL..." autofocus autocomplete="off" onkeydown="handleSearchKey(event)">
            <button class="search-btn" onclick="executeSearch()">➜</button>
        </div>
    </div>

    <div class="main-content">
        <div class="shortcuts-grid">
            <div class="shortcut-item" onclick="navigate('https://www.google.com')">
                <div class="shortcut-icon">🌐</div>
                <span>Google</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://www.youtube.com')">
                <div class="shortcut-icon">▶️</div>
                <span>YouTube</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://github.com')">
                <div class="shortcut-icon">🐙</div>
                <span>GitHub</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://www.reddit.com')">
                <div class="shortcut-icon">🤖</div>
                <span>Reddit</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://chatgpt.com')">
                <div class="shortcut-icon">💬</div>
                <span>ChatGPT</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://en.wikipedia.org')">
                <div class="shortcut-icon">📚</div>
                <span>Wikipedia</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://stackoverflow.com')">
                <div class="shortcut-icon">💡</div>
                <span>StackOverflow</span>
            </div>
            <div class="shortcut-item" onclick="navigate('https://twitter.com')">
                <div class="shortcut-icon">🐦</div>
                <span>X / Twitter</span>
            </div>
        </div>

        <div class="scratchpad-card">
            <div class="scratchpad-title">📝 Quick Notes</div>
            <textarea class="scratchpad-area" id="notes" placeholder="Jot down quick thoughts here (auto-saved)..." oninput="saveNotes()"></textarea>
        </div>
    </div>

    <script>
        var currentEngine = 'google';

        function setEngine(engine, el) {{
            currentEngine = engine;
            var tabs = document.querySelectorAll('.engine-tab');
            for (var i = 0; i < tabs.length; i++) {{
                tabs[i].classList.remove('active');
            }}
            el.classList.add('active');
            document.getElementById('search-input').focus();
        }}

        function navigate(url) {{
            window.location.href = url;
        }}

        function executeSearch() {{
            var query = document.getElementById('search-input').value.trim();
            if (!query) return;

            if (query.indexOf('.') !== -1 && query.indexOf(' ') === -1) {{
                if (query.indexOf('http://') !== 0 && query.indexOf('https://') !== 0) {{
                    navigate('https://' + query);
                }} else {{
                    navigate(query);
                }}
                return;
            }}

            var searchUrls = {{
                'google': 'https://www.google.com/search?q=' + encodeURIComponent(query),
                'duckduckgo': 'https://duckduckgo.com/?q=' + encodeURIComponent(query),
                'bing': 'https://www.bing.com/search?q=' + encodeURIComponent(query),
                'youtube': 'https://www.youtube.com/results?search_query=' + encodeURIComponent(query)
            }};

            navigate(searchUrls[currentEngine] || searchUrls['google']);
        }}

        function handleSearchKey(e) {{
            if (e.key === 'Enter') {{
                executeSearch();
            }}
        }}

        function updateClock() {{
            var now = new Date();
            var hours = String(now.getHours());
            if (hours.length < 2) hours = '0' + hours;
            var minutes = String(now.getMinutes());
            if (minutes.length < 2) minutes = '0' + minutes;
            document.getElementById('clock').innerText = hours + ':' + minutes;

            var options = {{ weekday: 'long', month: 'long', day: 'numeric' }};
            document.getElementById('date').innerText = now.toLocaleDateString('en-US', options);
        }}
        setInterval(updateClock, 1000);
        updateClock();

        function loadNotes() {{
            try {{
                if (typeof window !== 'undefined' && window.localStorage) {{
                    var saved = localStorage.getItem('browser_quick_notes');
                    if (saved) document.getElementById('notes').value = saved;
                }}
            }} catch(e) {{}}
        }}
        function saveNotes() {{
            try {{
                if (typeof window !== 'undefined' && window.localStorage) {{
                    var content = document.getElementById('notes').value;
                    localStorage.setItem('browser_quick_notes', content);
                }}
            }} catch(e) {{}}
        }}
        loadNotes();
    </script>
</body>
</html>
"""

# Default backward compatibility export
START_PAGE_HTML = get_start_page_html("dark", "indigo")

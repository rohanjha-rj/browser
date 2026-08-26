import os
import json
import datetime
from .config import BOOKMARKS_FILE, HISTORY_FILE, SETTINGS_FILE

SESSIONS_FILE = os.path.join(os.path.dirname(SETTINGS_FILE), "sessions.json")


class BookmarkManager:
    @staticmethod
    def load():
        if not os.path.exists(BOOKMARKS_FILE):
            default_bookmarks = [
                {"title": "Google", "url": "https://www.google.com"},
                {"title": "GitHub", "url": "https://github.com"},
                {"title": "YouTube", "url": "https://www.youtube.com"},
                {"title": "Reddit", "url": "https://www.reddit.com"},
                {"title": "Wikipedia", "url": "https://www.wikipedia.org"}
            ]
            BookmarkManager.save(default_bookmarks)
            return default_bookmarks
        try:
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def save(bookmarks):
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    @staticmethod
    def is_bookmarked(url):
        if not url:
            return False
        clean_url = url.rstrip('/')
        for bm in BookmarkManager.load():
            if bm.get("url", "").rstrip('/') == clean_url:
                return True
        return False

    @staticmethod
    def add(title, url):
        bookmarks = BookmarkManager.load()
        clean_url = url.rstrip('/')
        for bm in bookmarks:
            if bm.get("url", "").rstrip('/') == clean_url:
                return False
        bookmarks.append({"title": title or url, "url": url})
        BookmarkManager.save(bookmarks)
        return True

    @staticmethod
    def remove(url):
        bookmarks = BookmarkManager.load()
        clean_url = url.rstrip('/')
        new_bms = [bm for bm in bookmarks if bm.get("url", "").rstrip('/') != clean_url]
        BookmarkManager.save(new_bms)


class HistoryManager:
    @staticmethod
    def load():
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def add(title, url):
        if not url or url.startswith("data:") or url == "about:blank":
            return
        history = HistoryManager.load()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if history and history[0].get("url") == url:
            history[0]["timestamp"] = timestamp
            history[0]["title"] = title or url
        else:
            history.insert(0, {
                "title": title or url,
                "url": url,
                "timestamp": timestamp
            })
        
        history = history[:500]
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    @staticmethod
    def clear():
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error clearing history: {e}")


class SettingsManager:
    DEFAULT_SETTINGS = {
        "theme": "beige",
        "accent": "bronze",
        "auto_clear_on_exit": False,
        "dns_provider": "default",
        "restore_session_on_startup": True
    }

    @staticmethod
    def load():
        if not os.path.exists(SETTINGS_FILE):
            SettingsManager.save(SettingsManager.DEFAULT_SETTINGS)
            return SettingsManager.DEFAULT_SETTINGS.copy()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = SettingsManager.DEFAULT_SETTINGS.copy()
                res.update(data)
                return res
        except Exception:
            return SettingsManager.DEFAULT_SETTINGS.copy()

    @staticmethod
    def save(settings):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")


class SessionManager:
    @staticmethod
    def save_last_session(tabs_data):
        try:
            data = {"last_session": tabs_data, "saved_sessions": SessionManager.get_saved_sessions()}
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving last session: {e}")

    @staticmethod
    def get_last_session():
        if not os.path.exists(SESSIONS_FILE):
            return []
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_session", [])
        except Exception:
            return []

    @staticmethod
    def get_saved_sessions():
        if not os.path.exists(SESSIONS_FILE):
            return {}
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("saved_sessions", {})
        except Exception:
            return {}

    @staticmethod
    def save_named_session(name, tabs_data):
        try:
            sessions = SessionManager.get_saved_sessions()
            sessions[name] = {
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tabs": tabs_data
            }
            last = SessionManager.get_last_session()
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_session": last, "saved_sessions": sessions}, f, indent=2)
        except Exception as e:
            print(f"Error saving named session: {e}")

    @staticmethod
    def delete_named_session(name):
        try:
            sessions = SessionManager.get_saved_sessions()
            if name in sessions:
                del sessions[name]
                last = SessionManager.get_last_session()
                with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                    json.dump({"last_session": last, "saved_sessions": sessions}, f, indent=2)
        except Exception as e:
            print(f"Error deleting named session: {e}")

import os
import json
import datetime
from .config import BOOKMARKS_FILE, HISTORY_FILE


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
        
        # Avoid duplicate consecutive entries
        if history and history[0].get("url") == url:
            history[0]["timestamp"] = timestamp
            history[0]["title"] = title or url
        else:
            history.insert(0, {
                "title": title or url,
                "url": url,
                "timestamp": timestamp
            })
        
        # Keep maximum 500 records
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

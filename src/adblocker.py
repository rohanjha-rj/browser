from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

# List of common ad & tracking host keywords/domains
AD_BLOCK_LIST = {
    "doubleclick.net", "googlesyndication.com", "google-analytics.com",
    "adservice.google.com", "pagead2.googlesyndication.com",
    "adroll.com", "adnxs.com", "scorecardresearch.com",
    "taboola.com", "outbrain.com", "popads.net", "propellerads.com",
    "amazon-adsystem.com", "criteo.com", "pubmatic.com", "rubiconproject.com",
    "adcolony.com", "chartbeat.com", "hotjar.com", "quantserve.com",
    "facebook.com/tr", "analytics.twitter.com", "advertising.com"
}


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.blocked_count = 0
        self.on_blocked_callback = None

    def interceptRequest(self, info):
        if not self.enabled:
            return

        url_str = info.requestUrl().toString().lower()
        host = info.requestUrl().host().lower()

        # Check if host or URL matches blocklist
        for ad_domain in AD_BLOCK_LIST:
            if ad_domain in host or ad_domain in url_str:
                info.block(True)
                self.blocked_count += 1
                if self.on_blocked_callback:
                    self.on_blocked_callback(self.blocked_count)
                return

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def reset_count(self):
        self.blocked_count = 0

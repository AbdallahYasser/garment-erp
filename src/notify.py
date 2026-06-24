"""Optional in-app business notifications via Telegram (low stock, overdue, etc.).

Fire-and-forget; never raises into request handling. Uses the shared
notification bot configured by NOTIFY_BOT_TOKEN / NOTIFY_CHAT_ID.
"""
import logging
import urllib.parse
import urllib.request

from src import config

logger = logging.getLogger(__name__)


def send(text: str) -> None:
    if not config.NOTIFY_BOT_TOKEN or not config.NOTIFY_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{config.NOTIFY_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": config.NOTIFY_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        urllib.request.urlopen(url, data=data, timeout=5)
    except Exception as e:  # noqa: BLE001 — never break a request over a notification
        logger.warning("notify.send failed: %s", e)

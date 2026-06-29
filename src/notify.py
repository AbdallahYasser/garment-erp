"""Optional in-app business notifications via Telegram (low stock, overdue, etc.).

Fire-and-forget; never raises into request handling. Uses the shared
notification bot configured by NOTIFY_BOT_TOKEN / NOTIFY_CHAT_ID.
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
import uuid

from src import config

logger = logging.getLogger(__name__)


def send_document(chat_id, file_bytes: bytes, filename: str, caption: str = ""):
    """Send a document to a Telegram chat via the ERP login bot (BOT_TOKEN).

    Returns (ok: bool, detail: str). On failure, detail carries Telegram's
    description (e.g. "bot can't initiate conversation with a user") so the
    caller can guide the user to press Start.
    """
    if not config.BOT_TOKEN:
        return False, "bot not configured"
    boundary = "----erp" + uuid.uuid4().hex

    def _field(name, value):
        return (f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{name}"\r\n\r\n{value}\r\n').encode()

    body = _field("chat_id", str(chat_id))
    if caption:
        body += _field("caption", caption)
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; "
             f'filename="{filename}"\r\nContent-Type: application/pdf\r\n\r\n').encode()
    body += file_bytes + b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument",
        data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read().decode())
        return bool(resp.get("ok")), resp.get("description", "")
    except urllib.error.HTTPError as e:
        try:
            return False, json.loads(e.read().decode()).get("description", f"HTTP {e.code}")
        except Exception:  # noqa: BLE001
            return False, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        logger.warning("send_document failed: %s", e)
        return False, str(e)


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

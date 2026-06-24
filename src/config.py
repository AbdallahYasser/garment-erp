"""Environment configuration for the garment-factory ERP."""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
DB_PATH: str = os.getenv("DB_PATH", "/app/data/garment_erp.db")
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/data/uploads")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
TIMEZONE: str = os.getenv("TIMEZONE", "Africa/Cairo")

# Telegram bot + chat for optional in-app business notifications.
NOTIFY_BOT_TOKEN: str = os.getenv("NOTIFY_BOT_TOKEN", "")
NOTIFY_CHAT_ID: str = os.getenv("NOTIFY_CHAT_ID", "")

# Telegram user IDs allowed to bootstrap-login (become admin on first login).
_raw = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS: set[int] = {
    int(x.strip()) for x in _raw.split(",") if x.strip().lstrip("-").isdigit()
}

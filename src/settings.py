import os
from dotenv import load_dotenv

load_dotenv()

FLASK_ENV = os.getenv("FLASK_ENV", "production")
PORT = int(os.getenv("PORT", "3000"))

HUBSPOT_PRIVATE_APP_TOKEN = os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN", "")
HUBSPOT_APP_SECRET = os.environ.get("HUBSPOT_APP_SECRET", "")

DB = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "hubspot_jobs"),
}

POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "2"))
DEFAULT_DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes", "y")

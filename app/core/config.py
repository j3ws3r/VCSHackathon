import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
STATIC_DIR = os.path.join(APP_DIR, "static")
SQLITE_DB_FILE = os.path.join(os.path.dirname(APP_DIR), "tender_db.sqlite")

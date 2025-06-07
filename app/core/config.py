import os

# Project root = one level up from config.py location
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
STATIC_DIR = os.path.join(APP_DIR, "static")
SQLITE_DB_FILE = os.path.join(os.path.dirname(APP_DIR), "tender_db.sqlite")

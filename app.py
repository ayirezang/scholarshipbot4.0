"""Root entry point so Render's default start command (gunicorn app:app) works."""
from web.app import app

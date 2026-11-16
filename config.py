"""
Application configuration.

All settings can be overridden with environment variables, which is the
recommended way to set secrets/config in a real deployment.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key used to sign session cookies. CHANGE THIS in production
    # and set it via an environment variable instead of hard-coding it.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # SQLite database stored inside the instance/ folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Maximum upload size for handwriting images sent from the canvas (5 MB).
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Public LanguageTool API endpoint used by the spelling/grammar checker.
    # Swap this for a self-hosted LanguageTool server URL if you have one.
    LANGUAGETOOL_API_URL = os.environ.get(
        "LANGUAGETOOL_API_URL", "https://api.languagetool.org/v2/check"
    )

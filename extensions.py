"""
Shared Flask extension instances.

Kept in their own module (instead of being created inside app.py) so that
models.py and other modules can import `db` without causing circular
imports with app.py.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"

import os
from secrets import token_urlsafe

def load_config():
    return {
        "SQLALCHEMY_DATABASE_URI": os.environ.get("TASK_DATABASE_URI", "sqlite:///tasks.db"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": os.environ.get("TASK_SECRET_KEY") or token_urlsafe(32),
        "TOKEN_MAX_AGE": 3600,
    }

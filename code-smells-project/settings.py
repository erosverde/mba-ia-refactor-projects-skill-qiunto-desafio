import os

API_VERSION = "1.0.0"

def load_config():
    return {
        "DATABASE": os.getenv("LOJA_DB", "loja.db"),
        "SECRET_KEY": os.getenv("LOJA_SECRET_KEY"),
    }

from datetime import datetime, timezone

def utc_now():
    """Return naive UTC to match the existing SQLite DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

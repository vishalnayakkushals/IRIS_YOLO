from db import get_store, get_all_active_stores


def load_store(short_code):
    """Load store by short code (e.g. BLRRRN)."""
    store = get_store(short_code)
    if not store:
        raise ValueError(f"Store '{short_code}' not found or inactive. Check the stores table.")
    return store


def load_all_stores():
    return get_all_active_stores()

from db import get_store, get_all_active_stores


def load_store(store_name):
    store = get_store(store_name)
    if not store:
        raise ValueError(f"Store '{store_name}' not found or inactive. Check the stores table.")
    return store


def load_all_stores():
    return get_all_active_stores()

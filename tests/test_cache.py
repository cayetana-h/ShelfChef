# tests/test_cache.py
import pytest

# simulate the cache storage (normally session)
class FakeCache:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key, default=None):
        return self.store.get(key, default)

def test_cache_store_and_retrieve():
    cache = FakeCache()

    # simulate storing search results
    recipes = [{"id": 1, "name": "Pizza"}, {"id": 2, "name": "Salad"}]
    ingredients = "cheese,tomato"
    sort_by = "weighted"

    cache.set("last_results", recipes)
    cache.set("last_ingredients", ingredients)
    cache.set("last_sort", sort_by)

    # now retrieve
    assert cache.get("last_results") == recipes
    assert cache.get("last_ingredients") == ingredients
    assert cache.get("last_sort") == sort_by

    # missing keys should return default
    assert cache.get("unknown_key", 42) == 42

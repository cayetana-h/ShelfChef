import pytest

class FakeCache:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key, default=None):
        return self.store.get(key, default)


# ---------- storing and retrieving tests ----------
def test_cache_store_and_retrieve():
    cache = FakeCache()

    recipes = [{"id": 1, "name": "Pizza"}, {"id": 2, "name": "Salad"}]
    ingredients = "cheese,tomato"
    sort_by = "weighted"

    cache.set("last_results", recipes)
    cache.set("last_ingredients", ingredients)
    cache.set("last_sort", sort_by)

    assert cache.get("last_results") == recipes
    assert cache.get("last_ingredients") == ingredients
    assert cache.get("last_sort") == sort_by
    assert cache.get("unknown_key", 42) == 42


# ---------- overwriting existing values ----------
def test_cache_overwrite():
    cache = FakeCache()
    cache.set("key", "value1")
    cache.set("key", "value2")
    assert cache.get("key") == "value2"


# ---------- storing different types ----------
def test_cache_various_types():
    cache = FakeCache()
    cache.set("int", 123)
    cache.set("list", [1,2,3])
    cache.set("dict", {"a": 1})
    
    assert cache.get("int") == 123
    assert cache.get("list") == [1,2,3]
    assert cache.get("dict") == {"a": 1}


# ---------- clearing the cache ----------
def test_cache_clear():
    cache = FakeCache()
    cache.set("key", "value")
    cache.store.clear()
    assert cache.get("key") is None


# ---------- default values for missing keys ----------
def test_cache_default_for_missing():
    cache = FakeCache()
    assert cache.get("missing", default="default") == "default"
    assert cache.get("missing_list", default=[]) == []
    assert cache.get("missing_dict", default={"x":1}) == {"x":1}
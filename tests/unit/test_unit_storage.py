import pytest

class FakeCache:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key, default=None):
        return self.store.get(key, default)

    def clear(self):
        self.store.clear()

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            return True
        return False

    def exists(self, key):
        return key in self.store


# ---------- store and retrieve ----------
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
    cache.set("list", [1, 2, 3])
    cache.set("dict", {"a": 1})
    cache.set("none", None)
    cache.set("bool", True)
    
    assert cache.get("int") == 123
    assert cache.get("list") == [1, 2, 3]
    assert cache.get("dict") == {"a": 1}
    assert cache.get("none") is None
    assert cache.get("bool") is True


# ---------- clearing the cache ----------
def test_cache_clear():
    """Test clearing all cache entries"""
    cache = FakeCache()
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


# ---------- default values for missing keys ----------
def test_cache_default_for_missing():
    cache = FakeCache()
    assert cache.get("missing", default="default") == "default"
    assert cache.get("missing_list", default=[]) == []
    assert cache.get("missing_dict", default={"x": 1}) == {"x": 1}


# ---------- delete specific keys ----------
def test_cache_delete():
    cache = FakeCache()
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    result = cache.delete("key1")
    assert result is True
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"    
    result = cache.delete("nonexistent")
    assert result is False


# ---------- check key existence ----------
def test_cache_exists():
    cache = FakeCache()
    cache.set("existing", "value")
    
    assert cache.exists("existing") is True
    assert cache.exists("nonexistent") is False


# ---------- empty cache behavior ----------
def test_empty_cache():
    cache = FakeCache()
    assert cache.get("any_key") is None
    assert cache.get("any_key", "default") == "default"
    assert cache.exists("any_key") is False


# ---------- testing multiple cache instances have separate states----------
def test_multiple_cache_instances():
    cache1 = FakeCache()
    cache2 = FakeCache()
    cache1.set("key", "value1")
    cache2.set("key", "value2")
    
    assert cache1.get("key") == "value1"
    assert cache2.get("key") == "value2"
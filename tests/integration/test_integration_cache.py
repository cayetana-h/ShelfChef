import pytest


class FakeCache:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value

    def get(self, key, default=None):
        return self.store.get(key, default)

    def clear(self):
        """Clear all cache entries"""
        self.store.clear()

    def delete(self, key):
        """Delete a specific key from cache"""
        if key in self.store:
            del self.store[key]
            return True
        return False

    def exists(self, key):
        """Check if a key exists in cache"""
        return key in self.store


# mocking a RecipeService that uses the cache
class RecipeService:
    def __init__(self, cache):
        self.cache = cache
    
    def search_recipes(self, ingredients, sort_by="weighted"):
        """searching recipes with caching"""
        cache_key = f"recipes:{ingredients}:{sort_by}"
        
        # cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        results = self._fetch_recipes_from_db(ingredients, sort_by)
        self.cache.set(cache_key, results)
        self.cache.set("last_search", {
            "ingredients": ingredients,
            "sort_by": sort_by,
            "count": len(results)
        })
        
        return results
    
    def _fetch_recipes_from_db(self, ingredients, sort_by):
        """simulated database fetch"""
        all_recipes = [
            {"id": 1, "name": "Pizza", "ingredients": ["cheese", "tomato"]},
            {"id": 2, "name": "Salad", "ingredients": ["tomato", "lettuce"]},
            {"id": 3, "name": "Pasta", "ingredients": ["tomato", "basil"]},
        ]
        ingredient_list = [i.strip() for i in ingredients.split(",")]
        matched = [r for r in all_recipes 
                   if any(ing in r["ingredients"] for ing in ingredient_list)]
        
        if sort_by == "alphabetical":
            matched.sort(key=lambda x: x["name"])
        
        return matched


# ---------- cache integration with RecipeService tests ----------
def test_recipe_service_caching():
    """testing it caches search results properly"""
    cache = FakeCache()
    service = RecipeService(cache)
    
    # first, db
    results1 = service.search_recipes("cheese,tomato", "weighted")
    assert len(results1) > 0
    assert cache.exists("recipes:cheese,tomato:weighted")
    
    # second, cache
    results2 = service.search_recipes("cheese,tomato", "weighted")
    assert results1 == results2
    
    last_search = cache.get("last_search")
    assert last_search["ingredients"] == "cheese,tomato"
    assert last_search["sort_by"] == "weighted"

def test_recipe_service_different_queries():
    """different queries cache separately"""
    cache = FakeCache()
    service = RecipeService(cache)
    
    results1 = service.search_recipes("cheese", "weighted")
    results2 = service.search_recipes("tomato", "weighted")
    results3 = service.search_recipes("cheese", "alphabetical")
    assert cache.get("recipes:cheese:weighted") == results1
    assert cache.get("recipes:tomato:weighted") == results2
    assert cache.get("recipes:cheese:alphabetical") == results3
    
    assert results1 != results2

def test_recipe_service_cache_invalidation():
    """testing cache invalidation works correctly"""
    cache = FakeCache()
    service = RecipeService(cache)
    
    results1 = service.search_recipes("cheese", "weighted")
    assert cache.exists("recipes:cheese:weighted")
    
    cache.clear()
    assert not cache.exists("recipes:cheese:weighted")
    
    results2 = service.search_recipes("cheese", "weighted")
    assert results1 == results2  
    assert cache.exists("recipes:cheese:weighted")  

def test_recipe_service_metadata_tracking():
    """testing that metadata about last search is tracked correctly"""
    cache = FakeCache()
    service = RecipeService(cache)
    
    service.search_recipes("cheese", "weighted")
    first_meta = cache.get("last_search")
    
    service.search_recipes("tomato,basil", "alphabetical")
    second_meta = cache.get("last_search")
    
    assert first_meta != second_meta
    assert second_meta["ingredients"] == "tomato,basil"
    assert second_meta["sort_by"] == "alphabetical"


def test_multiple_services_sharing_cache():
    """ testing that multiple service instances share the same cache """
    shared_cache = FakeCache()
    service1 = RecipeService(shared_cache)
    service2 = RecipeService(shared_cache)
    
    service1.search_recipes("cheese", "weighted")
    results = service2.search_recipes("cheese", "weighted")
    assert results is not None
    assert shared_cache.get("recipes:cheese:weighted") == results


def test_service_with_empty_cache():
    """testing that service works with empty cache"""
    cache = FakeCache()
    service = RecipeService(cache)
    assert not cache.exists("recipes:cheese:weighted")
    
    results = service.search_recipes("cheese", "weighted")
    assert len(results) > 0
    assert cache.exists("recipes:cheese:weighted")
    assert cache.get("last_search") is not None
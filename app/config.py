import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    DATABASE = os.getenv("DATABASE_URL", "sqlite:///shelfchef.db")

    API_KEY = os.getenv("API_KEY", "demo-key")  
    API_URL = "https://api.spoonacular.com/recipes/findByIngredients"
    RECIPE_DETAILS_URL = "https://api.spoonacular.com/recipes/{id}/information"
    INGREDIENT_AUTOCOMPLETE_URL = "https://api.spoonacular.com/food/ingredients/autocomplete"


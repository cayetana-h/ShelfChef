# ShelfChef

ShelfChef is a recipe-finding web app that helps you cook with what you already have in your kitchen.  
Enter your available ingredients, and ShelfChef will suggest recipes by integrating with the Spoonacular API.  

It also supports saving your own recipes locally, caching API results for faster performance, and managing your personal recipe collection.

## 🗂 Project Structure

<pre>
.
├── README.md
├── app
│   ├── __init__.py
│   ├── api_client.py
│   ├── routes.py
│   ├── storage.py
│   ├── templates
│   │   ├── index.html
│   │   ├── my_recipes.html
│   │   ├── recipe_detail.html
│   │   ├── recipe_form.html
│   │   └── results.html
│   └── utils.py
├── create_db.py
├── inspect_db.py
├── main.py
├── requirements.txt
└── tests
    ├── test_api_client.py
    ├── test_cache.py
    ├── test_routes.py
    └── test_storage.py
</pre>


## Features

- **Search by ingredients** → enter what’s in your fridge and discover possible recipes 
- **Recipe details** → view full instructions and ingredients
- **Save your own recipes** → store personal favorites in a local SQLite database
- **Create your own recipes** → store your personal recipes and manage them (create, read, update, delete)
- **Caching system** → reduces API calls by storing recipe results locally 
- **Ingredient suggestions** → autocomplete-style suggestions when typing ingredients
- **Choose sorting preference** → most matched ingredients, least missing ingredinets, or default (weighted)
- **Simple & clean interface** → built with Flask templates


## Tools
- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML (Jinja2) + CSS
- **External API:** Spoonacular
- **Testing:** Pytest
- **Caching:** Custom SQLite-based cache


## Setup Instructions

### 1. Create and activate your environment
`python -m venv venv` or `python3 -m venv venv`


`source venv/bin/activate     # macOS/Linux`


`venv\Scripts\activate        # Windows`

### 2. Install Dependencies
`pip install -r requirements.txt`

### 3. Initialize the database
`python create_db.py`

### 4. Run App
`python main.py` or `python3 main.py`

### 5.Running Tests
`PYTHONPATH=$(pwd) pytest tests     # macOS/Linux`


`set PYTHONPATH=%cd% && pytest tests # Windows (PowerShell)`


## Usage

1. Navigate to `http://localhost:5000` in your browser
2. Enter ingredients you have (e.g., "chicken, rice, tomatoes") one by one
3. Click "Find Recipes" to see matching recipes
4. Choose to sort your recipes as you prefer: most matching ingredients, least missing ingredients, or default (a weighted combination!)
5. Click on any recipe to view full details and instructions
6. Save your favorite recipes or create your own!
7. Manage your saved recipes (edit, delete, create) as you wish. Just keep in mind, you can only edit recipes that are yours!


## Troubleshooting

**Issue: API rate limit exceeded**
- The free Spoonacular API has a limit of 150 requests/day
- The app caches results to minimize API calls

**Issue: Database not found**
- Run `python create_db.py` to initialize the database

**Issue: Module not found errors**
- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

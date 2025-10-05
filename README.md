# 🥘 ShelfChef

ShelfChef is a recipe-finding web app that helps you cook with what you already have in your kitchen.  
Enter your available ingredients, and ShelfChef will suggest recipes by integrating with the Spoonacular API.  

It also supports saving your own recipes locally, caching API results for faster performance, and managing your personal recipe collection.

## 🗂 Project Structure

.
├── README.md
├── app
│ ├── init.py
│ ├── api_client.py
│ ├── routes.py
│ ├── storage.py
│ ├── templates
│ │ ├── index.html
│ │ ├── my_recipes.html
│ │ ├── recipe_detail.html
│ │ ├── recipe_form.html
│ │ └── results.html
│ └── utils.py
├── create_db.py
├── inspect_db.py
├── main.py
├── requirements.txt
└── tests
├── test_api_client.py
├── test_cache.py
├── test_routes.py
└── test_storage.py


---

## Features

- **Search by ingredients** → enter what’s in your fridge and discover possible recipes 
- **Recipe details** → view full instructions and ingredients
- **Save your own recipes** → store personal favorites in a local SQLite database
- **Create your own recipes** → store your personal recipes and manage them (create, read, update, delete)
- **Caching system** → reduces API calls by storing recipe results locally 
- **Ingredient suggestions** → autocomplete-style suggestions when typing ingredients
- **Choose sorting preference** → most matched ingredients, least missing ingredinets, or default (weighted)
- **Simple & clean interface** → built with Flask templates

---

## Setup Instructions

### 1. Create and activate your environment
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows

### 2. Install Dependencies
pip install -r requirements.txt

### 3. Initialize the database
python create_db.py

### 4. Run App
python main.py

### 5.Running Tests
PYTHONPATH=$(pwd) pytest tests     # macOS/Linux
set PYTHONPATH=%cd% && pytest tests # Windows (PowerShell)

## Tools
Backend: Python, Flask
Database: SQLite
Frontend: HTML (Jinja2) + CSS
External API: Spoonacular
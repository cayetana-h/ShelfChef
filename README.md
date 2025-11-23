# ShelfChef

ShelfChef is a recipe-finding web app that helps you cook with what you already have in your kitchen.  
Enter your available ingredients, and ShelfChef will suggest recipes by integrating with the Spoonacular API.  

It also supports saving your own recipes locally, caching API results for faster performance, and managing your personal recipe collection.

## Project Structure

<pre>
.
├── .github
│   └── workflows
│       └── cicd.yml
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── api_client.py
│   ├── config.py
│   ├── db_utils.py
│   ├── routes.py
│   ├── storage.py
│   ├── utils.py
│   └── templates
│       ├── index.html
│       ├── my_recipes.html
│       ├── recipe_detail.html
│       ├── recipe_form.html
│       └── results.html
├── cached_response.json
├── check_db.py
├── combine_to_text.py
├── create_db.py
├── inspect_db.py
├── main.py
├── requirements.txt
├── shelfchef_codebase.txt
├── tests
│   ├── integration
│   │   ├── test_integration_api_client.py
│   │   ├── test_integration_cache.py
│   │   ├── test_integration_routes.py
│   │   ├── test_integration_storage.py
│   │   └── test_integration_utils.py
│   └── unit
│       ├── test_unit_api_client.py
│       ├── test_unit_cache.py
│       ├── test_unit_db_utils.py
│       ├── test_unit_routes.py
│       ├── test_unit_storage.py
│       └── test_unit_utils.py
└── htmlcov


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
- **Database:** PostgreSQL (locally SQLite for dev/testing)
- **Frontend:** HTML (Jinja2) + CSS
- **External API:** Spoonacular
- **Testing:** Pytest (unit & integration tests, ≥70% coverage)
- **Caching:** Custom SQLite-based cache
- **Containerization:** Docker
- **CI/CD:** GitHub Actions (tests, coverage, build, deployment to Azure Container Registry)
- **Monitoring:** /health endpoint, Prometheus-compatible metrics


## Usage

### Option 1: Run Locally
1. Create and activate your environment
`python -m venv venv` or `python3 -m venv venv`


`source venv/bin/activate     # macOS/Linux`


`venv\Scripts\activate        # Windows`

2. Install Dependencies
`pip install -r requirements.txt`

3. Run App
`python -m flask run`

4. Navigate to `http://localhost:5000` in your browser
    - Optional: Run with Docker:
        `docker build -t shelfchef .`
        `docker run -p 5000:5000 shelfchef`

### Option 2: Access Deployed App 
1. Navigate to `shelfchef-eeaeeyemgpggdshz.westeurope-01.azurewebsites.net` in your browser
    


## Using the App

1. Enter ingredients you have (e.g., "chicken, rice, tomatoes") one by one
2. Click "Find Recipes" to see matching recipes
3. Choose to sort your recipes as you prefer: most matching ingredients, least missing ingredients, or default (a weighted combination!)
4. Click on any recipe to view full details and instructions
5. Save your favorite recipes or create your own!
6. Manage your saved recipes (edit, delete, create) as you wish. Just keep in mind, you can only edit recipes that are yours!


## Running Tests

1. Activate your virtual environment 
2. Run `PYTHONPATH=$(pwd) python -m pytest tests/ -v --cov=app --cov-report=html --cov-fail-under=70` 
    - Only integration tests `PYTHONPATH=$(pwd) python -m pytest tests/integration -v`
    - Only unit tests `PYTHONPATH=$(pwd) python -m pytest tests/unit -v`
3. Run `open htmlcov/index.html ` for a detailed coverage report
    - The project requires at least 70% coverage

## Monitoring/Health

To check the app’s status and exposed metrics:

1. Run `python -m flask run`
2. Open in your browser `http://127.0.0.1:5000`: 
  - Monitoring endpointL=: `http://127.0.0.1:5000\metrics`
    - Displays Prometheus-compatible metrics (request counts, latencies, errors). 
  - Health endpoint: `http://127.0.0.1:5000\health`
    - Returns a JSON response like: {"details":{"app":"ok","database":"ok"},"status":"ok"}


## Troubleshooting

**Issue: API rate limit exceeded**
- The free Spoonacular API has a limit of 150 requests/day
- The app caches results to minimize API calls

**Issue: Database not found**
- Run `python create_db.py` to initialize the database (for local run)

**Issue: Module not found errors**
- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Issue: Azure deployment stopped**
- You may see: `"Error 403 - This web app is stopped."`
- This happens if the Azure app service is not running.


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
- **Choose sorting preference** → most matched ingredients, least missing ingredients, or default (weighted)
- **Simple & clean interface** → built with Flask templates


## Tech Stack

**Backend & Framework**
- Python 3.11 + Flask

**Database**
- PostgreSQL (Production on Azure)
- SQLite (Local development/testing)

**Frontend**
- HTML/CSS with Jinja2 templating

**External APIs**
- Spoonacular Recipe & Ingredient API

**Testing**
- pytest with 95% code coverage (176 tests: 99 unit, 77 integration)

**DevOps & Infrastructure**
- Docker containerization
- GitHub Actions CI/CD
- Azure App Service deployment
- Azure Container Registry

**Monitoring**
- Custom `/health` endpoint
- Prometheus-compatible `/metrics` endpoint


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
        `docker run -p 8000:8000 shelfchef`

### Option 2: Access Deployed App 
1. Navigate to [https://shelfchef-eeaeeyemgpggdshz.westeurope-01.azurewebsites.net](https://shelfchef-eeaeeyemgpggdshz.westeurope-01.azurewebsites.net)
    


## Using the App

1. Enter ingredients you have (e.g., "chicken, rice, tomatoes") one by one
2. Click "Find Recipes" to see matching recipes
3. Choose to sort your recipes as you prefer: most matching ingredients, least missing ingredients, or default (a weighted combination!)
4. Click on any recipe to view full details and instructions
5. Save your favorite recipes or create your own!
6. Manage your saved recipes (edit, delete, create) as you wish. Just keep in mind, you can only edit recipes that are yours!


## Running Tests

### Prerequisites
Ensure you're in the activated virtual environment:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Run All Tests with Coverage
```bash
PYTHONPATH=$(pwd) pytest tests/ -v --cov=app --cov-report=html --cov-fail-under=70
```

### Run Specific Test Suites
```bash
# Unit tests only (fast, isolated)
python -m pytest tests/unit

# Integration tests only (slower, with database)
python -m pytest tests/integration
```

### View Coverage Report
```bash
# macOS/Linux
open htmlcov/index.html

# Windows
start htmlcov/index.html

# Linux (alternative)
xdg-open htmlcov/index.html
```

### Current Coverage: **94.53%** (190 tests)
- Unit tests: 99
- Integration tests: 117
- Minimum required: 70%

## Monitoring/Health

To check the app’s status and exposed metrics:

1. Run `python -m flask run`
2. Open in your browser `http://127.0.0.1:5000`: 
  - Monitoring endpoint=: `http://127.0.0.1:5000\metrics` (local) or `https://shelfchef-[...].azurewebsites.net/metrics` (production)
    - Displays Prometheus-compatible metrics (request counts, latencies, errors). 
  - Health endpoint: `http://127.0.0.1:5000\health` (local) or `https://shelfchef-[...].azurewebsites.net/health` (production)
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
- The Azure App Service may be paused 
- Contact the repository maintainer to restart the service
- Alternatively, run locally following the setup instructions


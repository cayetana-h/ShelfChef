# ShelfChef Refactor & Deployment Report

This report summarizes the improvements, refactoring, testing, CI/CD, database changes, and monitoring features implemented in the ShelfChef project.

---

## 1. Database & Configuration Improvements

- **Centralized SQLite connections**  
  Replaced scattered `sqlite3.connect` calls with a `db_connection()` context manager to automatically handle opening/closing connections.

- **Configurable DB path**  
  `current_app.config.get("DATABASE_PATH")` replaces hardcoded `"recipes.db"`, allowing overrides in Flask apps, tests, or Docker containers.

- **Centralized DB access**  
  All CRUD and caching functions now use `db_connection()` internally; `_get_connection()` is no longer called directly outside the context manager.

- **Minor cleanups**  
  Removed redundant global `DB_PATH`.

---

## 2. Flask Routes Refactor

- Removed `init_routes(app)` and un-nested route functions under the blueprint.
- Removed local `recipe_cache = {}`; now use `current_app.recipe_cache`.
- Updated imports and blueprint registration to attach routes cleanly in `__init__.py`.
- Routes now strictly handle HTTP requests; all business logic (form validation, sorting, API calls) moved to helper functions in `utils.py`.

---

## 3. API Client Refactor

- Removed module-level `ingredient_cache`; attached it to Flask app via `current_app.ingredient_cache`.
- Extracted helper functions for query preparation, cache handling, API interactions, and recipe formatting.
- Main functions (`search_recipes` and `get_ingredient_suggestions`) now clearly separate cache and API logic.
- Optional `requester` parameter added for easy testing/mocking.

---

## 4. Storage & DB Utilities

- Introduced `DatabaseInitializer` and `RecipeStorage` classes for DB setup and CRUD operations.
- Moved caching logic (`get_cached_response`, `save_cached_response`) into `db_utils.py` to reduce circular imports and separate concerns.
- `init_db(app)` added as public wrapper for cleaner app initialization.

---

## 5. Testing Improvements

- **Unit Tests:** isolated functions, fast execution, mocks/stubs for dependencies.
- **Integration Tests:** workflows, DB interactions, cache usage, realistic component interactions.
- **Coverage:** ensured ≥70% across `app/` modules.
- **Key patterns:** fixtures for in-memory DB, mocking external API calls, testing edge cases, descriptive test names.

---

## 6. Continuous Integration (CI)

- CI workflow using `.github/workflows/ci.yml`.
- Steps:
  - Checkout code
  - Setup Python 3.11
  - Install dependencies
  - Run tests with coverage (`--cov=app`, `--cov-fail-under=70`)
  - Build Docker image
  - Upload coverage report as artifact
- CI pipeline runs successfully on pushes; tests pass with minimum coverage, Docker builds complete.

---

## 7. Continuous Deployment (CD)

- **Azure Deployment**:
  - Backend updated for cloud-ready configuration using environment variables.
  - GitHub Secrets for CI/CD; Azure App Settings for production.
- **Publish profile** used instead of blocked Service Principal workflow.
- Workflow:
  ```yaml
  uses: azure/webapps-deploy@v2
  with:
    app-name: shelfchef
    publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
    images: cayetanah/shelfchef:latest
- Docker image compatible with Azure; automated deployment after CI passes.

---

## 8. Database & Deployment Fixes
- Switched to Python 3.11 for compatibility with PostgreSQL and SQLAlchemy.
- Resolved circular import in `storage.py`.
- Configured `DATABASE_UR`L environment variable for Azure PostgreSQL.
- Verified local DB connection and template route accessibility.
- Dockerfile updated for PostgreSQL dependencies and Gunicorn serving.

---

## 9. Monitoring & Health
- Added `/health` endpoint: returns JSON with app and database status.
- Added `/metrics` endpoint using `prometheus_client` for request count, latency, and error tracking.
- Challenges:
  - Non-blocking DB checks for `/health`.
  - Avoiding double-counting requests in metrics.
  - Verified metrics locally without full Prometheus/Grafana setup.

---

## 10. Outcome
- Refactored, modular, and testable codebase.
- CI/CD pipeline fully functional.
- Azure deployment with PostgreSQL backend working.
- API caching and health/metrics monitoring integrated.
- Comprehensive unit and integration test coverage.
# Tests

All tests run on an in-memory SQLite database. They never touch `database.db` or your Postgres database,
and no extra packages are needed beyond `requirements.txt` (pytest, pytest-asyncio, httpx).

```bash
# from the project root, with the virtual environment active
pytest tests/unit -v           # unit tests: mocks only, no database
pytest tests/integration -v    # integration tests: real database + HTTP calls
pytest -v                      # everything
```

* `tests/unit/` - business rules, schemas, security helpers and auth dependencies in isolation (repositories are mocked).
* `tests/integration/` - repositories, services, the JSON API (`/api/...`) and the HTML pages against a real in-memory database
  (SQLite with foreign keys switched on, so it behaves like PostgreSQL).
* `postman/CampusStay_API.postman_collection.json` - API tests for Postman. Start the app first
  (`python manage.py init` then `python manage.py run`), import the file into Postman, set the `baseUrl`
  collection variable if your port is not 5000, then run the whole collection.
  Command-line alternative: `npx newman run postman/CampusStay_API.postman_collection.json`.

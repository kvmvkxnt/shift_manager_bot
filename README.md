# Shift Manager Bot Backend

## Backend File Structure

```tree
shift_manager_bot/
├── pyproject.toml
├── README.md
├── docker-compose.yml
├── Dockerfile
├── .env
│
├── src/
│   └── shift_manager_bot/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database/
│       │   ├── base.py
│       │   ├── session.py
│       │   └── models/
│       │       ├── user.py
│       │       ├── shift.py
│       │       └── task.py
│       ├── api/
│       │   ├── router.py
│       │   └── routes/
│       │       ├── users.py
│       │       ├── shifts.py
│       │       └── tasks.py
│       ├── bot/
│       │   ├── handlers/
│       │   │   ├── common.py
│       │   │   ├── manager.py
│       │   │   └── employee.py
│       │   ├── keyboards/
│       │   │   ├── manager.py
│       │   │   └── employee.py
│       │   └── middlewares/
│       │       ├── auth.py
│       │       └── db.py
│       ├── services/
│       │   ├── user_service.py
│       │   ├── shift_service.py
│       │   └── task_service.py
│       └── scheduler/
│           └── jobs.py
│
└── tests/
    ├── conftest.py           # Shared fixtures (db, client, fake data)
    ├── test_api/
    │   ├── test_users.py
    │   ├── test_shifts.py
    │   └── test_tasks.py
    ├── test_bot/
    │   ├── test_handlers.py
    │   └── test_middlewares.py
    └── test_services/
        ├── test_user_service.py
        ├── test_shift_service.py
        └── test_task_service.py
```

## Backend Tech Stack

- Python + aiogram 3.x — bot logic
- FastAPI — REST API for the Mini App to talk to
- PostgreSQL + SQLAlchemy (async) — database
- Redis — sessions and caching
- APScheduler — reminders and scheduled jobs
- Poetry — package management
- Docker + Docker Compose — local dev and deployment
- Railway — backend + database hosting

### Testing Stack

- pytest — the standard for Python testing, no competition. Clean, simple, widely
  used.
- pytest-asyncio — essential since our entire app is async. Lets you write async
  test functions natively.
- pytest-mock — for mocking services, database calls, Telegram API calls etc.
- factory-boy — for generating test data (fake users, shifts, tasks) cleanly instead
  of manually creating objects in every test.
- httpx — for testing FastAPI endpoints. It has an async test client that works
  perfectly with FastAPI.

## Project Steps

1. Dependencies first.
  Add all packages via Poetry before writing a single line of code. Split into
  main dependencies and dev dependencies (testing tools). This way your environment
  is fully ready and you never interrupt coding to install something.
2. Config & environment.
  config.py — reads all environment variables from .env (database URL, bot token,
  Redis URL, secret key etc.) using pydantic-settings. Everything else in the app
  imports config from here. This goes first because literally every other module
  will need it.
3. Database foundation.
  SQLAlchemy base setup, async session factory, then the models — User, Shift,
  Task. Nothing works without this layer being solid.
4. Alembic migrations.
  Set up Alembic right after models so your database schema is managed properly
  from day one, not bolted on later.
5. Services layer.
  Business logic for users, shifts, tasks — pure Python, no Telegram, no FastAPI.
  Testable in isolation.
6. FastAPI routes.
  API endpoints that the Mini App will consume, built on top of services.
7. Bot handlers.
  aiogram handlers built on top of the same services.
8. Scheduler.
  APScheduler jobs — reminders etc.
9. Tests.
  Written alongside or right after each layer.

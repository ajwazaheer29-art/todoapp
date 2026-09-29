# Daymark — Task Management

A polished, responsive Django task manager with per-user task isolation, search, filters, sorting, statistics, and SQLite storage.

## Requirements

- Python 3.10 or newer
- Django (see `requirements.txt`)

The project uses your configured system Python; it does not create or require a virtual environment. Django 6.1 is already installed in the development environment.

## Run locally

```powershell
python --version
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. Register an account to get started. To create an administrator, run `python manage.py createsuperuser`.

## Production notes

Set `DJANGO_SECRET_KEY` to a unique secret, set `DJANGO_DEBUG=false`, and provide `DJANGO_ALLOWED_HOSTS` as a comma-separated list before deployment. Configure a production database by replacing `DATABASES` in `config/settings.py`; the task schema uses standard Django fields and is database-portable. Run `python manage.py check --deploy` and collect static files with `python manage.py collectstatic` as part of deployment.

## Features

- Signup, login, logout, and owner-scoped access to tasks
- Dashboard summary cards, overdue detection, and task list
- Task create, view, edit, delete confirmation, and reopen/complete actions
- Search across title and description; combined status, priority, and due-date filters
- Database-level sorting and pagination
- Accessible responsive UI with CSRF-protected mutation forms
- Automated model, validation, authentication, and access-control tests

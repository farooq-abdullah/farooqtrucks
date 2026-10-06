# Django code walkthrough

This guide follows the backend file by file. The structure groups related work
instead of creating a separate file for every small function. Django entry points
keep their conventional names; calculation and map code live in service modules.

## The request flow

```text
React submits the four trip inputs
  -> config/urls.py -> trips/urls.py
  -> views.py -> serializers.py validates the JSON
  -> routing/ resolves locations and fetches a road route
  -> hos/ schedules driving, work and rests
  -> routing/ attaches planned stop positions
  -> logs.py generates complete daily sheets
  -> views.py returns JSON -> React displays it
```

The frontend pages use `/plan`, `/route`, and `/logs`. Each serves the same
`index.html` in production; React reads the pathname and displays that page.
The `/api/` prefix is reserved for Django's JSON endpoints.
`/api/locations/search/` provides the location dropdown suggestions. It uses
Photon and a bundled index of verified common cities. Trip submission resolves
the same place data and checks the resolved country and area.

## File map and lesson order

All paths below are relative to `backend/`.

| Order | File | Responsibility |
| --- | --- | --- |
| 1 | `manage.py` | Run Django commands such as `runserver`, `check` and `test`. |
| 2 | `config/settings.py` | Configure apps, middleware, API behavior, providers and static files. |
| 3 | `config/urls.py` | Connect the `/api/` prefix and serve React at `/plan`, `/route`, and `/logs`. |
| 4 | `trips/urls.py` | Connect health, location search, and planning endpoints to their views. |
| 5 | `trips/serializers.py` | Declare input fields and reject invalid data. |
| 6 | `trips/clock.py` | Infer the origin timezone and build the default departure timestamp. |
| 7 | `trips/views.py` | Coordinate a request and return a response. |
| 8 | `frontend/src/lib/assumptions.js` (from repository root) | Explain the backend's returned planning parameters. |
| 9 | `trips/services/routing/client.py` | Make bounded provider requests, reuse connections, and translate provider errors. |
| 10 | `trips/services/routing/geocoding.py` | Search suggestions, validate place countries, and resolve coordinates and nearby place names. |
| 11 | `trips/services/routing/routes.py` | Convert an OSRM response into our route format. |
| 12 | `trips/services/hos/rules.py` | Declare duration limits and the `Leg` data structure. |
| 13 | `trips/services/hos/planner.py` | Keep driver clocks together with the methods that update them. |
| 14 | `trips/services/hos/schedule.py` | Assemble both trip legs and expose completion clocks. |
| 15 | `trips/services/routing/locations.py` | Follow the route polyline and attach estimated places and road names. |
| 16 | `trips/services/logs.py` | Split events at midnight and fill each sheet to 24 hours. |
| 17 | `config/wsgi.py` | Create the application callable used by production servers. |
| 18 | `trips/tests/` | Verify the API and scheduling behavior. |

The `__init__.py` files mark packages. The HOS and routing package files also
re-export their public names, so existing imports remain readable. Their modules
contain the actual implementations. No model or migration files are needed because
this version calculates requests without saving database records.

## Lesson 1: manage.py

### What this file does

`manage.py` is the project's command-line entry point. For example, from the
repository root:

```powershell
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

The virtual environment's Python runs this file. It selects the project's settings
and passes the requested command to Django. Django then starts its development
server. The trip's HTTP request is handled by the URL/view/service flow above.

### The opening description

```python
"""Django's command-line entry point. No database or migrations are required."""
```

This is the module's docstring. It documents the file; it does not disable a
database. The dummy database backend is configured in `config/settings.py`.

### The imports

```python
import os
import sys
```

`os` gives access to process environment variables. We use it to tell Django
which settings module to load. `sys` gives access to the command-line arguments
passed to this Python process. Both are included with Python.

### The entry-point guard

```python
if __name__ == "__main__":
```

When Python runs this file directly, its `__name__` is `"__main__"`, so the
indented block runs. Importing the file gives it a module name instead, so an
import does not unexpectedly run a Django command.

### Choosing the settings

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

`DJANGO_SETTINGS_MODULE` is Django's environment-variable name for the settings
module. `config.settings` is a Python import path pointing to `config/settings.py`.
`setdefault` uses this value only if the variable is absent, preserving an existing
configuration. This environment value belongs to the current process; this line
does not permanently edit Windows environment settings or read a `.env` file.

### Loading Django's command runner

```python
from django.core.management import execute_from_command_line
```

This function belongs to Django, rather than to our app. The import is inside
the guarded block and follows selection of the settings module.

### Passing the command to Django

```python
execute_from_command_line(sys.argv)
```

For the example above, `sys.argv` is approximately:

```python
["backend\\manage.py", "runserver", "127.0.0.1:8000"]
```

The Python executable's path is not part of this list. Django interprets
`runserver` as the command and the address as its argument. The same file can
run other commands:

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py test trips.tests
```

`check` runs Django's project checks. `test trips.tests` runs our backend tests.
They do not need a database in this project. Running `manage.py` without a command
shows Django's available commands.

### Small practice exercise

Run `check` from the repository root. Trace what happens: Python enters the guarded
block, sets the settings module if needed, imports the command runner and passes
`["backend\\manage.py", "check"]` to it. No trip is planned by that command.

The next lesson is `config/settings.py`: the configuration selected by this file.

## Code style

`pyproject.toml` sets the Ruff formatter and import/check rules. The development
dependency is in `backend/requirements-dev.txt`; production requirements remain in
`backend/requirements.txt`. Run the commands in the README to check formatting and
basic Python errors. Tests verify behavior separately from formatting.

# Project Structure Documentation

This document describes the purpose of each folder and major file in the project.

## Root Directory
- **manage.py**: Django's command-line utility for administrative tasks.
- **db.sqlite3**: SQLite database file (default for Django projects).
- **requirements.txt**: Python dependencies for the project.
- **runtime.txt**: Specifies the Python runtime version (for deployment).
- **Procfile**: Used for deployment (e.g., on Heroku) to declare process types.
- **README.md**: Project overview and basic instructions.
- **DEPLOYMENT.md**: Detailed deployment instructions.
- **DEPLOYMENT_CHECKLIST.md**: Checklist for deployment readiness.
- **MEDIA_HANDLING.md**: Instructions for handling media files (uploads, images).
- **QUICKSTART.md**: Quick start guide for running the project.
- **check-deployment.sh, deploy.sh**: Shell scripts for deployment automation.

## Folders
- **housing_project/**: Main Django project configuration (settings, URLs, WSGI/ASGI entry points).
  - `__init__.py`: Marks the directory as a Python package.
  - `settings.py`: Django settings (database, apps, middleware, etc.).
  - `urls.py`: URL routing for the project.
  - `wsgi.py`, `asgi.py`: Entry points for WSGI/ASGI servers.

- **listings/**: Main app for house listings, landlord/customer features, and messaging.
  - `__init__.py`: Marks the directory as a Python package.
  - `admin.py`: Django admin customizations for the app.
  - `apps.py`: App configuration.
  - `forms.py`: Django forms for user input (registration, listing, messaging, etc.).
  - `media_storage.py`: Custom media storage logic (if any).
  - `models.py`: Database models (Listing, Message, LandlordProfile, etc.).
  - `tests.py`: Automated tests for the app.
  - `urls.py`: URL routing for the app.
  - `views.py`: View functions (business logic for web pages).
  - **migrations/**: Database schema migrations.
  - **static/**: App-specific static files (CSS, JS, images).
  - **templates/**: HTML templates for rendering web pages.

- **media/**: Uploaded media files (images, documents, etc.).
- **staticfiles/**: Collected static files for deployment (do not edit directly).

---

# How to Use
- Edit code in the `listings/` app for business logic and features.
- Add new templates in `listings/templates/listings/`.
- Place static assets in `listings/static/listings/`.
- Use `media/` for user-uploaded content.
- Run/manage the project using `manage.py`.

For more details, see the individual markdown files in the root directory.

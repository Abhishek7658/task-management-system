# TeamFlow Backend

Django REST Framework backend for the TeamFlow Project & Task Management System.

## Stack
- Python 3.11+
- Django 5.2
- Django REST Framework
- PostgreSQL
- JWT authentication (Simple JWT)
- Swagger / OpenAPI documentation

## 1. Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
copy .env.example .env
# macOS/Linux: cp .env.example .env
```

Update database credentials in `.env`.

## 2. Start PostgreSQL

Using Docker:

```bash
docker compose up -d db
```

Alternatively, use an existing PostgreSQL server and update `.env`.

## 3. Run migrations and start the API

```bash
python manage.py makemigrations accounts teams projects tasks activity
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API base URL: `http://127.0.0.1:8000/api/`

Swagger UI: `http://127.0.0.1:8000/api/docs/`  
OpenAPI schema: `http://127.0.0.1:8000/api/schema/`  
Django admin: `http://127.0.0.1:8000/admin/`

## Authentication

Obtain tokens:

`POST /api/auth/token/`

```json
{
  "username": "your-username",
  "password": "your-password"
}
```

Refresh token:

`POST /api/auth/token/refresh/`

Use the access token on protected endpoints:

`Authorization: Bearer <access_token>`

Public registration creates a **Member** account only. Administrators can create users and assign roles through `/api/users/`. Do not expose administrator account creation publicly.

## Main API endpoints

| Module | Endpoint | Methods |
|---|---|---|
| Current user | `/api/users/me/` | GET |
| User management | `/api/users/` | GET, POST (admin) |
| Teams | `/api/teams/` | GET, POST, PATCH, DELETE |
| Team members | `/api/teams/{id}/members/` | POST |
| Projects | `/api/projects/` | GET, POST, PATCH, DELETE |
| Project members | `/api/projects/{id}/members/` | POST |
| Tasks | `/api/tasks/` | GET, POST, PATCH, DELETE |
| Task comments | `/api/tasks/{id}/comments/` | GET, POST |\n| Task activity history | `/api/tasks/{id}/history/` | GET |
| Dashboard | `/api/dashboard/` | GET |

### Useful filters

Tasks support:
- `status`: `todo`, `in_progress`, `in_review`, `complete`
- `priority`: `low`, `medium`, `high`, `urgent`
- `project`: project ID
- `assignee`: user ID
- `due_date`: YYYY-MM-DD
- `search`: searches task title and description

Projects and teams support `search`.

## Roles and access rules

- **Administrator**: organization-wide access and user administration.
- **Manager**: creates and manages projects/teams and manages tasks within accessible projects.
- **Member**: views assigned tasks and relevant project/team information; can update their assigned task status and comment.

All protected API endpoints require authentication. Object querysets are scoped by role to avoid exposing unrelated records.

## Notes for frontend integration

- Dates use ISO format (`YYYY-MM-DD`).
- API responses are JSON.
- Task status values are `todo`, `in_progress`, `in_review`, `complete`.
- Task priority values are `low`, `medium`, `high`, `urgent`.
- The API uses pagination (DRF default page size: 20).
- CORS origins are configured through `CORS_ALLOWED_ORIGINS` in `.env`.

## Before deployment

- Set `DEBUG=False` and a strong unique `SECRET_KEY`.
- Set production `ALLOWED_HOSTS` and CORS origins.
- Use managed PostgreSQL credentials and HTTPS.
- Review role permissions against the team's final access policy.
- Run automated tests and security checks in the deployment environment.

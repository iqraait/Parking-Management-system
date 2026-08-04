# Enterprise Parking Management System (ParkOS)

A robust, enterprise-grade, Apple-inspired full-stack Django application for commercial parking logic.

## 🌟 Delivered Features & Implementation Details

### 1. Apple-Inspired Premium Dashboard 
The design system implements a **Sherwin Williams Rice Grain** theme with Apple design influences:
- **Glassmorphism:** Navigation menus, floating docks, and dashboard cards use `backdrop-filter: blur(20px)` and semi-transparent backgrounds with subtle shadows.
- **Bubble Navigation:** Mimics the iOS floating dock. An animated `bubble-nav-container` remains fixed at the bottom with expanding icons using pure CSS transitions (`style.css`).
- **Responsive Animations:** HTMX loading states, subtle hover lifting (`transform: translateY(-2px);`), and entry fade-ins.

### 2. Full Stack Architecture
- **Backend Framework:** Django 5+ running behind `gunicorn` with `whitenoise`.
- **Frontend Strategy:** Pure Django Templates + Bootstrap 5 + Alpine.js (for reactive toggle states) + HTMX (dynamic pagination, form submissions, and search logic without full page reloads).
- **APIs:** Django REST Framework (DRF).

### 3. Database Schema (PostgreSQL)
Three modular Django Apps handle the data layer:
1. **`accounts` App:** Custom `User` model implementing Role-Based Access Control (RBAC). Granular staff permissions track access for modules (View Dashboard, Manage Exits).
2. **`parking` App:** `ParkingZone` stores constraints and dynamic hourly pricing rules. `VehicleRecord` manages the ticket entity lifecycle (Entry vs Exit timelines, duration calc).
3. **`payments` App:** `PaymentMethod` and `Payment` entity explicitly separating the parking lifecycle from financial validation/discounting.
4. **`analytics` App**: `AuditLog` captures granular system activities.

### 4. Open-API (Swagger) Generation
We integrated `drf_spectacular`.
To view Swagger API endpoints:
1. Ensure the web server is running.
2. Navigate to: `http://localhost:8000/api/schema/swagger-ui/`
3. Redoc alternative: `http://localhost:8000/api/schema/redoc/`

### 5. Automated CI/CD & Environments
- Provided `Dockerfile` utilizes a minimal `python:3.12-slim` image.
- Static assets are compressed and served effectively via `Whitenoise` combined with Django's `collectstatic`.
- The `docker-compose.yml` configures:
  - Postgres 15 database instance.
  - Redis cache instance (ready for Celery usage or caching DRF views).
  - The Web App container.
  - A Celery worker container.

---

## 🚀 Deployment Guide

### Local Development Setup
If you want to run this purely with SQLite for rapid UI testing (Windows):

```bash
# 1. Activate your virtual environment and install deps
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Apply the database schemas
python manage.py makemigrations
python manage.py migrate

# 3. Create a Super Admin
python manage.py createsuperuser

# 4. Start the server
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000` to see the Apple-inspired Dashboard featuring dynamic stats and the animated Bubble Navigation interface.

### Production Environment (Docker & PostgreSQL)

In a commercial environment, avoid SQLite and deploy onto a Linux server (e.g. AWS EC2, DigitalOcean) utilizing the provided `docker-compose.yml` and `Dockerfile`.

1. **Upload your code** to the host machine.
2. **Setup environment variables** in a `.env` file containing the `POSTGRES_PASSWORD`, `DATABASE_URL`, and a secret `SECRET_KEY`.
3. **Build and spin up the cluster**:
   ```bash
   docker-compose up -d --build
   ```
4. **Run production migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```
5. **Reverse Proxy via Nginx**: Connect an instance of Nginx to point domain traffic directly to `127.0.0.1:8000`.

### ER Diagram Overview
- `User (1) <---> (M) AuditLog`
- `User (M) <---> (M) ParkingZone (Assign Staff)`
- `ParkingZone (1) <---> (M) VehicleRecord`
- `VehicleRecord (1) <---> (1) Payment`
- `PaymentMethod (1) <---> (M) Payment`

## Code Highlights for UI Expectations
See `static/css/style.css` containing variables:
- `--rice-grain: #D5CFAF;`
- `--apple-light-bg: #FBFBFD;`
And elements `.glass-card`, `.bubble-nav`, which apply `backdrop-filter: blur(20px)` and `-webkit-backdrop-filter` attributes across elements.

# UniRides — Backend

REST API for a university ride-sharing application, developed individually by [Daniel Rossi](https://github.com/danirso) as an undergraduate final project (TCC).

The backend manages drivers, passengers, vehicles, ride requests and reviews. It uses PostgreSQL/PostGIS to find rides whose routes pass near a passenger's pickup and destination points, in the correct travel order.

Companion application: [Flutter frontend](https://github.com/danirso/tcc_caronas_frontend).

## Stack and features

- **Python / FastAPI:** REST endpoints, request validation and interactive API documentation.
- **SQLAlchemy / GeoAlchemy2 / PostgreSQL / PostGIS:** persistence and spatial queries; Alembic tracks schema migrations.
- **Authentication:** bcrypt password hashing, JWT access tokens and email activation restricted to supported university domains.
- **Ride management:** vehicles, ride lifecycle, passenger requests, acceptance, cancellation and participant reviews.
- **Google Maps Directions:** route details and encoded polylines, converted into PostGIS geometries for matching.
- **Pytest / GitHub Actions:** API tests with a real PostGIS database and mocked external services.
- **Hosted setup:** Azure App Service runs the API; Supabase provides hosted PostgreSQL/PostGIS. Local execution uses separate Docker services.

## Run locally

Requirements: Python 3, a virtual environment, Bash, and Docker with the Compose plugin. CI uses Python 3.12; the local suite has also passed with Python 3.14. Commands below target Linux/macOS or a compatible shell such as WSL.

Only PostGIS and the local email inbox run in Docker. The API runs in your Python environment.

```bash
git clone https://github.com/danirso/tcc-caronas-backend.git
cd tcc-caronas-backend
python3 -m venv venv
venv/bin/python -m pip install -r requirements-dev.txt
./scripts/run-local.sh
```

The script checks the virtual environment, starts PostGIS and Mailpit, applies `alembic upgrade head`, then starts Uvicorn. It supplies local development settings without requiring a `.env` file or a Supabase account.

| Service | Local address |
| --- | --- |
| Swagger UI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| API health endpoint | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| Mailpit inbox | [http://127.0.0.1:8025](http://127.0.0.1:8025) |
| Application database | `127.0.0.1:5434` |
| Local SMTP | `127.0.0.1:1025` |

To explore authentication in Swagger UI:

1. Register through `POST /auth/register`. Registration accepts `puccampinas.edu.br`, `puc-campinas.edu.br` and `dac.unicamp.br` email domains.
2. Open Mailpit and follow the activation link. Local email stays in Mailpit rather than being delivered to the recipient.
3. Use **Authorize** in Swagger UI with the registered email as the username and the account password.
4. Try the authenticated user, vehicle and ride endpoints.

UniRides is an academic project, not an official service of the universities associated with those domains. API messages and parts of the source code are in Portuguese.

### Google Maps key

Starting the API, inspecting Swagger UI and running the tests do not require a Google Maps key. Creating a ride calls Google Maps Directions and requires your own valid key with that API enabled.

To pass a key to the local process without placing it in a command saved to shell history:

```bash
read -rs GOOGLE_MAPS_API_KEY
export GOOGLE_MAPS_API_KEY
./scripts/run-local.sh
```

Without a valid key, ride creation through the external routing service will fail. The automated tests mock that integration.

### Stop local services

Stop Uvicorn with Ctrl+C, then stop the supporting services:

```bash
docker compose -f compose.local.yml down
```

Application data persists in a Docker volume. To deliberately reset the local application database, use `docker compose -f compose.local.yml down -v`.

## Run the tests

After installing the development dependencies:

```bash
./scripts/test-local.sh
```

The script selects `venv/bin/python`, checks that Pytest is installed and starts a dedicated PostGIS instance on `127.0.0.1:5433`. It overrides database URLs and credentials for the test process. Tests create and drop application tables in this disposable database, which is separate from the local application database and the hosted Supabase projects.

You can pass Pytest options through the script, for example:

```bash
./scripts/test-local.sh -q tests/test_rideRequest.py
```

Set `PYTHON_BIN` to use a different virtual environment, for example `PYTHON_BIN=.venv/bin/python ./scripts/test-local.sh`.

The current suite contains **68 tests**:

| Area | Tests |
| --- | ---: |
| Authentication and email activation | 9 |
| User profiles | 8 |
| Vehicles | 8 |
| Rides and geospatial matching | 12 |
| Ride requests | 13 |
| Reviews | 17 |
| Health endpoint | 1 |

The suite exercises the HTTP API through FastAPI's TestClient with real database operations. It includes successful flows, validation failures, ownership checks, ride state transitions and spatial matching cases. Email delivery is mocked; tests that create routes mock Google Maps responses. A cancellation regression test checks that using a request ID with a different ride ID returns 404 without changing request status or seat counts.

Clean up the disposable test database after the run:

```bash
docker compose -f compose.test.yml down -v
```

## How ride matching works

The API stores a ride's route as a PostGIS `LINESTRING`. A search filters for future, scheduled rides with available seats, excluding rides offered by the requesting user. It then checks:

- `ST_DWithin`, using geography casts, verifies that both passenger points are within the ride's allowed distance from the route, in meters.
- `ST_LineLocatePoint` verifies that the pickup point occurs before the destination along the route.

This is proximity and travel-order matching against a stored route. It does not calculate the exact extra driving time for a pickup or optimize multiple passenger stops.

## CI and deployment

The GitHub Actions configuration runs the test suite with Python 3.12 and a PostGIS service container on pull requests to `main`. The Azure workflow also calls that reusable test workflow before building the deployment artifact. Its dependency chain is **tests → build → deploy**; failed tests prevent the downstream jobs from running.

Deployment is triggered by pushes to `main` or manual dispatch. Azure login uses OpenID Connect and GitHub Actions secrets. Runtime application settings are configured separately in Azure App Service.

## Configuration and repository layout

The local scripts supply their own settings. For a custom environment, [.env.example](.env.example) lists the database, JWT, Google Maps and SMTP variables expected by the application. Copy it to `.env` and replace the placeholders for your environment. Swagger UI is enabled when `ENVIRONMENT=dev`.

```text
app/
  api/          API routers and authentication dependencies
  core/         Settings, security utilities and exceptions
  db/           Database engine and sessions
  models/       SQLAlchemy models
  schemas/      Pydantic request and response schemas
  services/     Google Maps integration
  utils/        Activation email delivery
alembic/        Database migrations
tests/          Pytest API tests and fixtures
scripts/        Local API and test runners
.github/        CI and Azure deployment workflows
```

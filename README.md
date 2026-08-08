# UpPing — Backend

Backend central de **UpPing**, app de diagnóstico de red (latencia, pérdida de
paquetes e historial de tests de ping). El test de red corre en el cliente; este
servicio autentica usuarios y sincroniza sus datos entre plataformas
(Android, iOS y web).

## Stack

- Python 3.12+, FastAPI
- PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic
- Pydantic v2 + pydantic-settings
- JWT (access + refresh) con python-jose, passlib + bcrypt
- pytest + httpx (integración contra PostgreSQL real)
- Docker + docker-compose

## Estructura

```
app/
  main.py            # app factory, CORS, logs estructurados, routers
  core/              # config, security (JWT/bcrypt), rate limiter
  models/            # User, PingTest, UserSettings, RefreshToken
  schemas/           # schemas Pydantic v2
  api/               # deps (get_current_user) y routers: auth, tests, settings, users
  db/                # base.py, session.py (async engine + get_db)
alembic/             # migraciones (variante async)
tests/               # tests de integración
```

## Setup local

Requisitos: Docker Desktop. En Windows el puerto `5432` suele estar ocupado por
un PostgreSQL local, por eso el contenedor publica la DB en **5433** y el API
en **8000**.

```bash
# 1. Levantar DB + API (el API corre las migraciones al arrancar)
docker compose up -d

# 2. Ver logs
docker compose logs -f api
```

Una vez arriba:

- API: http://localhost:8000
- Documentación interactiva (Swagger): http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json (también hay una copia en `openapi.json`)

### Migraciones

Se ejecutan automáticamente al arrancar el contenedor del API. Para correrlas a
mano (fuera de Docker):

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows (source .venv/bin/activate en Linux/macOS)
pip install -r requirements.txt

alembic upgrade head            # aplica migraciones pendientes
alembic revision --autogenerate -m "descripcion"   # nueva migración
```

### Variables de entorno

Copiá `.env.example` a `.env` (ya existe en el repo). Variables:

| Variable | Descripción | Default |
|---|---|---|
| `DATABASE_URL` | URL async de PostgreSQL | `postgresql+asyncpg://postgres:postgrespassword@localhost:5433/app_db` |
| `JWT_SECRET` | Secreto para firmar tokens | — |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_EXPIRATION` | Vida del access token (min) | `30` |
| `REFRESH_TOKEN_EXPIRATION_DAYS` | Vida del refresh token (días) | `30` |
| `CORS_ORIGINS` | Lista JSON de orígenes permitidos | `["http://localhost:3000"]` |
| `LOGIN_MAX_ATTEMPTS` | Intentos máx de login por ventana | `5` |
| `LOGIN_WINDOW_SECONDS` | Ventana del rate limiter (seg) | `60` |

## Tests

Los tests crean la DB `app_db_test` en el Postgres de Docker (puerto 5433),
corren cada suite contra ella y la borran al terminar.

```bash
docker compose up -d db         # Postgres debe estar corriendo
.\.venv\Scripts\activate
pytest -v                       # 28 tests
```

Cubren: registro, login, refresh/logout, rate limiting, crear/listar/filtrar/
paginación/detalle/delete de tests, export CSV, settings, `/me`, y el
aislamiento entre usuarios (un usuario nunca puede leer ni borrar tests de otro).

## Endpoints

### Auth (`/auth/*`, sin token)
- `POST /auth/register` — `{email, password, display_name}` → 201
- `POST /auth/login` — `{email, password}` → `{access_token, refresh_token, ...}` (rate limit: 5/min por IP)
- `POST /auth/refresh` — `{refresh_token}` → rota y devuelve tokens nuevos
- `POST /auth/logout` — `{refresh_token}` → invalida el refresh token

### Tests (`/tests/*`, requiere `Authorization: Bearer <token>`)
- `POST /tests` — sube un resultado
- `GET /tests?limit=&offset=&target_ip=` — lista paginada `{items, total, limit, offset}`
- `GET /tests/export` — CSV con todo el historial del usuario
- `GET /tests/{id}` — detalle (404 si no existe o no es del usuario)
- `DELETE /tests/{id}` — borra (solo del usuario autenticado)

### Configuración
- `GET /settings` — configuración del usuario (defaults: 1000ms, 1500ms, csv on, perf off)
- `PATCH /settings` — actualiza uno o más campos

### Perfil
- `GET /me` — email, display_name, license_tier, created_at, total_tests
- `PATCH /me` — actualiza `display_name`

Todos los errores siguen el formato `{"detail": "mensaje"}` con el status code
correcto (401 no autenticado, 403 sin permiso, 404 no encontrado, 409 email
duplicado, 422 validación, 429 rate limit). Todo query de datos se filtra por
`user_id` del token.

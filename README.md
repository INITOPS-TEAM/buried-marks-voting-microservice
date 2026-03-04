# Voting Service

Microservice for managing internal voting and role promotions.

## Overview

Isolated microservice that handles three types of votes:
ban voting, level promotion (1→2), and senior promotion (2→3).
Votes close automatically after 24 hours via a background scheduler.

## Tech Stack

- **Python** 3.10
- **FastAPI** — web framework
- **SQLAlchemy** 2.0 — ORM (async)
- **PostgreSQL** — database
- **Alembic** — migrations
- **APScheduler** — background job for auto-closing polls
- **httpx** — HTTP calls to auth-service
- **PyJWT** — JWT decoding (ES256)
- **Docker** + **docker-compose**

## Voting Types

| Type | Initiated by | Voters | Success condition | Result |
| ------ | ------------- | -------- | ------------------- | -------- |
| `ban` | `is_inspector=True` | All active users | >50% of total eligible | Account banned |
| `level_up` | `role="1"` (self) | `role="2"` and `role="3"` | >50% of votes cast | Role changed to `"2"` |
| `level_top` | `role="2"` (self) | `role="3"` only | ≥80% of votes cast | Role changed to `"3"` |

## API Endpoints

| Method | Path | Description |
| -------- | ------ | ------------- |
| `GET` | `/healthcheck` | Service health check |
| `POST` | `/api/polls/` | Create a new poll |
| `POST` | `/api/polls/{id}/vote` | Cast a vote |
| `GET` | `/api/polls/{id}` | Get poll status |
| `GET` | `/api/polls/{id}/result` | Get poll result |

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:

```bash
DATABASE_URL=postgresql://user:password@db:5432/voting_db
DB_USER=
DB_PASSWORD=
DB_NAME=
PGADMIN_EMAIL=
PGADMIN_PASSWORD=
PUBLIC_KEY_PATH=
DJANGO_SECRET_KEY= 
AUTH_SERVICE_URL=
```

### Run

```bash
docker compose up -d --build
```

Services started:

- `voting_app` — FastAPI app on <http://localhost/docs>
- `voting_db` — PostgreSQL on port 5432

### Migrations

Migrations run automatically on startup via:

```bash
alembic upgrade head
```

To create a new migration manually:

```bash
docker compose exec app alembic revision --autogenerate -m "description"
```

### API Documentation

Swagger UI is available at:

```text
http://localhost:8900/docs
```

## Authentication

All endpoints require a JWT token issued by `auth-service`:

```text
Authorization: Bearer <token>
```

The token is decoded using an ES256 public key (`ec_public.key`).
Token payload must contain: `user_id`, `role`, `inspector`.

## Integration with Auth Service

This service requires the following endpoints to be available in `auth-service`:

```text
GET  /api/users/count/               — total active users
GET  /api/users/count/?role=2        — users by role
POST /api/users/{id}/ban/            — ban user
PATCH /api/users/{id}/role/          — change user role
```

## Scheduler

A background job runs every minute to:

1. Find polls where `ends_at <= now()` and `status = "active"`
2. Count `for` and `against` votes
3. Evaluate success condition per poll type
4. Update poll status to `success` or `failed`
5. Trigger action in `auth-service` if successful

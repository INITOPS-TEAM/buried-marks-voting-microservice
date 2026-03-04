# Voting Service

Microservice for managing internal voting and role promotions.
This microservice is part of a mapping application.
Not for anyone else's use.

## Overview

Isolated microservice that handles three types of votes:
ban voting, level promotion (1→2), and senior promotion (2→3).
Votes close automatically after 24 hours via a background scheduler.
For correct operation, you also need to have an authorization service
and a frontend microservice.

## Tech Stack

- **Python**
- **FastAPI** - web framework
- **SQLAlchemy** - ORM (async)
- **PostgreSQL** - database
- **Alembic** - migrations
- **APScheduler** - background job for auto-closing polls
- **httpx** - HTTP calls to auth-service
- **PyJWT** - JWT decoding (ES256)
- **Docker** + **docker-compose**

## Voting Types

| Type | Initiated by | Voters | Success condition | Result |
| ------ | ------------- | -------- | ------------------- | -------- |
| `ban` | `is_inspector=True` | All active users | >50% of total eligible | Account banned |
| `level_up` | `role="1"` (self) | `role="2"`, `role="3"` and `role="4"` | >50% of votes cast | Role changed to `"2"` |
| `level_top` | `role="2"` (self) | `role="3"` and `role="4"` | ≥80% of votes cast | Role changed to `"3"` |

## Getting Started

### Prerequisites

- Other application microservices
- Docker
- Docker Compose (One for all microservices in the project. Located in a different repository.)

### Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

### Run

To obtain the dockercompose file, contact the project team lead.

```bash
docker compose up -d --build
```

Services started:

- `voting_service` — Listening at the port <http://localhost:8900>
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
To resolve requests to the `auth-service`, you need to have a Django secret key.

## Scheduler

A background job runs every minute to:

1. Find polls where `ends_at <= now()` and `status = "active"`
2. Count `for` and `against` votes
3. Evaluate success condition per poll type
4. Update poll status to `success` or `failed`
5. Trigger action in `auth-service` if successful

# FastAPI Project

A simple FastAPI service containerized for local development using Docker and docker-compose.

## Local development with Docker

This project uses `.env` for environment-specific configuration and a PostgreSQL dependency managed by `docker-compose`.

### Start the app locally

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Build and start the services:
   ```bash
   docker compose up --build
   ```
3. Open the API docs:
   ```text
   http://localhost:8000/docs
   ```

### Services

- `api` — FastAPI application running with `uvicorn`
- `db` — PostgreSQL database container

### Environment

The application loads configuration from `.env` via `app/core/config.py`.

Example values are provided in `.env.example`.

### Useful commands

- Rebuild and restart:
  ```bash
  docker compose up --build
  ```
- Stop services:
  ```bash
  docker compose down
  ```
- Run tests inside the app container:
  ```bash
  docker compose exec api pytest
  ```

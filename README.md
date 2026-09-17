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

## Phase 3 - Authorization

Implemented:
- `ADMIN` and `USER` roles
- Permission model and role-permission mapping
- `require_role()` and `require_permission()` FastAPI dependencies
- Admin-only role APIs
- Permission-protected user list/get APIs
- 401 for missing/invalid authentication and 403 for insufficient authorization

Run migrations before starting the application:

```bash
alembic upgrade head
```

The latest migration creates the default `USER` and `ADMIN` roles and seeds user-management permissions for `ADMIN`.

## Phase 4 - User CRUD

Implemented:
- paginated user listing with `page` and `page_size`
- filtering by username and email
- safe sorting by username, email, created_at, or updated_at
- user lookup by UUID
- PATCH user update with duplicate checks and email normalization
- permission-protected soft delete
- soft-deleted users are excluded from normal authentication and CRUD queries

Examples:

```text
GET /api/v1/users/?page=1&page_size=20&username=john&sort_by=created_at&sort_order=desc
GET /api/v1/users/{user_id}
PATCH /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
```

Admin authorization management also includes:

```text
GET  /api/v1/roles/
POST /api/v1/roles/
POST /api/v1/roles/{role_id}/permissions
PUT  /api/v1/roles/users/{user_id}
```


## Phase 7 - AWS

AWS deployment infrastructure is provided under `infra/terraform/`.

It covers:
- ECR
- ECS Fargate
- ALB
- RDS PostgreSQL
- ElastiCache Redis
- CloudWatch
- Secrets Manager
- VPC/private subnets/security groups
- GitHub Actions OIDC deployment workflow

Before deployment, review `infra/README.md` and run:

```bash
cd infra/terraform
terraform init
terraform plan
```

Do not commit `terraform.tfvars` or secret values.

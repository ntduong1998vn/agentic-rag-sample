---
description: create and run database migrations
---

# Database Migration Workflow

This workflow covers creating and running database migrations using Alembic.

## Create a New Migration

1. Ensure Docker PostgreSQL is running:
   ```bash
   docker-compose up -d postgres
   ```

2. Make changes to your SQLAlchemy models in `app/infrastructure/database/models.py`

// turbo
3. Generate a new migration file automatically:
   ```bash
   uv run alembic revision --autogenerate -m "description of your changes"
   ```

4. Review the generated migration file in `alembic/versions/` directory

5. Edit the migration file if needed to add custom logic

## Apply Migrations

// turbo
6. Apply all pending migrations:
   ```bash
   uv run alembic upgrade head
   ```

## Rollback Migrations

7. Rollback the last migration:
   ```bash
   uv run alembic downgrade -1
   ```

8. Rollback to a specific revision:
   ```bash
   uv run alembic downgrade <revision_id>
   ```

## Check Migration Status

// turbo
9. Check current migration status:
   ```bash
   uv run alembic current
   ```

// turbo
10. View migration history:
    ```bash
    uv run alembic history
    ```

## Tips

- Always review auto-generated migrations before applying
- Test migrations on a development database first
- Create descriptive migration messages
- For complex schema changes, consider writing custom migration logic
- Keep migrations small and focused on one change at a time

## Troubleshooting

- If autogenerate creates empty migration: ensure models are properly imported in `alembic/env.py`
- If migration fails: check database logs with `docker-compose logs postgres`
- To reset database completely: drop all tables and run `alembic upgrade head`

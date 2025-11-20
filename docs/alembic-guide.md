# Alembic Migration Guide

## Overview

This project uses Alembic for database migrations with SQLAlchemy ORM models.

## How It Works

### Automatic Model Discovery

All ORM models are automatically imported through the database package's `__init__.py`:

```python
# app/infrastructure/database/__init__.py
from app.infrastructure.database.models import IngestJobModel, IngestFileModel

__all__ = [
    "Base",
    "IngestJobModel",
    "IngestFileModel",
    # Add new models here
]
```

When you import from `app.infrastructure.database`, all models are automatically loaded and registered with `Base.metadata`, which allows Alembic to detect them.

### Alembic Configuration

The `alembic/env.py` file imports the database package:

```python
from app.infrastructure.database import Base
target_metadata = Base.metadata
```

This single import automatically loads all models defined in the package's `__init__.py`.

## Adding New Models

When you create a new ORM model:

1. **Create the model** in `app/infrastructure/database/models.py` (or a new file)
2. **Export it** in `app/infrastructure/database/__init__.py`:
   ```python
   from app.infrastructure.database.models import (
       IngestJobModel,
       IngestFileModel,
       YourNewModel,  # Add here
   )
   
   __all__ = [
       "Base",
       "IngestJobModel",
       "IngestFileModel",
       "YourNewModel",  # And here
   ]
   ```
3. **Generate migration** (see commands below)

That's it! No need to modify `alembic/env.py`.

## Common Commands

### Generate a New Migration

```bash
# Using virtual environment
.venv/bin/alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest version
.venv/bin/alembic upgrade head

# Upgrade one version
.venv/bin/alembic upgrade +1

# Downgrade one version
.venv/bin/alembic downgrade -1
```

### Check Current Version

```bash
.venv/bin/alembic current
```

### View Migration History

```bash
.venv/bin/alembic history
```

### View SQL Without Executing

```bash
# See SQL for upgrade
.venv/bin/alembic upgrade head --sql

# See SQL for downgrade
.venv/bin/alembic downgrade -1 --sql
```

## Troubleshooting

### Empty Migration Generated

**Problem**: Running `alembic revision --autogenerate` creates an empty migration.

**Solution**: Make sure your new model is:
1. Imported in `app/infrastructure/database/__init__.py`
2. Added to the `__all__` list
3. Inherits from `Base`

**Verify models are loaded**:
```bash
.venv/bin/python3 -c "from app.infrastructure.database import Base; print(list(Base.metadata.tables.keys()))"
```

### Target Database Not Up to Date

**Problem**: Error message "Target database is not up to date"

**Solution**: Apply existing migrations first:
```bash
.venv/bin/alembic upgrade head
```

### Import Errors

**Problem**: `ModuleNotFoundError` when running Alembic

**Solution**: Make sure you're using the virtual environment:
```bash
# Use .venv/bin/alembic instead of just alembic
.venv/bin/alembic <command>
```

## Best Practices

1. **Always review** generated migrations before applying them
2. **Test migrations** on a development database first
3. **Backup production** database before running migrations
4. **Use descriptive names** for migration messages
5. **One logical change** per migration when possible
6. **Don't edit** applied migrations - create a new one instead

## Project Structure

```
app/infrastructure/database/
├── __init__.py          # Exports all models (IMPORTANT!)
├── database.py          # Base, engine, session
├── models.py            # ORM models
└── repository.py        # Repository pattern

alembic/
├── env.py              # Alembic configuration
├── versions/           # Migration files
└── alembic.ini         # Alembic settings
```

## Example: Adding a New Model

```python
# 1. Create model in app/infrastructure/database/models.py
class UserModel(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

# 2. Export in app/infrastructure/database/__init__.py
from app.infrastructure.database.models import (
    IngestJobModel,
    IngestFileModel,
    UserModel,  # Add this
)

__all__ = [
    "Base",
    "IngestJobModel",
    "IngestFileModel",
    "UserModel",  # Add this
]

# 3. Generate migration
# .venv/bin/alembic revision --autogenerate -m "add users table"

# 4. Review the generated migration file

# 5. Apply migration
# .venv/bin/alembic upgrade head
```

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

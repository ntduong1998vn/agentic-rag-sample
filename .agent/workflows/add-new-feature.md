---
description: add a new feature following clean architecture
---

# Add a New Feature

This workflow guides you through adding a new feature following Clean Architecture principles.

## Architecture Overview

The project follows Clean Architecture with these layers:
- `app/domain/` - Domain entities and business logic
- `app/application/` - Use cases and application services
- `app/infrastructure/` - External integrations (DB, APIs, etc.)
- `app/api/` - HTTP endpoints and request/response models

## Steps to Add a Feature

### 1. Define Domain Entities

1. Create domain entities in `app/domain/<feature>/`:
   ```python
   # app/domain/<feature>/entities.py
   from dataclasses import dataclass
   from datetime import datetime
   
   @dataclass
   class YourEntity:
       id: int
       name: str
       created_at: datetime
   ```

2. Define repository ports (interfaces):
   ```python
   # app/domain/<feature>/ports.py
   from abc import ABC, abstractmethod
   from typing import List, Optional
   
   class YourRepositoryPort(ABC):
       @abstractmethod
       async def create(self, entity: YourEntity) -> YourEntity:
           pass
       
       @abstractmethod
       async def get_by_id(self, id: int) -> Optional[YourEntity]:
           pass
   ```

### 2. Create Application Services

3. Implement use cases in `app/application/<feature>/`:
   ```python
   # app/application/<feature>/service.py
   from app.domain.<feature>.entities import YourEntity
   from app.domain.<feature>.ports import YourRepositoryPort
   
   class YourService:
       def __init__(self, repository: YourRepositoryPort):
           self.repository = repository
       
       async def create_entity(self, name: str) -> YourEntity:
           # Business logic here
           entity = YourEntity(name=name, ...)
           return await self.repository.create(entity)
   ```

### 3. Implement Infrastructure

4. Create SQLAlchemy models in `app/infrastructure/database/models.py`:
   ```python
   from sqlalchemy import Column, Integer, String, DateTime
   from .database import Base
   
   class YourEntityModel(Base):
       __tablename__ = "your_entities"
       
       id = Column(Integer, primary_key=True)
       name = Column(String, nullable=False)
       created_at = Column(DateTime, nullable=False)
   ```

5. Implement repository in `app/infrastructure/database/`:
   ```python
   # app/infrastructure/database/your_repository.py
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.domain.<feature>.ports import YourRepositoryPort
   from app.domain.<feature>.entities import YourEntity
   from .models import YourEntityModel
   
   class YourRepository(YourRepositoryPort):
       def __init__(self, session: AsyncSession):
           self.session = session
       
       async def create(self, entity: YourEntity) -> YourEntity:
           model = YourEntityModel(**entity.__dict__)
           self.session.add(model)
           await self.session.commit()
           return entity
   ```

### 4. Create Database Migration

6. Generate migration:
   ```bash
   uv run alembic revision --autogenerate -m "add your_entities table"
   ```

7. Review and apply migration:
   ```bash
   uv run alembic upgrade head
   ```

### 5. Add API Endpoints

8. Create API routes in `app/api/routes_<feature>.py`:
   ```python
   from fastapi import APIRouter, Depends
   from app.api.deps import get_database_session
   from app.application.<feature>.service import YourService
   from app.infrastructure.database.your_repository import YourRepository
   
   router = APIRouter(prefix="/<feature>", tags=["<feature>"])
   
   @router.post("/")
   async def create_entity(
       name: str,
       session = Depends(get_database_session)
   ):
       repository = YourRepository(session)
       service = YourService(repository)
       entity = await service.create_entity(name)
       return entity
   ```

9. Register router in `app/main.py`:
   ```python
   from app.api.routes_<feature> import router as feature_router
   
   app.include_router(feature_router)
   ```

### 6. Add Tests

10. Create tests in `tests/test_<feature>.py`:
    ```python
    import pytest
    from httpx import AsyncClient
    
    @pytest.mark.asyncio
    async def test_create_entity(client: AsyncClient):
        response = await client.post(
            "/<feature>/",
            json={"name": "Test"}
        )
        assert response.status_code == 200
    ```

11. Run tests:
    ```bash
    uv run pytest tests/test_<feature>.py
    ```

## Directory Structure Example

```
app/
├── domain/
│   └── <feature>/
│       ├── entities.py       # Domain models
│       └── ports.py          # Repository interfaces
├── application/
│   └── <feature>/
│       └── service.py        # Business logic
├── infrastructure/
│   └── database/
│       ├── models.py         # SQLAlchemy models
│       └── <feature>_repository.py  # Repository implementation
└── api/
    └── routes_<feature>.py   # API endpoints
```

## Best Practices

- Keep domain layer free of external dependencies
- Use dependency injection for repositories
- Write tests for each layer
- Follow existing code patterns in the project
- Document your code with docstrings
- Handle errors appropriately
- Use type hints for better code clarity

## Checklist

- [ ] Domain entities created
- [ ] Repository ports defined
- [ ] Application service implemented
- [ ] Database models created
- [ ] Repository implementation added
- [ ] Database migration created and applied
- [ ] API routes implemented
- [ ] Router registered in main.py
- [ ] Tests written and passing
- [ ] Code documented

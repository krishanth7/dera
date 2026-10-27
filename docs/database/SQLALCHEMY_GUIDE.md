# SQLAlchemy 2.x Development Guide

DERA adheres strictly to modern SQLAlchemy 2.x standards, fully utilizing typed declarative mappings and the asynchronous ORM extension.

---

## 1. Declarative Base & Naming Conventions

All platform models inherit from `dera_api.db.base.Base`, which specifies deterministic PostgreSQL constraint naming conventions:

```python
from dera_api.db.base import Base

# Naming convention tokens:
# ix: ix_%(column_0_label)s
# uq: uq_%(table_name)s_%(column_0_name)s
# ck: ck_%(table_name)s_%(constraint_name)s
# fk: fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
# pk: pk_%(table_name)s
```

---

## 2. Defining Typed Models

Use `Mapped[...]` and `mapped_column(...)`:

```python
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from dera_api.db.base import Base

class MyPlatformModel(Base):
    __tablename__ = "dera_my_model"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

---

## 3. Session Lifecycle & FastAPI Dependency

Never create global session objects. Use `get_db_session` dependency injection:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dera_api.db.dependencies import get_db_session

router = APIRouter()

@router.get("/example")
async def example_endpoint(session: AsyncSession = Depends(get_db_session)):
    # Session is cleanly closed automatically when the request terminates
    pass
```

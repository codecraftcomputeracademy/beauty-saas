from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"localhost:5432/"
    f"{settings.postgres_db}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
from typing import AsyncGenerator, Type
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()

def heredar(clase_padre: Type[Base], nombre_clase: str) -> Type[Base]:
    """Crea dinámicamente una clase hija con su identidad polimórfica."""
    return type(
        nombre_clase, 
        (clase_padre,), 
        {
            "__mapper_args__": {"polymorphic_identity": nombre_clase.lower()}
        }
    )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

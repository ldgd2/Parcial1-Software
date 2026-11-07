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

from sqlalchemy import text

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS etiquetas_habilidades JSONB;"))
        await conn.execute(text("ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS deployment_url VARCHAR;"))
        await conn.execute(text("ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS rol_ia VARCHAR;"))
        await conn.execute(text("ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS areas JSONB;"))
        await conn.execute(text("ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS responsabilidades JSONB;"))
        await conn.execute(text("ALTER TABLE tareas_ia ADD COLUMN IF NOT EXISTS area VARCHAR DEFAULT 'general';"))

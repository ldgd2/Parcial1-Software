from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Local SQLite DB for Deployer State
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Init DB function
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

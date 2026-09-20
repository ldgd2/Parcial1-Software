import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config import settings

async def alter_table():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE usuarios ADD COLUMN db_password_encrypted VARCHAR;"))
            print("Columna añadida correctamente.")
        except Exception as e:
            print(f"Error o la columna ya existe: {e}")

if __name__ == "__main__":
    asyncio.run(alter_table())

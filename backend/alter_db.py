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
            print("Columna db_password_encrypted añadida.")
        except Exception as e:
            print(f"Error en usuarios (quizá ya existe): {e}")
            
        try:
            await conn.execute(text("ALTER TABLE proyectos ADD COLUMN github_repo_url VARCHAR;"))
            print("Columna github_repo_url añadida.")
        except Exception as e:
            print(f"Error en proyectos github (quizá ya existe): {e}")

        try:
            await conn.execute(text("ALTER TABLE proyectos ADD COLUMN deployment_url VARCHAR;"))
            print("Columna deployment_url añadida.")
        except Exception as e:
            print(f"Error en proyectos deploy (quizá ya existe): {e}")

if __name__ == "__main__":
    asyncio.run(alter_table())

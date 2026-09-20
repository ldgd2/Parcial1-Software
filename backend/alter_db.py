import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config import settings

async def alter_table():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async def run_query(query: str, success_msg: str, error_msg: str):
        try:
            async with engine.begin() as conn:
                await conn.execute(text(query))
            print(success_msg)
        except Exception as e:
            print(f"{error_msg}: {e}")

    await run_query(
        "ALTER TABLE usuarios ADD COLUMN db_password_encrypted VARCHAR;",
        "Columna db_password_encrypted añadida.",
        "Error en usuarios (quizá ya existe)"
    )
    
    await run_query(
        "ALTER TABLE proyectos ADD COLUMN github_repo_url VARCHAR;",
        "Columna github_repo_url añadida.",
        "Error en proyectos github (quizá ya existe)"
    )

    await run_query(
        "ALTER TABLE proyectos ADD COLUMN deployment_url VARCHAR;",
        "Columna deployment_url añadida.",
        "Error en proyectos deploy (quizá ya existe)"
    )

if __name__ == "__main__":
    asyncio.run(alter_table())

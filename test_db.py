import asyncio
import asyncpg
from backend.core.config import settings
from urllib.parse import quote_plus

async def run():
    print(f"Connecting to: {settings.DB_IP}:{settings.DB_PORT} as {settings.DB_USER} to db {settings.DB_NAME}")
    try:
        conn = await asyncpg.connect(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            host=settings.DB_IP,
            port=settings.DB_PORT
        )
        print("Success!")
        await conn.close()
    except Exception as e:
        print(f"Failed: {type(e).__name__} - {e}")

asyncio.run(run())

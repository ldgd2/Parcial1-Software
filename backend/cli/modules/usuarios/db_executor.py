import asyncio
from backend.core.database import AsyncSessionLocal
from backend.modules.gestion_usuarios.models import Usuario

async def get_all_usuarios():
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario))
        return result.scalars().all()

async def create_usuario_db(nombre, email):
    async with AsyncSessionLocal() as session:
        nuevo = Usuario(nombre=nombre, email=email, is_active=True, tipo="registrado")
        session.add(nuevo)
        await session.commit()
        await session.refresh(nuevo)
        return nuevo

async def delete_usuario_db(email):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario).where(Usuario.email == email))
        user = result.scalars().first()
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False

async def get_usuario_db(email):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario).where(Usuario.email == email))
        return result.scalars().first()

async def update_usuario_db(email, nuevo_nombre):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario).where(Usuario.email == email))
        user = result.scalars().first()
        if user:
            user.nombre = nuevo_nombre
            await session.commit()
            return True
        return False

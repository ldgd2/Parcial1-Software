import asyncio
from backend.core.database import AsyncSessionLocal
from backend.modules.gestion_usuarios.models import Usuario, UsuarioRegistrado

async def get_all_usuarios():
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Usuario))
        return result.scalars().all()

async def create_usuario_db(nombre, email):
    from sqlalchemy import select
    from backend.core.permissions.models import Rol
    async with AsyncSessionLocal() as session:
        # Mismo rol que asigna el registro de la app: sin rol, todo endpoint con permisos da 403.
        rol = (await session.execute(select(Rol).where(Rol.nombre == "registrado"))).scalars().first()
        # El tipo lo pone la identidad polimórfica ('usuarioregistrado'), igual que el registro de la app.
        # Un tipo inventado como "registrado" hace que SQLAlchemy no pueda volver a leer la fila.
        nuevo = UsuarioRegistrado(nombre=nombre, email=email, is_active=True, rol_id=rol.id if rol else None)
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

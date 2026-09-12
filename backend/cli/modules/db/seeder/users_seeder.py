from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
from backend.modules.gestion_usuarios.models import Usuario
from backend.core.security import get_password_hash

# Avoid circular imports by locally importing BaseSeeder or just using duck-typing.
# But since we have it in seeder.py:
# To avoid circular import, we won't import BaseSeeder here, Python duck-typing is fine.

from sqlalchemy.future import select
from backend.core.permissions.models import Rol

class UsersSeeder:
    async def run(self, db: AsyncSession, cantidad: int) -> None:
        fake = Faker('es_ES')
        
        # Obtener rol usuario
        result = await db.execute(select(Rol).where(Rol.nombre == "usuario"))
        rol_usuario = result.scalars().first()
        rol_id = rol_usuario.id if rol_usuario else None
        
        # Generar dinámicos
        for _ in range(cantidad):
            nuevo_usuario = Usuario(
                nombre=fake.name(),
                email=fake.unique.email(),
                hashed_password=get_password_hash("password123"),
                rol_id=rol_id
            )
            db.add(nuevo_usuario)
            
        await db.commit()

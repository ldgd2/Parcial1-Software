from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.repository import BaseRepository
from backend.modules.gestion_usuarios.models import Usuario, UsuarioRegistrado
from backend.modules.gestion_usuarios.registrar_usuario.schemas.request import UsuarioCreate
from backend.modules.gestion_usuarios.registrar_usuario.schemas.response import UsuarioResponse
from backend.core.security import get_password_hash
from backend.core.permissions.models import Rol

class UserRepository(BaseRepository[Usuario, UsuarioCreate, UsuarioResponse]):
    
    async def create_user(self, db: AsyncSession, user: UsuarioCreate) -> UsuarioRegistrado:
        hashed_password = get_password_hash(user.password)
        
        # Obtener el rol registrado
        result = await db.execute(select(Rol).where(Rol.nombre == "registrado"))
        rol = result.scalars().first()
        
        db_user = UsuarioRegistrado(
            nombre=user.nombre, 
            email=user.email, 
            hashed_password=hashed_password,
            rol_id=rol.id if rol else None
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

user_repo = UserRepository(Usuario)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.repository import BaseRepository
from backend.modules.gestion_usuarios.models import Usuario, UsuarioAnonimo
from backend.core.permissions.models import Rol
from backend.modules.gestion_usuarios.iniciar_sesion.schemas.request import AnonimoCreate

class LoginRepository(BaseRepository):
    
    async def create_anonimo(self, db: AsyncSession, data: AnonimoCreate) -> UsuarioAnonimo:
        result = await db.execute(select(Rol).where(Rol.nombre == "anonimo"))
        rol = result.scalars().first()
        
        db_user = UsuarioAnonimo(nombre=data.nombre, rol_id=rol.id if rol else None)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

login_repo = LoginRepository(Usuario)

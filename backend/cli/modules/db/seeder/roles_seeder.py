from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.permissions.models import Rol, Permiso
from sqlalchemy.future import select

class RolesSeeder:
    async def run(self, db: AsyncSession, cantidad: int) -> None:
        # Permisos que queremos tener
        nombres_permisos = [
            "crear_proyecto", 
            "editar_proyecto", 
            "eliminar_proyecto", 
            "invitar_usuario", 
            "gestionar_roles"
        ]
        
        permisos_creados = []
        for nombre in nombres_permisos:
            # Check if exists
            result = await db.execute(select(Permiso).where(Permiso.nombre == nombre))
            permiso = result.scalars().first()
            if not permiso:
                permiso = Permiso(nombre=nombre, descripcion=f"Permite {nombre.replace('_', ' ')}")
                db.add(permiso)
            permisos_creados.append(permiso)
            
        await db.flush()
        
        # Mapeo de roles a sus permisos
        roles_data = {
            "admin": permisos_creados,
            "usuario": [p for p in permisos_creados if p.nombre in ["crear_proyecto", "editar_proyecto"]],
            "invitado": []
        }
        
        for rol_nombre, permisos in roles_data.items():
            result = await db.execute(select(Rol).where(Rol.nombre == rol_nombre))
            rol = result.scalars().first()
            if not rol:
                rol = Rol(nombre=rol_nombre, descripcion=f"Rol {rol_nombre}", permisos=permisos)
                db.add(rol)
                
        await db.commit()

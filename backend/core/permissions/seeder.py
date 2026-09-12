from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.seeder import BaseSeeder, runner
from backend.core.permissions.models import Rol, Permiso

@runner.register
class RolesYPermisosSeeder(BaseSeeder):
    async def run(self, db: AsyncSession) -> None:
        # Check if already seeded
        result = await db.execute(select(Rol))
        if result.scalars().first():
            return # Ya existen roles, omitir seeding
            
        # 1. Crear permisos base
        p_crear_proyecto = Permiso(nombre="crear_proyecto", descripcion="Permite crear proyectos nuevos")
        p_editar_proyecto = Permiso(nombre="editar_proyecto", descripcion="Permite editar proyectos")
        p_ver_proyecto = Permiso(nombre="ver_proyecto", descripcion="Permite ver proyectos")
        p_eliminar_proyecto = Permiso(nombre="eliminar_proyecto", descripcion="Permite eliminar proyectos")
        p_gestionar_colaboradores = Permiso(nombre="gestionar_colaboradores", descripcion="Permite aprobar o rechazar colaboradores")
        
        db.add_all([p_crear_proyecto, p_editar_proyecto, p_ver_proyecto, p_eliminar_proyecto, p_gestionar_colaboradores])
        
        # 2. Crear roles y asociar permisos
        rol_admin = Rol(nombre="admin", descripcion="Administrador global del sistema")
        rol_admin.permisos = [p_crear_proyecto, p_editar_proyecto, p_ver_proyecto, p_eliminar_proyecto, p_gestionar_colaboradores]
        
        rol_registrado = Rol(nombre="registrado", descripcion="Usuario con cuenta registrada")
        # El usuario normal puede hacer todo esto (dentro de su proyecto, lo cual se filtra lógicamente en el CU)
        rol_registrado.permisos = [p_crear_proyecto, p_editar_proyecto, p_ver_proyecto, p_eliminar_proyecto, p_gestionar_colaboradores]
        
        rol_anonimo = Rol(nombre="anonimo", descripcion="Usuario invitado sin cuenta")
        rol_anonimo.permisos = [p_ver_proyecto] # Un anónimo no debería crear proyectos desde cero
        
        db.add_all([rol_admin, rol_registrado, rol_anonimo])
        await db.commit()

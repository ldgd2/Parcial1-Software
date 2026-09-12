from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
from sqlalchemy.future import select
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
from backend.modules.gestion_usuarios.models import Usuario

class ProjectsSeeder:
    async def run(self, db: AsyncSession, cantidad: int) -> None:
        fake = Faker('es_ES')
        
        result = await db.execute(select(Usuario))
        usuarios = result.scalars().all()
        
        if not usuarios:
            print("No hay usuarios para asignar proyectos. Ejecuta UsersSeeder primero.")
            return
            
        for _ in range(cantidad):
            proyecto = Proyecto(
                nombre=fake.company(),
                descripcion=fake.catch_phrase()
            )
            db.add(proyecto)
            await db.flush()
            
            anfitrion = fake.random_element(elements=usuarios)
            colab = ColaboradorProyecto(
                proyecto_id=proyecto.id,
                usuario_id=anfitrion.id,
                rol_proyecto="anfitrion",
                estado="aprobado"
            )
            db.add(colab)
            
        await db.commit()

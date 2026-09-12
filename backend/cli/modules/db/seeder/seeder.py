import logging
from typing import List, Type
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import AsyncSessionLocal
from backend.cli.modules.db.seeder.users_seeder import UsersSeeder
from backend.cli.modules.db.seeder.roles_seeder import RolesSeeder
from backend.cli.modules.db.seeder.projects_seeder import ProjectsSeeder

class BaseSeeder:
    """Clase base estandarizada para todos los seeders hijos."""
    async def run(self, db: AsyncSession, cantidad: int) -> None:
        raise NotImplementedError("Cada seeder debe implementar el método run()")

class MasterSeeder:
    """El Seeder Padre que orquesta la ejecución de los seeders hijos."""
    def __init__(self):
        # Aquí se registran los seeders hijos en el orden de ejecución correcto
        self.seeders: List[Type[BaseSeeder]] = [
            RolesSeeder,
            UsersSeeder,
            ProjectsSeeder,
        ]

    async def execute_all(self, db: AsyncSession, cantidad: int):
        from backend.cli.console import console
        for seeder_cls in self.seeders:
            seeder_name = seeder_cls.__name__
            console.print(f"[dim]Iniciando {seeder_name}...[/dim]")
            seeder_instance = seeder_cls()
            await seeder_instance.run(db, cantidad)
            console.print(f"[green]✓ {seeder_name} completado.[/green]")

async def correr_master_seeder(cantidad: int):
    master = MasterSeeder()
    async with AsyncSessionLocal() as db:
        await master.execute_all(db, cantidad)

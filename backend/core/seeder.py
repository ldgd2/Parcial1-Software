from typing import List, Type
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class BaseSeeder:
    """Clase padre para todos los seeders. Define el contrato abstracto."""
    async def run(self, db: AsyncSession) -> None:
        raise NotImplementedError("Cada seeder debe implementar el método run()")

class SeederRunner:
    """Ejecuta todos los seeders registrados en lote."""
    def __init__(self):
        self._seeders: List[Type[BaseSeeder]] = []

    def register(self, seeder_cls: Type[BaseSeeder]):
        self._seeders.append(seeder_cls)
        return seeder_cls # Permite usarlo como decorador si queremos

    async def run_all(self, db: AsyncSession):
        logger.info("Ejecutando seeders de base de datos...")
        for seeder_cls in self._seeders:
            seeder = seeder_cls()
            logger.info(f"Ejecutando seeder: {seeder_cls.__name__}")
            await seeder.run(db)
        logger.info("Todos los seeders se han ejecutado con éxito.")

runner = SeederRunner()

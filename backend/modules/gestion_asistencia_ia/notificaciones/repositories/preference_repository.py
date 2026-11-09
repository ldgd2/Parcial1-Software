from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_asistencia_ia.notificaciones.models.preference import NotificationPreference

class PreferenceRepository:
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> NotificationPreference | None:
        result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert(db: AsyncSession, user_id: int, data: dict) -> NotificationPreference:
        existing = await PreferenceRepository.get_by_user(db, user_id)
        if existing:
            await db.execute(
                update(NotificationPreference)
                .where(NotificationPreference.id == existing.id)
                .values(**data)
            )
            await db.commit()
            return await PreferenceRepository.get_by_user(db, user_id)
        else:
            stmt = insert(NotificationPreference).values(user_id=user_id, **data)
            await db.execute(stmt)
            await db.commit()
            return await PreferenceRepository.get_by_user(db, user_id)


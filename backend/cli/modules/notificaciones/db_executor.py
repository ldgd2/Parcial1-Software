import json
from typing import List, Dict, Any, Optional
from sqlalchemy import select, desc
from backend.core.database import AsyncSessionLocal
from backend.modules.gestion_asistencia_ia.notificaciones.models import NotificationToken, NotificationLog
from backend.modules.gestion_notificaciones.models import Notificacion, DispositivoPush
from backend.modules.gestion_usuarios.models import Usuario


async def obtener_todos_los_tokens() -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        tokens_lista: List[Dict[str, Any]] = []
        
        stmt1 = (
            select(NotificationToken, Usuario.email, Usuario.nombre)
            .outerjoin(Usuario, Usuario.id == NotificationToken.user_id)
            .order_by(desc(NotificationToken.created_at))
            if hasattr(NotificationToken, "created_at")
            else select(NotificationToken, Usuario.email, Usuario.nombre).outerjoin(Usuario, Usuario.id == NotificationToken.user_id)
        )
        res1 = await session.execute(stmt1)
        for row in res1.all():
            token_obj = row[0]
            email = row[1] or "Desconocido"
            nombre = row[2] or "Sin nombre"
            tokens_lista.append({
                "fuente": "notifications",
                "usuario_id": token_obj.user_id,
                "usuario": f"{nombre} ({email})",
                "token": token_obj.device_token,
                "plataforma": "movil",
            })

        stmt2 = (
            select(DispositivoPush, Usuario.email, Usuario.nombre)
            .outerjoin(Usuario, Usuario.id == DispositivoPush.usuario_id)
            .order_by(desc(DispositivoPush.created_at))
        )
        res2 = await session.execute(stmt2)
        for row in res2.all():
            disp = row[0]
            email = row[1] or "Desconocido"
            nombre = row[2] or "Sin nombre"
            tokens_lista.append({
                "fuente": "dispositivos_push",
                "usuario_id": disp.usuario_id,
                "usuario": f"{nombre} ({email})",
                "token": disp.token,
                "plataforma": disp.plataforma,
            })

        return tokens_lista


async def obtener_token_por_usuario(usuario_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as session:
        stmt = select(NotificationToken.device_token).where(NotificationToken.user_id == usuario_id)
        res = await session.execute(stmt)
        token = res.scalar_one_or_none()
        if token:
            return token

        stmt2 = select(DispositivoPush.token).where(DispositivoPush.usuario_id == usuario_id)
        res2 = await session.execute(stmt2)
        return res2.scalar_one_or_none()


async def registrar_log_envio(
    usuario_id: int,
    titulo: str,
    body: str,
    enviado: bool,
    datos: Optional[Dict[str, str]] = None,
) -> None:
    async with AsyncSessionLocal() as session:
        stmt = select(NotificationToken.id).where(NotificationToken.user_id == usuario_id)
        res = await session.execute(stmt)
        token_id = res.scalar_one_or_none()

        if token_id:
            log_item = NotificationLog(
                notification_id=token_id,
                title=titulo,
                body=body,
                data=json.dumps(datos) if datos else None,
                sent=enviado,
            )
            session.add(log_item)
            await session.commit()


async def crear_notificacion_in_app(
    usuario_id: int,
    titulo: str,
    mensaje: str,
    tipo: str = "sistema",
    url: Optional[str] = "/dashboard",
) -> None:
    async with AsyncSessionLocal() as session:
        notif = Notificacion(
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            url=url,
        )
        session.add(notif)
        await session.commit()


async def obtener_historial_logs(limite: int = 15) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(NotificationLog, NotificationToken.user_id)
            .join(NotificationToken, NotificationToken.id == NotificationLog.notification_id)
            .order_by(desc(NotificationLog.sent_at))
            .limit(limite)
        )
        res = await session.execute(stmt)
        resultado: List[Dict[str, Any]] = []
        for log_obj, user_id in res.all():
            resultado.append({
                "id": log_obj.id,
                "usuario_id": user_id,
                "titulo": log_obj.title,
                "cuerpo": log_obj.body,
                "enviado": log_obj.sent,
                "fecha": log_obj.sent_at.strftime("%Y-%m-%d %H:%M:%S") if log_obj.sent_at else "-",
            })
        return resultado

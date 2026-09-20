from contextlib import asynccontextmanager
import sys
import os
# Agregar el directorio padre (Examen) al PYTHONPATH para que reconozca el paquete 'backend'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.config import settings
from backend.core.seeder import runner
# Importar seeders para que se registren
import backend.core.permissions.seeder

# Importar modelos genéricos para que SQLAlchemy los cree
import backend.modules.gestion_proyectos.versioning.models
import backend.modules.gestion_modelado.models

# Importar routers de los casos de uso
from backend.modules.gestion_usuarios.registrar_usuario.controllers.user_controller import router as register_router
from backend.modules.gestion_usuarios.iniciar_sesion.controllers.login_controller import router as login_router
from backend.modules.gestion_usuarios.cerrar_sesion.controllers.logout_controller import router as logout_router
from backend.modules.gestion_usuarios.recuperar_password.controllers.reset_controller import router as reset_password_router
from backend.modules.gestion_usuarios.configurar_perfil.controllers.config_controller import router as config_router
from backend.modules.gestion_proyectos.crear_proyecto.controllers.crear_controller import router as crear_proyecto_router
from backend.modules.gestion_proyectos.administrar_proyecto.controllers.admin_controller import router as admin_proyecto_router
from backend.modules.gestion_proyectos.compartir_proyecto.controllers.compartir_controller import router as compartir_proyecto_router
from backend.modules.gestion_proyectos.notificar_despliegue.controllers.callback_controller import router as callback_router
from backend.modules.gestion_salas.controllers.sala_controller import router as sala_router
from backend.modules.gestion_concurrencia.sincronizacion_tiempo_real.controllers.ws_sync_controller import router as ws_router

# CU8 - CU11: Gestión de Modelado
from backend.modules.gestion_modelado.insertar_elemento.controllers.insertar_controller import router as insertar_elemento_router
from backend.modules.gestion_modelado.conectar_elemento.controllers.conectar_controller import router as conectar_elemento_router
from backend.modules.gestion_modelado.editar_elemento.controllers.editar_controller import router as editar_elemento_router
from backend.modules.gestion_modelado.eliminar_elemento.controllers.eliminar_controller import router as eliminar_elemento_router

# Interoperabilidad
from backend.modules.gestion_interoperabilidad.exportar_a_xml.controllers.export_controller import router as export_router
from backend.modules.gestion_interoperabilidad.importar_desde_xml.controllers.import_controller import router as import_router

# IA
from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.controllers.prompt_controller import router as prompt_ia_router
from backend.modules.gestion_asistencia_ia.digitalizar_desde_imagen.controllers.digitalizar_controller import router as digitalizar_ia_router
from backend.modules.gestion_asistencia_ia.exportar_github.controllers.exportar_controller import router as exportar_github_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    # Ejecutar seeders
    async with AsyncSessionLocal() as db:
        await runner.run_all(db)
        
    yield

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://diagramador.example.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers de usuarios
app.include_router(register_router)
app.include_router(login_router)
app.include_router(logout_router)
app.include_router(reset_password_router)
app.include_router(config_router)

# Registrar routers de proyectos
app.include_router(crear_proyecto_router)
app.include_router(admin_proyecto_router)
app.include_router(compartir_proyecto_router)
app.include_router(callback_router)
app.include_router(sala_router)
app.include_router(ws_router)

# Gestión de Modelado (CU8 - CU11)
app.include_router(insertar_elemento_router)
app.include_router(conectar_elemento_router)
app.include_router(editar_elemento_router)
app.include_router(eliminar_elemento_router)

# Interoperabilidad
app.include_router(export_router)
app.include_router(import_router)

# IA
app.include_router(prompt_ia_router)
app.include_router(digitalizar_ia_router)
app.include_router(exportar_github_router)


@app.get("/")
async def root():
    return {"message": f"Bienvenido a la API de {settings.PROJECT_NAME}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

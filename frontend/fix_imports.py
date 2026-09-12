import os
import re

# Mapping of old strings to new strings for import paths
replacements = {
    # AUTH
    "features/auth/login_view": "features/gestion_usuarios/iniciar_sesion",
    "features/auth/register_view": "features/gestion_usuarios/registrar_usuario",
    "features/auth/reset_password_view": "features/gestion_usuarios/recuperar_password",
    "features/auth/shared": "features/gestion_usuarios/shared",

    # DASHBOARD
    "features/dashboard/views": "features/gestion_proyectos/administrar_proyecto/views",
    "features/dashboard/components/DashboardBackground": "features/gestion_proyectos/administrar_proyecto/components/DashboardBackground",
    "features/dashboard/components/DashboardNavbar": "features/gestion_proyectos/administrar_proyecto/components/DashboardNavbar",
    "features/dashboard/components/ProyectoCard": "features/gestion_proyectos/administrar_proyecto/components/ProyectoCard",
    "features/dashboard/components/Modal": "features/gestion_proyectos/administrar_proyecto/components/Modal",
    "features/dashboard/components/ToastStack": "features/gestion_proyectos/administrar_proyecto/components/ToastStack",
    "features/dashboard/components/ProyectoFormModal": "features/gestion_proyectos/crear_proyecto/components/ProyectoFormModal",
    "features/dashboard/components/NuevoProyectoCard": "features/gestion_proyectos/crear_proyecto/components/NuevoProyectoCard",
    "features/dashboard/components/CompartirModal": "features/gestion_proyectos/compartir_proyecto/components/CompartirModal",
    "features/dashboard/context": "features/gestion_proyectos/shared/context",
    "features/dashboard/shared": "features/gestion_proyectos/shared/utils",

    # SALA -> GESTION_SALAS
    "features/sala/views": "features/gestion_salas/entrar_sala/views",
    "features/sala/context/SalaSocketContext": "features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext",
    "features/sala/components/MultiplayerCursors": "features/gestion_salas/colaboracion_tiempo_real/components/MultiplayerCursors",

    # SALA -> GESTION_MODELADO
    "features/sala/components/Toolbar": "features/gestion_modelado/insertar_elemento/components/Toolbar",
    "features/sala/components/ConnectPicker": "features/gestion_modelado/conectar_elemento/components/ConnectPicker",
    "features/sala/components/RelationLayer": "features/gestion_modelado/conectar_elemento/components/RelationLayer",
    "features/sala/components/ClassNode": "features/gestion_modelado/editar_elemento/components/ClassNode",
    "features/sala/components/DiagramCanvas": "features/gestion_modelado/lienzo_principal/components/DiagramCanvas",
    "features/sala/components/Menustrip": "features/gestion_modelado/lienzo_principal/components/Menustrip",

    "features/sala/context": "features/gestion_modelado/shared/context",
    "features/sala/store": "features/gestion_modelado/shared/store",
    "features/sala/utils": "features/gestion_modelado/shared/utils",
    "features/sala/shared": "features/gestion_modelado/shared/types",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    for old, new in replacements.items():
        # Replace occurrences in import strings
        # E.g. '@/features/auth/login_view'
        # Or relative paths like '../../features/auth/login_view'
        content = content.replace(old, new)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

def main():
    src_dir = r"c:\Users\ldgd2\Documents\universidad\software 1\sem 2-2026\examen1\Examen\frontend\src"
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                filepath = os.path.join(root, file)
                process_file(filepath)

if __name__ == "__main__":
    main()

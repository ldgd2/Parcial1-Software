import os

def fix_imports():
    # We will use absolute aliases @/features/... for simplicity
    fixes = {
        r"src/features/gestion_modelado/shared/context/DiagramContext.tsx": [
            ("../shared/types", "../types/types"),
            ("./SalaSocketContext", "@/features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext"),
        ],
        r"src/features/gestion_modelado/shared/utils/VersionManager.ts": [
            ("../shared/types", "../types/types"),
        ],
        r"src/features/gestion_proyectos/administrar_proyecto/components/ProyectoCard/ProyectoCard.tsx": [
            ("../../shared/types", "@/features/gestion_proyectos/shared/utils/types"),
        ],
        r"src/features/gestion_proyectos/administrar_proyecto/components/ToastStack/ToastStack.tsx": [
            ("../../context/NotifContext", "@/features/gestion_proyectos/shared/context/NotifContext"),
            ("../../shared/types", "@/features/gestion_proyectos/shared/utils/types"),
        ],
        r"src/features/gestion_proyectos/administrar_proyecto/views/DashboardView.tsx": [
            ("../components/NuevoProyectoCard/NuevoProyectoCard", "@/features/gestion_proyectos/crear_proyecto/components/NuevoProyectoCard/NuevoProyectoCard"),
            ("../components/ProyectoFormModal/ProyectoFormModal", "@/features/gestion_proyectos/crear_proyecto/components/ProyectoFormModal/ProyectoFormModal"),
            ("../components/CompartirModal/CompartirModal", "@/features/gestion_proyectos/compartir_proyecto/components/CompartirModal/CompartirModal"),
            ("../context/NotifContext", "@/features/gestion_proyectos/shared/context/NotifContext"),
            ("../shared/proyectoService", "@/features/gestion_proyectos/shared/utils/proyectoService"),
            ("../shared/types", "@/features/gestion_proyectos/shared/utils/types"),
        ],
        r"src/features/gestion_proyectos/compartir_proyecto/components/CompartirModal/CompartirModal.tsx": [
            ("../Modal/Modal", "@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal"),
            ("../../shared/proyectoService", "@/features/gestion_proyectos/shared/utils/proyectoService"),
            ("../../shared/types", "@/features/gestion_proyectos/shared/utils/types"),
        ],
        r"src/features/gestion_proyectos/crear_proyecto/components/ProyectoFormModal/ProyectoFormModal.tsx": [
            ("../Modal/Modal", "@/features/gestion_proyectos/administrar_proyecto/components/Modal/Modal"),
            ("../../shared/types", "@/features/gestion_proyectos/shared/utils/types"),
        ],
        r"src/features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext.tsx": [
            ("../../../shared/utils/animalNames", "@/shared/utils/animalNames"),
            ("../store/ObjectStore", "@/features/gestion_modelado/shared/store/ObjectStore"),
        ],
        r"src/features/gestion_salas/entrar_sala/views/SalaView.tsx": [
            ("../context/DiagramContext", "@/features/gestion_modelado/shared/context/DiagramContext"),
            ("../context/SalaSocketContext", "@/features/gestion_salas/colaboracion_tiempo_real/context/SalaSocketContext"),
            ("../components/Menustrip/Menustrip", "@/features/gestion_modelado/lienzo_principal/components/Menustrip/Menustrip"),
            ("../components/Toolbar/Toolbar", "@/features/gestion_modelado/insertar_elemento/components/Toolbar/Toolbar"),
            ("../components/DiagramCanvas/DiagramCanvas", "@/features/gestion_modelado/lienzo_principal/components/DiagramCanvas/DiagramCanvas"),
            ("../components/MultiplayerCursors/MultiplayerCursors", "@/features/gestion_salas/colaboracion_tiempo_real/components/MultiplayerCursors/MultiplayerCursors"),
            ("../shared/salaService", "@/features/gestion_salas/shared/services/salaService"),
            ("../shared/types", "@/features/gestion_modelado/shared/types/types"),
        ],
        r"src/features/gestion_salas/entrar_sala/views/UnirseView.tsx": [
            ("../shared/salaService", "@/features/gestion_salas/shared/services/salaService"),
            ("../../../shared/utils/animalNames", "@/shared/utils/animalNames"),
        ]
    }

    base = r"c:\Users\ldgd2\Documents\universidad\software 1\sem 2-2026\examen1\Examen\frontend"
    for file, replacements in fixes.items():
        filepath = os.path.join(base, file)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        for old, new in replacements:
            content = content.replace(old, new)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {file}")

if __name__ == "__main__":
    fix_imports()

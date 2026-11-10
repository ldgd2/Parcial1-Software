import subprocess
import os
import shutil
from fastapi import HTTPException

def subir_codigo_a_github(carpeta_temporal: str, url_repo: str, token: str):
    """Sube el contenido de una carpeta temporal a un repositorio de GitHub utilizando git."""
    try:
        if not os.path.exists(carpeta_temporal):
            raise Exception("La carpeta temporal con el código generado no existe.")
            
        url_con_token = url_repo.replace("https://", f"https://x-access-token:{token}@")
        
        # Comandos de Git usando cwd en lugar de os.chdir para evitar problemas de concurrencia
        subprocess.run(["git", "init"], cwd=carpeta_temporal, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "IA Assistant"], cwd=carpeta_temporal, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "ia@assistant.local"], cwd=carpeta_temporal, check=True, capture_output=True)
        
        subprocess.run(["git", "add", "."], cwd=carpeta_temporal, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Commit inicial: Monorepo con /backend (Spring Boot) y /frontend (Flutter App Móvil)"], cwd=carpeta_temporal, check=True, capture_output=True)
        
        subprocess.run(["git", "branch", "-M", "main"], cwd=carpeta_temporal, check=True, capture_output=True)
        
        push_process = subprocess.run(["git", "push", "-u", url_con_token, "main"], cwd=carpeta_temporal, check=True, capture_output=True, text=True)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        error_msg_safe = error_msg.replace(token, "***TOKEN***")
        print(f"Git Push Error: {error_msg_safe}")
        raise HTTPException(status_code=500, detail=f"Error en Git: {error_msg_safe}")
    except Exception as e:
        print(f"General Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al subir código: {str(e)}")
    finally:
        # Destruir la carpeta temporal para liberar espacio
        if os.path.exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal, ignore_errors=True)

async def actualizar_codigo_en_github(carpeta_temporal: str, url_repo: str, token: str):
    """
    Clona el repositorio existente, sobreescribe los archivos con los nuevos, 
    detecta los cambios, genera un mensaje con IA y hace push.
    """
    from backend.modules.gestion_asistencia_ia.exportar_github.services.ia_commit_service import generar_mensaje_commit_ia
    
    # Creamos un directorio paralelo para clonar el repositorio
    carpeta_clon = f"{carpeta_temporal}_clone"
    
    try:
        if not os.path.exists(carpeta_temporal):
            raise Exception("La carpeta temporal con el código generado no existe.")
            
        url_con_token = url_repo.replace("https://", f"https://x-access-token:{token}@")
        
        # 1. Clonar el repositorio existente
        subprocess.run(["git", "clone", url_con_token, carpeta_clon], check=True, capture_output=True)
        
        # 2. Manejo de persistencia de migraciones SQL:
        # Preserva migraciones previas (V1, V2...) y versiona la nueva secuencialmente
        import re
        mig_dir_clon = os.path.join(carpeta_clon, "backend", "src", "main", "resources", "db", "migration")
        mig_dir_temp = os.path.join(carpeta_temporal, "backend", "src", "main", "resources", "db", "migration")

        if os.path.isdir(mig_dir_clon) and os.path.isdir(mig_dir_temp):
            existing_migs = [f for f in os.listdir(mig_dir_clon) if f.endswith(".sql") and f.startswith("V")]
            if existing_migs:
                versions = []
                for m in existing_migs:
                    match = re.match(r"^V(\d+)__", m)
                    if match:
                        versions.append(int(match.group(1)))
                next_version = (max(versions) + 1) if versions else 2

                temp_v1 = os.path.join(mig_dir_temp, "V1__Esquema_Inicial.sql")
                if os.path.exists(temp_v1):
                    # Las migraciones de esquema anteriores pudieron quedar rotas (antes las FK las escribía
                    # una IA: `fk_tu_nombre_unico`, columna INTEGER -> id UUID). En una BD nueva Flyway
                    # las ejecuta todas desde V1 y la app no arrancaba. El esquema nuevo es idempotente
                    # (IF NOT EXISTS, FK tolerantes) y validate-on-migrate=false, así que se reescriben
                    # con él: las BD que ya las aplicaron no las vuelven a correr.
                    with open(temp_v1, "r", encoding="utf-8") as f:
                        esquema_nuevo = f.read()
                    next_mig_name = f"V{next_version}__Actualizacion_Diagrama.sql"
                    next_mig_path = os.path.join(mig_dir_temp, next_mig_name)
                    os.rename(temp_v1, next_mig_path)
                    for m in existing_migs:
                        if re.match(r"^V\d+__(Esquema_Inicial|Actualizacion_Diagrama)\.sql$", m):
                            with open(os.path.join(mig_dir_temp, m), "w", encoding="utf-8") as f:
                                f.write(esquema_nuevo)

        # 3. Copiar archivos nuevos SOBRE el clon manteniendo archivos nativos y configuraciones
        # Esto previene pérdida de carpetas nativas (android, ios, windows, web) y configs locales
        shutil.copytree(carpeta_temporal, carpeta_clon, dirs_exist_ok=True)
        
        # 4. Configurar Git usando cwd=carpeta_clon
        subprocess.run(["git", "config", "user.name", "IA Assistant"], cwd=carpeta_clon, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "ia@assistant.local"], cwd=carpeta_clon, check=True, capture_output=True)
        
        # 5. Añadir archivos al stage para calcular el diff
        subprocess.run(["git", "add", "."], cwd=carpeta_clon, check=True, capture_output=True)
        
        # 6. Obtener el diff (staged)
        diff_process = subprocess.run(["git", "diff", "--staged"], cwd=carpeta_clon, check=True, capture_output=True, text=True)
        diff_content = diff_process.stdout
        
        if not diff_content.strip():
            # Si no hay cambios, no hacemos nada
            return "No se detectaron cambios en el diagrama para subir a GitHub."
            
        # 7. Generar mensaje con IA
        mensaje_commit = await generar_mensaje_commit_ia(diff_content)
        
        # 8. Commit y Push desde el clon
        subprocess.run(["git", "commit", "-m", mensaje_commit], cwd=carpeta_clon, check=True, capture_output=True)
        push_process = subprocess.run(["git", "push", "origin", "main"], cwd=carpeta_clon, check=True, capture_output=True, text=True)
        
        return mensaje_commit
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        error_msg_safe = error_msg.replace(token, "***TOKEN***")
        print(f"Git Update Error: {error_msg_safe}")
        raise HTTPException(status_code=500, detail=f"Error en Git al actualizar: {error_msg_safe}")
    except Exception as e:
        print(f"General Update Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar código: {str(e)}")
    finally:
        # Destruir carpetas
        if os.path.exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal, ignore_errors=True)
        if os.path.exists(carpeta_clon):
            shutil.rmtree(carpeta_clon, ignore_errors=True)

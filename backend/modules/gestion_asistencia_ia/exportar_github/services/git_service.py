import subprocess
import os
import shutil
from fastapi import HTTPException

def subir_codigo_a_github(carpeta_temporal: str, url_repo: str, token: str):
    """Sube el contenido de una carpeta temporal a un repositorio de GitHub utilizando git."""
    try:
        if not os.path.exists(carpeta_temporal):
            raise Exception("La carpeta temporal con el código generado no existe.")
            
        # Inyectamos el token en la URL de forma segura para autenticación HTTPS
        # url_repo suele ser "https://github.com/usuario/repo.git"
        url_con_token = url_repo.replace("https://", f"https://x-access-token:{token}@")
        
        # Nos aseguramos de estar en la carpeta correcta
        os.chdir(carpeta_temporal)
        
        # Comandos de Git
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # Configurar un usuario temporal para el commit (Git a veces se queja si no hay config)
        subprocess.run(["git", "config", "user.name", "IA Assistant"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "ia@assistant.local"], check=True, capture_output=True)
        
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Commit inicial: Backend generado por IA"], check=True, capture_output=True)
        
        # Renombramos la rama principal a main (por si se inicializó como master)
        subprocess.run(["git", "branch", "-M", "main"], check=True, capture_output=True)
        
        # Hacemos push al repositorio con el token inyectado
        push_process = subprocess.run(["git", "push", "-u", url_con_token, "main"], check=True, capture_output=True, text=True)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        # Limpiar token del error por seguridad si es que se imprime
        error_msg_safe = error_msg.replace(token, "***TOKEN***")
        raise HTTPException(status_code=500, detail=f"Error en Git: {error_msg_safe}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir código: {str(e)}")
    finally:
        # Destruir la carpeta temporal para liberar espacio
        if os.path.exists(carpeta_temporal):
            os.chdir("..") # Salimos para poder borrarla
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
        
        # 2. Mover la carpeta .git del clon a la nueva carpeta generada
        git_dir_src = os.path.join(carpeta_clon, ".git")
        git_dir_dst = os.path.join(carpeta_temporal, ".git")
        shutil.move(git_dir_src, git_dir_dst)
        
        # Nos movemos a la nueva carpeta (que ahora es un repo git con cambios sin registrar)
        os.chdir(carpeta_temporal)
        
        # 3. Configurar Git
        subprocess.run(["git", "config", "user.name", "IA Assistant"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "ia@assistant.local"], check=True, capture_output=True)
        
        # 4. Añadir archivos al stage para calcular el diff
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # 5. Obtener el diff (staged)
        diff_process = subprocess.run(["git", "diff", "--staged"], check=True, capture_output=True, text=True)
        diff_content = diff_process.stdout
        
        if not diff_content.strip():
            # Si no hay cambios, no hacemos nada
            return "No se detectaron cambios en el diagrama para subir a GitHub."
            
        # 6. Generar mensaje con IA
        mensaje_commit = await generar_mensaje_commit_ia(diff_content)
        
        # 7. Commit y Push
        subprocess.run(["git", "commit", "-m", mensaje_commit], check=True, capture_output=True)
        push_process = subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True, text=True)
        
        return mensaje_commit
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        error_msg_safe = error_msg.replace(token, "***TOKEN***")
        raise HTTPException(status_code=500, detail=f"Error en Git al actualizar: {error_msg_safe}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar código: {str(e)}")
    finally:
        # Destruir carpetas
        os.chdir("..") # Salir por si acaso
        if os.path.exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal, ignore_errors=True)
        if os.path.exists(carpeta_clon):
            shutil.rmtree(carpeta_clon, ignore_errors=True)

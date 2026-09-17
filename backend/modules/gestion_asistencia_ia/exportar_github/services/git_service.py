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
        subprocess.run(["git", "commit", "-m", "🚀 Commit inicial: Backend generado por IA"], check=True, capture_output=True)
        
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

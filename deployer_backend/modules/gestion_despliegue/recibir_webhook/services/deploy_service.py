import os
import subprocess
import shutil
import asyncio
from pathlib import Path
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models import Deployment
import platform
import psutil
import re
import socket


def ocultar_secretos(texto: str) -> str:
    """Quita tokens de URLs (https://x-access-token:TOKEN@github.com) antes de imprimir."""
    return re.sub(r"(https?://)[^/@\s]+@", r"\1***@", str(texto))


def encontrar_proyecto_maven(project_dir: str) -> str:
    """Carpeta con el pom.xml: la raíz, backend/ (monorepo exportado por el diagramador) u otra
    subcarpeta de primer nivel."""
    candidatos = [project_dir, os.path.join(project_dir, "backend")]
    try:
        candidatos += [os.path.join(project_dir, d) for d in sorted(os.listdir(project_dir))
                       if not d.startswith(".") and os.path.isdir(os.path.join(project_dir, d))]
    except OSError:
        pass
    for carpeta in candidatos:
        if os.path.isfile(os.path.join(carpeta, "pom.xml")):
            return carpeta
    raise RuntimeError(f"No se encontró pom.xml en {project_dir} ni en sus subcarpetas.")


def _pg_local() -> bool:
    return settings.PG_HOST in ("localhost", "127.0.0.1", "::1", "")


def psql(sql: str, db_name: str = None, capturar: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta SQL como administrador de PostgreSQL.

    - PostgreSQL en este VPS: como el usuario del sistema `postgres` por socket local (peer). En
      Ubuntu `postgres` no tiene contraseña por TCP: con `-h 127.0.0.1` psql salía con código 2
      y la BD del proyecto nunca se creaba.
    - PostgreSQL remoto: TCP con PG_PASSWORD.
    El SQL va por stdin: así las contraseñas no aparecen en errores, logs ni en `ps`."""
    opciones = ["-v", "ON_ERROR_STOP=1", "-X", "-q"] + (["-t", "-A"] if capturar else [])
    if db_name:
        opciones += ["-d", db_name]
    env = os.environ.copy()
    if _pg_local() and platform.system() == "Linux":
        if os.geteuid() == 0:
            # runuser vive en /usr/sbin, que no siempre está en el PATH del servicio systemd
            runuser = shutil.which("runuser") or next(
                (r for r in ("/usr/sbin/runuser", "/sbin/runuser") if os.path.exists(r)), None)
            comando = ([runuser, "-u", "postgres", "--"] if runuser else ["sudo", "-u", "postgres"]) + ["psql"]
        else:
            comando = ["sudo", "-u", "postgres", "psql"]
    else:
        comando = ["psql", "-U", "postgres", "-h", settings.PG_HOST]
        env["PGPASSWORD"] = settings.PG_PASSWORD
    resultado = subprocess.run(comando + opciones, input=sql, env=env, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"psql salió con código {resultado.returncode}: {resultado.stderr.strip()[:500]}")
    return resultado

async def ensure_dependencies():
    """Verify and install dependencies like Git, Java, Maven if on Linux."""
    if platform.system() != "Linux":
        print("Not on Linux, assuming dependencies are installed manually.")
        return
        
    try:
        res_java = subprocess.run(["java", "-version"], capture_output=True)
        if res_java.returncode != 0:
            print("Installing default-jre...")
            subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "default-jre"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "default-jdk"], check=True)
            
        res_mvn = subprocess.run(["mvn", "-version"], capture_output=True)
        if res_mvn.returncode != 0:
            print("Installing maven...")
            subprocess.run(["sudo", "apt-get", "install", "-y", "maven"], check=True)
            
        res_git = subprocess.run(["git", "--version"], capture_output=True)
        if res_git.returncode != 0:
            print("Installing git...")
            subprocess.run(["sudo", "apt-get", "install", "-y", "git"], check=True)
    except Exception as e:
        print(f"Error ensuring dependencies: {e}")

# Puertos del VPS que NO puede tomar una app desplegada (comparten servidor dos proyectos):
#   8000 backend del diagramador · 8080 API del diagramador por IP (nginx)
#   8001 deployer (uvicorn)      · 8081 deployer por IP (nginx)
PUERTOS_RESERVADOS = {80, 443, 5432, 8000, 8001, 8080, 8081}
PUERTO_INICIAL_APPS = 9000


def get_free_port(start_port: int = PUERTO_INICIAL_APPS, exclude_ports: set = None) -> int:
    """Encuentra el primer puerto libre que no esté asignado en la BD ni reservado por el sistema."""
    if exclude_ports is None:
        exclude_ports = set()

    reserved_system_ports = PUERTOS_RESERVADOS.union(exclude_ports)
    port = start_port
    while port < 65535:
        if port in reserved_system_ports:
            port += 1
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', port)) != 0:
                    return port
        except Exception:
            pass
        port += 1
    raise Exception("No hay puertos libres disponibles en el servidor.")

def ensure_nginx_include():
    """Asegura que 'include /etc/nginx/deploy_apps/*.conf;' esté dentro de un bloque server activo de Nginx."""
    if platform.system() != "Linux":
        return
    try:
        sites_dir = Path("/etc/nginx/sites-enabled")
        if not sites_dir.exists():
            return
            
        # Solo los sitios del DEPLOYER: antes tomaba el primer archivo con "server {" y podía
        # meter las apps desplegadas dentro del nginx del diagramador.
        target_file = None
        for nombre in ("deployer.conf", "deployer-ip.conf"):
            conf_file = sites_dir / nombre
            if not conf_file.exists():
                continue
            content = conf_file.read_text(encoding="utf-8", errors="ignore")
            if "deploy_apps/*.conf" in content:
                return
            target_file = target_file or conf_file

        if target_file:
            content = target_file.read_text(encoding="utf-8", errors="ignore")
            new_content = content.replace("server {", "server {\n    include /etc/nginx/deploy_apps/*.conf;\n", 1)
            target_file.write_text(new_content, encoding="utf-8")
            print(f"Incluido /etc/nginx/deploy_apps/*.conf en {target_file}")
    except Exception as e:
        print(f"Advertencia al incluir deploy_apps en Nginx: {e}")

def kill_process_on_port(port: int):
    """Encuentra y mata de forma segura el proceso (Spring Boot) que esté usando el puerto."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        print(f"Matando proceso {proc.pid} ({proc.name()}) en el puerto {port}")
                        proc.terminate()
                        proc.wait(timeout=5)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    except psutil.TimeoutExpired:
                        proc.kill()
    except Exception as e:
        print(f"Error al intentar buscar/matar proceso en puerto {port}: {e}")

def grant_all_permissions_to_db(db_name: str, db_user: str):
    """Otorgar permisos totales sobre la BD, esquema public, tablas y secuencias al usuario."""
    if platform.system() != "Linux":
        return
    try:
        grant_sql = (
            f'ALTER SCHEMA public OWNER TO "{db_user}"; '
            f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{db_user}"; '
            f'GRANT ALL ON SCHEMA public TO "{db_user}"; '
            f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{db_user}"; '
            f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{db_user}"; '
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{db_user}"; '
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{db_user}"; '
            f'ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO "{db_user}"; '
            f'ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO "{db_user}";'
        )
        psql(grant_sql, db_name=db_name)
        print(f"[{db_name}] Permisos PostgreSQL otorgados a {db_user}.")
    except Exception as e:
        print(f"[{db_name}] Error al otorgar permisos: {e}")

def auto_fix_all_databases():
    """Recorre todas las bases de datos de usuarios en PostgreSQL y otorga permisos totales a sus propietarios."""
    if platform.system() != "Linux":
        return
    try:
        result = psql("SELECT datname, pg_catalog.pg_get_userbyid(datdba) FROM pg_database "
                      "WHERE datname NOT IN ('postgres', 'template0', 'template1');", capturar=True)
        for line in result.stdout.strip().split("\n"):
            parts = line.split("|")
            if len(parts) == 2:
                dbname = parts[0].strip()
                dbowner = parts[1].strip()
                if dbname and dbowner and dbowner != "postgres":
                    grant_all_permissions_to_db(dbname, dbowner)
    except Exception as e:
        print(f"Error en auto_fix_all_databases: {e}")

async def deploy_project(repo_url: str, project_id: int, db: AsyncSession, db_name: str = None, db_password: str = None, owner_prefix: str = None):
    """
    Background task to clone, build, and run the project.
    """
    await ensure_dependencies()
    
    # Extract repo name from URL
    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
        
    project_dir = os.path.join(settings.WORKSPACE_DIR, f"{project_id}_{repo_name}")
    
    # 1. Git Clone or Pull
    if os.path.exists(project_dir):
        print(f"Directory {project_dir} exists. Pulling latest changes...")
        subprocess.run(["git", "pull"], cwd=project_dir, check=True)
    else:
        # La URL lleva el token de GitHub: nunca imprimirla tal cual
        print(f"Cloning {ocultar_secretos(repo_url)} into {project_dir}...")
        clon = subprocess.run(["git", "clone", repo_url, project_dir], capture_output=True, text=True)
        if clon.returncode != 0:
            raise RuntimeError(f"git clone falló: {ocultar_secretos(clon.stderr.strip())[:500]}")

    # 2. Create Database in Postgres (if auto_deploy requested)
    if db_name and db_password and owner_prefix:
        print(f"[{project_id}] Aprovisionando base de datos PostgreSQL: {db_name} con usuario {owner_prefix}...")
        db_user = owner_prefix
        clave = db_password.replace("'", "''")
        try:
            psql(f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{db_user}') "
                 f"THEN CREATE ROLE \"{db_user}\" WITH LOGIN ENCRYPTED PASSWORD '{clave}'; "
                 f"ELSE ALTER ROLE \"{db_user}\" WITH LOGIN PASSWORD '{clave}'; END IF; END $$;")
            existe = psql(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';", capturar=True)
            if "1" not in existe.stdout:
                psql(f'CREATE DATABASE "{db_name}" OWNER "{db_user}";')
            # Otorgar permisos completos sobre la BD, esquema public, tablas y secuencias
            grant_all_permissions_to_db(db_name, db_user)
            print(f"[{project_id}] Base de datos {db_name} lista.")
        except Exception as e:
            print(f"[{project_id}] Error aprovisionando BD PostgreSQL: {e}")

    # 3. Build the project using Maven
    # El diagramador exporta un MONOREPO (backend/ + frontend/): el pom.xml está en backend/,
    # no en la raíz. Antes Maven corría en la raíz y fallaba al instante ("no POM").
    build_dir = encontrar_proyecto_maven(project_dir)
    print(f"[{project_id}] Compilando con Maven en {os.path.relpath(build_dir, project_dir)}/ ...")
    mvn_cmd = "mvn.cmd" if platform.system() == "Windows" else "mvn"
    maven_env = os.environ.copy()
    java17_home = "/usr/lib/jvm/java-17-openjdk-amd64"
    if os.path.isdir(java17_home):
        maven_env["JAVA_HOME"] = java17_home
        maven_env["PATH"] = f"{java17_home}/bin:" + maven_env.get("PATH", "")
    build = subprocess.run([mvn_cmd, "-B", "clean", "package", "-DskipTests"], cwd=build_dir,
                           env=maven_env, capture_output=True, text=True)
    if build.returncode != 0:
        # Antes solo decía "returned non-zero exit status 1": se muestran los errores reales
        salida = (build.stdout + build.stderr).splitlines()
        errores = [l for l in salida if "[ERROR]" in l][:25] or salida[-40:]
        print(f"[{project_id}] Maven falló. Java usado: {maven_env.get('JAVA_HOME', 'el del sistema')}")
        print("\n".join(errores))
        raise RuntimeError("La compilación con Maven falló (ver errores arriba).")

    # Find the generated jar
    target_dir = os.path.join(build_dir, "target")
    jar_file = None
    if os.path.exists(target_dir):
        for file in os.listdir(target_dir):
            if file.endswith(".jar") and not file.endswith("-sources.jar"):
                jar_file = os.path.join(target_dir, file)
                break
            
    if not jar_file:
        raise Exception("JAR file not found after build.")
        
    target_jar = jar_file

    # 4. Database operations (Find deployment, assign port)
    result = await db.execute(select(Deployment).where(Deployment.project_id == project_id))
    deployment = result.scalar_one_or_none()

    # Puertos ocupados por otros proyectos en la BD
    other_deployments = await db.execute(select(Deployment.port).where(Deployment.project_id != project_id))
    used_ports_in_db = set(p for p in other_deployments.scalars().all() if p is not None)
    
    if not deployment:
        port = get_free_port(exclude_ports=used_ports_in_db)
        
        deployment = Deployment(
            project_id=project_id,
            repo_url=repo_url,
            port=port,
            status='deploying'
        )
        db.add(deployment)
        await db.commit()
        await db.refresh(deployment)
    elif deployment.port in used_ports_in_db:
        new_port = get_free_port(exclude_ports=used_ports_in_db)
        deployment.port = new_port
        await db.commit()
        await db.refresh(deployment)
        
    # 5. Kill old process safely by port
    if deployment.port:
        print(f"Asegurando que el puerto {deployment.port} esté libre...")
        kill_process_on_port(deployment.port)
            
    # 6. Run the Spring Boot application
    print(f"[{project_id}] Starting Spring Boot application on port {deployment.port}...")
    log_file = open(os.path.join(project_dir, "app.log"), "w")
    
    java_cmd = [
        "java",
        "-jar", target_jar,
        f"--server.port={deployment.port}",
    ]
    
    if db_name and db_password and owner_prefix:
        java_cmd.extend([
            f"--spring.datasource.password={db_password}",
            f"--spring.datasource.username={owner_prefix}",
            f"--spring.datasource.url=jdbc:postgresql://127.0.0.1:5432/{db_name}"
        ])
        
    if owner_prefix and db_name:
        java_cmd.append(f"--server.servlet.context-path=/host/{owner_prefix}/{db_name}")
    
    if platform.system() == "Windows":
        process = subprocess.Popen(java_cmd, cwd=build_dir, stdout=log_file, stderr=log_file)
    else:
        process = subprocess.Popen(java_cmd, cwd=build_dir, stdout=log_file, stderr=log_file, start_new_session=True)
        
    print(f"[{project_id}] Esperando a que Spring Boot inicie y escuche en el puerto {deployment.port}...")
    ready = False
    for _ in range(180):  # hasta 90 s: en el VPS Spring + Flyway puede tardar más de 15 s
        await asyncio.sleep(0.5)
        if process.poll() is not None:
            break
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex(('127.0.0.1', deployment.port)) == 0:
                    ready = True
                    break
        except Exception:
            pass

    if process.poll() is not None:
        print(f"[{project_id}] ERROR: El proceso de Spring Boot finalizó prematuramente (código: {process.returncode}).")
        causa = "revisa app.log"
        try:
            with open(os.path.join(project_dir, "app.log"), "r", encoding="utf-8", errors="ignore") as f:
                lineas = f.read().splitlines()
            # Lo útil son las causas, no las 40 líneas de stack trace del final
            claves = [l for l in lineas if re.search(r"Caused by|ERROR|Detail:|Where:|APPLICATION FAILED|Description:|Action:", l)]
            print(f"[{project_id}] --- APP LOG (causas) ---")
            print("\n".join(claves[-30:] or lineas[-40:]))
            print(f"[{project_id}] --- FIN ---")
            causas = [l for l in claves if "Caused by" in l or "Detail:" in l]
            if causas:
                causa = causas[-1].strip()[:300]
        except Exception as log_err:
            print(f"[{project_id}] No se pudo leer app.log: {log_err}")
        deployment.status = "failed"
        await db.commit()
        # Sin esto se publicaba en nginx una app muerta y el usuario solo veía 502 Bad Gateway
        raise RuntimeError(f"Spring Boot no arrancó: {causa}")
    elif not ready:
        print(f"[{project_id}] Spring Boot sigue iniciando (PID {process.pid}); se publica igual en el puerto {deployment.port}.")
        if db_name and owner_prefix:
            grant_all_permissions_to_db(db_name, owner_prefix)
    else:
        print(f"[{project_id}] El proceso de Spring Boot (PID {process.pid}) está activo y respondiendo en el puerto {deployment.port}.")
        
        # Otorgar permisos sobre todas las tablas recién creadas por Flyway/Hibernate al usuario del proyecto
        if db_name and owner_prefix:
            grant_all_permissions_to_db(db_name, owner_prefix)
        
    # 7. Configurar Nginx Dinámicamente si hay owner_prefix
    deployment_url = f"http://{settings.SERVER_HOST}:{deployment.port}"
    if owner_prefix and db_name:
        try:
            ensure_nginx_include()
            nginx_conf_dir = "/etc/nginx/deploy_apps"
            os.makedirs(nginx_conf_dir, exist_ok=True)
            
            nginx_conf_path = os.path.join(nginx_conf_dir, f"{project_id}.conf")
            nginx_conf_content = f'''location /host/{owner_prefix}/{db_name} {{
    if ($request_method = 'OPTIONS') {{
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,Accept' always;
        add_header 'Access-Control-Max-Age' 1728000 always;
        add_header 'Content-Type' 'text/plain; charset=utf-8' always;
        add_header 'Content-Length' 0 always;
        return 204;
    }}

    proxy_pass http://127.0.0.1:{deployment.port};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /host/{owner_prefix}/{db_name};
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}}
'''
            with open(nginx_conf_path, "w", encoding="utf-8") as f:
                f.write(nginx_conf_content)
                
            test_res = subprocess.run(["sudo", "nginx", "-t"], capture_output=True, text=True)
            if test_res.returncode != 0:
                print(f"[{project_id}] ERROR Sintaxis Nginx: {test_res.stderr}")
            else:
                subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
                print(f"[{project_id}] Nginx reload OK. App en /host/{owner_prefix}/{db_name}/")
            deployment_url = f"{settings.SERVER_DOMAIN}/host/{owner_prefix}/{db_name}/"
        except Exception as e:
            print(f"[{project_id}] Error configurando Nginx: {e}")

    # 8. Update DB
    deployment.pid = process.pid
    deployment.status = "running"
    deployment.deployed_url = deployment_url
    await db.commit()
    
    # 9. Notify Main API
    print(f"Deployment successful. PID: {deployment.pid}, Port: {deployment.port}")
    
    import httpx
    callback_url = f"{settings.MAIN_API_URL}/deploy-callback"
    
    payload = {
        "project_id": project_id,
        "deployment_url": deployment_url
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(callback_url, json=payload)
            if resp.status_code == 200:
                print("Callback to main API successful.")
            else:
                print(f"Callback to main API failed with status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Could not reach main API for callback: {e}")
            
    return deployment

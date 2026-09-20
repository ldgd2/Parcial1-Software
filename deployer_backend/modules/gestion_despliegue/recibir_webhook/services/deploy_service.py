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
import socket

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

def get_free_port(start_port: int = 8080, exclude_ports: set = None) -> int:
    """Encuentra el primer puerto libre que no esté asignado en la BD ni reservado por el sistema."""
    if exclude_ports is None:
        exclude_ports = set()
        
    reserved_system_ports = {80, 443, 5432, 8000, 8001}.union(exclude_ports)
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
            
        already_included = False
        target_file = None
        
        for conf_file in sites_dir.glob("*"):
            try:
                content = conf_file.read_text(encoding="utf-8", errors="ignore")
                if "deploy_apps/*.conf" in content:
                    already_included = True
                    break
                if not target_file and "server {" in content:
                    target_file = conf_file
            except Exception:
                pass
                
        if not already_included and target_file:
            content = target_file.read_text(encoding="utf-8", errors="ignore")
            new_content = content.replace("server {", "server {\n    include /etc/nginx/deploy_apps/*.conf;\n")
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
        print(f"Cloning {repo_url} into {project_dir}...")
        subprocess.run(["git", "clone", repo_url, project_dir], check=True)
        
    # 2. Create Database in Postgres (if auto_deploy requested)
    if db_name and db_password and owner_prefix:
        print(f"[{project_id}] Aprovisionando base de datos PostgreSQL: {db_name} con usuario {owner_prefix}...")
        db_user = owner_prefix
        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.PG_PASSWORD
            pg_host = settings.PG_HOST
            psql_cmd = ["psql", "-U", "postgres", "-h", pg_host]

            create_role_sql = f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{db_user}') THEN CREATE ROLE \"{db_user}\" WITH LOGIN ENCRYPTED PASSWORD '{db_password}'; ELSE ALTER ROLE \"{db_user}\" WITH PASSWORD '{db_password}'; END IF; END $$;"
            subprocess.run(psql_cmd + ["-c", create_role_sql], env=env, check=True)

            check_result = subprocess.run(psql_cmd + ["-t", "-c", f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';"], env=env, capture_output=True, text=True)
            if "1" not in check_result.stdout:
                subprocess.run(psql_cmd + ["-c", f'CREATE DATABASE "{db_name}" OWNER "{db_user}";'], env=env, check=True)
            
            # Otorgar permisos completos sobre la BD, esquema public, tablas y secuencias
            psql_db_cmd = ["psql", "-U", "postgres", "-h", pg_host, "-d", db_name]
            grant_schema_sql = (
                f'ALTER SCHEMA public OWNER TO "{db_user}"; '
                f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{db_user}"; '
                f'GRANT ALL ON SCHEMA public TO "{db_user}"; '
                f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{db_user}"; '
                f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{db_user}"; '
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{db_user}"; '
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{db_user}";'
            )
            subprocess.run(psql_db_cmd + ["-c", grant_schema_sql], env=env, check=True)
            print(f"[{project_id}] Base de datos {db_name} lista y permisos totales otorgados a {db_user}.")
        except subprocess.CalledProcessError as e:
            print(f"[{project_id}] Error aprovisionando BD PostgreSQL: {e}")

    # 3. Build the project using Maven
    print("Building project with Maven...")
    mvn_cmd = "mvn.cmd" if platform.system() == "Windows" else "mvn"
    maven_env = os.environ.copy()
    java17_home = "/usr/lib/jvm/java-17-openjdk-amd64"
    if os.path.isdir(java17_home):
        maven_env["JAVA_HOME"] = java17_home
        maven_env["PATH"] = f"{java17_home}/bin:" + maven_env.get("PATH", "")
    subprocess.run([mvn_cmd, "clean", "package", "-DskipTests"], cwd=project_dir, env=maven_env, check=True)

    # Find the generated jar
    target_dir = os.path.join(project_dir, "target")
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
        port = get_free_port(start_port=8080, exclude_ports=used_ports_in_db)
        
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
        new_port = get_free_port(start_port=8080, exclude_ports=used_ports_in_db)
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
        process = subprocess.Popen(java_cmd, cwd=project_dir, stdout=log_file, stderr=log_file)
    else:
        process = subprocess.Popen(java_cmd, cwd=project_dir, stdout=log_file, stderr=log_file, start_new_session=True)
        
    print(f"[{project_id}] Esperando 6 segundos a que Spring Boot inicie en puerto {deployment.port}...")
    await asyncio.sleep(6)
    
    if process.poll() is not None:
        print(f"[{project_id}] ERROR: El proceso de Spring Boot finalizó prematuramente (código: {process.returncode}).")
        try:
            with open(os.path.join(project_dir, "app.log"), "r", encoding="utf-8", errors="ignore") as f:
                logs = f.read()
                print(f"[{project_id}] --- APP LOG INICIO ---")
                print(logs[-2000:] if len(logs) > 2000 else logs)
                print(f"[{project_id}] --- APP LOG FIN ---")
        except Exception as log_err:
            print(f"[{project_id}] No se pudo leer app.log: {log_err}")
    else:
        print(f"[{project_id}] El proceso de Spring Boot (PID {process.pid}) está activo en el puerto {deployment.port}.")
        
        # Otorgar permisos sobre todas las tablas recién creadas por Flyway/Hibernate al usuario del proyecto
        if db_name and owner_prefix:
            try:
                env = os.environ.copy()
                env["PGPASSWORD"] = settings.PG_PASSWORD
                pg_host = settings.PG_HOST
                psql_db_cmd = ["psql", "-U", "postgres", "-h", pg_host, "-d", db_name]
                grant_sql = (
                    f'ALTER SCHEMA public OWNER TO "{owner_prefix}"; '
                    f'GRANT ALL ON SCHEMA public TO "{owner_prefix}"; '
                    f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{owner_prefix}"; '
                    f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{owner_prefix}"; '
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{owner_prefix}"; '
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{owner_prefix}";'
                )
                subprocess.run(psql_db_cmd + ["-c", grant_sql], env=env, check=False)
                print(f"[{project_id}] Permisos sobre tablas otorgados a {owner_prefix} en BD {db_name}.")
            except Exception as e:
                print(f"[{project_id}] Advertencia al otorgar permisos post-despliegue: {e}")
        
    # 7. Configurar Nginx Dinámicamente si hay owner_prefix
    deployment_url = f"http://{settings.SERVER_HOST}:{deployment.port}"
    if owner_prefix and db_name:
        try:
            ensure_nginx_include()
            nginx_conf_dir = "/etc/nginx/deploy_apps"
            os.makedirs(nginx_conf_dir, exist_ok=True)
            
            nginx_conf_path = os.path.join(nginx_conf_dir, f"{project_id}.conf")
            nginx_conf_content = f'''location /host/{owner_prefix}/{db_name} {{
    proxy_pass http://127.0.0.1:{deployment.port};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /host/{owner_prefix}/{db_name};
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

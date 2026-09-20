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

async def ensure_dependencies():
    """Verify and install dependencies like Git, Java, Maven if on Linux."""
    if platform.system() != "Linux":
        print("Not on Linux, assuming dependencies are installed manually.")
        return
        
    try:
        # Check if java is installed
        res_java = subprocess.run(["java", "-version"], capture_output=True)
        if res_java.returncode != 0:
            print("Installing default-jre...")
            subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "default-jre"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "default-jdk"], check=True)
            
        # Check if maven is installed
        res_mvn = subprocess.run(["mvn", "-version"], capture_output=True)
        if res_mvn.returncode != 0:
            print("Installing maven...")
            subprocess.run(["sudo", "apt-get", "install", "-y", "maven"], check=True)
            
        # Check git
        res_git = subprocess.run(["git", "--version"], capture_output=True)
        if res_git.returncode != 0:
            print("Installing git...")
            subprocess.run(["sudo", "apt-get", "install", "-y", "git"], check=True)
    except Exception as e:
        print(f"Error ensuring dependencies: {e}")

import socket

def get_free_port(start_port: int = 8080) -> int:
    """Encuentra el primer puerto libre a partir de start_port."""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
        port += 1
    raise Exception("No hay puertos libres disponibles.")

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
    1. Git clone / pull
    2. Build (mvn clean package)
    3. Find free port
    4. Kill old process if exists
    5. Start new process
    6. Update DB
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
        
    # 2. Build with Maven
    # 3. Create Database in Postgres (if auto_deploy requested)
    if db_name and db_password and owner_prefix:
        print(f"[{project_id}] Aprovisionando base de datos PostgreSQL: {db_name} con usuario {owner_prefix}...")
        db_user = owner_prefix
        
        # We run psql commands as the 'postgres' user. This requires 'sudo -u postgres psql'
        # or passwordless psql access for the system user.
        # Ensure that the deployer VPS has postgresql installed and the deployer runs with proper rights.
        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.PG_PASSWORD
            pg_host = settings.PG_HOST
            psql_cmd = ["psql", "-U", "postgres", "-h", pg_host]

            create_role_sql = f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{db_user}') THEN CREATE ROLE \"{db_user}\" WITH LOGIN ENCRYPTED PASSWORD '{db_password}'; END IF; END $$;"
            subprocess.run(psql_cmd + ["-c", create_role_sql], env=env, check=True)

            check_result = subprocess.run(psql_cmd + ["-t", "-c", f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';"], env=env, capture_output=True, text=True)
            if "1" not in check_result.stdout:
                subprocess.run(psql_cmd + ["-c", f'CREATE DATABASE "{db_name}" OWNER "{db_user}";'], env=env, check=True)
            print(f"[{project_id}] Base de datos {db_name} lista.")
        except subprocess.CalledProcessError as e:
            print(f"[{project_id}] Error aprovisionando BD PostgreSQL: {e}")
            # Non-fatal error, but Spring Boot might fail to connect
    
    # 4. Build the project using Maven
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

    # 3. Database operations (Find deployment, assign port)
    result = await db.execute(select(Deployment).where(Deployment.project_id == project_id))
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        # Find next available port starting from max in DB + 1, or 8080
        max_port_query = await db.execute(select(func.max(Deployment.port)))
        max_port_val = max_port_query.scalar()
        start_port = max_port_val + 1 if max_port_val and max_port_val >= 8080 else 8080
        
        # Verify physical port availability
        port = get_free_port(start_port)
        
        deployment = Deployment(
            project_id=project_id,
            repo_url=repo_url,
            port=port,
            status='deploying'
        )
        db.add(deployment)
        await db.commit()
        await db.refresh(deployment)
        
    # 4. Kill old process safely by port
    if deployment.port:
        print(f"Asegurando que el puerto {deployment.port} esté libre...")
        kill_process_on_port(deployment.port)
            
    # 5. Run the Spring Boot application
    print(f"[{project_id}] Starting Spring Boot application on port {deployment.port}...")
    log_file = open(os.path.join(project_dir, "app.log"), "w")
    
    java_cmd = [
        "java",
        f"-Dserver.port={deployment.port}",
    ]
    
    if db_name and db_password and owner_prefix:
        java_cmd.extend([
            f"--spring.datasource.password={db_password}",
            f"--spring.datasource.username={owner_prefix}",
            f"--spring.datasource.url=jdbc:postgresql://127.0.0.1:5432/{db_name}"
        ])
        
    if owner_prefix and db_name:
        java_cmd.append(f"--server.servlet.context-path=/host/{owner_prefix}/{db_name}")
        
    java_cmd.extend(["-jar", target_jar])
    
    if platform.system() == "Windows":
        process = subprocess.Popen(java_cmd, cwd=project_dir, stdout=log_file, stderr=log_file)
    else:
        # In Linux, nohup equivalent or just detaching
        process = subprocess.Popen(java_cmd, cwd=project_dir, stdout=log_file, stderr=log_file, start_new_session=True)
        
    # 6. Configurar Nginx Dinámicamente si hay owner_prefix
    deployment_url = f"http://{settings.SERVER_HOST}:{deployment.port}"
    if owner_prefix and db_name:
        try:
            nginx_conf_dir = "/etc/nginx/deploy_apps"
            os.makedirs(nginx_conf_dir, exist_ok=True)
            
            nginx_conf_path = os.path.join(nginx_conf_dir, f"{project_id}.conf")
            nginx_conf_content = f'''location /host/{owner_prefix}/{db_name}/ {{
    proxy_pass http://localhost:{deployment.port};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}}
'''
            with open(nginx_conf_path, "w", encoding="utf-8") as f:
                f.write(nginx_conf_content)
                
            subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
            print(f"[{project_id}] Nginx reload OK. App en /host/{owner_prefix}/{db_name}/")
            deployment_url = f"{settings.SERVER_DOMAIN}/host/{owner_prefix}/{db_name}/"
        except Exception as e:
            print(f"[{project_id}] Error configurando Nginx: {e}")

    # 7. Update DB
    deployment.pid = process.pid
    deployment.status = "running"
    deployment.deployed_url = deployment_url
    await db.commit()
    
    # 8. Notify Main API
    print(f"Deployment successful. PID: {deployment.pid}, Port: {deployment.port}")
    
    import httpx
    callback_url = f"{settings.MAIN_API_URL}/deploy-callback"
    
    # Send the friendly deployment URL to the main API
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

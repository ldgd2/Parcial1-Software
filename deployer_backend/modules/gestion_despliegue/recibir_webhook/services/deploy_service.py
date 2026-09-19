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

async def deploy_project(repo_url: str, project_id: int, db: AsyncSession):
    """
    Main deployment pipeline:
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
    print("Building project with Maven...")
    # Using shell=True for mvn command in Windows if needed, but subprocess with list is safer
    mvn_cmd = "mvn.cmd" if platform.system() == "Windows" else "mvn"
    subprocess.run([mvn_cmd, "clean", "package", "-DskipTests"], cwd=project_dir, check=True)
    
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
        
    # 4. Kill old process
    if deployment.pid:
        print(f"Killing old process {deployment.pid}")
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/PID", str(deployment.pid)])
            else:
                subprocess.run(["kill", "-9", str(deployment.pid)])
        except Exception as e:
            print(f"Could not kill process: {e}")
            
    # 5. Start new process
    print(f"Starting JAR on port {deployment.port}...")
    log_file = open(os.path.join(project_dir, "app.log"), "w")
    
    # We pass the port to Spring Boot via system property
    java_cmd = ["java", f"-Dserver.port={deployment.port}", "-jar", jar_file]
    
    if platform.system() == "Windows":
        # In Windows, we can use creationflags to detach, but simple Popen works for dev
        process = subprocess.Popen(java_cmd, cwd=project_dir, stdout=log_file, stderr=log_file)
    else:
        # In Linux, nohup equivalent or just detaching
        process = subprocess.Popen(java_cmd, cwd=project_dir, stdout=log_file, stderr=log_file, start_new_session=True)
        
    # 6. Update DB
    deployment.pid = process.pid
    deployment.status = 'running'
    await db.commit()
    
    print(f"Deployment successful. PID: {deployment.pid}, Port: {deployment.port}")
    return deployment

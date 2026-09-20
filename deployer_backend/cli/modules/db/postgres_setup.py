import os
import subprocess
from cli.console import console, print_header
from rich.prompt import Prompt
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), "../../../../.env")

def menu_postgres():
    while True:
        print_header("Configuración de PostgreSQL (Requisito Spring Boot)")
        
        console.print("Este submódulo te permite instalar PostgreSQL y configurar la contraseña")
        console.print("del usuario 'postgres' en este VPS, lo cual es obligatorio para los")
        console.print("despliegues automáticos del motor IA.")
        
        console.print("\n[1] Instalar PostgreSQL (apt-get)")
        console.print("[2] Cambiar contraseña del usuario 'postgres' y guardar en .env")
        console.print("[3] Configurar exposición de red (Local, Dominio, IP Pública)")
        console.print("[0] Volver")
        
        op = Prompt.ask("\nSelecciona una opción", default="0")
        
        if op == "1":
            if os.name != 'nt':
                console.print("[cyan]Instalando PostgreSQL...[/cyan]")
                subprocess.run(["sudo", "apt-get", "update"])
                subprocess.run(["sudo", "apt-get", "install", "-y", "postgresql", "postgresql-contrib"])
                console.print("[bold green]✔ PostgreSQL instalado.[/bold green]")
            else:
                console.print("[yellow]Instalación automática solo disponible en Linux.[/yellow]")
            input("Presiona Enter para continuar...")
            
        elif op == "2":
            if os.name != 'nt':
                new_pass = Prompt.ask("Ingresa la nueva contraseña para el superusuario postgres (Recomendado: postgres)")
                if new_pass:
                    try:
                        # Set postgres password using sudo -u postgres psql
                        sql = f"ALTER USER postgres WITH PASSWORD '{new_pass}';"
                        subprocess.run(["sudo", "-u", "postgres", "psql", "-c", sql], check=True)
                        
                        # Save to .env
                        if not os.path.exists(ENV_FILE):
                            open(ENV_FILE, 'w').close()
                        set_key(ENV_FILE, "PG_PASSWORD", new_pass)
                        
                        console.print(f"[bold green]✔ Contraseña de postgres actualizada en DB y .env[/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]Error al configurar PostgreSQL: {e}[/bold red]")
            else:
                console.print("[yellow]Mock en Windows: Solo actualizando .env[/yellow]")
                new_pass = Prompt.ask("Ingresa la nueva contraseña para postgres")
                if not os.path.exists(ENV_FILE):
                    open(ENV_FILE, 'w').close()
                set_key(ENV_FILE, "PG_PASSWORD", new_pass)
                console.print(f"[bold green]✔ Guardado en .env localmente.[/bold green]")
            input("Presiona Enter para continuar...")
            
        elif op == "3":
            if os.name != 'nt':
                console.print("\n[cyan]--- EXPOSICIÓN DE RED ---[/cyan]")
                console.print("[1] Solo Localhost (Seguro, por defecto)")
                console.print("[2] Por Dominio (Ej. db.example.com - Requiere DNS apuntando a esta IP)")
                console.print("[3] Por IP Pública")
                net_op = Prompt.ask("Selecciona cómo exponer PostgreSQL", choices=["1", "2", "3"])
                
                host_val = "localhost"
                if net_op == "2":
                    host_val = Prompt.ask("Introduce tu dominio (ej. example.com)")
                elif net_op == "3":
                    host_val = Prompt.ask("Introduce tu IP Pública (o deja vacío para auto-detectar)")
                    if not host_val:
                        try:
                            host_val = subprocess.check_output(["curl", "-s", "ifconfig.me"]).decode().strip()
                        except:
                            host_val = "127.0.0.1"
                
                try:
                    console.print("[cyan]Detectando archivos de configuración de PostgreSQL...[/cyan]")
                    conf_file = subprocess.check_output(["sudo", "-u", "postgres", "psql", "-t", "-P", "format=unaligned", "-c", "SHOW config_file;"]).decode().strip()
                    hba_file = subprocess.check_output(["sudo", "-u", "postgres", "psql", "-t", "-P", "format=unaligned", "-c", "SHOW hba_file;"]).decode().strip()
                    
                    if net_op == "1":
                        # Localhost
                        subprocess.run(["sudo", "sed", "-i", "s/^listen_addresses = .*/listen_addresses = 'localhost'/", conf_file])
                        subprocess.run(["sudo", "sed", "-i", "/host all all 0.0.0.0\\/0 md5/d", hba_file])
                    else:
                        # Escuchar en todo (El dominio solo se usa para el cliente)
                        subprocess.run(["sudo", "sed", "-i", "s/^#*listen_addresses = .*/listen_addresses = '*'/", conf_file])
                        
                        # Añadir permiso a pg_hba.conf si no existe
                        check_hba = subprocess.run(["sudo", "grep", "-q", "host all all 0.0.0.0/0 md5", hba_file])
                        if check_hba.returncode != 0:
                            subprocess.run(["sudo", "bash", "-c", f"echo 'host all all 0.0.0.0/0 md5' >> {hba_file}"])
                    
                    console.print("[cyan]Reiniciando PostgreSQL para aplicar cambios...[/cyan]")
                    subprocess.run(["sudo", "systemctl", "restart", "postgresql"])
                    
                    # Guardar en el .env de deployer
                    if not os.path.exists(ENV_FILE):
                        open(ENV_FILE, 'w').close()
                    set_key(ENV_FILE, "PG_HOST", host_val)
                    
                    console.print(f"[bold green]✔ Configuración de red aplicada. PG_HOST guardado como '{host_val}'.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Error al configurar red: {e}[/bold red]")
            else:
                console.print("[yellow]Mock en Windows: Solo actualizando .env[/yellow]")
                host_val = Prompt.ask("Introduce tu dominio/IP para desarrollo local")
                if not os.path.exists(ENV_FILE):
                    open(ENV_FILE, 'w').close()
                set_key(ENV_FILE, "PG_HOST", host_val)
                console.print(f"[bold green]✔ Guardado en .env localmente.[/bold green]")
            input("Presiona Enter para continuar...")
            
        elif op == "0":
            break

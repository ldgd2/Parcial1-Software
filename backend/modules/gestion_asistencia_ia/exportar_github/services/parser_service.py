import os
import re
from jinja2 import Environment, FileSystemLoader

def sanitize_identifier(name: str) -> str:
    """Convierte un string a camelCase válido para Java, limpiando símbolos UML (- email: string -> email)"""
    if not name:
        return "unnamed"
    name = re.sub(r'^[\-\+\#\~\s]+', '', str(name))
    if ':' in name:
        name = name.split(':')[0]
    name = re.sub(r'[^a-zA-Z0-9]', ' ', name)
    parts = name.split()
    if not parts:
        return "unnamed"
    res = parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
    if res[0].isdigit():
        res = "attr" + res
    return res

def map_java_type(tipo_uml: str) -> str:
    """Mapea tipos UML genéricos a tipos Java"""
    t = str(tipo_uml).lower().strip()
    if "int" in t or "entero" in t: return "Integer"
    if "string" in t or "varchar" in t or "texto" in t or "char" in t: return "String"
    if "bool" in t or "logico" in t: return "Boolean"
    if "float" in t or "decimal" in t or "double" in t or "real" in t: return "Double"
    if "date" in t or "fecha" in t: return "java.time.LocalDate"
    return "String"


def obtener_ejemplo_atributo_raw(nombre: str, tipo: str) -> str:
    """Genera un valor de ejemplo realista en formato texto sin comillas envolventes."""
    n = str(nombre).lower().strip()
    t = str(tipo).lower().strip()
    if "email" in n or "correo" in n:
        return "usuario@ejemplo.com"
    if "nombre" in n or "name" in n or "titulo" in n or "title" in n or "criterio" in n or "criterion" in n:
        return f"Ejemplo {nombre.capitalize()}"
    if "desc" in n or "description" in n:
        return f"Descripción detallada de {nombre}"
    if "telefono" in n or "phone" in n or "celular" in n:
        return "+59171234567"
    if "password" in n or "clave" in n or "pass" in n:
        return "Secreto123!"
    if "fecha" in n or "date" in n or "due" in n:
        return "2026-09-20"
    if "score" in n or "punto" in n or "nota" in n or "max" in n or "min" in n:
        return "100"
    if "bool" in t or "activo" in n or "is" in n or "group" in n:
        return "true"
    if "double" in t or "float" in t or "precio" in n or "monto" in n or "total" in n or "costo" in n:
        return "99.50"
    if "int" in t or "integer" in t or "edad" in n or "stock" in n or "cantidad" in n:
        return "10"
    if "uuid" in t or n == "id":
        return "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    return f"ejemplo_{n}"


def obtener_ejemplo_atributo_json(nombre: str, tipo: str) -> str:
    """Genera un valor formateado para JSON (con comillas si es string/date, sin comillas si es número/bool)."""
    val = obtener_ejemplo_atributo_raw(nombre, tipo)
    t = str(tipo).lower().strip()
    if val in ["true", "false"] or t in ["integer", "int", "double", "float", "long", "short"]:
        return val
    return f'"{val}"'


RESERVED_CRUD_METHODS = {'delete', 'deletebyid', 'remove', 'save', 'update', 'create', 'findall', 'findbyid', 'getid', 'setid'}

def parse_java_parameters(params_str: str, method_name: str = "") -> tuple[str, str, str]:
    """
    Parsea parámetros UML o Java a (java_decl, call_args, spring_params).
    Si los parámetros están vacíos pero el nombre del método sugiere una búsqueda o criterio,
    deduce parámetros por defecto para que la API sea funcional y auto-documentada.
    """
    m_lower = method_name.lower().strip()
    
    if not params_str or not str(params_str).strip():
        if "email" in m_lower or "correo" in m_lower or "user" in m_lower or "usuario" in m_lower:
            params_str = "email: string"
        elif "codigo" in m_lower or "code" in m_lower:
            params_str = "codigo: string"
        elif "nombre" in m_lower or "name" in m_lower:
            params_str = "nombre: string"
        elif "estado" in m_lower or "status" in m_lower:
            params_str = "estado: string"
        elif "criterion" in m_lower or "criterio" in m_lower:
            params_str = "criteriondescription: string"
        elif m_lower.startswith(("get", "find", "buscar", "filter", "search")):
            params_str = "query: string"

    if not params_str or not str(params_str).strip():
        return "", "", ""
        
    raw_parts = [p.strip() for p in str(params_str).split(",") if p.strip()]
    java_decls = []
    call_args = []
    spring_params = []
    
    for idx, part in enumerate(raw_parts):
        if ":" in part:
            p_name_raw, p_type_raw = part.split(":", 1)
            p_name = sanitize_identifier(p_name_raw)
            p_type = map_java_type(p_type_raw)
        else:
            sub = part.split()
            if len(sub) >= 2:
                p_type = map_java_type(sub[0])
                p_name = sanitize_identifier(sub[1])
            else:
                p_name = sanitize_identifier(part)
                p_type = "String"
                
        if not p_name or p_name == "unnamed":
            p_name = f"arg{idx}"
            
        ex_val = obtener_ejemplo_atributo_raw(p_name, p_type)
        java_decls.append(f"{p_type} {p_name}")
        call_args.append(p_name)
        spring_params.append(f'@Parameter(description = "Parámetro {p_name} ({p_type})", example = "{ex_val}") @RequestParam(required = false) {p_type} {p_name}')
        
    return ", ".join(java_decls), ", ".join(call_args), ", ".join(spring_params)


def inicializar_estructura_spring(temp_dir: str, nombre_repo: str = "proyecto_db", db_password: str = "password"):
    """
    Crea la estructura de carpetas y archivos base (pom.xml, Application.java, properties)
    para un proyecto Spring Boot estándar sin depender de un .zip
    """
    src_main_java = os.path.join(temp_dir, "src", "main", "java", "com", "proyecto")
    src_main_resources = os.path.join(temp_dir, "src", "main", "resources")
    
    # Crear carpetas
    carpetas = ["models", "repositories", "services", "controllers", "dtos", "exceptions", "config", "common"]
    for carpeta in carpetas:
        os.makedirs(os.path.join(src_main_java, carpeta), exist_ok=True)
        
    os.makedirs(os.path.join(src_main_resources, "db", "migration"), exist_ok=True)
    
    # pom.xml
    with open(os.path.join(temp_dir, "pom.xml"), "w", encoding="utf-8") as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.1.2</version>
        <relativePath/> <!-- lookup parent from repository -->
    </parent>
    <groupId>com.proyecto</groupId>
    <artifactId>backend</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>backend</name>
    <description>Proyecto generado automáticamente</description>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-core</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>2.2.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
''')

    # Sanitizar el nombre para DB (minúsculas, reemplazar guiones por guiones bajos)
    db_name_sanitizado = re.sub(r'[^a-z0-9_]', '_', str(nombre_repo).lower())
    if not db_name_sanitizado:
        db_name_sanitizado = "proyecto_db"

    # .env.example
    with open(os.path.join(temp_dir, ".env.example"), "w", encoding="utf-8") as f:
        f.write(f'''DB_IP=127.0.0.1
DB_PORT=5432
DB_NAME={db_name_sanitizado}
DB_USER={db_name_sanitizado}_user
DB_PASSWORD={db_password}
''')

    # .gitignore
    with open(os.path.join(temp_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write('''HELP.md
target/
!.mvn/wrapper/maven-wrapper.jar
!**/src/main/**/target/
!**/src/test/**/target/

### STS ###
.apt_generated
.classpath
.factorypath
.project
.settings
.springBeans
.sts4-cache

### IntelliJ IDEA ###
.idea
*.iws
*.iml
*.ipr

### NetBeans ###
/nbproject/private/
/nbbuild/
/dist/
/nbdist/
/.nb-gradle/
build/
!**/src/main/**/build/
!**/src/test/**/build/

### VS Code ###
.vscode/

### Custom Secrets ###
.env
*.env
application-local.properties
''')

    # application.properties
    with open(os.path.join(src_main_resources, "application.properties"), "w", encoding="utf-8") as f:
        f.write('''spring.datasource.url=jdbc:postgresql://${DB_IP:127.0.0.1}:${DB_PORT:5432}/${DB_NAME:dbname}
spring.datasource.username=${DB_USER:postgres}
spring.datasource.password=${DB_PASSWORD:password}
spring.jpa.hibernate.ddl-auto=update
spring.flyway.enabled=true
spring.flyway.baseline-on-migrate=true
spring.flyway.out-of-order=true
spring.flyway.validate-on-migrate=false
server.forward-headers-strategy=framework
springdoc.swagger-ui.path=/help
springdoc.api-docs.path=/v3/api-docs
''')

    # HomeController.java
    with open(os.path.join(src_main_java, "controllers", "HomeController.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.controllers;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@CrossOrigin(originPatterns = "*", allowedHeaders = "*", allowCredentials = "true")
@RestController
public class HomeController {

    @GetMapping("/")
    public Map<String, Object> home() {
        return Map.of(
            "status", "online",
            "message", "Servicio Spring Boot activo y en línea",
            "swagger_docs", "help"
        );
    }
}
''')

    # Application.java
    with open(os.path.join(src_main_java, "Application.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
''')

    # CorsConfig.java
    with open(os.path.join(src_main_java, "config", "CorsConfig.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }
}
''')

    # OpenApiConfig.java
    with open(os.path.join(src_main_java, "config", "OpenApiConfig.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("API Backend Generada")
                        .version("1.0")
                        .description("API RESTful generada automáticamente"))
                .servers(List.of(
                        new Server().url("").description("Servidor Relativo (HTTPS/HTTP)")
                ));
    }
}
''')

    # BaseEntity.java
    with open(os.path.join(src_main_java, "common", "BaseEntity.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.common;

import jakarta.persistence.Column;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Setter
@MappedSuperclass
public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "is_active")
    private Boolean isActive = true;

    @PrePersist
    protected void onCreate() {
        if (id == null) {
            id = UUID.randomUUID();
        }
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (updatedAt == null) {
            updatedAt = LocalDateTime.now();
        }
        if (isActive == null) {
            isActive = true;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
''')

    # ResourceNotFoundException.java
    with open(os.path.join(src_main_java, "exceptions", "ResourceNotFoundException.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.exceptions;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(value = HttpStatus.NOT_FOUND)
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
''')

    # GlobalExceptionHandler.java
    with open(os.path.join(src_main_java, "exceptions", "GlobalExceptionHandler.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.exceptions;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.context.request.WebRequest;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<?> resourceNotFoundException(ResourceNotFoundException ex, WebRequest request) {
        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now());
        errorDetails.put("message", ex.getMessage());
        errorDetails.put("details", request.getDescription(false));
        return new ResponseEntity<>(errorDetails, HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<?> globalExceptionHandler(Exception ex, WebRequest request) {
        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now());
        errorDetails.put("message", ex.getMessage());
        errorDetails.put("details", request.getDescription(false));
        return new ResponseEntity<>(errorDetails, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
''')

    # CorsConfig.java
    with open(os.path.join(src_main_java, "config", "CorsConfig.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }
}
''')

    # OpenApiConfig.java
    with open(os.path.join(src_main_java, "config", "OpenApiConfig.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .servers(List.of(new Server().url("").description("Relative Server")))
                .info(new Info()
                        .title("API Backend Generado")
                        .version("1.0")
                        .description("API REST modular generada automáticamente por IA"));
    }
}
''')

    # BaseService.java
    with open(os.path.join(src_main_java, "common", "BaseService.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.common;

import java.util.List;
import java.util.Optional;

public interface BaseService<T, ID> {
    List<T> findAll();
    Optional<T> findById(ID id);
    T save(T entity);
    void deleteById(ID id);
}
''')

def generar_archivos_java(diagram_json: dict, temp_dir: str):
    """
    Parsea las clases del JSON y genera las entidades, repositorios, 
    servicios y controladores usando Jinja2.
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    
    entity_template = env.get_template("Entity.java.jinja")
    repo_template = env.get_template("Repository.java.jinja")
    service_template = env.get_template("Service.java.jinja")
    controller_template = env.get_template("Controller.java.jinja")
    req_dto_template = env.get_template("RequestDTO.java.jinja")
    res_dto_template = env.get_template("ResponseDTO.java.jinja")
    
    src_main_java = os.path.join(temp_dir, "src", "main", "java", "com", "proyecto")
    
    nodos = diagram_json.get("nodes", [])
    
    for nodo in nodos:
        if nodo.get("type") in ["class", "interface"]:
            nombre_clase = nodo.get("nombre", "EntidadDesconocida")
            nombre_clase = re.sub(r'[^a-zA-Z0-9]', '', nombre_clase)
            nombre_clase = nombre_clase.capitalize() if nombre_clase else "Entidad"

            atributos_sanitizados = []
            for a in nodo.get("atributos", []):
                nuevo_a = dict(a)
                nuevo_nombre = sanitize_identifier(a.get("nombre", ""))
                nuevo_a["nombre"] = nuevo_nombre
                nuevo_a["nombre_capitalizado"] = nuevo_nombre[0].upper() + nuevo_nombre[1:] if nuevo_nombre else ""
                
                if a.get("visibilidad") != "PK":
                    nuevo_a["tipo"] = map_java_type(a.get("tipo", ""))
                else:
                    nuevo_a["tipo"] = "UUID"
                
                nuevo_a["ejemplo_val"] = obtener_ejemplo_atributo_raw(nuevo_nombre, nuevo_a["tipo"])
                atributos_sanitizados.append(nuevo_a)

            metodos_sanitizados = []
            for m in nodo.get("metodos", []):
                m_name = sanitize_identifier(m.get("nombre", ""))
                if m_name.lower() in RESERVED_CRUD_METHODS:
                    continue
                    
                nuevo_m = dict(m)
                nuevo_m["nombre"] = m_name
                tipo_ret = str(m.get("retorno", "void")).strip()
                if tipo_ret.lower() != "void":
                    nuevo_m["retorno"] = map_java_type(tipo_ret)
                else:
                    nuevo_m["retorno"] = "void"
                
                java_decl, call_args, spring_params = parse_java_parameters(str(m.get("parametros", "")), m_name)
                nuevo_m["java_decl"] = java_decl
                nuevo_m["call_args"] = call_args
                nuevo_m["spring_params"] = spring_params
                
                metodos_sanitizados.append(nuevo_m)

            clase_data = {
                "nombre": nombre_clase,
                "atributos": atributos_sanitizados,
                "metodos": metodos_sanitizados
            }
            
            # Entity
            codigo_entity = entity_template.render(clase=clase_data)
            with open(os.path.join(src_main_java, "models", f"{clase_data['nombre']}.java"), "w", encoding="utf-8") as f:
                f.write(codigo_entity)
                
            # Repository
            codigo_repo = repo_template.render(clase=clase_data)
            with open(os.path.join(src_main_java, "repositories", f"{clase_data['nombre']}Repository.java"), "w", encoding="utf-8") as f:
                f.write(codigo_repo)
                
            # Service
            codigo_service = service_template.render(clase=clase_data)
            with open(os.path.join(src_main_java, "services", f"{clase_data['nombre']}Service.java"), "w", encoding="utf-8") as f:
                f.write(codigo_service)
                
            # Controller
            codigo_controller = controller_template.render(clase=clase_data)
            with open(os.path.join(src_main_java, "controllers", f"{clase_data['nombre']}Controller.java"), "w", encoding="utf-8") as f:
                f.write(codigo_controller)

            # DTOs
            codigo_req_dto = req_dto_template.render(clase=clase_data)
            with open(os.path.join(src_main_java, "dtos", f"{clase_data['nombre']}RequestDTO.java"), "w", encoding="utf-8") as f:
                f.write(codigo_req_dto)

            codigo_res_dto = res_dto_template.render(clase=clase_data)
            with open(os.path.join(src_main_java, "dtos", f"{clase_data['nombre']}ResponseDTO.java"), "w", encoding="utf-8") as f:
                f.write(codigo_res_dto)

def generar_documentacion_md(diagram_json: dict, url_base: str, nombre_repo: str, descripcion_proyecto: str = "") -> str:
    """Genera la documentación en formato Markdown detallada con ejemplos prácticos de cURL, JSON y parámetros."""
    nodos = diagram_json.get("nodes", [])
    
    md = f"# Documentación Interactiva de APIs: {nombre_repo.capitalize()}\n\n"
    if descripcion_proyecto:
        md += f"**Propósito del Proyecto:** {descripcion_proyecto}\n\n"
    md += f"Servicio activo y desplegado en: **{url_base}**\n\n"
    md += f"## 📚 Swagger UI (Pruebas Gráficas en Vivo)\n"
    md += f"Puedes ejecutar y probar todas las peticiones interactivamente ingresando a:\n"
    md += f"👉 **[{url_base}/help]({url_base}/help)**\n\n"
    md += "---\n\n"
    md += "## 🚀 Guía Completa de Endpoints y Ejemplos de Petición\n\n"
    
    for nodo in nodos:
        if nodo.get("type") in ["class", "interface"]:
            nombre = sanitize_identifier(nodo.get("nombre", "Entidad")).capitalize()
            ruta = nombre.lower() + "s"
            base_endpoint = f"{url_base}/api/{ruta}"
            
            md += f"### Entidad: `{nombre}`\n"
            md += f"Ruta Base: `{base_endpoint}`\n\n"
            
            atributos = [a for a in nodo.get("atributos", []) if a.get("visibilidad") != "PK"]
            json_example_lines = []
            json_patch_example_lines = []
            
            if atributos:
                for a in atributos:
                    n = sanitize_identifier(a.get("nombre", ""))
                    t = map_java_type(a.get("tipo", ""))
                    ex_val = obtener_ejemplo_atributo_json(n, t)
                    json_example_lines.append(f'  "{n}": {ex_val}')
                
                if len(atributos) > 0:
                    first_attr = sanitize_identifier(atributos[0].get("nombre", ""))
                    first_type = map_java_type(atributos[0].get("tipo", ""))
                    json_patch_example_lines.append(f'  "{first_attr}": {obtener_ejemplo_atributo_json(first_attr, first_type)}')
            
            body_json_full = "{\n" + ",\n".join(json_example_lines) + "\n}" if json_example_lines else "{}"
            body_json_patch = "{\n" + ",\n".join(json_patch_example_lines) + "\n}" if json_patch_example_lines else "{}"
            
            md += "**Estructura de Datos JSON Body para POST/PUT (Petición):**\n```json\n" + body_json_full + "\n```\n\n"
            
            md += "#### 🛠️ Operaciones CRUD Estándar:\n\n"
            
            # GET ALL
            md += f"1. **`GET {base_endpoint}`** — Listar todos los registros\n"
            md += f"   - **Ejemplo `curl`:**\n"
            md += f"     ```bash\n     curl -X GET \"{base_endpoint}\"\n     ```\n\n"
            
            # GET BY ID
            md += f"2. **`GET {base_endpoint}/{{id}}`** — Obtener por UUID\n"
            md += f"   - **Ejemplo `curl`:**\n"
            md += f"     ```bash\n     curl -X GET \"{base_endpoint}/3fa85f64-5717-4562-b3fc-2c963f66afa6\"\n     ```\n\n"
            
            # POST
            md += f"3. **`POST {base_endpoint}`** — Crear nuevo registro\n"
            md += f"   - **Header:** `Content-Type: application/json`\n"
            md += f"   - **Ejemplo `curl`:**\n"
            md += f"     ```bash\n     curl -X POST \"{base_endpoint}\" \\\n       -H \"Content-Type: application/json\" \\\n       -d '{body_json_full}'\n     ```\n\n"
            
            # PUT
            md += f"4. **`PUT {base_endpoint}/{{id}}`** — Actualización completa por UUID\n"
            md += f"   - **Header:** `Content-Type: application/json`\n"
            md += f"   - **Ejemplo `curl`:**\n"
            md += f"     ```bash\n     curl -X PUT \"{base_endpoint}/3fa85f64-5717-4562-b3fc-2c963f66afa6\" \\\n       -H \"Content-Type: application/json\" \\\n       -d '{body_json_full}'\n     ```\n\n"
            
            # PATCH
            md += f"5. **`PATCH {base_endpoint}/{{id}}`** — Actualización parcial (solo campos enviados)\n"
            md += f"   - **Header:** `Content-Type: application/json`\n"
            md += f"   - **Ejemplo `curl`:**\n"
            md += f"     ```bash\n     curl -X PATCH \"{base_endpoint}/3fa85f64-5717-4562-b3fc-2c963f66afa6\" \\\n       -H \"Content-Type: application/json\" \\\n       -d '{body_json_patch}'\n     ```\n\n"
            
            # DELETE
            md += f"6. **`DELETE {base_endpoint}/{{id}}`** — Eliminar registro por UUID\n"
            md += f"   - **Ejemplo `curl`:**\n"
            md += f"     ```bash\n     curl -X DELETE \"{base_endpoint}/3fa85f64-5717-4562-b3fc-2c963f66afa6\"\n     ```\n\n"

            metodos = nodo.get("metodos", [])
            if metodos:
                md += "#### APIs de Lógica de Negocio Personalizadas (Generadas por IA):\n\n"
                for m in metodos:
                    m_name = sanitize_identifier(m.get("nombre", ""))
                    if m_name.lower() in RESERVED_CRUD_METHODS:
                        continue
                    java_decl, call_args, _ = parse_java_parameters(str(m.get("parametros", "")), m_name)
                    ret_type = map_java_type(m.get("retorno", "void")) if str(m.get("retorno", "")).lower() != "void" else "void"
                    
                    query_example = ""
                    if call_args:
                        params_list = [p.strip() for p in call_args.split(",") if p.strip()]
                        query_parts = []
                        for p in params_list:
                            ex = obtener_ejemplo_atributo_raw(p, "String")
                            query_parts.append(f"{p}={ex}")
                        query_example = "?" + "&".join(query_parts)

                    method_endpoint = f"{base_endpoint}/{m_name}"
                    md += f"- **`POST {method_endpoint}`** — Función `{m_name}({java_decl})`\n"
                    md += f"  - **Retorno:** `{ret_type}`\n"
                    if query_example:
                        md += f"  - **Parámetros Query:** `{query_example}`\n"
                    md += f"  - **Ejemplo `curl`:**\n"
                    md += f"    ```bash\n    curl -X POST \"{method_endpoint}{query_example}\"\n    ```\n\n"

            md += "---\n\n"
            
    return md

def parsear_diagrama(diagram_json: dict, temp_dir: str, nombre_repo: str = "proyecto_db", db_password: str = "password", url_base: str = "http://localhost:8080", descripcion_proyecto: str = "") -> str:
    """
    Orquestador del parser. Retorna la documentación en formato MD.
    """
    inicializar_estructura_spring(temp_dir, nombre_repo, db_password)
    generar_archivos_java(diagram_json, temp_dir)
    return generar_documentacion_md(diagram_json, url_base, nombre_repo, descripcion_proyecto)


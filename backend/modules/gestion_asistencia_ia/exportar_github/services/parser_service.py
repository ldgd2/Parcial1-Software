import os
from jinja2 import Environment, FileSystemLoader

def inicializar_estructura_spring(temp_dir: str):
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

    # .env.example
    with open(os.path.join(temp_dir, ".env.example"), "w", encoding="utf-8") as f:
        f.write('''DB_IP=127.0.0.1
DB_PORT=5432
DB_NAME=dbname
DB_USER=postgres
DB_PASSWORD=password
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
spring.jpa.hibernate.ddl-auto=validate
spring.flyway.enabled=true
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

    # BaseEntity.java
    with open(os.path.join(src_main_java, "common", "BaseEntity.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.common;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDateTime;

@Getter
@Setter
@MappedSuperclass
public abstract class BaseEntity {

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "is_active")
    private Boolean isActive = true;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
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

    # OpenApiConfig.java
    with open(os.path.join(src_main_java, "config", "OpenApiConfig.java"), "w", encoding="utf-8") as f:
        f.write('''package com.proyecto.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
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
        # Solo procesamos clases e interfaces (por ahora clases)
        if nodo.get("type") in ["class", "interface"]:
            clase_data = {
                "nombre": nodo.get("nombre", "EntidadDesconocida").replace(" ", ""),
                "atributos": nodo.get("atributos", []),
                "metodos": nodo.get("metodos", [])
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

def parsear_diagrama(diagram_json: dict, temp_dir: str):
    """
    Orquestador del parser.
    """
    inicializar_estructura_spring(temp_dir)
    generar_archivos_java(diagram_json, temp_dir)

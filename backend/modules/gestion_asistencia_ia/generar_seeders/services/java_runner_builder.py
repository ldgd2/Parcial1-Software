def construir_java_runner() -> str:
    """Genera la clase de configuración Spring Boot CommandLineRunner para ejecutar seeders."""
    return """package com.proyecto.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;

import javax.sql.DataSource;

@Configuration
public class DatabaseSeedRunner {

    private static final Logger log = LoggerFactory.getLogger(DatabaseSeedRunner.class);

    @Bean
    public CommandLineRunner initDatabase(DataSource dataSource) {
        return args -> {
            log.info("[DatabaseSeedRunner] Iniciando comprobación de seeders de prueba...");
            try {
                ClassPathResource resource = new ClassPathResource("data.sql");
                if (resource.exists()) {
                    ResourceDatabasePopulator populator = new ResourceDatabasePopulator();
                    populator.addScript(resource);
                    populator.setContinueOnError(true);
                    populator.setIgnoreFailedDrops(true);
                    populator.populate(dataSource.getConnection());
                    log.info("[DatabaseSeedRunner] Carga de seeders de prueba completada con éxito.");
                } else {
                    log.info("[DatabaseSeedRunner] Archivo data.sql no encontrado; omitiendo.");
                }
            } catch (Exception ex) {
                log.warn("[DatabaseSeedRunner] Advertencia al ejecutar seeders: {}", ex.getMessage());
            }
        };
    }
}
"""


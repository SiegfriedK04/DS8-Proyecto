-- ============================================================
-- ESTACIÓN METEOROLÓGICA IOT - ESQUEMA DE BASE DE DATOS
-- Base de datos: PostgreSQL 14+
-- Autor: Sistema IoT
-- Fecha: 2024
-- ============================================================

-- ==================== ELIMINACIÓN DE TABLAS ====================
-- Usar solo si necesitas resetear completamente la BD
-- ¡ADVERTENCIA! Esto borrará TODOS los datos

-- DROP TABLE IF EXISTS statistics CASCADE;
-- DROP TABLE IF EXISTS events CASCADE;
-- DROP TABLE IF EXISTS sensor_readings CASCADE;

-- ==================== TABLA: sensor_readings ====================
-- Almacena todas las lecturas de los sensores
-- Incluye manejo de anomalías (NULL para sensores desconectados)

CREATE TABLE IF NOT EXISTS sensor_readings (
    -- Identificador único autoincremental
    id SERIAL PRIMARY KEY,
    
    -- Timestamp de inserción en la BD (UTC por defecto)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- SENSORES - Permiten NULL para anomalías
    -- Temperatura en grados Celsius (°C)
    temperature REAL,
    
    -- Humedad relativa en porcentaje (%)
    humidity REAL,
    
    -- Luminosidad en porcentaje (0-100%)
    -- NOT NULL porque el LDR siempre funciona
    ldr_percent REAL NOT NULL,
    
    -- Valor raw del ADC (0-65535 para 16-bit)
    -- NOT NULL porque el LDR siempre funciona
    ldr_raw INTEGER NOT NULL,
    
    -- METADATOS
    -- Timestamp del dispositivo (formato "HH:MM")
    estado VARCHAR(20) NOT NULL,
    
    -- Nivel de confort térmico calculado
    -- Valores posibles: "Muy Frío", "Fresco", "Agradable", "Cálido", "Muy Caliente"
    comfort_level VARCHAR(50),
    
    -- Número secuencial de lectura (para análisis temporal)
    reading_number INTEGER,
    
    -- CONSTRAINTS
    CONSTRAINT check_temperature_range CHECK (temperature IS NULL OR (temperature >= -50 AND temperature <= 80)),
    CONSTRAINT check_humidity_range CHECK (humidity IS NULL OR (humidity >= 0 AND humidity <= 100)),
    CONSTRAINT check_ldr_percent_range CHECK (ldr_percent >= 0 AND ldr_percent <= 100),
    CONSTRAINT check_ldr_raw_range CHECK (ldr_raw >= 0 AND ldr_raw <= 65535)
);

-- Comentarios en columnas
COMMENT ON COLUMN sensor_readings.temperature IS 'Temperatura en °C, NULL si sensor desconectado';
COMMENT ON COLUMN sensor_readings.humidity IS 'Humedad relativa %, NULL si sensor desconectado';
COMMENT ON COLUMN sensor_readings.ldr_percent IS 'Luminosidad 0-100%, siempre válido';
COMMENT ON COLUMN sensor_readings.ldr_raw IS 'Valor ADC raw 0-65535, siempre válido';
COMMENT ON COLUMN sensor_readings.estado IS 'Timestamp del dispositivo IoT';
COMMENT ON COLUMN sensor_readings.comfort_level IS 'Nivel de confort térmico calculado';
COMMENT ON COLUMN sensor_readings.reading_number IS 'Número secuencial de lectura';

-- ==================== TABLA: events ====================
-- Log de eventos del sistema (conexiones, errores, acciones)

CREATE TABLE IF NOT EXISTS events (
    -- Identificador único autoincremental
    id SERIAL PRIMARY KEY,
    
    -- Timestamp del evento (UTC por defecto)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Tipo de evento (para filtrado rápido)
    -- Ejemplos: SYSTEM, MQTT_BRIDGE, LED, ERROR, WARNING
    event_type VARCHAR(50) NOT NULL,
    
    -- Descripción detallada del evento
    description TEXT NOT NULL,
    
    -- CONSTRAINTS
    CONSTRAINT check_event_type_not_empty CHECK (event_type <> '')
);

-- Comentarios
COMMENT ON COLUMN events.event_type IS 'Categoría del evento para filtrado';
COMMENT ON COLUMN events.description IS 'Descripción completa del evento';

-- ==================== TABLA: statistics ====================
-- Estadísticas agregadas para análisis rápido
-- Generadas periódicamente por el sistema

CREATE TABLE IF NOT EXISTS statistics (
    -- Identificador único autoincremental
    id SERIAL PRIMARY KEY,
    
    -- Timestamp de la agregación (UTC por defecto)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- TEMPERATURA
    temp_avg REAL,      -- Promedio (°C)
    temp_min REAL,      -- Mínimo (°C)
    temp_max REAL,      -- Máximo (°C)
    
    -- HUMEDAD
    hum_avg REAL,       -- Promedio (%)
    hum_min REAL,       -- Mínimo (%)
    hum_max REAL,       -- Máximo (%)
    
    -- LUMINOSIDAD
    ldr_avg REAL,       -- Promedio (%)
    ldr_min REAL,       -- Mínimo (%)
    ldr_max REAL,       -- Máximo (%)
    
    -- METADATOS
    readings_count INTEGER,  -- Cantidad de lecturas en el período
    
    -- CONSTRAINTS
    CONSTRAINT check_stats_temp_range CHECK (
        (temp_avg IS NULL OR (temp_avg >= -50 AND temp_avg <= 80)) AND
        (temp_min IS NULL OR (temp_min >= -50 AND temp_min <= 80)) AND
        (temp_max IS NULL OR (temp_max >= -50 AND temp_max <= 80))
    ),
    CONSTRAINT check_stats_hum_range CHECK (
        (hum_avg IS NULL OR (hum_avg >= 0 AND hum_avg <= 100)) AND
        (hum_min IS NULL OR (hum_min >= 0 AND hum_min <= 100)) AND
        (hum_max IS NULL OR (hum_max >= 0 AND hum_max <= 100))
    ),
    CONSTRAINT check_stats_ldr_range CHECK (
        (ldr_avg IS NULL OR (ldr_avg >= 0 AND ldr_avg <= 100)) AND
        (ldr_min IS NULL OR (ldr_min >= 0 AND ldr_min <= 100)) AND
        (ldr_max IS NULL OR (ldr_max >= 0 AND ldr_max <= 100))
    ),
    CONSTRAINT check_readings_count CHECK (readings_count > 0)
);

-- Comentarios
COMMENT ON TABLE statistics IS 'Estadísticas agregadas para análisis temporal';
COMMENT ON COLUMN statistics.readings_count IS 'Cantidad de lecturas incluidas en el agregado';

-- ==================== ÍNDICES ====================
-- Optimización de queries frecuentes

-- Índice para ordenamiento temporal descendente (lecturas más recientes primero)
CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
ON sensor_readings(timestamp DESC);

-- Índice para filtrado por nivel de confort
CREATE INDEX IF NOT EXISTS idx_sensor_comfort 
ON sensor_readings(comfort_level);

-- Índice para análisis secuencial
CREATE INDEX IF NOT EXISTS idx_sensor_reading_num 
ON sensor_readings(reading_number);

-- Índice compuesto para búsqueda por fecha y confort
CREATE INDEX IF NOT EXISTS idx_sensor_date_comfort 
ON sensor_readings(DATE(timestamp), comfort_level);

-- Índice para eventos recientes
CREATE INDEX IF NOT EXISTS idx_events_timestamp 
ON events(timestamp DESC);

-- Índice para filtrado de eventos por tipo
CREATE INDEX IF NOT EXISTS idx_events_type 
ON events(event_type);

-- Índice para estadísticas por fecha
CREATE INDEX IF NOT EXISTS idx_stats_timestamp 
ON statistics(timestamp DESC);

-- ==================== VISTAS ====================
-- Vistas útiles para análisis de datos

-- Vista: Últimas 100 lecturas con información completa
CREATE OR REPLACE VIEW v_recent_readings AS
SELECT 
    id,
    timestamp AT TIME ZONE 'UTC' as timestamp_utc,
    temperature,
    humidity,
    ldr_percent,
    ldr_raw,
    estado,
    comfort_level,
    reading_number,
    CASE 
        WHEN temperature IS NULL THEN 'Anomalía Temperatura'
        WHEN humidity IS NULL THEN 'Anomalía Humedad'
        ELSE 'OK'
    END as sensor_status
FROM sensor_readings
ORDER BY timestamp DESC
LIMIT 100;

-- Vista: Resumen diario de lecturas
CREATE OR REPLACE VIEW v_daily_summary AS
SELECT 
    DATE(timestamp) as fecha,
    COUNT(*) as total_lecturas,
    COUNT(*) FILTER (WHERE temperature IS NOT NULL) as lecturas_temp_ok,
    COUNT(*) FILTER (WHERE temperature IS NULL) as anomalias_temp,
    COUNT(*) FILTER (WHERE humidity IS NOT NULL) as lecturas_hum_ok,
    COUNT(*) FILTER (WHERE humidity IS NULL) as anomalias_hum,
    ROUND(AVG(temperature)::numeric, 2) as temp_promedio,
    ROUND(MIN(temperature)::numeric, 2) as temp_minima,
    ROUND(MAX(temperature)::numeric, 2) as temp_maxima,
    ROUND(AVG(humidity)::numeric, 2) as hum_promedio,
    ROUND(AVG(ldr_percent)::numeric, 2) as luz_promedio
FROM sensor_readings
GROUP BY DATE(timestamp)
ORDER BY DATE(timestamp) DESC;

-- Vista: Distribución de confort térmico
CREATE OR REPLACE VIEW v_comfort_distribution AS
SELECT 
    comfort_level,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM sensor_readings
WHERE comfort_level IS NOT NULL
GROUP BY comfort_level
ORDER BY cantidad DESC;

-- Vista: Eventos recientes por tipo
CREATE OR REPLACE VIEW v_recent_events AS
SELECT 
    event_type,
    COUNT(*) as cantidad,
    MAX(timestamp) as ultimo_evento
FROM events
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY event_type
ORDER BY ultimo_evento DESC;

-- ==================== FUNCIONES ====================

-- Función: Obtener rango de temperatura del día
CREATE OR REPLACE FUNCTION get_daily_temp_range(fecha DATE DEFAULT CURRENT_DATE)
RETURNS TABLE(
    temp_min REAL,
    temp_max REAL,
    temp_avg REAL,
    lecturas_validas BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        MIN(temperature) as temp_min,
        MAX(temperature) as temp_max,
        AVG(temperature) as temp_avg,
        COUNT(*) FILTER (WHERE temperature IS NOT NULL) as lecturas_validas
    FROM sensor_readings
    WHERE DATE(timestamp) = fecha;
END;
$$ LANGUAGE plpgsql;

-- Función: Detectar anomalías consecutivas
CREATE OR REPLACE FUNCTION detect_consecutive_anomalies(threshold INTEGER DEFAULT 3)
RETURNS TABLE(
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    anomaly_count BIGINT,
    sensor_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH anomaly_sequences AS (
        SELECT 
            timestamp,
            CASE 
                WHEN temperature IS NULL THEN 'temperature'
                WHEN humidity IS NULL THEN 'humidity'
            END as sensor_type,
            reading_number,
            reading_number - ROW_NUMBER() OVER (
                PARTITION BY 
                    CASE 
                        WHEN temperature IS NULL THEN 'temperature'
                        WHEN humidity IS NULL THEN 'humidity'
                    END
                ORDER BY reading_number
            ) as grp
        FROM sensor_readings
        WHERE temperature IS NULL OR humidity IS NULL
    )
    SELECT 
        MIN(timestamp) as start_time,
        MAX(timestamp) as end_time,
        COUNT(*) as anomaly_count,
        sensor_type
    FROM anomaly_sequences
    GROUP BY sensor_type, grp
    HAVING COUNT(*) >= threshold
    ORDER BY start_time DESC;
END;
$$ LANGUAGE plpgsql;

-- ==================== TRIGGERS ====================

-- Trigger: Registrar evento automáticamente al detectar anomalía
CREATE OR REPLACE FUNCTION log_sensor_anomaly()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.temperature IS NULL THEN
        INSERT INTO events (event_type, description)
        VALUES ('ANOMALY', 'Sensor de temperatura desconectado - Lectura #' || NEW.reading_number);
    END IF;
    
    IF NEW.humidity IS NULL THEN
        INSERT INTO events (event_type, description)
        VALUES ('ANOMALY', 'Sensor de humedad desconectado - Lectura #' || NEW.reading_number);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_anomaly
AFTER INSERT ON sensor_readings
FOR EACH ROW
WHEN (NEW.temperature IS NULL OR NEW.humidity IS NULL)
EXECUTE FUNCTION log_sensor_anomaly();

-- ==================== PERMISOS ====================
-- Configuración de permisos para diferentes roles

-- Rol de lectura (solo SELECT)
-- CREATE ROLE iot_reader;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO iot_reader;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO iot_reader;

-- Rol de escritura (INSERT, UPDATE)
-- CREATE ROLE iot_writer;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO iot_writer;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO iot_writer;

-- ==================== MANTENIMIENTO ====================

-- Procedimiento: Limpiar datos antiguos (retención de 90 días)
CREATE OR REPLACE PROCEDURE cleanup_old_data(retention_days INTEGER DEFAULT 90)
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_readings INTEGER;
    deleted_events INTEGER;
    deleted_stats INTEGER;
BEGIN
    -- Borrar lecturas antiguas
    DELETE FROM sensor_readings 
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_readings = ROW_COUNT;
    
    -- Borrar eventos antiguos
    DELETE FROM events 
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_events = ROW_COUNT;
    
    -- Borrar estadísticas antiguas
    DELETE FROM statistics 
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_stats = ROW_COUNT;
    
    -- Log de limpieza
    INSERT INTO events (event_type, description)
    VALUES ('MAINTENANCE', 
            format('Limpieza completada: %s lecturas, %s eventos, %s estadísticas eliminadas',
                   deleted_readings, deleted_events, deleted_stats));
    
    -- Optimizar tablas
    VACUUM ANALYZE sensor_readings;
    VACUUM ANALYZE events;
    VACUUM ANALYZE statistics;
    
    RAISE NOTICE 'Limpieza completada: % lecturas, % eventos, % estadísticas eliminadas',
                 deleted_readings, deleted_events, deleted_stats;
END;
$$;

-- ==================== DATOS DE PRUEBA ====================
-- Insertar datos de ejemplo para testing (comentar en producción)

/*
INSERT INTO sensor_readings (temperature, humidity, ldr_percent, ldr_raw, estado, comfort_level, reading_number)
VALUES 
    (23.5, 55.0, 75.3, 49152, '14:30', 'Agradable', 1),
    (24.2, 58.0, 82.1, 53600, '14:31', 'Agradable', 2),
    (NULL, NULL, 45.0, 29360, '14:32', NULL, 3),  -- Anomalía
    (22.8, 52.0, 68.5, 44728, '14:33', 'Fresco', 4);

INSERT INTO events (event_type, description)
VALUES 
    ('SYSTEM', 'Sistema iniciado'),
    ('MQTT_BRIDGE', 'Conectado a Adafruit IO'),
    ('LED', 'LED encendido desde cloud');

INSERT INTO statistics (temp_avg, temp_min, temp_max, hum_avg, hum_min, hum_max, ldr_avg, ldr_min, ldr_max, readings_count)
VALUES 
    (23.5, 18.5, 28.5, 55.0, 45.0, 65.0, 70.0, 45.0, 95.0, 50);
*/

-- ==================== VERIFICACIÓN ====================
-- Queries para verificar la instalación correcta

-- Verificar tablas creadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verificar índices creados
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- Verificar vistas creadas
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verificar funciones creadas
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
ORDER BY routine_name;

-- ==================== FIN DEL SCRIPT ====================
-- Para aplicar este esquema:
-- 1. Conectar a PostgreSQL: psql $DATABASE_URL
-- 2. Ejecutar: \i database_schema.sql
-- 3. Verificar: SELECT COUNT(*) FROM sensor_readings;
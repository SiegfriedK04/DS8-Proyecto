# 🏗️ Arquitectura del Sistema IoT - Documentación Técnica

## Índice
1. [Visión General](#visión-general)
2. [Capas de la Arquitectura](#capas-de-la-arquitectura)
3. [Patrones de Diseño](#patrones-de-diseño)
4. [Protocolos de Comunicación](#protocolos-de-comunicación)
5. [Flujo de Datos Detallado](#flujo-de-datos-detallado)
6. [Manejo de Errores y Resiliencia](#manejo-de-errores-y-resiliencia)
7. [Escalabilidad](#escalabilidad)
8. [Seguridad](#seguridad)

---

## Visión General

### Tipo de Arquitectura
**Arquitectura IoT de 4 Capas + Bridge**

```
┌─────────────────────────────────────────────────────────┐
│  Capa 5: Persistencia (Railway PostgreSQL)             │
├─────────────────────────────────────────────────────────┤
│  Capa 4: Bridge (mqtt_to_database.py)                  │
├─────────────────────────────────────────────────────────┤
│  Capa 3: Cloud IoT (Adafruit IO MQTT Broker)           │
├─────────────────────────────────────────────────────────┤
│  Capa 2: Edge Computing (MicroPython en ESP32)         │
├─────────────────────────────────────────────────────────┤
│  Capa 1: Sensores y Actuadores (Hardware Wokwi)        │
└─────────────────────────────────────────────────────────┘
```

### Características Principales
- ✅ **Desacoplamiento**: Cada capa es independiente
- ✅ **Pub/Sub Pattern**: Comunicación asíncrona vía MQTT
- ✅ **Tolerancia a Fallos**: Manejo de anomalías y reconexiones
- ✅ **Escalable**: Fácil agregar nuevos sensores/dispositivos
- ✅ **Híbrido**: Combinación de simulación y hardware real

---

## Capas de la Arquitectura

### **Capa 1: Sensores y Actuadores (Hardware Layer)**

#### Componentes Físicos

| Componente | Modelo | Pin | Función | Especificaciones |
|------------|--------|-----|---------|------------------|
| **Microcontrolador** | ESP32 | - | Procesamiento | 240MHz, WiFi, 520KB RAM |
| **Sensor T/H** | DHT22 | GPIO 15 | Temperatura/Humedad | ±0.5°C, ±2%RH |
| **Fotoresistor** | LDR + Divisor | GPIO 26 (ADC) | Luminosidad | 0-65535 (12-bit ADC) |
| **Display** | LCD I2C 16x2 | SDA:4, SCL:5 | Visualización local | I2C 0x27 |
| **LED** | LED estándar | GPIO 14 | Indicador visual | 5V, 20mA |
| **Buzzer** | Buzzer pasivo | GPIO 13 | Notificaciones | PWM 1500-2500Hz |

#### Ciclo de Lectura de Sensores

```python
# Pseudo-código del ciclo
SENSOR_INTERVAL = 10  # segundos

while True:
    if (current_time - last_read) >= SENSOR_INTERVAL:
        # 1. Activar indicadores (LED + Buzzer)
        led.on()
        buzzer.beep(50ms)
        
        # 2. Lectura de sensores
        temp, hum = dht22.read()        # 2-3 segundos
        ldr_raw = adc.read()            # < 1ms
        ldr_pct = (ldr_raw / 65535) * 100
        
        # 3. Filtrado (Media Móvil de 5 muestras)
        ldr_smoothed = moving_average.add(ldr_pct)
        
        # 4. Detección de anomalías
        if temp is None: temp = "ANOMALIA"
        if hum is None: hum = "ANOMALIA"
        
        # 5. Cálculos derivados
        comfort = calculate_comfort(temp, hum)
        luz_desc = describe_light(ldr_pct)
        
        # 6. Actualizar LCD
        lcd.display(f"{luz_desc} {ldr_pct}%", comfort)
        
        led.off()
```

#### Filtro de Media Móvil (LDR)

**Problema**: El LDR es sensible a fluctuaciones de luz ambiente  
**Solución**: Filtro de media móvil de ventana deslizante

```python
class MovingAverage:
    def __init__(self, size=5):
        self.window = []
        self.size = size
    
    def add(self, value):
        self.window.append(value)
        if len(self.window) > self.size:
            self.window.pop(0)
        return sum(self.window) / len(self.window)
```

**Resultado**: Suavizado de ±3% → ±0.5% de variación

---

### **Capa 2: Edge Computing (Software Layer)**

#### Arquitectura de Software MicroPython

```
main.py (Orquestador)
    ├── sensors.py (Abstracción de hardware)
    │   ├── LDR (ADC reading + conversion)
    │   └── DHT22Sensor (Temperature/Humidity)
    │
    ├── actuators.py (Control de salidas)
    │   ├── LED (on/off/blink)
    │   └── Buzzer (beep con PWM)
    │
    ├── lcd_i2c.py (Driver de pantalla)
    │   └── SimpleI2cLcd (control I2C)
    │
    ├── utils.py (Lógica de negocio)
    │   ├── Simulación de 24h
    │   ├── Cálculo de confort térmico
    │   └── Clasificación de luminosidad
    │
    └── mqtt_client.py (Conectividad)
        ├── Conexión WiFi
        ├── Cliente MQTT 3.1.1
        ├── Publicación a feeds
        └── Suscripción a comandos
```

#### Máquina de Estados del Sistema

```
┌─────────────┐
│   INICIO    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ CONECTAR_WIFI   │◄──────────┐
└──────┬──────────┘           │
       │ [éxito]              │
       ▼                      │ [fallo]
┌─────────────────┐           │
│ CONECTAR_MQTT   │───────────┘
└──────┬──────────┘
       │ [éxito]
       ▼
┌─────────────────┐
│  SUSCRIBIR      │
│  FEEDS          │
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────┐
│      LOOP PRINCIPAL         │
│                             │
│  ┌───────────────────────┐  │
│  │ Cada 10s:             │  │
│  │  • Leer sensores      │  │
│  │  • Actualizar LCD     │  │
│  └───────────────────────┘  │
│                             │
│  ┌───────────────────────┐  │
│  │ Cada 20s:             │  │
│  │  • Publicar a MQTT    │  │
│  └───────────────────────┘  │
│                             │
│  ┌───────────────────────┐  │
│  │ Continuo:             │  │
│  │  • Check mensajes     │  │
│  │  • Procesar comandos  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
       │
       ▼
  [Error MQTT]
       │
       └─────► RECONECTAR_MQTT
```

#### Modo Simulación

**Propósito**: Testing rápido de ciclos completos de 24 horas

```python
# Compresión temporal: 24h → 5min (288x más rápido)
SIMULATION_SPEEDUP = 288

def obtener_hora_actual():
    if MODO_SIMULACION:
        elapsed = (utime.ticks_ms() - start_time) / 1000
        sim_seconds = elapsed * SIMULATION_SPEEDUP
        hour = int((sim_seconds / 3600) % 24)
        minute = int((sim_seconds % 3600) / 60)
        return f"{hour:02d}:{minute:02d}"
    else:
        return time.strftime("%H:%M")
```

**Simulaciones Incluidas**:
1. **Temperatura**: 18°C (noche) → 32°C (mediodía) → 20°C (tarde)
2. **Humedad**: 75% (noche) → 45% (mediodía) → 60% (tarde)
3. **Luminosidad**: 5% (noche) → 95% (mediodía) → 30% (tarde)

---

### **Capa 3: Cloud IoT Platform (MQTT Broker)**

#### Adafruit IO - Características Técnicas

| Característica | Especificación | Límite Gratuito |
|----------------|----------------|-----------------|
| **Protocolo** | MQTT 3.1.1 | - |
| **Puerto** | 1883 (sin TLS) | - |
| **QoS** | 0 (At most once) | - |
| **Mensajes/min** | Configurable | 30 msg/min |
| **Feeds** | Ilimitados | 10 feeds activos |
| **Retención** | 30 días | Todas las cuentas |
| **API REST** | Sí | 120 req/min |

#### Estructura de Topics MQTT

**Formato**: `{username}/feeds/{feed_name}`

**Ejemplo de Publicación**:
```
Topic:   "_Sieg_/feeds/sensor_temp"
Payload: "23.5"
QoS:     0
Retain:  false
```

**Ejemplo de Suscripción**:
```
Topic:   "_Sieg_/feeds/comando_led"
Payload: "ON"
```

#### Dashboard - Componentes Visuales

| Bloque | Tipo | Feed | Configuración |
|--------|------|------|---------------|
| Temperatura | Gauge | sensor_temp | Min: 0, Max: 50, Unidad: °C |
| Humedad | Gauge | sensor_hum | Min: 0, Max: 100, Unidad: % |
| Luminosidad | Gauge | sensor_ldr_pct | Min: 0, Max: 100, Unidad: % |
| Histórico Temp | Line Chart | sensor_temp | Últimas 24h |
| Confort | Text Block | sensor_comfort | Auto-size |
| Control LED | Toggle | comando_led | ON/OFF |
| Timestamp | Text Block | sensor_estado | Fuente monospace |

---

### **Capa 4: Bridge MQTT→PostgreSQL**

#### Arquitectura del Bridge

```python
┌──────────────────────────────────────┐
│     MQTT Client (Paho-MQTT)          │
│  • Suscripción a 8 feeds             │
│  • Callback por mensaje              │
│  • Reconexión automática             │
└───────────────┬──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│         Buffer de Datos              │
│  {                                   │
│    temperature: float | "ANOMALIA"   │
│    humidity: float | "ANOMALIA"      │
│    ldr_percent: float                │
│    ldr_raw: int                      │
│    estado: string                    │
│    comfort: string                   │
│    last_update: timestamp            │
│  }                                   │
└───────────────┬──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│      Parser & Validator              │
│  • Conversión de tipos               │
│  • Manejo "ANOMALIA" → NULL          │
│  • Validación de rangos              │
└───────────────┬──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│      PostgreSQL Connection           │
│  • psycopg2 con connection pooling   │
│  • Transacciones ACID                │
│  • Auto-commit                       │
└──────────────────────────────────────┘
```

#### Lógica de Buffer

**Problema**: Los mensajes MQTT llegan desordenados  
**Solución**: Buffer de acumulación con trigger en `estado`

```python
# Estado inicial
buffer = {temp: None, hum: None, ldr_pct: None, ...}

# Mensajes MQTT llegan en orden aleatorio
on_message("sensor_temp", "23.5")     → buffer.temp = 23.5
on_message("sensor_ldr_pct", "75.3")  → buffer.ldr_pct = 75.3
on_message("sensor_hum", "55.0")      → buffer.hum = 55.0
on_message("sensor_estado", "14:30")  → buffer.estado = "14:30"
                                        ↓
                                    TRIGGER: flush_to_db()
```

**Timeout**: Si no llega `estado` en 60s, se guardan datos parciales

#### Manejo de Anomalías

**Flujo Completo**:
```
ESP32: temp = None
  ↓
main.py: temp = "ANOMALIA"
  ↓
MQTT Publish: payload = "ANOMALIA"
  ↓
Adafruit IO: Feed muestra "ANOMALIA"
  ↓
mqtt_to_database.py: if value == "ANOMALIA": temp = None
  ↓
PostgreSQL: INSERT temperature = NULL
```

**Ventajas**:
- ✅ Queries SQL estándar funcionan (NULL es nativo)
- ✅ Fácil identificar lecturas fallidas
- ✅ No rompe tipos de datos (float vs string)
- ✅ Dashboard muestra claramente el error

---

### **Capa 5: Persistencia (Database Layer)**

#### Esquema de Base de Datos

**Diagrama ER**:
```
┌─────────────────────┐
│  sensor_readings    │
├─────────────────────┤
│ id (PK)             │───┐
│ timestamp           │   │
│ temperature (NULL?) │   │
│ humidity (NULL?)    │   │
│ ldr_percent         │   │
│ ldr_raw             │   │
│ estado              │   │
│ comfort_level       │   │
│ reading_number      │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│      events         │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ timestamp           │   │
│ event_type          │   │
│ description         │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│    statistics       │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ timestamp           │   │
│ temp_avg/min/max    │   │
│ hum_avg/min/max     │   │
│ ldr_avg/min/max     │   │
│ readings_count      │───┘
└─────────────────────┘
```

#### Índices para Optimización

```sql
-- Búsqueda temporal rápida
CREATE INDEX idx_sensor_timestamp ON sensor_readings(timestamp DESC);

-- Filtrado por confort
CREATE INDEX idx_sensor_comfort ON sensor_readings(comfort_level);

-- Análisis secuencial
CREATE INDEX idx_sensor_reading_num ON sensor_readings(reading_number);

-- Eventos recientes
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);

-- Estadísticas por fecha
CREATE INDEX idx_stats_timestamp ON statistics(timestamp DESC);
```

#### Estrategia de Auto-Migración

```python
def run_migration():
    """
    Migraciones sin downtime:
    1. Detectar columnas existentes
    2. Agregar solo lo faltante (ALTER TABLE)
    3. Crear índices si no existen
    4. Backfill de datos (UPDATE)
    """
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='sensor_readings'
    """)
    existing = [row[0] for row in cursor.fetchall()]
    
    if 'comfort_level' not in existing:
        cursor.execute("""
            ALTER TABLE sensor_readings 
            ADD COLUMN comfort_level VARCHAR(50)
        """)
```

---

## Patrones de Diseño

### 1. **Publisher-Subscriber (Pub/Sub)**

**Implementación**: MQTT como message bus

```
Publishers (ESP32):
  - Publican a topics específicos
  - No conocen a los suscriptores
  - Comunicación asíncrona

Broker (Adafruit IO):
  - Enruta mensajes
  - Mantiene topics
  - Maneja QoS

Subscribers (Bridge + Dashboard):
  - Escuchan topics de interés
  - No conocen a los publicadores
  - Procesamiento independiente
```

**Ventajas**:
- ✅ Desacoplamiento total
- ✅ Escalabilidad (agregar suscriptores sin modificar ESP32)
- ✅ Tolerancia a fallos (si un suscriptor cae, otros siguen)

### 2. **Repository Pattern**

**Implementación**: Abstracción de acceso a datos

```python
# En mqtt_to_database.py

def save_sensor_reading(temp, hum, ldr, ...):
    """
    Repository para sensor_readings
    Encapsula toda la lógica de persistencia
    """
    conn = get_db_connection()
    cursor.execute("""
        INSERT INTO sensor_readings (...) VALUES (...)
    """)
    conn.commit()
```

**Ventajas**:
- ✅ Cambiar BD sin modificar lógica de negocio
- ✅ Testing fácil (mock del repository)
- ✅ Queries centralizadas

### 3. **Singleton**

**Implementación**: Conexión MQTT única

```python
# En main.py
mqtt = AdafruitMQTT(...)  # Instancia única global

# Uso en todo el código
mqtt.publish(...)
mqtt.check_messages()
```

### 4. **Observer Pattern**

**Implementación**: Callbacks de MQTT

```python
def on_cloud_message(feed_name, value):
    """Observer que reacciona a mensajes entrantes"""
    if feed_name == FEED_LED_COMMAND:
        if value == "ON":
            led.on()
        elif value == "OFF":
            led.off()

mqtt.set_message_callback(on_cloud_message)
```

---

## Protocolos de Comunicación

### MQTT 3.1.1

**Características Usadas**:

1. **CONNECT Packet**:
```
Fixed Header: 0x10
Variable Header:
  - Protocol Name: "MQTT"
  - Protocol Level: 0x04
  - Flags: 0xC2 (username + password + clean session)
  - Keep Alive: 60s
Payload:
  - Client ID: "wokwi-XXXX"
  - Username: "tu_usuario"
  - Password: "aio_KEY"
```

2. **PUBLISH Packet (QoS 0)**:
```
Fixed Header: 0x30 (PUBLISH, QoS0, no retain)
Variable Header:
  - Topic Length: 2 bytes
  - Topic: "username/feeds/sensor_temp"
Payload:
  - Value: "23.5"
```

3. **SUBSCRIBE Packet**:
```
Fixed Header: 0x82 (SUBSCRIBE, QoS1)
Variable Header:
  - Message ID: 0x0001
Payload:
  - Topic: "username/feeds/comando_led"
  - QoS: 0x00
```

### I2C (LCD)

**Configuración**:
- Velocidad: 100 kHz (modo estándar)
- Dirección: 0x27 (típica para LCD I2C)
- Pull-ups: Resistencias de 4.7kΩ

**Secuencia de Escritura**:
```
START → ADDRESS(0x27) + W → ACK →
DATA_HIGH → ACK →
DATA_LOW → ACK →
STOP
```

### ADC (LDR)

**Configuración**:
- Resolución: 12 bits (0-4095)
- Atenuación: 11dB (rango 0-3.3V)
- Muestreo: ~1kHz

**Conversión**:
```python
raw = adc.read()            # 0-65535 (over-sampled)
voltage = raw * 3.3 / 65535
percent = (raw / 65535) * 100
```

---

## Flujo de Datos Detallado

### Lectura Completa (End-to-End)

```
[T=0s] ESP32 activa sensores
  ↓ 50ms
[T=50ms] LED ON + Buzzer BEEP
  ↓ 2-3s
[T=2s] DHT22 entrega temp=23.5°C, hum=55%
  ↓ 1ms
[T=2.001s] LDR entrega raw=49152 (75.3%)
  ↓ 10ms
[T=2.011s] Filtro media móvil: 75.3% → 75.1%
  ↓ 5ms
[T=2.016s] Cálculo confort: "Agradable"
  ↓ 50ms
[T=2.066s] Actualización LCD
  ↓ 200ms
[T=2.266s] LED OFF
  ↓ 17.734s (espera hasta completar 20s)
[T=20s] Publicación MQTT:
  • sensor_temp: "23.5"          (100ms)
  • sensor_hum: "55.0"           (100ms)
  • sensor_ldr_pct: "75.1"       (100ms)
  • sensor_ldr_raw: "49152"      (100ms)
  • sensor_estado: "14:30"       (100ms)
  • sensor_comfort: "Agradable"  (100ms)
  ↓ Network latency ~200ms
[T=20.6s] Adafruit IO recibe mensajes
  ↓ 10ms
[T=20.61s] Dashboard actualiza gauges
  ↓ Parallel processing
[T=20.61s] mqtt_to_database recibe via suscripción
  ↓ 50ms (buffer accumulation)
[T=20.66s] Buffer completo, trigger flush
  ↓ 100ms (INSERT query)
[T=20.76s] PostgreSQL confirma escritura
  ↓
[T=20.76s] Lectura completada ✅
```

**Latencia Total**: ~20.76 segundos desde inicio de lectura hasta BD

---

## Manejo de Errores y Resiliencia

### Estrategias Implementadas

#### 1. **WiFi Disconnection**
```python
if not wlan.isconnected():
    print("WiFi perdido, reconectando...")
    wlan.connect(SSID, PASSWORD)
    # Timeout de 15s
    wait_with_timeout(15)
```

#### 2. **MQTT Disconnection**
```python
def check_messages():
    try:
        if not mqtt.sock:
            return False  # Señal para reconectar
        # ... procesar mensajes
    except OSError:
        return False  # Error de socket

# En main loop
if not mqtt.check_messages():
    mqtt_connected = False
    connect_mqtt()  # Reintento
```

#### 3. **Sensor Failure**
```python
temp, hum = dht.read()
if temp is None:
    temp = "ANOMALIA"  # Marcador especial
    # Sistema continúa funcionando
    # LDR y otros sensores siguen operativos
```

#### 4. **Database Unavailable**
```python
def save_sensor_reading(...):
    try:
        conn = get_db_connection()
        # ... INSERT
    except Exception as e:
        print(f"BD no disponible: {e}")
        # Datos se pierden, pero bridge sigue ejecutando
        # Próxima lectura intentará de nuevo
```

#### 5. **Buffer Timeout**
```python
if time.time() - buffer['last_update'] > 60:
    # Han pasado 60s sin completar lectura
    save_sensor_reading(
        buffer['temp'],
        buffer['hum'] or "N/A",  # Valor parcial
        buffer['ldr_pct'] or 0,
        # ...
    )
```

### Matriz de Fallos

| Fallo | Detección | Recuperación | Pérdida de Datos |
|-------|-----------|--------------|------------------|
| WiFi desconectado | `wlan.isconnected()` | Reconexión automática 15s | ✅ No (buffer local) |
| MQTT desconectado | `check_messages()` retorna False | Reconexión automática 2s | ❌ Sí (últimos 20s) |
| Sensor DHT22 falla | `temp is None` | Marcador "ANOMALIA" | ⚠️ Parcial (solo T/H) |
| BD no disponible | Exception en `psycopg2.connect()` | Reintento en próxima lectura | ❌ Sí (lectura actual) |
| Adafruit IO caído | Timeout en CONNECT | Reintentos cada 5s | ❌ Sí (durante downtime) |

---

## Escalabilidad

### Agregar Nuevos Sensores

**Pasos**:
1. **Hardware**: Conectar sensor a ESP32
2. **Driver**: Crear clase en `sensors.py`
3. **Lectura**: Integrar en `read_sensors()` de `main.py`
4. **Feed**: Crear en Adafruit IO
5. **Publicación**: Agregar en `publish_all_sensors()`
6. **BD**: Migración para nueva columna
7. **Bridge**: Agregar parsing en `on_message()`

**Ejemplo - Agregar sensor de presión barométrica**:

```python
# 1. En sensors.py
class BMP280:
    def read_pressure(self):
        return self.i2c.read_register(0xF7)

# 2. En main.py
bmp = BMP280(i2c=i2c)
pressure = bmp.read_pressure()

# 3. Nueva constante
FEED_PRESSURE = "sensor_pressure"

# 4. Publicar
mqtt.publish(FEED_PRESSURE, pressure)

# 5. En BD
ALTER TABLE sensor_readings ADD COLUMN pressure REAL;
```

### Múltiples Dispositivos

**Estrategia**: Client ID único por dispositivo

```python
# Dispositivo 1
client_id = "estacion_001"
FEED_TEMP = "estacion_001_temp"

# Dispositivo 2
client_id = "estacion_002"
FEED_TEMP = "estacion_002_temp"

# Dashboard puede mostrar ambos en gráfica comparativa
```

### Optimización de Tráfico MQTT

**Técnicas**:
1. **Compresión**: JSON → MessagePack (reducción ~30%)
2. **Batching**: Agrupar 3 lecturas en 1 mensaje
3. **QoS**: Usar QoS 1 solo para comandos críticos
4. **Retained**: Activar solo en `estado` para última lectura

**Antes** (6 mensajes):
```
sensor_temp: "23.5"
sensor_hum: "55.0"
sensor_ldr_pct: "75.1"
sensor_ldr_raw: "49152"
sensor_estado: "14:30"
sensor_comfort: "Agradable"
```

**Después** (1 mensaje JSON):
```json
{
  "t": 23.5,
  "h": 55.0,
  "ldr": {"pct": 75.1, "raw": 49152},
  "ts": "14:30",
  "comfort": "Agradable"
}
```

---

## Seguridad

### Amenazas Identificadas

| Amenaza | Severidad | Mitigación Actual | Mejora Sugerida |
|---------|-----------|-------------------|-----------------|
| Clave MQTT hardcoded | 🔴 Alta | Ninguna | Variables de entorno |
| Sin encriptación (puerto 1883) | 🟡 Media | Limitado a LAN/sim | TLS (puerto 8883) |
| SQL Injection | 🟢 Baja | Prepared statements | ✅ Implementado |
| Fuerza bruta API | 🟡 Media | Rate limiting de Adafruit | API key rotación |
| BD sin autenticación | 🔴 Alta | Ninguna | Railway auth activada |

### Recomendaciones de Producción

#### 1. **Gestión de Secretos**
```bash
# .env (NO subir a Git)
ADAFRUIT_USERNAME=usuario
ADAFRUIT_KEY=aio_XXXX
DATABASE_URL=postgresql://...

# main.py lee de archivo config
with open('config.json') as f:
    config = json.load(f)
    ADAFRUIT_KEY = config['mqtt_key']
```

#### 2. **MQTT con TLS**
```python
# Cambiar puerto
ADAFRUIT_PORT = 8883

# Agregar contexto SSL
import ssl
ssl_context = ssl.create_default_context()
client.tls_set_context(ssl_context)
```

####
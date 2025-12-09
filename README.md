# 🌦️ Estación Meteorológica IoT - Sistema de Monitoreo Ambiental

Sistema IoT completo de monitoreo ambiental con sensores virtuales (Wokwi), transmisión MQTT en tiempo real (Adafruit IO) y almacenamiento persistente (Railway PostgreSQL).

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![MicroPython](https://img.shields.io/badge/MicroPython-ESP32-green.svg)](https://micropython.org/)
[![MQTT](https://img.shields.io/badge/MQTT-Adafruit%20IO-orange.svg)](https://io.adafruit.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://www.postgresql.org/)

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Componentes](#️-componentes)
- [Flujo de Datos](#-flujo-de-datos)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [Estructura de la Base de Datos](#️-estructura-de-la-base-de-datos)
- [Feeds MQTT](#-feeds-mqtt)
- [Troubleshooting](#-troubleshooting)

---

## 🌟 Descripción General

Este proyecto implementa una estación meteorológica completa que:

- ✅ **Monitorea** temperatura, humedad y luminosidad en tiempo real
- ✅ **Calcula** métricas de confort térmico y condiciones de iluminación
- ✅ **Transmite** datos vía MQTT a la nube (Adafruit IO)
- ✅ **Visualiza** datos en dashboards web interactivos
- ✅ **Almacena** historial completo en PostgreSQL
- ✅ **Detecta** anomalías y sensores desconectados
- ✅ **Permite** control remoto de actuadores (LED/Buzzer)

### Modos de Operación

1. **Modo Real**: Lecturas de sensores físicos cada 10 segundos
2. **Modo Simulación**: Ciclo completo de 24 horas comprimido en 5 minutos (ideal para testing)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   WOKWI ESP32   │  MQTT   │  ADAFRUIT IO     │  HTTP   │  RAILWAY        │
│   (Sensores)    │────────>│  (Cloud Broker)  │────────>│  (PostgreSQL)   │
│                 │         │                  │         │                 │
│ • DHT22 (T/H)   │         │ • Feeds MQTT     │         │ • sensor_       │
│ • LDR (Luz)     │         │ • Dashboard      │         │   readings      │
│ • LED/Buzzer    │<────────│ • Control Remoto │         │ • events        │
│ • LCD I2C       │  MQTT   │                  │         │ • statistics    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
       ↑                             ↑                            ↑
       │                             │                            │
   main.py                      Dashboard Web              mqtt_to_database.py
  (MicroPython)                   (Visualización)            (Bridge Python)
```

---

## 🛠️ Componentes

### 1️⃣ **Wokwi - Simulador de Hardware** 
*Ubicación: Plataforma Wokwi*

**Archivos:**
- `main.py` - Script principal MicroPython
- `sensors.py` - Drivers de sensores (DHT22, LDR)
- `actuators.py` - Control de actuadores (LED, Buzzer)
- `lcd_i2c.py` - Driver para pantalla LCD I2C
- `utils.py` - Utilidades (simulación, cálculos)
- `mqtt_client.py` - Cliente MQTT ligero para ESP32
- `diagram.json` - Configuración del circuito Wokwi

**Hardware Virtual:**
- **ESP32** - Microcontrolador principal
- **DHT22** - Sensor temperatura/humedad (GPIO 15)
- **LDR** - Fotoresistor + divisor de voltaje (ADC GPIO 26)
- **LCD I2C** - Pantalla 16x2 (I2C: SDA=GPIO4, SCL=GPIO5)
- **LED** - Indicador visual (GPIO 14)
- **Buzzer** - Notificaciones sonoras (GPIO 13)

### 2️⃣ **Adafruit IO - Cloud MQTT Broker**
*Ubicación: io.adafruit.com*

**Funcionalidad:**
- Recibe datos de sensores en tiempo real
- Dashboard interactivo con gauges y gráficos
- Control remoto del LED via feed `comando_led`
- API REST para análisis de datos

### 3️⃣ **GitHub Repository - Bridge MQTT→PostgreSQL**
*Ubicación: Repository GitHub*

**Archivos:**
- `mqtt_to_database.py` - Script principal del bridge
- `requirements.txt` - Dependencias Python
- `runtime.txt` - Versión de Python (3.11.x)

**Funcionalidad:**
- Escucha feeds MQTT de Adafruit IO
- Parsea y valida datos entrantes
- Almacena en PostgreSQL con manejo de anomalías
- Auto-migración de esquema de BD

### 4️⃣ **Railway - Base de Datos PostgreSQL**
*Ubicación: Railway.app*

**Tablas:**
- `sensor_readings` - Historial de lecturas
- `events` - Log de eventos del sistema
- `statistics` - Métricas agregadas

---

## 🔄 Flujo de Datos

### Ciclo Completo de una Lectura

```
┌──────────┐
│  INICIO  │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 1. WOKWI lee sensores (cada 10s)    │
│    • DHT22 → Temperatura/Humedad    │
│    • LDR → Luminosidad              │
│    • Aplica filtro de media móvil   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 2. Cálculo de métricas derivadas    │
│    • Confort térmico                │
│    • Descripción de luminosidad     │
│    • Detección de anomalías         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 3. Publicación MQTT (cada 20s)      │
│    → Adafruit IO                    │
│    • sensor_temp                    │
│    • sensor_hum                     │
│    • sensor_ldr_pct                 │
│    • sensor_comfort                 │
│    • sensor_estado (timestamp)      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 4. Visualización en Dashboard       │
│    • Gauges de temperatura/humedad  │
│    • Gráfico histórico              │
│    • Texto de confort térmico       │
│    • Timestamp actualizado          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 5. Bridge MQTT escucha feeds        │
│    (mqtt_to_database.py)            │
│    • Acumula datos en buffer        │
│    • Espera conjunto completo       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 6. Guardado en PostgreSQL           │
│    Railway                          │
│    • INSERT en sensor_readings      │
│    • Manejo de NULL para anomalías  │
│    • Timestamp de server            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 7. Dashboard actualiza estadísticas │
│    • Últimas 5 lecturas             │
│    • Distribución de confort        │
│    • Conteo de anomalías            │
└─────────────────────────────────────┘
```

### Control Remoto (Flujo Inverso)

```
Usuario → Adafruit IO Dashboard → Feed "comando_led" → MQTT → 
Wokwi ESP32 → LED ON/OFF + Buzzer + Evento en BD
```

---

## 📦 Requisitos Previos

### Para Wokwi (Simulador)
- Cuenta gratuita en [Wokwi.com](https://wokwi.com)
- Navegador moderno (Chrome/Firefox/Edge)

### Para Adafruit IO
- Cuenta gratuita en [io.adafruit.com](https://io.adafruit.com)
- API Key (disponible en tu perfil)

### Para Railway (Base de Datos)
- Cuenta en [Railway.app](https://railway.app)
- Proyecto con PostgreSQL provisionado

### Para el Bridge (Ejecución Local o Cloud)
- **Python 3.11+**
- **pip** (gestor de paquetes)
- Git (opcional, para clonar el repo)

---

## 🚀 Instalación

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/estacion-meteorologica-iot.git
cd estacion-meteorologica-iot
```

### Paso 2: Crear Entorno Virtual

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Contenido de `requirements.txt`:**
```
paho-mqtt==1.6.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

---

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Credenciales Adafruit IO
ADAFRUIT_USERNAME=tu_usuario
ADAFRUIT_KEY=aio_XXXXXXXXXXXX

# URL de PostgreSQL Railway
DATABASE_URL=postgresql://usuario:password@host:puerto/database
```

### 2. Configurar Wokwi

1. Abre el proyecto en Wokwi
2. Edita `main.py` con tus credenciales:

```python
### CREDENCIALES ADAFRUIT IO ###
ADAFRUIT_USERNAME = "tu_usuario"
ADAFRUIT_KEY = "aio_XXXXXXXXXXXX"
```

3. Activa/desactiva modo simulación en `utils.py`:

```python
# Modo simulación: 24h en 5 minutos
MODO_SIMULACION = True  # False para sensores reales
```

### 3. Crear Feeds en Adafruit IO

Ve a `Feeds` y crea los siguientes feeds:

| Feed Name | Descripción |
|-----------|-------------|
| `sensor_temp` | Temperatura (°C) |
| `sensor_hum` | Humedad (%) |
| `sensor_ldr_pct` | Luminosidad (%) |
| `sensor_ldr_raw` | Valor ADC raw |
| `sensor_estado` | Timestamp |
| `sensor_comfort` | Nivel de confort |
| `comando_led` | Control remoto LED |
| `system_event` | Log de eventos |

### 4. Configurar Dashboard en Adafruit IO

Crea un dashboard con estos bloques:

- **Gauge** para temperatura (0-50°C)
- **Gauge** para humedad (0-100%)
- **Gauge** para luminosidad (0-100%)
- **Line Chart** para histórico de temperatura
- **Text Block** para confort térmico
- **Toggle Button** para `comando_led`

---

## 🎯 Uso

### Ejecutar Simulador Wokwi

1. Abre el proyecto en Wokwi
2. Presiona el botón verde **"Start Simulation"**
3. Observa la consola y el LCD:

```
==================================================
   Sistema IoT - MODO SIMULACIÓN (24h→5min)
==================================================
[LCD] Inicializado
[Sensores] Inicializados
[WiFi] ✓ Conectado. IP: 192.168.1.100
[MQTT] ✓ Conectado a Adafruit IO
[Sistema] Iniciando bucle principal...

[SIM] LDR:15.2% (Muy Oscuro) | T:18.5°C H:65.0% (Fresco) | 00:30
[MQTT] ✓ Datos publicados #1
```

### Ejecutar Bridge MQTT→PostgreSQL

```bash
python mqtt_to_database.py
```

Salida esperada:

```
============================================================
   🚀 MQTT to PostgreSQL Bridge V3
   Con manejo inteligente de anomalías
============================================================

[1] Inicializando base de datos con auto-migración...
🔧 Ejecutando auto-migración de base de datos...
   ✓ Columna 'comfort_level' ya existe
   ✓ Columna 'reading_number' ya existe
✅ Base de datos ya está actualizada

[2] Configurando cliente MQTT...
[3] Conectando a Adafruit IO...
✅ Conectado a Adafruit IO
   📡 Suscrito a: sensor_temp
   📡 Suscrito a: sensor_hum
   📡 Suscrito a: sensor_ldr_pct
   ...

📥 MQTT → sensor_temp: 23.5
📥 MQTT → sensor_hum: 55.0
📥 MQTT → sensor_ldr_pct: 75.3
✅ Lectura #15 guardada (ID:152) - T:23.5°C H:55.0% LDR:75.3% 14:30 [Agradable]
```

### Control Remoto

Desde el dashboard de Adafruit IO:

1. Activa el **Toggle Button** del feed `comando_led`
2. El LED en Wokwi se enciende
3. Se emite un beep en el buzzer
4. Se registra el evento en la BD

---

## 🗄️ Estructura de la Base de Datos

### Tabla: `sensor_readings`

```sql
CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,              -- NULL si ANOMALIA
    humidity REAL,                 -- NULL si ANOMALIA
    ldr_percent REAL NOT NULL,     -- Siempre válido
    ldr_raw INTEGER NOT NULL,      -- Siempre válido
    estado VARCHAR(20) NOT NULL,   -- Timestamp del dispositivo
    comfort_level VARCHAR(50),     -- Nivel de confort calculado
    reading_number INTEGER         -- Número secuencial
);
```

**Ejemplo de datos:**

| id | timestamp | temperature | humidity | ldr_percent | comfort_level | reading_number |
|----|-----------|-------------|----------|-------------|---------------|----------------|
| 1 | 2024-12-09 14:30:00 | 23.5 | 55.0 | 75.3 | Agradable | 1 |
| 2 | 2024-12-09 14:30:20 | NULL | NULL | 80.2 | NULL | 2 |
| 3 | 2024-12-09 14:30:40 | 24.1 | 58.0 | 82.5 | Cálido | 3 |

### Tabla: `events`

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL
);
```

**Tipos de eventos:**
- `SYSTEM` - Inicio/detención del sistema
- `MQTT_BRIDGE` - Conexión/desconexión del bridge
- `LED` - Acciones del LED
- `ERROR` - Errores capturados

### Tabla: `statistics`

```sql
CREATE TABLE statistics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temp_avg REAL,
    temp_min REAL,
    temp_max REAL,
    hum_avg REAL,
    hum_min REAL,
    hum_max REAL,
    ldr_avg REAL,
    ldr_min REAL,
    ldr_max REAL,
    readings_count INTEGER
);
```

---

## 📡 Feeds MQTT

### Publicación (Wokwi → Adafruit IO)

| Feed | Tipo | Ejemplo | Frecuencia |
|------|------|---------|------------|
| `sensor_temp` | float/string | `23.5` o `ANOMALIA` | 20s |
| `sensor_hum` | float/string | `55.0` o `ANOMALIA` | 20s |
| `sensor_ldr_pct` | float | `75.3` | 20s |
| `sensor_ldr_raw` | int | `49152` | 20s |
| `sensor_estado` | string | `14:30` | 20s |
| `sensor_comfort` | string | `Agradable` | 20s |
| `system_event` | string | `SYSTEM:Conectado` | On event |

### Suscripción (Adafruit IO → Wokwi)

| Feed | Valores | Acción |
|------|---------|--------|
| `comando_led` | `ON` / `OFF` / `1` / `0` | Controla LED + Buzzer |

---

## 🔍 Manejo de Anomalías

El sistema detecta y registra fallos de sensores:

### Detección
```python
# En main.py
temp, hum = dht.read()
if temp is None:
    temp = "ANOMALIA"
if hum is None:
    hum = "ANOMALIA"
```

### Transmisión MQTT
```
sensor_temp → "ANOMALIA"
sensor_hum → "ANOMALIA"
```

### Almacenamiento en BD
```python
# En mqtt_to_database.py
if value == "ANOMALIA":
    temperature = None  # Se guarda como NULL en BD
```

### Consulta de Anomalías

```sql
-- Lecturas con temperatura anómala
SELECT * FROM sensor_readings WHERE temperature IS NULL;

-- Conteo de anomalías
SELECT 
    COUNT(*) FILTER (WHERE temperature IS NULL) as temp_anomalias,
    COUNT(*) FILTER (WHERE humidity IS NULL) as hum_anomalias
FROM sensor_readings;
```

---

## 🐛 Troubleshooting

### Problema: Wokwi no conecta a WiFi

**Solución:**
```python
# Verifica credenciales en main.py
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""  # Vacío para Wokwi-GUEST
```

### Problema: Error MQTT "Not authorized"

**Solución:**
- Verifica tu Adafruit IO Key en https://io.adafruit.com/profile
- Asegúrate de copiar la key completa (`aio_XXXX...`)

### Problema: Bridge no guarda datos en BD

**Solución:**
```bash
# Verifica DATABASE_URL
echo $DATABASE_URL

# Prueba conexión manual
psql $DATABASE_URL

# Revisa logs del bridge
python mqtt_to_database.py 2>&1 | tee bridge.log
```

### Problema: Datos "ANOMALIA" frecuentes

**Causas comunes:**
1. DHT22 desconectado en Wokwi
2. Inicialización del sensor muy rápida
3. Alimentación insuficiente

**Solución:**
```python
# En main.py, aumenta tiempo de inicialización
dht = DHT22Sensor(pin=15)
utime.sleep(2)  # Esperar 2s antes de primera lectura
```

### Problema: Dashboard no actualiza

**Verificar:**
1. ✅ Feeds creados con nombres exactos
2. ✅ Bloques vinculados a feeds correctos
3. ✅ Simulador en ejecución
4. ✅ MQTT conectado (ver consola Wokwi)

---

## 📊 Consultas SQL Útiles

### Últimas 10 lecturas
```sql
SELECT * FROM sensor_readings 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Promedio por hora
```sql
SELECT 
    DATE_TRUNC('hour', timestamp) as hora,
    AVG(temperature) as temp_avg,
    AVG(humidity) as hum_avg,
    AVG(ldr_percent) as luz_avg
FROM sensor_readings
WHERE temperature IS NOT NULL
GROUP BY hora
ORDER BY hora DESC;
```

### Distribución de confort
```sql
SELECT comfort_level, COUNT(*) as cantidad
FROM sensor_readings
WHERE comfort_level IS NOT NULL
GROUP BY comfort_level
ORDER BY cantidad DESC;
```

### Rango de temperatura por día
```sql
SELECT 
    DATE(timestamp) as fecha,
    MIN(temperature) as temp_min,
    MAX(temperature) as temp_max,
    AVG(temperature) as temp_avg
FROM sensor_readings
WHERE temperature IS NOT NULL
GROUP BY fecha
ORDER BY fecha DESC;
```

---

## 📝 Notas Adicionales

### Modo Simulación

Ideal para testing rápido:
- ⏱️ 24 horas → 5 minutos
- 🌅 Simula ciclo día/noche completo
- 📈 Genera 180+ lecturas en minutos

```python
# Activar en utils.py
MODO_SIMULACION = True
```

### Optimización de Datos

Para reducir carga en Adafruit IO (límite: 30 msg/min en plan gratuito):

```python
# En main.py
PUBLISH_INTERVAL = 20  # Aumentar a 30s o 60s
```

### Auto-Migración de BD

El bridge detecta y actualiza automáticamente el esquema:
- ✅ Agrega columnas nuevas
- ✅ Crea índices
- ✅ Preserva datos existentes

---

## 🤝 Contribuciones

¡Contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es de código abierto.

---

## 👨‍💻 Autor

**Tu Nombre**  
📧 Grupo 1: Gabriel Rodriguez / Carlos Jaen / Jose Avila / Christian Dutary / Yireikis Abrego
🐙 GitHub: https://github.com/SiegfriedK04

---

## 🙏 Agradecimientos

- [Wokwi](https://wokwi.com) - Simulador de hardware
- [Adafruit IO](https://io.adafruit.com) - Plataforma MQTT
- [Railway](https://railway.app) - Hosting de PostgreSQL

---

**⚡ Happy Monitoring!**

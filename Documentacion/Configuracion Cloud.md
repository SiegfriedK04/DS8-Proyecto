# ☁️ Guía de Configuración de Plataformas Cloud

Esta guía te llevará paso a paso por la configuración de las tres plataformas cloud necesarias para el proyecto:
1. **Wokwi** - Simulador de hardware
2. **Adafruit IO** - Broker MQTT y dashboard
3. **Railway** - Base de datos PostgreSQL

---

## 📋 Prerequisitos

Antes de comenzar, asegúrate de tener:
- ✅ Correo electrónico válido
- ✅ Navegador web moderno (Chrome, Firefox, Edge)
- ✅ Git instalado (opcional)
- ✅ Python 3.11+ instalado (para el bridge)

---

## 🔧 Parte 1: Configuración de Wokwi

### Paso 1.1: Crear Cuenta

1. Ve a [https://wokwi.com](https://wokwi.com)
2. Haz clic en **"Sign In"** → **"Sign up"**
3. Opciones de registro:
   - Con Google
   - Con GitHub
   - Con correo electrónico
4. Confirma tu correo (si usaste email)

### Paso 1.2: Crear Nuevo Proyecto

1. En el dashboard, haz clic en **"New Project"**
2. Selecciona **"ESP32"** como plataforma
3. Nombre del proyecto: `Estacion Meteorologica IoT`

### Paso 1.3: Subir Archivos del Código

#### Opción A: Desde GitHub (Recomendado)

1. En Wokwi, ve a **File** → **Import from GitHub**
2. Pega la URL de tu repositorio
3. Selecciona los archivos:
   - `main.py`
   - `sensors.py`
   - `actuators.py`
   - `lcd_i2c.py`
   - `utils.py`
   - `mqtt_client.py`
   - `diagram.json`

#### Opción B: Manual

1. Haz clic en el **"+"** junto a "Files"
2. Para cada archivo:
   - Selecciona **"New File"**
   - Nombra el archivo (ej: `main.py`)
   - Copia y pega el contenido desde GitHub

### Paso 1.4: Configurar el Circuito

Si no importaste `diagram.json`, configura manualmente:

**Componentes necesarios:**
- 1x ESP32
- 1x DHT22
- 1x LDR (Photoresistor)
- 1x LCD I2C 16x2
- 1x LED
- 1x Buzzer
- 1x Resistencia 10kΩ (para LDR)
- 1x Resistencia 220Ω (para LED)

**Conexiones:**

```
ESP32          →  Componente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO 15        →  DHT22 (Data)
GPIO 26        →  LDR (Señal + divisor de voltaje)
GPIO 4 (SDA)   →  LCD I2C (SDA)
GPIO 5 (SCL)   →  LCD I2C (SCL)
GPIO 14        →  LED (Ánodo + resistencia 220Ω)
GPIO 13        →  Buzzer (+)
GND            →  Todos los componentes (común)
3.3V           →  DHT22, LCD I2C
```

**Diagrama de LDR (divisor de voltaje):**
```
3.3V ──[LDR]──┬──[10kΩ]── GND
              │
              └── GPIO 26 (ADC)
```

### Paso 1.5: Configurar WiFi y MQTT

Edita `main.py` con tus credenciales:

```python
### CONEXIÓN WIFI ###
WIFI_SSID = "Wokwi-GUEST"  # Gratuito en Wokwi
WIFI_PASSWORD = ""          # Sin contraseña

### CREDENCIALES ADAFRUIT IO ###
ADAFRUIT_USERNAME = "tu_usuario"     # ⚠️ Cambiar
ADAFRUIT_KEY = "aio_XXXXXXXXXXXX"    # ⚠️ Cambiar
```

> ⚠️ **IMPORTANTE**: Las credenciales de Adafruit IO las obtendrás en el Paso 2

### Paso 1.6: Modo Simulación (Opcional)

Para testing rápido, activa modo simulación en `utils.py`:

```python
# Línea 10 aproximadamente
MODO_SIMULACION = True  # Cambia a True

# Esto comprime 24 horas en 5 minutos
```

### Paso 1.7: Primera Prueba

1. Haz clic en el botón verde **"Start Simulation"**
2. Observa la consola (debe mostrar):
   ```
   [WiFi] ✓ Conectado. IP: 192.168.1.100
   [MQTT] Conectando al broker...
   ```
3. Si ves errores de MQTT, es normal (aún no configuramos Adafruit IO)

---

## 🌐 Parte 2: Configuración de Adafruit IO

### Paso 2.1: Crear Cuenta

1. Ve a [https://io.adafruit.com](https://io.adafruit.com)
2. Haz clic en **"Get Started for Free"**
3. Completa el formulario de registro
4. Confirma tu correo electrónico

### Paso 2.2: Obtener API Key

1. Inicia sesión en Adafruit IO
2. Haz clic en tu nombre de usuario (esquina superior derecha)
3. Selecciona **"My Key"**
4. Verás dos valores importantes:
   ```
   Username: tu_usuario
   Active Key: aio_XXXXXXXXXXXXXXXX
   ```
5. **Copia estos valores** (los necesitarás en múltiples lugares)

> 🔒 **SEGURIDAD**: Nunca compartas tu API Key públicamente

### Paso 2.3: Crear Feeds

Los feeds son canales de datos. Necesitas crear 8 feeds:

1. Ve a **"Feeds"** en el menú superior
2. Haz clic en **"New Feed"** (botón amarillo)
3. Crea cada feed con estos nombres **EXACTOS**:

| # | Nombre del Feed | Descripción | Notas |
|---|----------------|-------------|-------|
| 1 | `sensor_temp` | Temperatura (°C) | Acepta números y "ANOMALIA" |
| 2 | `sensor_hum` | Humedad (%) | Acepta números y "ANOMALIA" |
| 3 | `sensor_ldr_pct` | Luminosidad (%) | Solo números 0-100 |
| 4 | `sensor_ldr_raw` | Valor ADC raw | Solo números 0-65535 |
| 5 | `sensor_estado` | Timestamp | Formato "HH:MM" |
| 6 | `sensor_comfort` | Nivel de confort | Texto descriptivo |
| 7 | `comando_led` | Control LED | Valores: ON/OFF/1/0 |
| 8 | `system_event` | Eventos del sistema | Formato "TIPO:Descripción" |

**Proceso para cada feed:**
```
New Feed → Name: "sensor_temp" → Description: "Temperatura" → Create
```

### Paso 2.4: Crear Dashboard

1. Ve a **"Dashboards"** en el menú superior
2. Haz clic en **"New Dashboard"**
3. Nombre: `Estación Meteorológica`
4. Descripción: `Monitoreo en tiempo real`
5. Haz clic en **"Create"**

### Paso 2.5: Agregar Bloques al Dashboard

#### Bloque 1: Gauge de Temperatura

1. Dentro del dashboard, haz clic en **"+"** → **"Create New Block"**
2. Selecciona **"Gauge"**
3. Configuración:
   - **Feed**: `sensor_temp`
   - **Block Title**: Temperatura
   - **Min Value**: 0
   - **Max Value**: 50
   - **Units**: °C
   - **Gauge Type**: Simple
   - **Color Ranges**:
     - 0-15: Azul (#0000FF)
     - 15-25: Verde (#00FF00)
     - 25-35: Amarillo (#FFFF00)
     - 35-50: Rojo (#FF0000)
4. Haz clic en **"Create Block"**

#### Bloque 2: Gauge de Humedad

1. **"+"** → **"Gauge"**
2. Configuración:
   - **Feed**: `sensor_hum`
   - **Block Title**: Humedad
   - **Min Value**: 0
   - **Max Value**: 100
   - **Units**: %
   - **Color Ranges**:
     - 0-30: Rojo (seco)
     - 30-60: Verde (ideal)
     - 60-100: Azul (húmedo)
3. **"Create Block"**

#### Bloque 3: Gauge de Luminosidad

1. **"+"** → **"Gauge"**
2. Configuración:
   - **Feed**: `sensor_ldr_pct`
   - **Block Title**: Luminosidad
   - **Min Value**: 0
   - **Max Value**: 100
   - **Units**: %
   - **Color Ranges**:
     - 0-20: Gris oscuro
     - 20-40: Gris
     - 40-70: Amarillo
     - 70-100: Amarillo brillante
3. **"Create Block"**

#### Bloque 4: Gráfico de Temperatura

1. **"+"** → **"Line Chart"**
2. Configuración:
   - **Feed**: `sensor_temp`
   - **Block Title**: Histórico Temperatura
   - **Show Y-Axis**: ✅
   - **Hours of Data**: 24
   - **Step Plot**: ❌
3. **"Create Block"**

#### Bloque 5: Texto de Confort

1. **"+"** → **"Text"**
2. Configuración:
   - **Feed**: `sensor_comfort`
   - **Block Title**: Nivel de Confort
   - **Font Size**: Large
   - **Text Alignment**: Center
3. **"Create Block"**

#### Bloque 6: Timestamp

1. **"+"** → **"Text"**
2. Configuración:
   - **Feed**: `sensor_estado`
   - **Block Title**: Última Lectura
   - **Font**: Monospace
3. **"Create Block"**

#### Bloque 7: Control LED (Bidireccional)

1. **"+"** → **"Toggle"**
2. Configuración:
   - **Feed**: `comando_led`
   - **Block Title**: Control LED
   - **Button On Text**: LED ON
   - **Button Off Text**: LED OFF
   - **On Value**: ON
   - **Off Value**: OFF
3. **"Create Block"**

> 🎯 **TIP**: Este botón controla el LED en Wokwi en tiempo real

#### Bloque 8: Log de Eventos (Opcional)

1. **"+"** → **"Stream"**
2. Configuración:
   - **Feed**: `system_event`
   - **Block Title**: Eventos del Sistema
   - **Show Timestamps**: ✅
   - **Max Items**: 10
3. **"Create Block"**

### Paso 2.6: Organizar Dashboard

Arrastra los bloques para organizarlos así:

```
┌─────────────────────────────────────────┐
│  Temperatura  │  Humedad  │ Luminosidad │
│    [Gauge]    │  [Gauge]  │   [Gauge]   │
├─────────────────────────────────────────┤
│        Histórico Temperatura            │
│            [Line Chart]                 │
├──────────────┬──────────────┬───────────┤
│ Confort      │  Timestamp   │  Control  │
│  [Text]      │   [Text]     │   LED     │
│              │              │  [Toggle] │
└──────────────┴──────────────┴───────────┘
```

### Paso 2.7: Probar Conexión desde Wokwi

1. Vuelve a Wokwi
2. Asegúrate de tener las credenciales correctas en `main.py`
3. Inicia la simulación
4. Observa la consola:
   ```
   [MQTT] ✓ Conectado a Adafruit IO
   [MQTT→Cloud] sensor_temp = 23.5
   [MQTT→Cloud] sensor_hum = 55.0
   ```
5. Ve a tu Dashboard de Adafruit IO
6. Los gauges deben empezar a moverse ✅

### Paso 2.8: Probar Control Remoto

1. En el Dashboard, activa el **Toggle del LED** (ON)
2. En Wokwi, debes ver en la consola:
   ```
   [CLOUD→DEVICE] comando_led = ON
   [LED] Encendido desde cloud
   ```
3. El LED en el circuito virtual debe encenderse 💡

---

## 🚂 Parte 3: Configuración de Railway (PostgreSQL)

### Paso 3.1: Crear Cuenta en Railway

1. Ve a [https://railway.app](https://railway.app)
2. Haz clic en **"Start a New Project"** → **"Login with GitHub"**
3. Autoriza Railway a acceder a tu GitHub
4. Confirma tu correo electrónico

> 💰 **Plan Gratuito**: $5 de crédito mensual (suficiente para este proyecto)

### Paso 3.2: Crear Proyecto

1. En el dashboard, haz clic en **"New Project"**
2. Selecciona **"Provision PostgreSQL"**
3. Railway automáticamente crea:
   - Un contenedor PostgreSQL
   - Credenciales de acceso
   - URL de conexión

### Paso 3.3: Obtener DATABASE_URL

1. Haz clic en tu servicio PostgreSQL
2. Ve a la pestaña **"Connect"**
3. Copia el **"Postgres Connection URL"**:
   ```
   postgresql://usuario:contraseña@host.railway.app:puerto/railway
   ```
4. Guarda esta URL (la necesitarás pronto)

> 🔒 **IMPORTANTE**: Esta URL contiene credenciales sensibles. No la subas a Git.

### Paso 3.4: Configurar Variables de Entorno Locales

En tu máquina local, crea un archivo `.env`:

```bash
# En la raíz del proyecto
touch .env
```

Edita `.env` con:
```bash
# Credenciales Adafruit IO
ADAFRUIT_USERNAME=tu_usuario
ADAFRUIT_KEY=aio_XXXXXXXXXXXX

# URL de Railway PostgreSQL
DATABASE_URL=postgresql://usuario:password@host.railway.app:puerto/railway
```

### Paso 3.5: Instalar Dependencias del Bridge

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

**Contenido de `requirements.txt`:**
```
paho-mqtt==1.6.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

### Paso 3.6: Ejecutar el Bridge (Primera Vez)

```bash
# Cargar variables de entorno
export $(cat .env | xargs)  # Linux/macOS
# O en Windows PowerShell:
# Get-Content .env | ForEach-Object { $name,$value = $_.split('='); [Environment]::SetEnvironmentVariable($name,$value) }

# Ejecutar bridge
python mqtt_to_database.py
```

**Salida esperada:**
```
============================================================
   🚀 MQTT to PostgreSQL Bridge V3
   Con manejo inteligente de anomalías
============================================================

[1] Inicializando base de datos con auto-migración...
🔧 Ejecutando auto-migración de base de datos...
   ⚙️  Agregando columna 'comfort_level'...
   ⚙️  Agregando columna 'reading_number'...
   ⚙️  Verificando tabla 'statistics'...
   ⚙️  Creando índices...
✅ Migración completada: comfort_level, reading_number

📊 Estado de la base de datos:
   • sensor_readings: 0 registros
   • events: 1 registros
   • statistics: 0 registros

[2] Configurando cliente MQTT...
[3] Conectando a Adafruit IO...
✅ Conectado a Adafruit IO
   📡 Suscrito a: sensor_temp
   📡 Suscrito a: sensor_hum
   📡 Suscrito a: sensor_ldr_pct
   📡 Suscrito a: sensor_ldr_raw
   📡 Suscrito a: sensor_estado
   📡 Suscrito a: sensor_comfort
   📡 Suscrito a: system_event

Esperando datos...
```

### Paso 3.7: Verificar Flujo Completo

Con todo funcionando:

1. **Wokwi** → Lee sensores cada 10s, publica MQTT cada 20s
2. **Adafruit IO** → Recibe datos, actualiza dashboard
3. **Bridge** → Escucha MQTT, guarda en PostgreSQL

Debes ver en el bridge:
```
📥 MQTT → sensor_temp: 23.5
📥 MQTT → sensor_hum: 55.0
📥 MQTT → sensor_ldr_pct: 75.3
📥 MQTT → sensor_ldr_raw: 49152
📥 MQTT → sensor_estado: 14:30
📥 MQTT → sensor_comfort: Agradable
✅ Lectura #1 guardada (ID:1) - T:23.5°C H:55.0% LDR:75.3% 14:30 [Agradable]
```

### Paso 3.8: Verificar Datos en PostgreSQL

#### Opción A: Usar Railway Dashboard

1. En Railway, ve a tu servicio PostgreSQL
2. Haz clic en la pestaña **"Data"**
3. Verás las tablas: `sensor_readings`, `events`, `statistics`
4. Haz clic en `sensor_readings` para ver los datos

#### Opción B: Usar psql (línea de comandos)

```bash
# Instalar psql (si no lo tienes)
# Ubuntu/Debian:
sudo apt install postgresql-client

# macOS:
brew install postgresql

# Conectar a la BD
psql $DATABASE_URL

# Consultas útiles
SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;
SELECT COUNT(*) FROM sensor_readings;
SELECT * FROM events ORDER BY timestamp DESC;
```

---

## 🔄 Parte 4: Despliegue del Bridge en Railway (Opcional)

Si quieres que el bridge corra 24/7 sin tener tu PC encendida:

### Paso 4.1: Preparar Repositorio

1. Asegúrate de que tu repo tenga:
   - `mqtt_to_database.py`
   - `requirements.txt`
   - `runtime.txt` (con contenido: `python-3.11.8`)

2. **NO** subas el archivo `.env` a Git:
   ```bash
   # Agregar a .gitignore
   echo ".env" >> .gitignore
   ```

### Paso 4.2: Crear Servicio en Railway

1. En Railway, en tu proyecto, haz clic en **"New"** → **"GitHub Repo"**
2. Selecciona tu repositorio `estacion-meteorologica-iot`
3. Railway detectará automáticamente `requirements.txt` y Python

### Paso 4.3: Configurar Variables de Entorno en Railway

1. En el servicio recién creado, ve a **"Variables"**
2. Agrega las mismas variables del `.env`:
   ```
   ADAFRUIT_USERNAME = tu_usuario
   ADAFRUIT_KEY = aio_XXXXXXXXXXXX
   DATABASE_URL = ${{Postgres.DATABASE_URL}}  # Referencia interna
   ```

### Paso 4.4: Configurar Start Command

1. Ve a **"Settings"** → **"Start Command"**
2. Ingresa:
   ```bash
   python mqtt_to_database.py
   ```

### Paso 4.5: Desplegar

1. Haz clic en **"Deploy"**
2. Railway construirá e iniciará el servicio
3. Ve a **"Logs"** para monitorear:
   ```
   ✅ Conectado a Adafruit IO
   📥 MQTT → sensor_temp: 23.5
   ✅ Lectura #1 guardada
   ```

¡Ahora el bridge corre en la nube 24/7! 🎉

---

## ✅ Verificación Final - Checklist

### Wokwi
- [ ] Proyecto creado con todos los archivos `.py`
- [ ] Circuito configurado (DHT22, LDR, LCD, LED, Buzzer)
- [ ] Credenciales de Adafruit IO actualizadas en `main.py`
- [ ] Simulación inicia sin errores
- [ ] Conecta a WiFi exitosamente
- [ ] Conecta a MQTT exitosamente

### Adafruit IO
- [ ] Cuenta creada y email confirmado
- [ ] 8 feeds creados con nombres exactos
- [ ] Dashboard creado con 7-8 bloques
- [ ] Gauges funcionan y muestran datos en tiempo real
- [ ] Control LED responde desde dashboard
- [ ] Gráfico histórico muestra datos

### Railway
- [ ] Cuenta creada y vinculada con GitHub
- [ ] PostgreSQL provisionado
- [ ] DATABASE_URL obtenida
- [ ] Bridge ejecuta localmente sin errores
- [ ] Datos se guardan en PostgreSQL
- [ ] (Opcional) Bridge desplegado en Railway

### Flujo End-to-End
- [ ] Wokwi → Sensores leen valores
- [ ] Wokwi → Publica a Adafruit IO
- [ ] Adafruit IO → Dashboard actualiza
- [ ] Bridge → Recibe vía MQTT
- [ ] Bridge → Guarda en PostgreSQL
- [ ] Control remoto LED funciona

---

## 🐛 Troubleshooting Cloud

### Problema: Wokwi no conecta a Adafruit IO

**Síntomas:**
```
[MQTT] ✗ Error conectando: OSError 103
```

**Soluciones:**
1. Verifica que `ADAFRUIT_USERNAME` sea tu username (no email)
2. Copia la API Key completa desde Adafruit IO → My Key
3. Asegúrate de no tener espacios extras en las credenciales
4. Intenta regenerar la API Key en Adafruit IO

### Problema: Dashboard no actualiza

**Soluciones:**
1. Verifica que los feeds tengan los **nombres exactos**:
   - ❌ `temperature` → ✅ `sensor_temp`
   - ❌ `humidity` → ✅ `sensor_hum`
2. En Wokwi, revisa la consola para confirmar publicaciones:
   ```
   [MQTT→Cloud] sensor_temp = 23.5  ✅
   ```
3. Refresca el Dashboard (F5)
4. Verifica en Feeds individuales si están recibiendo datos

### Problema: Bridge no encuentra DATABASE_URL

**Síntomas:**
```
❌ ERROR: DATABASE_URL no está configurada
```

**Soluciones:**
```bash
# Verificar variable de entorno
echo $DATABASE_URL

# Si está vacía, cargar de .env
export $(cat .env | xargs)

# Windows PowerShell
$env:DATABASE_URL = "postgresql://..."

# O ejecutar con dotenv
python -m dotenv run python mqtt_to_database.py
```

### Problema: Railway - "No such file or directory"

**Síntomas:**
```
Error: python: can't open file 'mqtt_to_database.py'
```

**Soluciones:**
1. Verifica que el archivo esté en la **raíz** del repo
2. Revisa mayúsculas/minúsculas del nombre
3. Confirma que el archivo se subió a GitHub
4. En Railway, ve a **"Deployments"** → Click en el último → **"View Logs"**

### Problema: Límite de 30 mensajes/minuto en Adafruit IO

**Síntomas:**
```
429 Too Many Requests
```

**Solución:**
En `main.py`, aumenta `PUBLISH_INTERVAL`:
```python
PUBLISH_INTERVAL = 30  # Cambia de 20 a 30 segundos
# O incluso 60 para estar seguro
```

---

## 📊 Monitoreo de Uso

### Adafruit IO

Ve a **"Usage"** en tu perfil:
- **Messages**: Cuántos mensajes has enviado (límite: 30/min)
- **Data Storage**: Cuántos puntos de datos tienes (límite: 30 días)
- **Active Feeds**: Feeds con datos recientes (límite: 10)

### Railway

Ve a **"Usage"** en tu proyecto:
- **Estimated Usage**: Costo estimado del mes
- **Included**: $5 gratuitos
- **CPU/RAM**: Recursos usados por el bridge

**Optimización**:
- El bridge usa ~50MB RAM y <1% CPU
- PostgreSQL usa ~200MB RAM
- Costo típico: **$0.50 - $1.00/mes** (dentro del plan gratuito)

---

## 🎓 Buenas Prácticas

### Seguridad
1. ✅ Nunca subas `.env` a Git
2. ✅ Usa `.gitignore` para secretos
3. ✅ Rota API Keys cada 3-6 meses
4. ✅ Usa variables de entorno en producción

### Monitoreo
1. ✅ Revisa logs del bridge diariamente
2. ✅ Configura alertas en Railway (opcional)
3. ✅ Verifica que el dashboard actualice cada 20s
4. ✅ Monitorea el uso de Adafruit IO

### Escalabilidad
1. ✅ Si superas 30 msg/min, considera MQTT batching
2. ✅ Si superas $5/mes en Railway, optimiza queries
3. ✅ Para múltiples dispositivos, usa client IDs únicos

---

## 📚 Recursos Adicionales

### Documentación Oficial
- **Wokwi**: https://docs.wokwi.com
- **Adafruit IO**: https://io.adafruit.com/api/docs
- **Railway**: https://docs.railway.app
- **MicroPython**: https://docs.micropython.org

### Comunidades
- **Wokwi Discord**: https://wokwi.com/discord
- **Adafruit Forums**: https://forums.adafruit.com
- **Railway Discord**: https://discord.gg/railway

### Tutoriales Relacionados
- MQTT con ESP32: https://learn.adafruit.com/mqtt-in-circuitpython
- PostgreSQL básico: https://www.postgresqltutorial.com
- MicroPython IoT: https://docs.micropython.org/en/latest/esp32/quickref.html

---

¡Felicitaciones! 🎉 Ahora tienes tu **Estación Meteorológica IoT completamente funcional** en la nube.

**Próximos pasos sugeridos:**
1. Personaliza el dashboard con tus colores favoritos
2. Agrega más sensores (presión, CO2, UV)
3. Implementa alertas por email/SMS
4. Crea visualizaciones avanzadas con Grafana
# config.py
# Archivo de configuración centralizado - VERSIÓN CORREGIDA

# ==================== WiFi ====================
WIFI_SSID = "Wokwi-GUEST"  # Cambiar por tu red WiFi real
WIFI_PASSWORD = ""          # Cambiar por tu contraseña WiFi

# Para Wokwi, usar "Wokwi-GUEST" sin contraseña
# Para hardware real, configurar tu red

# ==================== Adafruit IO ====================
ADAFRUIT_USERNAME = "_Sieg_"
ADAFRUIT_KEY = "aio_hsZH30eJHN40CGihpPbqL1lIowSV"

# Nombres de los feeds (deben coincidir EXACTAMENTE con Adafruit IO)
FEED_HUMIDITY = "sensor_hum"       
FEED_TEMPERATURE = "sensor_temp"  
FEED_LED_COMMAND = "comando_led"   

# ==================== Hardware ====================
# Pines I2C para LCD
I2C_SDA = 4
I2C_SCL = 5

# Pines de sensores
DHT_PIN = 15
LDR_ADC_PIN = 26
LDR_DO_PIN = None  # Pin digital opcional

# Pines de actuadores
LED_PIN = 14
BUZZER_PIN = 13

# ==================== Intervalos (segundos) ====================
SENSOR_INTERVAL = 10       # Leer sensores cada 10s
PUBLISH_INTERVAL = 30      # Publicar a cloud cada 30s
RECONNECT_INTERVAL = 30    # Reintentar conexión cada 30s
DB_CLEANUP_INTERVAL = 3600 # Limpiar BD cada hora (1h)

# ==================== Base de Datos ====================
DB_PATH = "/"
DB_KEEP_LINES = 500  # Mantener últimas 500 lecturas

# ==================== Sensores ====================
# Media móvil para suavizar lecturas LDR
MOVING_AVERAGE_SIZE = 5

# Umbrales para estado día/noche (%)
UMBRAL_DIA = 60.0    # >= 60% es DÍA
UMBRAL_NOCHE = 30.0  # <= 30% es NOCHE
# Entre 30-60% es TARDE/INTERMEDIO

# ==================== Actuadores ====================
LED_ON_MS = 200  # Tiempo mínimo LED encendido al leer sensores

# Configuración buzzer
BUZZER_FREQ_SENSOR = 1800   # Frecuencia al leer sensores
BUZZER_FREQ_PUBLISH = 2500  # Frecuencia al publicar
BUZZER_FREQ_COMMAND = 1500  # Frecuencia al recibir comando
BUZZER_DURATION = 100       # Duración en ms

# ==================== Debug ====================
DEBUG = True  # Activar mensajes de debug detallados

# ==================== Validación ====================
def validate_config():
    """Validar configuración antes de iniciar"""
    errors = []
    
    # Validar feeds (no deben tener guiones)
    if "-" in FEED_HUMIDITY:
        errors.append(f"FEED_HUMIDITY contiene guión: '{FEED_HUMIDITY}'")
    if "-" in FEED_TEMPERATURE:
        errors.append(f"FEED_TEMPERATURE contiene guión: '{FEED_TEMPERATURE}'")
    if "-" in FEED_LED_COMMAND:
        errors.append(f"FEED_LED_COMMAND contiene guión: '{FEED_LED_COMMAND}'")
    
    # Validar credenciales
    if not ADAFRUIT_USERNAME or not ADAFRUIT_KEY:
        errors.append("Credenciales de Adafruit IO vacías")
    
    if errors:
        print("\n⚠️  ERRORES DE CONFIGURACIÓN:")
        for e in errors:
            print(f"  - {e}")
        return False
    
    print("✅ Configuración validada correctamente")
    return True
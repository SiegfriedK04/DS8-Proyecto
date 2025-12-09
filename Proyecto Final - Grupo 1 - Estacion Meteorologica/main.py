# main.py
# Sistema IoT - MQTT Cloud con Simulador Integrado
# MODO SIMULACIÓN: 24h en 5 minutos (activar en utils.py)
# ✨ MEJORAS: Intervalo 20s + Manejo de anomalías

from machine import I2C, Pin
import utime

from sensors import LDR, DHT22Sensor
from actuators import LED, Buzzer
from lcd_i2c import SimpleI2cLcd
from utils import (
    MODO_SIMULACION,
    obtener_hora_actual,
    obtener_temperatura_simulada,
    obtener_humedad_simulada,
    obtener_luminosidad_simulada,
    calcular_confort_termico,
    descripcion_luminosidad,
    MovingAverage
)
from mqtt_client import AdafruitMQTT

# ==================== CONFIGURACIÓN ====================

### CONEXIÓN WIFI ###
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

### CREDENCIALES ADAFRUIT IO ###
ADAFRUIT_USERNAME = "_Sieg_"
ADAFRUIT_KEY = "aio_hsZH30eJHN40CGihpPbqL1lIowSV"

### FEEDS MQTT - CANALES DE COMUNICACIÓN ###
# Sensores -> Cloud
FEED_HUMIDITY = "sensor_hum"           # Humedad relativa (%)
FEED_TEMPERATURE = "sensor_temp"       # Temperatura (°C)
FEED_LDR_PERCENT = "sensor_ldr_pct"    # Luminosidad (%)
FEED_LDR_RAW = "sensor_ldr_raw"        # Valor ADC del LDR
FEED_ESTADO = "sensor_estado"          # Hora actual
FEED_COMFORT = "sensor_comfort"        # Nivel de confort térmico

# Cloud -> Dispositivo
FEED_LED_COMMAND = "comando_led"       # Control remoto del LED

# Eventos del sistema
FEED_SYSTEM_EVENT = "system_event"     # Log de eventos

### HARDWARE - CONFIGURACIÓN DE PINES ###
I2C_SDA = 4  # Pin de datos I2C
I2C_SCL = 5  # Pin de reloj I2C

### TEMPORIZADORES ###
SENSOR_INTERVAL = 10   # Lectura de sensores cada 10 segundos
PUBLISH_INTERVAL = 20  # Publicación MQTT cada 20 segundos (optimizado)

### CONFIGURACIÓN LED ###
LED_ON_MS = 200  # Duración del parpadeo al leer sensores

### CONSTANTE PARA DATOS ANÓMALOS ###
ANOMALIA = "ANOMALIA"  # Marcador cuando los sensores fallan

# ==================== INICIALIZACIÓN ====================

print("\n" + "="*50)
if MODO_SIMULACION:
    print("   Sistema IoT - MODO SIMULACIÓN (24h→5min)")
else:
    print("   Sistema IoT - MQTT Cloud")
print("="*50)

### INICIALIZACIÓN LCD ###
# Detectar y configurar pantalla I2C
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA))
addrs = i2c.scan()
lcd = None
if addrs:
    try:
        lcd = SimpleI2cLcd(i2c, addrs[0])
        lcd.clear()
        if MODO_SIMULACION:
            lcd.putstr("Modo Simulacion")
            utime.sleep(1)
        lcd.putstr("Iniciando...")
        print("[LCD] Inicializado")
    except Exception as e:
        print("[LCD] Error:", e)
        lcd = None
else:
    print("[LCD] No detectado")

### INICIALIZACIÓN SENSORES Y ACTUADORES ###
ldr = LDR(adc_pin=26, do_pin=None)  # Sensor de luz
dht = DHT22Sensor(pin=15)           # Sensor temperatura/humedad
led = LED(pin=14)                   # LED indicador
buzzer = Buzzer(pin=13)             # Buzzer para notificaciones
print("[Sensores] Inicializados")

### FILTRO DE MEDIA MÓVIL ###
# Suaviza las lecturas del LDR para reducir fluctuaciones
ma = MovingAverage(size=5)

### CLIENTE MQTT ###
mqtt = AdafruitMQTT(ADAFRUIT_USERNAME, ADAFRUIT_KEY, WIFI_SSID, WIFI_PASSWORD)

### VARIABLES DE ESTADO ###
last_sensor_read = 0    # Timestamp última lectura
last_publish = 0        # Timestamp última publicación MQTT
last_temp = None        # Última temperatura leída
last_hum = None         # Última humedad leída
last_ldr_pct = None     # Último porcentaje de luminosidad
mqtt_connected = False  # Estado de la conexión MQTT
publish_counter = 0     # Contador de publicaciones exitosas

# ==================== FUNCIONES ====================

def display_message(line1, line2=""):
    """
    Muestra un mensaje de dos líneas en el LCD
    Maneja errores silenciosamente si el LCD no está disponible
    """
    if lcd:
        try:
            lcd.clear()
            lcd.putstr(line1[:16])  # Línea 1 (máx 16 caracteres)
            if line2:
                lcd.move_to(0, 1)
                lcd.putstr(line2[:16])  # Línea 2 (máx 16 caracteres)
        except:
            pass

def publish_event(event_type, description):
    """
    Registra eventos del sistema en Adafruit IO
    Formato: "TIPO:Descripción"
    """
    if mqtt_connected:
        try:
            event_msg = f"{event_type}:{description}"
            mqtt.publish(FEED_SYSTEM_EVENT, event_msg)
            print(f"[Evento] {event_msg}")
        except Exception as e:
            print(f"[Error] Publicando evento: {e}")

def on_cloud_message(feed_name, value):
    """
    Callback ejecutado al recibir comandos desde Adafruit IO
    Maneja control remoto del LED y proporciona feedback al usuario
    """
    global last_temp, last_hum, last_ldr_pct
    
    print(f"\n[CLOUD→DEVICE] {feed_name} = {value}")
    
    try:
        # Procesar comandos de LED
        if feed_name == FEED_LED_COMMAND or "comando" in feed_name.lower():
            if value == "ON" or value == "1":
                led.on()
                publish_event("LED", "ON desde cloud")
                display_message("LED: ON", "Desde Cloud")
                print("[LED] Encendido desde cloud")
            elif value == "OFF" or value == "0":
                led.off()
                publish_event("LED", "OFF desde cloud")
                display_message("LED: OFF", "Desde Cloud")
                print("[LED] Apagado desde cloud")
            
            # Confirmación sonora
            buzzer.beep(100, 1500)
            utime.sleep_ms(200)
            
            # Restaurar display con datos ambientales después de 2s
            if last_temp is not None and last_ldr_pct is not None:
                utime.sleep(2)
                desc_luz = descripcion_luminosidad(last_ldr_pct)
                confort = calcular_confort_termico(last_temp, last_hum)
                display_message(f"{desc_luz}", f"{confort}")
                
    except Exception as e:
        print("[ERROR] Procesando mensaje cloud:", e)

def connect_mqtt():
    """
    Establece conexión con Adafruit IO y se suscribe a feeds de comandos
    Retorna True si la conexión es exitosa
    """
    global mqtt_connected
    
    display_message("Conectando", "Adafruit IO...")
    
    if mqtt.connect_mqtt():
        # Suscribirse al feed de comandos
        mqtt.subscribe(FEED_LED_COMMAND)
        mqtt.set_message_callback(on_cloud_message)
        mqtt_connected = True
        
        # Notificar conexión exitosa
        modo = "SIMULACION" if MODO_SIMULACION else "REAL"
        publish_event("SYSTEM", f"Conectado - Modo {modo}")
        display_message("Cloud OK!", "Adafruit IO")
        buzzer.beep(100, 2000)
        utime.sleep(1)
        
        return True
    else:
        mqtt_connected = False
        display_message("Error Cloud", "Reintentando...")
        return False

def read_sensors():
    """
    Lee todos los sensores (reales o simulados según configuración)
    Aplica filtrado de media móvil al LDR para suavizar lecturas
    Maneja valores None convirtiéndolos a ANOMALIA para tracking
    
    Retorna: (temp, hum, ldr_pct, ldr_raw, hora, confort, desc_luz)
    """
    global last_temp, last_hum, last_ldr_pct
    
    # Indicadores visuales de lectura
    led.on()
    buzzer.beep(50, 1800)
    
    ### LECTURA DE SENSORES ###
    if MODO_SIMULACION:
        # Datos simulados (ciclo de 24h comprimido en 5min)
        temp = obtener_temperatura_simulada()
        hum = obtener_humedad_simulada()
        pct = obtener_luminosidad_simulada()
        raw = int((pct / 100.0) * 65535) if pct else 0
    else:
        # Sensores físicos
        raw = ldr.read_raw()
        pct = ldr.read_pct()
        temp, hum = dht.read()
    
    utime.sleep_ms(LED_ON_MS)
    led.off()
    
    ### FILTRADO DE MEDIA MÓVIL PARA LDR ###
    # Reduce ruido en lecturas de luminosidad
    if pct is not None:
        ma.add(pct)
        avg_pct = ma.avg()
        pct_smoothed = round(avg_pct, 1) if avg_pct is not None else pct
    else:
        pct_smoothed = None
    
    ### MANEJO DE ANOMALÍAS ###
    # Marcar valores None para tracking en la nube
    if temp is None:
        temp = ANOMALIA
    if hum is None:
        hum = ANOMALIA
    
    ### CÁLCULOS DERIVADOS ###
    desc_luz = descripcion_luminosidad(pct_smoothed)
    confort = calcular_confort_termico(
        temp if temp != ANOMALIA else None,
        hum if hum != ANOMALIA else None
    )
    hora = obtener_hora_actual()
    
    # Actualizar cache de valores
    last_temp = temp
    last_hum = hum
    last_ldr_pct = pct_smoothed
    
    ### LOGGING Y DISPLAY ###
    modo_str = "[SIM]" if MODO_SIMULACION else "[REAL]"
    if temp == ANOMALIA:
        print(f"{modo_str} LDR:{pct_smoothed}% ({desc_luz}) | DHT:{ANOMALIA} | {hora}")
    else:
        print(f"{modo_str} LDR:{pct_smoothed}% ({desc_luz}) | T:{temp}°C H:{hum}% ({confort}) | {hora}")
    
    display_message(f"{desc_luz} {pct_smoothed}%", f"{confort}")
    
    return temp, hum, pct_smoothed, raw, hora, confort, desc_luz

def publish_all_sensors(temp, hum, ldr_pct, ldr_raw, hora, confort, desc_luz):
    """
    Publica todas las lecturas a sus respectivos feeds MQTT
    Envía "ANOMALIA" cuando los sensores fallan
    Incluye delays de 100ms entre publicaciones para estabilidad
    
    Retorna: True si todas las publicaciones fueron exitosas
    """
    global publish_counter, mqtt_connected
    
    if not mqtt_connected:
        return False
    
    try:
        success = True
        
        ### PUBLICACIÓN DE DATOS ###
        # Temperatura
        temp_value = temp if temp != ANOMALIA else ANOMALIA
        if not mqtt.publish(FEED_TEMPERATURE, temp_value):
            success = False
        utime.sleep_ms(100)
        
        # Humedad
        hum_value = hum if hum != ANOMALIA else ANOMALIA
        if not mqtt.publish(FEED_HUMIDITY, hum_value):
            success = False
        utime.sleep_ms(100)
        
        # Luminosidad (porcentaje)
        if not mqtt.publish(FEED_LDR_PERCENT, ldr_pct):
            success = False
        utime.sleep_ms(100)
        
        # Luminosidad (valor ADC raw)
        if not mqtt.publish(FEED_LDR_RAW, ldr_raw):
            success = False
        utime.sleep_ms(100)
        
        # Timestamp
        if not mqtt.publish(FEED_ESTADO, hora):
            success = False
        utime.sleep_ms(100)
        
        # Confort térmico
        if not mqtt.publish(FEED_COMFORT, confort):
            success = False
        
        ### FEEDBACK ###
        if success:
            publish_counter += 1
            print(f"[MQTT] ✓ Datos publicados #{publish_counter}")
            print(f"       Hora: {hora} | Confort: {confort} | Luz: {desc_luz}")
            buzzer.beep(50, 2500)
        else:
            mqtt_connected = False
            print("[MQTT] ✗ Error publicando algunos datos")
        
        return success
        
    except Exception as e:
        print("[ERROR] Publicando datos:", e)
        mqtt_connected = False
        return False

# ==================== BUCLE PRINCIPAL ====================

### INICIO DEL SISTEMA ###
print("\n[Sistema] Iniciando bucle principal...")
buzzer.beep(100, 1500)
utime.sleep_ms(100)
buzzer.beep(100, 2000)

# Conexión inicial a MQTT
connect_mqtt()

### RESUMEN DE CONFIGURACIÓN ###
print(f"\n[Sistema] Configuración:")
print(f"  - Modo:         {'SIMULACIÓN (24h→5min)' if MODO_SIMULACION else 'REAL'}")
print(f"  - Sensores:     {SENSOR_INTERVAL}s")
print(f"  - MQTT:         {PUBLISH_INTERVAL}s ✨ (reducido para capturar más datos)")
print(f"\n[Sistema] Feeds MQTT:")
print(f"  - Temperatura:  {FEED_TEMPERATURE}")
print(f"  - Humedad:      {FEED_HUMIDITY}")
print(f"  - LDR %:        {FEED_LDR_PERCENT}")
print(f"  - LDR raw:      {FEED_LDR_RAW}")
print(f"  - Hora:         {FEED_ESTADO}")
print(f"  - Confort:      {FEED_COMFORT}")
print(f"  - Comandos:     {FEED_LED_COMMAND}")
print(f"  - Eventos:      {FEED_SYSTEM_EVENT}")

### LOOP INFINITO ###
while True:
    try:
        current_time = utime.time()
        
        ### VERIFICACIÓN DE MENSAJES MQTT ###
        # Procesar comandos entrantes desde la nube
        if mqtt_connected:
            try:
                if not mqtt.check_messages():
                    print("\n[MQTT] Reconectando...")
                    mqtt_connected = False
                    publish_event("SYSTEM", "Conexión MQTT perdida")
                    utime.sleep(2)
                    connect_mqtt()
            except Exception as e:
                print(f"[MQTT] Error: {e}")
                mqtt_connected = False
        else:
            # Intentar reconexión cada 30 segundos
            if current_time - last_publish > 30:
                connect_mqtt()
        
        ### LECTURA PERIÓDICA DE SENSORES ###
        # Ejecuta cada SENSOR_INTERVAL segundos
        if current_time - last_sensor_read >= SENSOR_INTERVAL:
            temp, hum, pct, raw, hora, confort, desc_luz = read_sensors()
            last_sensor_read = current_time
        
        ### PUBLICACIÓN PERIÓDICA A MQTT ###
        # Ejecuta cada PUBLISH_INTERVAL segundos (20s optimizado)
        if mqtt_connected and (current_time - last_publish >= PUBLISH_INTERVAL):
            if last_temp is not None or last_ldr_pct is not None:
                hora_actual = obtener_hora_actual()
                
                # Recalcular métricas con valores más recientes
                temp_calc = last_temp if last_temp != ANOMALIA else None
                hum_calc = last_hum if last_hum != ANOMALIA else None
                confort_actual = calcular_confort_termico(temp_calc, hum_calc)
                desc_luz_actual = descripcion_luminosidad(last_ldr_pct)
                
                # Obtener valor raw correcto según modo
                if MODO_SIMULACION:
                    raw_actual = int((last_ldr_pct / 100.0) * 65535) if last_ldr_pct else 0
                else:
                    raw_actual = ldr.read_raw()
                
                # Publicar conjunto completo de datos
                publish_all_sensors(
                    last_temp, last_hum, last_ldr_pct,
                    raw_actual, hora_actual, confort_actual, desc_luz_actual
                )
            last_publish = current_time
        
        # Pequeño delay para no saturar el CPU
        utime.sleep_ms(100)
        
    except KeyboardInterrupt:
        ### APAGADO LIMPIO ###
        print("\n\n[Sistema] Detenido por usuario")
        
        publish_event("SYSTEM", "Sistema detenido")
        mqtt.disconnect()
        display_message("Sistema", "Detenido")
        
        print("\n[Sistema] Datos guardados en Adafruit IO")
        break
        
    except Exception as e:
        ### MANEJO DE ERRORES ###
        print(f"\n[ERROR] En bucle principal: {e}")
        publish_event("ERROR", str(e))
        utime.sleep(1)

print("[Sistema] Finalizado")
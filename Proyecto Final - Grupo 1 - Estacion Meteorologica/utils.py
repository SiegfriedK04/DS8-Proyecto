# utils.py
# Utilidades mejoradas: hora, confort térmico, descripción luz
# + SIMULADOR DE TIEMPO ACELERADO (24h en 5 minutos)
# ✨ Manejo de valores anómalos

import utime
import math

# ==================== CONFIGURACIÓN ====================

### MODO SIMULACIÓN ###
# Activa tiempo acelerado para pruebas rápidas
# True: 24 horas se ejecutan en 5 minutos (factor 288x)
# False: Usa tiempo real del sistema
MODO_SIMULACION = True

### PARÁMETROS DE SIMULACIÓN ###
ACELERACION_TIEMPO = 288    # Factor de aceleración (86400s / 300s)
HORA_INICIO_SIM = 6         # Hora de inicio del ciclo simulado (6:00 AM)

### UMBRALES DE LUMINOSIDAD (%) ###
# Definen los rangos para clasificar la luz ambiente
UMBRAL_MUY_LUMINOSO = 80.0  # >= 80%: Muy luminoso
UMBRAL_LUMINOSO = 60.0      # >= 60%: Luminoso
UMBRAL_MEDIO = 40.0         # >= 40%: Iluminación media
UMBRAL_TENUE = 20.0         # >= 20%: Tenue, < 20%: Oscuro

### CONSTANTE PARA VALORES ANÓMALOS ###
ANOMALIA = "ANOMALIA"  # Marcador para lecturas de sensores fallidas

# ==================== VARIABLES GLOBALES DE SIMULACIÓN ====================

# Mantienen el estado del simulador entre llamadas
_sim_tiempo_inicio = None   # Timestamp de inicio de la simulación
_sim_ruido_contador = 0     # Contador para generar ruido pseudo-aleatorio

def _inicializar_simulacion():
    """
    Inicializa el simulador de tiempo acelerado
    Se ejecuta automáticamente en la primera llamada si MODO_SIMULACION=True
    """
    global _sim_tiempo_inicio
    if MODO_SIMULACION and _sim_tiempo_inicio is None:
        _sim_tiempo_inicio = utime.time()
        print(f"\n[SIMULADOR] Activado: 24h en 5min (factor {ACELERACION_TIEMPO}x)")
        print(f"[SIMULADOR] Hora inicio: {HORA_INICIO_SIM}:00 AM")

def _obtener_hora_simulada():
    """
    Calcula la hora simulada aplicando factor de aceleración
    Convierte tiempo real transcurrido en tiempo simulado
    
    Retorna: (hora, minuto, segundo) o None si simulación desactivada
    """
    if not MODO_SIMULACION:
        return None
    
    global _sim_tiempo_inicio
    if _sim_tiempo_inicio is None:
        _inicializar_simulacion()
    
    # Tiempo real transcurrido desde inicio
    tiempo_real = utime.time() - _sim_tiempo_inicio
    
    # Aplicar aceleración: 1 segundo real = 288 segundos simulados
    tiempo_sim = tiempo_real * ACELERACION_TIEMPO
    
    # Calcular hora del día (0-86399 segundos)
    segundos_totales = (HORA_INICIO_SIM * 3600) + tiempo_sim
    segundos_totales = segundos_totales % 86400  # Ciclo de 24h
    
    # Convertir a horas, minutos, segundos
    hora = int(segundos_totales // 3600)
    minuto = int((segundos_totales % 3600) // 60)
    segundo = int(segundos_totales % 60)
    
    return hora, minuto, segundo

def _ruido():
    """
    Genera variación pseudo-aleatoria para simular fluctuaciones naturales
    Usa función seno con contador incremental para variabilidad
    
    Retorna: Valor flotante entre -1.0 y 1.0
    """
    global _sim_ruido_contador
    _sim_ruido_contador += 1
    return math.sin(_sim_ruido_contador * 0.1234)

# ==================== FUNCIONES PÚBLICAS ====================

def obtener_hora_actual():
    """
    Obtiene la hora actual en formato 12h con AM/PM
    
    Si MODO_SIMULACION=True:
        Usa tiempo acelerado del simulador
    Si MODO_SIMULACION=False:
        Usa tiempo real del sistema (utime.localtime)
    
    Retorna: String formato "HH:MM AM/PM" (ej: "02:30 PM")
             o "N/A" si hay error
    """
    try:
        # Determinar fuente de tiempo
        if MODO_SIMULACION:
            hora_sim = _obtener_hora_simulada()
            if hora_sim:
                hora, minuto, _ = hora_sim
            else:
                t = utime.localtime()
                hora, minuto = t[3], t[4]
        else:
            t = utime.localtime()
            hora, minuto = t[3], t[4]
        
        ### CONVERSIÓN A FORMATO 12H ###
        if hora == 0:
            hora_12h = 12
            periodo = "AM"
        elif hora < 12:
            hora_12h = hora
            periodo = "AM"
        elif hora == 12:
            hora_12h = 12
            periodo = "PM"
        else:
            hora_12h = hora - 12
            periodo = "PM"
        
        return f"{hora_12h:02d}:{minuto:02d} {periodo}"
    except Exception:
        return "N/A"

def obtener_temperatura_simulada():
    """
    Simula temperatura con patrón diario realista
    Solo funciona si MODO_SIMULACION=True
    
    Patrón basado en ciclo natural:
    - Mínima: ~6:00 AM (~18°C)
    - Máxima: ~2:00 PM (~30°C)
    - Usa función seno para transición suave
    - Añade ruido para variabilidad realista
    
    Retorna: Temperatura en °C (float) o None si simulación desactivada
    """
    if not MODO_SIMULACION:
        return None
    
    hora_sim = _obtener_hora_simulada()
    if not hora_sim:
        return None
    
    hora, minuto, _ = hora_sim
    hora_decimal = hora + minuto / 60.0
    
    ### PATRÓN SINUSOIDAL ###
    # Desplazar fase para mínimo a las 6am
    fase = ((hora_decimal - 6) / 24.0) * 2 * math.pi
    variacion = math.sin(fase) * 6.0  # Amplitud de ±6°C
    
    ### CALCULAR TEMPERATURA ###
    temp_base = 23.0  # Temperatura promedio
    ruido = _ruido() * 0.8  # Fluctuación pequeña
    
    temp = temp_base + variacion + ruido
    return round(temp, 1)

def obtener_humedad_simulada():
    """
    Simula humedad relativa con patrón inverso a temperatura
    Solo funciona si MODO_SIMULACION=True
    
    Patrón natural:
    - Alta en la mañana/noche (cuando es más frío)
    - Baja al mediodía (cuando hace más calor)
    - Limitada al rango 20-90% para realismo
    
    Retorna: Humedad en % (float) o None si simulación desactivada
    """
    if not MODO_SIMULACION:
        return None
    
    hora_sim = _obtener_hora_simulada()
    if not hora_sim:
        return None
    
    hora, minuto, _ = hora_sim
    hora_decimal = hora + minuto / 60.0
    
    ### PATRÓN INVERSO A TEMPERATURA ###
    fase = ((hora_decimal - 6) / 24.0) * 2 * math.pi
    variacion = -math.sin(fase) * 15.0  # Amplitud de ±15%, inversa
    
    ### CALCULAR HUMEDAD ###
    hum_base = 55.0  # Humedad promedio
    ruido = _ruido() * 3.0  # Fluctuación moderada
    
    hum = hum_base + variacion + ruido
    hum = max(20, min(90, hum))  # Limitar a rango realista
    return round(hum, 1)

def obtener_luminosidad_simulada():
    """
    Simula luminosidad según hora del día con patrón natural
    Solo funciona si MODO_SIMULACION=True
    
    Patrón de luz natural:
    - 00:00-06:00: Noche (5-10%)
    - 06:00-08:00: Amanecer gradual (20-50%)
    - 08:00-12:00: Mañana creciente (50-85%)
    - 12:00-14:00: Mediodía máximo (85-95%)
    - 14:00-18:00: Tarde decreciente (70-40%)
    - 18:00-20:00: Atardecer gradual (40-10%)
    - 20:00-24:00: Noche (5-10%)
    
    Retorna: Luminosidad en % (float) o None si simulación desactivada
    """
    if not MODO_SIMULACION:
        return None
    
    hora_sim = _obtener_hora_simulada()
    if not hora_sim:
        return None
    
    hora, minuto, _ = hora_sim
    hora_decimal = hora + minuto / 60.0
    
    ### CÁLCULO POR FRANJAS HORARIAS ###
    if hora_decimal < 6:  # Noche
        luz = 5 + _ruido() * 3
    elif hora_decimal < 8:  # Amanecer
        progreso = (hora_decimal - 6) / 2
        luz = 20 + progreso * 30 + _ruido() * 5
    elif hora_decimal < 12:  # Mañana
        progreso = (hora_decimal - 8) / 4
        luz = 50 + progreso * 35 + _ruido() * 8
    elif hora_decimal < 14:  # Mediodía (pico máximo)
        luz = 85 + _ruido() * 10
    elif hora_decimal < 18:  # Tarde
        progreso = (hora_decimal - 14) / 4
        luz = 70 - progreso * 30 + _ruido() * 8
    elif hora_decimal < 20:  # Atardecer
        progreso = (hora_decimal - 18) / 2
        luz = 40 - progreso * 30 + _ruido() * 5
    else:  # Noche
        progreso = (hora_decimal - 20) / 4
        luz = 10 - progreso * 5 + _ruido() * 3
    
    # Asegurar rango válido 0-100%
    luz = max(0, min(100, luz))
    return round(luz, 1)

def calcular_confort_termico(temp, hum):
    """
    Calcula el índice de confort térmico combinando temperatura y humedad
    ✨ Maneja correctamente valores None y string ANOMALIA
    
    Clasificación mejorada:
    - Considera temperatura base
    - Ajusta por nivel de humedad (>70% húmedo, <30% seco)
    
    Categorías de confort:
    < 15°C: Frío / Frío Húmedo
    15-20°C: Fresco / Fresco Húmedo
    20-24°C: Confortable / Confortable Seco/Húmedo (zona ideal)
    24-28°C: Tibio / Tibio Húmedo
    28-32°C: Caluroso / Caluroso Húmedo
    >= 32°C: Muy Caluroso / Muy Caluroso Húmedo
    
    Args:
        temp: Temperatura en °C (float, None, o "ANOMALIA")
        hum: Humedad relativa en % (float, None, o "ANOMALIA")
    
    Retorna: String describiendo el confort, o "ANOMALIA" si datos inválidos
    """
    ### VALIDACIÓN DE ENTRADA ###
    if temp is None or hum is None:
        return ANOMALIA
    
    # Manejar string ANOMALIA
    if isinstance(temp, str) and temp == ANOMALIA:
        return ANOMALIA
    if isinstance(hum, str) and hum == ANOMALIA:
        return ANOMALIA
    
    # Convertir a números
    try:
        temp = float(temp)
        hum = float(hum)
    except (ValueError, TypeError):
        return ANOMALIA
    
    ### CLASIFICACIÓN DE HUMEDAD ###
    es_humedo = hum > 70  # Alta humedad
    es_seco = hum < 30    # Baja humedad
    
    ### CÁLCULO DE CONFORT SEGÚN TEMPERATURA ###
    if temp < 15:
        return "Frio Humedo" if es_humedo else "Frio"
    
    elif 15 <= temp < 20:
        return "Fresco Humedo" if es_humedo else "Fresco"
    
    elif 20 <= temp < 24:
        # Zona de confort óptima
        if es_seco:
            return "Confortable Seco"
        elif es_humedo:
            return "Confortable Humedo"
        else:
            return "Confortable"
    
    elif 24 <= temp < 28:
        return "Tibio Humedo" if es_humedo else "Tibio"
    
    elif 28 <= temp < 32:
        return "Caluroso Humedo" if es_humedo else "Caluroso"
    
    else:  # temp >= 32
        return "Muy Caluroso Humedo" if es_humedo else "Muy Caluroso"

def descripcion_luminosidad(pct):
    """
    Clasifica la luminosidad en categorías descriptivas en español
    ✨ Maneja valores None correctamente
    
    Categorías basadas en umbrales configurables:
    >= 80%: Muy Luminoso
    >= 60%: Luminoso
    >= 40%: Iluminación Media
    >= 20%: Tenue
    < 20%: Oscuro
    
    Args:
        pct: Porcentaje de luminosidad (0-100) o None
    
    Retorna: String descriptivo o "Desconocido" si valor inválido
    """
    if pct is None:
        return "Desconocido"
    
    try:
        pct = float(pct)
    except (ValueError, TypeError):
        return "Desconocido"
    
    ### CLASIFICACIÓN POR UMBRALES ###
    if pct >= UMBRAL_MUY_LUMINOSO:
        return "Muy Luminoso"
    elif pct >= UMBRAL_LUMINOSO:
        return "Luminoso"
    elif pct >= UMBRAL_MEDIO:
        return "Iluminacion Media"
    elif pct >= UMBRAL_TENUE:
        return "Tenue"
    else:
        return "Oscuro"

def estado_dia_noche(pct, umbral_dia=60.0, umbral_noche=30.0):
    """
    ⚠️ FUNCIÓN DEPRECADA - Mantener solo por compatibilidad
    
    Clasificación simple de luminosidad en DÍA/TARDE/NOCHE
    Se recomienda usar descripcion_luminosidad() para mejor granularidad
    
    Args:
        pct: Porcentaje de luminosidad
        umbral_dia: Límite para considerar "día" (default: 60%)
        umbral_noche: Límite para considerar "noche" (default: 30%)
    
    Retorna: "DIA", "TARDE", "NOCHE", o "DESCONOCIDO"
    """
    if pct is None:
        return "DESCONOCIDO"
    
    try:
        pct = float(pct)
    except (ValueError, TypeError):
        return "DESCONOCIDO"
    
    if pct >= umbral_dia:
        return "DIA"
    if pct <= umbral_noche:
        return "NOCHE"
    return "TARDE"

class MovingAverage:
    """
    Filtro de media móvil con buffer circular
    Compatible con MicroPython (sin librerías externas)
    
    Mantiene un buffer de tamaño fijo y calcula el promedio
    de los últimos N valores añadidos. Útil para suavizar
    lecturas ruidosas de sensores como el LDR.
    
    Ejemplo:
        ma = MovingAverage(size=5)
        for valor in lecturas:
            ma.add(valor)
            promedio = ma.avg()
    """
    def __init__(self, size=3):
        """
        Inicializa el filtro con buffer de tamaño específico
        
        Args:
            size: Número de valores a promediar (default: 3)
        """
        if size <= 0:
            size = 3
        self.size = int(size)
        self.buf = [0.0] * self.size  # Buffer circular
        self.count = 0  # Cantidad de valores válidos
        self.idx = 0    # Índice de escritura actual

    def add(self, v):
        """
        Añade un nuevo valor al buffer circular
        Los valores antiguos se sobrescriben automáticamente
        
        Args:
            v: Valor numérico a añadir (se convierte a float)
        """
        try:
            val = float(v)
        except Exception:
            return  # Ignorar valores no numéricos
        
        # Escribir en posición actual y avanzar índice
        self.buf[self.idx] = val
        self.idx = (self.idx + 1) % self.size  # Circular
        
        # Incrementar contador hasta llenar el buffer
        if self.count < self.size:
            self.count += 1

    def avg(self):
        """
        Calcula el promedio de los valores en el buffer
        
        Retorna: Promedio (float) o None si buffer vacío
        """
        if self.count == 0:
            return None
        
        # Sumar solo valores válidos
        s = 0.0
        for i in range(self.count):
            s += self.buf[i]
        
        return s / self.count
# sensors.py
# Sistema IoT - Módulo de Sensores
# Interfaces para LDR (luz) y DHT22 (temperatura/humedad)

from machine import ADC, Pin
import dht

# ==================== CONSTANTES ====================

VREF = 3.3  # Voltaje de referencia del ADC

# ==================== CLASE LDR ====================

class LDR:
    """
    Sensor de luz LDR (Light Dependent Resistor)
    
    Características:
    - Lectura ADC raw (0-65535)
    - Conversión a porcentaje (0-100%)
    - Conversión a voltaje (0-3.3V)
    - Salida digital opcional (DO)
    
    Uso:
        ldr = LDR(adc_pin=26, do_pin=27)
        pct = ldr.read_pct()      # Porcentaje 0-100%
        raw = ldr.read_raw()      # Valor ADC 0-65535
        vol = ldr.read_voltage()  # Voltaje 0-3.3V
    """
    
    def __init__(self, adc_pin=26, do_pin=None):
        """
        Inicializa el sensor LDR
        
        Args:
            adc_pin (int): Pin ADC (default: 26)
            do_pin (int, opcional): Pin digital comparador
        """
        self.adc = ADC(adc_pin)
        
        if do_pin is not None:
            self.do_pin = Pin(do_pin, Pin.IN)
        else:
            self.do_pin = None

    def read_raw(self):
        """
        Lee valor raw del ADC
        
        Returns:
            int: Valor 0-65535 (resolución 16 bits)
        """
        return int(self.adc.read_u16())

    def read_pct(self):
        """
        Lee luminosidad como porcentaje
        
        Returns:
            float: Porcentaje 0-100% (1 decimal)
        """
        raw = self.read_raw()
        return round((raw / 65535.0) * 100, 1)

    def read_voltage(self):
        """
        Lee el voltaje analógico del sensor
        
        Returns:
            float: Voltaje 0-3.3V (3 decimales)
        
        Diagnóstico:
            - ~0V: Sensor desconectado
            - ~3.3V: Señal saturada
            - 0.5-2.8V: Rango normal
        """
        raw = self.read_raw()
        return round((raw / 65535.0) * VREF, 3)

    def read_do(self):
        """
        Lee salida digital del comparador
        
        Returns:
            int: 0 o 1 si do_pin configurado, None si no
        
        Funcionamiento:
            - DO = 0: Luz por debajo del umbral
            - DO = 1: Luz por encima del umbral
            - Umbral ajustable por potenciómetro en módulo
        """
        if self.do_pin is None:
            return None
        return self.do_pin.value()

# ==================== CLASE DHT22 ====================

class DHT22Sensor:
    """
    Sensor DHT22 (temperatura y humedad)
    
    Especificaciones:
    - Temperatura: -40°C a +80°C (±0.5°C)
    - Humedad: 0-100% RH (±2-5%)
    - Protocolo: One-Wire digital
    - Frecuencia: Máximo cada 2 segundos
    
    Uso:
        dht = DHT22Sensor(pin=15)
        temp, hum = dht.read()
        
        if temp is not None:
            print(f"T: {temp}°C, H: {hum}%")
    """
    
    def __init__(self, pin=15):
        """
        Inicializa el sensor DHT22
        
        Args:
            pin (int): Pin One-Wire (default: 15)
        
        Hardware:
            DHT22 VCC  → 3.3V/5V
            DHT22 DATA → GPIO (pull-up 4.7kΩ)
            DHT22 GND  → GND
        """
        self.sensor = dht.DHT22(Pin(pin))

    def read(self):
        """
        Lee temperatura y humedad del sensor
        
        Returns:
            tuple: (temperatura, humedad) con 1 decimal
            tuple: (None, None) si hay error
        
        Causas de error:
            - Lecturas muy frecuentes (< 2s)
            - Sensor desconectado
            - Falta resistencia pull-up
            - Interferencia electromagnética
        
        Frecuencia recomendada:
            - Mínimo: 2 segundos entre lecturas
            - Óptimo: 5-10 segundos
        """
        try:
            self.sensor.measure()  # Inicia lectura (~5ms)
            
            t = round(self.sensor.temperature(), 1)
            h = round(self.sensor.humidity(), 1)
            
            return t, h
            
        except Exception:
            # Error en comunicación, checksum o timing
            return None, None
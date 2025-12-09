# actuators.py
# Sistema IoT - Módulo de Actuadores
# Controla LED y Buzzer con manejo robusto de errores

from machine import Pin
import utime

# ==================== CLASE LED ====================

class LED:
    """
    Controla un LED conectado a un pin GPIO
    
    Uso:
        led = LED(pin=14)
        led.on()         # Enciende
        led.blink(200)   # Parpadea 200ms
        led.off()        # Apaga
    """
    
    def __init__(self, pin=14):
        """
        Inicializa el LED
        
        Args:
            pin (int): Pin GPIO (default: 14)
        """
        self.pin = Pin(pin, Pin.OUT)

    def on(self):
        """Enciende el LED (HIGH)"""
        try:
            self.pin.value(1)
        except Exception:
            pass

    def off(self):
        """Apaga el LED (LOW)"""
        try:
            self.pin.value(0)
        except Exception:
            pass

    def blink(self, ms=200):
        """
        Parpadea el LED
        
        Args:
            ms (int): Duración en milisegundos
        """
        self.on()
        utime.sleep_ms(ms)
        self.off()

# ==================== CLASE BUZZER ====================

class Buzzer:
    """
    Controla un buzzer pasivo o activo
    
    Soporta:
    - PWM para buzzers pasivos (control de tono)
    - Fallback para buzzers activos (on/off simple)
    
    Uso:
        buzzer = Buzzer(pin=13)
        buzzer.beep(150, 2000, 80)  # 150ms, 2kHz, 80% volumen
    """
    
    def __init__(self, pin=13):
        """
        Inicializa el buzzer
        
        Args:
            pin (int): Pin GPIO (default: 13)
        """
        self.pin_num = pin
        self.pin = Pin(pin, Pin.OUT)
        self._pwm = None

    def on(self):
        """Activa el buzzer continuamente"""
        self.pin.value(1)

    def off(self):
        """Desactiva el buzzer y libera PWM"""
        self.pin.value(0)
        try:
            if self._pwm:
                self._pwm.deinit()
                self._pwm = None
        except Exception:
            self._pwm = None

    def beep(self, ms=150, freq=2000, volume=80):
        """
        Genera un beep con frecuencia y volumen específicos
        
        Args:
            ms (int): Duración en milisegundos (default: 150)
            freq (int): Frecuencia en Hz (default: 2000)
            volume (int): Volumen 0-100% (default: 80)
        
        Tonos recomendados:
            - 1500 Hz: Grave (confirmación)
            - 2000 Hz: Medio (notificación)
            - 2500 Hz: Agudo (alerta)
        
        Implementación:
            - Buzzer PASIVO: Usa PWM para generar frecuencia
            - Buzzer ACTIVO: Fallback on/off simple
        """
        try:
            from machine import PWM
            
            # Convierte volumen 0-100% a duty cycle 0-65535
            duty = int(max(0, min(100, volume)) / 100.0 * 65535)
            
            if duty == 0:
                return
            
            # Configura y ejecuta PWM
            self._pwm = PWM(Pin(self.pin_num))
            self._pwm.freq(int(freq))
            self._pwm.duty_u16(duty)
            utime.sleep_ms(int(ms))
            
            # Limpia recursos
            self._pwm.deinit()
            self._pwm = None
            
        except Exception:
            # Fallback para buzzers activos
            self.pin.value(1)
            utime.sleep_ms(int(ms))
            self.pin.value(0)
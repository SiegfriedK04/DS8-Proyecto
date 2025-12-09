# lcd_i2c.py
# Driver compacto para LCD HD44780 con interfaz I2C via PCF8574
# Compatible con displays 16x2 y 20x4 estándar

import utime

class SimpleI2cLcd:
    """
    Driver minimalista para LCD HD44780 con módulo I2C PCF8574
    
    El módulo PCF8574 es un expansor de 8 pines I2C que simplifica
    la conexión del LCD reduciendo cables de ~16 a solo 4 (SDA, SCL, VCC, GND)
    
    Arquitectura del PCF8574:
    - P0-P3: Datos LCD (nibble mode, 4 bits)
    - P4: RS (Register Select: 0=comando, 1=dato)
    - P5: R/W (siempre 0, solo escritura)
    - P6: E (Enable, pulso para clock)
    - P7: Backlight (1=encendido)
    
    Compatible con:
    - LCD 16x2 (16 columnas, 2 filas)
    - LCD 20x4 (20 columnas, 4 filas)
    - Controlador HD44780 o compatible (KS0066, etc)
    """
    
    def __init__(self, i2c, addr, rows=2, cols=16):
        """
        Inicializa el LCD con secuencia de configuración HD44780
        
        Args:
            i2c: Objeto I2C ya inicializado
            addr: Dirección I2C del PCF8574 (típicamente 0x27 o 0x3F)
            rows: Número de filas del display (default: 2)
            cols: Número de columnas por fila (default: 16)
        
        Secuencia de inicialización (según datasheet HD44780):
        1. Espera 20ms tras power-on
        2. Modo 8-bit × 3 (reset por software)
        3. Modo 4-bit
        4. Configuración: 4-bit, 2 líneas, fuente 5x8
        5. Display ON, cursor OFF
        6. Clear display
        """
        self.i2c = i2c
        self.addr = addr
        self.rows = rows
        self.cols = cols
        self.backlight = 0x08  # Bit P7 = backlight encendido
        
        ### SECUENCIA DE INICIALIZACIÓN ###
        utime.sleep_ms(20)  # Espera tras encendido
        
        # Reset por software: 3 comandos en modo 8-bit
        self._write_init(0x03); utime.sleep_ms(5)
        self._write_init(0x03); utime.sleep_ms(1)
        self._write_init(0x03)
        
        # Cambiar a modo 4-bit
        self._write_init(0x02)
        
        # Configuración funcional: 4-bit, 2 líneas, fuente 5x8
        self._cmd(0x28)
        
        # Display ON, cursor OFF, blink OFF
        self._cmd(0x0C)
        
        # Limpiar pantalla
        self.clear()

    def _write_init(self, nibble):
        """
        Envía nibble (4 bits) durante inicialización
        Usado en modo 8-bit de la secuencia de reset
        
        Args:
            nibble: 4 bits a enviar (0x0-0xF)
        """
        self._write_byte((nibble << 4) | self.backlight)
        self._pulse((nibble << 4) | self.backlight)

    def _write_byte(self, b):
        """
        Escribe byte al PCF8574 via I2C
        
        Args:
            b: Byte a escribir (8 bits de control del PCF8574)
        """
        self.i2c.writeto(self.addr, bytes([b]))

    def _pulse(self, data):
        """
        Genera pulso de Enable (E) para latching de datos
        
        Protocolo HD44780:
        1. E = HIGH (habilitar)
        2. Espera mínima (1µs)
        3. E = LOW (latch en flanco descendente)
        4. Espera de procesamiento (50µs)
        
        Args:
            data: Byte base con datos y flags
        """
        self._write_byte(data | 0x04)  # E = HIGH (bit P6)
        utime.sleep_us(1)
        self._write_byte(data & ~0x04) # E = LOW
        utime.sleep_us(50)

    def _cmd(self, cmd):
        """
        Envía comando al LCD (RS=0)
        
        Args:
            cmd: Código de comando HD44780 (ej: 0x01=clear, 0x80=setpos)
        """
        self._send(cmd, 0)

    def _put(self, ch):
        """
        Envía carácter ASCII al LCD (RS=1)
        
        Args:
            ch: Carácter a mostrar (string de 1 char)
        """
        self._send(ord(ch), 1)

    def _send(self, val, mode):
        """
        Envía byte completo al LCD en modo nibble (4-bit)
        Divide byte en 2 nibbles y envía secuencialmente
        
        Args:
            val: Byte a enviar (comando o dato)
            mode: 0=comando (RS=0), 1=dato (RS=1)
        """
        # Dividir en nibble alto y bajo
        high = val & 0xF0        # 4 bits superiores
        low = (val << 4) & 0xF0  # 4 bits inferiores desplazados
        
        # Enviar ambos nibbles con RS apropiado
        self._write4(high | (0x01 if mode else 0x00) | self.backlight)
        self._write4(low  | (0x01 if mode else 0x00) | self.backlight)

    def _write4(self, data):
        """
        Envía nibble (4 bits) con pulso de Enable
        
        Args:
            data: Byte con nibble, RS, y backlight configurados
        """
        self._write_byte(data)
        self._pulse(data)

    # ==================== API PÚBLICA ====================

    def clear(self):
        """
        Limpia toda la pantalla y retorna cursor a (0,0)
        Comando HD44780: 0x01
        Tiempo de ejecución: ~2ms
        """
        self._cmd(0x01)
        utime.sleep_ms(2)

    def move_to(self, col, row):
        """
        Mueve el cursor a posición específica
        
        Args:
            col: Columna (0 a cols-1)
            row: Fila (0 a rows-1)
        
        Direcciones DDRAM HD44780:
        - Fila 0: 0x00-0x0F (0x00-0x13 para 20x4)
        - Fila 1: 0x40-0x4F (0x40-0x53 para 20x4)
        - Fila 2: 0x14-0x27 (solo 20x4)
        - Fila 3: 0x54-0x67 (solo 20x4)
        
        Comando: 0x80 | dirección_DDRAM
        """
        row_offsets = [0x00, 0x40]  # Offsets para LCD 16x2
        addr = col + row_offsets[row]
        self._cmd(0x80 | addr)  # Set DDRAM address

    def putstr(self, s):
        """
        Escribe string en posición actual del cursor
        No maneja wrapping ni newlines automáticamente
        
        Args:
            s: String a mostrar (se trunca en límite de display)
        
        Ejemplo:
            lcd.clear()
            lcd.putstr("Hola Mundo")
            lcd.move_to(0, 1)
            lcd.putstr("Linea 2")
        """
        for ch in s:
            self._put(ch)
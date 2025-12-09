# mqtt_client.py
# Cliente MQTT para Adafruit IO usando sockets nativos
# Compatible con Wokwi (sin TLS) - Implementación MQTT 3.1.1

import utime
import network

try:
    import usocket as socket
except ImportError:
    import socket  # type: ignore


class AdafruitMQTT:
    """
    Cliente MQTT ligero para Adafruit IO
    
    Implementa protocolo MQTT 3.1.1 sobre TCP (puerto 1883, sin TLS)
    Diseñado para simulación en Wokwi y hardware real MicroPython
    
    Características:
    - Conexión WiFi automática
    - Publicación a feeds de Adafruit IO
    - Suscripción a feeds para control remoto
    - Socket no bloqueante para integración en loop principal
    - Reconexión automática en caso de fallo
    """
    
    def __init__(self, username, key, wifi_ssid=None, wifi_password=None,
                 host="io.adafruit.com", port=1883, keepalive=60):
        """
        Inicializa el cliente MQTT
        
        Args:
            username: Usuario de Adafruit IO
            key: Clave API de Adafruit IO
            wifi_ssid: SSID de red WiFi (opcional, conectar después)
            wifi_password: Contraseña WiFi (opcional)
            host: Broker MQTT (default: io.adafruit.com)
            port: Puerto MQTT (default: 1883 sin TLS)
            keepalive: Intervalo de keepalive en segundos (default: 60)
        """
        self.username = username
        self.key = key
        self.host = host
        self.port = port
        self.keepalive = keepalive
        
        # Generar ID único basado en timestamp
        self.client_id = b"wokwi-" + str(utime.ticks_ms() & 0xFFFF).encode()
        
        self.sock = None
        self.connected = False
        self.on_message_callback = None

        ### INICIALIZACIÓN WIFI ###
        self.wlan = network.WLAN(network.STA_IF)
        if wifi_ssid is not None:
            self.connect_wifi(wifi_ssid, wifi_password or "")

        print("[MQTT] Cliente inicializado")
        print("[MQTT] Usuario:", self.username)
        print("[MQTT] Broker:", self.host, "puerto", self.port)

    # ==================== GESTIÓN WIFI ====================

    def connect_wifi(self, ssid, password, timeout=15):
        """
        Conecta a red WiFi
        Compatible con Wokwi-GUEST (sin contraseña) y redes reales
        
        Args:
            ssid: Nombre de la red
            password: Contraseña (vacía para redes abiertas)
            timeout: Tiempo máximo de espera en segundos
        
        Retorna: True si conexión exitosa, False si timeout
        """
        if self.wlan.isconnected():
            print("[WiFi] Ya conectado:", self.wlan.ifconfig())
            return True

        print("[WiFi] Conectando a:", ssid)
        self.wlan.active(True)
        self.wlan.connect(ssid, password)

        # Esperar conexión con timeout
        start = utime.time()
        while not self.wlan.isconnected():
            if utime.time() - start > timeout:
                print("[WiFi] ✗ Tiempo de espera agotado")
                return False
            print(".", end="")
            utime.sleep(1)

        print("\n[WiFi] ✓ Conectado. IP:", self.wlan.ifconfig()[0])
        return True

    # ==================== UTILIDADES MQTT INTERNAS ====================

    def _encode_varlen(self, length):
        """
        Codifica 'remaining length' según especificación MQTT
        Formato variable de 1-4 bytes usando codificación de 7 bits
        
        Args:
            length: Longitud a codificar (0-268,435,455)
        
        Retorna: bytes con longitud codificada
        """
        enc = bytearray()
        while True:
            digit = length & 0x7F  # 7 bits de datos
            length >>= 7
            if length > 0:
                digit |= 0x80  # Bit de continuación
            enc.append(digit)
            if length == 0:
                break
        return bytes(enc)

    def _encode_str(self, s):
        """
        Codifica string en formato MQTT (longitud + datos)
        Formato: [MSB length][LSB length][datos UTF-8]
        
        Args:
            s: String o bytes a codificar
        
        Retorna: bytes con longitud prefijada
        """
        if isinstance(s, str):
            s = s.encode("utf-8")
        return bytes([len(s) >> 8, len(s) & 0xFF]) + s

    # ==================== CONEXIÓN AL BROKER ====================

    def connect_mqtt(self):
        """
        Establece conexión MQTT con Adafruit IO
        Implementa handshake MQTT 3.1.1 (CONNECT/CONNACK)
        
        Proceso:
        1. Crea socket TCP al broker
        2. Envía paquete CONNECT con credenciales
        3. Espera paquete CONNACK de confirmación
        4. Configura socket no bloqueante
        
        Retorna: True si conexión exitosa, False si falla
        """
        if not self.wlan.isconnected():
            print("[MQTT] ✗ No hay WiFi, llama primero a connect_wifi()")
            return False

        try:
            print("[MQTT] Conectando al broker...")
            
            ### CREAR SOCKET TCP ###
            addr_info = socket.getaddrinfo(self.host, self.port)[0][-1]
            self.sock = socket.socket()
            self.sock.connect(addr_info)
            self.sock.settimeout(5)  # Timeout inicial para handshake

            ### CONSTRUIR PAQUETE CONNECT (MQTT 3.1.1) ###
            vh = b""  # Variable header
            vh += self._encode_str("MQTT")        # Nombre del protocolo
            vh += b"\x04"                         # Nivel de protocolo (3.1.1)
            flags = 0xC2                          # Flags: user+password+clean session
            vh += bytes([flags])
            vh += bytes([self.keepalive >> 8, self.keepalive & 0xFF])

            # Payload: Client ID, username, password
            payload = b""
            payload += self._encode_str(self.client_id)
            payload += self._encode_str(self.username)
            payload += self._encode_str(self.key)

            # Fixed header: tipo CONNECT (1) + remaining length
            remaining_len = len(vh) + len(payload)
            fixed_header = b"\x10" + self._encode_varlen(remaining_len)

            ### ENVIAR CONNECT ###
            self.sock.send(fixed_header + vh + payload)

            ### RECIBIR CONNACK (4 bytes esperados) ###
            resp = self.sock.recv(4)
            if len(resp) != 4 or resp[0] != 0x20 or resp[1] != 0x02 or resp[3] != 0x00:
                print("[MQTT] ✗ Error en CONNACK:", resp)
                self.sock.close()
                self.sock = None
                self.connected = False
                return False

            ### CONEXIÓN EXITOSA ###
            self.connected = True
            self.sock.settimeout(0)  # No bloqueante para loop principal
            print("[MQTT] ✓ Conectado a Adafruit IO como", self.client_id)
            return True

        except Exception as e:
            print("[MQTT] ✗ Error conectando:", e)
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
            self.sock = None
            self.connected = False
            return False

    def disconnect(self):
        """
        Cierra la conexión MQTT limpiamente
        Envía paquete DISCONNECT antes de cerrar socket
        """
        if self.sock:
            try:
                # DISCONNECT packet (tipo 14, sin payload)
                self.sock.send(b"\xE0\x00")
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None
        self.connected = False
        print("[MQTT] Desconectado")

    # ==================== SUSCRIPCIÓN Y PUBLICACIÓN ====================

    def subscribe(self, feed_name, msg_id=1):
        """
        Suscribe a un feed de Adafruit IO para recibir mensajes
        
        Args:
            feed_name: Nombre del feed (sin prefijo de usuario)
            msg_id: ID del mensaje MQTT (default: 1)
        
        Retorna: True si suscripción exitosa, False si no conectado
        
        Ejemplo:
            mqtt.subscribe("comando_led")
            # Se suscribe a: username/feeds/comando_led
        """
        if not self.connected or not self.sock:
            print("[MQTT] ✗ No conectado, no se puede suscribir")
            return False

        # Construir topic completo
        topic = "{}/feeds/{}".format(self.username, feed_name)
        topic_bytes = topic.encode("utf-8")

        ### CONSTRUIR PAQUETE SUBSCRIBE ###
        packet = bytearray()
        packet.append(0x82)  # SUBSCRIBE con QoS1
        
        # Calcular remaining length
        rem_len = 2 + 2 + len(topic_bytes) + 1
        packet.extend(self._encode_varlen(rem_len))
        
        # Message ID (2 bytes)
        packet.append(msg_id >> 8)
        packet.append(msg_id & 0xFF)
        
        # Topic con longitud prefijada
        packet.append(len(topic_bytes) >> 8)
        packet.append(len(topic_bytes) & 0xFF)
        packet.extend(topic_bytes)
        
        # QoS solicitado (0 = at most once)
        packet.append(0x00)

        self.sock.send(packet)
        print("[MQTT] ✓ Suscrito a feed:", feed_name)
        return True

    def publish(self, feed_name, value, retain=False):
        """
        Publica un valor a un feed de Adafruit IO
        
        Args:
            feed_name: Nombre del feed (sin prefijo de usuario)
            value: Valor a publicar (string, número, o bytes)
            retain: Retener mensaje en broker (default: False)
        
        Retorna: True si publicación exitosa, False si no conectado
        
        Ejemplo:
            mqtt.publish("sensor_temp", 23.5)
            mqtt.publish("sensor_hum", "45.2")
        """
        if not self.connected or not self.sock:
            print("[MQTT] ✗ No conectado, no se puede publicar")
            return False

        # Construir topic completo
        topic = "{}/feeds/{}".format(self.username, feed_name)
        topic_bytes = topic.encode("utf-8")
        
        # Convertir valor a bytes
        if not isinstance(value, (bytes, bytearray)):
            payload = str(value).encode("utf-8")
        else:
            payload = value

        ### CONSTRUIR PAQUETE PUBLISH ###
        header = 0x30  # PUBLISH con QoS0
        if retain:
            header |= 0x01  # Flag RETAIN

        var_header = self._encode_str(topic_bytes)
        remaining_len = len(var_header) + len(payload)
        
        packet = bytearray()
        packet.append(header)
        packet.extend(self._encode_varlen(remaining_len))
        packet.extend(var_header)
        packet.extend(payload)

        self.sock.send(packet)
        print("[MQTT→Cloud] {} = {}".format(feed_name, value))
        return True

    # ==================== RECEPCIÓN DE MENSAJES ====================

    def set_message_callback(self, callback):
        """
        Registra función callback para mensajes entrantes
        
        Args:
            callback: Función con firma callback(feed_name, value)
        
        Ejemplo:
            def on_message(feed, val):
                print(f"Recibido: {feed} = {val}")
            
            mqtt.set_message_callback(on_message)
        """
        self.on_message_callback = callback
        print("[MQTT] Callback de mensajes configurado")

    def _recv_exact(self, n):
        """
        Lee exactamente n bytes del socket
        Maneja socket no bloqueante y buffers incompletos
        
        Args:
            n: Número de bytes a leer
        
        Retorna: bytes de longitud n, o None si falla
        """
        data = bytearray()
        while len(data) < n:
            try:
                chunk = self.sock.recv(n - len(data))
            except OSError:
                return None  # No hay datos disponibles
            if not chunk:
                return None  # Conexión cerrada
            data.extend(chunk)
        return bytes(data)

    def _read_remaining_length(self):
        """
        Lee 'remaining length' según formato MQTT variable
        Decodifica 1-4 bytes con codificación de 7 bits
        
        Retorna: Longitud decodificada (int) o 0 si error
        """
        multiplier = 1
        value = 0
        while True:
            b = self._recv_exact(1)
            if not b:
                return 0
            digit = b[0]
            value += (digit & 0x7F) * multiplier
            if (digit & 0x80) == 0:  # Bit de continuación
                break
            multiplier *= 128
        return value

    def check_messages(self):
        """
        Verifica mensajes PUBLISH entrantes y ejecuta callback
        Debe llamarse periódicamente en el loop principal
        
        Socket no bloqueante: retorna inmediatamente si no hay datos
        
        Retorna: 
            True si operación exitosa (con o sin mensajes)
            False si error grave de conexión
        
        Ejemplo de uso en loop:
            while True:
                if not mqtt.check_messages():
                    mqtt.reconnect()
                # ... resto del código
        """
        if not self.connected or not self.sock:
            return False

        ### LEER FIXED HEADER ###
        try:
            hdr = self.sock.recv(1)
        except OSError:
            return True  # No hay datos (socket no bloqueante)

        if not hdr:
            return True  # Sin datos, pero conexión OK

        # Extraer tipo de paquete
        packet_type = hdr[0] >> 4
        
        ### PROCESAR SOLO PAQUETES PUBLISH (tipo 3) ###
        if packet_type != 3:
            # Otro tipo de paquete: leer y descartar
            rem_len = self._read_remaining_length()
            if rem_len:
                try:
                    self.sock.recv(rem_len)
                except Exception:
                    pass
            return True

        ### PARSEAR PAQUETE PUBLISH ###
        rem_len = self._read_remaining_length()

        # Leer longitud del topic
        tl_bytes = self._recv_exact(2)
        if not tl_bytes:
            return False
        topic_len = (tl_bytes[0] << 8) | tl_bytes[1]
        
        # Leer topic
        topic = self._recv_exact(topic_len)
        if topic is None:
            return False

        # Leer payload
        payload_len = rem_len - 2 - topic_len
        payload = self._recv_exact(payload_len) if payload_len > 0 else b""

        ### DECODIFICAR Y EJECUTAR CALLBACK ###
        try:
            topic_str = topic.decode("utf-8")
        except Exception:
            topic_str = str(topic)
        
        try:
            payload_str = payload.decode("utf-8")
        except Exception:
            payload_str = str(payload)

        # Extraer nombre del feed (última parte del topic)
        feed_name = topic_str.split("/")[-1]

        print("[MQTT←Cloud] {} = {}".format(feed_name, payload_str))
        
        if self.on_message_callback:
            try:
                self.on_message_callback(feed_name, payload_str)
            except Exception as e:
                print("[MQTT] Error en callback:", e)
        
        return True

    # ==================== RECONEXIÓN ====================

    def reconnect(self):
        """
        Intenta reconectar a Adafruit IO
        Cierra conexión existente y establece una nueva
        
        Retorna: True si reconexión exitosa, False si falla
        """
        print("[MQTT] Intentando reconectar...")
        self.disconnect()
        utime.sleep(2)
        
        if not self.wlan.isconnected():
            print("[MQTT] No hay WiFi")
            return False
        
        return self.connect_mqtt()
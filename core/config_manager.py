import json
import os

class ConfigManager:
    def __init__(self, archivo="config.json"):
        self.archivo = archivo
        self.configuracion = {
            "puerto_com": "COM3",
            "baudrate": 9600,
            
            # Configuración de Cámara
            "tipo_camara": "USB",  # "USB" o "IP_RTSP"
            "camara_index": 0,
            "camara_ip": "192.168.1.64",
            "camara_puerto": 554,
            "camara_usuario": "admin",
            "camara_password": "",
            "camara_ruta_stream": "/Streaming/Channels/101",
            "camara_url_personalizada": "",
            
            "materiales": ["Caolín", "Plata", "Oro", "Cobre", "Otro Mineral"]
        }
        self.cargar()

    def cargar(self):
        """Carga la configuración desde el archivo JSON si existe."""
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    self.configuracion.update(datos)
            except Exception as e:
                print(f"[CONFIG] Error al cargar configuración: {e}")
        else:
            self.guardar()

    def guardar(self):
        """Guarda la configuración actual en el archivo JSON."""
        try:
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(self.configuracion, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CONFIG] Error al guardar configuración: {e}")

    def obtener(self, clave, defecto=None):
        """Obtiene un valor de la configuración."""
        return self.configuracion.get(clave, defecto)

    def actualizar(self, clave, valor):
        """Actualiza un valor y guarda en el archivo."""
        self.configuracion[clave] = valor
        self.guardar()

    def obtener_fuente_camara(self):
        """
        Retorna la fuente lista para OpenCV:
        - Un entero (0, 1, ...) para USB.
        - Una URL string ('rtsp://...' o 'http://...') para Cámara IP.
        """
        tipo = self.obtener("tipo_camara", "USB")
        if tipo == "USB":
            try:
                return int(self.obtener("camara_index", 0))
            except ValueError:
                return 0
        else:
            # Si hay una URL personalizada, usarla directamente
            url_custom = self.obtener("camara_url_personalizada", "").strip()
            if url_custom:
                return url_custom
            
            # Construir URL RTSP estándar
            ip = self.obtener("camara_ip", "192.168.1.64").strip()
            puerto = self.obtener("camara_puerto", 554)
            usuario = self.obtener("camara_usuario", "").strip()
            password = self.obtener("camara_password", "").strip()
            ruta = self.obtener("camara_ruta_stream", "/Streaming/Channels/101").strip()
            if not ruta.startswith("/"):
                ruta = "/" + ruta

            if usuario and password:
                return f"rtsp://{usuario}:{password}@{ip}:{puerto}{ruta}"
            else:
                return f"rtsp://{ip}:{puerto}{ruta}"

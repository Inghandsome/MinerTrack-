import serial
import time
import random
import threading
import re
from collections import deque

class LectorBascula:
    """
    Clase para manejar la lectura del indicador Transcell TI-1680.
    Permite trabajar en modo 'físico' o en modo 'simulación'.
    Incluye algoritmo de detección de estabilidad para captura autónoma.
    """
    
    def __init__(self, puerto='COM3', baudrate=9600, simulacion=True, umbral_minimo=1000.0, tolerancia_estabilidad=20.0):
        self.puerto = puerto
        self.baudrate = baudrate
        self.simulacion = simulacion
        self.umbral_minimo = umbral_minimo  # Peso mínimo para considerar que hay un camión (kg)
        self.tolerancia_estabilidad = tolerancia_estabilidad  # Máxima variación permitida para considerarse estable (kg)
        
        self.conexion = None
        self.conectado = False
        self.peso_actual = 0.0
        self.es_estable = False
        
        # Historial de lecturas para cálculo de estabilidad
        self._buffer_lecturas = deque(maxlen=8)
        self._tiempo_estable_inicio = None
        
        self._hilo_lectura = None
        self._detener = False

    def conectar(self):
        if self.simulacion:
            print(f"[SIMULACIÓN] Conectado a la báscula virtual en {self.puerto}")
            self.conectado = True
            self._iniciar_hilo_lectura()
            return True
        
        try:
            # Configuración típica para Transcell TI-1680 (8, N, 1)
            self.conexion = serial.Serial(
                port=self.puerto,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            if self.conexion.is_open:
                self.conectado = True
                print(f"[ÉXITO] Conectado a la báscula física en {self.puerto}")
                self._iniciar_hilo_lectura()
                return True
        except Exception as e:
            print(f"[ERROR] No se pudo conectar a la báscula en {self.puerto}: {e}")
            self.conectado = False
            return False

    def desconectar(self):
        self._detener = True
        if self._hilo_lectura and self._hilo_lectura.is_alive():
            self._hilo_lectura.join(timeout=1.0)
            
        if not self.simulacion and self.conexion and self.conexion.is_open:
            self.conexion.close()
        self.conectado = False
        print("[INFO] Desconectado de la báscula.")

    def _iniciar_hilo_lectura(self):
        """Inicia un hilo en segundo plano para leer datos constantemente."""
        self._detener = False
        self._hilo_lectura = threading.Thread(target=self._leer_datos, daemon=True)
        self._hilo_lectura.start()

    def _leer_datos(self):
        """Ciclo infinito que lee los datos del puerto serial o genera los simulados."""
        peso_base = 0.0
        incremento = 2500.0
        
        while not self._detener:
            if self.simulacion:
                # Simula cómo un camión entra y se estabiliza alrededor de ~32,000 kg
                if peso_base < 32000.0:
                    peso_base += incremento
                    time.sleep(0.3)
                else:
                    # Una vez que llega, añade pequeña fluctuación natural de la báscula
                    time.sleep(0.2)

                fluctuacion = random.uniform(-6.0, 6.0)
                peso_leido = max(0.0, peso_base + fluctuacion)
                self._procesar_nueva_lectura(peso_leido)
            else:
                if self.conexion and self.conexion.in_waiting > 0:
                    try:
                        linea = self.conexion.readline().decode('ascii', errors='ignore').strip()
                        peso_leido = self._parsear_peso(linea)
                        self._procesar_nueva_lectura(peso_leido)
                    except Exception as e:
                        print(f"[ERROR LECTURA] Fallo al leer trama: {e}")
                time.sleep(0.1)

    def _procesar_nueva_lectura(self, peso):
        """Actualiza el peso y evalúa si está en estado ESTABLE."""
        self.peso_actual = peso
        self._buffer_lecturas.append(peso)
        
        # Evaluar estabilidad
        if len(self._buffer_lecturas) >= 5 and self.peso_actual >= self.umbral_minimo:
            diferencia = max(self._buffer_lecturas) - min(self._buffer_lecturas)
            if diferencia <= self.tolerancia_estabilidad:
                if self._tiempo_estable_inicio is None:
                    self._tiempo_estable_inicio = time.time()
                elif time.time() - self._tiempo_estable_inicio >= 1.2:
                    # Ha estado dentro de tolerancia por más de 1.2 segundos
                    self.es_estable = True
            else:
                self.es_estable = False
                self._tiempo_estable_inicio = None
        else:
            self.es_estable = False
            self._tiempo_estable_inicio = None

    def _parsear_peso(self, trama_serial):
        """
        Extrae el peso numérico de la cadena que manda el Transcell TI-1680.
        """
        try:
            numeros = re.findall(r"[-+]?\d*\.\d+|\d+", trama_serial)
            if numeros:
                return float(numeros[0])
        except Exception:
            pass
        return 0.0

    def obtener_peso(self):
        """Retorna el peso limpio redondeado a 2 decimales para la Interfaz Gráfica."""
        return round(self.peso_actual, 2)

    def obtener_estado_completo(self):
        """
        Retorna (peso, es_estable, hay_vehiculo).
        hay_vehiculo = True si peso >= umbral_minimo.
        """
        peso = round(self.peso_actual, 2)
        hay_vehiculo = peso >= self.umbral_minimo
        return peso, self.es_estable, hay_vehiculo

    def forzar_peso_simulado(self, nuevo_peso):
        """Permite a la interfaz simular que un camión entra o sale manualmente."""
        self.peso_actual = nuevo_peso
        self._buffer_lecturas.clear()
        self._buffer_lecturas.append(nuevo_peso)
        self.es_estable = nuevo_peso >= self.umbral_minimo


# ==========================================
# CÓDIGO DE PRUEBA RÁPIDA
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO PRUEBA DEL MÓDULO BÁSCULA CON ESTABILIDAD ---")
    bascula = LectorBascula(simulacion=True)
    if bascula.conectar():
        for i in range(15):
            peso, estable, vehiculo = bascula.obtener_estado_completo()
            print(f"[{i+1:02d}s] Peso: {peso:,.2f} kg | Estable: {'🟢 SI' if estable else '🔴 NO'} | Camión: {'🚛 SI' if vehiculo else '⚪ NO'}")
            time.sleep(1)
        bascula.desconectar()
        print("Prueba finalizada.")

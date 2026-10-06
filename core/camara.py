import cv2
import easyocr
import threading
import time
import numpy as np
from PIL import Image, ImageTk

class LectorPlacas:
    """
    Controlador de Cámara (USB o IP/RTSP) y OCR en Tiempo Real.
    - Mantiene stream de video continuo a ~30 FPS para mostrar en la GUI.
    - Soporta Webcams USB locales (0, 1, 2...) y Cámaras IP (RTSP / HTTP).
    - Ejecuta OCR periódico en segundo plano para detección instantánea sin pausas.
    - Dibuja un recuadro verde en vivo sobre la placa detectada.
    """
    def __init__(self, fuente_camara=0):
        self.fuente_camara = fuente_camara  # Puede ser int (0, 1) o str ("rtsp://...")
        self.lector_ocr = None
        self.modelo_listo = False
        
        self.camara = None
        self.camara_activa = False
        self.ultimo_frame = None
        
        # Datos de la última placa reconocida
        self.ultima_placa = ""
        self.confianza_ultima_placa = 0.0
        self.tiempo_ultima_placa = 0.0
        self.caja_placa_actual = None  # Coordenadas (x, y, w, h) para dibujo
        
        # Hilos de ejecución
        self._detener = False
        self._bloqueo_frame = threading.Lock()
        
        # 1. Iniciar carga del modelo IA
        self._hilo_ia = threading.Thread(target=self._cargar_modelo, daemon=True)
        self._hilo_ia.start()
        
        # 2. Iniciar captura de video
        self._iniciar_camara()

    def _cargar_modelo(self):
        print("[OCR] Cargando modelo de Inteligencia Artificial (EasyOCR)...")
        try:
            self.lector_ocr = easyocr.Reader(['es', 'en'], gpu=False)
            self.modelo_listo = True
            print("[OCR] Modelo IA cargado exitosamente.")
            
            # Iniciar hilo de OCR continuo una vez cargado el modelo
            self._hilo_ocr = threading.Thread(target=self._bucle_ocr_continuo, daemon=True)
            self._hilo_ocr.start()
        except Exception as e:
            print(f"[OCR ERROR] Fallo al cargar EasyOCR: {e}")

    def _iniciar_camara(self):
        """Inicia el hilo de captura de video."""
        self._detener = False
        self._hilo_video = threading.Thread(target=self._bucle_captura_video, daemon=True)
        self._hilo_video.start()

    def _abrir_dispositivo(self, fuente):
        """Intenta abrir la cámara sea por índice numérico (USB) o URL RTSP/HTTP."""
        try:
            # Si es número en formato string, convertirlo a int
            if isinstance(fuente, str) and fuente.isdigit():
                fuente = int(fuente)
            
            # Abrir con VideoCapture
            cap = cv2.VideoCapture(fuente)
            return cap
        except Exception as e:
            print(f"[CÁMARA ERROR] No se pudo inicializar fuente {fuente}: {e}")
            return None

    def _bucle_captura_video(self):
        """Hilo dedicado a leer frames de la cámara continuamente a alta velocidad."""
        try:
            self.camara = self._abrir_dispositivo(self.fuente_camara)
            if self.camara and self.camara.isOpened():
                self.camara_activa = True
                print(f"[CÁMARA] Conectada exitosamente a la fuente: {self.fuente_camara}")
            else:
                self.camara_activa = False
                print(f"[CÁMARA AVISO] No se pudo abrir la fuente: {self.fuente_camara}")
        except Exception as e:
            self.camara_activa = False
            print(f"[CÁMARA ERROR] Error al abrir cámara: {e}")

        while not self._detener:
            if self.camara and self.camara.isOpened():
                ret, frame = self.camara.read()
                if ret:
                    with self._bloqueo_frame:
                        self.ultimo_frame = frame.copy()
                        self.camara_activa = True
                else:
                    self.camara_activa = False
                    time.sleep(0.1)
            else:
                self.camara_activa = False
                time.sleep(0.2)
            time.sleep(0.02)  # ~40-50 FPS

    def _bucle_ocr_continuo(self):
        """Hilo en segundo plano que analiza el video periódicamente buscando placas."""
        while not self._detener:
            if not self.modelo_listo or not self.camara_activa:
                time.sleep(0.4)
                continue

            frame_a_procesar = None
            with self._bloqueo_frame:
                if self.ultimo_frame is not None:
                    frame_a_procesar = self.ultimo_frame.copy()

            if frame_a_procesar is not None:
                try:
                    # Reducimos resolución para acelerar el procesamiento de OCR
                    h, w = frame_a_procesar.shape[:2]
                    escala = 640.0 / max(w, h) if max(w, h) > 640 else 1.0
                    if escala < 1.0:
                        frame_ocr = cv2.resize(frame_a_procesar, (int(w * escala), int(h * escala)))
                    else:
                        frame_ocr = frame_a_procesar

                    resultados = self.lector_ocr.readtext(frame_ocr)
                    
                    placa_encontrada = ""
                    confianza_max = 0.0
                    caja_detectada = None

                    for (bbox, texto, prob) in resultados:
                        texto_limpio = "".join(c for c in texto if c.isalnum()).upper()
                        # Formato típico de placa vehicular (entre 4 y 8 caracteres)
                        if 4 <= len(texto_limpio) <= 8 and prob > 0.35:
                            placa_encontrada = texto_limpio
                            confianza_max = prob
                            
                            # Ajustar coordenadas al tamaño original si hubo escala
                            if escala < 1.0:
                                pts = np.array(bbox) / escala
                            else:
                                pts = np.array(bbox)
                            
                            x_min = int(min(p[0] for p in pts))
                            y_min = int(min(p[1] for p in pts))
                            x_max = int(max(p[0] for p in pts))
                            y_max = int(max(p[1] for p in pts))
                            caja_detectada = (x_min, y_min, x_max - x_min, y_max - y_min)
                            break

                    if placa_encontrada:
                        self.ultima_placa = placa_encontrada
                        self.confianza_ultima_placa = confianza_max
                        self.tiempo_ultima_placa = time.time()
                        self.caja_placa_actual = caja_detectada
                    else:
                        if time.time() - self.tiempo_ultima_placa > 2.0:
                            self.caja_placa_actual = None

                except Exception as e:
                    print(f"[OCR CONTINUO ERROR] {e}")

            time.sleep(0.35)  # Analizar ~3 veces por segundo

    def obtener_frame_para_tkinter(self, ancho_deseado=360, alto_deseado=230):
        """
        Retorna una imagen PhotoImage lista para renderizarse en Tkinter.
        """
        with self._bloqueo_frame:
            if self.ultimo_frame is not None and self.camara_activa:
                frame = self.ultimo_frame.copy()
            else:
                frame = None

        if frame is None:
            # Crear un cuadro oscuro elegante de "Cámara sin señal"
            img_vacia = np.zeros((alto_deseado, ancho_deseado, 3), dtype=np.uint8)
            img_vacia[:] = (46, 52, 64)  # Color #2E3440
            cv2.putText(img_vacia, "CAMARA SIN SENAL", (20, alto_deseado // 2 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (136, 192, 208), 2)
            cv2.putText(img_vacia, "Verifica conexion en Configuracion", (20, alto_deseado // 2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (216, 222, 233), 1)
            frame_rgb = cv2.cvtColor(img_vacia, cv2.COLOR_BGR2RGB)
        else:
            # Si hay una placa detectada recientemente, dibujar recuadro y etiqueta
            if self.caja_placa_actual and (time.time() - self.tiempo_ultima_placa < 2.0):
                x, y, w, h = self.caja_placa_actual
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                texto_label = f"{self.ultima_placa} ({self.confianza_ultima_placa*100:.0f}%)"
                cv2.putText(frame, texto_label, (x, max(25, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            frame_redim = cv2.resize(frame, (ancho_deseado, alto_deseado))
            frame_rgb = cv2.cvtColor(frame_redim, cv2.COLOR_BGR2RGB)

        img_pil = Image.fromarray(frame_rgb)
        return ImageTk.PhotoImage(image=img_pil)

    def obtener_placa_actual(self, max_antiguedad_seg=4.0):
        """Retorna la última placa si fue detectada recientemente."""
        if self.ultima_placa and (time.time() - self.tiempo_ultima_placa <= max_antiguedad_seg):
            return self.ultima_placa, self.confianza_ultima_placa
        return "", 0.0

    def forzar_placa_simulada(self, texto_placa):
        self.ultima_placa = texto_placa.upper()
        self.confianza_ultima_placa = 0.98
        self.tiempo_ultima_placa = time.time()

    def limpiar_placa_actual(self):
        self.ultima_placa = ""
        self.caja_placa_actual = None
        self.tiempo_ultima_placa = 0.0

    def cambiar_camara(self, nueva_fuente):
        """Cambia dinámicamente el dispositivo de cámara (USB o IP)."""
        self.fuente_camara = nueva_fuente
        if self.camara and self.camara.isOpened():
            self.camara.release()
        try:
            self.camara = self._abrir_dispositivo(self.fuente_camara)
            self.camara_activa = (self.camara is not None and self.camara.isOpened())
            print(f"[CÁMARA] Cambio de fuente a {self.fuente_camara} -> {'Éxito' if self.camara_activa else 'Fallo'}")
        except Exception as e:
            print(f"[CÁMARA] Error al cambiar dispositivo: {e}")

    @staticmethod
    def probar_fuente(fuente):
        """
        Prueba rápida estática para verificar si una fuente de video responde.
        Retorna (True, "Conectado") o (False, "Error").
        """
        try:
            if isinstance(fuente, str) and fuente.isdigit():
                fuente = int(fuente)
            cap = cv2.VideoCapture(fuente)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return True, "Cámara detectada y transmitiendo video correctamente."
                else:
                    return False, "La cámara abrió el puerto pero no entregó imagen."
            else:
                return False, "No se pudo conectar a la cámara (Verifica IP, puerto o índice)."
        except Exception as e:
            return False, f"Error al probar cámara: {e}"

    def cerrar(self):
        """Libera todos los recursos."""
        self._detener = True
        if self.camara and self.camara.isOpened():
            self.camara.release()
        print("[CÁMARA] Recursos de video liberados.")

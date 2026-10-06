import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
try:
    import winsound
except ImportError:
    winsound = None

from core.bascula import LectorBascula
from core.database import GestorBaseDatos
from core.camara import LectorPlacas
from core.config_manager import ConfigManager
from core.ticket_generator import GeneradorTicket
from gui.historial_window import VentanaHistorial
from gui.dashboard_window import VentanaDashboard
from gui.config_window import VentanaConfiguracion

class AplicacionMinerTrack:
    # Estados del ciclo autónomo
    ESTADO_ESPERANDO = "ESPERANDO"
    ESTADO_ESTABILIZANDO = "ESTABILIZANDO"
    ESTADO_DISPARO = "DISPARO"
    ESTADO_ATENDIDO = "ATENDIDO"

    def __init__(self, root, operador="Operador"):
        self.root = root
        self.root.title("MinerTrack - Sistema de Pesaje Autónomo")
        self.root.geometry("1080x760")
        self.root.configure(bg="#2E3440")
        
        # Operador en turno (viene del Login)
        self.operador = operador
        
        # Cargar configuración
        self.config = ConfigManager()
        
        # Variables de pesaje
        self.peso_tara = 0.0
        self.peso_bruto = 0.0
        self.peso_neto = 0.0
        self.modo_automatico = tk.BooleanVar(value=True)
        self.estado_ciclo = self.ESTADO_ESPERANDO
        
        # Conexión con la báscula
        self.bascula = LectorBascula(
            puerto=self.config.obtener("puerto_com"), 
            baudrate=self.config.obtener("baudrate"), 
            simulacion=True
        )
        self.bascula.conectar()
        
        # Conexión con MongoDB
        self.bd = GestorBaseDatos()
        if not self.bd.conectar():
            messagebox.showwarning("Aviso BD", "No se pudo conectar a MongoDB de forma local. Verifica que el servicio esté corriendo.")
            
        # Lector OCR y Cámara en tiempo real (USB o IP/RTSP según configuración)
        fuente_cam = self.config.obtener_fuente_camara()
        self.lector_ocr = LectorPlacas(fuente_camara=fuente_cam)
        self.generador_ticket = GeneradorTicket()
        
        # Guardamos referencia a la imagen de video para evitar garbage collection
        self._foto_video = None
        
        self.crear_interfaz()
        
        # Iniciar bucles periódicos
        self.actualizar_peso_en_vivo()
        self.actualizar_video_en_vivo()
        self.evaluar_ciclo_autonomo()

        # Cerrar limpiamente
        self.root.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def crear_interfaz(self):
        # ═══════════════════════════════════════════════════
        #  HEADER SUPERIOR
        # ═══════════════════════════════════════════════════
        header_frame = tk.Frame(self.root, bg="#2E3440")
        header_frame.pack(fill="x", padx=15, pady=8)

        btn_config = tk.Button(header_frame, text="⚙️ CONFIGURACIÓN", font=("Helvetica", 11, "bold"), 
                               bg="#4C566A", fg="white", command=self._abrir_configuracion)
        btn_config.pack(side="left", padx=5)

        # Switch de Modo Automático
        chk_auto = tk.Checkbutton(header_frame, text="⚡ CAPTURA 100% AUTOMÁTICA", 
                                  variable=self.modo_automatico,
                                  font=("Helvetica", 11, "bold"), bg="#3B4252", fg="#A3BE8C",
                                  selectcolor="#2E3440", activebackground="#3B4252", activeforeground="#A3BE8C",
                                  padx=10, pady=4, relief="ridge", bd=2)
        chk_auto.pack(side="left", padx=20)

        btn_historial = tk.Button(header_frame, text="📊 HISTORIAL", font=("Helvetica", 11, "bold"), 
                                  bg="#A3BE8C", fg="#2E3440", command=self.abrir_historial)
        btn_historial.pack(side="right", padx=5)
        
        btn_stats = tk.Button(header_frame, text="📈 ESTADÍSTICAS", font=("Helvetica", 11, "bold"), 
                              bg="#81A1C1", fg="#2E3440", command=self._abrir_dashboard)
        btn_stats.pack(side="right", padx=5)

        # ═══════════════════════════════════════════════════
        #  DISPLAY DE PESO EN VIVO + ESTADO
        # ═══════════════════════════════════════════════════
        frame_display = tk.Frame(self.root, bg="#3B4252", bd=4, relief="ridge")
        frame_display.pack(pady=(5, 10), padx=25, fill="x")

        top_disp = tk.Frame(frame_display, bg="#3B4252")
        top_disp.pack(fill="x", padx=10, pady=(6, 0))

        tk.Label(top_disp, text="BÁSCULA CAMIONERA (TI-1680)", fg="#D8DEE9", bg="#3B4252", 
                 font=("Helvetica", 12, "bold")).pack(side="left")

        self.lbl_indicador_estable = tk.Label(top_disp, text="⚪ ESPERANDO VEHÍCULO", fg="#ECEFF4", bg="#4C566A",
                                              font=("Helvetica", 10, "bold"), padx=10, pady=2)
        self.lbl_indicador_estable.pack(side="right")

        self.lbl_peso_vivo = tk.Label(frame_display, text="0.00", fg="#A3BE8C", bg="#2E3440", 
                                      font=("Courier", 54, "bold"))
        self.lbl_peso_vivo.pack(pady=(4, 8), padx=15, fill="x")

        # ═══════════════════════════════════════════════════
        #  DESGLOSE BRUTO / TARA / NETO
        # ═══════════════════════════════════════════════════
        frame_desglose = tk.Frame(self.root, bg="#2E3440")
        frame_desglose.pack(pady=4, padx=25, fill="x")
        frame_desglose.grid_columnconfigure(0, weight=1)
        frame_desglose.grid_columnconfigure(1, weight=1)
        frame_desglose.grid_columnconfigure(2, weight=1)

        self.lbl_bruto = self._crear_caja_valor(frame_desglose, "PESO BRUTO", 0)
        self.lbl_tara = self._crear_caja_valor(frame_desglose, "TARA", 1)
        self.lbl_neto = self._crear_caja_valor(frame_desglose, "PESO NETO", 2, color_texto="#EBCB8B")

        # ═══════════════════════════════════════════════════
        #  CUERPO PRINCIPAL: FORMULARIO (IZQ) Y VIDEO CCTV (DER)
        # ═══════════════════════════════════════════════════
        frame_cuerpo = tk.Frame(self.root, bg="#2E3440")
        frame_cuerpo.pack(pady=8, padx=25, fill="both", expand=True)
        frame_cuerpo.grid_columnconfigure(0, weight=5)
        frame_cuerpo.grid_columnconfigure(1, weight=5)

        # --- COLUMNA IZQUIERDA: Formulario y Acciones ---
        frame_izq = tk.LabelFrame(frame_cuerpo, text="  📋 DATOS DEL PESAJE  ", bg="#3B4252", fg="#88C0D0",
                                  font=("Helvetica", 11, "bold"), bd=2, relief="groove")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        # Campo Placas
        tk.Label(frame_izq, text="Placas del Vehículo:", bg="#3B4252", fg="#ECEFF4", 
                 font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 2))
        
        frame_input_placa = tk.Frame(frame_izq, bg="#3B4252")
        frame_input_placa.pack(fill="x", padx=15, pady=(0, 8))
        
        self.txt_placas = tk.Entry(frame_input_placa, font=("Helvetica", 16, "bold"), width=12, 
                                   justify="center", bg="#4C566A", fg="#ECEFF4", insertbackground="white")
        self.txt_placas.pack(side="left", padx=(0, 10))
        
        self.lbl_estado_ocr = tk.Label(frame_input_placa, text="🔍 Esperando OCR...", bg="#3B4252", 
                                       fg="#EBCB8B", font=("Helvetica", 10))
        self.lbl_estado_ocr.pack(side="left")

        # Campo Material
        tk.Label(frame_izq, text="Material a Pesar:", bg="#3B4252", fg="#ECEFF4", 
                 font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(4, 2))
        self.combo_material = ttk.Combobox(frame_izq, values=self.config.obtener("materiales"), 
                                           font=("Helvetica", 13), state="readonly")
        self.combo_material.pack(fill="x", padx=15, pady=(0, 10))
        if self.config.obtener("materiales"):
            self.combo_material.current(0)

        # Botones de control manual
        frame_botones_manuales = tk.Frame(frame_izq, bg="#3B4252")
        frame_botones_manuales.pack(fill="x", padx=15, pady=4)

        btn_tara = tk.Button(frame_botones_manuales, text="Capturar Tara", font=("Helvetica", 10, "bold"), 
                             bg="#4C566A", fg="white", command=self.capturar_tara)
        btn_tara.pack(side="left", expand=True, fill="x", padx=2)

        btn_bruto = tk.Button(frame_botones_manuales, text="Capturar Bruto", font=("Helvetica", 10, "bold"), 
                              bg="#4C566A", fg="white", command=self.capturar_bruto)
        btn_bruto.pack(side="left", expand=True, fill="x", padx=2)

        btn_limpiar = tk.Button(frame_botones_manuales, text="Limpiar", font=("Helvetica", 10, "bold"), 
                                bg="#BF616A", fg="white", command=self.limpiar_pesos)
        btn_limpiar.pack(side="left", expand=True, fill="x", padx=2)

        # Botón Guardar Manual
        self.btn_guardar = tk.Button(frame_izq, text="💾 GUARDAR MOVIMIENTO MANUAL", 
                                     font=("Helvetica", 12, "bold"), bg="#5E81AC", fg="white", 
                                     command=self.guardar_movimiento_manual)
        self.btn_guardar.pack(fill="x", padx=15, pady=(10, 5), ipady=4)

        # Banner de Estado del Sistema
        self.lbl_banner_estado = tk.Label(frame_izq, text="⚡ Modo Autónomo: Listo para capturar.", 
                                          bg="#434C5E", fg="#A3BE8C", font=("Helvetica", 10, "bold"), 
                                          padx=8, pady=4, relief="sunken")
        self.lbl_banner_estado.pack(fill="x", padx=15, pady=(5, 8))

        # --- COLUMNA DERECHA: Video CCTV en Vivo ---
        frame_der = tk.LabelFrame(frame_cuerpo, text="  📹 CÁMARA EN VIVO (RECONOCIMIENTO OCR)  ", bg="#3B4252", 
                                  fg="#88C0D0", font=("Helvetica", 11, "bold"), bd=2, relief="groove")
        frame_der.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        # Contenedor de la imagen de video
        self.lbl_video = tk.Label(frame_der, bg="#2E3440", width=360, height=230)
        self.lbl_video.pack(padx=12, pady=(10, 4), expand=True)

        # Barra inferior de estado de cámara
        frame_pie_video = tk.Frame(frame_der, bg="#3B4252")
        frame_pie_video.pack(fill="x", padx=12, pady=(0, 8))

        self.lbl_info_cam = tk.Label(frame_pie_video, text="🟢 CÁMARA ACTIVA", bg="#3B4252", 
                                     fg="#A3BE8C", font=("Helvetica", 10, "bold"))
        self.lbl_info_cam.pack(side="left")

        self.lbl_placa_cctv = tk.Label(frame_pie_video, text="Placa: Ninguna", bg="#3B4252", 
                                       fg="#ECEFF4", font=("Helvetica", 10, "bold"))
        self.lbl_placa_cctv.pack(side="right")

    def _crear_caja_valor(self, parent, titulo, col, color_texto="white"):
        frame = tk.Frame(parent, bg="#434C5E", bd=2, relief="groove")
        frame.grid(row=0, column=col, padx=6, sticky="nsew")
        tk.Label(frame, text=titulo, bg="#434C5E", fg="#D8DEE9", font=("Helvetica", 11, "bold")).pack(pady=(4, 0))
        lbl_valor = tk.Label(frame, text="0.00", bg="#434C5E", fg=color_texto, font=("Courier", 22, "bold"))
        lbl_valor.pack(pady=(2, 6))
        return lbl_valor

    # ═══════════════════════════════════════════════════
    #  BUCLES PERIÓDICOS
    # ═══════════════════════════════════════════════════

    def actualizar_peso_en_vivo(self):
        """Lee la báscula y actualiza el display principal."""
        peso, es_estable, hay_vehiculo = self.bascula.obtener_estado_completo()
        self.lbl_peso_vivo.config(text=f"{peso:,.2f}")
        
        # Actualizar indicador visual de báscula
        if not hay_vehiculo:
            self.lbl_indicador_estable.config(text="⚪ BÁSCULA LIBRE", bg="#4C566A", fg="#ECEFF4")
        elif es_estable:
            self.lbl_indicador_estable.config(text="🟢 PESO ESTABLE", bg="#A3BE8C", fg="#2E3440")
        else:
            self.lbl_indicador_estable.config(text="🟡 ESTABILIZANDO...", bg="#EBCB8B", fg="#2E3440")

        self.root.after(100, self.actualizar_peso_en_vivo)

    def actualizar_video_en_vivo(self):
        """Refresca el feed de la cámara a ~30 FPS."""
        try:
            foto = self.lector_ocr.obtener_frame_para_tkinter(ancho_deseado=360, alto_deseado=230)
            self._foto_video = foto
            self.lbl_video.config(image=foto)
            
            # Actualizar estado de la cámara
            if self.lector_ocr.camara_activa:
                self.lbl_info_cam.config(text="🟢 CÁMARA EN VIVO", fg="#A3BE8C")
            else:
                self.lbl_info_cam.config(text="🔴 MODO DEMO / SIN SEÑAL", fg="#BF616A")

            # Mostrar placa detectada en vivo si existe
            placa_act, conf = self.lector_ocr.obtener_placa_actual()
            if placa_act:
                self.lbl_placa_cctv.config(text=f"Placa: {placa_act} ({conf*100:.0f}%)", fg="#A3BE8C")
            else:
                self.lbl_placa_cctv.config(text="Placa: Buscando...", fg="#D8DEE9")

        except Exception as e:
            pass

        self.root.after(35, self.actualizar_video_en_vivo)

    # ═══════════════════════════════════════════════════
    #  MÁQUINA DE ESTADOS: CAPTURA 100% AUTÓNOMA
    # ═══════════════════════════════════════════════════

    def evaluar_ciclo_autonomo(self):
        """
        Monitorea báscula y OCR continuamente para disparar la captura
        de forma instantánea y automática sin intervención humana.
        """
        if not self.modo_automatico.get():
            self.lbl_banner_estado.config(text="⚠️ Modo Automático Desactivado (Operación Manual).", 
                                          bg="#3B4252", fg="#EBCB8B")
            self.root.after(150, self.evaluar_ciclo_autonomo)
            return

        peso, es_estable, hay_vehiculo = self.bascula.obtener_estado_completo()
        placa_detectada, conf = self.lector_ocr.obtener_placa_actual()

        # Si hay placa en cámara, actualizar campo de texto en vivo
        if placa_detectada and self.estado_ciclo != self.ESTADO_ATENDIDO:
            if self.txt_placas.get() != placa_detectada:
                self.txt_placas.delete(0, tk.END)
                self.txt_placas.insert(0, placa_detectada)
                self.lbl_estado_ocr.config(text=f"✅ {placa_detectada} ({conf*100:.0f}%)", fg="#A3BE8C")

        # --- TRANSICIONES DE ESTADO ---
        if not hay_vehiculo:
            # 1. Báscula libre -> Reiniciar máquina de estados
            if self.estado_ciclo != self.ESTADO_ESPERANDO:
                self.estado_ciclo = self.ESTADO_ESPERANDO
                self.lbl_banner_estado.config(text="⚡ Modo Autónomo: Esperando vehículo...", bg="#434C5E", fg="#A3BE8C")
                self.txt_placas.delete(0, tk.END)
                self.lbl_estado_ocr.config(text="🔍 Esperando OCR...", fg="#EBCB8B")
                self.limpiar_pesos()

        elif self.estado_ciclo == self.ESTADO_ESPERANDO:
            # 2. Vehículo entra a báscula
            self.estado_ciclo = self.ESTADO_ESTABILIZANDO
            self.lbl_banner_estado.config(text="🟡 Vehículo en báscula: Estabilizando peso y leyendo placa...", 
                                          bg="#434C5E", fg="#EBCB8B")

        elif self.estado_ciclo == self.ESTADO_ESTABILIZANDO:
            # 3. Evaluar condiciones de disparo
            placa_actual = self.txt_placas.get().strip().upper()
            
            # Si no ha detectado placa por cámara, asignamos temporalmente una genérica para no bloquear si no hay cámara
            if not placa_actual and es_estable:
                placa_actual = "CAMION-" + str(int(time.time()))[-4:]
                self.txt_placas.insert(0, placa_actual)

            if es_estable and placa_actual:
                # ¡DISPARO AUTOMÁTICO INSTANTÁNEO!
                self._ejecutar_disparo_automatico(peso, placa_actual)

        self.root.after(100, self.evaluar_ciclo_autonomo)

    def _ejecutar_disparo_automatico(self, peso_capturado, placa):
        """Ejecuta la captura, guarda en MongoDB, crea el ticket y emite aviso sonoro."""
        self.estado_ciclo = self.ESTADO_ATENDIDO
        
        # 1. Buscar camión en el catálogo para Taras Automáticas
        camion = self.bd.buscar_camion_por_placa(placa) if self.bd.bd is not None else None
        
        chofer = "DESCONOCIDO"
        tipo_mov = "SALIDA"
        
        if camion:
            chofer = camion.get("chofer", "DESCONOCIDO")
            self.peso_tara = camion.get("tara_kg", 0.0)
            
            # Lógica de Entrada / Salida (si el peso capturado es casi igual a la tara, es camión vacío)
            tolerancia_vacio = 300.0 # kg
            if abs(peso_capturado - self.peso_tara) <= tolerancia_vacio:
                # Viene a cargar (Camión Vacío)
                self.peso_bruto = peso_capturado
                self.peso_neto = 0.0
                tipo_mov = "ENTRADA"
            else:
                # Viene cargado (Camión Lleno)
                self.peso_bruto = peso_capturado
                self.peso_neto = max(0.0, self.peso_bruto - self.peso_tara)
                tipo_mov = "SALIDA"
        else:
            # Si no está en catálogo, se asume sin tara
            self.peso_bruto = peso_capturado
            self.peso_tara = 0.0
            self.peso_neto = peso_capturado

        # Asignar a la GUI
        self.lbl_tara.config(text=f"{self.peso_tara:,.2f}")
        self.lbl_bruto.config(text=f"{self.peso_bruto:,.2f}")
        self.lbl_neto.config(text=f"{self.peso_neto:,.2f}")
        
        material = self.combo_material.get()
        fecha_str = time.strftime('%Y-%m-%d %H:%M:%S')

        # 2. Guardar en Base de Datos (con los nuevos campos para Supercap)
        exito_bd = False
        if self.bd.bd is not None:
            exito_bd = self.bd.guardar_movimiento(placa, material, self.peso_bruto, self.peso_tara, self.peso_neto, chofer, tipo_mov, self.operador)

        # 2. Generar Ticket PDF de forma automática
        try:
            archivo_pdf = self.generador_ticket.generar_ticket(
                placa, material, f"{self.peso_bruto:,.2f}", f"{self.peso_tara:,.2f}", f"{self.peso_neto:,.2f}", fecha_str, self.operador
            )
        except Exception as e:
            print(f"[TICKET AUTO ERROR] {e}")

        # 3. Sonido de confirmación del sistema (beep industrial)
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

        # 4. Alerta visual de éxito
        self.lbl_banner_estado.config(
            text=f"🟢 ¡PESAJE CAPTURADO! Placa: {placa} | Peso: {peso_capturado:,.2f} kg (Ticket Generado)",
            bg="#2E7D32", fg="white"
        )

        # Limpiar placa de la cámara para que no re-dispare de inmediato
        self.lector_ocr.limpiar_placa_actual()

    # ═══════════════════════════════════════════════════
    #  ACCIONES MANUALES
    # ═══════════════════════════════════════════════════

    def capturar_tara(self):
        self.peso_tara = self.bascula.obtener_peso()
        self.lbl_tara.config(text=f"{self.peso_tara:,.2f}")
        self._calcular_neto()

    def capturar_bruto(self):
        self.peso_bruto = self.bascula.obtener_peso()
        self.lbl_bruto.config(text=f"{self.peso_bruto:,.2f}")
        self._calcular_neto()

    def limpiar_pesos(self):
        self.peso_tara = 0.0
        self.peso_bruto = 0.0
        self.lbl_tara.config(text="0.00")
        self.lbl_bruto.config(text="0.00")
        self.lbl_neto.config(text="0.00")

    def _calcular_neto(self):
        neto = abs(self.peso_bruto - self.peso_tara)
        self.lbl_neto.config(text=f"{neto:,.2f}")

    def guardar_movimiento_manual(self):
        placas = self.txt_placas.get().strip().upper()
        material = self.combo_material.get()
        neto = abs(self.peso_bruto - self.peso_tara)
        
        if not placas:
            messagebox.showwarning("Atención", "Por favor ingresa las placas del vehículo.")
            return

        if self.peso_bruto == 0:
            self.peso_bruto = self.bascula.obtener_peso()
            neto = self.peso_bruto

        if self.bd.bd is not None:
            # Buscar chofer en catálogo
            camion = self.bd.buscar_camion_por_placa(placas)
            chofer = camion.get("chofer", "") if camion else ""
            exito = self.bd.guardar_movimiento(placas, material, self.peso_bruto, self.peso_tara, neto, chofer, "SALIDA", self.operador)
            if exito:
                messagebox.showinfo("Registro Exitoso", f"Movimiento guardado exitosamente:\nPlacas: {placas}\nPeso: {neto:,.2f} kg")
            else:
                messagebox.showerror("Error", "Fallo al guardar en la base de datos.")
        else:
            messagebox.showinfo("Simulación", f"Movimiento simulado:\nPlacas: {placas}\nPeso: {neto:,.2f} kg")

        self.txt_placas.delete(0, tk.END)
        self.limpiar_pesos()

    # ═══════════════════════════════════════════════════
    #  APERTURA DE VENTANAS SECUNDARIAS
    # ═══════════════════════════════════════════════════

    def abrir_historial(self):
        if self.bd.bd is not None:
            VentanaHistorial(self.root, self.bd)
        else:
            messagebox.showwarning("Aviso", "No hay conexión a MongoDB. No se puede ver el historial.")

    def _abrir_dashboard(self):
        if self.bd.bd is not None:
            VentanaDashboard(self.root, self.bd)
        else:
            messagebox.showwarning("Aviso", "No hay conexión a MongoDB. No se puede mostrar el dashboard.")

    def _abrir_configuracion(self):
        VentanaConfiguracion(self.root, self.config, self.bd, self._on_config_guardada)
        
    def _on_config_guardada(self):
        materiales = self.config.obtener("materiales")
        self.combo_material['values'] = materiales
        if materiales and self.combo_material.get() not in materiales:
            self.combo_material.current(0)
            
        self.bascula.desconectar()
        self.bascula.puerto = self.config.obtener("puerto_com")
        self.bascula.baudrate = self.config.obtener("baudrate")
        self.bascula.conectar()

        # Actualizar cámara según configuración (USB o IP/RTSP)
        nueva_fuente = self.config.obtener_fuente_camara()
        self.lector_ocr.cambiar_camara(nueva_fuente)

    def al_cerrar(self):
        self.bascula.desconectar()
        self.lector_ocr.cerrar()
        self.root.destroy()

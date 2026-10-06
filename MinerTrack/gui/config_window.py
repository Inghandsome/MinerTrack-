import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from core.camara import LectorPlacas

class VentanaConfiguracion:
    def __init__(self, parent, config_manager, gestor_bd, on_config_saved):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("MinerTrack - Configuración del Sistema")
        self.ventana.geometry("660x650")
        self.ventana.configure(bg="#2E3440")
        self.ventana.resizable(False, False)
        
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self.config = config_manager
        self.bd = gestor_bd
        self.on_config_saved = on_config_saved
        
        self._crear_interfaz()
        
    def _crear_interfaz(self):
        # Título
        tk.Label(self.ventana, text="⚙️ CONFIGURACIÓN DEL SISTEMA", 
                 font=("Helvetica", 15, "bold"), bg="#2E3440", fg="#88C0D0").pack(pady=(12, 6))

        # Cuaderno de Pestañas (Notebook)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#2E3440", borderwidth=0)
        style.configure("TNotebook.Tab", background="#3B4252", foreground="#ECEFF4", 
                        font=("Helvetica", 10, "bold"), padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", "#5E81AC")], foreground=[("selected", "white")])

        notebook = ttk.Notebook(self.ventana)
        notebook.pack(fill="both", expand=True, padx=15, pady=6)

        # ── PESTAÑA 1: CÁMARA Y VISIÓN ARTIFICIAL ──
        tab_cam = tk.Frame(notebook, bg="#3B4252")
        notebook.add(tab_cam, text="📹 Cámara / OCR")
        self._crear_tab_camara(tab_cam)

        # ── PESTAÑA 2: BÁSCULA SERIAL ──
        tab_bascula = tk.Frame(notebook, bg="#3B4252")
        notebook.add(tab_bascula, text="⚖️ Báscula Serial")
        self._crear_tab_bascula(tab_bascula)

        # ── PESTAÑA 3: MATERIALES ──
        tab_mat = tk.Frame(notebook, bg="#3B4252")
        notebook.add(tab_mat, text="📋 Materiales")
        self._crear_tab_materiales(tab_mat)

        # ── PESTAÑA 4: BASE DE DATOS Y RESPALDOS ──
        tab_bd = tk.Frame(notebook, bg="#3B4252")
        notebook.add(tab_bd, text="💾 Base de Datos")
        self._crear_tab_bd(tab_bd)

        # ── PESTAÑA 5: CAMIONES Y TARAS ──
        tab_camiones = tk.Frame(notebook, bg="#3B4252")
        notebook.add(tab_camiones, text="🚛 Camiones y Taras")
        self._crear_tab_camiones(tab_camiones)

        # Botón Guardar Todo
        frame_guardar = tk.Frame(self.ventana, bg="#2E3440")
        frame_guardar.pack(fill="x", padx=15, pady=(4, 12))

        tk.Button(frame_guardar, text="💾 GUARDAR Y APLICAR CONFIGURACIÓN", 
                  font=("Helvetica", 12, "bold"), bg="#5E81AC", fg="white", 
                  command=self._guardar).pack(fill="x", ipady=6)

    # ═══════════════════════════════════════════════════
    #  PESTAÑA 1: CÁMARA (USB / IP / RTSP)
    # ═══════════════════════════════════════════════════
    def _crear_tab_camara(self, parent):
        self.var_tipo_cam = tk.StringVar(value=self.config.obtener("tipo_camara", "USB"))

        frame_tipo = tk.Frame(parent, bg="#3B4252")
        frame_tipo.pack(fill="x", padx=15, pady=10)

        tk.Label(frame_tipo, text="Tipo de Conexión:", bg="#3B4252", fg="#ECEFF4", 
                 font=("Helvetica", 11, "bold")).pack(side="left", padx=(0, 15))

        rb_usb = tk.Radiobutton(frame_tipo, text="🔌 Webcam USB / Local", variable=self.var_tipo_cam, 
                                value="USB", bg="#3B4252", fg="#ECEFF4", selectcolor="#2E3440",
                                font=("Helvetica", 10), activebackground="#3B4252", activeforeground="white",
                                command=self._actualizar_vista_tipo_cam)
        rb_usb.pack(side="left", padx=10)

        rb_ip = tk.Radiobutton(frame_tipo, text="🌐 Cámara IP / RTSP / Stream", variable=self.var_tipo_cam, 
                               value="IP_RTSP", bg="#3B4252", fg="#ECEFF4", selectcolor="#2E3440",
                               font=("Helvetica", 10), activebackground="#3B4252", activeforeground="white",
                               command=self._actualizar_vista_tipo_cam)
        rb_ip.pack(side="left", padx=10)

        # Contenedor USB
        self.frame_usb = tk.LabelFrame(parent, text="Configuración Webcam USB", bg="#3B4252", fg="#88C0D0", 
                                       font=("Helvetica", 10, "bold"), padx=10, pady=8)
        
        tk.Label(self.frame_usb, text="Índice de Dispositivo (0 = Principal, 1 = Externa):", 
                 bg="#3B4252", fg="white").grid(row=0, column=0, sticky="w", pady=4)
        self.txt_cam_index = tk.Entry(self.frame_usb, width=8, font=("Helvetica", 11))
        self.txt_cam_index.grid(row=0, column=1, sticky="w", padx=10, pady=4)
        self.txt_cam_index.insert(0, str(self.config.obtener("camara_index", 0)))

        # Contenedor Cámara IP
        self.frame_ip = tk.LabelFrame(parent, text="Configuración Cámara IP / Red (Hikvision, Dahua, ONVIF)", 
                                      bg="#3B4252", fg="#88C0D0", font=("Helvetica", 10, "bold"), padx=10, pady=8)
        
        # IP y Puerto
        tk.Label(self.frame_ip, text="Dirección IP / Host:", bg="#3B4252", fg="white").grid(row=0, column=0, sticky="e", pady=4)
        self.txt_cam_ip = tk.Entry(self.frame_ip, width=18, font=("Helvetica", 10))
        self.txt_cam_ip.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        self.txt_cam_ip.insert(0, str(self.config.obtener("camara_ip", "192.168.1.64")))

        tk.Label(self.frame_ip, text="Puerto RTSP:", bg="#3B4252", fg="white").grid(row=0, column=2, sticky="e", pady=4)
        self.txt_cam_puerto = tk.Entry(self.frame_ip, width=8, font=("Helvetica", 10))
        self.txt_cam_puerto.grid(row=0, column=3, sticky="w", padx=6, pady=4)
        self.txt_cam_puerto.insert(0, str(self.config.obtener("camara_puerto", 554)))

        # Usuario y Contraseña
        tk.Label(self.frame_ip, text="Usuario:", bg="#3B4252", fg="white").grid(row=1, column=0, sticky="e", pady=4)
        self.txt_cam_user = tk.Entry(self.frame_ip, width=18, font=("Helvetica", 10))
        self.txt_cam_user.grid(row=1, column=1, sticky="w", padx=6, pady=4)
        self.txt_cam_user.insert(0, str(self.config.obtener("camara_usuario", "admin")))

        tk.Label(self.frame_ip, text="Contraseña:", bg="#3B4252", fg="white").grid(row=1, column=2, sticky="e", pady=4)
        self.txt_cam_pass = tk.Entry(self.frame_ip, width=12, show="*", font=("Helvetica", 10))
        self.txt_cam_pass.grid(row=1, column=3, sticky="w", padx=6, pady=4)
        self.txt_cam_pass.insert(0, str(self.config.obtener("camara_password", "")))

        # Canal / Ruta de Stream
        tk.Label(self.frame_ip, text="Ruta de Stream / Canal:", bg="#3B4252", fg="white").grid(row=2, column=0, sticky="e", pady=4)
        self.txt_cam_ruta = tk.Entry(self.frame_ip, width=28, font=("Helvetica", 10))
        self.txt_cam_ruta.grid(row=2, column=1, columnspan=3, sticky="w", padx=6, pady=4)
        self.txt_cam_ruta.insert(0, str(self.config.obtener("camara_ruta_stream", "/Streaming/Channels/101")))

        # URL Completa Opcional
        tk.Label(self.frame_ip, text="O URL RTSP/HTTP directa:", bg="#3B4252", fg="#D8DEE9", 
                 font=("Helvetica", 9, "italic")).grid(row=3, column=0, sticky="e", pady=(8, 4))
        self.txt_cam_url_custom = tk.Entry(self.frame_ip, width=38, font=("Helvetica", 10))
        self.txt_cam_url_custom.grid(row=3, column=1, columnspan=3, sticky="w", padx=6, pady=(8, 4))
        self.txt_cam_url_custom.insert(0, str(self.config.obtener("camara_url_personalizada", "")))

        # Botón Probar Conexión
        frame_test = tk.Frame(parent, bg="#3B4252")
        frame_test.pack(fill="x", padx=15, pady=12)

        btn_probar = tk.Button(frame_test, text="🔍 PROBAR CONEXIÓN DE CÁMARA", font=("Helvetica", 10, "bold"),
                               bg="#EBCB8B", fg="#2E3440", command=self._probar_camara)
        btn_probar.pack(side="left", padx=5)

        self.lbl_resultado_test = tk.Label(frame_test, text="", bg="#3B4252", fg="#A3BE8C", font=("Helvetica", 9, "bold"))
        self.lbl_resultado_test.pack(side="left", padx=10)

        self._actualizar_vista_tipo_cam()

    def _actualizar_vista_tipo_cam(self):
        tipo = self.var_tipo_cam.get()
        if tipo == "USB":
            self.frame_ip.pack_forget()
            self.frame_usb.pack(fill="x", padx=15, pady=6)
        else:
            self.frame_usb.pack_forget()
            self.frame_ip.pack(fill="x", padx=15, pady=6)

    def _obtener_fuente_actual_formulario(self):
        tipo = self.var_tipo_cam.get()
        if tipo == "USB":
            try:
                return int(self.txt_cam_index.get().strip())
            except ValueError:
                return 0
        else:
            url_custom = self.txt_cam_url_custom.get().strip()
            if url_custom:
                return url_custom
            ip = self.txt_cam_ip.get().strip()
            puerto = self.txt_cam_puerto.get().strip() or "554"
            usuario = self.txt_cam_user.get().strip()
            password = self.txt_cam_pass.get().strip()
            ruta = self.txt_cam_ruta.get().strip() or "/Streaming/Channels/101"
            if not ruta.startswith("/"):
                ruta = "/" + ruta

            if usuario and password:
                return f"rtsp://{usuario}:{password}@{ip}:{puerto}{ruta}"
            else:
                return f"rtsp://{ip}:{puerto}{ruta}"

    def _probar_camara(self):
        self.lbl_resultado_test.config(text="⏳ Probando conexión...", fg="#EBCB8B")
        self.ventana.update()
        
        fuente = self._obtener_fuente_actual_formulario()
        exito, mensaje = LectorPlacas.probar_fuente(fuente)
        
        if exito:
            self.lbl_resultado_test.config(text="✅ ¡Conexión Exitosa!", fg="#A3BE8C")
            messagebox.showinfo("Prueba de Cámara", f"¡Éxito!\n{mensaje}\n\nFuente: {fuente}", parent=self.ventana)
        else:
            self.lbl_resultado_test.config(text="❌ Fallo de Conexión", fg="#BF616A")
            messagebox.showwarning("Fallo de Cámara", f"No se pudo conectar:\n{mensaje}\n\nFuente probada: {fuente}", parent=self.ventana)

    # ═══════════════════════════════════════════════════
    #  PESTAÑA 2: BÁSCULA SERIAL
    # ═══════════════════════════════════════════════════
    def _crear_tab_bascula(self, parent):
        frame_hw = tk.Frame(parent, bg="#3B4252")
        frame_hw.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame_hw, text="Puerto COM de Báscula (Transcell TI-1680):", 
                 bg="#3B4252", fg="white", font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        self.txt_com = tk.Entry(frame_hw, width=15, font=("Helvetica", 11))
        self.txt_com.grid(row=0, column=1, sticky="w", padx=15, pady=10)
        self.txt_com.insert(0, str(self.config.obtener("puerto_com", "COM3")))

        tk.Label(frame_hw, text="Baudrate (Velocidad en Baudios):", 
                 bg="#3B4252", fg="white", font=("Helvetica", 11, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        self.txt_baudrate = tk.Entry(frame_hw, width=15, font=("Helvetica", 11))
        self.txt_baudrate.grid(row=1, column=1, sticky="w", padx=15, pady=10)
        self.txt_baudrate.insert(0, str(self.config.obtener("baudrate", 9600)))

        tk.Label(frame_hw, text="Configuración por defecto del TI-1680: 9600 baudios, 8 bits, Sin Paridad (8, N, 1).", 
                 bg="#3B4252", fg="#D8DEE9", font=("Helvetica", 9, "italic")).grid(row=2, column=0, columnspan=2, sticky="w", pady=(15, 0))

    # ═══════════════════════════════════════════════════
    #  PESTAÑA 3: MATERIALES
    # ═══════════════════════════════════════════════════
    def _crear_tab_materiales(self, parent):
        frame_mat = tk.Frame(parent, bg="#3B4252")
        frame_mat.pack(fill="both", expand=True, padx=15, pady=15)

        self.lista_mat = tk.Listbox(frame_mat, bg="#4C566A", fg="white", font=("Helvetica", 11), selectbackground="#5E81AC")
        self.lista_mat.pack(side="left", fill="both", expand=True, padx=(0, 10))

        for m in self.config.obtener("materiales", []):
            self.lista_mat.insert(tk.END, m)

        frame_btn_mat = tk.Frame(frame_mat, bg="#3B4252")
        frame_btn_mat.pack(side="right", fill="y")

        tk.Label(frame_btn_mat, text="Nuevo Material:", bg="#3B4252", fg="white", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_nuevo_mat = tk.Entry(frame_btn_mat, width=18, font=("Helvetica", 10))
        self.txt_nuevo_mat.pack(pady=(0, 8))

        tk.Button(frame_btn_mat, text="➕ Añadir", bg="#A3BE8C", font=("Helvetica", 10, "bold"),
                  command=self._agregar_material).pack(fill="x", pady=4)
        tk.Button(frame_btn_mat, text="🗑️ Eliminar", bg="#BF616A", fg="white", font=("Helvetica", 10, "bold"),
                  command=self._eliminar_material).pack(fill="x", pady=4)

    def _agregar_material(self):
        nuevo = self.txt_nuevo_mat.get().strip()
        if nuevo:
            if nuevo not in self.lista_mat.get(0, tk.END):
                self.lista_mat.insert(tk.END, nuevo)
                self.txt_nuevo_mat.delete(0, tk.END)
            else:
                messagebox.showinfo("Aviso", "El material ya está en la lista.", parent=self.ventana)

    def _eliminar_material(self):
        seleccion = self.lista_mat.curselection()
        if seleccion:
            self.lista_mat.delete(seleccion[0])

    # ═══════════════════════════════════════════════════
    #  PESTAÑA 4: BASE DE DATOS Y RESPALDOS
    # ═══════════════════════════════════════════════════
    def _crear_tab_bd(self, parent):
        frame_bd = tk.Frame(parent, bg="#3B4252")
        frame_bd.pack(fill="both", expand=True, padx=20, pady=25)

        tk.Label(frame_bd, text="Copias de Seguridad (MongoDB)", bg="#3B4252", fg="#88C0D0", 
                 font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(frame_bd, text="Exporta todos tus registros a un archivo JSON para respaldo en memoria USB,\no importa un respaldo previo si reinstalas el sistema.",
                 bg="#3B4252", fg="#D8DEE9", font=("Helvetica", 10), justify="left").pack(anchor="w", pady=(0, 20))

        frame_acciones_bd = tk.Frame(frame_bd, bg="#3B4252")
        frame_acciones_bd.pack(fill="x", pady=10)

        tk.Button(frame_acciones_bd, text="📤 EXPORTAR RESPALDO JSON", bg="#81A1C1", fg="#2E3440", 
                  font=("Helvetica", 11, "bold"), command=self._exportar_bd).pack(side="left", padx=10, expand=True, fill="x", ipady=8)

        tk.Button(frame_acciones_bd, text="📥 IMPORTAR RESPALDO JSON", bg="#D08770", fg="#2E3440", 
                  font=("Helvetica", 11, "bold"), command=self._importar_bd).pack(side="right", padx=10, expand=True, fill="x", ipady=8)

    def _exportar_bd(self):
        ruta = filedialog.asksaveasfilename(
            parent=self.ventana, defaultextension=".json", filetypes=[("JSON Backup", "*.json")], 
            initialfile=f"MinerTrack_Backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )
        if ruta:
            exito, msj = self.bd.exportar_respaldo(ruta)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=self.ventana)
            else:
                messagebox.showerror("Error", msj, parent=self.ventana)

    def _importar_bd(self):
        respuesta = messagebox.askyesno(
            "Advertencia", "Importar un respaldo BORRARÁ los datos actuales para reemplazarlos con la copia.\n\n¿Estás seguro de continuar?", 
            parent=self.ventana
        )
        if not respuesta:
            return
            
        ruta = filedialog.askopenfilename(
            parent=self.ventana, defaultextension=".json", filetypes=[("JSON Backup", "*.json")]
        )
        if ruta:
            exito, msj = self.bd.importar_respaldo(ruta)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=self.ventana)
            else:
                messagebox.showerror("Error", msj, parent=self.ventana)

    # ═══════════════════════════════════════════════════
    #  GUARDADO GENERAL DE CONFIGURACIÓN
    # ═══════════════════════════════════════════════════
    def _guardar(self):
        # 1. Báscula
        self.config.actualizar("puerto_com", self.txt_com.get().strip())
        try:
            self.config.actualizar("baudrate", int(self.txt_baudrate.get().strip()))
        except ValueError:
            messagebox.showerror("Error", "El baudrate debe ser un número entero.", parent=self.ventana)
            return

        # 2. Cámara
        tipo_cam = self.var_tipo_cam.get()
        self.config.actualizar("tipo_camara", tipo_cam)

        if tipo_cam == "USB":
            try:
                self.config.actualizar("camara_index", int(self.txt_cam_index.get().strip()))
            except ValueError:
                messagebox.showerror("Error", "El índice de cámara USB debe ser un número entero (ej. 0, 1).", parent=self.ventana)
                return
        else:
            self.config.actualizar("camara_ip", self.txt_cam_ip.get().strip())
            try:
                self.config.actualizar("camara_puerto", int(self.txt_cam_puerto.get().strip() or "554"))
            except ValueError:
                messagebox.showerror("Error", "El puerto RTSP debe ser un número.", parent=self.ventana)
                return
            self.config.actualizar("camara_usuario", self.txt_cam_user.get().strip())
            self.config.actualizar("camara_password", self.txt_cam_pass.get().strip())
            self.config.actualizar("camara_ruta_stream", self.txt_cam_ruta.get().strip())
            self.config.actualizar("camara_url_personalizada", self.txt_cam_url_custom.get().strip())

        # 3. Materiales
        materiales = list(self.lista_mat.get(0, tk.END))
        if not materiales:
            messagebox.showerror("Error", "Debes tener al menos un material en la lista.", parent=self.ventana)
            return
        self.config.actualizar("materiales", materiales)

        messagebox.showinfo("Configuración Guardada", 
                            "¡Configuración guardada exitosamente!\n\nLos cambios de cámara y báscula se aplicarán de inmediato.", 
                            parent=self.ventana)
        self.on_config_saved()
        self.ventana.destroy()

    def _crear_tab_camiones(self, tab):
        frame_superior = tk.Frame(tab, bg="#3B4252")
        frame_superior.pack(fill="x", padx=10, pady=10)
        
        tk.Label(frame_superior, text="ID Int:", bg="#3B4252", fg="white").grid(row=0, column=0, padx=2)
        self.ent_cam_id = tk.Entry(frame_superior, width=5)
        self.ent_cam_id.grid(row=0, column=1, padx=2)
        
        tk.Label(frame_superior, text="Placa:", bg="#3B4252", fg="white").grid(row=0, column=2, padx=2)
        self.ent_cam_placa = tk.Entry(frame_superior, width=12)
        self.ent_cam_placa.grid(row=0, column=3, padx=2)
        
        tk.Label(frame_superior, text="Chofer:", bg="#3B4252", fg="white").grid(row=0, column=4, padx=2)
        self.ent_cam_chofer = tk.Entry(frame_superior, width=25)
        self.ent_cam_chofer.grid(row=0, column=5, padx=2)
        
        tk.Label(frame_superior, text="Tara (kg):", bg="#3B4252", fg="white").grid(row=0, column=6, padx=2)
        self.ent_cam_tara = tk.Entry(frame_superior, width=8)
        self.ent_cam_tara.grid(row=0, column=7, padx=2)
        
        btn_add = tk.Button(frame_superior, text="➕ Agregar / Editar", bg="#A3BE8C", fg="black", command=self._guardar_camion_ui)
        btn_add.grid(row=0, column=8, padx=10)

        # Tabla (Treeview)
        frame_tabla = tk.Frame(tab, bg="#3B4252")
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
        
        columnas = ("id", "placa", "chofer", "tara")
        self.tree_camiones = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)
        self.tree_camiones.heading("id", text="# ID")
        self.tree_camiones.heading("placa", text="Placa")
        self.tree_camiones.heading("chofer", text="Chofer / Propietario")
        self.tree_camiones.heading("tara", text="Tara (kg)")
        
        self.tree_camiones.column("id", width=50, anchor="center")
        self.tree_camiones.column("placa", width=100, anchor="center")
        self.tree_camiones.column("chofer", width=300, anchor="w")
        self.tree_camiones.column("tara", width=100, anchor="center")
        
        self.tree_camiones.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tree_camiones.yview)
        self.tree_camiones.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Botones inferiores
        frame_inferior = tk.Frame(tab, bg="#3B4252")
        frame_inferior.pack(fill="x", padx=10, pady=10)
        
        btn_del = tk.Button(frame_inferior, text="🗑️ Eliminar Seleccionado", bg="#BF616A", fg="white", command=self._eliminar_camion_ui)
        btn_del.pack(side="left")
        
        btn_load = tk.Button(frame_inferior, text="📋 Cargar Lista Inicial ATSA", bg="#5E81AC", fg="white", command=self._cargar_lista_inicial)
        btn_load.pack(side="right")
        
        self._actualizar_tabla_camiones()

    def _actualizar_tabla_camiones(self):
        for item in self.tree_camiones.get_children():
            self.tree_camiones.delete(item)
        camiones = self.bd.obtener_camiones()
        for c in camiones:
            self.tree_camiones.insert("", tk.END, values=(c.get("id_interno", ""), c.get("placa", ""), c.get("chofer", ""), c.get("tara_kg", "")))

    def _guardar_camion_ui(self):
        placa = self.ent_cam_placa.get().strip()
        chofer = self.ent_cam_chofer.get().strip()
        tara = self.ent_cam_tara.get().strip()
        id_int = self.ent_cam_id.get().strip()
        
        if not placa or not chofer or not tara:
            messagebox.showwarning("Faltan datos", "Placa, Chofer y Tara son obligatorios.", parent=self.ventana)
            return
            
        try:
            float(tara)
        except ValueError:
            messagebox.showwarning("Error", "La Tara debe ser un número (ej. 11500).", parent=self.ventana)
            return
            
        if self.bd.agregar_camion(placa, chofer, tara, id_int):
            self.ent_cam_placa.delete(0, tk.END)
            self.ent_cam_chofer.delete(0, tk.END)
            self.ent_cam_tara.delete(0, tk.END)
            self.ent_cam_id.delete(0, tk.END)
            self._actualizar_tabla_camiones()
        else:
            messagebox.showerror("Error BD", "No se pudo guardar el camión.", parent=self.ventana)

    def _eliminar_camion_ui(self):
        seleccionado = self.tree_camiones.selection()
        if not seleccionado:
            return
        item = self.tree_camiones.item(seleccionado[0])
        placa = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar el camión con placa {placa}?", parent=self.ventana):
            if self.bd.eliminar_camion(placa):
                self._actualizar_tabla_camiones()

    def _cargar_lista_inicial(self):
        lista_inicial = [
            ('67AA8G', 'JOSE PEREZ (MARINO)', 11600, 1),
            ('HT53523', 'ELEAZAR SAMPAYO', 10340, 2),
            ('MU2728S', 'EDEN GARCIA (MARTIN JARDINEZ)', 12150, 3),
            ('RV1596B', 'MARLEN GARCIA (OSVALDO GARCIA)', 10840, 4),
            ('XU1050A', 'GUADALUPE SAMPAYO (ELOY GARCIA)', 10660, 5),
            ('703AH8', 'SALOMON JUAREZ (HERNAN LAGOS)', 11500, 6),
            ('LC09198', 'GUADALUPE SAMPAYO (ELOY GARCIA)', 11340, 7),
            ('XX9680A', 'PEDRO GARCIA (EFRAIN MARTINEZ)', 10470, 8),
            ('RU8448B', 'MARLEN GARCIA (IGNACIO LAGOS)', 10510, 9),
            ('LF46846', 'LAURENTINO ORTEGA (ELISEO PEREZ)', 10260, 10),
            ('XW64125', 'MARLEN GARCIA (OSVALDO GARCIA)', 10400, 11),
            ('630DX4', 'LAURENTINO ORTEGA (ELISEO PEREZ)', 10700, 12)
        ]
        if messagebox.askyesno("Cargar Lista", "¿Deseas cargar la lista predeterminada de 12 camiones de ATSA? Esto sobreescribirá registros si tienen la misma placa.", parent=self.ventana):
            for placa, chofer, tara, id_int in lista_inicial:
                self.bd.agregar_camion(placa, chofer, tara, id_int)
            self._actualizar_tabla_camiones()
            messagebox.showinfo("Éxito", "Catálogo de camiones cargado exitosamente.", parent=self.ventana)

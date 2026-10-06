import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd
import os
from core.ticket_generator import GeneradorTicket

class VentanaHistorial:
    """
    Ventana secundaria que muestra el historial de todos los movimientos
    guardados en MongoDB, con búsqueda por placa y filtro por día.
    """
    def __init__(self, parent, gestor_bd):
        self.gestor_bd = gestor_bd
        
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("MinerTrack - Historial de Movimientos")
        self.ventana.geometry("1050x620")
        self.ventana.configure(bg="#2E3440")
        self.ventana.grab_set()  # Ventana modal (bloquea la principal)
        
        self._crear_interfaz()
        self._cargar_todos()

    def _crear_interfaz(self):
        # ═══════════════════════════════════════════════════
        #  BARRA SUPERIOR: Título + Búsqueda
        # ═══════════════════════════════════════════════════
        frame_top = tk.Frame(self.ventana, bg="#3B4252", bd=3, relief="ridge")
        frame_top.pack(fill="x", padx=15, pady=(15, 5))

        tk.Label(frame_top, text="📊 HISTORIAL DE MOVIMIENTOS",
                 bg="#3B4252", fg="#ECEFF4",
                 font=("Helvetica", 18, "bold")).pack(side="left", padx=20, pady=12)

        # Campo de búsqueda por placa con autocompletado
        frame_busqueda = tk.Frame(frame_top, bg="#3B4252")
        frame_busqueda.pack(side="right", padx=20, pady=10)

        tk.Label(frame_busqueda, text="🔍 Buscar placa:",
                 bg="#3B4252", fg="#D8DEE9",
                 font=("Helvetica", 11)).pack(side="left", padx=(0, 5))

        # Contenedor para el Entry + la lista de sugerencias
        frame_entry = tk.Frame(frame_busqueda, bg="#3B4252")
        frame_entry.pack(side="left", padx=(0, 5))

        self.txt_buscar = tk.Entry(frame_entry, font=("Helvetica", 13),
                                   width=12, justify="center")
        self.txt_buscar.pack()
        self.txt_buscar.bind("<Return>", lambda e: self._buscar_placa())
        self.txt_buscar.bind("<KeyRelease>", self._al_escribir_placa)

        # Listbox de sugerencias (oculta por defecto)
        self.lista_sugerencias = tk.Listbox(frame_entry, font=("Helvetica", 11),
                                             bg="#434C5E", fg="#ECEFF4",
                                             selectbackground="#5E81AC",
                                             width=14, height=5,
                                             relief="solid", bd=1)
        self.lista_sugerencias.bind("<<ListboxSelect>>", self._al_seleccionar_sugerencia)
        # No la mostramos todavía (se muestra cuando haya coincidencias)

        # Cache de placas únicas para el autocompletado
        self._placas_unicas = []
        self._cargar_placas_unicas()

        btn_buscar = tk.Button(frame_busqueda, text="Buscar",
                               font=("Helvetica", 10, "bold"),
                               bg="#5E81AC", fg="white",
                               command=self._buscar_placa)
        btn_buscar.pack(side="left", padx=2)

        # ═══════════════════════════════════════════════════
        #  BARRA DE FILTROS
        # ═══════════════════════════════════════════════════
        frame_filtros = tk.Frame(self.ventana, bg="#2E3440")
        frame_filtros.pack(fill="x", padx=15, pady=5)

        btn_todos = tk.Button(frame_filtros, text="📋 Ver Todos",
                              font=("Helvetica", 10, "bold"),
                              bg="#4C566A", fg="white",
                              command=self._cargar_todos)
        btn_todos.pack(side="left", padx=5)

        btn_hoy = tk.Button(frame_filtros, text="📅 Solo Hoy",
                            font=("Helvetica", 10, "bold"),
                            bg="#4C566A", fg="white",
                            command=self._cargar_hoy)
        btn_hoy.pack(side="left", padx=5)

        btn_actualizar = tk.Button(frame_filtros, text="🔄 Actualizar",
                                   font=("Helvetica", 10, "bold"),
                                   bg="#4C566A", fg="white",
                                   command=self._cargar_todos)
        btn_actualizar.pack(side="left", padx=5)

        btn_excel = tk.Button(frame_filtros, text="📥 Exportar a Excel",
                              font=("Helvetica", 10, "bold"),
                              bg="#2E7D32", fg="white",
                              command=self._exportar_excel)
        btn_excel.pack(side="left", padx=20)

        btn_ticket = tk.Button(frame_filtros, text="🖨️ Ver Ticket",
                               font=("Helvetica", 10, "bold"),
                               bg="#EBCB8B", fg="#2E3440",
                               command=self._ver_ticket)
        btn_ticket.pack(side="left", padx=5)

        btn_eliminar = tk.Button(frame_filtros, text="🗑️ Eliminar Seleccionado",
                                 font=("Helvetica", 10, "bold"),
                                 bg="#BF616A", fg="white",
                                 command=self._eliminar_seleccionado)
        btn_eliminar.pack(side="right", padx=5)

        # Etiqueta de resumen
        self.lbl_resumen = tk.Label(frame_filtros, text="",
                                    bg="#2E3440", fg="#A3BE8C",
                                    font=("Helvetica", 11, "bold"))
        self.lbl_resumen.pack(side="right", padx=20)

        # ═══════════════════════════════════════════════════
        #  TABLA DE DATOS (Treeview)
        # ═══════════════════════════════════════════════════
        frame_tabla = tk.Frame(self.ventana, bg="#2E3440")
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=10)

        columnas = ("num", "fecha", "placas", "material", "bruto", "tara", "neto", "estado")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas,
                                  show="headings", height=18)

        # Definir encabezados y anchos
        self.tabla.heading("num", text="#")
        self.tabla.heading("fecha", text="Fecha y Hora")
        self.tabla.heading("placas", text="Placas")
        self.tabla.heading("material", text="Material")
        self.tabla.heading("bruto", text="Bruto (kg)")
        self.tabla.heading("tara", text="Tara (kg)")
        self.tabla.heading("neto", text="Neto (kg)")
        self.tabla.heading("estado", text="Estado")

        self.tabla.column("num", width=40, anchor="center")
        self.tabla.column("fecha", width=160, anchor="center")
        self.tabla.column("placas", width=110, anchor="center")
        self.tabla.column("material", width=120, anchor="center")
        self.tabla.column("bruto", width=110, anchor="e")
        self.tabla.column("tara", width=110, anchor="e")
        self.tabla.column("neto", width=120, anchor="e")
        self.tabla.column("estado", width=100, anchor="center")

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical",
                                  command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Estilo personalizado para la tabla (tema oscuro)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background="#3B4252",
                         foreground="#ECEFF4",
                         fieldbackground="#3B4252",
                         font=("Helvetica", 11),
                         rowheight=28)
        style.configure("Treeview.Heading",
                         background="#434C5E",
                         foreground="#ECEFF4",
                         font=("Helvetica", 11, "bold"))
        style.map("Treeview",
                  background=[("selected", "#5E81AC")],
                  foreground=[("selected", "white")])

        # ═══════════════════════════════════════════════════
        #  BARRA INFERIOR: Totales
        # ═══════════════════════════════════════════════════
        frame_totales = tk.Frame(self.ventana, bg="#3B4252", bd=3, relief="ridge")
        frame_totales.pack(fill="x", padx=15, pady=(0, 15))

        self.lbl_total_neto = tk.Label(frame_totales,
                                       text="Total Neto: 0.00 kg",
                                       bg="#3B4252", fg="#EBCB8B",
                                       font=("Courier", 14, "bold"))
        self.lbl_total_neto.pack(side="right", padx=20, pady=10)

        self.lbl_total_registros = tk.Label(frame_totales,
                                            text="Registros: 0",
                                            bg="#3B4252", fg="#A3BE8C",
                                            font=("Helvetica", 12, "bold"))
        self.lbl_total_registros.pack(side="left", padx=20, pady=10)

        # Diccionario para guardar los IDs de MongoDB asociados a cada fila
        self._ids_mongo = {}

    def _llenar_tabla(self, movimientos, titulo_resumen=""):
        """Limpia la tabla y la llena con los movimientos recibidos."""
        # Limpiar tabla actual
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self._ids_mongo.clear()

        total_neto = 0.0
        for i, mov in enumerate(movimientos, 1):
            fecha = mov.get("fecha_hora", "")
            if isinstance(fecha, datetime):
                fecha_str = fecha.strftime("%d/%m/%Y  %H:%M")
            else:
                fecha_str = str(fecha)

            placas = mov.get("placas", "N/A")
            material = mov.get("material", "N/A")
            bruto = mov.get("peso_bruto_kg", 0)
            tara = mov.get("peso_tara_kg", 0)
            neto = mov.get("peso_neto_kg", 0)
            estado = mov.get("estado", "---")

            total_neto += neto

            item_id = self.tabla.insert("", "end", values=(
                i,
                fecha_str,
                placas,
                material,
                f"{bruto:,.2f}",
                f"{tara:,.2f}",
                f"{neto:,.2f}",
                estado
            ))
            # Guardar referencia al _id de MongoDB
            self._ids_mongo[item_id] = str(mov.get("_id", ""))

        # Actualizar totales
        cantidad = len(movimientos)
        self.lbl_total_registros.config(text=f"Registros: {cantidad}")
        self.lbl_total_neto.config(text=f"Total Neto: {total_neto:,.2f} kg")
        if titulo_resumen:
            self.lbl_resumen.config(text=titulo_resumen)

    def _cargar_todos(self):
        """Carga todos los movimientos de la base de datos."""
        movimientos = self.gestor_bd.obtener_movimientos()
        self._llenar_tabla(movimientos, "Mostrando: Todos")

    def _cargar_hoy(self):
        """Carga solo los movimientos del día de hoy."""
        movimientos = self.gestor_bd.obtener_movimientos_hoy()
        hoy = datetime.now().strftime("%d/%m/%Y")
        self._llenar_tabla(movimientos, f"Mostrando: Hoy ({hoy})")

    def _buscar_placa(self):
        """Busca movimientos que coincidan con la placa ingresada."""
        texto = self.txt_buscar.get().strip()
        if not texto:
            messagebox.showinfo("Búsqueda", "Escribe una placa o parte de ella para buscar.",
                                parent=self.ventana)
            return
        movimientos = self.gestor_bd.buscar_por_placa(texto)
        self._llenar_tabla(movimientos, f'Resultados para: "{texto.upper()}"')

    def _eliminar_seleccionado(self):
        """Elimina el movimiento seleccionado en la tabla."""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Eliminar", "Selecciona una fila de la tabla primero.",
                                parent=self.ventana)
            return

        item = seleccion[0]
        valores = self.tabla.item(item, "values")
        placa = valores[2] if len(valores) > 2 else "N/A"

        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar el registro de la placa '{placa}'?",
            parent=self.ventana
        )
        if not confirmar:
            return

        mongo_id = self._ids_mongo.get(item)
        if mongo_id and self.gestor_bd.eliminar_movimiento(mongo_id):
            self.tabla.delete(item)
            messagebox.showinfo("Eliminado", "Registro eliminado correctamente.",
                                parent=self.ventana)
            # Recargar para actualizar totales y placas únicas
            self._cargar_todos()
            self._cargar_placas_unicas()
        else:
            messagebox.showerror("Error", "No se pudo eliminar el registro.",
                                 parent=self.ventana)

    def _exportar_excel(self):
        """Exporta los datos actualmente visibles en la tabla a un archivo de Excel."""
        if not self.tabla.get_children():
            messagebox.showinfo("Exportar", "No hay datos en la tabla para exportar.",
                                parent=self.ventana)
            return
            
        ruta_archivo = filedialog.asksaveasfilename(
            parent=self.ventana,
            defaultextension=".xlsx",
            filetypes=[("Archivos de Excel", "*.xlsx")],
            title="Guardar como Excel",
            initialfile=f"Reporte_MinerTrack_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        
        if not ruta_archivo:
            return  # El usuario canceló
            
        try:
            # Recopilamos los datos de la tabla
            datos = []
            columnas = ["#", "Fecha y Hora", "Placas", "Material", "Bruto (kg)", "Tara (kg)", "Neto (kg)", "Estado"]
            
            for item in self.tabla.get_children():
                valores = self.tabla.item(item, "values")
                datos.append(valores)
                
            # Creamos el DataFrame de Pandas
            df = pd.DataFrame(datos, columns=columnas)
            
            # Guardamos a Excel
            df.to_excel(ruta_archivo, index=False, engine='openpyxl')
            
            messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en:\n{ruta_archivo}",
                                parent=self.ventana)
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un problema al exportar a Excel:\n{e}",
                                 parent=self.ventana)

    def _ver_ticket(self):
        """Genera y abre un PDF del ticket para el movimiento seleccionado."""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Ver Ticket", "Selecciona una fila de la tabla primero.",
                                parent=self.ventana)
            return
            
        item = seleccion[0]
        valores = self.tabla.item(item, "values")
        
        # Extraer los datos de la fila (valores = (num, fecha, placas, material, bruto, tara, neto, estado))
        fecha = valores[1]
        placas = valores[2]
        material = valores[3]
        bruto = valores[4]
        tara = valores[5]
        neto = valores[6]
        
        try:
            generador = GeneradorTicket()
            archivo_pdf = generador.generar_ticket(placas, material, bruto, tara, neto, fecha)
            
            # Abrir el PDF generado con la aplicación por defecto del sistema
            if os.name == 'nt':
                os.startfile(archivo_pdf)
            else:
                messagebox.showinfo("Ticket Generado", f"El ticket se generó como: {archivo_pdf}", parent=self.ventana)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket:\n{e}", parent=self.ventana)

    # ═══════════════════════════════════════════════════
    #  AUTOCOMPLETADO DE PLACAS
    # ═══════════════════════════════════════════════════

    def _cargar_placas_unicas(self):
        """Obtiene todas las placas únicas de la base de datos para el autocompletado."""
        try:
            if self.gestor_bd.bd is not None:
                coleccion = self.gestor_bd.bd["movimientos"]
                self._placas_unicas = sorted(coleccion.distinct("placas"))
            else:
                self._placas_unicas = []
        except Exception:
            self._placas_unicas = []

    def _al_escribir_placa(self, event):
        """Se ejecuta cada vez que el usuario escribe una letra en el buscador."""
        texto = self.txt_buscar.get().strip().upper()

        # Si el campo está vacío, ocultar sugerencias
        if not texto:
            self.lista_sugerencias.pack_forget()
            return

        # Filtrar placas que contengan el texto escrito
        coincidencias = [p for p in self._placas_unicas if texto in p.upper()]

        if coincidencias:
            self.lista_sugerencias.delete(0, tk.END)
            for placa in coincidencias[:8]:  # Máximo 8 sugerencias
                self.lista_sugerencias.insert(tk.END, placa)
            self.lista_sugerencias.pack(fill="x")
        else:
            self.lista_sugerencias.pack_forget()

    def _al_seleccionar_sugerencia(self, event):
        """Cuando el usuario hace clic en una sugerencia de la lista."""
        seleccion = self.lista_sugerencias.curselection()
        if seleccion:
            placa = self.lista_sugerencias.get(seleccion[0])
            self.txt_buscar.delete(0, tk.END)
            self.txt_buscar.insert(0, placa)
            self.lista_sugerencias.pack_forget()
            # Ejecutar la búsqueda automáticamente
            self._buscar_placa()

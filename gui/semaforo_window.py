import tkinter as tk

class VentanaSemaforo:
    """
    Ventana secundaria de pantalla completa que muestra un semaforo gigante
    para indicarle al chofer del camion cuando puede avanzar.
    """
    
    ESTADO_LIBRE = "LIBRE"
    ESTADO_ROJO = "ROJO"
    ESTADO_AMARILLO = "AMARILLO"
    ESTADO_VERDE = "VERDE"

    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("MinerTrack - Semaforo de Bascula")
        self.ventana.configure(bg="black")
        self.ventana.attributes("-fullscreen", False)
        self.ventana.geometry("600x800")
        
        self.estado_actual = self.ESTADO_LIBRE
        self._crear_interfaz()
        self.actualizar_estado(self.ESTADO_LIBRE)
    
    def _crear_interfaz(self):
        frame = tk.Frame(self.ventana, bg="black")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.lbl_titulo = tk.Label(frame, text="BASCULA CAMIONERA", 
                                    font=("Helvetica", 28, "bold"), bg="black", fg="white")
        self.lbl_titulo.pack(pady=(0, 30))
        
        self.lbl_circulo = tk.Label(frame, text="\u25CF", font=("Arial", 250), bg="black", fg="#333333")
        self.lbl_circulo.pack()
        
        self.lbl_instruccion = tk.Label(frame, text="BASCULA LIBRE", 
                                         font=("Helvetica", 36, "bold"), bg="black", fg="gray")
        self.lbl_instruccion.pack(pady=(20, 0))
        
        self.lbl_sub = tk.Label(frame, text="", 
                                 font=("Helvetica", 16), bg="black", fg="gray")
        self.lbl_sub.pack(pady=(10, 0))

        btn_full = tk.Button(self.ventana, text="Pantalla Completa", font=("Helvetica", 10),
                              bg="#333333", fg="white", command=self._toggle_fullscreen)
        btn_full.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
    
    def _toggle_fullscreen(self):
        is_full = self.ventana.attributes("-fullscreen")
        self.ventana.attributes("-fullscreen", not is_full)

    def actualizar_estado(self, nuevo_estado, placa=""):
        self.estado_actual = nuevo_estado
        
        if nuevo_estado == self.ESTADO_LIBRE:
            self.lbl_circulo.config(fg="#333333")
            self.lbl_instruccion.config(text="BASCULA LIBRE", fg="gray")
            self.lbl_sub.config(text="Esperando vehiculo...", fg="gray")
            self.ventana.configure(bg="black")
            
        elif nuevo_estado == self.ESTADO_ROJO:
            self.lbl_circulo.config(fg="#FF0000")
            self.lbl_instruccion.config(text="ALTO!", fg="#FF0000")
            self.lbl_sub.config(text="PESANDO... NO SE MUEVA", fg="#FF6666")
            self.ventana.configure(bg="#1A0000")
            
        elif nuevo_estado == self.ESTADO_AMARILLO:
            self.lbl_circulo.config(fg="#FFD700")
            self.lbl_instruccion.config(text="ESPERE...", fg="#FFD700")
            self.lbl_sub.config(text="Estabilizando peso...", fg="#FFE680")
            self.ventana.configure(bg="#1A1500")
            
        elif nuevo_estado == self.ESTADO_VERDE:
            self.lbl_circulo.config(fg="#00FF00")
            self.lbl_instruccion.config(text="LISTO, AVANCE!", fg="#00FF00")
            texto_sub = f"Placa: {placa} - Ticket generado" if placa else "Ticket generado"
            self.lbl_sub.config(text=texto_sub, fg="#80FF80")
            self.ventana.configure(bg="#001A00")
    
    def cerrar(self):
        try:
            self.ventana.destroy()
        except Exception:
            pass

import tkinter as tk
from tkinter import messagebox

class VentanaLogin:
    def __init__(self, root, on_login_success):
        self.root = root
        self.root.title("MinerTrack - Iniciar Sesión")
        self.root.geometry("400x500")
        self.root.configure(bg="#2E3440")
        self.root.resizable(False, False)
        
        self.on_login_success = on_login_success
        
        # Usuarios estáticos por ahora (se pueden mover a BD luego)
        self.usuarios = {
            "admin": "admin",
            "operador": "1234"
        }
        
        self._crear_interfaz()
        
    def _crear_interfaz(self):
        # Marco principal
        frame_login = tk.Frame(self.root, bg="#3B4252", bd=2, relief="groove")
        frame_login.place(relx=0.5, rely=0.5, anchor="center", width=320, height=400)
        
        # Título / Logo
        tk.Label(frame_login, text="🔒", font=("Helvetica", 40), bg="#3B4252", fg="#88C0D0").pack(pady=(20, 0))
        tk.Label(frame_login, text="MinerTrack", font=("Helvetica", 22, "bold"), bg="#3B4252", fg="#ECEFF4").pack(pady=(0, 20))
        
        # Usuario
        tk.Label(frame_login, text="Usuario", font=("Helvetica", 12), bg="#3B4252", fg="#D8DEE9").pack(anchor="w", padx=30)
        self.txt_usuario = tk.Entry(frame_login, font=("Helvetica", 14), justify="center")
        self.txt_usuario.pack(fill="x", padx=30, pady=(5, 15))
        
        # Contraseña
        tk.Label(frame_login, text="Contraseña", font=("Helvetica", 12), bg="#3B4252", fg="#D8DEE9").pack(anchor="w", padx=30)
        self.txt_password = tk.Entry(frame_login, font=("Helvetica", 14), show="*", justify="center")
        self.txt_password.pack(fill="x", padx=30, pady=(5, 25))
        
        # Evento Enter
        self.txt_password.bind("<Return>", lambda e: self.verificar_login())
        self.txt_usuario.bind("<Return>", lambda e: self.txt_password.focus_set())
        
        # Botón
        btn_entrar = tk.Button(frame_login, text="INGRESAR", font=("Helvetica", 14, "bold"), 
                               bg="#81A1C1", fg="white", command=self.verificar_login)
        btn_entrar.pack(fill="x", padx=30, pady=10, ipady=5)
        
    def verificar_login(self):
        usuario = self.txt_usuario.get().strip().lower()
        password = self.txt_password.get().strip()
        
        if not usuario or not password:
            messagebox.showwarning("Atención", "Por favor ingresa usuario y contraseña.")
            return
            
        if usuario in self.usuarios and self.usuarios[usuario] == password:
            self.on_login_success(usuario)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
            self.txt_password.delete(0, tk.END)

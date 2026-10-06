import sys
import os

# Aseguramos que Python encuentre nuestras carpetas (core, gui)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import AplicacionMinerTrack
from gui.login_window import VentanaLogin
import tkinter as tk

def iniciar_app(usuario):
    """Callback que se ejecuta cuando el login es exitoso."""
    print(f"Bienvenido {usuario}")
    # Limpiamos la ventana de login actual (la reutilizamos para la app)
    for widget in root.winfo_children():
        widget.destroy()
    
    # Iniciamos la aplicación principal con el nombre del operador
    app = AplicacionMinerTrack(root, operador=usuario)

if __name__ == "__main__":
    root = tk.Tk()
    
    # Iniciamos primero la ventana de Login
    login = VentanaLogin(root, on_login_success=iniciar_app)
    
    root.mainloop()

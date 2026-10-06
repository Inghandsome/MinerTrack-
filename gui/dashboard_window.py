import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class VentanaDashboard:
    def __init__(self, parent, gestor_bd):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("MinerTrack - Dashboard de Estadísticas")
        self.ventana.geometry("900x600")
        self.ventana.configure(bg="#2E3440")
        
        self.gestor_bd = gestor_bd
        
        # Título
        lbl_titulo = tk.Label(self.ventana, text="📈 Estadísticas Generales",
                              font=("Helvetica", 20, "bold"),
                              bg="#2E3440", fg="#88C0D0")
        lbl_titulo.pack(pady=20)
        
        self._crear_graficos()
        
    def _crear_graficos(self):
        # Contenedor para las gráficas
        frame_graficas = tk.Frame(self.ventana, bg="#2E3440")
        frame_graficas.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Obtener datos de MongoDB
        if self.gestor_bd.bd is None:
            tk.Label(frame_graficas, text="Base de datos no conectada.", bg="#2E3440", fg="red",
                     font=("Helvetica", 14)).pack(pady=50)
            return
            
        movimientos = list(self.gestor_bd.bd["movimientos"].find())
        if not movimientos:
            tk.Label(frame_graficas, text="No hay datos suficientes para mostrar estadísticas.\nGuarda algunos movimientos primero.",
                     bg="#2E3440", fg="white", font=("Helvetica", 14), justify="center").pack(pady=50)
            return
            
        # Convertir a DataFrame de pandas
        # Los campos en MongoDB son: fecha_hora, placas, material, peso_bruto_kg, peso_tara_kg, peso_neto_kg, estado
        df = pd.DataFrame(movimientos)
        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
        df['fecha_corta'] = df['fecha_hora'].dt.date
        df['peso_neto_kg'] = pd.to_numeric(df['peso_neto_kg'], errors='coerce').fillna(0)
        
        # Crear Figura de Matplotlib con 2 subgráficos (1 fila, 2 columnas)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor='#3B4252')
        fig.tight_layout(pad=5.0)
        
        # Gráfico 1: Toneladas por Día (Barras)
        df_diario = df.groupby('fecha_corta')['peso_neto_kg'].sum() / 1000  # Convertir a Toneladas
        
        ax1.bar(df_diario.index.astype(str), df_diario.values, color='#88C0D0')
        ax1.set_title("Toneladas Netas por Día", color='white', pad=10)
        ax1.set_ylabel("Toneladas (t)", color='white')
        ax1.tick_params(axis='x', colors='white', rotation=45)
        ax1.tick_params(axis='y', colors='white')
        ax1.set_facecolor('#434C5E')
        for spine in ax1.spines.values():
            spine.set_edgecolor('#D8DEE9')
            
        # Gráfico 2: Distribución de Materiales (Pastel)
        df_material = df.groupby('material')['peso_neto_kg'].sum()
        
        # Colores personalizados para el pastel
        colores = ['#A3BE8C', '#EBCB8B', '#BF616A', '#B48EAD', '#D08770']
        
        ax2.pie(df_material.values, labels=df_material.index, autopct='%1.1f%%',
                colors=colores, textprops={'color': 'white'}, startangle=90)
        ax2.set_title("Distribución por Material (Base Peso Neto)", color='white', pad=10)
        
        # Integrar Matplotlib con Tkinter
        canvas = FigureCanvasTkAgg(fig, master=frame_graficas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
